import Foundation

struct FileQueue: Codable {
    let schemaVersion: String
    let lastUpdated: String
    var files: [FileEntry]

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case lastUpdated = "last_updated"
        case files
    }
}

struct FileEntry: Codable, Identifiable, Hashable {
    let id: String
    let sourcePath: String
    let destPath: String
    let confidence: Int
    let confidenceFactors: [String: Int]?
    let contentAnalysis: ContentAnalysis?
    var status: String
    let timestamp: String
    let reasoning: String?
    let alternatives: [Alternative]?
    let duplicateOf: [String]?
    let checksum: String?
    let action: String?
    let newFolder: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case sourcePath = "source_path"
        case destPath = "dest_path"
        case confidence
        case confidenceFactors = "confidence_factors"
        case contentAnalysis = "content_analysis"
        case status
        case timestamp
        case reasoning
        case alternatives
        case duplicateOf = "duplicate_of"
        case checksum
        case action
        case newFolder = "new_folder"
    }

    var sourceFileName: String {
        (sourcePath as NSString).lastPathComponent
    }

    var destFileName: String {
        (destPath as NSString).lastPathComponent
    }

    var destFolder: String {
        (destPath as NSString).deletingLastPathComponent
    }

    var isPending: Bool {
        status == "pending"
    }

    var isDelete: Bool {
        destPath == "DELETE" || action == "delete"
    }

    var timestampDate: Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: timestamp) {
            return date
        }
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: timestamp)
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: FileEntry, rhs: FileEntry) -> Bool {
        lhs.id == rhs.id
    }
}

struct ContentAnalysis: Codable {
    let summary: String?
    let detectedEntities: [String]?
    let detectedDates: [String]?

    enum CodingKeys: String, CodingKey {
        case summary
        case detectedEntities = "detected_entities"
        case detectedDates = "detected_dates"
    }
}

struct Alternative: Codable {
    let destPath: String
    let confidence: Int
    let confidenceFactors: [String: Int]?
    let reasoning: String?
    let differences: String?

    enum CodingKeys: String, CodingKey {
        case destPath = "dest_path"
        case confidence
        case confidenceFactors = "confidence_factors"
        case reasoning
        case differences
    }
}
