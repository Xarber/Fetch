// SPDX-License-Identifier: AGPL-3.0-only
import Foundation

struct MediaFormat: Codable, Identifiable, Sendable {
    let formatId: String
    let ext: String?
    let vcodec: String?
    let acodec: String?
    let height: Double?
    let width: Double?
    let fps: Double?
    let tbr: Double?
    let filesize: Double?
    let filesizeApprox: Double?
    var id: String { formatId }
    var label: String {
        [formatId, ext, height.map { "\(Int($0))p" }, vcodec, acodec].compactMap { $0 }.joined(separator: " · ")
    }
}
struct Inspection: Codable, Identifiable, Sendable {
    let id: String
    let title: String
    let creator: String?
    let duration: Double?
    let thumbnail: String?
    let source: String?
    let description: String?
    let formats: [MediaFormat]
}
struct Selection: Codable, Equatable, Sendable {
    var preset = "compatible"
    var formatId: String?
    var audioId: String?
    var audioFormat = "original"
    var bitrate = 192
    var subtitles = false
    var embedMetadata = true
}
struct JobProgress: Codable, Sendable {
    var stage: String?
    var downloadedBytes: Double?
    var totalBytes: Double?
    var totalEstimated: Bool?
    var speed: Double?
    var eta: Double?
    var fraction: Double? {
        guard let downloadedBytes, let totalBytes, totalBytes > 0 else { return nil }
        return min(1, max(0, downloadedBytes / totalBytes))
    }
}
struct DownloadJob: Codable, Identifiable, Sendable {
    let id: String
    let title: String
    let state: String
    let created: Double
    let updated: Double
    let version: Int
    let progress: JobProgress
    let error: String?
    let size: Int64?
    let sha256: String?
    var active: Bool { ["queued", "downloading", "postprocessing", "pausing"].contains(state) }
}
struct TransferTicket: Codable, Sendable {
    let id: String
    let token: String
    let path: String
    let expires: Double
    let size: Int64
    let sha256: String
    let filename: String
}
struct SessionToken: Codable, Sendable {
    let token: String
    let deviceId: String
    let expires: Double
    let admin: Bool
}
struct ServerProfile: Codable, Identifiable, Hashable, Sendable {
    var id = UUID().uuidString
    var name: String
    var url: URL
}
struct LocalMedia: Codable, Identifiable, Sendable {
    var id: String
    var filename: String
    var title: String
    var size: Int64
    var sha256: String
    var downloaded = Date()
    var serverId: String
}
struct ReleaseEntry: Codable, Sendable {
    let version: String
    let date: String
    let highlights: [String]
    let fixes: [String]
}
struct UpdateHighlight: Codable, Sendable { let icon: String; let text: String }
struct UpdateCandidate: Codable, Sendable {
    let version: String
    let build: Int
    let channel: String
    let releaseUrl: String
    let highlights: [UpdateHighlight]?
    let fixes: [String]?
    let minimumIos: String?
}
struct UpdateStatus: Codable, Sendable {
    let status: String
    let checkedAt: Double
    let candidate: UpdateCandidate?
}

struct ServerStatus: Codable, Sendable {
    struct Storage: Codable, Sendable { let free: Int64; let total: Int64 }
    let workerOnline: Bool
    let storage: Storage
}
