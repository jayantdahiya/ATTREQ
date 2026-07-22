//
//  ProfileScreen.swift
//  ATTREQ
//
//  Profile tab (M5-WP1, artboard 08). Pixel source:
//  assets/design/ios-redesign-v2/attreq-app.jsx → ATTREQProfile.
//  Header "You / *Profile*"; identity card with 3pt accent leading border
//  (50pt accent circle w/ serif-italic initials, display-20 name, 13pt email,
//  hairline, Pieces / Worn / Streak stats at gap 28); "Style DNA" row card
//  pushing StyleDnaProfileView; "Preferences" card (location edit sheet,
//  daily-reminder moss toggle, style-preferences edit sheet); centered clay
//  "Sign out" + version footer.
//
//  Identity comes from `AppSession.authState`; the stats row is driven by
//  `ProfileViewModel` (owned by `MainTabsView`, like the other tab models).
//
//  NOTE the style-preferences row: the backend `users.style_preferences`
//  column is DNA-OWNED (holds the Style DNA JSON, returned verbatim by
//  `GET /users/me`) and does NOT round-trip a chip string — a JSON value is
//  shown as "Not set" via `StylePreferencesValue`; see
//  StylePreferencesSheet.swift for the full ownership note.
//

import SwiftUI
import UserNotifications

struct ProfileScreen: View {
    @Environment(AppSession.self) private var session

    /// Owned by `MainTabsView` so stats survive tab switches.
    let viewModel: ProfileViewModel

    @State private var scheduler = ReminderScheduler()
    @State private var reminderEnabled = false
    /// Inline clay hint under the reminder row when permission is denied.
    @State private var reminderHint: String?
    /// True while an async reminder action is in flight (toggle disabled).
    @State private var isReminderBusy = false
    /// Monotonic action token: an `enable()` completion only applies when its
    /// token is still current; otherwise it was superseded (newer toggle or
    /// the Settings-revocation reconciliation) and is reconciled by disabling.
    @State private var reminderActionToken = 0

    @State private var showStyleDna = false
    @State private var showLocationSheet = false
    @State private var showStyleSheet = false
    @State private var isLoggingOut = false
    /// "How recommendations work" trust screen (RI-7) — pushed here manually;
    /// also shown once automatically post-onboarding from `MainTabsView`.
    @State private var showTrustScreen = false

    private var user: User? {
        if case let .authenticated(user) = session.authState { return user }
        return nil
    }

