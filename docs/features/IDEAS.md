# Developer Ideas

Ideas are independent of media history and work offline. Unlock Developer Options by tapping the version three times; access disappears when changing main tabs or after 30 seconds without interaction. Native destinations also gate access after expiry. This is a convenience gate, not a substitute for server permissions.

Schema v1: `schemaVersion:1`, `project:"org.openrecode.fetch"`, `exportedAt` Unix seconds, `ideas` array. Each entry has stable id, title, description, category, priority, status, created/modified timestamps, implementationReferences and history. Canonical statuses are pending, approved, deferred, inProgress, implemented, rejected. The original specification's New/Under consideration map to pending; no recorded data was migrated from a prior app.

Native storage is atomic protected JSON in Application Support. Browser storage is origin-local JSON. Create/edit/delete/duplicate/search, history, category/priority/status, JSON import preview and full export are implemented. Conflicting stable IDs preserve the incoming version as a separately identified conflict copy; identical entries deduplicate. Unknown schemas/projects and malformed entries are rejected. Unreadable collections are preserved rather than overwritten.

Native and browser use the same interchange identifiers/statuses/timestamps. JSON is the primary portable format. Bulk operations, dedicated filter/sort controls, per-idea screenshot attachment, Markdown export, automatic repository sync and released-changelog navigation remain incomplete. Current lists sort by modification time; search is available.

`docs/IDEAS.json` is the agent entry point. It currently contains zero ideas. Neither browser nor iOS private storage is automatically accessible to coding agents; use Export JSON. Future imports must be reviewed and merged explicitly. Do not automatically implement unrelated imported ideas. Mark implemented only after appropriate verification and attach commits/version/release identifiers; pending work must never appear as released. `release.json.idea_ids` is prepared for verified released links, but no published release exists.
