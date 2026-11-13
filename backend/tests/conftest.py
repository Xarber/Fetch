# SPDX-License-Identifier: AGPL-3.0-only
import functools
import os
import subprocess
import tempfile
import shutil
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer

class LocalServer(ThreadingHTTPServer):
    def server_bind(self):
        TCPServer.server_bind(self)
        self.server_name = "localhost"
        self.server_port = self.server_address[1]

import pytest

ROOT=Path(tempfile.mkdtemp(prefix='fetch-tests-'))
MEDIA=ROOT/'fixture'; MEDIA.mkdir()
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=blue:s=160x90:r=10','-f','lavfi','-i','sine=frequency=440:sample_rate=44100','-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(MEDIA/'authorized.mp4')],check=True)
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*_): pass
    def do_GET(self):
        if self.path=='/redirect':
            self.send_response(302); self.send_header('Location','http://169.254.169.254/latest/meta-data'); self.end_headers()
        else: super().do_GET()
server=LocalServer(('127.0.0.1',0),functools.partial(Handler,directory=str(MEDIA)))
threading.Thread(target=server.serve_forever,daemon=True).start()
os.environ['FETCH_DATA']=str(ROOT/'data')
os.environ['FETCH_ADMIN_PASSWORD']='test-only-unique-password-2026'
os.environ['FETCH_TEST_ORIGIN']=f'127.0.0.1:{server.server_port}'
os.environ['FETCH_MIN_FREE']='1048576'

@pytest.fixture(scope='session')
def client():
    from fastapi.testclient import TestClient
    from fetch_server.api import app
    with TestClient(app) as c: yield c
    server.shutdown()
    server.server_close()
    shutil.rmtree(ROOT,ignore_errors=True)

@pytest.fixture(scope='session')
def auth(client):
    result=client.post('/api/v1/auth/login',json={'username':'admin','password':os.environ['FETCH_ADMIN_PASSWORD']}).json()
    return {'Authorization':'Bearer '+result['token']}

@pytest.fixture(scope='session')
def media_url(): return f'http://127.0.0.1:{server.server_port}/authorized.mp4'

@pytest.fixture(scope='session')
def incompatible_media_url():
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-i',str(MEDIA/'authorized.mp4'),'-c:v','mpeg4','-c:a','libmp3lame',str(MEDIA/'legacy.mp4')],check=True)
    return f'http://127.0.0.1:{server.server_port}/legacy.mp4'
