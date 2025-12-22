import SwiftUI
import SwiftTerm

struct TerminalView: NSViewRepresentable {
    @Binding var workingDirectory: String

    func makeNSView(context: Context) -> LocalProcessTerminalView {
        let terminal = LocalProcessTerminalView(frame: .zero)

        // Configure terminal appearance
        terminal.font = NSFont.monospacedSystemFont(ofSize: 13, weight: .regular)

        // Launch Claude Code directly in the working directory
        let currentDir = workingDirectory.isEmpty ? FileManager.default.currentDirectoryPath : workingDirectory
        FileManager.default.changeCurrentDirectoryPath(currentDir)
        terminal.startProcess(executable: "/opt/homebrew/bin/claude", args: [], environment: nil, execName: nil)

        return terminal
    }

    func updateNSView(_ nsView: LocalProcessTerminalView, context: Context) {
        // Terminal updates handled internally by SwiftTerm
    }
}

struct TerminalView_Previews: PreviewProvider {
    static var previews: some View {
        TerminalView(workingDirectory: .constant(""))
            .frame(width: 600, height: 300)
    }
}
