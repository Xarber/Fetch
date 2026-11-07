// SPDX-License-Identifier: AGPL-3.0-only
import UIKit
import UniformTypeIdentifiers

@MainActor final class ShareViewController: UIViewController {
    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        Task { await receive() }
    }
    private func receive() async {
        let items=extensionContext?.inputItems.compactMap { $0 as? NSExtensionItem } ?? []
        var urls:[String]=[]
        for item in items {
            for provider in item.attachments ?? [] {
                do {
                    let type=provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) ? UTType.url.identifier : UTType.plainText.identifier
                    guard provider.hasItemConformingToTypeIdentifier(type) else { continue }
                    let text: String = try await withCheckedThrowingContinuation { continuation in
                        provider.loadItem(forTypeIdentifier:type,options:nil) { value,error in
                            if let error { continuation.resume(throwing:error) }
                            else { continuation.resume(returning:(value as? URL)?.absoluteString ?? value as? String ?? "") }
                        }
                    }
                    let detector=try NSDataDetector(types:NSTextCheckingResult.CheckingType.link.rawValue)
                    for match in detector.matches(in:text,range:NSRange(text.startIndex...,in:text)) {
                        if let url=match.url,["http","https"].contains(url.scheme?.lowercased() ?? "") { urls.append(url.absoluteString) }
                    }
                } catch { }
            }
        }
        guard let defaults=UserDefaults(suiteName:"group.org.openrecode.fetch"),!urls.isEmpty else { show("No supported HTTP or HTTPS link was shared."); return }
        var pending=defaults.stringArray(forKey:"pendingURLs") ?? []
        for url in urls where !pending.contains(url) { pending.append(url) }
        defaults.set(Array(pending.suffix(100)),forKey:"pendingURLs")
        show("Link saved. Open Fetch to choose a format and continue.")
    }
    private func show(_ message:String) {
        let alert=UIAlertController(title:"Fetch",message:message,preferredStyle:.alert)
        alert.addAction(UIAlertAction(title:"Done",style:.default) { _ in self.extensionContext?.completeRequest(returningItems:nil) })
        present(alert,animated:true)
    }
}
