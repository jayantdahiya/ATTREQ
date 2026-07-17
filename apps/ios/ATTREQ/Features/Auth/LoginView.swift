//
//  LoginView.swift
//  ATTREQ
//
//  Artboard 01 — login. Centered brand block, "Welcome back" card,
//  bottom link into the registration wizard.
//  Design: assets/design/ios-redesign-v2/attreq-auth.jsx (ATTREQLogin).
//

import SwiftUI

struct LoginView: View {
    @Environment(AppSession.self) private var session
    @State private var model = LoginViewModel()
    @State private var showRegister = false

    // Keyboard focus chain: email → password → submit.
    @FocusState private var isEmailFocused: Bool
    @FocusState private var isPasswordFocused: Bool

    var body: some View {
        NavigationStack {
            GeometryReader { geometry in
                ScrollView {
                    VStack(spacing: 0) {
                        brandBlock
                            .padding(.top, 42)

                        Spacer(minLength: 24)

                        loginCard

                        Spacer(minLength: 24)

                        registerLink
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 40)
                    .frame(minHeight: geometry.size.height)
                }
                .scrollBounceBehavior(.basedOnSize)
            }
            .background(Theme.bg.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(isPresented: $showRegister) {
                RegisterFlowView()
            }
        }
    }

    // MARK: Brand block

    private var brandBlock: some View {
        VStack(spacing: 0) {
            HStack(spacing: 14) {
                hairline
                // `layoutPriority` (instead of `fixedSize`) keeps the label
                // whole ahead of the flexible hairlines but still bounded by
                // the screen; `minimumScaleFactor` absorbs XL Dynamic Type
                // instead of overflowing the edges.
                MonoLabel("Est. 2026 — Personal Styling")
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
                    .layoutPriority(1)
                hairline
            }
            .padding(.bottom, 24)

            Text("ATTREQ")
                .font(.attreqDisplay(60))
                .tracking(9)
                .foregroundStyle(Theme.text)
                .lineLimit(1)
                // Scale down rather than truncate the wordmark at XL
                // Dynamic Type / narrow widths.
                .minimumScaleFactor(0.7)
                .padding(.bottom, 14)

            Text("Your closet, curated.")
                .font(.attreqDisplay(19, weight: .regular, italic: true))
                .tracking(0.3)
                .foregroundStyle(Theme.t2)
        }
    }

    private var hairline: some View {
        Rectangle()
            .fill(Theme.border)
            .frame(maxWidth: .infinity)
            .frame(height: 1)
    }

    // MARK: Card

    private var loginCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Welcome back")
                .font(.attreqDisplay(24))
                .foregroundStyle(Theme.text)
                .padding(.bottom, 4)

            BodyText("Sign in to your wardrobe.", size: 13)
                .padding(.bottom, 24)

            VStack(spacing: 20) {
                AttreqUnderlineInput(
                    label: "Email address",
                    text: $model.email,
                    keyboard: .emailAddress,
                    textContentType: .emailAddress,
                    focus: $isEmailFocused
                )
                .submitLabel(.next)
                .onSubmit { isPasswordFocused = true }

                AttreqUnderlineInput(
                    label: "Password",
                    text: $model.password,
                    isSecure: true,
                    textContentType: .password,
                    focus: $isPasswordFocused
                )
                .submitLabel(.done)
                .onSubmit(signIn)
            }
            .padding(.bottom, 24)

            if let errorMessage = model.errorMessage {
                BodyText(errorMessage, size: 13, color: Theme.clay)
                    .padding(.bottom, 12)
            }

            AttreqPrimaryButton("Sign in", isLoading: model.isLoading, action: signIn)

            MonoLabel("Forgot password")
                .frame(maxWidth: .infinity)
                .padding(.top, 14)
        }
        .padding(.vertical, 28)
        .padding(.horizontal, 24)
        .attreqCard(padding: 0)
    }

    // MARK: Footer

    private var registerLink: some View {
        Button {
            model.errorMessage = nil
            showRegister = true
        } label: {
            (
                Text("New here? ").foregroundStyle(Theme.t2)
                    + Text("Create account")
                    .font(.attreqBody(13, weight: .medium))
                    .foregroundStyle(Theme.accent)
            )
            .font(.attreqBody(13))
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("link-create-account")
    }

    private func signIn() {
        guard !model.isLoading else { return }
        Task { await model.signIn(using: session) }
    }
}

#Preview {
    LoginView()
}
