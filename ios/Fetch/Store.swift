// SPDX-License-Identifier: AGPL-3.0-only
import SwiftUI
import Observation

@MainActor @Observable final class AppStore {
    static let managedServer: URL? = {
        guard let address = Bundle.main.object(forInfoDictionaryKey: "FetchServerURL") as? String,
              let url = try? FetchAPI.validatedURL(address), url.scheme == "https" else { return nil }
        return url
    }()

    var updates = UpdateStore()
    var profiles: [ServerProfile] = []
    var selectedId: String = ""
    var jobs: [DownloadJob] = []
    var inspection: Inspection?
    var pairingURL: String?
    var urlInput = ""
    var error: String?
    var connected = false
    var serverStatus: ServerStatus?
    var busy = false
    var diagnostics = "Connect to a server to retrieve diagnostics."
    var selectedTab = 0 { didSet { if selectedTab != oldValue { lockDeveloper() } } }
    var developer = false
    var lastInteraction = Date()
    var taps = 0
    var ideas: [DeveloperIdea] = []
    var welcome = false
    var whatsNew = false
    var api: FetchAPI? {
        guard let profile = profiles.first(where: { $0.id == selectedId }) else { return nil }
        return FetchAPI(profile: profile, token: Keychain.read(profile.id))
    }
    private static var unreadableFiles = Set<String>()
    static let support: URL = {
        let folder = URL.applicationSupportDirectory.appendingPathComponent("Fetch", isDirectory: true)
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        return folder
    }()
    init() {
        profiles = Self.load("servers.json", default: [])
        selectedId = UserDefaults.standard.string(forKey: "server") ?? profiles.first?.id ?? ""
        if let endpoint = Self.managedServer {
            let profile = profiles.first { $0.url == endpoint }
            selectedId = profile?.id ?? ""
        }
        ideas = Self.load("ideas.json", default: [])
        jobs = Self.load("jobs-\(selectedId).json", default: [])
        welcome = Self.managedServer == nil && !UserDefaults.standard.bool(forKey: "welcomed")
        let previous = UserDefaults.standard.string(forKey: "lastVersion")
        whatsNew = previous != nil && previous != Self.version
        UserDefaults.standard.set(Self.version, forKey: "lastVersion")
    }
    static var version: String { Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0.1.0" }
    static var commit: String { Bundle.main.infoDictionary?["FetchCommit"] as? String ?? "development" }
    static func load<T: Decodable>(_ name: String, default value: T) -> T {
        let path = support.appendingPathComponent(name)
        guard FileManager.default.fileExists(atPath: path.path) else { return value }
        guard let data = try? Data(contentsOf: path), let result = try? JSONDecoder().decode(T.self, from: data) else {
            unreadableFiles.insert(name)
            return value
        }
        return result
    }
    static func save<T: Encodable>(_ value: T, name: String) throws {
        guard !unreadableFiles.contains(name) else { throw APIError.message("Existing \(name) could not be read. It was preserved; recover it before saving new data.") }
        let data = try JSONEncoder().encode(value)
        try data.write(to: support.appendingPathComponent(name), options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    }
    func recordIdeas() {
        do { try Self.save(ideas, name: "ideas.json") } catch { self.error = error.localizedDescription }
    }
    func lockDeveloper() { developer = false; taps = 0 }
    func versionTapped() {
        guard Self.managedServer == nil else { return }
        if Date().timeIntervalSince(lastInteraction) > 3 { taps = 0 }
        lastInteraction = Date(); taps += 1
        if taps == 3 { developer = true; taps = 0 }
    }
    func refresh() async {
        guard let api else { connected = false; return }
        let id = api.profile.id
        do {
            async let latest: [DownloadJob] = api.request("downloads")
            async let status: ServerStatus = api.request("status")
            let (loaded, health) = try await (latest, status)
            guard selectedId == id else { return }
            jobs = loaded; serverStatus = health; connected = true
            try Self.save(jobs, name: "jobs-\(id).json")
            await updates.check(using:api)
        } catch { connected = false }
    }
    func inspect() async {
        guard let api else { error = "Add a server in Settings first."; return }
        busy = true; defer { busy = false }
        do { inspection = try await api.send("media/inspect", object: ["url": urlInput]) }
        catch is CancellationError { }
        catch { self.error = error.localizedDescription }
    }
    func create(_ inspection: Inspection, selection: Selection, requestKey: String) async {
        guard let api else { return }
        do {
            struct Body: Encodable { let inspectionId: String; let selection: Selection; let requestKey: String; let authorized = true }
            let _: DownloadJob = try await api.request("downloads", method: "POST", body: FetchAPI.encoder.encode(Body(inspectionId: inspection.id, selection: selection, requestKey: requestKey)))
            self.inspection = nil; urlInput = ""; selectedTab = 1; await refresh()
        } catch { self.error = error.localizedDescription }
    }
    func action(_ action: String, job: DownloadJob) async {
        guard let api else { return }
        do {
            let _: DownloadJob = try await api.request("downloads/\(job.id)/\(action)", method: "POST")
            await refresh()
        } catch { self.error = error.localizedDescription }
    }
    func delete(_ job: DownloadJob) async {
        guard let api else { return }
        do { let _: EmptyResponse = try await api.request("downloads/\(job.id)",method:"DELETE"); await refresh() }
        catch { self.error = error.localizedDescription }
    }
    func transfer(_ job: DownloadJob) async {
        guard let api else { return }
        do {
            let ticket: TransferTicket = try await api.request("downloads/\(job.id)/transfer", method: "POST")
            try TransferManager.shared.start(ticket, job: job, profile: api.profile)
        } catch { self.error = error.localizedDescription }
    }
    func readSharedLinks() {
        guard let defaults = UserDefaults(suiteName: "group.org.openrecode.fetch"), let links = defaults.stringArray(forKey: "pendingURLs"), let first = links.first else { return }
        urlInput = first; selectedTab = 0
        defaults.set(Array(links.dropFirst()), forKey: "pendingURLs")
    }
}
