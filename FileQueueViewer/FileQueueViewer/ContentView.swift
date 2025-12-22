import SwiftUI

struct ContentView: View {
    @StateObject private var queueManager = QueueManager()
    @State private var selection = Set<String>()
    @State private var selectedFile: FileEntry?
    @State private var sortOrder = [KeyPathComparator(\FileEntry.timestamp, order: .reverse)]
    @State private var filterLevel: ConfidenceFilter = .all
    @State private var showingAlert = false
    @State private var alertMessage = ""
    @State private var alertTitle = ""
    @State private var recentlyMovedFiles: [FileEntry] = []  // Files that were just moved (for display)
    @State private var fileToSkip: FileEntry?  // File pending skip (waiting for reason)
    @State private var skipReason = ""
    @State private var showingBulkSkipReason = false
    @State private var bulkSkipReason = ""

    enum ConfidenceFilter: String, CaseIterable {
        case all = "All"
        case high = "High (90+)"
        case medium = "Medium (50-89)"
        case low = "Low (<50)"

        func matches(_ confidence: Int) -> Bool {
            switch self {
            case .all: return true
            case .high: return confidence >= 90
            case .medium: return confidence >= 50 && confidence < 90
            case .low: return confidence < 50
            }
        }
    }

    private var recentlyMovedIds: Set<String> {
        Set(recentlyMovedFiles.map { $0.id })
    }

