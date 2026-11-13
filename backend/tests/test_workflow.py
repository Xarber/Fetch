# SPDX-License-Identifier: AGPL-3.0-only
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from fetch_server.db import connect, transition
from fetch_server.security import safe_name, validate_url, start_proxy
import httpx
import pytest

@pytest.mark.parametrize('url',['file:///etc/passwd','http://127.0.0.1','http://[::1]','http://10.0.0.1','http://169.254.169.254','http://2130706433','http://user:pass@example.com','ftp://example.com','http://localhost','http://example.com:22'])
def test_unsafe_urls(url):
    with pytest.raises(ValueError): validate_url(url)

def test_auth(client):
    assert client.get('/api/v1/downloads').status_code==401
    assert client.post('/api/v1/auth/login',json={'username':'admin','password':'wrong'}).status_code==401

def test_pairing(client,auth):
    start=client.post('/api/v1/pairing/start',headers=auth).json()
    pair=client.post('/api/v1/pairing/complete',json={'challenge':start['challenge'],'device_name':'test iPhone'})
    assert pair.status_code==200
    device={'Authorization':'Bearer '+pair.json()['token']}
    assert client.get('/api/v1/admin/settings',headers=device).status_code==403
    assert client.post('/api/v1/pairing/complete',json={'challenge':start['challenge'],'device_name':'replay'}).status_code==401
    ident=pair.json()['device_id']
    assert client.delete('/api/v1/devices/'+ident,headers=auth).status_code==204
    assert client.get('/api/v1/downloads',headers=device).status_code==401

def test_redirect_blocked(media_url):
    proxy,address=start_proxy()
    try:
        with httpx.Client(proxy=address,follow_redirects=True,trust_env=False) as h:
            response=h.get(media_url.replace('authorized.mp4','redirect'))
            assert response.status_code==403
    finally: proxy.shutdown(); proxy.server_close()

def test_dns_rebinding_pin(monkeypatch):
    from fetch_server.security import resolve
    import socket
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',80))])
    with pytest.raises(ValueError): resolve('public-looking.example',80)

def test_lifecycle(client,auth,media_url):
    inspected=client.post('/api/v1/media/inspect',json={'url':media_url},headers=auth)
    assert inspected.status_code==200,inspected.text
    info=inspected.json(); assert info['formats']
    def create(selection):
        body={'inspection_id':info['id'],'authorized':True,'request_key':str(uuid.uuid4()),'selection':selection}
        r=client.post('/api/v1/downloads',json=body,headers=auth)
        assert r.status_code==201,r.text
        duplicate=client.post('/api/v1/downloads',json=body,headers=auth)
        assert duplicate.json()['id']==r.json()['id']
        return r.json()['id']
    video=create({'preset':'original'})
    audio=create({'preset':'audio','audio_format':'mp3'})
    worker=subprocess.Popen([sys.executable,'-m','fetch_server.worker'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+50
        while time.monotonic()<deadline:
            records=[client.get('/api/v1/downloads/'+j,headers=auth).json() for j in (video,audio)]
            states=[r['state'] for r in records]
            if all(s in ('ready','failed') for s in states) and not any(r['running'] for r in records): break
            time.sleep(.2)
        assert states==['ready','ready'],(states,worker.poll())
        for ident in (video,audio):
            r=client.post('/api/v1/downloads/'+ident+'/transfer',headers=auth)
            assert r.status_code==200,r.text
            transfer=r.json(); headers={'Authorization':'Bearer '+transfer['token']}
            assert client.get(transfer['path']).status_code==401
            assert client.get(transfer['path'],headers=auth).status_code==401
            file=client.get(transfer['path'],headers=headers)
            assert file.status_code==200
            assert hashlib.sha256(file.content).hexdigest()==transfer['sha256']
            partial=client.get(transfer['path'],headers={**headers,'Range':'bytes=0-99'})
            assert partial.status_code==206
            assert partial.content==file.content[:100]
            assert client.post('/api/v1/transfers/'+transfer['id']+'/complete',json={'sha256':transfer['sha256']},headers=auth).status_code==200
            with connect() as db: db.execute('UPDATE transfers SET expires=0 WHERE id=?',(transfer['id'],))
            assert client.get(transfer['path'],headers=headers).status_code==401
            assert client.delete('/api/v1/downloads/'+ident,headers=auth).status_code==204
    finally:
        worker.terminate()
        worker.communicate(timeout=10)
    bad={'inspection_id':info['id'],'authorized':True,'request_key':str(uuid.uuid4()),'selection':{'preset':'custom','format_id':'999999'}}
    assert client.post('/api/v1/downloads',json=bad,headers=auth).status_code==422
    bad['selection']={'preset':'custom','format_id':'$(whoami)'}
    assert client.post('/api/v1/downloads',json=bad,headers=auth).status_code==422
    bad['selection']={'preset':'best','exec':'touch /tmp/injection'}
    assert client.post('/api/v1/downloads',json=bad,headers=auth).status_code==422
    assert client.get('/api/v1/downloads/../../etc/passwd',headers=auth).status_code!=200

def test_safe_filename():
    assert '/' not in safe_name('../../etc/passwd')
    assert safe_name('...')=='media'

def test_state_transition():
    assert not transition('missing','ready')
