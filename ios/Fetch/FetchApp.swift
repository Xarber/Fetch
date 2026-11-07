// SPDX-License-Identifier: AGPL-3.0-only
import SwiftUI
import UIKit

@MainActor final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, handleEventsForBackgroundURLSession identifier: String, completionHandler: @escaping () -> Void) {
        TransferManager.shared.completionHandler = completionHandler
        TransferManager.shared.restore()
    }
}
@main struct FetchApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @State private var store = AppStore()
    @Environment(\.scenePhase) private var phase
    var body: some Scene {
        WindowGroup {
            RootView().environment(store).tint(Color(red: 98/255, green: 105/255, blue: 245/255))
                .onOpenURL { url in
                    if url.scheme == "fetch", url.host == "pair" {
                        store.pairingURL = url.absoluteString; return
                    }
                    if url.scheme == "fetch", let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
                       let source = components.queryItems?.first(where: { $0.name == "url" })?.value {
                        store.urlInput = source; store.selectedTab = 0
                    }
                }
                .onChange(of: phase) { _, phase in
                    if phase == .active { store.readSharedLinks(); Task { await store.refresh() } }
                }
                .task {
                    TransferManager.shared.restore(); store.readSharedLinks()
                    while !Task.isCancelled {
                        if phase == .active { await store.refresh() }
                        if store.developer && Date().timeIntervalSince(store.lastInteraction) >= 30 { store.lockDeveloper() }
                        try? await Task.sleep(for: .seconds(3))
                    }
                }
        }
    }
}
