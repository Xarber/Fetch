# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from . import __version__
from .config import DATA, CONCURRENCY, RETENTION, MAX_BYTES, STORE_MODE, SOURCE_HOSTS
from .db import init, connect, job_dict, transition
from .models import Inspect, Selection, CreateJob, Batch, Login, Pair, Priority, Settings, Preset, PairStart
from .security import digest, validate_url, safe_name

hasher = PasswordHasher()
rate = defaultdict(deque)
inspection_slots = asyncio.Semaphore(2)

def initialize_admin():
    init()
    with connect() as db:
        if not db.execute('SELECT 1 FROM users').fetchone():
            password = os.getenv('FETCH_ADMIN_PASSWORD','')
            if len(password) < 14:
                raise RuntimeError('Set FETCH_ADMIN_PASSWORD to a unique password of at least 14 characters for initial setup')
            db.execute('INSERT INTO users VALUES(?,?)',('admin',hasher.hash(password)))

@asynccontextmanager
async def lifespan(app):
    initialize_admin()
    yield

app = FastAPI(title='Fetch',version=__version__,lifespan=lifespan)

@app.middleware('http')
async def guard(request: Request, call_next):
    if request.url.path.startswith('/api/'):
        # Bound unauthenticated request bodies and login/inspection pressure.
        try:
            length = int(request.headers.get('content-length','0'))
        except ValueError: length = 10**9
        if length > 128*1024 or request.headers.get('transfer-encoding'):
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail':'Request body too large or unbounded'},413)
        if request.url.path.endswith(('/login','/complete','/inspect')):
            key = (request.client.host,request.url.path)
            q = rate[key]; now = time.monotonic()
            while q and q[0] < now-60: q.popleft()
            if len(q) >= 15:
                from fastapi.responses import JSONResponse
                return JSONResponse({'detail':'Please retry in a minute'},429)
            q.append(now)
    response = await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    if request.url.path.startswith('/api/'): response.headers['Cache-Control']='no-store'
    else:
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https: http://localhost:* http://127.0.0.1:*; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    return response

def device(authorization: Annotated[str|None,Header()] = None):
    if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Authentication required')
    with connect() as db:
        row = db.execute('SELECT * FROM devices WHERE token=? AND expires>?',(digest(authorization[7:]),time.time())).fetchone()
    if not row: raise HTTPException(401,'Session expired or revoked')
    return dict(row)

def admin(d=Depends(device)):
    if not d['admin']: raise HTTPException(403,'Administrator permission required')
    return d

def own_job(job_id,d):
    with connect() as db: row = db.execute('SELECT * FROM jobs WHERE id=? AND owner=?',(job_id,d['owner'])).fetchone()
    if not row: raise HTTPException(404,'Download not found')
    return row

def issue_device(owner,name,is_admin=False):
    token = secrets.token_urlsafe(40); ident = str(uuid.uuid4()); expires=time.time()+30*86400
    with connect() as db:
        db.execute('INSERT INTO devices VALUES(?,?,?,?,?,?)',(ident,owner,name,digest(token),int(is_admin),expires))
    return dict(token=token,device_id=ident,expires=expires,admin=is_admin)

@app.get('/api/v1/health')
def health(): return {'status':'ok','api_version':1}

@app.post('/api/v1/auth/login')
def login(body: Login):
    with connect() as db: row = db.execute('SELECT * FROM users WHERE id=?',(body.username,)).fetchone()
    try:
        # Check a dummy hash for unknown users to avoid obvious account timing leaks.
        stored = row['password'] if row else hasher.hash('unused-password')
        hasher.verify(stored,body.password)
        if not row: raise VerificationError()
    except (VerificationError,InvalidHashError): raise HTTPException(401,'Invalid credentials')
    return issue_device(row['id'],body.device_name,True)

@app.post('/api/v1/auth/refresh')
def refresh(d=Depends(device)):
    new = issue_device(d['owner'],d['name'],bool(d['admin']))
    with connect() as db: db.execute('DELETE FROM devices WHERE id=?',(d['id'],))
    return new

@app.post('/api/v1/auth/logout',status_code=204)
def logout(d=Depends(device)):
    with connect() as db: db.execute('DELETE FROM devices WHERE id=?',(d['id'],))

