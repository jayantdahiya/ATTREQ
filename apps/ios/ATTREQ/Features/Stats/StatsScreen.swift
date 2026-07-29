//
//  StatsScreen.swift
//  ATTREQ
//
//  Stats tab (RI-7, no artboard — composed in the design language, same
//  approach as `ResultsView`/`ReviewItemsView` for M3's un-designed screens).
//  Composition/color/brand breakdowns render as plain SwiftUI proportional
//  bars (Rectangle/Capsule widths) — no charting library, per the RI-7 plan.
//
//  Sections: overview (active items / closet value / never-worn %),
//  composition breakdown, cost-per-wear, most/least worn, and the
//  forgotten-items "wear it with…" surface. Tapping any item pushes
//  `WardrobeItemDetailView` via this screen's own `NavigationStack`.
//

import SwiftUI

struct StatsScreen: View {
    /// Owned by `MainTabsView` so state survives tab switches.
    let viewModel: StatsViewModel
    /// Shared with the Wardrobe tab so item-detail pushes from here use the
    /// same stateless facade instead of constructing a redundant one.
    let wardrobeRepository: WardrobeRepository

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.bg.ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 0) {
                        header
                            .padding(.bottom, 18)

                        statusBanner

                        if let stats = viewModel.wardrobeStats {
                            overviewCard(stats)
                                .padding(.bottom, 18)

                            if stats.itemsMissingPrice > 0 {
                                missingPriceNudge(stats.itemsMissingPrice)
                                    .padding(.bottom, 18)
                            }

                            sectionHeader("Composition")
                            compositionCard(stats)
                                .padding(.bottom, 18)

                            if !stats.costPerWear.isEmpty {
                                sectionHeader("Cost per wear")
                                costPerWearCard(stats)
                                    .padding(.bottom, 18)
                            }

                            if !stats.mostWorn.isEmpty {
                                sectionHeader("Most worn")
                                wornList(stats.mostWorn)
                                    .padding(.bottom, 18)
                            }

                            if !stats.leastWorn.isEmpty {
                                sectionHeader("Least worn")
                                wornList(stats.leastWorn)
                                    .padding(.bottom, 18)
                            }
                        }

                        if let forgotten = viewModel.forgottenItems, !forgotten.items.isEmpty {
                            sectionHeader("Forgotten pieces")
                            forgottenCard(forgotten)
                        }
                    }
                    .padding(.horizontal, 24)
                    .padding(.top, 10)
                    // Clearance for the floating tab bar.
                    .padding(.bottom, 110)
                }
                .refreshable { await viewModel.refresh() }
            }
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(for: String.self) { itemId in
                WardrobeItemDetailView(itemId: itemId, repository: wardrobeRepository)
            }
        }
        .task { await viewModel.load() }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel("Closet")
            Text("Stats")
                .font(.attreqDisplay(28, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.text)
        }
    }

    private func sectionHeader(_ title: String) -> some View {
        MonoLabel(title).padding(.bottom, 8)
    }

    // MARK: - Status / error banner

    @ViewBuilder
    private var statusBanner: some View {
        if case let .failed(message) = viewModel.state {
            VStack(alignment: .leading, spacing: 10) {
                errorBanner(message)
                Button {
                    Task { await viewModel.refresh() }
                } label: {
                    MonoLabel("Retry", size: 10, color: Theme.text)
                        .padding(.vertical, 9)
                        .padding(.horizontal, 18)
                        .overlay(Capsule().strokeBorder(Theme.border, lineWidth: 1))
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("stats-retry")
            }
            .padding(.bottom, 14)
        } else if viewModel.state == .loading, viewModel.wardrobeStats == nil {
            HStack {
                Spacer()
                ProgressView().tint(Theme.t2)
                Spacer()
            }
            .padding(.top, 48)
            .padding(.bottom, 14)
        } else if let message = viewModel.errorMessage {
            errorBanner(message)
                .padding(.bottom, 14)
        }
    }

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    // MARK: - Overview

    private func overviewCard(_ stats: WardrobeStatsResponse) -> some View {
        HStack(alignment: .top, spacing: 24) {
            overviewStat(label: "Active pieces", value: "\(stats.totalActiveItems)")
            overviewStat(label: "Closet value", value: Self.currency(stats.closetValue))
            overviewStat(
                label: "Never worn",
                value: "\(Int(stats.neverWornPercent.rounded()))%",
                accent: stats.neverWornPercent >= 25
            )
        }
        .padding(.vertical, 18)
        .padding(.horizontal, 20)
        .attreqCard(padding: 0)
    }

    private func overviewStat(label: String, value: String, accent: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            MonoLabel(label)
            Text(value)
                .font(.attreqDisplay(20, italic: true))
                .foregroundStyle(accent ? Theme.clay : Theme.text)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func missingPriceNudge(_ count: Int) -> some View {
        HStack(spacing: 10) {
            AttreqIcon.sparkles.view(size: 14, color: Theme.accent)
            BodyText(
                "\(count) piece\(count == 1 ? "" : "s") missing a price — add one from the item's detail screen to see its cost per wear.",
                size: 12.5,
                color: Theme.text
            )
        }
        .padding(12)
        .background(Theme.accentSoft, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    // MARK: - Composition

    private func compositionCard(_ stats: WardrobeStatsResponse) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            if !stats.byCategory.isEmpty {
                barGroup(
                    title: "By category",
                    entries: stats.byCategory.map { ($0.category.capitalized, $0.count) }
                )
            }
            if !stats.byColorFamily.isEmpty {
                if !stats.byCategory.isEmpty { divider }
                barGroup(
                    title: "By color family",
                    entries: stats.byColorFamily.map { ($0.family.capitalized, $0.count) }
                )
            }
            if !stats.byBrand.isEmpty {
                if !stats.byCategory.isEmpty || !stats.byColorFamily.isEmpty { divider }
                barGroup(title: "By brand", entries: stats.byBrand.map { ($0.brand, $0.count) })
            }
        }
        .attreqCard(padding: 16)
    }

    private var divider: some View {
        Rectangle().fill(Theme.borderSoft).frame(height: 1)
    }

    /// Proportional bars (no charting library): each row's fill width is
    /// `count / maxCount` of the row's available width.
    private func barGroup(title: String, entries: [(label: String, count: Int)]) -> some View {
        let maxCount = max(entries.map(\.count).max() ?? 1, 1)
        return VStack(alignment: .leading, spacing: 9) {
            MonoLabel(title, size: 8.5)
            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(entries.enumerated()), id: \.offset) { _, entry in
                    barRow(label: entry.label, count: entry.count, maxCount: maxCount)
                }
            }
        }
    }

    private func barRow(label: String, count: Int, maxCount: Int) -> some View {
        let fraction = CGFloat(count) / CGFloat(maxCount)
        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label)
                    .font(.attreqBody(12.5, weight: .medium))
                    .foregroundStyle(Theme.text)
                    .lineLimit(1)
                Spacer(minLength: 8)
                MonoLabel("\(count)", size: 9)
            }
            GeometryReader { geometry in
                Capsule()
                    .fill(Theme.borderSoft)
                    .overlay(alignment: .leading) {
                        Capsule()
                            .fill(Theme.accent)
                            .frame(width: max(4, geometry.size.width * fraction))
                    }
            }
            .frame(height: 6)
        }
    }

    // MARK: - Cost per wear

    private func costPerWearCard(_ stats: WardrobeStatsResponse) -> some View {
        VStack(spacing: 0) {
            ForEach(Array(stats.costPerWear.enumerated()), id: \.element.itemId) { index, entry in
                if index > 0 { divider }
                NavigationLink(value: entry.itemId) {
                    costPerWearRow(entry)
                }
                .buttonStyle(.plain)
            }
        }
        .attreqCard(padding: 12)
    }

    private func costPerWearRow(_ entry: CostPerWearEntry) -> some View {
        HStack(spacing: 12) {
            thumbnail(entry.thumbnailUrl, category: entry.category)
            VStack(alignment: .leading, spacing: 2) {
                Text(itemTitle(category: entry.category, color: entry.colorPrimary))
                    .font(.attreqBody(13.5, weight: .medium))
                    .foregroundStyle(Theme.text)
                    .lineLimit(1)
                MonoLabel("\(Self.currency(entry.purchasePrice)) · worn in \(entry.wearCount) outfit\(entry.wearCount == 1 ? "" : "s")", size: 8.5)
            }
            Spacer(minLength: 8)
            if let costPerWear = entry.costPerWear {
                Text(Self.currency(costPerWear))
                    .font(.attreqDisplay(15, italic: true))
                    .foregroundStyle(Theme.accent)
            } else {
                AttreqPill("Not worn yet", variant: .muted)
            }
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle())
    }

    // MARK: - Most / least worn

    private func wornList(_ entries: [WornItemEntry]) -> some View {
        VStack(spacing: 0) {
            ForEach(Array(entries.enumerated()), id: \.element.itemId) { index, entry in
                if index > 0 { divider }
                NavigationLink(value: entry.itemId) {
                    wornRow(entry)
                }
                .buttonStyle(.plain)
            }
        }
        .attreqCard(padding: 12)
    }

    private func wornRow(_ entry: WornItemEntry) -> some View {
        HStack(spacing: 12) {
            thumbnail(entry.thumbnailUrl, category: entry.category)
            VStack(alignment: .leading, spacing: 2) {
                Text(itemTitle(category: entry.category, color: entry.colorPrimary))
                    .font(.attreqBody(13.5, weight: .medium))
                    .foregroundStyle(Theme.text)
                    .lineLimit(1)
                MonoLabel(entry.lastWorn.map { "Last worn \($0)" } ?? "Not worn yet", size: 8.5)
            }
            Spacer(minLength: 8)
            AttreqPill("\(entry.wearCount) outfit\(entry.wearCount == 1 ? "" : "s")", variant: .gold)
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle())
    }

    // MARK: - Forgotten items

    private func forgottenCard(_ forgotten: ForgottenItemsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            BodyText("Pieces you own but haven't reached for lately.", size: 12.5)
            VStack(spacing: 0) {
                ForEach(Array(forgotten.items.enumerated()), id: \.element.itemId) { index, entry in
                    if index > 0 { divider }
                    forgottenRow(entry)
                }
            }
        }
        .attreqCard(padding: 16)
    }

    private func forgottenRow(_ entry: ForgottenItemEntry) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            NavigationLink(value: entry.itemId) {
                HStack(spacing: 12) {
                    thumbnail(entry.thumbnailUrl, category: entry.category)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(itemTitle(category: entry.category, color: entry.colorPrimary))
                            .font(.attreqBody(13.5, weight: .medium))
                            .foregroundStyle(Theme.text)
                            .lineLimit(1)
                        MonoLabel(forgottenSubtitle(entry), size: 8.5)
                    }
                    Spacer(minLength: 8)
                    AttreqIcon.chevron.view(size: 12, color: Theme.t3)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            if let partner = entry.bestPartner {
                NavigationLink(value: partner.itemId) {
                    HStack(spacing: 8) {
                        MonoLabel("Wear it with", size: 8)
                        thumbnail(partner.thumbnailUrl, category: partner.category, size: 32)
                        Text(itemTitle(category: partner.category, color: partner.colorPrimary))
                            .font(.attreqBody(12))
                            .foregroundStyle(Theme.t2)
                            .lineLimit(1)
                        Spacer(minLength: 8)
                    }
                }
                .buttonStyle(.plain)
                .padding(.leading, 8)
            }
            // `bestPartner == nil` (no good pairing candidate found): the row
            // simply omits the partner suggestion — no placeholder shown.
        }
        .padding(.vertical, 10)
    }

    private func forgottenSubtitle(_ entry: ForgottenItemEntry) -> String {
        if entry.wearCount == 0 {
            return "Never worn"
        }
        if let days = entry.daysSinceWorn {
            return "Not worn in \(days) day\(days == 1 ? "" : "s")"
        }
        return "Worn in \(entry.wearCount) outfit\(entry.wearCount == 1 ? "" : "s")"
    }

    // MARK: - Shared row pieces

    private func thumbnail(_ url: String?, category: String?, size: CGFloat = 46) -> some View {
        let shape = RoundedRectangle(cornerRadius: 10, style: .continuous)
        return Group {
            if let url, let resolved = AppConfig.absoluteMediaURL(url) {
                AsyncImage(url: resolved) { phase in
                    if case let .success(image) = phase {
                        image.resizable().scaledToFill()
                    } else {
                        GarmentPlaceholder(tone: Self.tone(for: category), cornerRadius: 10)
                    }
                }
            } else {
                GarmentPlaceholder(tone: Self.tone(for: category), cornerRadius: 10)
            }
        }
        .frame(width: size, height: size * 1.25)
        .clipShape(shape)
        .overlay(shape.strokeBorder(Theme.borderSoft, lineWidth: 1))
    }

    private func itemTitle(category: String?, color: String?) -> String {
        let name = category?.capitalized ?? "Piece"
        guard let color, !color.isEmpty else { return name }
        return "\(color.capitalized) \(name)"
    }

    /// `WardrobeFilter.bucket(for:)` never returns `.all` (it's a bucket
    /// classifier, not a filter selection), so every case maps to a real tone.
    private static func tone(for category: String?) -> GarmentTone {
        switch WardrobeFilter.bucket(for: category) {
        case .all, .tops: .top
        case .bottoms: .bottom
        case .outer: .outer
        case .accents: .accent
        case .shoes: .shoes
        }
    }

    private static func currency(_ value: Double) -> String {
        "$" + String(format: "%.2f", value)
    }
}

// MARK: - Previews

#Preview("Stats") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    StatsScreen(
        viewModel: StatsViewModel(repository: StatsRepository(apiClient: client)),
        wardrobeRepository: WardrobeRepository(apiClient: client)
    )
}
