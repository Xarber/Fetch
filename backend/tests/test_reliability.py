# SPDX-License-Identifier: AGPL-3.0-only
import json
import os
import signal
import subprocess
import sys
import time
import uuid
import pytest
from fetch_server.api import issue_device
from fetch_server.db import connect,transition
from fetch_server.engine import selector

@pytest.mark.parametrize(('selection','expected'),[
    ({'preset':'audio','audio_format':'mp3'},'bestaudio/best'),
    ({'preset':'best','audio_format':'original'},'bestvideo+bestaudio/best'),
    ({'preset':'custom','format_id':'137','audio_id':'140'},'137+140'),
])
def test_typed_selection(selection,expected): assert selector(selection)==expected

def make_job(client,auth,media_url):
    info=client.post('/api/v1/media/inspect',headers=auth,json={'url':media_url}).json()
    response=client.post('/api/v1/downloads',headers=auth,json={'inspection_id':info['id'],'authorized':True,'request_key':str(uuid.uuid4()),'selection':{'preset':'original'}})
    assert response.status_code==201,response.text
    return response.json()['id']

def test_ownership_and_state_machine(client,auth,media_url):
    ident=make_job(client,auth,media_url)
    other=issue_device('other-owner','other-library')
    headers={'Authorization':'Bearer '+other['token']}
    assert client.get('/api/v1/downloads/'+ident,headers=headers).status_code==404
    assert client.post('/api/v1/downloads/'+ident+'/transfer',headers=headers).status_code==404
    assert not transition(ident,'ready')
    assert client.post('/api/v1/downloads/'+ident+'/resume',headers=auth).status_code==409
    assert client.post('/api/v1/downloads/'+ident+'/pause',headers=auth).json()['state']=='paused'
    assert client.post('/api/v1/downloads/'+ident+'/resume',headers=auth).json()['state']=='queued'
    assert client.post('/api/v1/downloads/'+ident+'/cancel',headers=auth).json()['state']=='cancelled'
    with connect() as db: db.execute('UPDATE jobs SET running=1 WHERE id=?',(ident,))
    assert client.post('/api/v1/downloads/'+ident+'/retry',headers=auth).status_code==409
    assert client.delete('/api/v1/downloads/'+ident,headers=auth).status_code==409
    with connect() as db: db.execute('UPDATE jobs SET running=0 WHERE id=?',(ident,))
    assert client.delete('/api/v1/downloads/'+ident,headers=auth).status_code==204

