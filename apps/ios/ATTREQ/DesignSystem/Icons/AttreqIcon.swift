import SwiftUI

/// Design-system icon set, mapped from the 16 handoff SVGs in
/// `assets/design/ios-redesign-v2/attreq-shared.jsx` to the closest SF Symbols.
///
/// The handoff icons are 24x24 feather-style strokes (1.5px default; chevrons 1.8,
/// back 2.0, check 2.2). Symbol weights below approximate those stroke widths.
/// The raw value is the SF Symbol name.
enum AttreqIcon: String, CaseIterable {
    case sun = "sun.max"
    case shirt = "tshirt"
    case book = "book.closed"
    case person = "person"
    case camera = "camera"
    case image = "photo"
    case location = "mappin.and.ellipse"
    case search = "magnifyingglass"
    case bell = "bell"
    case chevron = "chevron.right"
    case sparkles = "sparkles"
    case back = "chevron.left"
    case check = "checkmark"
    case heart = "heart"
    case menu = "line.3.horizontal"
    case x = "xmark"

    /// Approximates the per-icon stroke width from the handoff SVGs.
    private var symbolWeight: Font.Weight {
        switch self {
        case .chevron, .x:
            .regular // 1.8px stroke
        case .back:
            .medium // 2.0px stroke
        case .check:
            .semibold // 2.2px stroke
        default:
            .light // 1.5px stroke
        }
    }

    /// Renders the icon inside a `size` x `size` box, tinted with `color`.
    ///
    /// Design-system icons are deliberately **fixed-metric**: sizes come from
    /// the handoff's pixel values and do NOT scale with Dynamic Type, matching
    /// the design's fixed icon boxes even next to text that does scale.
    /// (`AttreqPrimaryButton` pins its `systemImage` the same way.)
    func view(size: CGFloat = 20, color: Color = Theme.t3) -> some View {
        Image(systemName: rawValue)
            .font(.system(size: size * 0.85, weight: symbolWeight))
            .foregroundStyle(color)
            .frame(width: size, height: size)
    }
}

#Preview("Icon set") {
    LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 20) {
        ForEach(AttreqIcon.allCases, id: \.self) { icon in
            VStack(spacing: 6) {
                icon.view()
                Text(String(describing: icon))
                    .font(.attreqMono(8))
                    .foregroundStyle(Theme.t2)
            }
        }
    }
    .padding(24)
    .background(Theme.bg)
}
