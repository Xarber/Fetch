# Remaining implementation and verification

This is a development implementation, not a completed production release. The requested scope is larger than the verified deliverable.

## Essential before native release

- Restore access to Xcode or authorize an appropriately budgeted remote build; compile both targets and resolve any SDK/Swift concurrency diagnostics.
- Validate signing/App Groups, Share Extension, Keychain, Photos/Files/Quick Look, QR camera fallback, URLSession restoration and integrity recovery on real iPhone/iPad.
- Test lifecycle/network/storage failures, accessibility, Dynamic Type, layouts, dark appearance and background notifications.
- Execute Docker build/Compose/health and backup/restore on both intended host architectures; enforce host egress and hard storage isolation before hostile exposure.
- Complete privacy cleanup/inspection retention, live release discovery validation through the implemented private metadata bridge, complete structured developer changelog generation and native release validation.

## Requested features still incomplete

Playlist inspection/item selection, richer metadata/thumbnails in the client, named preset editing UI, device discovery, transfer resume data and advanced scheduling, browser streaming/progress for large files, Ideas batch/filter/sort/Markdown flows, two-version PWA lifecycle validation, source-licensed App Store product, and a complete plugin registry/runtime are not claimed as delivered. Basic batches, formats, audio conversion, queue and transfers are real implementations.

## Optional on-device engine research

Ordinary iOS apps cannot run Linux Docker or unrestricted yt-dlp subprocesses. A bundled Python runtime would need an iOS-compatible embedding, signed native extensions, extractor/EJS compatibility, supported JavaScript execution, an appropriately licensed FFmpeg framework, memory/energy limits and a distribution-policy review. Background extraction remains OS-constrained. No JIT, jailbreak or dynamically downloaded executable dependency is assumed.

No iOS local Python engine has been built or demonstrated. A macOS proof-of-concept would not establish iOS compatibility. Preserve the remote API/domain seam for a future local adapter, but do not replace the tested server path with speculative code.

## Interoperability and sync

Explicit Files/share exports are the current Harmony/Echo boundary. No private data is read or shared automatically. Bonjour discovery and direct device backup/sync are potential future adapters, not delivered continuous P2P functionality.
