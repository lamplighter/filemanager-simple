import XCTest
@testable import FileQueueViewer

final class QueueManagerTests: XCTestCase {

    var tempDir: URL!
    var queuePath: String!
    var historyPath: String!
    var skipHistoryPath: String!
    let fileManager = FileManager.default

    override func setUpWithError() throws {
        try super.setUpWithError()
        // Create a temporary directory for each test
        tempDir = fileManager.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try fileManager.createDirectory(at: tempDir, withIntermediateDirectories: true)

        queuePath = tempDir.appendingPathComponent("file_queue.json").path
        historyPath = tempDir.appendingPathComponent("move_history.json").path
        skipHistoryPath = tempDir.appendingPathComponent("skip_history.json").path
    }

    override func tearDownWithError() throws {
        if fileManager.fileExists(atPath: tempDir.path) {
            try fileManager.removeItem(at: tempDir)
        }
        try super.tearDownWithError()
    }

    // MARK: - Load Queue Tests

    func testLoadQueueWithValidFile() throws {
        // Create a test queue file
        let queueJSON = """
        {
            "schema_version": "1.0",
            "last_updated": "2024-01-15T10:30:00Z",
            "files": [
                {
                    "id": "file-1",
                    "source_path": "/Downloads/a.pdf",
                    "dest_path": "/Filing/a.pdf",
                    "confidence": 90,
                    "status": "pending",
                    "timestamp": "2024-01-15T10:00:00Z"
                },
                {
                    "id": "file-2",
                    "source_path": "/Downloads/b.pdf",
                    "dest_path": "/Filing/b.pdf",
                    "confidence": 80,
                    "status": "completed",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "id": "file-3",
                    "source_path": "/Downloads/c.pdf",
                    "dest_path": "/Filing/c.pdf",
                    "confidence": 70,
                    "status": "pending",
                    "timestamp": "2024-01-15T11:00:00Z"
                }
            ]
        }
        """
        try queueJSON.write(toFile: queuePath, atomically: true, encoding: .utf8)

        // Load queue
        let manager = QueueManager(
            queuePath: queuePath,
            historyPath: historyPath,
            skipHistoryPath: skipHistoryPath
        )

        // Wait for async load
        let expectation = XCTestExpectation(description: "Queue loaded")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: 2.0)

