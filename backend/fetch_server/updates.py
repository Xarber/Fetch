# SPDX-License-Identifier: AGPL-3.0-only
"""Server-side GitHub metadata bridge. Client applications never receive GitHub tokens."""
import os
import re
import threading
import time
from urllib.parse import quote
import requests

_lock=threading.Lock()
_cache={}
_failures={}

def version_key(version,build):
    match=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)',version)
    if not match or not isinstance(build,int) or build<0:raise ValueError('Invalid release version/build')
    return tuple(int(v) for v in match.groups())+(build,)

def compatible(manifest,installed,build,channel,variant,os_version="17.0"):
    def os_key(value):
        if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?",value):raise ValueError("Invalid OS version")
        return tuple((list(map(int,value.split(".")))+[0,0,0])[:3])
    try:
        return (manifest.get('schema_version')==1 and manifest.get('application')=='org.openrecode.fetch'
            and manifest.get('published') is True and manifest.get('distribution')==variant
            and manifest.get('channel') in (['stable','beta'] if channel=='beta' else ['stable'])
            and version_key(manifest['version'],manifest['build'])>version_key(installed,build)
            and re.fullmatch(r'[a-f0-9]{40}',manifest.get('commit','')) is not None
            and os_key(manifest.get('minimum_ios','17.0'))<=os_key(os_version)
            and isinstance(manifest.get('artifacts'),list)
            and all(isinstance(a,dict) for a in manifest['artifacts'])
            and any(a.get('name','').endswith('.ipa') for a in manifest['artifacts'])
            and any(a.get('name','').endswith('.app.zip') for a in manifest['artifacts'])
            and all(isinstance(a.get('size'),int) and a['size']>0 and re.fullmatch(r'[a-f0-9]{64}',a.get('sha256','')) for a in manifest['artifacts']))
    except (ValueError,KeyError,TypeError,AttributeError):return False

def release_candidates(channel):
    repository=os.getenv('FETCH_RELEASE_REPOSITORY','')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository):return 'unconfigured',[]
    with _lock:
        previous=_cache.get((repository,channel))
        if previous and time.time()-previous[0]<3600:return previous[1],previous[2]
        if time.time()-_failures.get((repository,channel),0)<60:return ('stale',previous[2]) if previous else ('unavailable',[])
        headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'OpenRecode-Fetch'}
        secret=os.getenv('FETCH_RELEASE_TOKEN','')
        if secret:headers['Authorization']='Bearer '+secret
        session=requests.Session();session.headers.update(headers)
        try:
            response=session.get(f'https://api.github.com/repos/{repository}/releases',params={'per_page':30},timeout=10)
            response.raise_for_status()
            if len(response.content)>2_000_000:raise ValueError('Oversized release list')
            results=[]
            inspected=0
            for release in response.json():
                if release.get('draft') or (release.get('prerelease') and channel!='beta') or str(release.get('tag_name','')).startswith(('sources-','metadata-')):continue
                asset=next((a for a in release.get('assets',[]) if a.get('name')=='release-manifest.json'),None)
                if not asset or not isinstance(asset.get('id'),int) or asset.get('size',0)>128*1024:continue
                if inspected>=3:break
                inspected+=1
                # Canonical API URL; never follow arbitrary asset URLs from a manifest.
                result=session.get(f'https://api.github.com/repos/{repository}/releases/assets/{asset["id"]}',headers={'Accept':'application/octet-stream'},timeout=10)
                result.raise_for_status()
                if len(result.content)>128*1024:continue
                manifest=result.json()
                if not isinstance(manifest,dict):continue
                manifest['release_url']=f'https://github.com/{repository}/releases/tag/{quote(str(release["tag_name"]),safe="")}'
                results.append(manifest)
                if len(results)>=10:break
            state='available' if results else 'no_releases'
            _cache[(repository,channel)]=(time.time(),state,results)
            return state,results
        except (requests.RequestException,ValueError,KeyError,TypeError):
            _failures[(repository,channel)]=time.time()
            # Never replace valid cached metadata with an invalid/failed fetch.
            if previous:return 'stale',previous[2]
            return 'unavailable',[]
        finally:session.close()

def check_updates(installed,build,channel,variant,os_version="17.0"):
    state,candidates=release_candidates(channel)
    compatible_candidates=[m for m in candidates if compatible(m,installed,build,channel,variant,os_version)]
    newest=max(compatible_candidates,key=lambda m:version_key(m['version'],m['build']),default=None)
    result={'status':state,'checked_at':time.time(),'candidate':None}
    if newest:
        # Expose safe user-facing metadata only, never repository credentials.
        result['candidate']={k:newest.get(k) for k in ['version','build','channel','release_url','highlights','fixes','minimum_ios','distribution','commit']}
        if state!='stale':result['status']='update_available'
    elif state=='available':result['status']='up_to_date'
    return result
