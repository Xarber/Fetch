// SPDX-License-Identifier: AGPL-3.0-only
import SwiftUI
import VisionKit

struct PairingScanner: View {
    @Environment(\.dismiss) private var dismiss
    let received: (String) -> Void
    @State private var failure: String?
    var body: some View {
        NavigationStack {
            Group {
                if let failure { ContentUnavailableView("Camera unavailable", systemImage:"camera", description:Text(failure)) }
                else if DataScannerViewController.isSupported && DataScannerViewController.isAvailable {
                    ScannerController(received:received,failed:{failure=$0})
                } else { ContentUnavailableView("Use manual pairing",systemImage:"qrcode",description:Text("QR scanning is unavailable on this device. Enter the challenge shown by your server administrator.")) }
            }.navigationTitle("Scan pairing code").toolbar { ToolbarItem(placement:.cancellationAction) { Button("Cancel") { dismiss() } } }
        }
    }
}
private struct ScannerController: UIViewControllerRepresentable {
    let received:(String)->Void
    let failed:(String)->Void
    func makeCoordinator()->Coordinator { Coordinator(received:received) }
    func makeUIViewController(context:Context)->DataScannerViewController {
        let scanner=DataScannerViewController(recognizedDataTypes:[.barcode(symbologies:[.qr])],qualityLevel:.balanced,recognizesMultipleItems:false,isGuidanceEnabled:true,isHighlightingEnabled:true)
        scanner.delegate=context.coordinator
        do { try scanner.startScanning() } catch { Task { @MainActor in failed(error.localizedDescription) } }
        return scanner
    }
    func updateUIViewController(_ scanner:DataScannerViewController,context:Context) {}
    static func dismantleUIViewController(_ scanner:DataScannerViewController,coordinator:Coordinator) { scanner.stopScanning() }
    @MainActor final class Coordinator:NSObject,DataScannerViewControllerDelegate {
        let received:(String)->Void
        var consumed=false
        init(received:@escaping(String)->Void) { self.received=received }
        func dataScanner(_ scanner:DataScannerViewController,didAdd items:[RecognizedItem],allItems:[RecognizedItem]) {
            for item in items {
                if case let .barcode(barcode)=item,let payload=barcode.payloadStringValue,!consumed {
                    consumed=true;scanner.stopScanning();received(payload);return
                }
            }
        }
    }
}
