import SwiftUI

/// The four root tabs of the app.
enum AttreqTab: CaseIterable {
    case today, wardrobe, history, profile

    var label: String {
        switch self {
        case .today: "TODAY"
        case .wardrobe: "WARDROBE"
        case .history: "HISTORY"
        case .profile: "PROFILE"
        }
    }

    var icon: AttreqIcon {
        switch self {
        case .today: .sun
        case .wardrobe: .shirt
        case .history: .book
        case .profile: .person
        }
    }
}

/// Floating pill tab bar (`ATTREQTabBar` in the design handoff).
///
/// Stateless: the host owns the active tab. Callers overlay this at the bottom
/// of the screen with 16pt horizontal margins and a 20pt bottom inset.
struct AttreqTabBar: View {
    @Environment(\.colorScheme) private var colorScheme

    let active: AttreqTab
    let onSelect: (AttreqTab) -> Void

    init(active: AttreqTab, onSelect: @escaping (AttreqTab) -> Void) {
        self.active = active
        self.onSelect = onSelect
    }

    private static let barShape = RoundedRectangle(cornerRadius: 22, style: .continuous)

    private var isDark: Bool { colorScheme == .dark }

    var body: some View {
        HStack(spacing: 0) {
            ForEach(AttreqTab.allCases, id: \.self) { tab in
                tabItem(tab)
            }
        }
        .padding(.vertical, 4)
        .padding(.horizontal, 4)
        .background {
            // Design: bg at 95% (light) / 96% (dark) opacity over a 20pt backdrop blur.
            Self.barShape
                .fill(.ultraThinMaterial)
                .overlay(Self.barShape.fill(Theme.bg.opacity(isDark ? 0.96 : 0.95)))
        }
        .overlay(Self.barShape.strokeBorder(Theme.border, lineWidth: 1))
        .overlay {
            // Inner top highlight (inset 0 1px 0 white 0.7 light / 0.06 dark in the handoff).
            RoundedRectangle(cornerRadius: 21, style: .continuous)
                .strokeBorder(
                    LinearGradient(
                        colors: [Color.white.opacity(isDark ? 0.06 : 0.7), Color.white.opacity(0)],
                        startPoint: .top,
                        endPoint: .bottom
                    ),
                    lineWidth: 1
                )
                .padding(1)
        }
        .clipShape(Self.barShape)
        .shadow(color: Color.black.opacity(isDark ? 0.30 : 0.08), radius: 16, x: 0, y: 8)
    }

    private func tabItem(_ tab: AttreqTab) -> some View {
        let isActive = tab == active
        return Button {
            onSelect(tab)
        } label: {
            VStack(spacing: 2) {
                tab.icon.view(size: 19, color: isActive ? Theme.text : Theme.t3)
                Text(tab.label)
                    .font(.attreqMono(7))
                    .tracking(0.7)
                    .foregroundStyle(isActive ? Theme.text : Theme.t3)
            }
            .padding(.vertical, 5)
            .padding(.horizontal, 4)
            .background {
                if isActive {
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(Theme.text.opacity(isDark ? 0.08 : 0.07))
                }
            }
            // 44pt minimum tap target: the bar's former 2pt-per-side extra
            // padding lives inside the item's tappable frame instead, so the
            // pill visual and overall bar height are unchanged.
            .frame(maxWidth: .infinity, minHeight: 44)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(tab.label.capitalized)
        .accessibilityAddTraits(isActive ? [.isSelected] : [])
    }
}

#Preview("Tab bar") {
    ZStack(alignment: .bottom) {
        Theme.bg.ignoresSafeArea()
        AttreqTabBar(active: .today) { _ in }
            .padding(.horizontal, 16)
            .padding(.bottom, 20)
    }
}
