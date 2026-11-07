// SPDX-License-Identifier: AGPL-3.0-only
import SwiftUI
import AVKit
import QuickLook
import UniformTypeIdentifiers
import Photos

struct RootView: View {
    @Environment(AppStore.self) private var store
    var body: some View {
        @Bindable var store = store
        TabView(selection: $store.selectedTab) {
            NavigationStack { HomeView() }.tabItem { Label("Fetch", systemImage: "arrow.down.circle.fill") }.tag(0)
            NavigationStack { QueueView() }.tabItem { Label("Queue", systemImage: "tray.full") }.tag(1)
            NavigationStack { LibraryView() }.tabItem { Label("Files", systemImage: "folder") }.tag(2)
            NavigationStack { SettingsView() }.tabItem { Label("Settings", systemImage: "gearshape") }.tag(3)
        }
        .simultaneousGesture(TapGesture().onEnded { store.lastInteraction = Date() })
        .alert("Fetch", isPresented: Binding(get: { store.error != nil }, set: { if !$0 { store.error = nil } })) { Button("OK") { store.error = nil } } message: { Text(store.error ?? "") }
        .sheet(isPresented: $store.welcome) {
            VStack(spacing: 24) {
                Image(systemName: "arrow.down.circle.fill").font(.system(size: 72)).foregroundStyle(.tint).accessibilityHidden(true)
                Text("Your media.\nYour device.\nYour control.").font(.largeTitle.bold()).multilineTextAlignment(.center)
                Text("Save media you’re authorized to keep, using your own download server.").foregroundStyle(.secondary).multilineTextAlignment(.center)
                Button("Set up Fetch") { UserDefaults.standard.set(true, forKey: "welcomed"); store.welcome = false; store.selectedTab = 3 }.buttonStyle(.borderedProminent)
            }.padding(32).presentationDetents([.large])
        }
        .sheet(isPresented: Binding(get: { store.pairingURL != nil }, set: { if !$0 { store.pairingURL = nil } })) {
            NavigationStack { ServerSetupView(pairingLink: store.pairingURL) }
        }
        .sheet(isPresented: Binding(get: { store.updates.prompt && !store.welcome && store.inspection == nil && store.pairingURL == nil }, set: { store.updates.prompt = $0 })) {
            NavigationStack { UpdatesView().toolbar { ToolbarItem(placement:.cancellationAction) { Button("Later") { store.updates.prompt=false } } } }.presentationDetents([.medium,.large])
        }
        .sheet(isPresented: $store.whatsNew) { NavigationStack { ChangelogView() } }
    }
}
struct HomeView: View {
    @Environment(AppStore.self) private var store
    @State private var inspectionTask: Task<Void, Never>?
    var body: some View {
        @Bindable var store = store
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                HStack {
                    Label(store.connected ? "Server connected" : "Server disconnected", systemImage: store.connected ? "checkmark.circle" : "wifi.slash")
                        .font(.subheadline).foregroundStyle(.secondary)
                    Spacer()
                    if store.busy { ProgressView() }
                }
                if store.connected,let health=store.serverStatus {
                    HStack {
                        Label(health.workerOnline ? "Worker online" : "Worker offline · jobs will wait",systemImage:health.workerOnline ? "gearshape.2" : "exclamationmark.triangle")
                        Spacer()
                        Text(ByteCountFormatter.string(fromByteCount:health.storage.free,countStyle:.file)+" free on server")
                    }.font(.caption).foregroundStyle(.secondary)
                }
                Text("Something worth\nkeeping.").font(.largeTitle.bold())
                VStack(alignment: .leading, spacing: 16) {
                    Label("New download", systemImage: "link").font(.headline)
                    TextField("Paste an authorized media URL", text: $store.urlInput, axis: .vertical)
                        .textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL).accessibilityLabel("Media URL")
                    HStack {
                        Button { if let text = UIPasteboard.general.string { store.urlInput = text } } label: { Label("Paste", systemImage: "doc.on.clipboard") }
                        Spacer()
                        if store.busy {
                            Button("Cancel") { inspectionTask?.cancel(); store.busy = false }
                        } else {
                            Button { inspectionTask = Task { await store.inspect() } } label: { Label("Inspect", systemImage: "arrow.right") }
                                .buttonStyle(.borderedProminent).disabled(store.urlInput.isEmpty)
                        }
                    }
                }.padding(20).background(.regularMaterial, in: RoundedRectangle(cornerRadius: 24))
                if !store.connected { Label("Local files stay available while your server is offline.", systemImage: "folder").foregroundStyle(.secondary) }
                NavigationLink { BatchView() } label: { Label("Import multiple links", systemImage: "list.bullet.rectangle") }
                Text("Recent activity").font(.title2.bold())
                if store.jobs.isEmpty { ContentUnavailableView("A clean slate", systemImage: "tray", description: Text("Your downloads will appear here.")) }
                ForEach(store.jobs.prefix(4)) { job in NavigationLink { JobDetailView(jobId: job.id) } label: { JobRow(job: job) }.buttonStyle(.plain) }
            }.padding(20)
        }
        .navigationTitle("Fetch").navigationBarTitleDisplayMode(.inline)
        .sheet(item: $store.inspection) { inspection in NavigationStack { MediaView(inspection: inspection) } }
        .onDisappear { inspectionTask?.cancel() }
    }
}
struct MediaView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let inspection: Inspection
    @State private var selection = Selection()
    @State private var authorized = false
    @State private var submitting = false
    @State private var requestKey = UUID().uuidString
    var body: some View {
        Form {
            Section {
                Text(inspection.title).font(.title2.bold())
                if let creator = inspection.creator { Label(creator, systemImage: "person") }
                if let duration = inspection.duration { Label(Duration.seconds(duration).formatted(.time(pattern: .hourMinuteSecond)), systemImage: "clock") }
                if let source = inspection.source { Label(source, systemImage: "globe") }
                if let description = inspection.description, !description.isEmpty { DisclosureGroup("Description") { Text(description).font(.subheadline) } }
            }
            Section("Output") {
                Picker("Preset", selection: $selection.preset) {
                    Text("Best compatibility").tag("compatible"); Text("Best quality").tag("best"); Text("Smaller file").tag("small")
                    Text("Audio only").tag("audio"); Text("Original streams").tag("original"); Text("Custom").tag("custom")
                }
                if selection.preset == "custom" {
                    Picker("Format", selection: $selection.formatId) {
                        Text("Choose a format").tag(String?.none)
                        ForEach(inspection.formats) { Text($0.label).tag(Optional($0.id)) }
                    }
                    Picker("Separate audio", selection: $selection.audioId) {
                        Text("None").tag(String?.none)
                        ForEach(inspection.formats.filter { $0.vcodec == "none" }) { Text($0.label).tag(Optional($0.id)) }
                    }
                }
                if selection.preset == "audio" {
                    Picker("Audio output", selection: $selection.audioFormat) {
                        ForEach(["original", "m4a", "mp3", "opus", "flac", "wav"], id: \.self) { Text($0.uppercased()).tag($0) }
                    }
                    if selection.audioFormat == "mp3" { Picker("Bitrate", selection: $selection.bitrate) { ForEach([128,192,256,320], id: \.self) { Text("\($0) kbps").tag($0) } } }
                }
                Toggle("Embed metadata", isOn: $selection.embedMetadata)
                Toggle("English subtitles, when available", isOn: $selection.subtitles)
                DisclosureGroup("About quality and compatibility") {
                    Text("Original streams preserve source quality. Remuxing changes the container without re-encoding. Conversion may take longer. FLAC or WAV cannot restore quality lost in a lossy source. MP4 alone does not guarantee device-compatible codecs.")
                }
                DisclosureGroup("All source formats") { ForEach(inspection.formats) { Text($0.label).font(.caption.monospaced()) } }
            }
            Section {
                Toggle("I’m authorized to save this media", isOn: $authorized)
                Button {
                    submitting = true
                    Task { await store.create(inspection, selection: selection, requestKey: requestKey); submitting = false }
                } label: { HStack { Spacer(); if submitting { ProgressView() }; Label("Fetch media", systemImage: "arrow.down.circle.fill"); Spacer() } }
                    .disabled(!authorized || submitting || (selection.preset == "custom" && selection.formatId == nil))
            }
        }.navigationTitle("Choose your media").toolbar { ToolbarItem(placement: .cancellationAction) { Button("Close") { dismiss() } } }
    }
}
struct JobRow: View {
    let job: DownloadJob
    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: job.state == "ready" ? "checkmark.circle.fill" : job.state == "failed" ? "exclamationmark.circle" : "arrow.down.circle")
                .font(.title2).foregroundStyle(.tint).accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 5) {
                Text(job.title).font(.headline).lineLimit(2)
                Text(job.state.replacingOccurrences(of: "_", with: " ").capitalized).font(.caption).foregroundStyle(.secondary)
                if job.state == "downloading", let fraction = job.progress.fraction { ProgressView(value: fraction).accessibilityLabel("Server download") }
                if job.state == "postprocessing" { Text(job.progress.stage ?? "Processing").font(.caption) }
                if job.progress.totalEstimated == true { Text("Estimated source size").font(.caption).foregroundStyle(.secondary) }
            }
            Spacer()
        }.padding(.vertical, 8)
    }
}
struct QueueView: View {
    @Environment(AppStore.self) private var store
    @State private var history = false
    var body: some View {
        List {
            if !store.connected { Label("Cached server status · reconnect to refresh", systemImage: "wifi.slash").font(.caption).foregroundStyle(.secondary) }
            Picker("Show", selection: $history) { Text("Active").tag(false); Text("History").tag(true) }.pickerStyle(.segmented)
            ForEach(store.jobs.filter { history ? !$0.active : $0.active || $0.state == "paused" }) { job in
                NavigationLink { JobDetailView(jobId: job.id) } label: { JobRow(job: job) }
            }
            if store.jobs.isEmpty { ContentUnavailableView("No downloads yet", systemImage: "tray") }
            Section("Transfers to this device") {
                ForEach(TransferManager.shared.records) { record in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(record.title).font(.headline)
                        Text(record.state.capitalized).font(.caption)
                        if record.state == "transferring" {
                            ProgressView(value: Double(record.received), total: Double(max(1,record.expectedSize)))
                            Button("Cancel transfer", role: .destructive) { TransferManager.shared.cancel(record) }
                        }
                        if let error = record.error { Text(error).font(.caption).foregroundStyle(.secondary) }
                    }
                }
            }
        }.navigationTitle("Downloads").refreshable { await store.refresh() }
    }
}
struct JobDetailView: View {
    @Environment(AppStore.self) private var store
    let jobId: String
    @State private var deleting = false
    var body: some View {
        Group {
            if let job = store.jobs.first(where: { $0.id == jobId }) {
                Form {
                    Section { JobRow(job: job) }
                    Section("Server processing") {
                        if let bytes = job.progress.downloadedBytes { LabeledContent("Downloaded", value: ByteCountFormatter.string(fromByteCount: Int64(bytes), countStyle: .file)) }
                        if let speed = job.progress.speed { LabeledContent("Speed", value: ByteCountFormatter.string(fromByteCount: Int64(speed), countStyle: .file) + "/s") }
                        if let eta = job.progress.eta { LabeledContent("Estimated remaining", value: "\(Int(eta)) seconds") }
                        if let error = job.error { Label(error, systemImage: "exclamationmark.triangle") }
                        if let size = job.size { LabeledContent("File size", value: ByteCountFormatter.string(fromByteCount: size, countStyle: .file)) }
                    }
                    Section {
                        if job.state == "ready" { Button { Task { await store.transfer(job) } } label: { Label("Save to this device", systemImage: "iphone.and.arrow.down") } }
                        if ["queued","downloading"].contains(job.state) { Button("Pause server download") { Task { await store.action("pause",job:job) } } }
                        if job.state == "paused" { Button("Resume server download") { Task { await store.action("resume",job:job) } } }
                        if ["failed","cancelled"].contains(job.state) { Button("Retry") { Task { await store.action("retry",job:job) } } }
                        if job.active || job.state == "paused" { Button("Cancel job", role: .destructive) { Task { await store.action("cancel",job:job) } } }
                        if !job.active { Button("Remove server file and history", role: .destructive) { deleting = true } }
                    }
                    DisclosureGroup("Transfer and pause behavior") { Text("Server processing and device transfer are separate. Pause stops the server process; resumption uses partial media only when the source supports it. If a device transfer expires or fails, request a fresh transfer. iOS controls background scheduling.") }
                    if let hash = job.sha256 { DisclosureGroup("SHA-256") { Text(hash).font(.caption.monospaced()).textSelection(.enabled) } }
                }.confirmationDialog("Delete the server file and this history entry?", isPresented: $deleting, titleVisibility: .visible) { Button("Delete", role:.destructive) { Task { await store.delete(job) } } }
            } else { ContentUnavailableView("Download removed", systemImage: "tray") }
        }.navigationTitle("Download details")
    }
}
struct LibraryView: View {
    @Environment(AppStore.self) private var store
    @State private var search = ""
    @State private var preview: URL?
    @State private var deleting: LocalMedia?
    @State private var editingFile: LocalMedia?
    @State private var fileEditMode="Rename"
    @State private var fileEditText=""
    @State private var infoFile: LocalMedia?
    @State private var sort="date"
    var body: some View {
        List {
            if TransferManager.shared.library.isEmpty { ContentUnavailableView("Your files live here", systemImage: "folder", description: Text("Save a completed download to this device. Files remain available offline.")) }
            ForEach(TransferManager.shared.library.filter { search.isEmpty || $0.title.localizedCaseInsensitiveContains(search) }.sorted { sort == "name" ? $0.title.localizedStandardCompare($1.title) == .orderedAscending : sort == "size" ? $0.size > $1.size : $0.downloaded > $1.downloaded }) { media in
                let url = TransferManager.files.appendingPathComponent(media.filename)
                VStack(alignment:.leading, spacing:10) {
                    Button { preview = url } label: { Label(media.title, systemImage: "play.rectangle").font(.headline) }
                    Text(ByteCountFormatter.string(fromByteCount:media.size,countStyle:.file)).font(.caption).foregroundStyle(.secondary)
                    HStack {
                        ShareLink(item: url) { Label("Export",systemImage:"square.and.arrow.up") }
                        Spacer()
                        if ["mp4","mov","m4v"].contains(url.pathExtension.lowercased()) {
                            Button("Save to Photos") {
                                Task {
                                    let status = await PHPhotoLibrary.requestAuthorization(for: .addOnly)
                                    guard status == .authorized || status == .limited else { store.error = "Allow Photos access in system Settings."; return }
                                    do { try await PHPhotoLibrary.shared().performChanges { PHAssetChangeRequest.creationRequestForAssetFromVideo(atFileURL: url) } }
                                    catch { store.error = error.localizedDescription }
                                }
                            }
                        }
                        Button("Delete",role:.destructive) { deleting = media }
                    }.font(.subheadline)
                }.padding(.vertical,6)
                    .contextMenu {
                        Button("Rename",systemImage:"pencil") { editingFile=media;fileEditMode="Rename";fileEditText=media.title }
                        Button("Move to folder",systemImage:"folder") { editingFile=media;fileEditMode="Move";fileEditText=(media.filename as NSString).deletingLastPathComponent }
                        Button("Duplicate",systemImage:"doc.on.doc") { do { try TransferManager.shared.duplicate(media) } catch { store.error=error.localizedDescription } }
                        Button("File information",systemImage:"info.circle") { infoFile=media }
                    }
            }
        }.navigationTitle("On your device").searchable(text:$search)
            .toolbar { Menu("Sort",systemImage:"arrow.up.arrow.down") { Picker("Sort files",selection:$sort) { Text("Newest first").tag("date");Text("Name").tag("name");Text("Largest first").tag("size") } } }
            .alert(fileEditMode,isPresented:Binding(get:{editingFile != nil},set:{if !$0 {editingFile=nil}})) {
                TextField(fileEditMode == "Move" ? "Folder (empty for library root)" : "File name",text:$fileEditText)
                Button("Save") {
                    if let media=editingFile { do { if fileEditMode == "Move" { try TransferManager.shared.move(media,to:fileEditText) } else { try TransferManager.shared.rename(media,to:fileEditText) } } catch { store.error=error.localizedDescription } }
                    editingFile=nil
                }
                Button("Cancel",role:.cancel) { editingFile=nil }
            }
            .sheet(item:$infoFile) { media in NavigationStack { Form { LabeledContent("Name",value:media.title);LabeledContent("Size",value:ByteCountFormatter.string(fromByteCount:media.size,countStyle:.file));LabeledContent("Downloaded",value:media.downloaded.formatted());LabeledContent("Format",value:URL(fileURLWithPath:media.filename).pathExtension.uppercased());Text(media.filename);DisclosureGroup("SHA-256") { Text(media.sha256).font(.caption.monospaced()).textSelection(.enabled) } }.navigationTitle("File information").toolbar { Button("Done") { infoFile=nil } } } }
            .quickLookPreview($preview)
            .confirmationDialog("Delete this local file?",isPresented:Binding(get:{deleting != nil},set:{if !$0 {deleting=nil}}),titleVisibility:.visible) {
                Button("Delete file",role:.destructive) { if let media=deleting { do { try TransferManager.shared.remove(media) } catch { store.error=error.localizedDescription } }; deleting=nil }
            }
    }
}
struct BatchView: View {
    @Environment(AppStore.self) private var store
    @State private var text = ""
    @State private var authorized = false
    @State private var running = false
    @State private var result = ""
    var body: some View {
        Form {
            Section("One URL per line · maximum 50") { TextEditor(text:$text).frame(minHeight:180) }
            Toggle("I’m authorized to save these items",isOn:$authorized)
            Button("Inspect and queue links") {
                running=true
                let urls=Array(Set(text.split(whereSeparator: \.isNewline).map(String.init))).prefix(50)
                Task {
                    guard let api=store.api else { running=false; return }
                    var count=0
                    for url in urls {
                        do {
                            let info:Inspection=try await api.send("media/inspect",object:["url":url])
                            let _:DownloadJob=try await api.send("downloads",object:["inspection_id":info.id,"request_key":UUID().uuidString,"authorized":true,"selection":["preset":"compatible"]])
                            count += 1
                        } catch { result="Queued \(count) items. \(error.localizedDescription)"; running=false; return }
                    }
                    result="Queued \(count) items."; running=false; await store.refresh()
                }
            }.disabled(running || !authorized || text.isEmpty)
            if running { ProgressView("Inspecting sources…") }
            Text(result)
        }.navigationTitle("Batch download")
    }
}
