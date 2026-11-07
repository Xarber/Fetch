# Fetch branding

The user supplied the name **Fetch** and tagline **Your media. Your device. Your control.** They are preserved. No global name/trademark clearance is claimed. The existing unrelated public repository named Fetch is not reused; the private development repository is OpenRecode-Fetch.

Accent: `#6269F5`. Highlight: `#8287FF`. Deep violet: `#535AE1`. Light background: `#F7F8FB`. Dark background: `#13141C`. Primary text: `#242638`. Typography is the system sans-serif (SF on Apple platforms), with semantic native text sizes and a restrained web hierarchy.

`assets/branding/icon-master.svg` is the editable source. Stable groups: background, highlight, download-symbol (stem/arrow), tray. Gradient definitions remain editable. The download arrow enters a tray to communicate saving and ownership. White geometry remains identifiable at small sizes. Dark and monochrome SVG variants are generated separately.

`npm run branding` uses locked Sharp tooling to export PWA 192/512, maskable 512 and Apple Touch 180 PNGs, an SVG favicon and an opaque 1024 iOS AppIcon catalog. The iOS export removes the pre-rounded outer background so the OS applies its own mask. There are no Android/desktop assets because those native platforms are not currently implemented.

Editable SVG variants prepare independent foreground/background appearance. Native layered Icon Composer/Liquid Glass icon assets and iOS dark/tinted catalog variants are not implemented or validated. App UI uses system materials as a compatible fallback; no unsupported Liquid Glass API is assumed.

Use the icon with breathing room and preserve contrast. Do not label browser screenshots as native screenshots or use generated mockups as proof of functionality. Copyright © 2026 OpenRecode contributors; original branding assets are AGPL-3.0-only with the project.
