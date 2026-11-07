# SPDX-License-Identifier: AGPL-3.0-only
from fetch_server.updates import compatible,version_key,check_updates
import pytest

def manifest(**fields):
    return dict(schema_version=1,application='org.openrecode.fetch',version='1.0.0',build=2,published=True,distribution='extended',channel='stable',commit='a'*40,artifacts=[{'name':'Fetch.ipa','size':1,'sha256':'a'*64},{'name':'Fetch.app.zip','size':1,'sha256':'b'*64}],**fields)

def test_release_numeric_order_and_builds():
    assert version_key('1.10.0',1)>version_key('1.9.0',999)
    assert compatible(manifest(),'1.0.0',1,'stable','extended')
    assert not compatible(manifest(),'1.0.0',2,'stable','extended')
    assert not compatible(manifest(),'2.0.0',1,'stable','extended')

@pytest.mark.parametrize(('key','value'),[('published',False),('application','other'),('distribution','store'),('channel','beta'),('commit','invalid'),('version','invalid'),('artifacts',[])])
def test_rejects_incomplete_incompatible_releases(key,value):
    data=manifest();data[key]=value
    assert not compatible(data,'0.1.0',1,'stable','extended')

def test_unconfigured_is_honest(monkeypatch):
    monkeypatch.delenv('FETCH_RELEASE_REPOSITORY',raising=False)
    result=check_updates('0.1.0',1,'stable','extended')
    assert result['status']=='unconfigured' and result['candidate'] is None

def test_rejects_newer_required_os():
    data=manifest();data['minimum_ios']='27.0'
    assert not compatible(data,'0.1.0',1,'stable','extended','17.0')
    assert compatible(data,'0.1.0',1,'stable','extended','27.0')

def test_updates_route_authentication_and_unconfigured_state(client,auth,monkeypatch):
    monkeypatch.delenv('FETCH_RELEASE_REPOSITORY',raising=False)
    assert client.get('/api/v1/updates').status_code==401
    response=client.get('/api/v1/updates',headers=auth)
    assert response.status_code==200
    assert response.json()['status']=='unconfigured'
    assert client.get('/api/v1/updates?channel=unknown',headers=auth).status_code==422

def test_source_offer_does_not_expose_unprepared_paths(client,auth,monkeypatch,tmp_path):
    monkeypatch.setenv('FETCH_SOURCE_ARCHIVE',str(tmp_path/'missing.tar.gz'))
    assert client.get('/api/v1/source').status_code==401
    assert client.get('/api/v1/source',headers=auth).status_code==503
