# Builds and releases

No stable/prerelease has been published, no public update source exists, and no deployment has occurred. Native build workflows are prepared but have not run. Android APK/AAB are not applicable because Android is not a supported target in this specification.

The private repository is Xarber/OpenRecode-Fetch. `testing` receives development; beta/main begin at the governance-only baseline until explicit validated promotion. No full build/release is automatically triggered on testing. Pull requests can run checks; native builds are manual or run on beta/main. Existing unrelated Xarber/Fetch remains untouched.

`checks.yml` prepares Python fixtures, strict TypeScript and Docker build checks. `ios.yml` runs unsigned device and simulator jobs in parallel with fail-fast disabled, uploads each successful artifact and requires both jobs for validation. Metadata uses release.json version/build and the exact commit. The package validator inspects IPA Payload structure, app/extension IDs, platform markers, arm64, version and commit. SHA-256 and sizes are generated only after both artifacts exist.

No workflow publishes a GitHub release or uploads to an external store. Activating those channels requires explicit authorization, successful builds, licensing/source rights review and device validation. Signing identities remain externally managed. A future private update service must securely proxy release metadata; no long-lived GitHub credential belongs in a client.

GitHub runner usage/billing could not be inspected with current scopes. No manual macOS build has been started without confirming the permitted runner budget. Do not infer a successful build from committed workflow files. Respect the three-minute active waiting limit when a workflow is authorized.

Unsigned device IPAs need signing before ordinary installation. Simulator `.app.zip` is never a device IPA. Preserve archive executable permissions. The release script refuses incomplete artifact sets and creates no invented download URLs. AltSources/Obtainium endpoints are intentionally not activated before genuine authorized releases; the mutable metadata release must never be offered as an application update.

Native Updates uses the server-side GitHub metadata bridge described in features/UPDATES.md. Without configuration or a published compatible manifest it reports the actual unavailable/unconfigured state. Automatic/manual checking and compatibility filtering are implemented; live release/native installation validation, channel switching and complete developer commit-history generation remain open. PWA shell update detection is implemented independently.
