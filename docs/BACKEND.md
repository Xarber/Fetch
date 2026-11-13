# Backend

Python 3.11+; actual lock uses packages installed with Python 3.13.15. FastAPI 0.162.0/Pydantic 2.14.3/Starlette 1.10.0, yt-dlp 2026.10.26 and argon2-cffi 25.1.0. Install the committed runtime lock before the editable project. `.[test]` adds pytest and httpx. Starlette currently emits a deprecation notice for httpx-based TestClient; tests pass and a future migration to its new client is recorded in the roadmap.

Run `python scripts/run.py init` for idempotent schema creation and initial administrator setup. A unique 14+ character password is mandatory on first creation; Argon2 hashes are persisted and the environment password does not overwrite an existing administrator. Database schema v1 uses `CREATE IF NOT EXISTS`; no destructive migration is performed. Future schema changes need numbered migrations and backups.

Start API and worker independently using README commands. Both must resolve the same data directory. The worker's heartbeat is available via authenticated status. Default concurrency is two for the whole pipeline, maximum four; conversions therefore cannot exceed this bound. The worker checks disk space, cumulative per-job work files and deadlines twice per second. Default maximum final output is 2 GiB, runtime one hour, minimum free space 512 MiB, ready-artifact retention seven days.

Request bodies reject undeclared fields. Login/pairing/inspection attempts have in-process per-IP throttling, source inspection has two concurrent slots and a 60-second subprocess timeout, queued jobs are capped at 100 per owner. Deploy multiple API replicas only after adding coordinated rate limiting; the current deployment is single-host/single-API.

Resource limits are layered: download filesize hints, progress supervision, work-directory polling, and container CPU/memory/pid limits. Polling is not a hard filesystem quota; deploy with a dedicated bounded filesystem for hostile environments. Large unknown-size sources can temporarily exceed the application quota before termination. Failed intermediates are retained for retry until explicitly removed; cancelled artifacts are cleaned by the worker.
