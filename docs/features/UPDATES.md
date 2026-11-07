# Release detection

`GET /api/v1/updates` is an authenticated server-side GitHub metadata bridge. Configure `FETCH_RELEASE_REPOSITORY=owner/repository` and, for a private repository, a narrowly scoped read-only `FETCH_RELEASE_TOKEN` in protected server configuration. The token is never sent to mobile/web clients. Leaving the repository unset returns an explicit unconfigured state, not a fake up-to-date result.

The bridge filters drafts, disallowed prereleases and dedicated metadata tags. It fetches a bounded set of `release-manifest.json` assets from canonical GitHub API URLs. Compatible metadata requires schema/application/variant/channel agreement, a published marker, numeric version/build newer than installed, a full commit ID, a supported minimum iOS version, both IPA/simulator artifact names, positive sizes and SHA-256 values. Stable clients do not accept beta metadata. Version/build ordering is numeric; publication time is not the version order.

Successful metadata is cached one hour; transient failures retain the last valid candidate with a stale indicator and back off retries. No incomplete workflow artifact is advertised. The current manifest remains `published:false`, so it cannot masquerade as an available release.

Native source automatically checks after authenticated refresh, throttles per server, supports a manual check and automatic-check preference, shows concise release notes and a Later action, and directs installation through the actual external signing/store workflow. It never claims unsigned IPA installation or silently installs a package. Updates are exposed only with matching OS compatibility. Switching profiles clears update state from the previous server.

The backend comparison/rejection logic and unconfigured route are tested. No published release exists, so live GitHub artifact discovery, native prompts and a completed signed update have not been verified. Full alternate-store installation routing, persistent last-check/candidate cache on device and release history aggregation remain to be completed before release.

The PWA has a separate content-hashed service-worker lifecycle and explicit safe reload. Its waiting worker supplies the bundled structured release notes before reload; the new web build is recorded locally so a post-update summary appears once, with no first-install What's New popup. This is source implementation pending a two-version lifecycle test.
