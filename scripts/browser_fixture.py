# SPDX-License-Identifier: AGPL-3.0-only
"""Local-only disposable browser test server; never a deployment entry point."""
import functools
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer

class LocalServer(ThreadingHTTPServer):
    def server_bind(self):
        TCPServer.server_bind(self)
        self.server_name = "localhost"
        self.server_port = self.server_address[1]

root=Path(tempfile.mkdtemp(prefix='fetch-browser-'))
media=root/'fixture';media.mkdir()
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=blue:s=160x90:r=10','-f','lavfi','-i','sine=frequency=440','-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(media/'authorized.mp4')],check=True)
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
source=LocalServer(('127.0.0.1',0),functools.partial(Handler,directory=str(media)))
threading.Thread(target=source.serve_forever,daemon=True).start()
os.environ.update(FETCH_DATA=str(root/'data'),FETCH_ADMIN_PASSWORD='browser-test-only-password-2026',FETCH_TEST_ORIGIN=f'127.0.0.1:{source.server_port}',FETCH_MIN_FREE='1048576')
(root/'data').mkdir()
# Public fixture location only, no credentials or user data.
Path('.qa').mkdir(exist_ok=True)
Path('.qa/media-url.txt').write_text(f'http://127.0.0.1:{source.server_port}/authorized.mp4')
worker=subprocess.Popen([sys.executable,'-m','fetch_server.worker'])
api=subprocess.Popen([sys.executable,'-m','uvicorn','fetch_server.api:app','--host','127.0.0.1','--port','8787','--no-access-log'])
def stop(*_):
    api.terminate();worker.terminate()
    api.wait(timeout=10);worker.wait(timeout=10)
    source.shutdown();source.server_close()
    shutil.rmtree(root,ignore_errors=True)
    Path(".qa/media-url.txt").unlink(missing_ok=True)
    sys.exit(0)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
print('Local QA dashboard: http://127.0.0.1:8787',flush=True)
api.wait()
stop()
