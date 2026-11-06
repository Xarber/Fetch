# Data model

`fetch.sqlite3` uses WAL, foreign keys, transaction rollback on failure and schema version 1.

| Table | Purpose |
|---|---|
| users | administrator ID and Argon2 password hash |
| devices | owner, name, hashed session token, administrator flag, expiry |
| pairing | hashed one-use challenge, owner, expiry |
| inspections | owner, source URL, sanitized format metadata, creation time |
| jobs | owner, inspection, typed selection, state, priority, timestamps, revision, actual progress, running flag, relative artifact path, size, checksum, idempotency key |
| transfers | artifact/device foreign keys, hashed capability, expiry and verified receipt flag |
| presets | owner-scoped named selection |
| settings | concurrency, retention and worker heartbeat |

`(owner, request_key)` is unique. Clients retain a request key while retrying creation, preventing duplicate queue entries after network uncertainty. Queue claims use `BEGIN IMMEDIATE`. Job removal cascades transfer removal. Device revocation cascades transfer revocation. Relative paths are generated internally; transfer paths are revalidated under the media directory.

Inspections retain submitted URLs and therefore may be private. They are not sent to diagnostics; extractor errors are replaced with sanitized failure descriptions. Automatic inspection/history expiry is not yet implemented: ready artifacts expire according to policy; explicit job deletion removes its file and history but may leave the inspection row for future deduplicated history. See privacy limitations.

Native Application Support contains server profiles, per-server cached jobs, Ideas, local file metadata and transfer records as atomic JSON. Credentials are exclusively in Keychain. Documents/Media contains only verified media. Transfer records do not persist the bearer token. App Group UserDefaults stores pending shared URLs until consumed by the main app. Native storage migrations and corrupted-store recovery need additional device validation; JSON loading currently preserves unreadable files and falls back to empty UI state.
