// SPDX-License-Identifier: AGPL-3.0-only
const CACHE='fetch-shell-58f497fe4d79dee5';
const SHELL=['/','/index.html','/style.css','/design.css','/icons.js','/motion.js','/presentation.css','/presentation.js','/guide/','/guide/index.html','/screenshots/dashboard-desktop.png','/screenshots/dashboard-mobile.png','/app.js','/manifest.webmanifest','/release.json','/icon.svg','/icon-192.png','/icon-512.png','/icon-maskable.png','/apple-touch-icon.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('fetch-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('message',e=>{if(e.data?.type==='ACTIVATE')self.skipWaiting(); if(e.data?.type==='RELEASE_METADATA'&&e.ports[0])e.waitUntil(caches.open(CACHE).then(c=>c.match('/release.json')).then(r=>r?.json()).then(data=>e.ports[0].postMessage({...data,webBuild:CACHE}))); });
self.addEventListener('fetch',e=>{
 const url=new URL(e.request.url);
 if(e.request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
 if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).catch(()=>caches.match(url.pathname.startsWith('/guide')?'/guide/index.html':'/index.html')));return;}
 if(SHELL.includes(url.pathname))e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request)));
});
