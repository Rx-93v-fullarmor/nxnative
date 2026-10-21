"""Install missing runtime dependencies into a workspace-local virtual environment."""
import importlib
import importlib.metadata
import os
from pathlib import Path
import re
import subprocess
import sys

PACKAGES = {'fastapi': 'fastapi', 'uvicorn': 'uvicorn', 'lz4': 'lz4',
            'capstone': 'capstone', 'fonttools': 'fontTools', 'Pillow': 'PIL'}
MINIMUM = {'fastapi': (0, 115), 'uvicorn': (0, 34)}

def missing_dependencies():
    missing = []
    for package, module in PACKAGES.items():
        try:
            version = importlib.metadata.version(package)
            importlib.import_module(module)
            if package in MINIMUM:
                parts = tuple(int(x) for x in re.findall(r'\d+', version)[:2])
                if parts < MINIMUM[package] or parts >= (1, 0):
                    missing.append(package)
        except (ImportError, OSError, importlib.metadata.PackageNotFoundError):
            missing.append(package)
    return missing

def ensure_dependencies(root, repo):
    missing = missing_dependencies()
    if not missing:
        return
    print('Installing missing Python dependencies: ' + ', '.join(missing), flush=True)
    runtime = Path(root) / 'venv'
    python = runtime / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python3')
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    try:
        if not python.is_file():
            subprocess.run([sys.executable, '-m', 'venv', str(runtime)], check=True)
        probe = [str(python), str(Path(__file__).resolve()), '--check']
        if subprocess.run(probe, stdout=subprocess.DEVNULL, env=env).returncode:
            subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                            '-r', str(Path(repo) / 'dm/webui/requirements.txt')], check=True, env=env)
            subprocess.run(probe, check=True, env=env)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError('Automatic dependency setup failed. Check your network and Python venv/pip installation, then restart. ' + str(error)) from error
    # Use the same interpreter for the server and all build workers.
    return subprocess.run([str(python), str(Path(repo) / 'scripts/start_webui.py'), *sys.argv[1:]], env=env).returncode

if __name__ == '__main__':
    raise SystemExit(bool(missing_dependencies()))
