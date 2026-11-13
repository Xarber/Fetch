// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
import Testing
@testable import FetchCore

@Test func unknownProgressStaysUnknown() {
    #expect(JobProgress(downloadedBytes: 12).fraction == nil)
    #expect(JobProgress(downloadedBytes: 120, totalBytes: 100).fraction == 1)
}
@Test func importsPreserveConflicts() throws {
    var first = DeveloperIdea(); first.title = "Original"
    var conflict = first; conflict.title = "Incoming"
    let archive = try IdeasArchive(ideas: [conflict]).validated()
    #expect(archive.merging(into: [first]).count == 2)
    #expect(IdeasArchive(ideas: [first]).merging(into: [first]).count == 1)
}
@Test func rejectsUnknownSchema() {
    #expect(throws: (any Error).self) { try IdeasArchive(schemaVersion: 99, ideas: []).validated() }
}
@Test func decodesRealAPIShape() throws {
    let data = Data(#"{"id":"x","title":"Media","state":"ready","created":1,"updated":2,"version":3,"progress":{"stage":"ready"},"size":120,"sha256":"abc"}"#.utf8)
    let job = try JSONDecoder().decode(DownloadJob.self, from: data)
    #expect(job.size == 120)
    #expect(!job.active)
}