def test_restart_recovery(client,auth,media_url):
    ident=make_job(client,auth,media_url)
    # Simulate durable state left by an exited worker, then use a real new worker.
    assert transition(ident,'downloading',running=1)
    worker=subprocess.Popen([sys.executable,'-m','fetch_server.worker'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            job=client.get('/api/v1/downloads/'+ident,headers=auth).json()
            if job['state']=='ready' and not job['running']: break
            time.sleep(.2)
        assert job['state']=='ready',job
    finally: worker.terminate();worker.wait(timeout=10)
    assert client.delete('/api/v1/downloads/'+ident,headers=auth).status_code==204

def test_invalid_pairing_and_expiry(client,auth):
    assert client.post('/api/v1/pairing/complete',json={'challenge':'invalid','device_name':'bad'}).status_code==401
    start=client.post('/api/v1/pairing/start',headers=auth).json()
    with connect() as db: db.execute('UPDATE pairing SET expires=0')
    assert client.post('/api/v1/pairing/complete',json={'challenge':start['challenge'],'device_name':'expired'}).status_code==401

def test_untrusted_plugins_disabled(tmp_path,media_url):
    plugin=tmp_path/'yt_dlp_plugins'/'extractor';plugin.mkdir(parents=True)
    marker=tmp_path/'executed'
    (plugin/'bad.py').write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
    env={**os.environ,'PYTHONPATH':str(tmp_path)}
    process=subprocess.run([sys.executable,'-m','fetch_server.engine','inspect',media_url],env=env,capture_output=True,text=True,timeout=30)
    assert process.returncode==0,process.stdout
    assert not marker.exists()

def test_qr_pairing_payload(client,auth):
    import base64
    from urllib.parse import urlsplit,parse_qs
    response=client.post('/api/v1/pairing/start',headers=auth,json={'server_url':'https://fetch.example.com'})
    assert response.status_code==200,response.text
    payload=response.json()
    query=parse_qs(urlsplit(payload['pairing_url']).query)
    assert query['challenge']==[payload['challenge']]
    assert query['server']==['https://fetch.example.com']
    assert base64.b64decode(payload['qr_data_uri'].split(',')[1]).startswith(b'\x89PNG')
    assert client.post('/api/v1/pairing/start',headers=auth,json={'server_url':'http://untrusted.example.com'}).status_code==422

def test_source_policy_fail_closed(monkeypatch):
    from fetch_server import security
    monkeypatch.setattr(security,'STORE_MODE',True)
    monkeypatch.setattr(security,'SOURCE_HOSTS',set())
    with pytest.raises(ValueError):security.validate_url('https://example.com/video.mp4')

def test_revoked_device_revokes_file_capability(client,auth,media_url,tmp_path):
    from fetch_server.config import DATA
    ident=make_job(client,auth,media_url)
    folder=DATA/'jobs'/ident;folder.mkdir(parents=True,exist_ok=True)
    artifact=folder/'media.mp4';artifact.write_bytes(b'test-artifact-not-media')
    assert transition(ident,'downloading')
    assert transition(ident,'ready',file=str(artifact.relative_to(DATA)),size=artifact.stat().st_size,sha256='test')
    paired=issue_device('admin','temporary transfer device')
    headers={'Authorization':'Bearer '+paired['token']}
    ticket=client.post('/api/v1/downloads/'+ident+'/transfer',headers=headers).json()
    capability={'Authorization':'Bearer '+ticket['token']}
    assert client.head(ticket['path'],headers=capability).status_code==200
    assert client.delete('/api/v1/devices/'+paired['device_id'],headers=auth).status_code==204
    assert client.get(ticket['path'],headers=capability).status_code==401
    assert client.delete('/api/v1/downloads/'+ident,headers=auth).status_code==204

def test_oversized_download_fails_without_artifact(client,auth,media_url):
    ident=make_job(client,auth,media_url)
    env={**os.environ,'FETCH_MAX_BYTES':'1'}
    worker=subprocess.Popen([sys.executable,'-m','fetch_server.worker'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            job=client.get('/api/v1/downloads/'+ident,headers=auth).json()
            if job['state']=='failed' and not job['running']:break
            time.sleep(.2)
        assert job['state']=='failed',job
        assert client.post('/api/v1/downloads/'+ident+'/transfer',headers=auth).status_code==409
    finally:worker.terminate();worker.wait(timeout=10)
    assert client.delete('/api/v1/downloads/'+ident,headers=auth).status_code==204

@pytest.mark.parametrize('source',['https://example.com/video','rtmp://example.com/live','file:///etc/passwd','concat:http://127.0.0.1/internal'])
def test_ffmpeg_remote_fallback_is_blocked(source,tmp_path):
    from fetch_server.ffmpeg_guard import guarded_arguments
    with pytest.raises(ValueError):guarded_arguments('ffmpeg',['-i',source,'out.mp4'],tmp_path)

def test_ffmpeg_cannot_override_local_protocol_policy(tmp_path):
    from fetch_server.ffmpeg_guard import guarded_arguments
    media=tmp_path/'source.mp4'
    args=guarded_arguments('ffmpeg',['-protocol_whitelist','http,https,tcp','-i',str(media),'out.mp4'],tmp_path)
    assert 'http,https,tcp' not in args
    assert args[:3]==['-protocol_whitelist','file,pipe,crypto,data','-i']

def test_compatible_video_actually_transcodes(client,auth,incompatible_media_url,tmp_path):
    info=client.post('/api/v1/media/inspect',headers=auth,json={'url':incompatible_media_url}).json()
    response=client.post('/api/v1/downloads',headers=auth,json={'inspection_id':info['id'],'authorized':True,'request_key':str(uuid.uuid4()),'selection':{'preset':'compatible'}})
    assert response.status_code==201,response.text
    ident=response.json()['id']
    worker=subprocess.Popen([sys.executable,'-m','fetch_server.worker'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            job=client.get('/api/v1/downloads/'+ident,headers=auth).json()
            if job['state'] in ('ready','failed') and not job['running']:break
            time.sleep(.2)
        assert job['state']=='ready',job
        ticket=client.post('/api/v1/downloads/'+ident+'/transfer',headers=auth).json()
        payload=client.get(ticket['path'],headers={'Authorization':'Bearer '+ticket['token']})
        assert payload.status_code==200
        output=tmp_path/'compatible.mp4';output.write_bytes(payload.content)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)],text=True))
        assert {s['codec_name'] for s in probe['streams']}=={'h264','aac'}
    finally:worker.terminate();worker.wait(timeout=10)
    assert client.delete('/api/v1/downloads/'+ident,headers=auth).status_code==204

def test_encoded_bootstrap_preserves_password_characters(tmp_path):
    import base64
    import sqlite3
    from argon2 import PasswordHasher
    password="a unique 'quoted' $password #2026"
    env={**os.environ,'FETCH_DATA':str(tmp_path),'FETCH_ADMIN_PASSWORD':'','FETCH_ADMIN_PASSWORD_B64':base64.b64encode(password.encode()).decode()}
    subprocess.run([sys.executable,'-c','from fetch_server.api import initialize_admin; initialize_admin()'],env=env,check=True,capture_output=True,timeout=20)
    with sqlite3.connect(tmp_path/'fetch.sqlite3') as db: stored=db.execute('SELECT password FROM users WHERE id=?',('admin',)).fetchone()[0]
    assert PasswordHasher().verify(stored,password)
