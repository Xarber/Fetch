# SPDX-License-Identifier: AGPL-3.0-only
"""Short-lived, supervised extraction/download process. No shell or user arguments."""
import hashlib
import json
import os
import sys
import time
import threading
import signal
import subprocess
from pathlib import Path
from .config import DATA, MAX_BYTES
from .db import connect, transition
from .security import start_proxy, validate_url

# Upstream-supported switch; the Python API does not honor a plugin_dirs option.
os.environ["YTDLP_NO_PLUGINS"] = "1"

def supervise_parent():
    parent = os.getppid()
    def watch():
        while True:
            time.sleep(.25)
            if os.getppid() != parent:
                os.killpg(os.getpgrp(), signal.SIGKILL)
    threading.Thread(target=watch, daemon=True).start()

class QuietLogger:
    def debug(self,*args): pass
    def warning(self,*args): pass
    def error(self,*args): pass

def options(proxy):
    return dict(proxy=proxy, socket_timeout=20, retries=3, fragment_retries=3,
                noplaylist=True, quiet=True, no_warnings=True, logger=QuietLogger(),
                max_filesize=MAX_BYTES, cachedir=False, plugin_dirs=[],
                remote_components=set(), js_runtimes={'deno': {}},
                enable_file_urls=False, hls_prefer_native=True,
                external_downloader={'m3u8':'native','dash':'native'},
                # FFmpeg must only process local files; never fetch remote manifests.
                postprocessor_args={'ffmpeg_i':['-protocol_whitelist','file,pipe,crypto,data']})

def summarize(info):
    keys = ['format_id','ext','vcodec','acodec','width','height','fps','tbr','abr','audio_channels','dynamic_range','filesize','filesize_approx','format_note','protocol']
    formats = []
    for f in info.get('formats') or [info]:
        if f.get('has_drm') or f.get('protocol') not in ('http','https','m3u8_native','http_dash_segments'):
            continue
        formats.append({k:f.get(k) for k in keys})
    return dict(title=info.get('title') or 'Untitled media', creator=info.get('uploader'),
                duration=info.get('duration'),thumbnail=info.get('thumbnail'),
                source=info.get('extractor_key'), description=(info.get('description') or '')[:8000],
                upload_date=info.get('upload_date'),formats=formats,chapters=info.get('chapters') or [],
                subtitles=list((info.get('subtitles') or {}).keys()))

def selector(selection):
    p = selection['preset']
    if p == 'custom': return selection['format_id'] + ('+'+selection['audio_id'] if selection.get('audio_id') else '')
    if p == 'audio' or selection['audio_format'] != 'original': return 'bestaudio/best'
    return {'compatible':'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[ext=mp4]/best',
            'small':'worst[height>=360]/worst', 'best':'bestvideo+bestaudio/best', 'original':'bestvideo+bestaudio/best'}[p]

def inspect(url):
    import yt_dlp
    validate_url(url)
    server, proxy = start_proxy()
    try:
        with yt_dlp.YoutubeDL(options(proxy)) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get('_type') in ('playlist','multi_video'):
                raise ValueError('Playlist URL: import individual authorized item URLs as a batch')
            if info.get('is_live'): raise ValueError('Live streams are not supported')
            return summarize(info)
    finally:
        server.shutdown(); server.server_close()

def download(job_id):
    import yt_dlp
    with connect() as db:
        row = db.execute('SELECT j.*,i.url FROM jobs j JOIN inspections i ON i.id=j.inspection WHERE j.id=?',(job_id,)).fetchone()
    validate_url(row['url'])
    selection = json.loads(row['selection'])
    folder = DATA / 'jobs' / job_id
    folder.mkdir(parents=True,exist_ok=True)
    server, proxy = start_proxy()
    last = 0
    def progress(d):
        nonlocal last
        if time.monotonic()-last < .4 and d['status'] != 'finished': return
        last = time.monotonic()
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        payload = {'downloaded_bytes':d.get('downloaded_bytes'), 'total_bytes':total,
                   'total_estimated':not bool(d.get('total_bytes')), 'speed':d.get('speed'),
                   'eta':d.get('eta'), 'format_id':d.get('info_dict',{}).get('format_id'),'stage':'downloading'}
        transition(job_id, 'downloading',progress=json.dumps(payload))
    def post(d):
        transition(job_id,'postprocessing',progress=json.dumps({'stage':d.get('postprocessor','Processing')}))
    opts = options(proxy)
    opts.update(format=selector(selection),outtmpl=str(folder/'source.%(ext)s'),
                progress_hooks=[progress],postprocessor_hooks=[post],
                merge_output_format='mkv' if selection['preset'] in ('best','original') else 'mp4',
                writesubtitles=selection['subtitles'],subtitleslangs=['en'],
                postprocessors=[])
    if selection['audio_format'] != 'original':
        opts['postprocessors'].append({'key':'FFmpegExtractAudio','preferredcodec':selection['audio_format'],'preferredquality':str(selection['bitrate'])})
    elif selection['preset'] == 'audio':
        opts['postprocessors'].append({'key':'FFmpegExtractAudio','preferredcodec':'best'})
    if selection['embed_metadata']:
        opts['postprocessors'].append({'key':'FFmpegMetadata'})
    if selection['subtitles']:
        opts['postprocessors'].append({'key':'FFmpegEmbedSubtitle'})
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(row['url'], download=True)
        outputs = [p for p in folder.glob('source.*') if p.suffix.lower() in ('.mp4','.mkv','.webm','.m4a','.mp3','.opus','.ogg','.flac','.wav','.mov','.aac')]
        if len(outputs) != 1: raise ValueError('Expected one finalized media artifact')
        output = outputs[0]
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-protocol_whitelist','file,pipe','-show_streams','-show_format','-of','json',str(output)],timeout=20))
        streams = probe.get('streams',[])
        if not streams: raise ValueError('No playable media stream')
        if selection['preset'] == 'compatible' and selection['audio_format'] == 'original':
            video = next((s for s in streams if s.get('codec_type') == 'video'),None)
            audio = next((s for s in streams if s.get('codec_type') == 'audio'),None)
            if video and (output.suffix != '.mp4' or video.get('codec_name') != 'h264' or (audio and audio.get('codec_name') != 'aac')):
                transition(job_id,'postprocessing',progress=json.dumps({'stage':'Converting to H.264/AAC'}))
                converted = folder/'converted.mp4'
                subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-protocol_whitelist','file,pipe','-i',str(output),'-map','0:v:0','-map','0:a:0?','-map_metadata','0','-c:v','libx264','-threads','2','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(converted)],check=True)
                output.unlink()
                output = converted
        if output.stat().st_size > MAX_BYTES: raise ValueError('Output exceeds quota')
        with output.open('rb') as source:
            checksum = hashlib.file_digest(source,'sha256').hexdigest()
        final = folder / ('media' + output.suffix)
        os.replace(output, final)
        transition(job_id,'ready',file=str(final.relative_to(DATA)),size=final.stat().st_size,sha256=checksum,progress=json.dumps({'stage':'ready'}))
    finally:
        server.shutdown(); server.server_close()

if __name__ == '__main__':
    supervise_parent()
    try:
        if sys.argv[1] == 'inspect': print(json.dumps(inspect(sys.argv[2])))
        else: download(sys.argv[2])
    except Exception:
        # Deliberately do not persist extractor errors containing signed URLs/cookies.
        if sys.argv[1] == 'download': transition(sys.argv[2],'failed',error='Media operation failed. Check source support, access rights, format and server resources.')
        else: print(json.dumps({'error':'Could not inspect this source. Check access rights, URL and engine support.'}))
        sys.exit(1)