        // Should only have pending files
        XCTAssertEqual(manager.files.count, 2)
        XCTAssertTrue(manager.files.allSatisfy { $0.status == "pending" })
    }

    func testLoadQueueWithMissingFile() throws {
        // Don't create any queue file
        let manager = QueueManager(
            queuePath: queuePath,
            historyPath: historyPath,
            skipHistoryPath: skipHistoryPath
        )

        // Wait for async load
        let expectation = XCTestExpectation(description: "Queue load attempted")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: 2.0)

        // Should have error and no files
        XCTAssertEqual(manager.files.count, 0)
        XCTAssertNotNil(manager.error)
    }

    func testLoadQueueWithInvalidJSON() throws {
        // Create invalid JSON
        try "not valid json {{{".write(toFile: queuePath, atomically: true, encoding: .utf8)

        let manager = QueueManager(
            queuePath: queuePath,
            historyPath: historyPath,
            skipHistoryPath: skipHistoryPath
        )

        // Wait for async load
        let expectation = XCTestExpectation(description: "Queue load attempted")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: 2.0)

        XCTAssertEqual(manager.files.count, 0)
        XCTAssertNotNil(manager.error)
    }

    // MARK: - Remove File Tests

    func testRemoveFile() throws {
        // Create a test queue file
        let queueJSON = """
        {
            "schema_version": "1.0",
            "last_updated": "2024-01-15T10:30:00Z",
            "files": [
                {
                    "id": "to-remove",
                    "source_path": "/Downloads/remove.pdf",
                    "dest_path": "/Filing/remove.pdf",
                    "confidence": 90,
                    "status": "pending",
                    "timestamp": "2024-01-15T10:00:00Z"
                },
                {
                    "id": "to-keep",
                    "source_path": "/Downloads/keep.pdf",
                    "dest_path": "/Filing/keep.pdf",
                    "confidence": 80,
                    "status": "pending",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            ]
        }
        """
        try queueJSON.write(toFile: queuePath, atomically: true, encoding: .utf8)

        let manager = QueueManager(
            queuePath: queuePath,
            historyPath: historyPath,
            skipHistoryPath: skipHistoryPath
        )

        // Wait for load
        let loadExpectation = XCTestExpectation(description: "Queue loaded")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            loadExpectation.fulfill()
        }
        wait(for: [loadExpectation], timeout: 2.0)

        XCTAssertEqual(manager.files.count, 2)

        // Remove file
        manager.removeFile(id: "to-remove")

        XCTAssertEqual(manager.files.count, 1)
        XCTAssertEqual(manager.files[0].id, "to-keep")
    }

    // MARK: - Update Status Tests

    func testUpdateFileStatus() throws {
        let queueJSON = """
        {
            "schema_version": "1.0",
            "last_updated": "2024-01-15T10:30:00Z",
            "files": [
                {
                    "id": "update-me",
                    "source_path": "/Downloads/update.pdf",
                    "dest_path": "/Filing/update.pdf",
                    "confidence": 90,
                    "status": "pending",
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ]
        }
        """
        try queueJSON.write(toFile: queuePath, atomically: true, encoding: .utf8)

        let manager = QueueManager(
            queuePath: queuePath,
            historyPath: historyPath,
            skipHistoryPath: skipHistoryPath
        )

        // Wait for load
        let loadExpectation = XCTestExpectation(description: "Queue loaded")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            loadExpectation.fulfill()
        }
        wait(for: [loadExpectation], timeout: 2.0)

        XCTAssertEqual(manager.files[0].status, "pending")

        manager.updateFileStatus(id: "update-me", status: "completed")

        XCTAssertEqual(manager.files[0].status, "completed")
    }

    // MARK: - History Tests

    func testAppendToHistory() throws {
        let queueJSON = """
        {
            "schema_version": "1.0",
            "last_updated": "2024-01-15T10:30:00Z",
            "files": [
                {
                    "id": "history-test",
                    "source_path": "/Downloads/history.pdf",
                    "dest_path": "/Filing/history.pdf",
                    "confidence": 90,
                    "status": "pending",
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ]
        }
        """
        try queueJSON.write(toFile: queuePath, atomically: true, encoding: .utf8)

        let manager = QueueManager(
            queuePath: queuePath,
            historyPath: historyPath,
            skipHistoryPath: skipHistoryPath
        )

        // Wait for load
        let loadExpectation = XCTestExpectation(description: "Queue loaded")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            loadExpectation.fulfill()
        }
        wait(for: [loadExpectation], timeout: 2.0)

        let entry = manager.files[0]
        manager.appendToHistory(entry, movedAt: Date())

        // History file should now exist
        XCTAssertTrue(fileManager.fileExists(atPath: historyPath))

        // Read and verify
        let historyData = try Data(contentsOf: URL(fileURLWithPath: historyPath))
        let history = try JSONSerialization.jsonObject(with: historyData) as? [[String: Any]]

        XCTAssertEqual(history?.count, 1)
        XCTAssertEqual(history?[0]["id"] as? String, "history-test")
        XCTAssertEqual(history?[0]["status"] as? String, "moved")
    }

    func testAppendToSkipHistory() throws {
        let queueJSON = """
        {
            "schema_version": "1.0",
            "last_updated": "2024-01-15T10:30:00Z",
            "files": [
                {
                    "id": "skip-test",
                    "source_path": "/Downloads/skip.pdf",
                    "dest_path": "/Filing/skip.pdf",
                    "confidence": 50,
                    "status": "pending",
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ]
        }
        """
        try queueJSON.write(toFile: queuePath, atomically: true, encoding: .utf8)

        let manager = QueueManager(
            queuePath: queuePath,
            historyPath: historyPath,
            skipHistoryPath: skipHistoryPath
        )

        // Wait for load
        let loadExpectation = XCTestExpectation(description: "Queue loaded")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            loadExpectation.fulfill()
        }
        wait(for: [loadExpectation], timeout: 2.0)

        let entry = manager.files[0]
        manager.appendToSkipHistory(entry, skippedAt: Date(), skippedTo: "/Skipped/skip.pdf")

        // Skip history file should now exist
        XCTAssertTrue(fileManager.fileExists(atPath: skipHistoryPath))

        // Read and verify
        let historyData = try Data(contentsOf: URL(fileURLWithPath: skipHistoryPath))
        let history = try JSONSerialization.jsonObject(with: historyData) as? [[String: Any]]

        XCTAssertEqual(history?.count, 1)
        XCTAssertEqual(history?[0]["id"] as? String, "skip-test")
        XCTAssertEqual(history?[0]["status"] as? String, "skipped")
        XCTAssertEqual(history?[0]["skipped_to"] as? String, "/Skipped/skip.pdf")
    }
}
