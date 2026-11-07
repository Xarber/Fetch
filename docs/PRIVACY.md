# Privacy

Fetch includes no advertising SDK, telemetry or cross-app tracking. A proprietary account/service is not required. Configured self-hosting still sends requests to the original media source, which can observe the server's IP and requests.

The phone stores profiles, cached server snapshots, transfer status, verified files, Ideas and preferences locally. Keychain stores credentials. App Group storage holds shared links pending import. Explicit Paste is the only clipboard read. Camera and Photos permissions are requested for user-selected features. Local files stay browsable without a server.

The server stores submitted URLs, inspection metadata, job records and processed media. Ready files expire by configurable retention. Explicit Remove deletes the artifact and job; inspection records may remain. Automatic inspection/history expiration, a full privacy reset/export workflow and retention-disabled history are not yet implemented. Do not claim all traces are removed by deleting one job.

Browser job data is memory-only. Ideas persist in localStorage for this origin; they are not uploaded automatically. Export JSON to move them to development. The dashboard caches only the public application shell for offline use. Local browser storage/backups should be protected as private data.

Native protected stores that fail to decode are preserved and blocked from overwrite. Browser unreadable Ideas storage is also preserved and offers a recovery export rather than silently replacing it. This is a recovery safeguard, not a full schema migration UI.

No automatic Harmony/Echo integration reads another application's private storage. Explicit media share/export is the interoperability boundary. No public upload of personal media or private development Ideas is authorized.

App/extension privacy manifests declare own-container and App Group UserDefaults access; the app also declares space checks and file metadata access. These declarations need archive/privacy-report review before store distribution; they do not establish App Store approval.
