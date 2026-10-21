"""Bounded discovery and local import of user-supplied Apple tools."""
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil

SDK_MINIMUM = (26, 5)
SKIP = {'.git', '.webui-data', 'node_modules', 'venv', 'runtime', '__pycache__'}


def sdk_info(path):
    path = Path(path)
    if path.suffix.lower() != '.sdk' or not path.is_dir():
        return None
    try:
        metadata = path / 'SDKSettings.json'
        if metadata.is_file():
            data = json.loads(metadata.read_text(encoding='utf-8'))
        else:
            with (path / 'SDKSettings.plist').open('rb') as stream:
                data = plistlib.load(stream)
        if not isinstance(data, dict):
            return None
        canonical = str(data.get('CanonicalName', '')).lower()
        if not canonical.startswith('iphoneos'):
            return None
        version = str(data.get('Version', ''))
        if not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', version):
            return None
        numbers = tuple(int(n) for n in re.findall(r'\d+', version))
        if (numbers + (0, 0))[:2] < SDK_MINIMUM:
            return None
        required = ('usr/include', 'usr/lib/libSystem.tbd',
                    'System/Library/Frameworks/Foundation.framework/Headers/Foundation.h')
        if not all((path / name).exists() for name in required):
            return None
        return dict(path=str(path.resolve()), version=version)
    except (OSError, ValueError, TypeError, plistlib.InvalidFileException):
        return None


def downloads_directory():
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
                value, _ = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')
            return Path(os.path.expandvars(value)).expanduser()
        except OSError:
            pass
    return Path.home() / 'Downloads'


def search_locations(config):
    root = Path(config['tools'])
    candidates = [root / 'ios-cross', downloads_directory(), root,
                  Path(__file__).resolve().parents[2]]
    if config.get('sdk_search'):
        candidates.insert(0, Path(config['sdk_search']).expanduser())
    result = []
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
            # Never turn a configured drive/home root into a recursive search.
            if candidate == Path(candidate.anchor) or candidate == Path.home().resolve():
                continue
            if candidate not in result:
                result.append(candidate)
        except OSError:
            continue
    return result


def bounded_entries(root, depth=3, budget=1500):
    pending, count = [(Path(root), 0)], 0
    while pending and count < budget:
        directory, level = pending.pop(0)
        yield directory
        if directory.suffix.lower() == '.sdk':
            continue
        try:
            with os.scandir(directory) as stream:
                for entry in stream:
                    count += 1
                    if count > budget:
                        break
                    if entry.is_symlink() or entry.name in SKIP or entry.name.startswith('.'):
                        continue
                    path = Path(entry.path)
                    if entry.is_dir(follow_symlinks=False):
                        if level < depth:
                            pending.append((path, level + 1))
                    elif entry.is_file(follow_symlinks=False):
                        yield path
        except OSError:
            continue


def scan_apple_tools(config):
    locations = search_locations(config)
    sdks, archives, seen = [], [], set()
    for root in locations:
        for path in bounded_entries(root):
            if path in seen:
                continue
            seen.add(path)
            info = sdk_info(path)
            if info:
                sdks.append(info)
            elif 'iphoneos' in path.name.lower() and path.is_file() and path.name.lower().endswith(('.zip', '.tar', '.tar.gz', '.tar.xz', '.tgz')):
                archives.append(str(path.resolve()))
    sdks.sort(key=lambda item: (item['version'] == '26.5', tuple(int(n) for n in re.findall(r'\d+', item['version']))), reverse=True)
    metal = ''
    candidates = [Path(config['tools']) / 'metal/metal.exe']
    on_path = shutil.which('metal.exe')
    if on_path:
        candidates.append(Path(on_path))
    for variable in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)'):
        if os.environ.get(variable):
            candidates.append(Path(os.environ[variable]) / 'Metal Developer Tools/bin/metal.exe')
    for candidate in candidates:
        if candidate.is_file() and candidate.with_name('metallib.exe').is_file():
            metal = str(candidate.resolve())
            break
    return dict(sdks=sdks, archives=sorted(set(archives)), metal=metal,
                searched=[str(path) for path in locations], minimum='26.5')


def effective_config(config, discovery=None):
    result = dict(config)
    if platform.system() != 'Windows':
        return result
    discovery = discovery if discovery is not None else scan_apple_tools(config)
    selected = sdk_info(config.get('sdk') or Path(config['tools']) / 'ios-cross/iPhoneOS26.5.sdk')
    if selected:
        result['sdk'] = selected['path']
    elif discovery['sdks']:
        result['sdk'] = discovery['sdks'][0]['path']
    configured_metal = Path(config.get('metal') or Path(config['tools']) / 'metal/metal.exe')
    if configured_metal.is_file():
        result['metal'] = str(configured_metal.resolve())
    elif discovery['metal']:
        result['metal'] = discovery['metal']
    return result


def sdk_archive(config, discovery=None):
    explicit = config.get('sdk_archive')
    if explicit:
        path = Path(explicit)
        return path if path.is_file() and path.name.lower().endswith(('.zip', '.tar', '.tar.gz', '.tar.xz', '.tgz')) else None
    found = discovery if discovery is not None else scan_apple_tools(config)
    # Multiple archives require the user's choice rather than guessing a version.
    return Path(found['archives'][0]) if len(found['archives']) == 1 else None


def remove_stage(stage, root):
    stage, root = Path(stage).resolve(), Path(root).resolve()
    if stage == root or not stage.is_relative_to(root):
        raise ValueError('Refusing to remove a staging directory outside the tools folder')
    shutil.rmtree(stage, ignore_errors=True)


def install_sdk(folder, config):
    from .dependencies import unpack
    from .jobs import emit
    archive = sdk_archive(config)
    if not archive:
        raise ValueError('Download an iPhoneOS SDK archive first, or choose one of the discovered archives.')
    root = Path(config['tools']).resolve()
    stage = root / ('.sdk-install-' + folder.name)
    stage.mkdir(parents=True, exist_ok=False)
    try:
        emit(folder, 'stage', name='Extracting user-supplied iPhoneOS SDK')
        print('SDK archive: ' + str(archive), flush=True)
        unpack(archive, stage)
        candidates = [info for path in stage.rglob('*.sdk') if (info := sdk_info(path))]
        if len(candidates) != 1:
            raise ValueError('Archive must contain exactly one complete iPhoneOS SDK version 26.5 or newer; simulator and macOS SDKs are not accepted.')
        source = Path(candidates[0]['path'])
        destination = root / 'ios-cross' / ('iPhoneOS' + candidates[0]['version'] + '.sdk')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise ValueError('SDK destination already exists. Repair or choose the existing SDK in Settings.')
        source.rename(destination)
        print('SDK configured automatically: ' + str(destination), flush=True)
    finally:
        remove_stage(stage, root)
