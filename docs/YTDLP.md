# yt-dlp engine

The installed maintained Python API is used in short-lived subprocesses. Version pin at implementation: **2026.10.26**, `yt-dlp-ejs` **0.8.0**. See the runtime lock and authenticated `/versions` for actual deployment versions.

Official integration and JavaScript guidance: [yt-dlp README](https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp), [EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

Each instance receives a loopback HTTP proxy. Every HTTP request and CONNECT tunnel resolves all addresses, rejects unsafe results, connects to the validated numeric address and pins the connection. HTTPS certificate verification is retained; redirect requests are validated through the same proxy. Default ports are 80 and 443. Nonstandard external ports are not accepted. No cookie file, browser cookie extraction, arbitrary CLI flags or user credentials are accepted.

Installed-source inspection established that the Python API does **not** honor a `plugin_dirs` dictionary setting as a global disable switch. Fetch therefore sets upstream's `YTDLP_NO_PLUGINS=1` before constructing any downloader. A regression test supplies a malicious plugin and verifies it is not executed. Remote components are disabled, so EJS must be bundled through the pinned package rather than fetched dynamically.

Deno is explicitly enabled when installed; the container copies a pinned Deno 2.5.6 runtime. Some extractors still need source-specific support and authorization. The fixture tests prove the installed engine can inspect/download controlled media; they do not establish universal source compatibility, or YouTube challenge success.

Engine upgrades are administrator-controlled dependency/image changes. Stable/pinned versions can be tested by changing the lock on a development branch. Nightly selection is not an end-user control and no arbitrary build is auto-installed. Record the old image digest and lock, run workflow/security fixtures, stage the new image, then promote. Roll back to the previous image with the original data preserved. Runtime upgrade UI and automatic provenance/signature checks are not implemented.
