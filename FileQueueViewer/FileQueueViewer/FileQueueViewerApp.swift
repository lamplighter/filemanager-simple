import SwiftUI

@main
struct FileQueueViewerApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .windowStyle(.automatic)
        .commands {
            CommandGroup(replacing: .newItem) { }
        }
    }
}
