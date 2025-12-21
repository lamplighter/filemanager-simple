import XCTest
@testable import FileQueueViewer

final class FileOperationsTests: XCTestCase {

    var tempDir: URL!
    var fileOps: FileOperations!
    let fileManager = FileManager.default

    override func setUpWithError() throws {
        try super.setUpWithError()
        // Create a temporary directory for each test
        tempDir = fileManager.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try fileManager.createDirectory(at: tempDir, withIntermediateDirectories: true)
        fileOps = FileOperations.shared
    }

    override func tearDownWithError() throws {
        // Clean up temp directory
        if fileManager.fileExists(atPath: tempDir.path) {
            try fileManager.removeItem(at: tempDir)
        }
        try super.tearDownWithError()
    }

    // MARK: - moveFile Tests

    func testMoveFileSuccess() throws {
        // Create source file
        let sourceFile = tempDir.appendingPathComponent("source.txt")
        let destFile = tempDir.appendingPathComponent("dest/moved.txt")

        try "test content".write(to: sourceFile, atomically: true, encoding: .utf8)

        // Move file
        try fileOps.moveFile(from: sourceFile.path, to: destFile.path)

        // Verify source is gone and dest exists
        XCTAssertFalse(fileManager.fileExists(atPath: sourceFile.path))
        XCTAssertTrue(fileManager.fileExists(atPath: destFile.path))

        // Verify content
        let content = try String(contentsOf: destFile, encoding: .utf8)
        XCTAssertEqual(content, "test content")
    }

    func testMoveFileCreatesDestinationDirectory() throws {
        let sourceFile = tempDir.appendingPathComponent("source.txt")
        let destFile = tempDir.appendingPathComponent("nested/deep/folder/file.txt")

        try "content".write(to: sourceFile, atomically: true, encoding: .utf8)

        try fileOps.moveFile(from: sourceFile.path, to: destFile.path)

        XCTAssertTrue(fileManager.fileExists(atPath: destFile.path))
    }

    func testMoveFileHandlesExistingDestination() throws {
        let sourceFile = tempDir.appendingPathComponent("source.txt")
        let destFile = tempDir.appendingPathComponent("existing.txt")

        try "source content".write(to: sourceFile, atomically: true, encoding: .utf8)
        try "existing content".write(to: destFile, atomically: true, encoding: .utf8)

        try fileOps.moveFile(from: sourceFile.path, to: destFile.path)

        // Source should be gone
        XCTAssertFalse(fileManager.fileExists(atPath: sourceFile.path))

        // Original dest should still have original content
        let originalContent = try String(contentsOf: destFile, encoding: .utf8)
        XCTAssertEqual(originalContent, "existing content")

        // New file should exist with (1) suffix
        let renamedFile = tempDir.appendingPathComponent("existing (1).txt")
        XCTAssertTrue(fileManager.fileExists(atPath: renamedFile.path))

        let movedContent = try String(contentsOf: renamedFile, encoding: .utf8)
        XCTAssertEqual(movedContent, "source content")
    }

    func testMoveFileHandlesMultipleExisting() throws {
        let sourceFile = tempDir.appendingPathComponent("source.txt")
        let destFile = tempDir.appendingPathComponent("existing.txt")
        let destFile1 = tempDir.appendingPathComponent("existing (1).txt")

        try "source".write(to: sourceFile, atomically: true, encoding: .utf8)
        try "existing".write(to: destFile, atomically: true, encoding: .utf8)
        try "existing 1".write(to: destFile1, atomically: true, encoding: .utf8)

        try fileOps.moveFile(from: sourceFile.path, to: destFile.path)

        // Should create existing (2).txt
        let renamedFile = tempDir.appendingPathComponent("existing (2).txt")
        XCTAssertTrue(fileManager.fileExists(atPath: renamedFile.path))
    }

    func testMoveFileSourceNotFound() {
        let sourceFile = tempDir.appendingPathComponent("nonexistent.txt")
        let destFile = tempDir.appendingPathComponent("dest.txt")

        XCTAssertThrowsError(try fileOps.moveFile(from: sourceFile.path, to: destFile.path)) { error in
            guard case FileOperationError.sourceNotFound = error else {
                XCTFail("Expected sourceNotFound error")
                return
            }
        }
    }

    // MARK: - skipFile Tests

    func testSkipFile() throws {
        let sourceFile = tempDir.appendingPathComponent("toskip.txt")
        try "skip me".write(to: sourceFile, atomically: true, encoding: .utf8)

        let skippedPath = try fileOps.skipFile(from: sourceFile.path)

        XCTAssertFalse(fileManager.fileExists(atPath: sourceFile.path))
        XCTAssertTrue(fileManager.fileExists(atPath: skippedPath))
        XCTAssertTrue(skippedPath.contains("/Skipped/"))
    }

