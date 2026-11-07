# SPDX-License-Identifier: AGPL-3.0-only
"""Run with worker stopped. SQLite online backup plus finalized artifacts only."""
import argparse
import sqlite3
import shutil
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('data',type=Path);parser.add_argument('destination',type=Path)
args=parser.parse_args();args.destination.mkdir(parents=True,exist_ok=False)
source=sqlite3.connect(args.data/'fetch.sqlite3')
target=sqlite3.connect(args.destination/'fetch.sqlite3');source.backup(target);target.close()
for (name,) in source.execute("SELECT file FROM jobs WHERE state='ready' AND file IS NOT NULL"):
    original=(args.data/name).resolve()
    if not original.is_relative_to(args.data.resolve()/'jobs'): raise ValueError('Invalid artifact path')
    dest=args.destination/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,dest)
source.close()
print('Backed up database and ready artifacts. Protect this backup as private data.')
