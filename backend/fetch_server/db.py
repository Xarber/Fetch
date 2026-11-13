# SPDX-License-Identifier: AGPL-3.0-only
import json
import sqlite3
import time
from contextlib import contextmanager
from .config import DB

@contextmanager
def connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init():
    with connect() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
        INSERT OR IGNORE INTO schema_version VALUES(1);
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY,owner TEXT NOT NULL,name TEXT NOT NULL,token TEXT UNIQUE NOT NULL,admin INTEGER NOT NULL DEFAULT 0,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS pairing(token TEXT PRIMARY KEY,owner TEXT NOT NULL,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS inspections(id TEXT PRIMARY KEY,owner TEXT NOT NULL,url TEXT NOT NULL,metadata TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,owner TEXT NOT NULL,inspection TEXT NOT NULL,title TEXT NOT NULL,selection TEXT NOT NULL,state TEXT NOT NULL,priority INTEGER NOT NULL DEFAULT 0,created REAL NOT NULL,updated REAL NOT NULL,version INTEGER NOT NULL DEFAULT 1,progress TEXT NOT NULL DEFAULT '{}',error TEXT,file TEXT,size INTEGER,sha256 TEXT,running INTEGER NOT NULL DEFAULT 0,request_key TEXT NOT NULL,UNIQUE(owner,request_key));
        CREATE TABLE IF NOT EXISTS transfers(id TEXT PRIMARY KEY,owner TEXT NOT NULL,device TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,job TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,secret TEXT UNIQUE NOT NULL,expires REAL NOT NULL,completed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS presets(id TEXT PRIMARY KEY,owner TEXT NOT NULL,name TEXT NOT NULL,selection TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS queue ON jobs(state,priority,created);
        ''')

def job_dict(row):
    d = dict(row)
    d['selection'] = json.loads(d['selection'])
    d['progress'] = json.loads(d['progress'])
    d.pop('file', None)
    d.pop('request_key', None)
    return d

ALLOWED = {
    'queued': {'downloading','cancelled','paused','failed'},
    'downloading': {'postprocessing','ready','failed','cancelled','pausing'},
    'postprocessing': {'ready','failed','cancelled','pausing'},
    'pausing': {'paused','cancelled','failed'},
    'paused': {'queued','cancelled'},
    'failed': {'queued','cancelled'},
    'cancelled': {'queued'},
    'ready': {'expired'},
    'expired': set(),
}

def transition(job, state, **fields):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT state FROM jobs WHERE id=?', (job,)).fetchone()
        if not row or (state != row['state'] and state not in ALLOWED.get(row['state'], set())):
            return False
        fields.update(state=state, updated=time.time())
        keys = list(fields)
        db.execute(f"UPDATE jobs SET {','.join(k+'=?' for k in keys)},version=version+1 WHERE id=?", [fields[k] for k in keys]+[job])
        return True
