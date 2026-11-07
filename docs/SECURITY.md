# Security architecture and review scope

This document describes implemented controls, not a complete external security audit. Reviewed code: config, schema/state transitions, API authentication/ownership, proxy, engine options, supervisor, transfer serving, browser credential/cache handling and native credential/transfer source. Actual native execution and container isolation remain unverified.

## Identity and capabilities

No universal password exists. First administrator creation requires a unique environment password, stored using Argon2. Session secrets are random, hashed at rest, expire after 30 days and are revocable. Pairing challenges are random, hashed, consumed transactionally, expire in three minutes and are minted only by administrators. Paired sessions have personal-library access but no server administration.

Artifact bearer capabilities bind one ready file to the issuing device, expire after six hours and are revoked with the device/job. They permit Range retries until expiry rather than pretending to be one-use. Completion acknowledgement checks the expected hash and never deletes media merely because transfer began. Access logs are disabled in the documented runner/container to avoid logging source-related requests. Tokens are headers, never query parameters. Diagnostic exports omit them.

Browser sessions are memory-only and disappear on reload. The service worker excludes all API routes and caches no private job metadata or media. Native sessions use Keychain after-first-unlock/this-device-only; local protected JSON contains no token.

## Egress and execution

All yt-dlp HTTP requests use an explicit local proxy with per-request/CONNECT address validation. The resolver rejects non-global destinations, mixed safe/unsafe DNS answers, internal/local/link-local/metadata addresses, credentials in URLs, unsafe schemes and nonstandard public ports. Connections use the already-validated numeric address to prevent a second DNS lookup race. Redirects remain subject to proxy checks. HTTPS verification is retained.

FFmpeg postprocessors accept local protocols only, and compatible conversion is a fixed local-only command. The user cannot supply arbitrary command arguments, filesystem paths, plugins, credentials or executable code. yt-dlp plugins are disabled using its actual supported environment switch; a malicious-plugin regression test checks this behavior. EJS comes from the pinned package, with no remote component auto-download.

Application egress validation is not a substitute for host network enforcement. Deploy Internet-facing servers only with a dedicated bounded filesystem, restricted service identity, TLS, reverse-proxy limits and host-managed private-range egress denial. No host firewall was altered in this task. Optional future transports/extractors require fresh review before enabling.

## Resources/data integrity

Persistent claims, a singleton worker, process groups, quotas/deadlines, bounded concurrency and post-exit retry/delete rules protect job folders. Filenames and final paths are generated internally. SHA-256 and atomic finalization precede file exposure. Container configuration drops capabilities, uses non-root/read-only roots and bounds CPU/memory/pids/tmp/logging; Docker enforcement has not been tested here.

Unknown-size files and temporary streams can exceed a soft application quota briefly between polling checks. Failed partials consume disk until removed. No multi-tenant or hostile hosting certification is claimed. API replicas would require shared rate limits and a different queue coordination design.

## Distribution

No DRM bypass, protected subscription decryption, paywall bypass, cookie harvesting or untrusted plugin administration is implemented. Source availability does not establish download rights. Store-mode server allowlisting is not enough to claim App Store compliance. AGPL and actual bundled FFmpeg/dependency obligations require review before distribution. No production deployment, official store submission or public release has occurred.
