# Implementation and evidence matrix

| Area | Implementation | Evidence / limitation |
|---|---|---|
| Metadata and formats | Real yt-dlp, typed selections, direct/custom presets | Controlled real fixture inspected; universal source support not claimed |
| Download/FFmpeg pipeline | Download, merge, extract/convert audio, conditional compatible MP4, FFprobe | Real video/MP3 workflow passes; codec/subtitle matrix not exhaustive |
| Queue | SQLite persistence, priorities, idempotency, pause/restart, cancel/retry, quotas, retention | API/state/recovery tests; full hostile load/abrupt-crash matrix still open |
| Authentication | Argon2 admin, device sessions, revocation, pairing and generated one-use QR | Real backend negative tests; QR camera not device-tested |
| File transfer | Owner/file/device scoped expiring capabilities, Range/HEAD, checksum | Actual byte and hash tests plus browser save |
| SSRF/process safety | DNS-pinned proxy, address/scheme restrictions, disabled plugins, guarded local FFmpeg inputs | Actual redirect/private URL API paths and focused guard tests; host firewall unconfigured |
| Native navigation | SwiftUI server setup, home, selection, queue/history, library, Settings/admin | Source and syntax only; not compiled with iOS SDK |
| Native files | Quick Look, Files/share, Photos, search/sort, rename/duplicate/folders/info/delete | Implemented; native APIs and data recovery require device validation |
| Native transfer | Persistent background URLSession, restoration, staging recovery, size/hash, cancellation | Implemented; no native lifecycle or physical-device proof |
| Share Extension / links | App Group deduplicated inbox, URL/text attachments, download/pair links | Implemented; actual app/extension interoperability not tested |
| Batch | Multiple individual URLs with common selections | Implemented; playlist inspection/selection not implemented |
| Dashboard | Responsive same-origin strict TypeScript client and administration | Real Chrome E2E, mobile layout and screenshots |
| PWA | Manifest/icons, offline shell/Ideas, API exclusions, explicit reload and structured notes | Offline/cache/layout tested; actual installs and two-build update cycle open |
| Developer Ideas | Offline CRUD/search/duplicate, status/history, versioned JSON merge/export/import | Core conflict/schema checks and browser persistence; advanced batch/filter/Markdown not implemented |
| Changelog | Shared structured initial release metadata, first-launch suppression, native/web summaries | Native presentation untested; complete technical commit history/skip aggregation incomplete |
| Update checks | Server GitHub bridge, compatibility filtering, native automatic/manual flow | Backend rules tested; live releases unavailable and native prompts unverified |
| Self-hosting | Non-root two-service Compose, limits, health checks and backup script | Prepared; Docker build/start/backup restore not run locally |
| Licensing/branding | Full AGPL text, initial notices review, layered SVG and reproducible native/PWA exports | Complete source assets; no legal/App Store clearance or full container SBOM |
| Distribution | Private repo, testing/beta/main baseline, parallel native workflows and artifact validator | Workflows prepared; no native build/release/public source/deployment |

This is not the full specification's definition of done: iOS end-to-end acceptance and production/container validation are outstanding. The roadmap lists remaining implementation as well as missing evidence.
