# iOS and iPadOS

The client targets iOS/iPadOS 17+ with Swift 6, SwiftUI, Observation, Foundation, Keychain, Quick Look, Photos and VisionKit. There are no third-party native dependencies. iOS is the only native target currently requested; Android/macOS applications are not implemented.

## Build and signing

Open `ios/Fetch.xcodeproj` and select a development team for Fetch and FetchShare. Bundle IDs are `org.openrecode.fetch` and `org.openrecode.fetch.share`. Both targets require the App Group `group.org.openrecode.fetch`. Register/provision it with your Apple team, or consistently change it in both entitlements and Swift source. Do not change an established distributed signing identity.

The committed Xcode project can be regenerated with `ruby scripts/generate_xcode_project.rb` after installing the small xcodeproj Ruby dependency in your existing environment. Regeneration is not needed to build. Plists are regenerated with `python scripts/create_plists.py`. Full Xcode and an appropriate SDK are required; command-line Swift parsing is not an iOS build.

Simulator:

```sh
xcodebuild -project ios/Fetch.xcodeproj -scheme Fetch -configuration Debug \
  -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath build CODE_SIGNING_ALLOWED=NO FETCH_COMMIT="$(git rev-parse HEAD)" build
```

Choose an available simulator in Xcode and Run, or install `build/Build/Products/Debug-iphonesimulator/Fetch.app` with the existing simulator tools. No Metro/development server is required.

Unsigned device release:

```sh
xcodebuild -project ios/Fetch.xcodeproj -scheme Fetch -configuration Release \
  -sdk iphoneos -destination 'generic/platform=iOS' -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO FETCH_COMMIT="$(git rev-parse HEAD)" build
mkdir -p build/package/Payload
cp -R build/Build/Products/Release-iphoneos/Fetch.app build/package/Payload/
ditto -c -k --sequesterRsrc --keepParent build/package/Payload build/Fetch-ios-unsigned.ipa
```

Unsigned IPA requires signing through a compatible authorized tool before ordinary installation. Its Share Extension and App Group need correct entitlements; do not claim a generic signing tool preserves them automatically.

Simulator archive:

```sh
ditto -c -k --sequesterRsrc --keepParent \
  build/Build/Products/Debug-iphonesimulator/Fetch.app build/Fetch-ios-simulator.app.zip
```

Physical iPhone: connect your device, enable Developer Mode as required by iOS, select it in Xcode, configure your team and Run. Trust the development signing profile when the system requires it. A trusted HTTPS server must be reachable from the phone; the phone's localhost is not the Mac server. No developer account credentials or signing secrets are included in the project.

## Native workflow

Settings stores multiple named HTTPS profiles and Keychain credentials. Administrator login or one-use pairing connects to a server. QR codes contain a server URL and expiring challenge, never an admin password. VisionKit scanning uses the system camera permission and manual fallback on unsupported hardware. `fetch://pair?...` and `fetch://download?url=...` are registered deep-link flows.

Home uses explicit Paste, never automatic clipboard reads. Media selection uses server metadata and a rights confirmation. Queue and history are server states; transfers have their own progress section. Local files remain available offline. Verified files open through Quick Look, export via ShareLink/Files, and compatible video can be added to Photos with user permission. App Group Share Extension stores deduplicated links for the main app without long-running downloads.

## Verification required

The configured Xcode symlink points to an unmounted `/Volumes/MacOS_Data/Development/Xcode-beta.app`. No IPA/simulator build, native UI typecheck, signing, Share Extension launch, Keychain operation, camera scanning, Photos export or background lifecycle test has succeeded here. Swift syntax parsing and portable core behavioral checks are the available evidence.

Before release: compile both targets, fix SDK/concurrency diagnostics, test Dynamic Type/VoiceOver, portrait/landscape/iPad layouts, keyboard and safe areas, locked screen/suspension/system termination/network failures, integrity recovery, permission denial, and extension imports from real apps. Native source implementation is not proof of native functionality.

## Distribution policy

The current app is an independently distributed development configuration. Backend `FETCH_DISTRIBUTION=store` requires an explicit source host allowlist and fails closed when empty. This server switch alone does **not** establish an App Store-compatible client: a separately constrained native product, documented source rights, license review and actual App Review approval are still required. No App Store submission or dynamic post-review unlock is implemented.
