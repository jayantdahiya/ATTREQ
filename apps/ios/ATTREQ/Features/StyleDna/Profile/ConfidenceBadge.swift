//
//  ConfidenceBadge.swift
//  ATTREQ
//
//  Confidence pill for Style DNA fields (M3-WP3). RN's ConfidenceBadge only
//  flags LOW confidence ("Based on limited data"); this design-language
//  version always states the percentage — gold when the synthesis is sure
//  (>= 0.7), muted otherwise.
//

import SwiftUI

/// Small pill rendering a 0–1 confidence as e.g. "87% CONFIDENT".
struct ConfidenceBadge: View {
    /// Confidence from the synthesis payload, expected in `0...1`.
    let confidence: Double

    var body: some View {
        AttreqPill(
            "\(percent)% confident",
            variant: confidence >= 0.7 ? .gold : .muted
        )
    }

    private var percent: Int {
        Int((min(max(confidence, 0), 1) * 100).rounded())
    }
}

#Preview {
    HStack(spacing: 8) {
        ConfidenceBadge(confidence: 0.87)
        ConfidenceBadge(confidence: 0.7)
        ConfidenceBadge(confidence: 0.42)
    }
    .padding()
    .background(Theme.bg)
}
