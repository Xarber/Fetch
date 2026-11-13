# Development

Use Python 3.11+ (3.13 recommended), Node 22+ for TypeScript/branding tooling, existing FFmpeg/FFprobe and optional Deno. README contains installation and two-process start commands. The committed dashboard output allows backend/container deployment without Node at runtime.

`python scripts/configure.py` prompts for a unique initial administrator password, creates `.env` with mode 0600 and lossless base64 bootstrap-password encoding (not encryption) to avoid shell/dotenv interpolation and refuses to overwrite it. `scripts/run.py` loads the file without logging secrets. Docker Compose overrides the local `FETCH_DATA` with `/data`. Do not commit .env, data, signing profiles or private media.

Run `npm run build` after TypeScript or shell changes: this compiles app.js and stamps the service-worker cache with a content hash of the shell. Commit both source and generated output. `npm run branding` reproducibly exports icons from the editable layered SVG. Native project/plist regeneration is optional; committed project files are build inputs.

Branches: testing contains development, beta/main begin at the governance baseline and receive validated promotions only. Temporary branches/worktrees are allowed; none were needed for this initial implementation. Use Conventional Commits. Git signing may require a physically connected hardware key; initial commits were made unsigned with per-command configuration without changing the configured identity.

The new repository is private: Xarber/OpenRecode-Fetch. The user confirmed that public Xarber/Fetch is the original starter repository. See REPOSITORY_REUSE.md for the prepared integration and visibility decision. No public release or deployment is authorized. GitHub Actions usage quotas were not readable with the existing credential scopes; no paid runner execution is assumed or silently enabled by development pushes.
