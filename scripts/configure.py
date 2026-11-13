# SPDX-License-Identifier: AGPL-3.0-only
import getpass
import os
import base64
from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/'.env'
if path.exists(): raise SystemExit('.env already exists. Edit it explicitly; existing settings were preserved.')
password=getpass.getpass('Choose a unique initial administrator password (14+ characters): ')
if len(password)<14: raise SystemExit('Password must contain at least 14 characters')
encoded=base64.b64encode(password.encode()).decode()
text=(root/'.env.example').read_text().replace('FETCH_ADMIN_PASSWORD_B64=','FETCH_ADMIN_PASSWORD_B64='+encoded,1)
# Compose receives /data through its explicit environment; local runner needs a local path.
text=text.replace('FETCH_DATA=/data','FETCH_DATA=./data')
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as stream: stream.write(text)
print('Private .env created. Password is never printed. Log in as admin.')
