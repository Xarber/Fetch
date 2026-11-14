// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
import Observation
import CryptoKit
import UserNotifications

struct TransferRecord: Codable, Identifiable {
    var id: String
    var jobId: String
    var server: ServerProfile
    var filename: String
    var title: String
    var expectedSize: Int64
    var checksum: String
    var state = "transferring"
    var received: Int64 = 0
    var error: String?
}

@MainActor @Observable final class TransferManager: NSObject, @preconcurrency URLSessionDownloadDelegate {
    static let shared = TransferManager()
    var records: [TransferRecord] = AppStore.load("transfers.json", default: [])
    var library: [LocalMedia] = AppStore.load("library.json", default: [])
    private var pendingVerification = 0
    private var verifyingIDs = Set<String>()
    private var finishedEvents = false
    var completionHandler: (() -> Void)?
    var tasks: [String: URLSessionDownloadTask] = [:]
    @ObservationIgnored private lazy var session: URLSession = {
        let config = URLSessionConfiguration.background(withIdentifier: "org.openrecode.fetch.transfers")
        config.sessionSendsLaunchEvents = true
        config.allowsCellularAccess = !UserDefaults.standard.bool(forKey: "wifiOnly")
        config.isDiscretionary = false
        return URLSession(configuration: config, delegate: self, delegateQueue: .main)
    }()
    static var files: URL {
        let url = URL.documentsDirectory.appendingPathComponent("Media", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }
    func persist() {
        do { try AppStore.save(records, name: "transfers.json"); try AppStore.save(library, name: "library.json") }
        catch { records.firstIndex(where: { $0.state == "transferring" }).map { records[$0].error = "Could not persist transfer state" } }
    }
    func restore() {
        session.getAllTasks { tasks in
            Task { @MainActor in
                let ids = Set(tasks.compactMap(\.taskDescription))
                for task in tasks {
                    if let download = task as? URLSessionDownloadTask, let id = task.taskDescription { self.tasks[id] = download }
                }
                for index in self.records.indices where ["transferring", "verifying"].contains(self.records[index].state) && !ids.contains(self.records[index].id) {
                    let record = self.records[index]
                    let staging = AppStore.support.appendingPathComponent(record.id + ".staging")
                    let finalized = Self.files.appendingPathComponent(record.filename)
                    if FileManager.default.fileExists(atPath: staging.path) {
                        self.beginVerification(record, at: staging)
                    } else if FileManager.default.fileExists(atPath: finalized.path) {
                        self.beginVerification(record, at: finalized)
                    } else {
                        self.records[index].state = "interrupted"
                        self.records[index].error = "Transfer interrupted. Retry from the server queue."
                    }
                }
                self.persist()
            }
        }
    }
    func start(_ ticket: TransferTicket, job: DownloadJob, profile: ServerProfile) throws {
        guard !records.contains(where: { $0.jobId == job.id && $0.server.id == profile.id && $0.state == "transferring" }) else { return }
        let available = try Self.files.resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey]).volumeAvailableCapacityForImportantUsage ?? 0
        guard available > ticket.size + 50_000_000 else { throw APIError.message("Not enough storage for this file") }
        let name = job.id + "-" + URL(fileURLWithPath: ticket.filename).lastPathComponent
        let record = TransferRecord(id: ticket.id, jobId: job.id, server: profile, filename: name, title: job.title, expectedSize: ticket.size, checksum: ticket.sha256)
        records.append(record); persist()
        var request = URLRequest(url: profile.url.appendingPathComponent(ticket.path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))))
        request.setValue("Bearer " + ticket.token, forHTTPHeaderField: "Authorization")
        request.allowsCellularAccess = !UserDefaults.standard.bool(forKey: "wifiOnly")
        let task = session.downloadTask(with: request)
        task.taskDescription = ticket.id; tasks[ticket.id] = task; task.resume()
    }
    func cancel(_ record: TransferRecord) {
        tasks[record.id]?.cancel()
        if let index = records.firstIndex(where: { $0.id == record.id }) { records[index].state = "cancelled"; persist() }
    }
    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didWriteData bytesWritten: Int64, totalBytesWritten: Int64, totalBytesExpectedToWrite: Int64) {
        if let index = records.firstIndex(where: { $0.id == downloadTask.taskDescription }) { records[index].received = totalBytesWritten }
    }
    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didFinishDownloadingTo location: URL) {
        guard let index = records.firstIndex(where: { $0.id == downloadTask.taskDescription }) else { return }
        let record = records[index]
        guard let response = downloadTask.response as? HTTPURLResponse, response.statusCode == 200 else {
            records[index].state = "failed"; records[index].error = "Transfer authorization expired or server returned an error"; persist(); return
        }
        let staging = AppStore.support.appendingPathComponent(record.id + ".staging")
        do {
            try? FileManager.default.removeItem(at: staging)
            try FileManager.default.moveItem(at: location, to: staging)
            beginVerification(record, at: staging)
        } catch { finish(record.id, state: "failed", error: error.localizedDescription) }
    }
    private func beginVerification(_ record: TransferRecord, at source: URL) {
        guard verifyingIDs.insert(record.id).inserted else { return }
        pendingVerification += 1
        if let index = records.firstIndex(where: { $0.id == record.id }) { records[index].state = "verifying" }
        persist()
        Task {
            defer { verifyingIDs.remove(record.id); pendingVerification -= 1; completeBackgroundEventsIfReady() }
            do {
                let checksum = try await Self.checksum(source)
                let size = try source.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? -1
                guard checksum == record.checksum, Int64(size) == record.expectedSize else { throw APIError.message("File integrity check failed") }
                let destination = Self.files.appendingPathComponent(record.filename)
                if source != destination {
                    if FileManager.default.fileExists(atPath: destination.path) { try FileManager.default.removeItem(at: destination) }
                    try FileManager.default.moveItem(at: source, to: destination)
                }
                try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication], ofItemAtPath: destination.path)
                library.removeAll { $0.id == record.jobId }
                library.append(LocalMedia(id: record.jobId, filename: record.filename, title: record.title, size: record.expectedSize, sha256: checksum, serverId: record.server.id))
                finish(record.id, state: "completed")
                let api = FetchAPI(profile: record.server, token: Keychain.read(record.server.id))
                struct Verified: Decodable { let verified: Bool }
                let _: Verified? = try? await api.send("transfers/\(record.id)/complete", object: ["sha256": checksum])
                let content = UNMutableNotificationContent(); content.title = "Saved to Fetch"; content.body = record.title
                try? await UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: record.id, content: content, trigger: nil))
            } catch {
                if source.pathExtension == "staging" { try? FileManager.default.removeItem(at: source) }
                finish(record.id, state: "failed", error: error.localizedDescription)
            }
        }
    }
    nonisolated static func checksum(_ url: URL) async throws -> String {
        try await Task.detached(priority: .utility) {
            let handle = try FileHandle(forReadingFrom: url); defer { try? handle.close() }
            var hash = SHA256()
            while let data = try handle.read(upToCount: 1024 * 1024), !data.isEmpty { hash.update(data: data) }
            return hash.finalize().map { String(format: "%02x", $0) }.joined()
        }.value
    }
    private func finish(_ id: String, state: String, error: String? = nil) {
        if let index = records.firstIndex(where: { $0.id == id }) { records[index].state = state; records[index].error = error; persist() }
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: (any Error)?) {
        if let error, let id = task.taskDescription, records.first(where: { $0.id == id })?.state != "cancelled" { finish(id, state: "failed", error: error.localizedDescription) }
        if let id = task.taskDescription { tasks.removeValue(forKey: id) }
    }
    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        finishedEvents = true
        completeBackgroundEventsIfReady()
    }
    private func completeBackgroundEventsIfReady() {
        guard finishedEvents, pendingVerification == 0 else { return }
        completionHandler?(); completionHandler = nil; finishedEvents = false
    }
    func rename(_ media: LocalMedia, to title: String) throws {
        let cleaned=title.trimmingCharacters(in:.whitespacesAndNewlines)
        guard !cleaned.isEmpty,cleaned.count<=100 else { throw APIError.message("Use a name between 1 and 100 characters") }
        let safe=cleaned.unicodeScalars.map { CharacterSet.alphanumerics.union(CharacterSet(charactersIn:" _-.")).contains($0) ? String($0) : "_" }.joined()
        let previous=Self.files.appendingPathComponent(media.filename)
        let folder=(media.filename as NSString).deletingLastPathComponent
        let name=media.id+"-"+safe+"."+previous.pathExtension
        let filename=folder.isEmpty ? name : folder+"/"+name
        var next=library
        guard let index=next.firstIndex(where:{$0.id==media.id}) else { return }
        let destination=Self.files.appendingPathComponent(filename)
        if previous != destination { try FileManager.default.moveItem(at:previous,to:destination) }
        next[index].filename=filename;next[index].title=cleaned
        do { try AppStore.save(next,name:"library.json"); library=next }
        catch { if previous != destination { try? FileManager.default.moveItem(at:destination,to:previous) };throw error }
    }
    func move(_ media:LocalMedia,to folder:String) throws {
        let cleaned=folder.trimmingCharacters(in:.whitespacesAndNewlines)
        guard cleaned.count<=80,cleaned.unicodeScalars.allSatisfy({CharacterSet.alphanumerics.union(CharacterSet(charactersIn:" _-")).contains($0)}) else { throw APIError.message("Use a simple folder name without slashes or dots") }
        let basename=(media.filename as NSString).lastPathComponent
        let filename=cleaned.isEmpty ? basename : cleaned+"/"+basename
        guard filename != media.filename else { return }
        let source=Self.files.appendingPathComponent(media.filename)
        let destination=Self.files.appendingPathComponent(filename)
        try FileManager.default.createDirectory(at:destination.deletingLastPathComponent(),withIntermediateDirectories:true)
        try FileManager.default.moveItem(at:source,to:destination)
        var next=library
        guard let index=next.firstIndex(where:{$0.id==media.id}) else { return }
        next[index].filename=filename
        do { try AppStore.save(next,name:"library.json");library=next }
        catch { try? FileManager.default.moveItem(at:destination,to:source);throw error }
    }
    func duplicate(_ media:LocalMedia) throws {
        var copy=media;copy.id=UUID().uuidString;copy.title += " (copy)"
        copy.filename=copy.id+"."+URL(fileURLWithPath:media.filename).pathExtension
        let destination=Self.files.appendingPathComponent(copy.filename)
        try FileManager.default.copyItem(at:Self.files.appendingPathComponent(media.filename),to:destination)
        let next=library+[copy]
        do { try AppStore.save(next,name:"library.json");library=next }
        catch { try? FileManager.default.removeItem(at:destination);throw error }
    }
    func remove(_ media: LocalMedia) throws {
        let source=Self.files.appendingPathComponent(media.filename)
        let trash=AppStore.support.appendingPathComponent(UUID().uuidString+".trash")
        try FileManager.default.moveItem(at:source,to:trash)
        let next=library.filter { $0.id != media.id }
        do { try AppStore.save(next,name:"library.json");library=next;try? FileManager.default.removeItem(at:trash) }
        catch { try? FileManager.default.moveItem(at:trash,to:source);throw error }
    }
}
