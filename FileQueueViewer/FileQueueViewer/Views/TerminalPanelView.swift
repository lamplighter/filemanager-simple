import SwiftUI

struct TerminalPanelView: View {
    @Binding var isVisible: Bool
    @State private var workingDirectory = "/Users/marklampert/Code/_TOOLS/hoot"

    var body: some View {
        VStack(spacing: 0) {
            // Header bar
            HStack {
                Image(systemName: "terminal")
                    .foregroundColor(.secondary)
                Text("Terminal")
                    .font(.headline)
                    .foregroundColor(.primary)

                Spacer()

                Button(action: { isVisible = false }) {
                    Image(systemName: "xmark")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
                .help("Close terminal (Cmd+T)")
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            // Terminal view
            TerminalView(workingDirectory: $workingDirectory)
        }
    }
}

struct TerminalPanelView_Previews: PreviewProvider {
    static var previews: some View {
        TerminalPanelView(isVisible: .constant(true))
            .frame(width: 600, height: 300)
    }
}
