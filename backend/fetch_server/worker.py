# SPDX-License-Identifier: AGPL-3.0-only
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from .config import DATA, CONCURRENCY, RETENTION, MAX_BYTES, MAX_SECONDS, MIN_FREE
from .db import connect, init, transition

stop = False
def stopping(*_):
    global stop
    stop = True

def kill(process):
    try: os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    try: process.wait(timeout=4)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL); process.wait()

def run():
    init()
    lock = (DATA/'worker.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    signal.signal(signal.SIGTERM,stopping); signal.signal(signal.SIGINT,stopping)
    with connect() as db:
        db.execute("UPDATE jobs SET state='queued',running=0,version=version+1,error='Recovered after worker restart' WHERE state IN ('downloading','postprocessing')")
        db.execute("UPDATE jobs SET state='paused',running=0,version=version+1 WHERE state='pausing'")
    with connect() as db: db.execute('UPDATE jobs SET running=0')
    active = {}
    try:
        while not stop:
            now = time.time()
            with connect() as db:
                db.execute("INSERT OR REPLACE INTO settings VALUES('worker_heartbeat',?)",(str(now),))
                settings = {r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM settings')}
                states = {r['id']:r['state'] for r in db.execute('SELECT id,state FROM jobs')}
            for job,(proc,started) in list(active.items()):
                folder = DATA/'jobs'/job
                size = sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()) if folder.exists() else 0
                state = states.get(job)
                if state in ('cancelled','pausing') or now-started > MAX_SECONDS or size > MAX_BYTES*2 or shutil.disk_usage(DATA).free < MIN_FREE:
                    kill(proc)
                    if state == 'pausing': transition(job,'paused')
                    elif state != 'cancelled': transition(job,'failed',error='Execution timeout or storage quota exceeded')
                if proc.poll() is not None:
                    if states.get(job) in ('downloading','postprocessing'):
                        with connect() as db:
                            actual = db.execute('SELECT state FROM jobs WHERE id=?',(job,)).fetchone()
                        if actual and actual['state'] in ('downloading','postprocessing'):
                            transition(job,'failed',error='Worker subprocess exited before finalization')
                    if state == 'cancelled': shutil.rmtree(folder,ignore_errors=True)
                    with connect() as db: db.execute('UPDATE jobs SET running=0 WHERE id=?',(job,))
                    del active[job]
            if shutil.disk_usage(DATA).free > MIN_FREE:
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    pending = db.execute("SELECT id FROM jobs WHERE state='queued' ORDER BY priority DESC,created LIMIT ?",(max(0,int(settings.get('concurrency',CONCURRENCY))-len(active)),)).fetchall()
                    for row in pending:
                        db.execute("UPDATE jobs SET state='downloading',running=1,updated=?,version=version+1,error=NULL WHERE id=?",(now,row['id']))
                for row in pending:
                    # close_fds prevents child inheriting the singleton worker lock.
                    proc = subprocess.Popen([sys.executable,'-m','fetch_server.engine','download',row['id']],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True)
                    active[row['id']] = (proc,now)
            cutoff = now-int(settings.get('retention_hours',RETENTION))*3600
            with connect() as db:
                expired = db.execute("SELECT id FROM jobs WHERE state='ready' AND updated<?",(cutoff,)).fetchall()
                db.execute('DELETE FROM transfers WHERE expires<?',(now,))
                db.execute('DELETE FROM pairing WHERE expires<?',(now,))
            for row in expired:
                if transition(row['id'],'expired'): shutil.rmtree(DATA/'jobs'/row['id'],ignore_errors=True)
            time.sleep(.5)
    finally:
        for proc,_ in active.values(): kill(proc)

if __name__ == '__main__': run()
