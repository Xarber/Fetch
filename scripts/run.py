# SPDX-License-Identifier: AGPL-3.0-only
import os
import shlex
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.chdir(root)
file=root/'.env'
if file.exists():
    for line in file.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        key,sep,value=line.partition('=')
        if sep:
            parts=shlex.split(value,comments=True)
            os.environ.setdefault(key.strip(),' '.join(parts))
os.environ.setdefault('FETCH_DATA',str(root/'data'))
mode=sys.argv[1] if len(sys.argv)>1 else 'api'
if mode=='api':
    import uvicorn
    uvicorn.run('fetch_server.api:app',host='127.0.0.1',port=8000,access_log=False)
elif mode=='worker':
    from fetch_server.worker import run
    run()
elif mode=='init':
    from fetch_server.api import initialize_admin
    initialize_admin()
    print('Database schema and initial administrator ready.')
else: raise SystemExit('Usage: python scripts/run.py [api|worker|init]')
