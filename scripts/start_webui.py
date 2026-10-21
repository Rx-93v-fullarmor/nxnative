#!/usr/bin/env python3
"""Start the local nxnative WebUI (terminal or Spyder F5)."""
import argparse
import os
import json
from pathlib import Path
import secrets
import socket
import sys
import threading
import webbrowser

DATA_DIR = ''
PORT = 8765
OPEN_BROWSER = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', default=DATA_DIR)
    parser.add_argument('--tools', help='Prepared tool directory (or NX_TOOLS_DIR)')
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    toolroot = args.tools or os.environ.get('NX_TOOLS_DIR')
    if toolroot: sys.path.insert(0, str(Path(toolroot).resolve() / 'python-packages'))
    # Release launchers select the bundled Python; source installs use this interpreter.
    try:
        import uvicorn
        from dm.webui.server import create_app, data_directory
    except ImportError:
        parser.error('Web dependencies are missing. Install dm/webui/requirements.txt or use a prepared release bundle.')
    folder = args.data_dir or os.environ.get('NX_DATA_DIR', '')
    if not folder:
        if not sys.stdin.isatty(): parser.error('Set DATA_DIR or pass --data-dir')
        folder = input('Data folder (outside your home and repository): ').strip().strip('"')
    root = data_directory(folder)
    token = secrets.token_urlsafe(32)
    config_path = root / 'config.json'
    config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    if toolroot: config['tools'] = str(Path(toolroot).resolve())
    app = create_app(root, token, config)
    url = f'http://127.0.0.1:{args.port}/#{token}'
    print('Open in your browser: ' + url, flush=True)
    if OPEN_BROWSER and not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    try:
        uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False)
    finally:
        app.state.jobs.close()


if __name__ == '__main__':
    main()
