import SwiftUI

/// M0 proof screen: renders every piece of the ATTREQ design system on one
/// scrollable page, with the floating tab bar overlaid at the bottom.
struct ComponentGalleryView: View {
    @State private var email = "hi@natasha.com"
    @State private var password = "hunter2secret"
    @State private var selectedChips: Set<String> = ["Minimal", "Earthy", "Layered"]
    @State private var activeTab: AttreqTab = .today
    @State private var galleryStep = 1

    private let chipOptions = ["Minimal", "Earthy", "Tailored", "Layered", "Casual", "Formal", "Streetwear", "Athleisure"]

    var body: some View {
        ZStack(alignment: .bottom) {
            Theme.bg.ignoresSafeArea()

            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 40) {
                        header
                        typographySection
                        colorSection
                        buttonSection
                        inputSection
                        chipSection
                        pillSection
                        garmentSection
                        iconSection
                        stepNavSection
                    }
                    .padding(.horizontal, 24)
                    .padding(.top, 16)
                    .padding(.bottom, 120) // keep content clear of the floating tab bar
                    .id("gallery-content")
                }
                .task {
                    // Screenshot-verification hook: `simctl launch ... -scroll-bottom`
                    guard CommandLine.arguments.contains("-scroll-bottom") else { return }
                    try? await Task.sleep(for: .seconds(1))
                    proxy.scrollTo("gallery-content", anchor: .bottom)
                }
            }

            AttreqTabBar(active: activeTab) { activeTab = $0 }
                .padding(.horizontal, 16)
                .padding(.bottom, 20)
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            MonoLabel("ATTREQ — Design System")
            Text("Component Gallery")
                .font(.attreqDisplay(34))
                .foregroundStyle(Theme.text)
            Text("Every token, rendered.")
                .font(.attreqDisplay(19, weight: .regular, italic: true))
                .foregroundStyle(Theme.t2)
        }
    }

    // MARK: - Sections

    private var typographySection: some View {
        section("01 — Type Ramp") {
            VStack(alignment: .leading, spacing: 12) {
                Text("Your closet, curated.")
                    .font(.attreqDisplay(36))
                    .foregroundStyle(Theme.text)
                Text("Define your aesthetic.")
                    .font(.attreqDisplay(24, weight: .medium, italic: true))
                    .foregroundStyle(Theme.accent)
                Text("Display — Cormorant Garamond, regular")
                    .font(.attreqDisplay(18, weight: .regular))
                    .foregroundStyle(Theme.text)
                BodyText("Body — DM Sans regular at 14pt. A few details, then we'll curate every look.")
                Text("Body — DM Sans semibold at 14pt.")
                    .font(.attreqBody(14, weight: .semiBold))
                    .foregroundStyle(Theme.text)
                Text("Body — DM Sans light at 14pt.")
                    .font(.attreqBody(14, weight: .light))
                    .foregroundStyle(Theme.t2)
                MonoLabel("Mono label — IBM Plex Mono 9.5")
                Text("Mono 11 — est. 2026, medium")
                    .font(.attreqMono(11, weight: .medium))
                    .foregroundStyle(Theme.t2)
            }
        }
    }

    private var colorSection: some View {
        section("02 — Color Tokens") {
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 4), spacing: 14) {
                swatch("bg", Theme.bg)
                swatch("surface", Theme.surface)
                swatch("deep", Theme.deep)
                swatch("text", Theme.text)
                swatch("t2", Theme.t2)
                swatch("t3", Theme.t3)
                swatch("accent", Theme.accent)
                swatch("accentSoft", Theme.accentSoft)
                swatch("clay", Theme.clay)
                swatch("claySoft", Theme.claySoft)
                swatch("moss", Theme.moss)
                swatch("mossSoft", Theme.mossSoft)
                swatch("border", Theme.border)
                swatch("borderSoft", Theme.borderSoft)
            }
        }
    }

    private var buttonSection: some View {
        section("03 — Buttons") {
            VStack(spacing: 12) {
                AttreqPrimaryButton("Sign in") {}
                AttreqPrimaryButton("Create account", role: .accent, systemImage: "arrow.right") {}
                AttreqPrimaryButton("Curating…", isLoading: true) {}
            }
        }
    }

    private var inputSection: some View {
        section("04 — Inputs, on Card") {
            VStack(spacing: 20) {
                AttreqUnderlineInput(label: "Email address", text: $email)
                AttreqUnderlineInput(label: "Password", text: $password, isSecure: true)
            }
            .attreqCard(padding: 22)
        }
    }

    private var chipSection: some View {
        section("05 — Chips") {
            VStack(alignment: .leading, spacing: 8) {
                chipRow(Array(chipOptions.prefix(4)))
                chipRow(Array(chipOptions.suffix(4)))
            }
        }
    }

    private var pillSection: some View {
        section("06 — Pills") {
            HStack(spacing: 8) {
                AttreqPill("Muted")
                AttreqPill("Golden hour", variant: .gold)
                AttreqPill("Fresh", variant: .moss)
                AttreqPill("In laundry", variant: .clay)
            }
        }
    }

    private var garmentSection: some View {
        section("07 — Garment Tones") {
            HStack(spacing: 8) {
                ForEach(GarmentTone.allCases, id: \.self) { tone in
                    GarmentPlaceholder(tone: tone, label: String(describing: tone))
                        .frame(height: 96)
                }
            }
        }
    }

    private var iconSection: some View {
        section("08 — Icons") {
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 4), spacing: 18) {
                ForEach(AttreqIcon.allCases, id: \.self) { icon in
                    VStack(spacing: 6) {
                        icon.view(size: 20, color: Theme.t2)
                        MonoLabel(String(describing: icon), size: 7.5)
                    }
                }
            }
        }
    }

    private var stepNavSection: some View {
        section("09 — Step Nav") {
            AttreqStepNav(step: galleryStep) {
                galleryStep = max(0, galleryStep - 1)
            }
        }
    }

    // MARK: - Helpers

    private func section(_ title: String, @ViewBuilder content: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            MonoLabel(title)
            content()
        }
    }

    private func swatch(_ name: String, _ color: Color) -> some View {
        VStack(spacing: 5) {
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .fill(color)
                .frame(height: 44)
                .overlay {
                    RoundedRectangle(cornerRadius: 10, style: .continuous)
                        .strokeBorder(Theme.border, lineWidth: 1)
                }
            MonoLabel(name, size: 7.5)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
    }

    private func chipRow(_ options: [String]) -> some View {
        HStack(spacing: 7) {
            ForEach(options, id: \.self) { option in
                AttreqChip(option, selected: selectedChips.contains(option)) {
                    if selectedChips.contains(option) {
                        selectedChips.remove(option)
                    } else {
                        selectedChips.insert(option)
                    }
                }
            }
        }
    }
}

#Preview("Gallery — light") {
    ComponentGalleryView()
}

#Preview("Gallery — dark") {
    ComponentGalleryView()
        .preferredColorScheme(.dark)
}
