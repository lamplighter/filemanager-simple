import SwiftUI

struct FileDetailSheet: View {
    let file: FileEntry
    let onMove: (FileEntry) -> Void
    let onSkip: (FileEntry) -> Void
    let onDelete: (FileEntry) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var selectedTab = 0

    var body: some View {
        VStack(spacing: 0) {
            // Header
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(file.sourceFileName)
                        .font(.title2)
                        .fontWeight(.semibold)
                    Spacer()
                    ConfidenceBadge(confidence: file.confidence)
                }

                if file.isDelete {
                    Label("Duplicate - will be deleted", systemImage: "trash")
                        .foregroundColor(.red)
                        .font(.caption)
                } else if file.newFolder == true {
                    Label("New folder will be created", systemImage: "folder.badge.plus")
                        .foregroundColor(.blue)
                        .font(.caption)
                }
            }
            .padding()
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            // Tab picker
            Picker("", selection: $selectedTab) {
                Text("Details").tag(0)
                Text("Preview").tag(1)
                Text("Directory").tag(2)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            .padding(.vertical, 8)

            Divider()

            // Tab content
            Group {
                switch selectedTab {
                case 0:
                    DetailsTabView(file: file)
                case 1:
                    PreviewView(filePath: file.sourcePath)
                case 2:
                    DirectoryListView(path: file.destFolder)
                default:
                    EmptyView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            // Action buttons
            HStack {
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.escape, modifiers: [])

                Spacer()

                if file.isDelete {
                    Button(role: .destructive) {
                        onDelete(file)
                        dismiss()
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                    .keyboardShortcut(.delete, modifiers: [])
                } else {
                    Button {
                        onSkip(file)
                        dismiss()
                    } label: {
                        Label("Skip", systemImage: "arrow.right.circle")
                    }
                    .keyboardShortcut("s", modifiers: .command)

                    Button {
                        onMove(file)
                        dismiss()
                    } label: {
                        Label("Move", systemImage: "arrow.right.doc.on.clipboard")
                    }
                    .keyboardShortcut(.return, modifiers: .command)
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding()
            .background(Color(NSColor.windowBackgroundColor))
        }
        .frame(width: 700, height: 550)
    }
}

struct DetailsTabView: View {
    let file: FileEntry

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Paths
                GroupBox("Paths") {
                    VStack(alignment: .leading, spacing: 8) {
                        LabeledContent("Source") {
                            Text(shortenPath(file.sourcePath))
                                .textSelection(.enabled)
                                .foregroundColor(.secondary)
                        }
                        LabeledContent("Destination") {
                            Text(shortenPath(file.destPath))
                                .textSelection(.enabled)
                                .foregroundColor(.secondary)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }

                // Reasoning
                if let reasoning = file.reasoning, !reasoning.isEmpty {
                    GroupBox("Reasoning") {
                        Text(reasoning)
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                // Content Analysis
                if let analysis = file.contentAnalysis {
                    GroupBox("Content Analysis") {
                        VStack(alignment: .leading, spacing: 8) {
                            if let summary = analysis.summary {
                                Text(summary)
                                    .textSelection(.enabled)
                            }

                            if let entities = analysis.detectedEntities, !entities.isEmpty {
                                LabeledContent("Entities") {
                                    Text(entities.joined(separator: ", "))
                                        .foregroundColor(.blue)
                                }
                            }

                            if let dates = analysis.detectedDates, !dates.isEmpty {
                                LabeledContent("Dates") {
                                    Text(dates.joined(separator: ", "))
                                        .foregroundColor(.green)
                                }
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                // Confidence Factors
                if let factors = file.confidenceFactors, !factors.isEmpty {
                    GroupBox("Confidence Breakdown") {
                        ConfidenceFactorsView(factors: factors)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                // Duplicates
                if let duplicates = file.duplicateOf, !duplicates.isEmpty {
                    GroupBox("Duplicate Of") {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(duplicates, id: \.self) { path in
                                Text(shortenPath(path))
                                    .font(.caption)
                                    .textSelection(.enabled)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                // Alternatives
                if let alternatives = file.alternatives, !alternatives.isEmpty {
                    GroupBox("Alternative Destinations") {
                        VStack(alignment: .leading, spacing: 12) {
                            ForEach(alternatives, id: \.destPath) { alt in
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(shortenPath(alt.destPath))
                                            .fontWeight(.medium)
                                        Spacer()
                                        ConfidenceBadge(confidence: alt.confidence)
                                    }
                                    if let reasoning = alt.reasoning {
                                        Text(reasoning)
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding(.vertical, 4)
                                Divider()
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }

                // Metadata
                GroupBox("Metadata") {
                    VStack(alignment: .leading, spacing: 4) {
                        LabeledContent("ID") {
                            Text(file.id)
                                .font(.caption)
                                .textSelection(.enabled)
                                .foregroundColor(.secondary)
                        }
                        LabeledContent("Timestamp") {
                            Text(file.timestamp)
                                .foregroundColor(.secondary)
                        }
                        LabeledContent("Status") {
                            Text(file.status.capitalized)
                                .foregroundColor(.secondary)
                        }
                        if let checksum = file.checksum {
                            LabeledContent("Checksum") {
                                Text(checksum.prefix(16) + "...")
                                    .font(.caption)
                                    .textSelection(.enabled)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .padding()
        }
    }

    private func shortenPath(_ path: String) -> String {
        path.replacingOccurrences(of: NSHomeDirectory(), with: "~")
    }
}

#Preview {
    FileDetailSheet(
        file: FileEntry(
            id: "test-123",
            sourcePath: "/Users/marklampert/Downloads/test.pdf",
            destPath: "/Users/marklampert/Dropbox/Filing/Test/test.pdf",
            confidence: 85,
            confidenceFactors: ["similar_files_found": 30, "content_match": 20],
            contentAnalysis: ContentAnalysis(
                summary: "PDF document with invoice content",
                detectedEntities: ["TD Bank"],
                detectedDates: ["2024-01-15"]
            ),
            status: "pending",
            timestamp: "2024-01-20T10:30:00Z",
            reasoning: "Found similar TD Bank statements in destination folder",
            alternatives: nil,
            duplicateOf: nil,
            checksum: nil,
            action: nil,
            newFolder: nil
        ),
        onMove: { _ in },
        onSkip: { _ in },
        onDelete: { _ in }
    )
}
