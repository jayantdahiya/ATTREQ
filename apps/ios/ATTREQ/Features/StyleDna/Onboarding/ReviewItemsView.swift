//
//  ReviewItemsView.swift
//  ATTREQ
//
//  Style DNA onboarding step 3 (M3). No artboard — composed in the design
//  language. Content mirrors the RN screen
//  `apps/mobile/app/(onboarding)/review-items.tsx` + ItemReviewCard
//  (category/subcategory, colors, pattern, confidence, keep/remove), but as
//  a togglable list per the M3 WP2 spec instead of RN's one-card-at-a-time
//  walkthrough. The items were already seeded server-side during upload, so
//  confirming just completes onboarding (see OnboardingViewModel.confirmReview).
//

import SwiftUI

struct ReviewItemsView: View {
    let model: OnboardingViewModel
    /// Confirms the review (completes onboarding); loading state is
    /// `model.isCompleting`.
    let onConfirm: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 03 — Review", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 8)

            // "Found", not "added": this list is everything DETECTED across
            // all photos (any confidence); the server only auto-added the
            // >= 60%-confidence pieces from usable photos to the wardrobe.
            BodyText("We found these in your photos. Untick anything that isn't yours — you can edit any item later from your wardrobe.")
                .padding(.bottom, 8)

            MonoLabel("High-confidence pieces were added to your wardrobe automatically")
                .padding(.bottom, 18)

            if model.detectedItems.isEmpty {
                emptyState
                    .padding(.bottom, 18)
            } else {
                itemRows
                    .padding(.bottom, 12)

                MonoLabel("\(model.keptItemCount) of \(model.detectedItems.count) kept")
                    .padding(.bottom, 18)
            }

            if let message = model.completionError {
                BodyText(message, size: 13, color: Theme.clay)
                    .padding(.bottom, 12)
            }

            Spacer(minLength: 16)

            AttreqPrimaryButton(
                "Looks right →",
                role: .accent,
                isLoading: model.isCompleting,
                action: onConfirm
            )
        }
    }

    // MARK: - Header

    private var headline: some View {
        (
            Text("Review your\n").foregroundStyle(Theme.text)
                + Text("items.")
                .font(.attreqDisplay(34, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(34))
    }

    private var emptyState: some View {
        BodyText("No wardrobe items were detected in your photos. You can add pieces any time from the Wardrobe tab.", size: 13)
    }

    // MARK: - Item rows

    private var itemRows: some View {
        VStack(spacing: 10) {
            ForEach(Array(model.detectedItems.enumerated()), id: \.offset) { index, item in
                itemRow(item, at: index)
            }
        }
    }

    private func itemRow(_ item: DetectedWardrobeItem, at index: Int) -> some View {
        let isKept = model.reviewSelection.contains(index)
        return Button {
            model.toggleReviewItem(index)
        } label: {
            HStack(spacing: 12) {
                GarmentPlaceholder(tone: Self.tone(for: item.category), cornerRadius: 10)
                    .frame(width: 46, height: 58)

                VStack(alignment: .leading, spacing: 3) {
                    Text(title(for: item))
                        .font(.attreqDisplay(16, italic: true))
                        .foregroundStyle(Theme.text)
                        .lineLimit(1)
                    MonoLabel(detailLine(for: item))
                        .lineLimit(1)
                }

                Spacer(minLength: 8)

                AttreqPill(
                    "\(Int((item.confidence * 100).rounded()))%",
                    variant: item.confidence >= 0.6 ? .gold : .clay
                )

                keepIndicator(isKept: isKept)
            }
            .attreqCard(padding: 12)
            .opacity(isKept ? 1 : 0.45)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(title(for: item)), \(isKept ? "kept" : "removed")")
        .accessibilityAddTraits(isKept ? [.isSelected] : [])
        .accessibilityIdentifier("review-item-\(index)")
    }

    private func keepIndicator(isKept: Bool) -> some View {
        Group {
            if isKept {
                Circle()
                    .fill(Theme.accent)
                    .overlay {
                        AttreqIcon.check.view(size: 12, color: Theme.bg)
                    }
            } else {
                Circle()
                    .strokeBorder(Theme.border, lineWidth: 1.5)
                    .overlay {
                        AttreqIcon.x.view(size: 11, color: Theme.t3)
                    }
            }
        }
        .frame(width: 24, height: 24)
    }

    private func title(for item: DetectedWardrobeItem) -> String {
        (item.subcategory.isEmpty ? item.category : item.subcategory).capitalized
    }

    private func detailLine(for item: DetectedWardrobeItem) -> String {
        var parts: [String] = []
        if let color = item.colorPrimary {
            var colorText = color
            if let secondary = item.colorSecondary {
                colorText += " / \(secondary)"
            }
            parts.append(colorText)
        }
        if let pattern = item.pattern {
            parts.append(pattern)
        }
        return parts.isEmpty ? item.category : parts.joined(separator: " · ")
    }

    /// Category → garment placeholder tone, matching the categories the
    /// extraction prompt emits (top/bottom/outerwear/shoes/accessory/...).
    private static func tone(for category: String) -> GarmentTone {
        let needle = category.lowercased()
        if needle.contains("top") || needle.contains("shirt") || needle.contains("dress") {
            return .top
        }
        if needle.contains("bottom") || needle.contains("pant") || needle.contains("skirt") {
            return .bottom
        }
        if needle.contains("outer") || needle.contains("jacket") || needle.contains("coat") {
            return .outer
        }
        if needle.contains("shoe") || needle.contains("foot") || needle.contains("sneaker") {
            return .shoes
        }
        return .accent
    }
}

// MARK: - Previews

#if DEBUG
#Preview("Review items") {
    ScrollView {
        ReviewItemsView(
            model: .previewCompleted(
                response: StyleDnaUploadResponse(
                    photosProcessed: 4,
                    photosSkipped: 0,
                    wardrobeItemsSeeded: 4,
                    styleDna: .previewSample,
                    photos: []
                ),
                items: .previewSample
            ),
            onConfirm: {}
        )
        .padding(28)
    }
    .background(Theme.bg)
}
#endif
