// SPDX-License-Identifier: AGPL-3.0-only
const CACHE='fetch-shell-0e31a36d0c0229e6';
const SHELL=['/','/index.html','/style.css','/app.js','/manifest.webmanifest','/release.json','/icon.svg','/icon-192.png','/icon-512.png','/icon-maskable.png','/apple-touch-icon.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('fetch-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('message',e=>{if(e.data?.type==='ACTIVATE')self.skipWaiting(); if(e.data?.type==='RELEASE_METADATA'&&e.ports[0])e.waitUntil(caches.open(CACHE).then(c=>c.match('/release.json')).then(r=>r?.json()).then(data=>e.ports[0].postMessage({...data,webBuild:CACHE}))); });
self.addEventListener('fetch',e=>{
 const url=new URL(e.request.url);
 if(e.request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
 if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).catch(()=>caches.match('/index.html')));return;}
 if(SHELL.includes(url.pathname))e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request)));
});
