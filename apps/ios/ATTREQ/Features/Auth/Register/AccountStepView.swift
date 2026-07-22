//
//  AccountStepView.swift
//  ATTREQ
//
//  Artboard 02 — registration step 1 (account details).
//  Design: assets/design/ios-redesign-v2/attreq-auth.jsx (ATTREQRegisterAccount).
//

import SwiftUI

struct AccountStepView: View {
    @Bindable var model: RegisterViewModel
    let onContinue: () -> Void
    let onSignIn: () -> Void

    // Keyboard focus chain: email → name → password → confirm → submit.
    @FocusState private var isEmailFocused: Bool
    @FocusState private var isNameFocused: Bool
    @FocusState private var isPasswordFocused: Bool
    @FocusState private var isConfirmPasswordFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 01 — Account", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 6)

            BodyText("A few details, then we'll curate every look.")
                .padding(.bottom, 20)

            formCard
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            AttreqPrimaryButton("Continue →", action: onContinue)
                .padding(.top, 16)

            signInLink
                .frame(maxWidth: .infinity)
                .padding(.top, 12)
        }
    }

    private var headline: some View {
        (
            Text("Make this\n").foregroundStyle(Theme.text)
                + Text("your closet.")
                .font(.attreqDisplay(36, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(36))
    }

    private var formCard: some View {
        VStack(spacing: 18) {
            AttreqUnderlineInput(
                label: "Email address",
                text: $model.email,
                keyboard: .emailAddress,
                textContentType: .emailAddress,
                focus: $isEmailFocused
            )
            .submitLabel(.next)
            .onSubmit { isNameFocused = true }

            AttreqUnderlineInput(
                label: "Full name",
                text: $model.fullName,
                textContentType: .name,
                focus: $isNameFocused
            )
            .submitLabel(.next)
            .onSubmit { isPasswordFocused = true }

            AttreqUnderlineInput(
                label: "Password",
                text: $model.password,
                isSecure: true,
                textContentType: .newPassword,
                focus: $isPasswordFocused
            )
            .submitLabel(.next)
            .onSubmit { isConfirmPasswordFocused = true }

            AttreqUnderlineInput(
                label: "Confirm password",
                text: $model.confirmPassword,
                isSecure: true,
                textContentType: .newPassword,
                focus: $isConfirmPasswordFocused
            )
            .submitLabel(.done)
            .onSubmit(onContinue)

            if let errorMessage = model.errorMessage {
                BodyText(errorMessage, size: 13, color: Theme.clay)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .frame(maxHeight: .infinity, alignment: .center)
        .padding(.vertical, 22)
        .padding(.horizontal, 20)
        .attreqCard(padding: 0)
    }

    private var signInLink: some View {
        Button(action: onSignIn) {
            (
                Text("Have an account? ").foregroundStyle(Theme.t2)
                    + Text("Sign in")
                    .font(.attreqBody(13, weight: .medium))
                    .foregroundStyle(Theme.accent)
            )
            .font(.attreqBody(13))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    AccountStepView(model: RegisterViewModel(), onContinue: {}, onSignIn: {})
        .padding(28)
        .background(Theme.bg)
}
