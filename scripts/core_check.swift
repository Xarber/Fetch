// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
@main struct CoreCheck {
    static func main() throws {
        precondition(JobProgress(downloadedBytes: 12).fraction == nil)
        precondition(JobProgress(downloadedBytes: 120, totalBytes: 100).fraction == 1)
        var first = DeveloperIdea(); first.title = "Original"
        var conflict = first; conflict.title = "Incoming"
        let archive = try IdeasArchive(ideas: [conflict]).validated()
        precondition(archive.merging(into: [first]).count == 2)
        precondition(IdeasArchive(ideas: [first]).merging(into: [first]).count == 1)
        do { _ = try IdeasArchive(schemaVersion: 99, ideas: []).validated(); preconditionFailure("Unknown schema accepted") } catch {}
        let data = Data(#"{"id":"x","title":"Media","state":"ready","created":1,"updated":2,"version":3,"progress":{"stage":"ready"},"size":120,"sha256":"abc"}"#.utf8)
        let job = try JSONDecoder().decode(DownloadJob.self, from: data)
        precondition(job.size == 120 && !job.active)
        print("Core behavioral checks passed (progress, imports, conflicts, schema and API decoding)")
    }
}
