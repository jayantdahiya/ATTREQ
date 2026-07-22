//
//  WardrobeItemCard.swift
//  ATTREQ
//
//  Wardrobe grid card (M2, artboard 06). Image tile radius 16 with a status
//  pill for in-flight items, then serif-italic category + mono color label
//  below, per `ATTREQWardrobe` in attreq-app.jsx.
//

import SwiftUI

/// One cell of the two-column wardrobe grid: async thumbnail, processing
/// status pill, serif category, mono color label.
struct WardrobeItemCard: View {
    let item: WardrobeItem
    /// Width/height ratio of the image tile. The screen varies this by index
    /// to echo the design's staggered masonry heights.
    var imageAspectRatio: CGFloat = 0.8

    /// Best available image, resolved against the API origin:
    /// thumbnail → processed → original.
    private var imageURL: URL? {
        AppConfig.absoluteMediaURL(
            item.thumbnailUrl ?? item.processedImageUrl ?? item.originalImageUrl
        )
    }

    private static let tileShape = RoundedRectangle(cornerRadius: 16, style: .continuous)

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            imageTile
            VStack(alignment: .leading, spacing: 1) {
                Text(item.category?.capitalized ?? "Piece")
                    .font(.attreqDisplay(13, weight: .semiBold, italic: true))
                    .foregroundStyle(Theme.text)
                MonoLabel(item.colorPrimary ?? "—")
                    .lineLimit(1)
            }
            .padding(.top, 6)
            .padding(.leading, 1)
        }
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("wardrobe-item-\(item.id)")
    }

    private var imageTile: some View {
        AsyncImage(url: imageURL) { phase in
            switch phase {
            case let .success(image):
                image
                    .resizable()
                    .scaledToFill()
            default:
                // Theme-styled loading/failure placeholder.
                Self.tileShape
                    .fill(Theme.surface)
                    .overlay(Self.tileShape.strokeBorder(Theme.borderSoft, lineWidth: 1))
                    .overlay {
                        if phase.error == nil {
                            ProgressView()
                                .controlSize(.small)
                                .tint(Theme.t3)
                        } else {
                            AttreqIcon.image.view(size: 18, color: Theme.t3)
                        }
                    }
            }
        }
        .aspectRatio(imageAspectRatio, contentMode: .fit)
        .frame(maxWidth: .infinity)
        .clipShape(Self.tileShape)
        .overlay(alignment: .topTrailing) {
            statusPill
                .padding(8)
        }
    }

    @ViewBuilder
    private var statusPill: some View {
        switch item.processingStatus {
        case .pending:
            AttreqPill("Pending", variant: .muted)
        case .processing:
            AttreqPill("Processing", variant: .gold)
        case .failed:
            AttreqPill("Failed", variant: .clay)
        case .completed:
            EmptyView()
        }
    }
}

// MARK: - Previews

#Preview("Card states") {
    let base = WardrobeItem(
        id: "preview-1",
        userId: "u1",
        originalImageUrl: "/uploads/original/preview.jpg",
        processedImageUrl: nil,
        thumbnailUrl: nil,
        category: "top",
        colorPrimary: "Cream Linen",
        colorSecondary: nil,
        pattern: nil,
        season: nil,
        occasion: nil,
        detectionConfidence: 0.92,
        classificationSource: nil,
        processingStatus: .completed,
        wearCount: 0,
        lastWorn: nil,
        createdAt: .now,
        updatedAt: .now
    )
    return ScrollView {
        HStack(alignment: .top, spacing: 10) {
            VStack(spacing: 10) {
                WardrobeItemCard(item: base, imageAspectRatio: 0.77)
                WardrobeItemCard(
                    item: WardrobeItem(
                        id: "preview-2", userId: "u1",
                        originalImageUrl: "/uploads/original/p2.jpg",
                        processedImageUrl: nil, thumbnailUrl: nil,
                        category: nil, colorPrimary: nil, colorSecondary: nil,
                        pattern: nil, season: nil, occasion: nil,
                        detectionConfidence: nil, classificationSource: nil,
                        processingStatus: .processing, wearCount: 0,
                        lastWorn: nil, createdAt: .now, updatedAt: .now
                    ),
                    imageAspectRatio: 0.92
                )
            }
            VStack(spacing: 10) {
                WardrobeItemCard(
                    item: WardrobeItem(
                        id: "preview-3", userId: "u1",
                        originalImageUrl: "/uploads/original/p3.jpg",
                        processedImageUrl: nil, thumbnailUrl: nil,
                        category: "outer", colorPrimary: "Camel Coat",
                        colorSecondary: nil, pattern: nil, season: nil,
                        occasion: nil, detectionConfidence: nil,
                        classificationSource: nil, processingStatus: .failed,
                        wearCount: 0, lastWorn: nil, createdAt: .now, updatedAt: .now
                    ),
                    imageAspectRatio: 0.93
                )
            }
        }
        .padding(24)
    }
    .background(Theme.bg)
}
