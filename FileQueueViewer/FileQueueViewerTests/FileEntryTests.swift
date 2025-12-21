import XCTest
@testable import FileQueueViewer

final class FileEntryTests: XCTestCase {

    // MARK: - JSON Decoding Tests

    func testDecodeCompleteEntry() throws {
        let json = """
        {
            "id": "test-123",
            "source_path": "/Users/test/Downloads/invoice.pdf",
            "dest_path": "/Users/test/Filing/Invoices/2024-01-15.pdf",
            "confidence": 95,
            "confidence_factors": {
                "similar_files_found": 30,
                "content_entity_match": 20
            },
            "content_analysis": {
                "summary": "Invoice from Acme Corp",
                "detected_entities": ["Acme", "Corp"],
                "detected_dates": ["2024-01-15"]
            },
            "status": "pending",
            "timestamp": "2024-01-15T10:30:00Z",
            "reasoning": "Found similar invoices in destination"
        }
        """

        let data = json.data(using: .utf8)!
        let entry = try JSONDecoder().decode(FileEntry.self, from: data)

        XCTAssertEqual(entry.id, "test-123")
        XCTAssertEqual(entry.sourcePath, "/Users/test/Downloads/invoice.pdf")
        XCTAssertEqual(entry.destPath, "/Users/test/Filing/Invoices/2024-01-15.pdf")
        XCTAssertEqual(entry.confidence, 95)
        XCTAssertEqual(entry.status, "pending")
        XCTAssertEqual(entry.reasoning, "Found similar invoices in destination")

        // Content analysis
        XCTAssertEqual(entry.contentAnalysis?.summary, "Invoice from Acme Corp")
        XCTAssertEqual(entry.contentAnalysis?.detectedEntities, ["Acme", "Corp"])
        XCTAssertEqual(entry.contentAnalysis?.detectedDates, ["2024-01-15"])

        // Confidence factors
        XCTAssertEqual(entry.confidenceFactors?["similar_files_found"], 30)
        XCTAssertEqual(entry.confidenceFactors?["content_entity_match"], 20)
    }

    func testDecodeMinimalEntry() throws {
        let json = """
        {
            "id": "min-456",
            "source_path": "/Downloads/file.txt",
            "dest_path": "/Filing/file.txt",
            "confidence": 50,
            "status": "pending",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        """

        let data = json.data(using: .utf8)!
        let entry = try JSONDecoder().decode(FileEntry.self, from: data)

        XCTAssertEqual(entry.id, "min-456")
        XCTAssertNil(entry.confidenceFactors)
        XCTAssertNil(entry.contentAnalysis)
        XCTAssertNil(entry.reasoning)
        XCTAssertNil(entry.alternatives)
        XCTAssertNil(entry.duplicateOf)
    }

    func testDecodeWithAlternatives() throws {
        let json = """
        {
            "id": "alt-789",
            "source_path": "/Downloads/doc.pdf",
            "dest_path": "/Filing/Option1/doc.pdf",
            "confidence": 80,
            "status": "pending",
            "timestamp": "2024-02-01T12:00:00Z",
            "alternatives": [
                {
                    "dest_path": "/Filing/Option2/doc.pdf",
                    "confidence": 65,
                    "reasoning": "Less specific folder",
                    "differences": "General category vs specific"
                }
            ]
        }
        """

        let data = json.data(using: .utf8)!
        let entry = try JSONDecoder().decode(FileEntry.self, from: data)

        XCTAssertNotNil(entry.alternatives)
        XCTAssertEqual(entry.alternatives?.count, 1)
        XCTAssertEqual(entry.alternatives?[0].destPath, "/Filing/Option2/doc.pdf")
        XCTAssertEqual(entry.alternatives?[0].confidence, 65)
    }

    func testDecodeWithDuplicates() throws {
        let json = """
        {
            "id": "dup-001",
            "source_path": "/Downloads/duplicate.pdf",
            "dest_path": "DELETE",
            "confidence": 100,
            "status": "pending",
            "timestamp": "2024-03-01T00:00:00Z",
            "duplicate_of": ["/Filing/existing.pdf", "/Filing/backup/existing.pdf"],
            "checksum": "abc123def456",
            "action": "delete"
        }
        """

        let data = json.data(using: .utf8)!
        let entry = try JSONDecoder().decode(FileEntry.self, from: data)

        XCTAssertEqual(entry.duplicateOf?.count, 2)
        XCTAssertEqual(entry.checksum, "abc123def456")
        XCTAssertEqual(entry.action, "delete")
    }

