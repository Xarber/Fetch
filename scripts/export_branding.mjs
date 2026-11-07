// SPDX-License-Identifier: AGPL-3.0-only
import sharp from 'sharp';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
const svg=await readFile(new URL('../assets/branding/icon-master.svg',import.meta.url),'utf8');
const root=new URL('../',import.meta.url);
await writeFile(new URL('web/icon.svg',root),svg);
for(const [size,name] of [[192,'icon-192.png'],[512,'icon-512.png'],[512,'icon-maskable.png'],[180,'apple-touch-icon.png']])await sharp(Buffer.from(svg)).resize(size,size).png().toFile(new URL('web/'+name,root).pathname);
const icons=new URL('ios/Fetch/Assets.xcassets/AppIcon.appiconset/',root);await mkdir(icons,{recursive:true});
await sharp(Buffer.from(svg.replace('rx="224"','rx="0"'))).resize(1024,1024).flatten({background:'#6269f5'}).png().toFile(new URL('AppIcon.png',icons).pathname);
await writeFile(new URL('Contents.json',icons),JSON.stringify({images:[{filename:'AppIcon.png',idiom:'universal',platform:'ios',size:'1024x1024'}],info:{author:'OpenRecode',version:1}},null,2));
await writeFile(new URL('ios/Fetch/Assets.xcassets/Contents.json',root),JSON.stringify({info:{author:'OpenRecode',version:1}}));
await writeFile(new URL('assets/branding/icon-dark.svg',root),svg.replaceAll('#8287ff','#464a9f').replaceAll('#535ae1','#232657'));
await writeFile(new URL('assets/branding/icon-monochrome.svg',root),svg.replaceAll('#8287ff','#333333').replaceAll('#535ae1','#333333'));

await sharp(await readFile(new URL('assets/branding/banner.svg',root))).png().toFile(new URL('assets/branding/banner.png',root).pathname);