    var body: some View {
        // Own NavigationStack (like LoginView) so the Style DNA row can push
        // StyleDnaProfileView without involving the tab shell.
        NavigationStack {
            ZStack {
                Theme.bg.ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 0) {
                        header
                            .padding(.bottom, 18)

                        statsBanner

                        identityCard
                            .padding(.bottom, 18)

                        MonoLabel("Style DNA")
                            .padding(.bottom, 8)
                        styleDnaCard
                            .padding(.bottom, 18)

                        MonoLabel("Preferences")
                            .padding(.bottom, 8)
                        preferencesCard
                            .padding(.bottom, 18)

                        trustCard
                            .padding(.bottom, 18)

                        footer
                    }
                    .padding(.horizontal, 24)
                    .padding(.top, 10)
                    // Clearance for the floating tab bar.
                    .padding(.bottom, 110)
                }
                .refreshable { await viewModel.refresh() }
            }
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(isPresented: $showStyleDna) {
                StyleDnaProfileView()
            }
            .navigationDestination(isPresented: $showTrustScreen) {
                HowRecommendationsWorkView()
            }
        }
        .task {
            // Reconcile against the system: the user may have revoked
            // notification permission in Settings since we last persisted.
            reminderEnabled = await scheduler.reconciledEnabled()
            if scheduler.isEnabled == false, reminderEnabled == false {
                reminderHint = nil
            }
            await viewModel.load()
        }
        .sheet(isPresented: $showLocationSheet) {
            LocationEditSheet(initialCity: user?.savedCity ?? user?.location ?? "")
        }
        .sheet(isPresented: $showStyleSheet) {
            StylePreferencesSheet(current: user?.stylePreferences)
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel("You")
            Text("Profile")
                .font(.attreqDisplay(28, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.text)
        }
    }

    // MARK: - Stats error banner

    /// Initial-load failure gets a banner + retry; refresh-over-content
    /// failure keeps the stale numbers but surfaces the same banner.
    @ViewBuilder
    private var statsBanner: some View {
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
                        .contentShape(Capsule())
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("profile-stats-retry")
            }
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

    // MARK: - Identity card

    private var identityCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 14) {
                initialsCircle

                VStack(alignment: .leading, spacing: 2) {
                    Text(displayName)
                        .font(.attreqDisplay(20))
                        .foregroundStyle(Theme.text)
                        .lineLimit(1)
                    BodyText(user?.email ?? "", size: 13)
                        .lineLimit(1)
                }
            }
            .padding(.bottom, 14)

            Rectangle()
                .fill(Theme.borderSoft)
                .frame(height: 1)
                .padding(.bottom, 14)

            HStack(alignment: .top, spacing: 28) {
                stat(label: "Pieces", value: viewModel.stats.map { String($0.pieces) })
                stat(label: "Worn", value: viewModel.stats.map { String($0.worn) })
                stat(
                    label: "Streak",
                    value: viewModel.stats.map { "\($0.streakDays)d" },
                    accent: true
                )
            }
        }
        .padding(.vertical, 18)
        .padding(.horizontal, 20)
        .attreqCard(padding: 0)
        // 3pt accent leading border, masked to the card's rounded shape so
        // the bar follows the corner radius instead of poking past it.
        .overlay {
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(Theme.accent)
                .mask(alignment: .leading) {
                    Rectangle().frame(width: 3)
                }
                .allowsHitTesting(false)
        }
    }

    private var initialsCircle: some View {
        Circle()
            .fill(Theme.accent)
            .frame(width: 50, height: 50)
            .overlay {
                Text(initials)
                    .font(.attreqDisplay(19, italic: true))
                    .foregroundStyle(Theme.bg)
            }
            .accessibilityHidden(true)
    }

    private func stat(label: String, value: String?, accent: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            MonoLabel(label)
            Text(value ?? "—")
                .font(.attreqDisplay(22, italic: true))
                .foregroundStyle(accent ? Theme.accent : Theme.text)
                .redacted(reason: value == nil ? .placeholder : [])
        }
        .accessibilityElement(children: .combine)
    }

    /// First letters of the first two words of `fullName`; falls back to the
    /// email's first letter.
    private var initials: String {
        let nameParts = (user?.fullName ?? "")
            .split(whereSeparator: \.isWhitespace)
            .prefix(2)
        let letters = nameParts.compactMap(\.first).map(String.init).joined().uppercased()
        if !letters.isEmpty { return letters }
        if let first = user?.email.first { return String(first).uppercased() }
        return "A"
    }

    /// Full name, falling back to the email's local part.
    private var displayName: String {
        let trimmed = (user?.fullName ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty { return trimmed }
        if let email = user?.email, let local = email.split(separator: "@").first {
            return String(local)
        }
        return "ATTREQ user"
    }

    // MARK: - Style DNA row

    private var styleDnaCard: some View {
        Button {
            showStyleDna = true
        } label: {
            HStack(spacing: 12) {
                AttreqIcon.sparkles.view(size: 15, color: Theme.t2)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Your Style DNA")
                        .font(.attreqBody(14))
                        .foregroundStyle(Theme.text)
                    MonoLabel("Tap to view or edit")
                }

                Spacer(minLength: 8)

                AttreqIcon.chevron.view(size: 13, color: Theme.t3)
            }
            .padding(.vertical, 13)
            .padding(.horizontal, 16)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .attreqCard(padding: 0)
        .accessibilityIdentifier("row-style-dna")
    }

    // MARK: - Trust row (RI-7)

    private var trustCard: some View {
        Button {
            showTrustScreen = true
        } label: {
            HStack(spacing: 12) {
                AttreqIcon.heart.view(size: 15, color: Theme.t2)

                VStack(alignment: .leading, spacing: 2) {
                    Text("How recommendations work")
                        .font(.attreqBody(14))
                        .foregroundStyle(Theme.text)
                    MonoLabel("Only your wardrobe — never ads")
                }

                Spacer(minLength: 8)

                AttreqIcon.chevron.view(size: 13, color: Theme.t3)
            }
            .padding(.vertical, 13)
            .padding(.horizontal, 16)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .attreqCard(padding: 0)
        .accessibilityIdentifier("row-how-recommendations-work")
    }

    // MARK: - Preferences card

    private var preferencesCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            locationRow
            divider
            reminderRow
            divider
            stylePreferencesRow
        }
        .attreqCard(padding: 0)
    }

    private var divider: some View {
        Rectangle()
            .fill(Theme.borderSoft)
            .frame(height: 1)
    }

    private var hasCoordinates: Bool {
        user?.savedLatitude != nil && user?.savedLongitude != nil
    }

    private var locationRow: some View {
        Button {
            showLocationSheet = true
        } label: {
            preferenceRowLabel(
                icon: .location,
                label: user?.savedCity ?? user?.location ?? "Set your location",
                sub: hasCoordinates ? "Coordinates saved" : "For weather-aware suggestions"
            ) {
                MonoLabel("Edit", color: Theme.accent)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("row-location")
    }

    private var reminderRow: some View {
        preferenceRowLabel(
            icon: .bell,
            label: "Daily reminder",
            sub: "8:00 AM — every day",
            hint: reminderHint
        ) {
            MossToggle(isOn: reminderEnabled, isBusy: isReminderBusy, action: toggleReminder)
                .accessibilityIdentifier("toggle-daily-reminder")
        }
    }

    private var stylePreferencesRow: some View {
        Button {
            showStyleSheet = true
        } label: {
            preferenceRowLabel(
                icon: .sparkles,
                label: "Style preferences",
                sub: StylePreferencesValue.parse(user?.stylePreferences).displayString
            ) {
                MonoLabel("Edit", color: Theme.accent)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("row-style-preferences")
    }

    private func preferenceRowLabel(
        icon: AttreqIcon,
        label: String,
        sub: String,
        hint: String? = nil,
        @ViewBuilder trailing: () -> some View
    ) -> some View {
        HStack(alignment: .center, spacing: 12) {
            icon.view(size: 15, color: Theme.t2)

            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.attreqBody(13))
                    .foregroundStyle(Theme.text)
                    .lineLimit(1)
                MonoLabel(sub)
                    .lineLimit(1)
                if let hint {
                    BodyText(hint, size: 12, color: Theme.clay)
                        .padding(.top, 4)
                }
            }

            Spacer(minLength: 8)

            trailing()
        }
        .padding(.vertical, 12)
        .padding(.horizontal, 16)
    }

    private func toggleReminder() {
        guard !isReminderBusy else { return }
        let turningOn = !reminderEnabled
        reminderHint = nil
        reminderEnabled = turningOn
        reminderActionToken += 1
        let token = reminderActionToken

        if turningOn {
            isReminderBusy = true
            Task {
                let enabled = await scheduler.enable()
                isReminderBusy = false
                // A newer toggle (or reconciliation) superseded this action:
                // don't clobber the user's latest intent — reconcile instead.
                guard token == reminderActionToken else {
                    if !reminderEnabled { scheduler.disable() }
                    return
                }
                reminderEnabled = enabled
                if !enabled {
                    // Permission denied (or scheduling failed): flip back + hint.
                    reminderHint = "Notifications are off for ATTREQ. Allow them in Settings to get the reminder."
                }
            }
        } else {
            scheduler.disable()
        }
    }

    // MARK: - Sign out + footer

    private var footer: some View {
        VStack(spacing: 7) {
            Button {
                guard !isLoggingOut else { return }
                isLoggingOut = true
                Task {
                    await session.logout()
                    isLoggingOut = false
                }
            } label: {
                Group {
                    if isLoggingOut {
                        ProgressView()
                            .controlSize(.small)
                            .tint(Theme.clay)
                    } else {
                        MonoLabel("Sign out", size: 10, color: Theme.clay)
                    }
                }
                // Comfortable tap target around the small mono label.
                .padding(.vertical, 10)
                .padding(.horizontal, 24)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .disabled(isLoggingOut)
            // Stable id the UI smoke tests depend on (was the M2 stub button).
            .accessibilityIdentifier("button-Log out")

            MonoLabel(versionLine)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 4)
    }

    private var versionLine: String {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0"
        return "v \(version) — ATTREQ"
    }
}

// MARK: - Moss toggle

/// The design's 36x20 moss pill toggle (artboard 08 reminder row): moss track
/// when on, hairline track when off, 16pt paper thumb.
private struct MossToggle: View {
    let isOn: Bool
    var isBusy: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Capsule()
                .fill(isOn ? Theme.moss : Theme.border)
                .frame(width: 36, height: 20)
                .overlay(alignment: isOn ? .trailing : .leading) {
                    Circle()
                        .fill(Theme.bg)
                        .frame(width: 16, height: 16)
                        .padding(.horizontal, 2)
                }
                .animation(.easeOut(duration: 0.15), value: isOn)
                // Extend the tappable area toward 44pt without growing layout.
                .padding(12)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .padding(-12)
        // Disabled while an enable/disable action is in flight so a second
        // tap can't race the first (which flips the toggle back on completion).
        .disabled(isBusy)
        .opacity(isBusy ? 0.5 : 1)
        .accessibilityLabel("Daily reminder")
        .accessibilityValue(isOn ? "On" : "Off")
        .accessibilityAddTraits(isOn ? [.isSelected] : [])
    }
}

// MARK: - Previews

#Preview("Profile") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    ProfileScreen(
        viewModel: ProfileViewModel(
            wardrobeRepository: WardrobeRepository(apiClient: client),
            outfitsRepository: OutfitsRepository(apiClient: client)
        )
    )
    .environment(AppSession())
}
