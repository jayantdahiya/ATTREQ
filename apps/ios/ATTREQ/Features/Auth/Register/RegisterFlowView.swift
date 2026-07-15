//
//  RegisterFlowView.swift
//  ATTREQ
//
//  Wizard shell for the 3-step registration flow (artboards 02–04):
//  AttreqStepNav on top, one step view below. Back walks steps;
//  on step 0 it exits to login. Successful submit flips
//  `AppSession.authState`, which navigates away — no manual routing here.
//

import SwiftUI

struct RegisterFlowView: View {
    @Environment(AppSession.self) private var session
    @Environment(\.dismiss) private var dismiss
    @State private var model = RegisterViewModel()
    @State private var step: Int

    /// `initialStep` exists for design audits (`-screen register-style` etc.);
    /// real navigation always starts at step 0.
    init(initialStep: Int = 0) {
        _step = State(initialValue: initialStep)
    }

    var body: some View {
        GeometryReader { geometry in
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    AttreqStepNav(step: step, onBack: goBack)
                        .padding(.bottom, 26)

                    stepContent
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .transition(.opacity)
                }
                .padding(.top, 8)
                .padding(.horizontal, 28)
                .padding(.bottom, 32)
                .frame(minHeight: geometry.size.height, alignment: .top)
            }
            .scrollBounceBehavior(.basedOnSize)
        }
        .background(Theme.bg.ignoresSafeArea())
        .toolbar(.hidden, for: .navigationBar)
        .navigationBarBackButtonHidden(true)
    }

    @ViewBuilder
    private var stepContent: some View {
        switch step {
        case 0:
            AccountStepView(
                model: model,
                onContinue: advanceFromAccount,
                onSignIn: { dismiss() }
            )
        case 1:
            StyleStepView(model: model, onContinue: { go(to: 2) })
        default:
            LocationStepView(model: model) {
                Task { await model.submit(using: session) }
            }
        }
    }

    private func advanceFromAccount() {
        guard model.validateAccount() else { return }
        go(to: 1)
    }

    private func goBack() {
        if step == 0 {
            dismiss()
        } else {
            go(to: step - 1)
        }
    }

    private func go(to newStep: Int) {
        model.errorMessage = nil
        withAnimation(.easeInOut(duration: 0.2)) {
            step = newStep
        }
    }
}

#Preview {
    NavigationStack {
        RegisterFlowView()
    }
}
