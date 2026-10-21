"""Loopback-only HTTP API. No database and no external queue service."""
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import threading
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .capabilities import REPO, environment
from .jobs import Jobs, TERMINAL, read_events, summary, write_json

OPTIONS = {'DM_LANG': ['system', 'zh-Hans', 'zh-Hant', 'en-US', 'ja'],
           'DM_OPMODE': ['0', '1'], 'DM_METALFX_SPATIAL': ['1', '0'],
           'DM_METALFX_OUTPUT_HEIGHT': ['auto', '720', '900', '1080', '1440']}


def data_directory(path):
    path = Path(path).expanduser().resolve()
    if path == Path(path.anchor) or path.is_relative_to(REPO) or path.is_relative_to(Path.home()):
        raise ValueError('Choose a dedicated data folder outside the repository and your home directory.')
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_app(root, token=None, config=None):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    token = token or secrets.token_urlsafe(32)
    config_path = root / 'config.json'
    config = config or (json.loads(config_path.read_text()) if config_path.exists() else {})
    config.setdefault('tools', str(root / 'tools'))
    inbox = root / 'inbox'; inbox.mkdir(exist_ok=True)
    upload_lock = threading.Lock()
    jobs = Jobs(root, REPO, config)

    @asynccontextmanager
    async def lifespan(app):
        yield
        jobs.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.token, app.state.jobs = token, jobs

    @app.middleware('http')
    async def protect(request, call_next):
        host = request.headers.get('host', '').split(':')[0]
        if host not in ('127.0.0.1', 'localhost', 'testserver'):
            return JSONResponse({'detail': 'Invalid host'}, status_code=403)
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': 'Invalid origin'}, status_code=403)
        if request.url.path.startswith('/api/'):
            supplied = request.headers.get('x-session-token') or request.cookies.get('nx_session', '')
            if not secrets.compare_digest(supplied, token):
                return JSONResponse({'detail': 'Open the URL printed by the launcher.'}, status_code=401)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'"
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        return JSONResponse({'detail': str(error)}, status_code=400)

    @app.post('/api/session')
    def session():
        response = JSONResponse({'ok': True})
        response.set_cookie('nx_session', token, httponly=True, samesite='strict')
        return response

    @app.get('/api/environment')
    def env():
        return dict(environment(config), config=config, data_directory=str(root))

    @app.put('/api/config')
    async def configure(request: Request):
        value = await request.json()
        if any(k not in ('tools', 'sdk', 'metal') for k in value):
            raise ValueError('Unknown tool setting')
        with jobs.lock:
            if jobs.active or jobs.pending:
                raise ValueError('Wait for queued tasks before changing tools.')
            for key, path in value.items():
                if not isinstance(path, str): raise ValueError('Expected a path')
                config[key] = str(Path(path).expanduser().resolve()) if path else ''
            if not config.get('tools'): config['tools'] = str(root / 'tools')
            write_json(config_path, config)
        return environment(config)

    def upload_meta(identity):
        if not re.fullmatch('[a-f0-9]{32}', identity): raise ValueError('Invalid upload ID')
        path = inbox / (identity + '.json')
        if not path.is_file(): raise ValueError('Upload not found')
        return path, json.loads(path.read_text())

    @app.post('/api/uploads')
    async def upload_start(request: Request):
        value = await request.json()
        name, size = value.get('name', ''), value.get('size', 0)
        if not isinstance(name, str) or Path(name).name != name or any(c in name for c in '\\/:'):
            raise ValueError('Invalid filename')
        if Path(name).suffix.lower() not in ('.nsp', '.xci', '.keys'):
            raise ValueError('Expected NSP, XCI or keys')
        if type(size) is not int or size <= 0 or size > 256 * 1024**3:
            raise ValueError('Invalid file size')
        if name.lower().endswith('.keys') and size > 1024 * 1024:
            raise ValueError('Keys file is too large')
        if shutil.disk_usage(root).free < size + 256 * 1024**2:
            raise ValueError('Not enough free space')
        identity = uuid.uuid4().hex
        value = dict(name=name, size=size, path=str(inbox / (identity + Path(name).suffix.lower())), imported=False)
        write_json(inbox / (identity + '.json'), value)
        Path(value['path']).touch(mode=0o600)
        return dict(id=identity, offset=0)

    @app.get('/api/uploads/{identity}')
    def upload_status(identity: str):
        _, value = upload_meta(identity)
        return dict(id=identity, name=value['name'], size=value['size'], offset=Path(value['path']).stat().st_size)

    @app.put('/api/uploads/{identity}')
    async def upload_chunk(identity: str, request: Request, offset: int = 0):
        # Bound memory even when Content-Length is missing or dishonest.
        data = bytearray()
        async for block in request.stream():
            data.extend(block)
            if len(data) > 8 * 1024**2: raise ValueError('Maximum chunk size is 8 MiB')
        with upload_lock:
            _, value = upload_meta(identity)
            path = Path(value['path'])
            if value['imported'] or path.stat().st_size != offset or offset + len(data) > value['size']:
                raise ValueError('Upload offset conflict; fetch upload status before retrying')
            with path.open('ab') as stream: stream.write(data)
        return dict(offset=offset + len(data))

    @app.post('/api/import')
    async def import_file(request: Request):
        path = Path((await request.json())['path']).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() not in ('.nsp', '.xci', '.keys'):
            raise ValueError('Choose an existing NSP, XCI or keys file')
        identity = uuid.uuid4().hex
        write_json(inbox / (identity + '.json'), dict(name=path.name, size=path.stat().st_size, path=str(path), imported=True))
        return dict(id=identity, name=path.name)

    @app.delete('/api/uploads/{identity}')
    def delete_upload(identity: str):
        meta, value = upload_meta(identity)
        with jobs.lock:
            if jobs.active or jobs.pending: raise ValueError('Wait for tasks before clearing imports')
            if not value['imported']: Path(value['path']).unlink(missing_ok=True)
            meta.unlink()
        return {'ok': True}

    @app.get('/api/tasks')
    def list_tasks():
        return sorted([summary(p) for p in jobs.directory.iterdir() if (p / 'task.json').is_file()],
                      key=lambda x: x['created'], reverse=True)

    @app.post('/api/tasks')
    async def create_task(request: Request):
        value = await request.json()
        kind = value.get('kind', 'build')
        if kind not in ('build', 'convert', 'inspect'): raise ValueError('Invalid task type')
        files = []
        for identity in value.get('files', []):
            _, item = upload_meta(identity)
            if Path(item['path']).suffix.lower() not in ('.nsp', '.xci') or Path(item['path']).stat().st_size != item['size']:
                raise ValueError('Game input is incomplete')
            files.append(item['path'])
        _, keys = upload_meta(value.get('keys', ''))
        if not keys['path'].lower().endswith('.keys') or Path(keys['path']).stat().st_size != keys['size']:
            raise ValueError('Keys upload is incomplete')
        if not files: raise ValueError('Add at least one game file')
        targets = value.get('targets', ['ios'])
        if not isinstance(targets, list) or not targets or any(t not in ('ios', 'mac') for t in targets):
            raise ValueError('Invalid platform selection')
        settings = value.get('settings', {})
        if not isinstance(settings, dict) or any(k not in OPTIONS or v not in OPTIONS[k] for k, v in settings.items()):
            raise ValueError('Invalid launch settings')
        settings = {k: settings.get(k, choices[0]) for k, choices in OPTIONS.items()}
        settings.update(DM_METALFX_INTERPOLATION='0', DM_DYNAMIC_RESOLUTION='1')
        return {'id': jobs.create(dict(kind=kind, files=files, keys=keys['path'], game=value.get('game', ''),
            targets=list(dict.fromkeys(targets)), settings=settings, retain_keys=bool(value.get('retain_keys', False))))}

    @app.get('/api/tasks/{identity}/events')
    def events(identity: str, offset: int = 0):
        if offset < 0: raise ValueError('Invalid offset')
        rows, end = read_events(jobs.folder(identity) / 'events.jsonl', offset)
        return dict(events=rows, offset=end)

    @app.get('/api/tasks/{identity}/log')
    def log(identity: str, offset: int = 0):
        if offset < 0: raise ValueError('Invalid offset')
        path = jobs.folder(identity) / 'build.log'
        if not path.exists(): return dict(text='', offset=0)
        with path.open('rb') as stream:
            stream.seek(offset); data = stream.read(128 * 1024)
            return dict(text=data.decode('utf-8', errors='replace'), offset=stream.tell())

    @app.post('/api/tasks/{identity}/cancel')
    def cancel(identity: str):
        jobs.cancel(identity); return {'ok': True}

    @app.post('/api/tasks/{identity}/retry')
    def retry(identity: str):
        folder = jobs.folder(identity)
        if summary(folder)['status'] not in TERMINAL: raise ValueError('Task is still active')
        task = json.loads((folder / 'task.json').read_text(encoding='utf-8'))
        if (folder / 'private.keys').exists(): task['keys'] = str(folder / 'private.keys')
        if not Path(task['keys']).exists(): raise ValueError('Import keys again and create a new task')
        task['retry_of'] = identity
        return {'id': jobs.create(task)}

    @app.get('/api/tasks/{identity}/artifacts/{name:path}')
    def artifact(identity: str, name: str):
        folder = jobs.folder(identity)
        root = (folder / 'outputs').resolve()
        path = (root / name).resolve()
        if not path.is_relative_to(root) or name not in summary(folder)['artifacts'] or not path.is_file():
            raise HTTPException(404)
        return FileResponse(path, filename=path.name, media_type='application/octet-stream')

    @app.delete('/api/tasks/{identity}')
    def remove_task(identity: str):
        with jobs.lock:
            folder = jobs.folder(identity)
            if jobs.active or jobs.pending: raise ValueError('Wait for tasks before removing cached inputs')
            if summary(folder)['status'] not in TERMINAL: raise ValueError('Cancel the task first')
            if folder.resolve().parent != jobs.directory.resolve(): raise ValueError('Invalid task path')
            shutil.rmtree(folder)
        return {'ok': True}

    app.mount('/', StaticFiles(directory=Path(__file__).with_name('static'), html=True), name='ui')
    return app
