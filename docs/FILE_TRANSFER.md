# File transfer

A ready job is immutable and has final size/SHA-256. A session requests an artifact-specific six-hour bearer capability. Capabilities are hashed at rest and removed on issuing-device revocation or job deletion. They are intentionally reusable for Range requests until expiry; pairing challenges are the one-use credential. Tokens are never added to URL query strings or access logs.

Starlette FileResponse serves valid byte ranges, length/type/disposition and an explicitly supplied SHA-256 ETag. Job paths must resolve beneath the data/jobs directory. Partials are not exposed. Completion acknowledgement validates the submitted checksum but does not itself delete media.

## Native

Background URLSession uses a stable identifier and persists ticket/task identity, expected bytes and checksum (not the bearer token). On relaunch, tasks are enumerated and reconciled. A temporary download moves synchronously to staging; SHA-256 is streamed on a utility task, size is checked, then the final media file is moved into Documents/Media. Library metadata is persisted before success notification. Background completion is deferred until pending validation finishes.

If no OS task exists for a persisted active transfer, it is marked interrupted; the queue can request a new transfer and retry safely. Cancellation is implemented. URLSession resumeData is not yet implemented. A new transfer retries the full artifact. Force-quit, expiry, OS scheduling and network policy can prevent continuation. Native background behavior has not been tested on a simulator or device.

On relaunch, interrupted staging files and artifacts moved before metadata persistence are revalidated and reconciled. An in-memory verification set prevents concurrent finalization of the same ticket. This recovery path is implemented but requires native crash/lifecycle validation.

## Browser

Fetch validates length and SHA-256 before offering a browser download. It currently buffers files in memory and limits this path to 128 MiB, directing larger transfers to the native client. Download completion/actual file save is controlled by the browser; server acknowledgement means bytes verified, not confirmed filesystem placement. Streaming File System Access saving and browser transfer cancellation/progress remain open.

The native library also implements filename/title rename, duplication, movement into user-named managed subfolders, sorting, file information and explicit deletion. File operations preserve the original on metadata persistence failure where possible. These controls have not been executed on iOS; crash recovery during a library reorganization still needs native validation.
