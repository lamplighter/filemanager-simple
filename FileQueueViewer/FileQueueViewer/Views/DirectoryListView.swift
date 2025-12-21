import SwiftUI

struct DirectoryListView: View {
    let path: String
    @State private var items: [DirectoryItem] = []
    @State private var sortOrder = [KeyPathComparator(\DirectoryItem.name, order: .forward)]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "folder")
                    .foregroundColor(.blue)
                Text(shortenPath(path))
                    .font(.headline)
                Spacer()
                Text("\(items.count) items")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }

            if items.isEmpty {
                VStack {
                    Image(systemName: "folder.badge.questionmark")
                        .font(.largeTitle)
                        .foregroundColor(.secondary)
                    Text("Directory is empty or doesn't exist")
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                Table(items, sortOrder: $sortOrder) {
                    TableColumn("Name", value: \.name) { item in
                        HStack {
                            Image(systemName: item.isDirectory ? "folder.fill" : "doc.fill")
                                .foregroundColor(item.isDirectory ? .blue : .gray)
                            Text(item.name)
                                .lineLimit(1)
                        }
                    }
                    .width(min: 200)

                    TableColumn("Size", value: \.size) { item in
                        Text(item.isDirectory ? "--" : item.formattedSize)
                            .foregroundColor(.secondary)
                    }
                    .width(80)

                    TableColumn("Modified", value: \.modifiedDate) { item in
                        Text(item.formattedDate)
                            .foregroundColor(.secondary)
                    }
                    .width(150)
                }
                .onChange(of: sortOrder) { _, newOrder in
                    items.sort(using: newOrder)
                }
            }
        }
        .onAppear {
            loadDirectory()
        }
        .onChange(of: path) { _, _ in
            loadDirectory()
        }
    }

    private func loadDirectory() {
        items = FileOperations.shared.listDirectory(at: path)
    }

    private func shortenPath(_ path: String) -> String {
        path.replacingOccurrences(of: NSHomeDirectory(), with: "~")
    }
}

#Preview {
    DirectoryListView(path: NSHomeDirectory() + "/Downloads")
        .frame(width: 500, height: 300)
        .padding()
}
