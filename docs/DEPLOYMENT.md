# Deployment and rollback

X-Center is the default host. Use a dedicated Compose project, a separate volume, and a loopback-only port for private staging. Access it through an authenticated SSH tunnel.

## Hosts

Linux x86-64/ARM64, NAS and VPS systems with Docker Compose can use the two-service configuration. macOS requires a separately installed Docker-compatible runtime. Architecture builds are prepared from upstream multi-architecture Python/Deno bases but have not been tested. No Docker socket, privileged container, host networking or proprietary cloud is required.

Run README configuration, then `docker compose build` and `docker compose up -d`. API and worker run as UID/GID 10001, with read-only root filesystems, shared named data volume, bounded writable tmpfs, capability drop, no-new-privileges, CPU/memory/process/log limits and health checks. The volume persists database and media. Do not change volume ownership on an existing deployment without checking files and backups.

## Network

The default bind is `127.0.0.1:8000`. Set `FETCH_PORT` to use a different loopback port. Terminate HTTPS with your own Caddy/nginx reverse proxy and a trusted certificate. Proxy to that local port, preserve Range/ETag and streaming responses, disable response buffering for SSE, and set request body limits (128 KiB). Never expose plain HTTP login over an untrusted network. iOS rejects remote HTTP endpoints.

Application egress pinning is meaningful SSRF protection, but Internet-facing hostile workloads additionally need **host-managed egress firewall policy** blocking private/link-local/reserved ranges for API and worker. No host firewall changes were made automatically. Permit required DNS and public HTTPS carefully. Do not set FETCH_TEST_ORIGIN in deployment; it bypasses one exact destination only for isolated tests. This configuration is not a hardened multi-tenant hosting platform.

## Stage and validate

1. Record current commit, image digest, configuration and volume.
2. Stop the worker and take a protected backup.
3. Build from a tracked snapshot with `FETCH_COMMIT` and `FETCH_IMAGE_TAG` set to its full hash. Point `FETCH_ENV_FILE` at an external, mode-0600 dotenv file. Keep the previous tagged image for rollback.
4. Stage against a separate volume/port; run authorized fixture, authentication, SSRF, processing and Range checks.
5. Recreate only Fetch API/worker with the validated image; preserve data.
6. Verify `/health`, authenticated `/versions`, worker heartbeat and actual job/transfer workflow through the HTTPS endpoint.
7. Roll back to the recorded image/configuration if essential flows fail. Never delete the persistent volume as a rollback step.

No automated reverse proxy or public endpoint is provisioned. Paid infrastructure and new distribution channels need explicit authorization.

## Backup/restore

Stop the worker before an application-level backup. With a local data directory:

```sh
.venv/bin/python scripts/backup.py ./data ./backups/fetch-before-upgrade
```

This uses SQLite's online backup API and copies ready artifacts; partial files are omitted. Treat the backup as private (password hashes, tokens hashes, URLs, media). Encrypt external copies yourself. Restore only with API/worker stopped: preserve the existing directory, then copy the backed-up database and jobs directory into the configured data location with the original owner permissions. Restart and verify versions/status and a retained file checksum. No automated destructive restore command is provided.

For the named Docker volume, stop both services and use the host's supported encrypted volume-backup process, or copy it into a protected local staging directory before running the script. Never back up an actively changing raw SQLite file without its WAL or the SQLite backup API. Container backup/restore has not been executed locally.

## Corresponding source

The container build packages the application source without runtime data, credentials, signing files or dependencies. Authenticated users can download it from About Fetch or `/api/v1/source`, preserving private access without relying on public repository visibility. Local deployments must run `python scripts/package_source.py` again for each deployed revision. Never include private local files in a build context; use a clean checkout. This source offer supports AGPL obligations but does not replace reviewing bundled third-party source/notices requirements.

## X-Center staging — 2026-11-13

Private x86-64 Compose staging serves Fetch 0.1.0 at commit `82d40b2eda2ed2aaec9062b163a26c547a7d006a`. The API listens on host loopback port 18440. The landing, setup guide, authentication, version endpoint, engine availability and SQLite worker heartbeat were verified. The local browser fixture exercised media processing separately. X-Center had approximately 1.4 GiB available after the build, below this deployment’s 2 GiB floor. The worker will hold queued downloads until more storage is available.

Open an SSH local forward from port 18440 to X-Center loopback port 18440 using the existing authenticated route. Release directories are grouped under `/srv/xcenter/apps/openrecode-fetch/releases`. The previous image and snapshot at `cf3a0fe532e47de0b38b1bbf3533eb617b3f4914` are retained for rollback with the same protected environment file and volume.
