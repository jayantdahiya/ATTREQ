//
//  HowRecommendationsWorkView.swift
//  ATTREQ
//
//  "Trust screen" (RI-7) — static, no network calls. Explains in plain
//  language: recommendations only ever come from the user's own wardrobe
//  (never ads/affiliate items), what the per-recommendation explanation line
//  is for (RI-4 hasn't shipped the actual reasoning engine yet, so this
//  deliberately describes intent rather than specific mechanics that don't
//  exist), and how liking/disliking/wearing outfits feeds back into future
//  picks (this part IS real — `POST /outfits/{id}/feedback` and
//  `POST /outfits/{id}/wear` already feed the recommendation algorithm).
//
//  Shown once automatically post-onboarding (see `TrustScreenAutoShow`,
//  wired from `MainTabsView`), and reachable anytime from a Profile row.
//

import SwiftUI

/// Persisted "have I auto-shown this" flag. No `@AppStorage` idiom existed
/// anywhere in the codebase yet (grepped before adding this) — the closest
/// precedent is `ReminderScheduler`'s raw `UserDefaults` key/flag pattern,
/// which this mirrors for consistency rather than introducing a second idiom.
enum TrustScreenAutoShow {
    private static let defaultsKey = "attreq.hasShownHowRecommendationsWork"

    /// Whether the automatic post-onboarding presentation has already fired
    /// (on this device — device-global like the reminder flag, not per-account).
    static func hasShown(in defaults: UserDefaults = .standard) -> Bool {
        defaults.bool(forKey: defaultsKey)
    }

    /// Marks the automatic presentation as done so it never reappears
    /// unprompted again; the Profile row remains reachable regardless.
    static func markShown(in defaults: UserDefaults = .standard) {
        defaults.set(true, forKey: defaultsKey)
    }
}

struct HowRecommendationsWorkView: View {
    /// `nil` when pushed via `NavigationLink`/`navigationDestination` (Profile
    /// row); set when presented as a sheet (the automatic post-onboarding
    /// moment), so that path gets its own dismiss control instead of relying
    /// on a navigation bar back button.
    var onDismiss: (() -> Void)?

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    header
                        .padding(.bottom, 22)

                    section(
                        icon: .shirt,
                        title: "Only your own clothes",
                        body: "Every recommendation is built from pieces already in your wardrobe. We never suggest anything to buy, and nothing here is sponsored, an ad, or an affiliate link — if it's in your closet, it's fair game; if it isn't, it never shows up."
                    )
                    .padding(.bottom, 18)

                    section(
                        icon: .sparkles,
                        title: "\"Why we picked this\"",
                        body: "Under each outfit you'll see a short line explaining the thinking behind it. That reasoning is still getting richer — today it reflects things like color and formality matching your occasion; over time it will speak more specifically to your taste as that part of ATTREQ matures."
                    )
                    .padding(.bottom, 18)

                    section(
                        icon: .heart,
                        title: "Your feedback trains it",
                        body: "Loving, skipping, or wearing an outfit isn't just for your own history — each one quietly adjusts what gets suggested next. Wear something often and you'll see more like it; skip something and ATTREQ leans away from it."
                    )
                    .padding(.bottom, 28)

                    if let onDismiss {
                        AttreqPrimaryButton("Got it", action: onDismiss)
                            .accessibilityIdentifier("button-dismiss-trust-screen")
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 10)
                .padding(.bottom, 40)
            }
        }
        .navigationTitle("How recommendations work")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel("Trust")
            Text("How this\nworks.")
                .font(.attreqDisplay(30, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.text)
        }
    }

    private func section(icon: AttreqIcon, title: String, body text: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Circle()
                    .fill(Theme.accentSoft)
                    .frame(width: 30, height: 30)
                    .overlay(icon.view(size: 14, color: Theme.accent))
                Text(title)
                    .font(.attreqDisplay(18, italic: true))
                    .foregroundStyle(Theme.text)
            }
            BodyText(text, size: 13.5)
        }
        .padding(16)
        .attreqCard(padding: 0)
    }
}

// MARK: - Previews

#Preview("Pushed from Profile") {
    NavigationStack {
        HowRecommendationsWorkView()
    }
}

#Preview("Auto-shown sheet") {
    Color.clear
        .sheet(isPresented: .constant(true)) {
            NavigationStack {
                HowRecommendationsWorkView(onDismiss: {})
            }
        }
}
