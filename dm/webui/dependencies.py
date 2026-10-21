"""Allowlisted dependency installation through the existing logged task queue."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request
import zipfile

from scripts.webui_bootstrap import DEFAULT_INDEX, PYTHON_INDEXES
from .jobs import emit

PYTHON_PACKAGES = {'lz4': 'lz4', 'capstone': 'capstone', 'fontTools': 'fonttools', 'PIL': 'Pillow'}
BREW_PACKAGES = {'xcodegen', 'zstd', 'spirv-cross'}
DOTNET_METADATA = 'https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json'

def tool_path(config):
    return os.pathsep.join([str(Path(config['tools']) / 'bin'), '/opt/homebrew/bin', '/usr/local/bin', os.environ.get('PATH', '')])

def brew_path(config):
    return shutil.which('brew', path=tool_path(config))

def install_method(name, config, system=None):
    system = system or platform.system()
    if name in PYTHON_PACKAGES:
        return 'python'
    if name in ('dotnet', 'extractor') and system in ('Darwin', 'Windows') and platform.machine().lower() in ('arm64', 'aarch64', 'x86_64', 'amd64'):
        return 'local'
    if name in BREW_PACKAGES and system == 'Darwin' and brew_path(config):
        return 'homebrew'
    return 'manual'

def download(url, destination, folder, expected_hash):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('builds.dotnet.microsoft.com', 'download.visualstudio.microsoft.com', 'ci.dot.net'):
        raise ValueError('Unexpected .NET download origin')
    digest = hashlib.sha512()
    with urllib.request.urlopen(url, timeout=60) as response, destination.open('wb') as output:
        total = int(response.headers.get('Content-Length', 0))
        done, last = 0, -1
        while block := response.read(1024 * 1024):
            output.write(block); digest.update(block); done += len(block)
            if done // (8 * 1024**2) != last:
                last = done // (8 * 1024**2)
                print(f'Downloaded {done // 1024**2} / {total // 1024**2} MiB', flush=True)
                emit(folder, 'stage', name=f'Downloading .NET: {done // 1024**2} / {total // 1024**2} MiB')
    if digest.hexdigest().lower() != expected_hash.lower():
        destination.unlink(missing_ok=True)
        raise ValueError('.NET SHA-512 checksum mismatch')

def unpack(archive, destination):
    if archive.suffix == '.zip':
        with zipfile.ZipFile(archive) as source:
            for item in source.infolist():
                path = (destination / item.filename).resolve()
                if not path.is_relative_to(destination.resolve()) or ':' in item.filename or '\\' in item.filename:
                    raise ValueError('Unsafe archive member')
            source.extractall(destination)
    else:
        with tarfile.open(archive) as source:
            source.extractall(destination, filter='data')

def install_dotnet(folder, root, run):
    system = platform.system()
    arch = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'amd64': 'x64'}[platform.machine().lower()]
    rid = ('win' if system == 'Windows' else 'osx') + '-' + arch
    suffix = '.zip' if system == 'Windows' else '.tar.gz'
    print('Reading official .NET 10 SDK release metadata', flush=True)
    with urllib.request.urlopen(DOTNET_METADATA, timeout=60) as response:
        metadata = json.load(response)
    sdk = next(sdk for release in metadata['releases'] for sdk in release.get('sdks', [release['sdk']]) if sdk['version'] == metadata['latest-sdk'])
    asset = next(f for f in sdk['files'] if f['rid'] == rid and f['url'].endswith(suffix))
    archive = folder / ('dotnet' + suffix)
    download(asset['url'], archive, folder, asset['hash'])
    stage = root / ('.dotnet-install-' + folder.name)
    stage.mkdir(parents=True, exist_ok=True)
    try:
        unpack(archive, stage)
        binary = stage / ('dotnet.exe' if system == 'Windows' else 'dotnet')
        run(folder, [binary, '--version'], dict(os.environ, DOTNET_ROOT=str(stage)))
        if (root / 'dotnet').exists():
            raise ValueError('The configured dotnet directory already exists but is incomplete. Choose a new tools directory or repair it manually.')
        stage.rename(root / 'dotnet')
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        archive.unlink(missing_ok=True)

def install(folder, task, config, run):
    from .capabilities import REPO, environment
    root = Path(config['tools']); root.mkdir(parents=True, exist_ok=True)
    names = task['dependencies']
    if not isinstance(names, list) or any(install_method(n, config) == 'manual' for n in names):
        raise ValueError('Unsupported automatic dependency')
    names = list(dict.fromkeys(names))
    if 'extractor' in names and 'dotnet' not in names:
        names.insert(0, 'dotnet')
    if 'dotnet' in names:
        names.remove('dotnet'); names.insert(0, 'dotnet')
    index = config.get('python_index', DEFAULT_INDEX)
    if index not in PYTHON_INDEXES:
        raise ValueError('Unsupported Python package source')
    failed = []
    for name in names:
        if next(c for c in environment(config)['checks'] if c['name'] == name)['available']:
            print('Already installed: ' + name, flush=True)
            continue
        emit(folder, 'stage', name='Installing ' + name)
        try:
            if name in PYTHON_PACKAGES:
                package_dir = root / 'python-packages'
                env = dict(os.environ, PIP_CONFIG_FILE=os.devnull, PIP_EXTRA_INDEX_URL='', PIP_CACHE_DIR=str(root / 'pip-cache'))
                run(folder, [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--index-url', index,
                             '--target', package_dir, '--upgrade', PYTHON_PACKAGES[name]], env)
                if str(package_dir) not in sys.path: sys.path.insert(0, str(package_dir))
                importlib.invalidate_caches()
            elif name == 'dotnet':
                install_dotnet(folder, root, run)
            elif name == 'extractor':
                dotnet = root / 'dotnet' / ('dotnet.exe' if os.name == 'nt' else 'dotnet')
                run(folder, [dotnet, 'build', REPO / 'dm/tools/nx_extract', '-c', 'Release', '-o', root / 'nx_extract',
                             '-p:BaseIntermediateOutputPath=' + str(root / 'obj') + os.sep])
            else:
                env = dict(os.environ, HOMEBREW_NO_AUTO_UPDATE='1', HOMEBREW_NO_INSTALL_CLEANUP='1', HOMEBREW_CACHE=str(root / 'brew-cache'))
                run(folder, [brew_path(config), 'install', name], env)
            if not next(c for c in environment(config)['checks'] if c['name'] == name)['available']:
                raise RuntimeError('Dependency is still unavailable after installation: ' + name)
            print('Installed: ' + name, flush=True)
        except Exception as error:
            print('【红】' + name + ': ' + str(error), flush=True)
            failed.append(name)
    if failed:
        raise RuntimeError('Dependency installation failed: ' + ', '.join(failed) + '. See build.log; retry after fixing the reported cause.')
    emit(folder, 'stage', name='Dependency installation complete')
