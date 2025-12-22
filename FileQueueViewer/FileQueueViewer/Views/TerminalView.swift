import SwiftUI
import SwiftTerm

struct TerminalView: NSViewRepresentable {
    @Binding var workingDirectory: String

    func makeNSView(context: Context) -> LocalProcessTerminalView {
        let terminal = LocalProcessTerminalView(frame: .zero)

        // Configure terminal appearance
        terminal.font = NSFont.monospacedSystemFont(ofSize: 13, weight: .regular)

        // Start shell in the working directory
        let shell = ProcessInfo.processInfo.environment["SHELL"] ?? "/bin/zsh"
        terminal.startProcess(executable: shell, args: [], environment: nil, execName: nil)

        // Change to working directory
        if !workingDirectory.isEmpty {
            terminal.send(txt: "cd \"\(workingDirectory)\" && clear\n")
        }

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
