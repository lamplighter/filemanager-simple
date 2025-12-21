import SwiftUI

struct ConfidenceBadge: View {
    let confidence: Int

    private var color: Color {
        if confidence >= 90 {
            return .green
        } else if confidence >= 50 {
            return .orange
        } else {
            return .red
        }
    }

    private var label: String {
        if confidence >= 90 {
            return "High"
        } else if confidence >= 50 {
            return "Medium"
        } else {
            return "Low"
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Text("\(confidence)%")
                .fontWeight(.semibold)
            Text(label)
                .font(.caption)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.2))
        .foregroundColor(color)
        .cornerRadius(6)
    }
}

struct ConfidenceFactorsView: View {
    let factors: [String: Int]

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            ForEach(factors.sorted(by: { $0.value > $1.value }), id: \.key) { key, value in
                HStack {
                    Text(formatFactorName(key))
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("+\(value)")
                        .fontWeight(.medium)
                        .foregroundColor(.green)
                }
                .font(.caption)
            }
        }
    }

    private func formatFactorName(_ name: String) -> String {
        name.replacingOccurrences(of: "_", with: " ")
            .capitalized
    }
}

#Preview {
    VStack(spacing: 20) {
        ConfidenceBadge(confidence: 95)
        ConfidenceBadge(confidence: 72)
        ConfidenceBadge(confidence: 35)

        ConfidenceFactorsView(factors: [
            "similar_files_found": 30,
            "content_entity_match": 20,
            "file_type_match": 15
        ])
        .padding()
    }
    .padding()
}
