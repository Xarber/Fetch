# SPDX-License-Identifier: AGPL-3.0-only
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--channel',choices=['beta','stable'],required=True);p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[1]
release=json.loads((root/'release.json').read_text())
release.update(channel=args.channel,commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
release['artifacts']=[]
for file in sorted(args.artifacts.rglob('*')):
    if file.is_file() and file.suffix in ('.ipa','.zip'):
        with file.open('rb') as stream: checksum=hashlib.file_digest(stream,'sha256').hexdigest()
        release['artifacts'].append({'name':file.name,'size':file.stat().st_size,'sha256':checksum})
if not any(a['name'].endswith('.ipa') for a in release['artifacts']) or not any(a['name'].endswith('.app.zip') for a in release['artifacts']):
    raise SystemExit('Both device and simulator artifacts are required; refusing incomplete metadata')
(args.artifacts/'release-manifest.json').write_text(json.dumps(release,indent=2)+'\n')
print('Prepared metadata. Publication and download URLs require an authorized release destination.')
