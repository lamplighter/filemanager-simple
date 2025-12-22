import SwiftUI

struct SkipReasonSheet: View {
    let fileName: String
    @Binding var reason: String
    let onSkip: () -> Void
    let onCancel: () -> Void

    @FocusState private var isTextFieldFocused: Bool

    var body: some View {
        VStack(spacing: 16) {
            Text("Skip \(fileName)")
                .font(.headline)

            Text("Why are you skipping this file?")
                .foregroundColor(.secondary)

            TextField("Reason (optional)", text: $reason)
                .textFieldStyle(.roundedBorder)
                .focused($isTextFieldFocused)
                .onSubmit {
                    onSkip()
                }

            HStack {
                Button("Cancel") {
                    onCancel()
                }
                .keyboardShortcut(.escape, modifiers: [])

                Spacer()

                Button("Skip") {
                    onSkip()
                }
                .keyboardShortcut(.return, modifiers: [])
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(width: 400)
        .onAppear {
            isTextFieldFocused = true
        }
    }
}

#Preview {
    SkipReasonSheet(
        fileName: "invoice.pdf",
        reason: .constant(""),
        onSkip: { },
        onCancel: { }
    )
}
