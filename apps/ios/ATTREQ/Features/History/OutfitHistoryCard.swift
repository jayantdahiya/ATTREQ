//
//  OutfitHistoryCard.swift
//  ATTREQ
//
//  History look card (M4, artboard 07). Pixel source:
//  assets/design/ios-redesign-v2/attreq-app.jsx → ATTREQHistory outfit card:
//  attreqCard 11v/14h, three 34×50 garment tiles (radius 9, gap 3), italic
//  display 15 title + mono "N pieces", trailing status pill.
//
//  Takes primitives (not `HistoryEntry`) so the card stays previewable and
//  decoupled from the view-model layer; `HistoryScreen` does the mapping.
//

import SwiftUI

struct OutfitHistoryCard: View {
    let outfitID: String
    let title: String
    let piecesCount: Int
    let pillLabel: String
    let pillVariant: PillVariant

    /// The design (and RN `HistoryLookCard`) always shows the top/bottom/accent
    /// trio — `Outfit` carries only item ids, so gradient placeholders stand in
    /// for real thumbnails.
    private static let tileTones: [GarmentTone] = [.top, .bottom, .accent]

    var body: some View {
        HStack(spacing: 10) {
            HStack(spacing: 3) {
                ForEach(Self.tileTones, id: \.self) { tone in
                    GarmentPlaceholder(tone: tone, cornerRadius: 9)
                        .frame(width: 34, height: 50)
                }
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.attreqDisplay(15, weight: .semiBold, italic: true))
                    .foregroundStyle(Theme.text)
                    .lineLimit(1)
                MonoLabel("\(piecesCount) \(piecesCount == 1 ? "piece" : "pieces")")
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            AttreqPill(pillLabel, variant: pillVariant)
        }
        .padding(.vertical, 11)
        .padding(.horizontal, 14)
        .attreqCard(padding: 0)
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("history-entry-\(outfitID)")
    }
}

// MARK: - Previews

#Preview("History cards") {
    VStack(spacing: 8) {
        OutfitHistoryCard(
            outfitID: "1", title: "The Long Walk", piecesCount: 3,
            pillLabel: "Worn", pillVariant: .moss
        )
        OutfitHistoryCard(
            outfitID: "2", title: "Casual Friday", piecesCount: 3,
            pillLabel: "Loved", pillVariant: .gold
        )
        OutfitHistoryCard(
            outfitID: "3", title: "Morning Run", piecesCount: 2,
            pillLabel: "Skipped", pillVariant: .clay
        )
        OutfitHistoryCard(
            outfitID: "4", title: "Saved outfit", piecesCount: 1,
            pillLabel: "Tracked", pillVariant: .muted
        )
    }
    .padding(24)
    .background(Theme.bg)
}
