# Reusing Xarber/Fetch

The user confirmed that [Xarber/Fetch](https://github.com/Xarber/Fetch) is the original repository for this project. Its public `master` at `ea40c81f5ccb1b6402416bb25cd436d7000e8ad4` contains the Expo SDK 57 starter, the original Expo MIT license and two historical commits. The inspected source has the stock Expo welcome and explore screens. There were no releases, tags or repository rulesets in the inspected state.

The review branch keeps the original commits as ancestors and retains the starter tree under `legacy/expo/`, including its MIT license. Fetch's backend, dashboard and native code retain AGPL-3.0-only. The preserved starter is not an Android implementation of the downloader. Future Android work can use Expo and the existing typed HTTP API. Native background transfers and sharing remain platform-specific.

The public implementation is integrated through the original repository's `testing` branch. Both histories are ancestors and the preserved Expo subtree is byte-for-byte identical to the original tree. The original master remains a historical reference. The private OpenRecode-Fetch repository is retained as the pre-publication development history.
