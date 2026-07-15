import SwiftUI

@main
struct ATTREQApp: App {
    /// Single app-wide session, injected into the environment for every screen.
    @State private var session = AppSession()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(session)
        }
    }
}
