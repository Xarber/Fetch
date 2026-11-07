// SPDX-License-Identifier: AGPL-3.0-only
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
execFileSync(process.execPath,[new URL('node_modules/typescript/bin/tsc',root).pathname],{cwd:root.pathname,stdio:'inherit'});
const release=await readFile(new URL('release.json',root));
await writeFile(new URL('web/release.json',root),release);
await writeFile(new URL('ios/Fetch/ReleaseMetadata.json',root),release);
const worker=await readFile(new URL('web/sw.js',root),'utf8');
const hash=createHash('sha256');
hash.update(worker.replace(/const CACHE='[^']+';/,"const CACHE='';"));
for(const name of ['index.html','app.js','style.css','manifest.webmanifest','icon.svg','release.json'])hash.update(await readFile(new URL('web/'+name,root)));
const file=new URL('web/sw.js',root);
const source=await readFile(file,'utf8');
await writeFile(file,source.replace(/const CACHE='[^']+';/,`const CACHE='fetch-shell-${hash.digest('hex').slice(0,16)}';`));