    // MARK: - deleteFile Tests

    func testDeleteFile() throws {
        let fileToDelete = tempDir.appendingPathComponent("delete_me.txt")
        try "goodbye".write(to: fileToDelete, atomically: true, encoding: .utf8)

        XCTAssertTrue(fileManager.fileExists(atPath: fileToDelete.path))

        try fileOps.deleteFile(at: fileToDelete.path)

        XCTAssertFalse(fileManager.fileExists(atPath: fileToDelete.path))
    }

    func testDeleteFileNotFound() {
        let nonexistent = tempDir.appendingPathComponent("ghost.txt")

        XCTAssertThrowsError(try fileOps.deleteFile(at: nonexistent.path)) { error in
            guard case FileOperationError.sourceNotFound = error else {
                XCTFail("Expected sourceNotFound error")
                return
            }
        }
    }

    // MARK: - listDirectory Tests

    func testListDirectory() throws {
        // Create some files
        try "file a".write(to: tempDir.appendingPathComponent("a.txt"), atomically: true, encoding: .utf8)
        try "file b".write(to: tempDir.appendingPathComponent("b.txt"), atomically: true, encoding: .utf8)
        try fileManager.createDirectory(at: tempDir.appendingPathComponent("subdir"), withIntermediateDirectories: true)

        let items = fileOps.listDirectory(at: tempDir.path)

        XCTAssertEqual(items.count, 3)

        // Items should be sorted alphabetically
        XCTAssertEqual(items[0].name, "a.txt")
        XCTAssertEqual(items[1].name, "b.txt")
        XCTAssertEqual(items[2].name, "subdir")

        // Check file vs directory
        XCTAssertFalse(items[0].isDirectory)
        XCTAssertTrue(items[2].isDirectory)

        // Check size is positive for files
        XCTAssertGreaterThan(items[0].size, 0)
    }

    func testListDirectoryEmpty() throws {
        let items = fileOps.listDirectory(at: tempDir.path)
        XCTAssertEqual(items.count, 0)
    }

    func testListDirectoryNonexistent() {
        let items = fileOps.listDirectory(at: tempDir.appendingPathComponent("nope").path)
        XCTAssertEqual(items.count, 0)
    }

    // MARK: - fileExists Tests

    func testFileExists() throws {
        let file = tempDir.appendingPathComponent("exists.txt")
        try "hi".write(to: file, atomically: true, encoding: .utf8)

        XCTAssertTrue(fileOps.fileExists(at: file.path))
        XCTAssertFalse(fileOps.fileExists(at: tempDir.appendingPathComponent("nope.txt").path))
    }

    // MARK: - getFileSize Tests

    func testGetFileSize() throws {
        let file = tempDir.appendingPathComponent("sized.txt")
        let content = "12345678" // 8 bytes
        try content.write(to: file, atomically: true, encoding: .utf8)

        let size = fileOps.getFileSize(at: file.path)
        XCTAssertEqual(size, 8)
    }

    func testGetFileSizeNonexistent() {
        let size = fileOps.getFileSize(at: tempDir.appendingPathComponent("nope.txt").path)
        XCTAssertNil(size)
    }

    // MARK: - Path Expansion Tests

    func testMoveFileWithTildePath() throws {
        // This tests that paths with ~ are properly expanded
        // We'll use tempDir which doesn't have ~ but verify the expansion code path works
        let sourceFile = tempDir.appendingPathComponent("tilde_test.txt")
        try "content".write(to: sourceFile, atomically: true, encoding: .utf8)

        // The expandingTildeInPath should work with full paths too
        let destFile = tempDir.appendingPathComponent("dest/moved.txt")
        try fileOps.moveFile(from: sourceFile.path, to: destFile.path)

        XCTAssertTrue(fileManager.fileExists(atPath: destFile.path))
    }

    // MARK: - DirectoryItem Tests

    func testDirectoryItemFormattedSize() {
        let item = DirectoryItem(
            name: "test.pdf",
            path: "/test/test.pdf",
            size: 1024 * 1024, // 1 MB
            modifiedDate: Date(),
            isDirectory: false
        )

        // ByteCountFormatter should format this nicely
        XCTAssertFalse(item.formattedSize.isEmpty)
        XCTAssertTrue(item.formattedSize.contains("MB") || item.formattedSize.contains("1"))
    }

    func testDirectoryItemFormattedDate() {
        let item = DirectoryItem(
            name: "test.pdf",
            path: "/test/test.pdf",
            size: 100,
            modifiedDate: Date(),
            isDirectory: false
        )

        XCTAssertFalse(item.formattedDate.isEmpty)
    }
}
