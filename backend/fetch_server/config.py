# SPDX-License-Identifier: AGPL-3.0-only
import os
from pathlib import Path

DATA = Path(os.environ.get('FETCH_DATA', './data')).resolve()
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / 'fetch.sqlite3'
MAX_BYTES = int(os.getenv('FETCH_MAX_BYTES', str(2 * 1024**3)))
MAX_SECONDS = int(os.getenv('FETCH_MAX_SECONDS', '3600'))
MIN_FREE = int(os.getenv('FETCH_MIN_FREE', str(512 * 1024**2)))
CONCURRENCY = max(1, min(4, int(os.getenv('FETCH_CONCURRENCY', '2'))))
RETENTION = int(os.getenv('FETCH_RETENTION_HOURS', '168'))
# Explicit test-only exception; absent in deployment configuration.
TEST_ORIGIN = os.getenv('FETCH_TEST_ORIGIN', '')
SOURCE_HOSTS = {h.strip().lower() for h in os.getenv('FETCH_SOURCE_HOSTS', '').split(',') if h.strip()}
STORE_MODE = os.getenv('FETCH_DISTRIBUTION', 'extended') == 'store'
