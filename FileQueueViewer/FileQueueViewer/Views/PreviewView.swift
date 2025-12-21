import SwiftUI
import PDFKit
import QuickLookUI

struct PreviewView: View {
    let filePath: String

    private var fileExtension: String {
        (filePath as NSString).pathExtension.lowercased()
    }

    private var isImage: Bool {
        ["jpg", "jpeg", "png", "gif", "webp", "heic", "tiff", "bmp"].contains(fileExtension)
    }

    private var isPDF: Bool {
        fileExtension == "pdf"
    }

    private var isText: Bool {
        ["txt", "md", "json", "yaml", "yml", "xml", "csv", "log", "sh", "py", "swift", "js", "ts", "html", "css"].contains(fileExtension)
    }

    var body: some View {
        if !FileManager.default.fileExists(atPath: filePath) {
            VStack {
                Image(systemName: "doc.questionmark")
                    .font(.largeTitle)
                    .foregroundColor(.secondary)
                Text("File not found")
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if isPDF {
            PDFPreviewView(path: filePath)
        } else if isImage {
            ImagePreviewView(path: filePath)
        } else if isText {
            TextPreviewView(path: filePath)
        } else {
            VStack {
                Image(systemName: "doc")
                    .font(.largeTitle)
                    .foregroundColor(.secondary)
                Text("Preview not available for .\(fileExtension) files")
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

struct PDFPreviewView: NSViewRepresentable {
    let path: String

    func makeNSView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.autoScales = true
        pdfView.displayMode = .singlePageContinuous
        pdfView.backgroundColor = .textBackgroundColor
        return pdfView
    }

    func updateNSView(_ pdfView: PDFView, context: Context) {
        if let document = PDFDocument(url: URL(fileURLWithPath: path)) {
            pdfView.document = document
        }
    }
}

struct ImagePreviewView: View {
    let path: String

    var body: some View {
        if let image = NSImage(contentsOfFile: path) {
            Image(nsImage: image)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else {
            Text("Failed to load image")
                .foregroundColor(.secondary)
        }
    }
}

struct TextPreviewView: View {
    let path: String
    @State private var content: String = ""
    @State private var error: String?

    var body: some View {
        Group {
            if let error = error {
                Text(error)
                    .foregroundColor(.red)
            } else {
                ScrollView {
                    Text(content)
                        .font(.system(.body, design: .monospaced))
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                }
            }
        }
        .onAppear {
            loadContent()
        }
    }

    private func loadContent() {
        do {
            let data = try Data(contentsOf: URL(fileURLWithPath: path))
            if let text = String(data: data, encoding: .utf8) {
                // Limit to first 500 lines
                let lines = text.components(separatedBy: .newlines)
                if lines.count > 500 {
                    content = lines.prefix(500).joined(separator: "\n") + "\n\n... (truncated at 500 lines)"
                } else {
                    content = text
                }
            } else {
                error = "Unable to decode file as text"
            }
        } catch {
            self.error = error.localizedDescription
        }
    }
}

#Preview {
    PreviewView(filePath: "/Users/marklampert/Downloads/test.pdf")
        .frame(width: 600, height: 400)
}
