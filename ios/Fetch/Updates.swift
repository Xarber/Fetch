// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
import Observation

@MainActor @Observable final class UpdateStore {
    var result: UpdateStatus?
    var checking = false
    var prompt = false
    private var lastAttempt: Date?
    private var serverID: String?
    var message = "No update check yet."
    var lastSuccessfulCheck: Date?
    func check(using api: FetchAPI, force: Bool = false) async {
        guard !checking else { return }
        if serverID != api.profile.id { serverID=api.profile.id; lastAttempt=nil; lastSuccessfulCheck=nil; result=nil }
        if !force {
            guard UserDefaults.standard.object(forKey: "automaticUpdates") == nil || UserDefaults.standard.bool(forKey:"automaticUpdates") else { return }
            if let lastAttempt, Date().timeIntervalSince(lastAttempt) < 3600 { return }
        }
        lastAttempt = Date(); checking = true; defer { checking = false }
        do {
            let build=Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
            let os=ProcessInfo.processInfo.operatingSystemVersion
            let status:UpdateStatus=try await api.request("updates?version=\(AppStore.version)&build=\(build)&channel=\(Self.channel)&variant=extended&os_version=\(os.majorVersion).\(os.minorVersion).\(os.patchVersion)")
            result=status
            if let candidate=status.candidate,status.status=="update_available" {
                let identity="\(candidate.version)-\(candidate.build)"
                if UserDefaults.standard.string(forKey:"lastUpdatePrompt") != identity { prompt=true; UserDefaults.standard.set(identity,forKey:"lastUpdatePrompt") }
            }
            message=["unconfigured":"No release endpoint configured by this server.","unavailable":"Release metadata is temporarily unavailable.","no_releases":"No published compatible releases yet.","up_to_date":"You’re up to date.","update_available":"A newer version is available.","stale":"Cached release information; the latest check failed."][status.status] ?? "Release status unavailable."
            if !["stale","unavailable","unconfigured"].contains(status.status) { lastSuccessfulCheck=Date() }
        } catch { message=error.localizedDescription }
    }
    static var channel:String {
        Bundle.main.infoDictionary?["FetchChannel"] as? String ?? "stable"
    }
}
