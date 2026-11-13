# Testing

## Automated backend

`pytest -q` runs real ASGI endpoints, SQLite transactions, generated local media, actual yt-dlp extraction/download and FFmpeg/FFprobe processing. It covers credentials, pairing/QR payloads, challenge replay/expiry, device revocation, cross-owner access, unsafe schemes/addresses, redirect-based SSRF, rebinding-resolution rejection, format validation, injection-shaped input rejection, safe filenames, idempotency, queue pause/resume transitions, interrupted-state restart recovery, Range/HEAD transfer, expiration and deletion, disabled untrusted plugins, oversized source rejection and checksum verification.

Fixtures use a fresh temporary database, generated two-second video and one exact loopback origin exception. The exception is absent from production defaults and is not a general private-network allowance. No personal media or third-party source credentials are used. Tests involving synthetic durable rows explicitly test access/state behavior, not real media decoding.

Known gaps: full abrupt-process-crash races, container resource enforcement, DNS pinning against an actual rebinding DNS server, TLS interception, exhaustive FFmpeg inputs, slow/large transfers, performance/load, filesystem exhaustion, all source extractors and long-term retention. In-process httpx TestClient emits a Starlette deprecation notice; this is recorded and not hidden.

## Browser

`npm run check` validates strict TypeScript. `npm run build` compiles the production dashboard and content-hashes the service worker. `npx playwright test` launches an isolated real API/worker through `scripts/browser_fixture.py`; uses actual Chrome, login, inspect, MP3 conversion, verified browser save, Ideas persistence, developer unlock/reset, responsive 390px layout and offline service-worker reload. API URLs must not appear in the shell cache.

The default browser executable is installed macOS Google Chrome. Set `FETCH_BROWSER_EXECUTABLE` to another installed Chromium-compatible executable when necessary. No browser or SDK is installed automatically. Screenshot artifacts in reports show controlled QA media, not a native app or production history. A screenshot alone does not verify installability or accessibility.

## Swift/native

Portable assertions:

```sh
swiftc ios/FetchCore/*.swift scripts/core_check.swift -o /tmp/fetch-core-check
/tmp/fetch-core-check
```

These execute progress and Ideas/model behavior using the available macOS command-line Swift toolchain. `swift test --package-path ios` was attempted but the local Swift Testing macro plugin was missing; this failed and is not reported as passing. Native syntax parsing passes, but does not resolve SwiftUI/UIKit APIs or concurrency compatibility. Both iOS device/simulator builds and physical-device checks are outstanding. See IOS.md.

## Containers/release

Docker build/start/health and backup/restore must run on a host with Docker. Workflow files prepare private test and native build jobs; no successful remote build is implied. The artifact validator checks package layout, platform, arm64, extension, identifiers, version and exact commit before generating a manifest. Release publication is disabled until explicitly authorized and validated.
