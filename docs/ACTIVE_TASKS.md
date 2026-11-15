# Active task queue

| ID | Request | Status | Evidence and next action |
|---|---|---|---|
| FETCH-01 | Build and validate iOS packages | Implemented | Both build jobs passed in run 43592395339. Artifact validation rejected safe macOS temp paths. Commit 3674074 canonicalizes the extraction root. Verify the replacement run and inspect the packages. |
| FETCH-02 | Complete the X-Center download flow | Blocked | HTTPS and login verified at 0440f1b. Worker storage is below the 2 GiB floor in the last measured deployment. Recheck allocation and exercise an authorized controlled transfer when capacity permits. |
| FETCH-03 | Apply updated UADS | In Progress | Manifest, registry, validator and CI integration added. Verify CI and progressively expand requirement coverage. |
| FETCH-04 | Close new feature and release gaps | Queued | Add onboarding and platform screenshots, isolated sample rendering, managed server switching, live landing release discovery and PWA installation. Validate platform behavior and document release recovery and operations. Native public distribution depends on validated artifacts and publication authorization. |
