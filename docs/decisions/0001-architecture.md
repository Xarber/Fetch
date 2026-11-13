# Architecture decision: native client and isolated worker

Fetch implementation began in an empty local workspace. The original Expo starter was subsequently confirmed to be part of the same project. See [repository reuse](../REPOSITORY_REUSE.md). SwiftUI is the primary client because background URLSession, Keychain, Quick Look, Photos, document export, and a Share Extension are essential. No JavaScript runtime is embedded on iOS. iOS 17 is the initial minimum; system materials provide older-system fallbacks.

FastAPI and a dedicated Python worker share a WAL SQLite database on one host. A singleton coordinator claims durable jobs; each job runs in a separate process group. This is deliberately not a distributed multi-host queue. API inspection runs in a bounded subprocess. Native and web clients use the same versioned API; transfer state is separate from processing state.

Acceptance: real generated authorized media must pass inspection, download, FFmpeg audio conversion, authenticated range transfer and checksum verification. Negative tests exercise SSRF, credentials, ownership and input validation. Native compilation and lifecycle validation require a mounted Xcode installation/device; container validation requires Docker.

Security: every yt-dlp HTTP request uses a DNS-pinning egress proxy. FFmpeg postprocessing is restricted to local protocols. Deployment on an Internet-facing host additionally requires network-level egress filtering and TLS. No public deployment is authorized. No source permissions are inferred from URL accessibility.

Future extensions belong behind the typed selection schema and client API, not arbitrary command flags. Optional local execution is deferred because no iOS Python/FFmpeg runtime has been validated.