    func testDecodeWithNewFolder() throws {
        let json = """
        {
            "id": "new-001",
            "source_path": "/Downloads/newservice.pdf",
            "dest_path": "/Filing/NewService/2024-01-01.pdf",
            "confidence": 75,
            "status": "pending",
            "timestamp": "2024-04-01T00:00:00Z",
            "new_folder": true
        }
        """

        let data = json.data(using: .utf8)!
        let entry = try JSONDecoder().decode(FileEntry.self, from: data)

        XCTAssertEqual(entry.newFolder, true)
    }

    // MARK: - Computed Property Tests

    func testSourceFileName() {
        let entry = makeEntry(sourcePath: "/Users/test/Downloads/invoice.pdf")
        XCTAssertEqual(entry.sourceFileName, "invoice.pdf")
    }

    func testSourceFileNameWithSpaces() {
        let entry = makeEntry(sourcePath: "/Users/test/Downloads/My Invoice 2024.pdf")
        XCTAssertEqual(entry.sourceFileName, "My Invoice 2024.pdf")
    }

    func testDestFileName() {
        let entry = makeEntry(destPath: "/Users/test/Filing/2024-01-15.pdf")
        XCTAssertEqual(entry.destFileName, "2024-01-15.pdf")
    }

    func testDestFolder() {
        let entry = makeEntry(destPath: "/Users/test/Filing/Invoices/2024-01-15.pdf")
        XCTAssertEqual(entry.destFolder, "/Users/test/Filing/Invoices")
    }

    func testIsPendingTrue() {
        let entry = makeEntry(status: "pending")
        XCTAssertTrue(entry.isPending)
    }

    func testIsPendingFalse() {
        let entry = makeEntry(status: "completed")
        XCTAssertFalse(entry.isPending)
    }

    func testIsDeleteWithDeletePath() {
        let entry = makeEntry(destPath: "DELETE")
        XCTAssertTrue(entry.isDelete)
    }

    func testIsDeleteWithDeleteAction() {
        let entry = makeEntry(destPath: "/some/path", action: "delete")
        XCTAssertTrue(entry.isDelete)
    }

    func testIsDeleteFalse() {
        let entry = makeEntry(destPath: "/Users/test/Filing/file.pdf")
        XCTAssertFalse(entry.isDelete)
    }

    // MARK: - Date Parsing Tests

    func testTimestampDateParsing() {
        let entry = makeEntry(timestamp: "2024-01-15T10:30:00Z")
        XCTAssertNotNil(entry.timestampDate)

        let calendar = Calendar(identifier: .gregorian)
        let components = calendar.dateComponents(in: TimeZone(identifier: "UTC")!, from: entry.timestampDate!)

        XCTAssertEqual(components.year, 2024)
        XCTAssertEqual(components.month, 1)
        XCTAssertEqual(components.day, 15)
        XCTAssertEqual(components.hour, 10)
        XCTAssertEqual(components.minute, 30)
    }

    func testTimestampDateWithFractionalSeconds() {
        let entry = makeEntry(timestamp: "2024-01-15T10:30:00.123Z")
        XCTAssertNotNil(entry.timestampDate)
    }

    func testTimestampDateInvalidFormat() {
        let entry = makeEntry(timestamp: "not-a-date")
        XCTAssertNil(entry.timestampDate)
    }

    // MARK: - FileQueue Tests

    func testDecodeFileQueue() throws {
        let json = """
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
                }
            ]
        }
        """

        let data = json.data(using: .utf8)!
        let queue = try JSONDecoder().decode(FileQueue.self, from: data)

        XCTAssertEqual(queue.schemaVersion, "1.0")
        XCTAssertEqual(queue.files.count, 2)
        XCTAssertEqual(queue.files[0].id, "file-1")
        XCTAssertEqual(queue.files[1].id, "file-2")
    }

    // MARK: - Helper

    private func makeEntry(
        id: String = "test",
        sourcePath: String = "/source/file.pdf",
        destPath: String = "/dest/file.pdf",
        confidence: Int = 80,
        status: String = "pending",
        timestamp: String = "2024-01-01T00:00:00Z",
        action: String? = nil
    ) -> FileEntry {
        // Create via JSON to ensure proper initialization
        var json = """
        {
            "id": "\(id)",
            "source_path": "\(sourcePath)",
            "dest_path": "\(destPath)",
            "confidence": \(confidence),
            "status": "\(status)",
            "timestamp": "\(timestamp)"
        """

        if let action = action {
            // Remove trailing } and add action field
            json += ",\n    \"action\": \"\(action)\"\n}"
        } else {
            json += "\n}"
        }

        let data = json.data(using: .utf8)!
        return try! JSONDecoder().decode(FileEntry.self, from: data)
    }
}
