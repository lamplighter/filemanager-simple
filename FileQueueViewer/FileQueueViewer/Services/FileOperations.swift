import Foundation

enum FileOperationError: LocalizedError {
    case sourceNotFound(String)
    case destinationExists(String)
    case createDirectoryFailed(String)
    case moveFailed(String)
    case deleteFailed(String)

    var errorDescription: String? {
        switch self {
        case .sourceNotFound(let path):
            return "Source file not found: \(path)"
        case .destinationExists(let path):
            return "Destination already exists: \(path)"
        case .createDirectoryFailed(let error):
            return "Failed to create directory: \(error)"
        case .moveFailed(let error):
            return "Failed to move file: \(error)"
        case .deleteFailed(let error):
            return "Failed to delete file: \(error)"
        }
    }
}

struct DirectoryItem: Identifiable {
    let id = UUID()
    let name: String
    let path: String
    let size: Int64
    let modifiedDate: Date
    let isDirectory: Bool

    var formattedSize: String {
        ByteCountFormatter.string(fromByteCount: size, countStyle: .file)
    }

    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: modifiedDate)
    }
}

class FileOperations {
    static let shared = FileOperations()
    private let fileManager = FileManager.default
    private let skippedPath = NSHomeDirectory() + "/Downloads/Skipped"

    private init() {}

    func moveFile(from source: String, to destination: String) throws {
        // Normalize paths
        let sourcePath = (source as NSString).expandingTildeInPath
        let destPath = (destination as NSString).expandingTildeInPath

        // Check source exists
        guard fileManager.fileExists(atPath: sourcePath) else {
            throw FileOperationError.sourceNotFound(sourcePath)
        }

        // Create destination directory if needed
        let destDir = (destPath as NSString).deletingLastPathComponent
        if !fileManager.fileExists(atPath: destDir) {
            do {
                try fileManager.createDirectory(atPath: destDir, withIntermediateDirectories: true)
            } catch {
                throw FileOperationError.createDirectoryFailed(error.localizedDescription)
            }
        }

        // Handle existing destination
        if fileManager.fileExists(atPath: destPath) {
            // Generate unique name
            let uniquePath = generateUniquePath(destPath)
            try performMove(from: sourcePath, to: uniquePath)
        } else {
            try performMove(from: sourcePath, to: destPath)
        }
    }

    func skipFile(from source: String) throws -> String {
        let sourcePath = (source as NSString).expandingTildeInPath
        let fileName = (sourcePath as NSString).lastPathComponent

        // Ensure Skipped directory exists
        if !fileManager.fileExists(atPath: skippedPath) {
            try fileManager.createDirectory(atPath: skippedPath, withIntermediateDirectories: true)
        }

        var destPath = "\(skippedPath)/\(fileName)"
        if fileManager.fileExists(atPath: destPath) {
            destPath = generateUniquePath(destPath)
        }

        try performMove(from: sourcePath, to: destPath)
        return destPath
    }

    func deleteFile(at path: String) throws {
        let fullPath = (path as NSString).expandingTildeInPath

        guard fileManager.fileExists(atPath: fullPath) else {
            throw FileOperationError.sourceNotFound(fullPath)
        }

        do {
            try fileManager.removeItem(atPath: fullPath)
        } catch {
            throw FileOperationError.deleteFailed(error.localizedDescription)
        }
    }

    func listDirectory(at path: String) -> [DirectoryItem] {
        let fullPath = (path as NSString).expandingTildeInPath

        guard fileManager.fileExists(atPath: fullPath) else {
            return []
        }

        do {
            let contents = try fileManager.contentsOfDirectory(atPath: fullPath)
            return contents.compactMap { name -> DirectoryItem? in
                let itemPath = (fullPath as NSString).appendingPathComponent(name)
                guard let attrs = try? fileManager.attributesOfItem(atPath: itemPath) else {
                    return nil
                }

                let size = attrs[.size] as? Int64 ?? 0
                let modified = attrs[.modificationDate] as? Date ?? Date()
                let isDir = (attrs[.type] as? FileAttributeType) == .typeDirectory

                return DirectoryItem(
                    name: name,
                    path: itemPath,
                    size: size,
                    modifiedDate: modified,
                    isDirectory: isDir
                )
            }.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        } catch {
            return []
        }
    }

    func fileExists(at path: String) -> Bool {
        let fullPath = (path as NSString).expandingTildeInPath
        return fileManager.fileExists(atPath: fullPath)
    }

    func getFileSize(at path: String) -> Int64? {
        let fullPath = (path as NSString).expandingTildeInPath
        guard let attrs = try? fileManager.attributesOfItem(atPath: fullPath) else {
            return nil
        }
        return attrs[.size] as? Int64
    }

    private func performMove(from source: String, to destination: String) throws {
        do {
            try fileManager.moveItem(atPath: source, toPath: destination)
        } catch {
            throw FileOperationError.moveFailed(error.localizedDescription)
        }
    }

    private func generateUniquePath(_ path: String) -> String {
        let directory = (path as NSString).deletingLastPathComponent
        let filename = (path as NSString).lastPathComponent
        let ext = (filename as NSString).pathExtension
        let name = (filename as NSString).deletingPathExtension

        var counter = 1
        var newPath: String

        repeat {
            let newName = ext.isEmpty ? "\(name) (\(counter))" : "\(name) (\(counter)).\(ext)"
            newPath = (directory as NSString).appendingPathComponent(newName)
            counter += 1
        } while fileManager.fileExists(atPath: newPath)

        return newPath
    }
}
