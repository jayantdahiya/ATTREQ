//
//  AttreqUnderlineInput.swift
//  ATTREQ
//
//  Underline text input — port of `ATTREQInput` from attreq-shared.jsx.
//  Mono label above a borderless field with a 1pt bottom border.
//

import SwiftUI
import UIKit

/// Labeled single-line input with an underline instead of a box.
struct AttreqUnderlineInput: View {
    let label: String
    @Binding var text: String
    var isSecure: Bool = false
    var keyboard: UIKeyboardType = .default
    var textContentType: UITextContentType? = nil
    /// Explicit autocapitalization override. When `nil`, email keyboards
    /// default to `.never`; other keyboards use the system default.
    var autocapitalization: TextInputAutocapitalization? = nil
    /// Explicit autocorrection override. When `nil`, email keyboards
    /// default to disabling autocorrection; others use the system default.
    var disableAutocorrection: Bool? = nil

    private var resolvedAutocapitalization: TextInputAutocapitalization? {
        autocapitalization ?? (keyboard == .emailAddress ? .never : nil)
    }

    private var resolvedDisableAutocorrection: Bool {
        disableAutocorrection ?? (keyboard == .emailAddress)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel(label)

            Group {
                if isSecure {
                    SecureField("", text: $text)
                } else {
                    TextField("", text: $text)
                }
            }
            .textFieldStyle(.plain)
            .font(.attreqBody(14.5))
            .foregroundStyle(Theme.text)
            .keyboardType(keyboard)
            .textContentType(textContentType)
            .textInputAutocapitalization(resolvedAutocapitalization)
            .autocorrectionDisabled(resolvedDisableAutocorrection)
            .padding(.top, 6)
            .padding(.bottom, 8)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(Theme.border)
                    .frame(height: 1)
            }
        }
    }
}

#Preview {
    @Previewable @State var email = "ines@attreq.com"
    @Previewable @State var password = "secret-password"
    @Previewable @State var city = ""

    return VStack(spacing: 24) {
        AttreqUnderlineInput(
            label: "Email",
            text: $email,
            keyboard: .emailAddress,
            textContentType: .emailAddress
        )
        AttreqUnderlineInput(
            label: "Password",
            text: $password,
            isSecure: true,
            textContentType: .password
        )
        AttreqUnderlineInput(label: "City", text: $city)
    }
    .padding(24)
    .background(Theme.bg)
}
