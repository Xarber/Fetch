# SPDX-License-Identifier: AGPL-3.0-only
"""Validate package layout, identifiers, version, commit and binary platform on macOS."""
import json
import os
import plistlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
root=Path(sys.argv[1]); release=json.loads(Path('release.json').read_text())
commit=os.getenv('GITHUB_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
count=0
for package in root.iterdir():
    if package.suffix not in ('.ipa','.zip'):continue
    device=package.suffix=='.ipa'
    with tempfile.TemporaryDirectory(prefix='fetch-validate-') as temp:
        folder=Path(temp).resolve()
        with zipfile.ZipFile(package) as archive:
            for info in archive.infolist():
                path=(folder/info.filename).resolve()
                if not path.is_relative_to(folder):raise SystemExit('Unsafe archive path')
            archive.extractall(folder)
        app=folder/('Payload/Fetch.app' if device else 'Fetch.app')
        if not app.is_dir():raise SystemExit('Invalid app bundle layout: '+package.name)
        for bundle,identifier in [(app,'org.openrecode.fetch'),(app/'PlugIns/FetchShare.appex','org.openrecode.fetch.share')]:
            info=plistlib.loads((bundle/'Info.plist').read_bytes())
            assert info['CFBundleIdentifier']==identifier
            assert info['CFBundleShortVersionString']==release['version']
            assert str(info['CFBundleVersion'])==str(release['build'])
            binary=bundle/info['CFBundleExecutable']
            arch=subprocess.check_output(['lipo','-archs',str(binary)],text=True).strip()
            assert 'arm64' in arch
            platform=subprocess.check_output(['xcrun','vtool','-show-build',str(binary)],text=True)
            assert ('IOSSIMULATOR' in platform) if not device else ('IOS' in platform and 'IOSSIMULATOR' not in platform)
        app_info = plistlib.loads((app/'Info.plist').read_bytes())
        assert app_info['FetchCommit'] == commit
        expected_server = os.getenv('FETCH_EXPECTED_SERVER_URL')
        if expected_server is not None:
            assert app_info.get('FetchServerURL', '') == ('' if expected_server == 'self-hosted' else expected_server)
        count+=1
if count!=2:raise SystemExit('Expected complete device and simulator artifact pair')
print('Validated both artifact layouts, binaries, identifiers, versions and build commit')