@app.post('/api/v1/pairing/start')
def pair_start(body:PairStart|None=None,d=Depends(admin)):
    token = secrets.token_urlsafe(32); expires=time.time()+180
    with connect() as db: db.execute('INSERT INTO pairing VALUES(?,?,?)',(digest(token),d['owner'],expires))
    result = {'challenge':token,'expires':expires,'scope':'download-own-library'}
    if body and body.server_url:
        from urllib.parse import urlsplit, urlencode
        import base64
        import io
        import qrcode
        parsed = urlsplit(body.server_url)
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise HTTPException(422,'Invalid server URL')
        if parsed.scheme != 'https' and parsed.hostname not in ('localhost','127.0.0.1','::1'):
            raise HTTPException(422,'Pairing requires HTTPS for remote servers')
        payload = 'fetch://pair?' + urlencode({'server':body.server_url,'challenge':token})
        image = qrcode.make(payload)
        output = io.BytesIO(); image.save(output,format='PNG')
        result.update(pairing_url=payload,qr_data_uri='data:image/png;base64,'+base64.b64encode(output.getvalue()).decode())
    return result

@app.post('/api/v1/pairing/complete')
def pair_complete(body: Pair):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM pairing WHERE token=? AND expires>?',(digest(body.challenge),time.time())).fetchone()
        if not row: raise HTTPException(401,'Pairing challenge expired or already used')
        db.execute('DELETE FROM pairing WHERE token=?',(digest(body.challenge),))
    # A paired device shares the administrator personal library, without admin powers.
    return issue_device(row['owner'],body.device_name)

@app.get('/api/v1/devices')
def devices(d=Depends(admin)):
    with connect() as db: return [dict(r) for r in db.execute('SELECT id,name,admin,expires FROM devices WHERE owner=?',(d['owner'],))]

@app.delete('/api/v1/devices/{ident}',status_code=204)
def revoke(ident:str,d=Depends(admin)):
    with connect() as db: db.execute('DELETE FROM devices WHERE id=? AND owner=?',(ident,d['owner']))

@app.get('/api/v1/versions')
def versions(d=Depends(device)):
    import yt_dlp.version
    import importlib.metadata
    result = {'server':__version__,'python':sys.version.split()[0],'yt_dlp':yt_dlp.version.__version__,'api':1,'commit':os.getenv('FETCH_COMMIT','development')}
    for tool in ('ffmpeg','ffprobe','deno'):
        try: result[tool]=subprocess.check_output([tool,'-version' if tool != 'deno' else '--version'],timeout=5,text=True,stderr=subprocess.DEVNULL).splitlines()[0]
        except (OSError,subprocess.SubprocessError): result[tool]='unavailable'
    try: result['ejs']=importlib.metadata.version('yt-dlp-ejs')
    except importlib.metadata.PackageNotFoundError: result['ejs']='unavailable'
    return result

@app.get('/api/v1/capabilities')
def capabilities(d=Depends(device)):
    return {'presets':['best','compatible','small','audio','original','custom'], 'audio_formats':['original','m4a','mp3','opus','flac','wav'],
            'pause':'stop and restart using source partials when supported','playlist':False,'batch_limit':50,'store_mode':STORE_MODE,
            'authorized_sources':sorted(SOURCE_HOSTS),'max_bytes':MAX_BYTES,'api_version':1}

@app.get('/api/v1/status')
def status(d=Depends(device)):
    usage=shutil.disk_usage(DATA)
    with connect() as db:
        counts={r[0]:r[1] for r in db.execute('SELECT state,count(*) FROM jobs WHERE owner=? GROUP BY state',(d['owner'],))}
        beat=db.execute("SELECT value FROM settings WHERE key='worker_heartbeat'").fetchone()
    return {'worker_online':bool(beat and time.time()-float(beat[0])<10),'jobs':counts,'storage':{'free':usage.free,'total':usage.total}}

@app.post('/api/v1/media/inspect')
async def inspect(body:Inspect,d=Depends(device)):
    try: await asyncio.to_thread(validate_url,body.url)
    except ValueError as e: raise HTTPException(422,str(e))
    with connect() as db:
        if db.execute('SELECT count(*) FROM inspections WHERE owner=? AND created>?',(d['owner'],time.time()-60)).fetchone()[0]>=10:
            raise HTTPException(429,'Inspection quota exceeded')
    if inspection_slots.locked(): raise HTTPException(429,'Inspection capacity reached. Retry shortly.')
    await inspection_slots.acquire()
    try:
        return await run_inspection(body,d)
    finally:
        inspection_slots.release()

async def run_inspection(body,d):
    process = await asyncio.create_subprocess_exec(sys.executable,'-m','fetch_server.engine','inspect',body.url,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,start_new_session=True,env={**os.environ,'FETCH_PARENT_PID':str(os.getpid())})
    try:
        stdout,_ = await asyncio.wait_for(process.communicate(),60)
        result=json.loads(stdout)
        if process.returncode or 'error' in result: raise HTTPException(422,result.get('error','Inspection failed'))
    except asyncio.TimeoutError: raise HTTPException(504,'Inspection timed out')
    finally:
        if process.returncode is None:
            import signal
            try: os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            await process.wait()
    ident=str(uuid.uuid4())
    with connect() as db: db.execute('INSERT INTO inspections VALUES(?,?,?,?,?)',(ident,d['owner'],body.url,json.dumps(result),time.time()))
    return {'id':ident,**result}

