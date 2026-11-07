// SPDX-License-Identifier: AGPL-3.0-only
import Foundation

enum IdeaStatus: String, Codable, CaseIterable, Sendable {
    case pending, approved, deferred, inProgress, implemented, rejected
}
struct DeveloperIdea: Codable, Identifiable, Equatable, Sendable {
    var id = UUID().uuidString
    var title = ""
    var description = ""
    var category = "Feature"
    var priority = "Normal"
    var status = IdeaStatus.pending
    var created = Date().timeIntervalSince1970
    var modified = Date().timeIntervalSince1970
    var implementationReferences: [String] = []
    var history: [String] = []
}
struct IdeasArchive: Codable, Sendable {
    var schemaVersion = 1
    var project = "org.openrecode.fetch"
    var exportedAt = Date().timeIntervalSince1970
    var ideas: [DeveloperIdea]
    func validated() throws -> IdeasArchive {
        guard schemaVersion == 1, project == "org.openrecode.fetch", ideas.count <= 10_000,
              Set(ideas.map(\.id)).count == ideas.count,
              ideas.allSatisfy({ !$0.id.isEmpty && !$0.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && $0.title.count <= 500 && $0.description.count <= 50_000 && ["Feature","Improvement","Bug Fix","UI/UX","Performance","Other"].contains($0.category) && ["Low","Normal","High","Critical"].contains($0.priority) && $0.created.isFinite && $0.modified.isFinite })
        else { throw CocoaError(.fileReadCorruptFile) }
        return self
    }
    /// Preserve both conflicting versions; identical IDs with identical contents deduplicate.
    func merging(into existing: [DeveloperIdea]) -> [DeveloperIdea] {
        var merged = existing
        for idea in ideas {
            if let old = merged.first(where: { $0.id == idea.id }) {
                if old != idea {
                    var copy = idea
                    copy.id = UUID().uuidString
                    copy.title += " (imported conflict)"
                    copy.history.append("Conflict preserved from \(idea.id)")
                    merged.append(copy)
                }
            } else { merged.append(idea) }
        }
        return merged
    }
}
