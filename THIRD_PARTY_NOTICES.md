# Third-party notices and distribution review

Original Fetch code/branding: copyright © 2026 OpenRecode contributors, AGPL-3.0-only. Full license is LICENSE. Network-accessible modified versions must honor AGPL source availability; private repository visibility does not waive obligations to users.

Installed metadata reviewed during implementation:

| Component | License metadata |
|---|---|
| yt-dlp 2026.10.26 | Unlicense |
| yt-dlp-ejs 0.8.0 | Unlicense AND MIT AND ISC |
| FastAPI | MIT |
| Starlette / Uvicorn | BSD-3-Clause |
| Pydantic | MIT |
| argon2-cffi | MIT |
| qrcode | BSD |
| Pillow | HPND-family license; preserve distribution notices |
| Requests | Apache-2.0 |
| Mutagen | GPL-2.0-or-later (use a compatible later GPL version when combined) |
| PyCryptodome | BSD / public-domain components |
| Deno | MIT plus bundled dependency notices |
| TypeScript | Apache-2.0 |
| Playwright | Apache-2.0 (development/testing only) |
| Sharp | Apache-2.0; bundled libvips/dependencies retain their licenses |

FFmpeg licensing depends on build options and libraries; Debian/Homebrew binaries may enable GPL codecs. LGPL-only status is not assumed. The container build must retain relevant notices and provide required corresponding sources/relinking materials where applicable. Before publishing an image, record its exact image digests, complete package license inventory, FFmpeg build configuration and source availability. This initial metadata review is not a complete legal clearance or container SBOM.

No third-party media is bundled. Test audio/video is generated from synthetic FFmpeg sources. System Apple frameworks are supplied by the OS, not relicensed as Fetch code. Browser screenshots show only isolated QA media. No App Store license compatibility or source-distribution exemption is claimed.
