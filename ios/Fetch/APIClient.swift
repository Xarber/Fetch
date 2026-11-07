// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
import Security

struct FetchAPI {
    let profile: ServerProfile
    let token: String
    static var decoder: JSONDecoder {
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase; return decoder
    }
    static var encoder: JSONEncoder {
        let encoder = JSONEncoder(); encoder.keyEncodingStrategy = .convertToSnakeCase; return encoder
    }
    func request<T: Decodable>(_ path: String, method: String = "GET", body: Data? = nil) async throws -> T {
        guard let url = URL(string:path,relativeTo:profile.url.appendingPathComponent("api/v1",isDirectory:true)) else { throw URLError(.badURL) }
        var request = URLRequest(url: url)
        request.httpMethod = method; request.httpBody = body; request.timeoutInterval = 70
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !token.isEmpty { request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization") }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
        guard (200..<300).contains(response.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
            throw APIError.message(detail ?? "Server returned HTTP \(response.statusCode)")
        }
        if data.isEmpty, let empty = EmptyResponse() as? T { return empty }
        return try Self.decoder.decode(T.self, from: data)
    }
    func send<T: Decodable>(_ path: String, method: String = "POST", object: [String: Any]) async throws -> T {
        try await request(path, method: method, body: JSONSerialization.data(withJSONObject: object))
    }
    static func validatedURL(_ string: String) throws -> URL {
        guard let url = URL(string: string), let host = url.host, url.user == nil, url.password == nil,
              url.query == nil, url.fragment == nil,
              url.scheme == "https" || (url.scheme == "http" && ["localhost", "127.0.0.1", "::1"].contains(host))
        else { throw APIError.message("Use HTTPS for your server. HTTP is allowed only on this device’s loopback for development.") }
        return url
    }
}
struct EmptyResponse: Codable {}
enum APIError: LocalizedError {
    case message(String)
    var errorDescription: String? { if case let .message(message) = self { message } else { nil } }
}
enum Keychain {
    static func save(_ value: String, for id: String) throws {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "org.openrecode.fetch", kSecAttrAccount as String: id]
        SecItemDelete(query as CFDictionary)
        var insert = query
        insert[kSecValueData as String] = Data(value.utf8)
        insert[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        guard SecItemAdd(insert as CFDictionary, nil) == errSecSuccess else { throw APIError.message("Could not save credentials securely") }
    }
    static func read(_ id: String) -> String {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "org.openrecode.fetch", kSecAttrAccount as String: id, kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess, let data = result as? Data else { return "" }
        return String(decoding: data, as: UTF8.self)
    }
    static func remove(_ id: String) {
        SecItemDelete([kSecClass as String: kSecClassGenericPassword,kSecAttrService as String:"org.openrecode.fetch",kSecAttrAccount as String:id] as CFDictionary)
    }
}
