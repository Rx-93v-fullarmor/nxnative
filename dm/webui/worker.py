"""Isolated task runner; all descendants share its cancellable process group."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from .capabilities import REPO, game, profiles
from .jobs import emit
from .packages import catalog, convert, entries


def run(folder, command, env=None):
    process = subprocess.Popen([str(x) for x in command], stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', env=env)
    for line in process.stdout:
        if line.startswith('@NXEVENT '):
            try:
                event = json.loads(line[9:])
                emit(folder, 'stage', name=event['name'])
            except (ValueError, KeyError):
                pass
        print(line, end='', flush=True)
    if process.wait():
        raise RuntimeError('Build command failed. See build.log for details.')


def local_link(source, destination):
    if destination.exists():
        raise ValueError('Duplicate input content')
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def execute(folder):
    task = json.loads((folder / 'task.json').read_text(encoding='utf-8'))
    config = json.loads(os.environ['NX_WEB_CONFIG'])
    if task['kind'] == 'install':
        from .dependencies import install
        install(folder, task, config, run)
        return
    toolroot = Path(config['tools'])
    extractor = toolroot / 'nx_extract' / ('nx_extract.exe' if os.name == 'nt' else 'nx_extract')
    if not extractor.is_file():
        raise ValueError('Missing nx_extract. Prepare the dependency bundle in Settings first.')
    keys = folder / 'private.keys'
    source_keys = Path(task['keys'])
    if not source_keys.is_file():
        raise ValueError('Keys are no longer available. Import keys again before retrying.')
    shutil.copyfile(source_keys, keys)
    if os.name != 'nt':
        keys.chmod(0o600)
    outputs = folder / 'outputs'; outputs.mkdir(exist_ok=True)
    converted, package_paths = [], []
    last_progress = [0.0]
    def progress(done, total):
        now = time.monotonic()
        if now - last_progress[0] > 1 or done == total:
            emit(folder, 'progress', done=done, total=total)
            last_progress[0] = now
    for number, filename in enumerate(task['files']):
        source = Path(filename)
        if source.suffix.lower() == '.xci':
            emit(folder, 'stage', name='Converting XCI to NSP')
            converted += convert(source, outputs / f'conversion-{number}', extractor, keys, progress)
        elif source.suffix.lower() == '.nsp':
            entries(source)
            package_paths.append(source)
        else:
            raise ValueError('Only uncompressed NSP and XCI inputs are supported.')
    package_paths += converted
    for path in converted:
        emit(folder, 'artifact', name=str(path.relative_to(outputs)))
    if task['kind'] == 'convert':
        if not converted:
            raise ValueError('Select at least one XCI to convert.')
        return
    emit(folder, 'stage', name='Inspecting package metadata')
    records = [(path, item) for path in package_paths for item in catalog(extractor, keys, path)]
    bases = {item['title_id'] for _, item in records if item['type'] == 0x80}
    title = task.get('game') or (next(iter(bases)) if len(bases) == 1 else '')
    if title not in bases:
        raise ValueError('Choose one base game present in the input files.')
    profile = next((p for p in profiles() if p['id'] == title), None)
    report = dict(title_id=title, packages=[r for _, r in records], supported=bool(profile))
    (outputs / 'inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    emit(folder, 'artifact', name='inspection.json')
    if task['kind'] == 'inspect':
        emit(folder, 'stage', name='Extracting code and RomFS manifest')
        base_path = next(p for p, item in records if item['title_id'] == title and item['type'] == 0x80)
        updates = [(item['version'], p) for p, item in records if int(item['title_id'], 16) == int(title, 16) + 0x800]
        update = max(updates)[1] if updates else '-'
        survey = folder / 'survey'; survey.mkdir(exist_ok=True)
        run(folder, [extractor, keys, base_path, update, survey, '--manifest'])
        manifest = survey / 'romfs_manifest.tsv'
        if manifest.exists():
            shutil.copyfile(manifest, outputs / 'romfs_manifest.tsv')
            emit(folder, 'artifact', name='romfs_manifest.tsv')
        modules = {}
        for module in (survey / 'ExeFS').iterdir():
            with module.open('rb') as stream: header = stream.read(0x60)
            if header[:4] == b'NSO0' and len(header) >= 0x50:
                modules[module.name] = header[0x40:0x50].hex()
        report['module_build_ids'] = modules
        (outputs / 'inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        return
    if profile is None:
        raise ValueError('No registered profile. Inspection report is available; application build is disabled.')
    for target in task['targets']:
        if not profile[target]:
            raise ValueError(profile['reason'] or 'Target unavailable on this host.')
    g = game.load(title)
    inputs = folder / 'inputs'
    retry = task.get('retry_of', '')
    if len(retry) == 32 and all(c in '0123456789abcdef' for c in retry):
        previous = folder.parent / retry
        previous_task = json.loads((previous / 'task.json').read_text(encoding='utf-8'))
        if previous_task['files'] == task['files'] and (previous / 'inputs').is_dir():
            inputs = previous / 'inputs'
    inputs.mkdir(exist_ok=True)
    selected = []
    for path, item in records:
        tid = int(item['title_id'], 16)
        base = int(title, 16)
        if tid == base or tid == base + 0x800 or (item['type'] == 0x82 and (tid - 0x1000) & ~0xfff == base):
            if sum(1 for p, _ in records if p == path) != 1:
                raise ValueError('Multi-title NSP inputs must be separated before building.')
            target_input = inputs / f"{item['title_id']}_v{item['version']}.nsp"
            if not target_input.exists(): local_link(path, target_input)
            elif target_input.stat().st_size != path.stat().st_size or target_input.stat().st_mtime_ns != path.stat().st_mtime_ns:
                with path.open('rb') as original, target_input.open('rb') as cached:
                    if hashlib.file_digest(original, 'sha256').digest() != hashlib.file_digest(cached, 'sha256').digest():
                        raise ValueError('Cached input changed; create a new task instead of retrying.')
            selected.append(item)
    versions = {f"v{x['version']}" for x in selected if x['type'] in (0x80, 0x81)}
    needed = set(g.words('shader_versions')) | {g.get('package')}
    if not needed <= versions:
        raise ValueError('Missing required versions: ' + ', '.join(sorted(needed - versions)))
    settings = task['settings']
    if profile['graphics'] == 'vulkan':
        settings = dict(settings, DM_METALFX_SPATIAL='0')
    defaults = folder / 'launch-defaults.json'
    defaults.write_text(json.dumps(dict(settings, NX_WEBUI_RELEASE='1', NX_GRAPHICS=profile['graphics'])), encoding='utf-8')
    envfile = folder / 'launch.env'
    envfile.write_text('\n'.join(f'{k}={v}' for k, v in settings.items()) + '\n', encoding='utf-8')
    env = dict(os.environ, NX_PROGRESS='1', NX_LAUNCH_DEFAULTS=str(defaults))
    failed = []
    for target in task['targets']:
        emit(folder, 'stage', name=f'Building {target}')
        output = outputs / (title + ('.ipa' if target == 'ios' else '.app.zip'))
        if platform.system() == 'Windows':
            command = [sys.executable, REPO / 'scripts/build_ipa_windows.py', inputs, '--game', title,
                       '--keys', keys, '--tools', toolroot, '--out', output, '--env-file', envfile,
                       '--launch-defaults', defaults]
            for option in ('sdk', 'metal'):
                if config.get(option): command += ['--' + option, config[option]]
        else:
            command = [sys.executable, REPO / 'scripts/build_ipa_from_nsp.py', inputs, '--keys', keys,
                       '--target', target, '--out', output, '--env-file', envfile, '--keep-extracted', '--progress', 'off']
        try:
            run(folder, command, env)
            if not output.is_file():
                raise RuntimeError('Build did not produce its expected output.')
            with output.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            output.with_name(output.name + '.sha256').write_text(digest + '  ' + output.name + '\n')
            emit(folder, 'artifact', name=output.name)
            emit(folder, 'artifact', name=output.name + '.sha256')
            emit(folder, 'target', target=target, status='succeeded')
        except Exception as error:
            failed.append(target)
            emit(folder, 'target', target=target, status='failed', message=str(error))
    if failed:
        raise RuntimeError('Failed targets: ' + ', '.join(failed) + '. Any successful outputs remain downloadable.')


if __name__ == '__main__':
    directory = Path(sys.argv[1]).resolve()
    try:
        execute(directory)
        emit(directory, 'status', status='succeeded')
    except Exception as error:
        print('【红】' + str(error), flush=True)
        emit(directory, 'status', status='failed', message=str(error))
        sys.exit(1)