    private var filteredFiles: [FileEntry] {
        let pending = queueManager.files
            .filter { filterLevel.matches($0.confidence) }
        // Include recently moved files at their original position
        let combined = pending + recentlyMovedFiles.filter { moved in
            !pending.contains { $0.id == moved.id } && filterLevel.matches(moved.confidence)
        }
        return combined.sorted(using: sortOrder)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            HStack {
                Picker("Filter", selection: $filterLevel) {
                    ForEach(ConfidenceFilter.allCases, id: \.self) { level in
                        Text(level.rawValue).tag(level)
                    }
                }
                .pickerStyle(.segmented)
                .frame(maxWidth: 300)

                Spacer()

                Text("\(filteredFiles.count) files")
                    .foregroundColor(.secondary)

                Button {
                    queueManager.loadQueue()
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .help("Refresh queue")
            }
            .padding()
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            // Main table
            if queueManager.isLoading {
                ProgressView("Loading queue...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let error = queueManager.error {
                VStack {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.largeTitle)
                        .foregroundColor(.red)
                    Text(error)
                        .foregroundColor(.secondary)
                    Button("Retry") {
                        queueManager.loadQueue()
                    }
                    .padding(.top)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if filteredFiles.isEmpty {
                VStack {
                    Image(systemName: "tray")
                        .font(.largeTitle)
                        .foregroundColor(.secondary)
                    Text("No files in queue")
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                Table(filteredFiles, selection: $selection, sortOrder: $sortOrder) {
                    TableColumn("") { file in
                        Toggle("", isOn: Binding(
                            get: { selection.contains(file.id) },
                            set: { isSelected in
                                if isSelected {
                                    selection.insert(file.id)
                                } else {
                                    selection.remove(file.id)
                                }
                            }
                        ))
                        .toggleStyle(.checkbox)
                    }
                    .width(30)

                    TableColumn("Confidence", value: \.confidence) { file in
                        ConfidenceBadge(confidence: file.confidence)
                    }
                    .width(100)

                    TableColumn("Source", value: \.sourcePath) { file in
                        VStack(alignment: .leading) {
                            Text(file.sourceFileName)
                                .lineLimit(1)
                            Text(shortenPath((file.sourcePath as NSString).deletingLastPathComponent))
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .lineLimit(1)
                        }
                    }
                    .width(min: 200, ideal: 250)

                    TableColumn("Destination", value: \.destPath) { file in
                        if file.isDelete {
                            Label("DELETE", systemImage: "trash")
                                .foregroundColor(.red)
                        } else {
                            VStack(alignment: .leading) {
                                HStack {
                                    Text(file.destFileName)
                                        .lineLimit(1)
                                    if file.newFolder == true {
                                        Image(systemName: "folder.badge.plus")
                                            .foregroundColor(.blue)
                                            .font(.caption)
                                    }
                                }
                                Text(shortenPath(file.destFolder))
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .lineLimit(1)
                            }
                        }
                    }
                    .width(min: 200, ideal: 250)

                    TableColumn("Time", value: \.timestamp) { file in
                        if let date = file.timestampDate {
                            Text(date, style: .relative)
                                .foregroundColor(.secondary)
                        } else {
                            Text(file.timestamp)
                                .foregroundColor(.secondary)
                        }
                    }
                    .width(100)

                    TableColumn("Actions") { file in
                        if recentlyMovedIds.contains(file.id) {
                            Text("MOVED")
                                .font(.caption.bold())
                                .foregroundColor(.green)
                        } else {
                            HStack(spacing: 4) {
                                Button {
                                    selectedFile = file
                                } label: {
                                    Image(systemName: "info.circle")
                                }
                                .buttonStyle(.borderless)
                                .help("View Details")

                                if file.isDelete {
                                    Button(role: .destructive) {
                                        deleteFile(file)
                                    } label: {
                                        Image(systemName: "trash")
                                    }
                                    .buttonStyle(.bordered)
                                } else {
                                    Button {
                                        promptSkipReason(file)
                                    } label: {
                                        Image(systemName: "arrow.right.circle")
                                    }
                                    .buttonStyle(.bordered)
                                    .help("Skip")

                                    Button {
                                        moveFile(file)
                                    } label: {
                                        Image(systemName: "checkmark.circle.fill")
                                    }
                                    .buttonStyle(.borderedProminent)
                                    .help("Move")
                                }
                            }
                        }
                    }
                    .width(120)
                }
                .tableStyle(.inset(alternatesRowBackgrounds: true))
                .onChange(of: sortOrder) { _, newOrder in
                    // Table auto-sorts when sortOrder changes
                }
                .onDoubleClick(of: FileEntry.self) { file in
                    selectedFile = file
                }
                .onKeyPress(.space) {
                    openInfoForSelection()
                    return .handled
                }
            }

            Divider()

            // Bottom bar with bulk actions
            HStack {
                if !selection.isEmpty {
                    Text("\(selection.count) selected")
                        .foregroundColor(.secondary)

                    Button("Clear") {
                        selection.removeAll()
                    }

                    Spacer()

                    Button {
                        showingBulkSkipReason = true
                    } label: {
                        Label("Skip Selected", systemImage: "arrow.right.circle")
                    }

                    Button {
                        moveSelected()
                    } label: {
                        Label("Move Selected", systemImage: "checkmark.circle.fill")
                    }
                    .buttonStyle(.borderedProminent)
                } else {
                    Text("Press Space or double-click to see details")
                        .foregroundColor(.secondary)
                    Spacer()
                }
            }
            .padding()
            .background(Color(NSColor.windowBackgroundColor))
        }
        .sheet(item: $selectedFile) { file in
            FileDetailSheet(
                file: file,
                onMove: moveFile,
                onSkip: { f in
                    selectedFile = nil  // Close detail sheet first
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        promptSkipReason(f)
                    }
                },
                onDelete: deleteFile
            )
        }
        .alert(alertTitle, isPresented: $showingAlert) {
            Button("OK") { }
        } message: {
            Text(alertMessage)
        }
        .sheet(item: $fileToSkip) { file in
            SkipReasonSheet(
                fileName: file.sourceFileName,
                reason: $skipReason,
                onSkip: {
                    skipFile(file, reason: skipReason)
                    skipReason = ""
                    fileToSkip = nil
                },
                onCancel: {
                    skipReason = ""
                    fileToSkip = nil
                }
            )
        }
        .sheet(isPresented: $showingBulkSkipReason) {
            SkipReasonSheet(
                fileName: "\(selection.count) files",
                reason: $bulkSkipReason,
                onSkip: {
                    skipSelected(reason: bulkSkipReason)
                    bulkSkipReason = ""
                    showingBulkSkipReason = false
                },
                onCancel: {
                    bulkSkipReason = ""
                    showingBulkSkipReason = false
                }
            )
        }
        .onChange(of: queueManager.files) { _, _ in
            // Clear recently moved files when queue reloads
            recentlyMovedFiles.removeAll()
        }
        .frame(minWidth: 900, minHeight: 500)
    }

    // MARK: - Actions

    private func moveFile(_ file: FileEntry) {
        do {
            try FileOperations.shared.moveFile(from: file.sourcePath, to: file.destPath)
            queueManager.appendToHistory(file, movedAt: Date())
            recentlyMovedFiles.append(file)
            queueManager.removeFile(id: file.id)
        } catch {
            showError("Move failed: \(error.localizedDescription)")
        }
    }

    private func promptSkipReason(_ file: FileEntry) {
        fileToSkip = file
    }

    private func skipFile(_ file: FileEntry, reason: String = "") {
        do {
            let skippedTo = try FileOperations.shared.skipFile(from: file.sourcePath)
            queueManager.appendToSkipHistory(file, skippedAt: Date(), skippedTo: skippedTo, reason: reason)
            recentlyMovedFiles.append(file)
            queueManager.removeFile(id: file.id)
        } catch {
            showError("Skip failed: \(error.localizedDescription)")
        }
    }

    private func deleteFile(_ file: FileEntry) {
        do {
            try FileOperations.shared.deleteFile(at: file.sourcePath)
            queueManager.appendToHistory(file, movedAt: Date())
            recentlyMovedFiles.append(file)
            queueManager.removeFile(id: file.id)
        } catch {
            showError("Delete failed: \(error.localizedDescription)")
        }
    }

    private func moveSelected() {
        let filesToMove = filteredFiles.filter { selection.contains($0.id) && !recentlyMovedIds.contains($0.id) }
        var lastError: String?

        for file in filesToMove {
            do {
                if file.isDelete {
                    try FileOperations.shared.deleteFile(at: file.sourcePath)
                } else {
                    try FileOperations.shared.moveFile(from: file.sourcePath, to: file.destPath)
                }
                queueManager.appendToHistory(file, movedAt: Date())
                recentlyMovedFiles.append(file)
                queueManager.removeFile(id: file.id)
            } catch {
                lastError = error.localizedDescription
            }
        }

        selection.removeAll()

        if let error = lastError {
            showError("Some files failed to move: \(error)")
        }
    }

    private func skipSelected(reason: String = "") {
        let filesToSkip = filteredFiles.filter { selection.contains($0.id) && !recentlyMovedIds.contains($0.id) }
        var lastError: String?

        for file in filesToSkip {
            do {
                let skippedTo = try FileOperations.shared.skipFile(from: file.sourcePath)
                queueManager.appendToSkipHistory(file, skippedAt: Date(), skippedTo: skippedTo, reason: reason)
                recentlyMovedFiles.append(file)
                queueManager.removeFile(id: file.id)
            } catch {
                lastError = error.localizedDescription
            }
        }

        selection.removeAll()

        if let error = lastError {
            showError("Some files failed to skip: \(error)")
        }
    }

    // MARK: - Helpers

    private func openInfoForSelection() {
        // Open info modal for the first selected file
        if let firstSelectedId = selection.first,
           let file = filteredFiles.first(where: { $0.id == firstSelectedId }) {
            selectedFile = file
        }
    }

    private func shortenPath(_ path: String) -> String {
        path.replacingOccurrences(of: NSHomeDirectory(), with: "~")
    }

    private func showError(_ message: String) {
        alertTitle = "Error"
        alertMessage = message
        showingAlert = true
    }
}

// Extension to handle double-click on table rows
extension View {
    func onDoubleClick<T: Identifiable>(of type: T.Type, perform action: @escaping (T) -> Void) -> some View {
        self.gesture(TapGesture(count: 2).onEnded { _ in
            // This is a simplified version - full implementation would need table coordination
        })
    }
}

#Preview {
    ContentView()
}
