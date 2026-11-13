// SPDX-License-Identifier: AGPL-3.0-only
import SwiftUI
import UniformTypeIdentifiers
import UserNotifications

struct SettingsView: View {
    @Environment(AppStore.self) private var store
    @AppStorage("wifiOnly") private var wifiOnly = false
    var body: some View {
        @Bindable var store=store
        Form {
            if AppStore.managedServer != nil {
                Section("Fetch") {
                    if !store.connected {
                        NavigationLink { ServerSetupView() } label: { Label("Sign in", systemImage: "person.crop.circle") }
                    }
                }
            } else {
            Section("Your servers") {
                ForEach(store.profiles) { profile in
                    Button {
                        store.selectedId=profile.id; store.jobs=AppStore.load("jobs-\(profile.id).json",default:[])
                        UserDefaults.standard.set(profile.id,forKey:"server"); Task { await store.refresh() }
                    } label: { HStack { Label(profile.name,systemImage:"server.rack"); Spacer(); if profile.id==store.selectedId { Image(systemName:"checkmark") } } }
                }
                NavigationLink { ServerSetupView() } label: { Label("Connect a server",systemImage:"plus.circle") }
                NavigationLink { DiagnosticsView() } label: { Label("Connection diagnostics",systemImage:"waveform.path.ecg") }
            }
            }
            Section("Transfers") {
                Toggle("Transfer on Wi-Fi only",isOn:$wifiOnly)
                Text("Applies to newly started transfers. iOS schedules background networking.").font(.caption).foregroundStyle(.secondary)
                Button("Enable completion notifications") { Task { _ = try? await UNUserNotificationCenter.current().requestAuthorization(options:[.alert,.sound]) } }
            }
            Section("Privacy & security") {
                DisclosureGroup("What leaves your device?") { Text("Submitted URLs go to your configured server. The source website sees requests from that server. No advertising, tracking or analytics are included. Credentials are kept in Keychain. Server copies expire according to server retention settings; exporting a file does not delete them.") }
                if let api=store.api {
                    Button("Revoke this session",role:.destructive) {
                        Task {
                            do {
                                let _:EmptyResponse=try await api.request("auth/logout",method:"POST")
                                Keychain.remove(api.profile.id); store.connected=false
                            } catch { store.error=error.localizedDescription }
                        }
                    }
                }
            }
            Section("About") {
                NavigationLink { ChangelogView() } label: { Label("What’s New",systemImage:"sparkles") }
                NavigationLink { UpdatesView() } label: { Label("Updates",systemImage:"arrow.triangle.2.circlepath") }
                LabeledContent("License",value:"AGPL-3.0-only")
                if AppStore.managedServer == nil {
                    Button("Version \(AppStore.version)") { store.versionTapped() }
                    Text("Build \(AppStore.commit)").font(.caption.monospaced()).textSelection(.enabled)
                } else {
                    LabeledContent("Version", value: AppStore.version)
                }
            }
            if store.developer {
                Section("Developer options") {
                    NavigationLink { DiagnosticsView() } label: { Label("Diagnostics",systemImage:"stethoscope") }
                    NavigationLink { DeveloperAccess { IdeasView() } } label: { Label("Ideas",systemImage:"lightbulb") }
                    NavigationLink { DeveloperAccess { ServerAdminView() } } label: { Label("Server management",systemImage:"slider.horizontal.3") }
                    Text("Access closes after 30 seconds without interaction or when switching tabs.").font(.caption)
                }
            }
        }.navigationTitle("Settings")
    }
}
struct ServerSetupView: View {
    var pairingLink: String? = nil
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var name="My server"
    @State private var address=""
    @State private var password=""
    @State private var challenge=""
    @State private var pairing=false
    @State private var scanning=false
    @State private var busy=false
    var body: some View {
        Form {
            Section(AppStore.managedServer == nil ? "Self-hosted server" : "Fetch") {
                if AppStore.managedServer == nil {
                TextField("Name",text:$name)
                TextField("https://fetch.example.com",text:$address).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                }
                Button { scanning=true } label: { Label("Scan pairing QR code",systemImage:"qrcode.viewfinder") }
                Toggle("Use a pairing challenge",isOn:$pairing)
                if pairing { TextField("One-use challenge from administrator",text:$challenge).textInputAutocapitalization(.never).autocorrectionDisabled() }
                else { SecureField("Administrator password",text:$password) }
            }
            Section {
                Button(AppStore.managedServer == nil ? "Connect securely" : "Sign in", systemImage: "person.crop.circle") {
                    busy=true
                    Task {
                        defer { busy=false }
                        do {
                            let url = try AppStore.managedServer ?? FetchAPI.validatedURL(address.trimmingCharacters(in: .whitespacesAndNewlines))
                            let profile = AppStore.managedServer.flatMap { endpoint in
                                store.profiles.first { $0.url == endpoint }
                            } ?? ServerProfile(name: AppStore.managedServer == nil ? (name.isEmpty ? "Fetch server" : name) : "Fetch", url: url)
                            let api=FetchAPI(profile:profile,token:"")
                            let session:SessionToken = try await api.send(pairing ? "pairing/complete" : "auth/login",object:pairing ? ["challenge":challenge,"device_name":UIDevice.current.name] : ["username":"admin","password":password,"device_name":UIDevice.current.name])
                            try Keychain.save(session.token,for:profile.id)
                            if !store.profiles.contains(where: { $0.id == profile.id }) { store.profiles.append(profile) }
                            store.selectedId = profile.id
                            try AppStore.save(store.profiles,name:"servers.json"); UserDefaults.standard.set(profile.id,forKey:"server")
                            password=""; challenge=""; store.pairingURL=nil; await store.refresh(); dismiss()
                        } catch { store.error=error.localizedDescription }
                    }
                }.disabled(busy || (AppStore.managedServer == nil && address.isEmpty))
                if busy { ProgressView("Connecting…") }
                Text("Use a trusted HTTPS endpoint. Pairing challenges expire after three minutes and grant access to the personal media library without server administration.").font(.footnote).foregroundStyle(.secondary)
            }
        }.navigationTitle("Connect a server")
            .onAppear { if let pairingLink { receivePairing(pairingLink) } }
            .sheet(isPresented:$scanning) { PairingScanner { value in scanning=false; receivePairing(value) } }
    }
    private func receivePairing(_ value:String) {
        guard let components=URLComponents(string:value), components.scheme=="fetch", components.host=="pair",
              let server=components.queryItems?.first(where:{$0.name=="server"})?.value,
              let code=components.queryItems?.first(where:{$0.name=="challenge"})?.value,
              (try? FetchAPI.validatedURL(server)) != nil else { store.error="This is not a valid Fetch pairing code."; return }
        if let endpoint = AppStore.managedServer, (try? FetchAPI.validatedURL(server)) != endpoint {
            store.error = "This pairing code belongs to a different server."
            return
        }
        address=server; challenge=code; pairing=true
    }
}
struct DiagnosticsView: View {
    @Environment(AppStore.self) private var store
    @State private var text="Checking…"
    var body: some View {
        ScrollView { Text(text).font(.footnote.monospaced()).textSelection(.enabled).frame(maxWidth:.infinity,alignment:.leading).padding() }
            .navigationTitle("Diagnostics")
            .toolbar { ShareLink(item:text) { Label("Export",systemImage:"square.and.arrow.up") } }
            .task {
                guard let api=store.api else { text="No server configured."; return }
                do {
                    struct Value:Decodable { let server:String; let python:String; let ytDlp:String; let ffmpeg:String; let ffprobe:String; let commit:String }
                    let versions:Value=try await api.request("versions")
                    text="Fetch \(AppStore.version)\nClient commit: \(AppStore.commit)\nAPI: 1\nServer: \(versions.server)\nServer commit: \(versions.commit)\nPython: \(versions.python)\nyt-dlp: \(versions.ytDlp)\n\(versions.ffmpeg)\n\(versions.ffprobe)\nCached jobs: \(store.jobs.count)\nCredentials and source URLs are omitted."
                } catch { text=error.localizedDescription }
            }
    }
}
struct ServerAdminView: View {
    @Environment(AppStore.self) private var store
    @State private var concurrency=2
    @State private var retention=168
    @State private var challenge=""
    var body: some View {
        Form {
            Section("Worker limits") {
                Stepper("Concurrent jobs: \(concurrency)",value:$concurrency,in:1...4)
                Stepper("Retention: \(retention) hours",value:$retention,in:1...8760)
                Button("Save server settings") {
                    Task {
                        guard let api=store.api else { return }
                        do { let _:ServerSettings=try await api.send("admin/settings",method:"PATCH",object:["concurrency":concurrency,"retention_hours":retention]) }
                        catch { store.error=error.localizedDescription }
                    }
                }
            }
            Section("Pair another device") {
                Button("Create one-use pairing challenge") {
                    Task {
                        guard let api=store.api else { return }
                        do { let result:Challenge=try await api.request("pairing/start",method:"POST"); challenge=result.challenge }
                        catch { store.error=error.localizedDescription }
                    }
                }
                if !challenge.isEmpty { Text(challenge).textSelection(.enabled); Text("Expires in three minutes. Share only with a trusted device.").font(.caption) }
            }
        }.navigationTitle("Server management").task {
            if let api=store.api,let settings:ServerSettings=try? await api.request("admin/settings") { concurrency=settings.concurrency; retention=settings.retentionHours }
        }
    }
    struct ServerSettings:Codable { let concurrency:Int; let retentionHours:Int }
    struct Challenge:Decodable { let challenge:String }
}
struct IdeasView:View {
    @Environment(AppStore.self) private var store
    @State private var search=""
    @State private var editing:DeveloperIdea?
    @State private var importing=false
    @State private var incoming:IdeasArchive?
    @State private var exporting=false
    @State private var document=JSONDocument()
    var body:some View {
        List {
            ForEach(store.ideas.filter { search.isEmpty || $0.title.localizedCaseInsensitiveContains(search) }.sorted { $0.modified > $1.modified }) { idea in
                Button { editing=idea } label: {
                    VStack(alignment:.leading) { Label(idea.title,systemImage:idea.category == "Bug Fix" ? "ladybug" : "lightbulb"); Text(idea.status.rawValue).font(.caption).foregroundStyle(.secondary) }
                }.swipeActions { Button("Delete",role:.destructive) { store.ideas.removeAll { $0.id==idea.id }; store.recordIdeas() }; Button("Duplicate") { var copy=idea; copy.id=UUID().uuidString; copy.title += " (copy)"; store.ideas.append(copy); store.recordIdeas() } }
            }
            if store.ideas.isEmpty { ContentUnavailableView("Keep your next idea",systemImage:"lightbulb",description:Text("Ideas are saved on this device, even offline.")) }
        }.navigationTitle("Ideas").searchable(text:$search)
            .toolbar {
                ToolbarItem(placement:.primaryAction) { Button { editing=DeveloperIdea() } label: { Label("New idea",systemImage:"plus") } }
                ToolbarItem(placement:.secondaryAction) { Button("Import JSON") { importing=true } }
                ToolbarItem(placement:.secondaryAction) { Button("Export JSON") { document=JSONDocument(data:(try? JSONEncoder().encode(IdeasArchive(ideas:store.ideas))) ?? Data()); exporting=true } }
            }
            .sheet(item:$editing) { idea in IdeaEditor(idea:idea) }
            .fileImporter(isPresented:$importing,allowedContentTypes:[.json]) { result in
                do {
                    let url=try result.get(); let access=url.startAccessingSecurityScopedResource(); defer { if access { url.stopAccessingSecurityScopedResource() } }
                    let data=try Data(contentsOf:url); guard data.count <= 10_000_000 else { throw CocoaError(.fileReadTooLarge) }
                    incoming=try JSONDecoder().decode(IdeasArchive.self,from:data).validated()
                } catch { store.error=error.localizedDescription }
            }
            .confirmationDialog("Review import: \(incoming?.ideas.count ?? 0) ideas. Existing entries are preserved; conflicts become separate copies.",isPresented:Binding(get:{incoming != nil},set:{if !$0 {incoming=nil}}),titleVisibility:.visible) {
                Button("Merge ideas") { if let incoming { store.ideas=incoming.merging(into:store.ideas); store.recordIdeas() }; incoming=nil }
            }
            .fileExporter(isPresented:$exporting,document:document,contentType:.json,defaultFilename:"Fetch-Ideas") { result in if case .failure(let error)=result { store.error=error.localizedDescription } }
    }
}
struct IdeaEditor:View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State var idea:DeveloperIdea
    var body:some View {
        NavigationStack {
            Form {
                TextField("Title",text:$idea.title)
                TextEditor(text:$idea.description).frame(minHeight:160).accessibilityLabel("Idea description and reproduction steps")
                Picker("Category",selection:$idea.category) { ForEach(["Feature","Improvement","Bug Fix","UI/UX","Performance","Other"],id:\.self) { Text($0) } }
                Picker("Priority",selection:$idea.priority) { ForEach(["Low","Normal","High","Critical"],id:\.self) { Text($0) } }
                Picker("Status",selection:$idea.status) { ForEach(IdeaStatus.allCases,id:\.self) { Text($0.rawValue).tag($0) } }
                DisclosureGroup("Implementation history") { ForEach(idea.history,id:\.self) { Text($0).font(.caption) }; ForEach(idea.implementationReferences,id:\.self) { Text($0).font(.caption) } }
            }.navigationTitle("Idea").onChange(of:idea) { _,_ in store.lastInteraction=Date() }.toolbar {
                ToolbarItem(placement:.cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement:.confirmationAction) { Button("Save") {
                    idea.modified=Date().timeIntervalSince1970; idea.history.append("\(Date().formatted(.iso8601)): \(idea.status.rawValue)")
                    if let index=store.ideas.firstIndex(where:{$0.id==idea.id}) { store.ideas[index]=idea } else { store.ideas.append(idea) }
                    store.recordIdeas(); dismiss()
                }.disabled(idea.title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty) }
            }
        }
    }
}
struct JSONDocument:FileDocument {
    static var readableContentTypes:[UTType] { [.json] }
    var data=Data()
    init(data:Data=Data()) { self.data=data }
    init(configuration:ReadConfiguration) throws { data=configuration.file.regularFileContents ?? Data() }
    func fileWrapper(configuration:WriteConfiguration) throws -> FileWrapper { FileWrapper(regularFileWithContents:data) }
}
struct ChangelogView:View {
    var body:some View {
        List {
            if let release=ReleaseCatalog.current {
                Section("\(release.version) · \(release.date) · \(release.status.capitalized)") {
                    ForEach(release.highlights,id:\.text) { Label($0.text,systemImage:$0.icon) }
                    DisclosureGroup("Fixes & Improvements") { ForEach(release.fixes,id:\.self) { Text($0) } }
                }
            } else { ContentUnavailableView("Release details unavailable",systemImage:"doc.text") }
            Section("Build information") { LabeledContent("Version",value:AppStore.version);Text(AppStore.commit).font(.caption.monospaced()).textSelection(.enabled) }
        }.navigationTitle("What’s New")
    }
}
struct UpdatesView:View {
    @Environment(AppStore.self) private var store
    @AppStorage("automaticUpdates") private var automatic=true
    var body:some View {
        Form {
            Section {
                LabeledContent("Installed",value:AppStore.version)
                LabeledContent("Channel",value:UpdateStore.channel.capitalized)
                Toggle("Check automatically",isOn:$automatic)
                if let date=store.updates.lastSuccessfulCheck { LabeledContent("Last successful check",value:date.formatted()) }
                Text(store.updates.message).font(.subheadline)
                if !store.connected { Label("Cached information · server disconnected",systemImage:"wifi.slash").font(.caption) }
                Button("Check for Updates") { Task { if let api=store.api { await store.updates.check(using:api,force:true) } } }.disabled(store.updates.checking || store.api == nil)
                if store.updates.checking { ProgressView("Checking…") }
            }
            if let candidate=store.updates.result?.candidate {
                Section("Version \(candidate.version) · Build \(candidate.build)") {
                    ForEach(candidate.highlights ?? [],id:\.text) { Label($0.text,systemImage:$0.icon) }
                    DisclosureGroup("Fixes & Improvements") { ForEach(candidate.fixes ?? [],id:\.self) { Text($0) } }
                    if let url=URL(string:candidate.releaseUrl),url.scheme=="https",url.host=="github.com" { Link("View release and signing instructions",destination:url) }
                    Text("Native updates follow your signing or store channel. An unsigned IPA requires an external signing/install workflow.").font(.footnote)
                }
            }
            NavigationLink { ChangelogView() } label: { Label("Full changelog",systemImage:"clock.arrow.circlepath") }
        }.navigationTitle("Updates")
    }
}
struct DeveloperAccess<Content: View>: View {
    @Environment(AppStore.self) private var store
    let content: () -> Content
    init(@ViewBuilder content: @escaping () -> Content) { self.content=content }
    var body: some View {
        if store.developer { content() }
        else { ContentUnavailableView("Developer access expired", systemImage: "lock", description: Text("Return to Settings and tap the version three times to reopen developer options.")) }
    }
}
