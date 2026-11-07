# API v1

OpenAPI is available at `/openapi.json`, interactive documentation at `/docs`. Request models reject unknown fields. Device routes require `Authorization: Bearer <session>`. Artifact routes require a distinct artifact capability in the same header. API responses are not cached.

## Authentication

- `POST /api/v1/auth/login`: `{username,password,device_name}` → `{token,device_id,expires,admin}`. Initial username is admin. Sessions expire after 30 days.
- `POST /auth/refresh`: rotates session and revokes the old device session and associated transfer capabilities.
- `POST /auth/logout`: revokes the session, 204.
- `POST /pairing/start`: administrator-only, returns one-use challenge expiring in 180 seconds.
- `POST /pairing/complete`: `{challenge,device_name}` → limited device session. Challenge is atomically consumed.
- `GET /devices`, `DELETE /devices/{id}`: administrator-only.

All paths below have `/api/v1` prefix.

## Media/jobs

`POST /media/inspect {url}` runs real yt-dlp extraction and returns `id,title,creator,source,duration,description,thumbnail,upload_date,formats,chapters,subtitles`. Missing source metadata remains null/absent. Metadata includes only safe fields; stream/cookie credentials are not returned. Only one item is supported per inspection; playlist URLs are rejected with actionable feedback.

`GET /media/inspection/{id}` retrieves owner-scoped inspection.

`POST /downloads` accepts `{inspection_id,selection,request_key,authorized,priority?}`. `authorized` must be true. Same owner/idempotency key returns the original job. Selection fields:

- preset: compatible, best, small, audio, original, custom;
- format_id/audio_id: inspected format IDs only, strict identifier grammar;
- audio_format: original, m4a, mp3, opus, flac, wav;
- bitrate: 128, 192, 256, 320;
- subtitles: English source subtitles when available;
- embed_metadata: boolean.

`GET /downloads` lists up to 1,000 records for the owner. `GET /downloads/{id}` returns one snapshot. Fields include actual state/progress, revision, timestamps, error, size and SHA-256. Internal paths and idempotency keys are removed.

`POST /downloads/{id}/{cancel|retry|pause|resume}` executes state transitions; unsupported transitions return 409. Retry/delete while the worker is still stopping returns 409. Pause is stop/restart with source-dependent partial reuse, not guaranteed byte-perfect resume.

`PATCH /downloads/{id} {priority}` reorders queued jobs (-100…100). `DELETE /downloads/{id}` removes a terminal/stopped job and server artifacts. Clients should confirm this destructive action.

`POST /batches {jobs:[...]}` transactionally creates up to 50 inspected items. Each item has its own job and idempotency key. Playlist expansion is not implemented.

## Artifact delivery

`POST /downloads/{id}/transfer` → `{id,token,path,expires,size,sha256,filename}`. Token lifetime is six hours, artifact/device scoped. `GET` and `HEAD /transfers/{id}/file` require that token; support Content-Length, Content-Type, Content-Disposition, Range and SHA-256 ETag. Partial requests use the same capability until expiry. An ordinary session token cannot be substituted.

`POST /transfers/{id}/complete {sha256}` requires an owner session and matching checksum. It records verification; it does not automatically delete media or claim the operating system saved a browser download.

## Events/administration

`GET /events` is an authenticated SSE stream. Events are `job.updated` snapshots, ID `job-id:revision`; reconnect receives fresh snapshots. REST remains authoritative; deleted jobs are reconciled through the list endpoint. The shipped clients currently poll; there is no misleading claim of native push notifications for server completion.

`GET /health` is public and minimal. `GET /status`, `/capabilities`, `/versions` require sessions. `GET /admin/engine`, `/admin/storage`, `/admin/settings` and `PATCH /admin/settings {concurrency,retention_hours}` require administrator sessions. No dependency update endpoint pretends to install packages: updates are explicit image rebuild/rollback operations.

`GET/POST /presets` lists or persists named typed selections. Preset editing UI is not implemented.

## Application update metadata

`GET /updates?version=0.1.0&build=1&channel=stable&variant=extended&os_version=17.0` requires a device session and returns explicit status, check timestamp and a compatible published candidate when available. Private GitHub credentials stay on the server. See features/UPDATES.md for cache, compatibility and current validation limits.
