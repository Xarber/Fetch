# SPDX-License-Identifier: AGPL-3.0-only
"""Create corresponding-source archive from an explicit source checkout, never runtime data."""
import argparse
import tarfile
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path,default=Path('data/fetch-source.tar.gz'));args=parser.parse_args()
root=args.root.resolve();output=args.output.resolve()
allowed_roots={'backend','ios','web','docs','assets','scripts','.github'}
allowed_files={'LICENSE','README.md','AGENTS.md','THIRD_PARTY_NOTICES.md','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md','CHANGELOG.md','.env.example','.gitignore','.gitattributes','.editorconfig','.dockerignore','Dockerfile','compose.yaml','pyproject.toml','requirements.lock','package.json','package-lock.json','tsconfig.json','playwright.config.ts','release.json'}
excluded={'.git','.venv','node_modules','data','.qa','.build','build','DerivedData','__pycache__','.pytest_cache','.codex','test-results','playwright-report'}
args.output.parent.mkdir(parents=True,exist_ok=True)
with tarfile.open(output,'w:gz') as archive:
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root)
        if relative.parts[0] not in allowed_roots and str(relative) not in allowed_files:continue
        if any(part in excluded for part in relative.parts) or path.is_symlink() or not path.is_file():continue
        if path.resolve()==output or (path.name.startswith('.env') and path.name!='.env.example') or path.suffix.lower() in ('.p12','.mobileprovision','.key','.pem','.p8','.keystore','.jks') or any(part.endswith('.egg-info') for part in relative.parts):continue
        archive.add(path,arcname='fetch/'+str(relative),recursive=False)
print('Prepared source archive without runtime data or credentials')
