# Fetch engineering context

Read README.md, docs/INDEX.md, docs/ARCHITECTURE.md, docs/SECURITY.md and docs/reports/VALIDATION.md before substantial changes. Original code is AGPL-3.0-only. Preserve the SwiftUI primary client, server processing/device transfer separation, identifiers, credentials and user data. Never describe unverified native behavior as tested.

## Ideas review

Read docs/IDEAS.json at session start. Report pending/approved/deferred counts and related ideas. Compare against implemented functionality; ask whether relevant optional ideas should be implemented now or later without interrupting the explicit task repeatedly. Implement unrelated ideas only when selected. Update statuses and implementation references after verification, and link released work in release.json. Private on-device collections are inaccessible unless explicitly exported/imported; do not claim otherwise. Imported conflicts must preserve both versions.

## Layout and commands

- backend/fetch_server: API, SQLite schema/state machine, guarded egress proxy, supervised engine subprocesses, singleton worker.
- ios/FetchCore: Codable API/domain models and versioned Ideas format; included directly in app target and separately testable as a package.
- ios/Fetch: SwiftUI client, Keychain API, persisted background transfer delegate and library.
- ios/FetchShare: App Group inbox, no long-running downloads.
- web/src: strict TypeScript; build with npm run build. web/app.js is generated and committed for backend/container use.
- scripts: local runner, test fixtures, backup, branding export, project generation and release metadata.

Use Conventional Commits. Work on testing or isolated branches; integrate into testing before any promotion. beta/main are reserved for validated promotions. X-Center is the default host for managed Fetch services. Preserve existing services and keep public exposure, publishing and repository visibility changes subject to explicit authorization. Review docs/REPOSITORY_REUSE.md before touching the original repository. Build artifacts are produced by GitHub Actions. Releases and additional distribution channels require explicit authorization. Do not migrate to Android/Expo or build an on-device Python engine without a justified task.

## Checks

Run pytest, npm run check and npm run build. Playwright exercises a real local disposable server and FFmpeg worker. Set FETCH_BROWSER_EXECUTABLE to an installed browser when needed; do not install large toolchains without approval. Native changes require an actual Xcode build when available. Portable model assertions do not prove SwiftUI compilation. Never use FETCH_TEST_ORIGIN outside isolated tests.

## Security invariants

No arbitrary yt-dlp/FFmpeg flags, shell execution, file URLs, remote plugins, cookie harvesting or telemetry. Require authorization and source safety; preserve HTTPS validation. A job artifact becomes ready only after local processing, atomic finalization and checksum. Transfer tokens use Authorization headers, never query strings. No sensitive API caching in the service worker. Never silently expand source or distribution policy.

## Web and native experience

Keep the first-visit introduction integrated at the web root with direct workspace links and an in-document return path. Reuse the shared icons and motion tokens. Consult the relevant design and accessibility skills before substantial interface changes. Preserve SwiftUI for the current native client and prefer Expo for new mobile work when it supports the necessary native adapters. Prefer the configured hardware signing key and report unsigned commits when the key is unavailable.
