// SPDX-License-Identifier: AGPL-3.0-only
import Foundation

struct AppRelease: Decodable {
    let version: String
    let date: String
    let status: String
    let highlights: [UpdateHighlight]
    let fixes: [String]
}
enum ReleaseCatalog {
    static var current: AppRelease? {
        guard let url=Bundle.main.url(forResource:"ReleaseMetadata",withExtension:"json"),let data=try? Data(contentsOf:url) else { return nil }
        return try? JSONDecoder().decode(AppRelease.self,from:data)
    }
}
