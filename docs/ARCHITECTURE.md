# Architecture

The primary UI is SwiftUI, not a web wrapper. The optional dashboard is a same-origin strict TypeScript client served by FastAPI. Neither runs yt-dlp locally. Both use `/api/v1`.

## Backend modules

`config.py` reads process configuration. `db.py` owns SQLite schema v1, transactions, JSON persistence and state transitions. `models.py` defines allowed request contracts. `security.py` implements URL validation, safe display names and a local egress proxy. `api.py` authenticates, inspects media in isolated subprocesses, creates durable jobs, issues transfer credentials and serves immutable finalized artifacts. `worker.py` is a single coordinator with bounded child process concurrency. `engine.py` integrates the installed yt-dlp API and local FFmpeg.

Each process uses its own SQLite connection with WAL and busy timeout. The worker uses an advisory filesystem lock; only one coordinator is supported per local database. A claim transaction sets `running=1` before subprocess launch. User cancellation is durable; retry/delete is rejected until the subprocess is reaped. On restart, abandoned active states are requeued and partial files retained for source-supported retry. Per-job file locks serialize restarted attempts. Child engine processes monitor the expected parent identity and kill their process group if the parent exits. There is no distributed or remote database coordinator.

## State and ownership

Server states: queued, downloading, postprocessing, pausing, paused, ready, failed, cancelled, expired. Device transfer states are persisted independently. Job revisions increase monotonically on transitions and progress. SSE sends authoritative changed snapshots; client REST polling every three seconds provides reconnection recovery. No synthetic percentage is used during unmeasured postprocessing. `total_estimated` distinguishes source estimates.

Device sessions share one administrator's personal library while paired sessions cannot use administrator routes. Owner checks isolate future independent users; no multi-user management UI is implemented. Transfer capabilities are restricted to one artifact, linked to the issuing device, hashed at rest, expire after six hours, and are revoked on device deletion. Reuse for Range/retry is intentional until expiry.

## Native modules

`FetchCore` is Foundation-only and holds API/Ideas value types. `APIClient` handles Codable contracts, HTTPS and Keychain. `AppStore` owns foreground UI state, profiles and cached jobs. `Transfers` owns background URLSession and persists task identities separately from server jobs. Downloaded temporary files move immediately into staging; streamed SHA-256 verification precedes final placement in Documents/Media and local metadata persistence. The app delegate delays the background completion handler until verification work is done. Share Extension only appends deduplicated URLs to an App Group inbox.

No arbitrary plugin execution API exists. The typed preset/selection contract and client domain layer provide future extension seams. A complete sandboxed plugin registry/runtime is not implemented.
