# Dashboard PWA

The optional dashboard is a static production build served by the authenticated service's origin. It has manifest identity/scope/start URL, standalone display, theme/background colors, SVG favicon, Apple Touch icon, standard and maskable PNGs. Installation is offered when the browser exposes beforeinstallprompt; iOS users must use its supported Add to Home Screen flow.

The service worker precaches only a fixed public shell list. API requests, tokens, job history and media are never cached. Navigations prefer the network with offline-shell fallback; static shell resources use the versioned cache. Build tooling hashes HTML/TypeScript output/CSS/manifest/icon into the cache identity. Activation deletes only obsolete Fetch shell caches, preserving Ideas storage.

Updates wait for an explicit reload action with an unsaved-work confirmation, not a disruptive automatic reload. The first install does not show an update prompt. Current release notes are available in About. The waiting worker provides bundled structured release notes before activation. A web build identifier records post-update acknowledgement without showing a first-install popup. Skipped-release history aggregation is not yet implemented.

Browser tests verify service-worker registration, cache exclusions, offline shell, offline Ideas persistence and 390px layout. Actual Android/iOS/desktop installation, an upgrade between two deployed builds and cache recovery across release changes still require platform testing. HTTPS is required except browser-recognized localhost development contexts. The app is mounted at the origin root; subpath deployment needs coordinated manifest/assets/routing changes.