@app.get('/api/v1/media/inspection/{ident}')
def inspection(ident:str,d=Depends(device)):
    with connect() as db: row=db.execute('SELECT * FROM inspections WHERE id=? AND owner=?',(ident,d['owner'])).fetchone()
    if not row: raise HTTPException(404,'Inspection not found')
    return {'id':ident,**json.loads(row['metadata'])}

def create(body,d,db):
    if not body.authorized: raise HTTPException(422,'Confirm that you are authorized to save this media')
    existing=db.execute('SELECT * FROM jobs WHERE owner=? AND request_key=?',(d['owner'],body.request_key)).fetchone()
    if existing: return job_dict(existing)
    inspection=db.execute('SELECT * FROM inspections WHERE id=? AND owner=?',(body.inspection_id,d['owner'])).fetchone()
    if not inspection: raise HTTPException(404,'Inspection not found')
    if db.execute("SELECT count(*) FROM jobs WHERE owner=? AND state IN ('queued','downloading','postprocessing','paused')",(d['owner'],)).fetchone()[0]>=100:
        raise HTTPException(429,'Queue limit reached')
    formats={f['format_id'] for f in json.loads(inspection['metadata'])['formats']}
    if body.selection.preset=='custom' and (not body.selection.format_id or body.selection.format_id not in formats): raise HTTPException(422,'Choose an available format ID')
    if body.selection.audio_id and body.selection.audio_id not in formats: raise HTTPException(422,'Unknown audio stream')
    ident=str(uuid.uuid4()); now=time.time()
    db.execute('INSERT INTO jobs(id,owner,inspection,title,selection,state,priority,created,updated,request_key) VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,d['owner'],inspection['id'],json.loads(inspection['metadata'])['title'],body.selection.model_dump_json(),'queued',body.priority,now,now,body.request_key))
    return job_dict(db.execute('SELECT * FROM jobs WHERE id=?',(ident,)).fetchone())

@app.post('/api/v1/downloads',status_code=201)
def create_job(body:CreateJob,d=Depends(device)):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE'); return create(body,d,db)

@app.post('/api/v1/batches',status_code=201)
def batch(body:Batch,d=Depends(device)):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE'); return {'jobs':[create(b,d,db) for b in body.jobs]}

@app.get('/api/v1/downloads')
def jobs(d=Depends(device)):
    with connect() as db: return [job_dict(r) for r in db.execute('SELECT * FROM jobs WHERE owner=? ORDER BY priority DESC,created DESC LIMIT 1000',(d['owner'],))]

@app.get('/api/v1/downloads/{ident}')
def job(ident:str,d=Depends(device)): return job_dict(own_job(ident,d))

@app.post('/api/v1/downloads/{ident}/{action}')
def action(ident:str,action:str,d=Depends(device)):
    row=own_job(ident,d)
    if action=='transfer':
        if row['state']!='ready': raise HTTPException(409,'File is not ready')
        token=secrets.token_urlsafe(40); transfer=str(uuid.uuid4()); expires=time.time()+6*3600
        with connect() as db: db.execute('INSERT INTO transfers(id,owner,device,job,secret,expires) VALUES(?,?,?,?,?,?)',(transfer,d['owner'],d['id'],ident,digest(token),expires))
        return {'id':transfer,'token':token,'path':f'/api/v1/transfers/{transfer}/file','expires':expires,'size':row['size'],'sha256':row['sha256'],'filename':safe_name(row['title'])+Path(row['file']).suffix}
    if action in ('resume','retry') and row['running']: raise HTTPException(409,'Worker is still stopping. Retry shortly.')
    targets={'cancel':'cancelled','retry':'queued','resume':'queued','pause':'paused' if row['state']=='queued' else 'pausing'}
    if action not in targets: raise HTTPException(404,'Unsupported action')
    if action in ('resume','retry') and row['state'] not in ('paused','failed','cancelled'): raise HTTPException(409,'Job cannot restart in this state')
    if action=='pause' and row['state'] not in ('queued','downloading'): raise HTTPException(409,'Only queued/downloading jobs can pause')
    if not transition(ident,targets[action],error=None): raise HTTPException(409,'Operation unavailable in current state')
    return job_dict(own_job(ident,d))

@app.patch('/api/v1/downloads/{ident}')
def priority(ident:str,body:Priority,d=Depends(device)):
    row=own_job(ident,d)
    if row['state']!='queued': raise HTTPException(409,'Only queued jobs can be reordered')
    transition(ident,'queued',priority=body.priority)
    return job_dict(own_job(ident,d))

@app.delete('/api/v1/downloads/{ident}',status_code=204)
def delete(ident:str,d=Depends(device)):
    row=own_job(ident,d)
    if row['running'] or row['state'] not in ('ready','failed','cancelled','paused','expired'): raise HTTPException(409,'Stop the job before removing it')
    shutil.rmtree(DATA/'jobs'/ident,ignore_errors=True)
    with connect() as db: db.execute('DELETE FROM jobs WHERE id=?',(ident,))

@app.head('/api/v1/transfers/{ident}/file')
@app.get('/api/v1/transfers/{ident}/file')
def file(ident:str,authorization:Annotated[str|None,Header()]=None):
    if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Transfer authorization required')
    with connect() as db:
        row=db.execute('SELECT t.*,j.file,j.title,j.size,j.sha256,j.state FROM transfers t JOIN jobs j ON j.id=t.job WHERE t.id=? AND t.secret=? AND t.expires>?',(ident,digest(authorization[7:]),time.time())).fetchone()
    if not row or row['state']!='ready': raise HTTPException(401,'Transfer expired, revoked or unavailable')
    path=(DATA/row['file']).resolve()
    if not path.is_relative_to(DATA/'jobs') or not path.is_file(): raise HTTPException(410,'File unavailable')
    return FileResponse(path,filename=safe_name(row['title'])+path.suffix,headers={'ETag':'"'+row['sha256']+'"','Cache-Control':'private, no-store'})

@app.post('/api/v1/transfers/{ident}/complete')
def complete(ident:str,body:dict,d=Depends(device)):
    with connect() as db:
        row=db.execute('SELECT t.*,j.sha256 FROM transfers t JOIN jobs j ON j.id=t.job WHERE t.id=? AND t.owner=? AND t.expires>?',(ident,d['owner'],time.time())).fetchone()
        if not row: raise HTTPException(404,'Transfer not found')
        if body.get('sha256')!=row['sha256']: raise HTTPException(422,'Checksum mismatch')
        db.execute('UPDATE transfers SET completed=1 WHERE id=?',(ident,))
    return {'verified':True}

@app.get('/api/v1/events')
async def events(request:Request,d=Depends(device)):
    async def stream():
        previous={}
        while not await request.is_disconnected():
            # Session revocation affects existing streams too.
            with connect() as db:
                if not db.execute('SELECT 1 FROM devices WHERE id=? AND expires>?',(d['id'],time.time())).fetchone(): return
                rows=db.execute('SELECT * FROM jobs WHERE owner=? ORDER BY created',(d['owner'],)).fetchall()
            for row in rows:
                if previous.get(row['id'])!=row['version']:
                    previous[row['id']]=row['version']
                    yield 'id: '+row['id']+':'+str(row['version'])+'\nevent: job.updated\ndata: '+json.dumps(job_dict(row))+'\n\n'
            yield ': heartbeat\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(stream(),media_type='text/event-stream')

@app.get('/api/v1/presets')
def presets(d=Depends(device)):
    with connect() as db: return [{**dict(r),'selection':json.loads(r['selection'])} for r in db.execute('SELECT * FROM presets WHERE owner=?',(d['owner'],))]

@app.post('/api/v1/presets',status_code=201)
def preset(body:Preset,d=Depends(device)):
    ident=str(uuid.uuid4())
    with connect() as db: db.execute('INSERT INTO presets VALUES(?,?,?,?)',(ident,d['owner'],body.name,body.selection.model_dump_json()))
    return {'id':ident}

@app.get('/api/v1/admin/engine')
def engine(d=Depends(admin)): return versions(d)

@app.get('/api/v1/admin/storage')
def storage(d=Depends(admin)):
    usage=shutil.disk_usage(DATA)
    return {'free':usage.free,'total':usage.total,'media_bytes':sum(p.stat().st_size for p in (DATA/'jobs').rglob('*') if p.is_file())}

@app.get('/api/v1/admin/settings')
def get_settings(d=Depends(admin)):
    with connect() as db: settings={r['key']:json.loads(r['value']) for r in db.execute("SELECT * FROM settings WHERE key IN ('concurrency','retention_hours')")}
    return {'concurrency':settings.get('concurrency',CONCURRENCY),'retention_hours':settings.get('retention_hours',RETENTION)}

@app.patch('/api/v1/admin/settings')
def settings(body:Settings,d=Depends(admin)):
    with connect() as db:
        for k,v in body.model_dump().items(): db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(k,json.dumps(v)))
    return body

web = Path(os.getenv('FETCH_WEB',str(Path(__file__).resolve().parents[2]/'web')))
if web.is_dir(): app.mount('/',StaticFiles(directory=web,html=True),name='dashboard')
