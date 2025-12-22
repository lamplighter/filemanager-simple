import Foundation
import Combine

class QueueManager: ObservableObject {
    @Published var files: [FileEntry] = []
    @Published var isLoading = false
    @Published var error: String?

    private var fileWatcher: DispatchSourceFileSystemObject?
    private var fileDescriptor: Int32 = -1

    private let queuePath: String
    private let historyPath: String
    private let skipHistoryPath: String
    private let enableWatching: Bool
    private let checkFileExists: Bool

    init() {
        let basePath = "/Users/marklampert/Code/_TOOLS/hoot/state"
        self.queuePath = "\(basePath)/file_queue.json"
        self.historyPath = "\(basePath)/move_history.json"
        self.skipHistoryPath = "\(basePath)/skip_history.json"
        self.enableWatching = true
        self.checkFileExists = true

        loadQueue()
        startWatching()
    }

    /// Test initializer with custom paths
    init(queuePath: String, historyPath: String, skipHistoryPath: String, enableWatching: Bool = false, checkFileExists: Bool = false) {
        self.queuePath = queuePath
        self.historyPath = historyPath
        self.skipHistoryPath = skipHistoryPath
        self.enableWatching = enableWatching
        self.checkFileExists = checkFileExists

        loadQueue()
        if enableWatching {
            startWatching()
        }
    }

    deinit {
        stopWatching()
    }

    func loadQueue() {
        isLoading = true
        error = nil

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }

            do {
                let data = try Data(contentsOf: URL(fileURLWithPath: self.queuePath))
                let queue = try JSONDecoder().decode(FileQueue.self, from: data)

                // Filter to pending files (and optionally check source still exists)
                let pendingFiles = queue.files.filter { entry in
                    entry.status == "pending" && (!self.checkFileExists || FileManager.default.fileExists(atPath: entry.sourcePath))
                }

                DispatchQueue.main.async {
                    self.files = pendingFiles
                    self.isLoading = false
                }
            } catch {
                DispatchQueue.main.async {
                    self.error = "Failed to load queue: \(error.localizedDescription)"
                    self.isLoading = false
                }
            }
        }
    }

    func updateFileStatus(id: String, status: String) {
        guard let index = files.firstIndex(where: { $0.id == id }) else { return }
        files[index].status = status
        saveQueue()
    }

    func removeFile(id: String) {
        files.removeAll { $0.id == id }
        saveQueue()
    }

    private func saveQueue() {
        do {
            // Read full queue to preserve non-pending items
            let data = try Data(contentsOf: URL(fileURLWithPath: queuePath))
            var queue = try JSONDecoder().decode(FileQueue.self, from: data)

            // Keep non-pending items from disk, replace pending items with our current list
            let nonPendingFiles = queue.files.filter { $0.status != "pending" }
            queue.files = nonPendingFiles + files

            // Write atomically
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            let outputData = try encoder.encode(queue)

            let tempPath = queuePath + ".tmp"
            let tempURL = URL(fileURLWithPath: tempPath)
            let destURL = URL(fileURLWithPath: queuePath)
            try outputData.write(to: tempURL)
            _ = try FileManager.default.replaceItemAt(destURL, withItemAt: tempURL)
        } catch {
            self.error = "Failed to save queue: \(error.localizedDescription)"
        }
    }

    func appendToHistory(_ entry: FileEntry, movedAt: Date) {
        appendToHistoryFile(historyPath, entry: entry, timestamp: movedAt, status: "moved")
    }

    func appendToSkipHistory(_ entry: FileEntry, skippedAt: Date, skippedTo: String, reason: String) {
        var fields = ["skipped_to": skippedTo]
        if !reason.isEmpty {
            fields["reason"] = reason
        }
        appendToHistoryFile(skipHistoryPath, entry: entry, timestamp: skippedAt, status: "skipped", extraFields: fields)
    }

    private func appendToHistoryFile(_ path: String, entry: FileEntry, timestamp: Date, status: String, extraFields: [String: String] = [:]) {
        do {
            var history: [[String: Any]] = []

            if FileManager.default.fileExists(atPath: path) {
                let data = try Data(contentsOf: URL(fileURLWithPath: path))
                if let existing = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] {
                    history = existing
                }
            }

            let formatter = ISO8601DateFormatter()
            var record: [String: Any] = [
                "id": entry.id,
                "source_path": entry.sourcePath,
                "dest_path": entry.destPath,
                "status": status,
                "\(status)_at": formatter.string(from: timestamp)
            ]

            for (key, value) in extraFields {
                record[key] = value
            }

            history.append(record)

            let outputData = try JSONSerialization.data(withJSONObject: history, options: [.prettyPrinted, .sortedKeys])
            try outputData.write(to: URL(fileURLWithPath: path))
        } catch {
            print("Failed to append to history: \(error)")
        }
    }

    private func startWatching() {
        fileDescriptor = open(queuePath, O_EVTONLY)
        guard fileDescriptor >= 0 else { return }

        fileWatcher = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: fileDescriptor,
            eventMask: [.write, .rename],
            queue: DispatchQueue.global(qos: .utility)
        )

        fileWatcher?.setEventHandler { [weak self] in
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self?.loadQueue()
            }
        }

        fileWatcher?.setCancelHandler { [weak self] in
            if let fd = self?.fileDescriptor, fd >= 0 {
                close(fd)
            }
        }

        fileWatcher?.resume()
    }

    private func stopWatching() {
        fileWatcher?.cancel()
        fileWatcher = nil
    }
}
