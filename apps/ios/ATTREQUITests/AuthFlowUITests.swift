import XCTest

/// M1 smoke flow against the live local backend: register via the 3-step
/// wizard → complete onboarding → persistence across relaunch → logout →
/// login. Requires the API running (see docs/06-ios-native milestone docs).
final class AuthFlowUITests: XCTestCase {

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    func testRegisterOnboardLogoutLogin() throws {
        let email = "uitest+\(Int(Date().timeIntervalSince1970))@attreq.dev"
        let password = "Sup3rSecret!"

        // 1. Fresh launch: keychain reset → login screen.
        var app = XCUIApplication()
        app.launchArguments = ["-reset-auth"]
        app.launch()

        let signIn = app.buttons["button-Sign in"]
        XCTAssertTrue(signIn.waitForExistence(timeout: 10), "Login screen should appear")

        // 2. → Register wizard, step 1: account.
        app.buttons["link-create-account"].tap()

        let emailField = app.textFields["input-Email address"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 5), "Account step should appear")
        emailField.tap()
        emailField.typeText(email)
        let nameField = app.textFields["input-Full name"]
        nameField.tap()
        nameField.typeText("UI Test")
        let passwordField = app.secureTextFields["input-Password"]
        passwordField.tap()
        passwordField.typeText(password)
        let confirmField = app.secureTextFields["input-Confirm password"]
        confirmField.tap()
        confirmField.typeText(password)

        tapButton(app, beginningWith: "button-Continue")

        // 3. Step 2: style keywords.
        let minimalChip = app.buttons["chip-Minimal"]
        XCTAssertTrue(minimalChip.waitForExistence(timeout: 5), "Style step should appear")
        minimalChip.tap()
        app.buttons["chip-Earthy"].tap()
        tapButton(app, beginningWith: "button-Continue")

        // 4. Step 3: manual city, submit.
        let cityField = field(app, idContaining: "city")
        XCTAssertTrue(cityField.waitForExistence(timeout: 5), "Location step should appear")
        cityField.tap()
        cityField.typeText("Milan")
        tapButton(app, beginningWith: "button-Create account")

        // 5. Registered + logged in → onboarding gate (fresh users).
        let completeOnboarding = app.buttons["button-Complete onboarding"]
        XCTAssertTrue(completeOnboarding.waitForExistence(timeout: 20), "Onboarding placeholder should appear after registration")
        completeOnboarding.tap()

        // 6. Onboarding completed → main tab shell (Today tab active).
        let todayTab = app.buttons["tab-TODAY"]
        XCTAssertTrue(todayTab.waitForExistence(timeout: 15), "Tab shell should appear after onboarding")

        // Log out lives in the Profile tab since M2's real tab shell.
        app.buttons["tab-PROFILE"].tap()
        let logOut = app.buttons["button-Log out"]
        XCTAssertTrue(logOut.waitForExistence(timeout: 10), "Profile tab should offer Log out")

        // 7. Relaunch WITHOUT reset: session must persist via Keychain.
        app.terminate()
        app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.buttons["tab-PROFILE"].waitForExistence(timeout: 15), "Session should persist across relaunch")
        app.buttons["tab-PROFILE"].tap()
        let logOutAfterRelaunch = app.buttons["button-Log out"]
        XCTAssertTrue(logOutAfterRelaunch.waitForExistence(timeout: 10), "Profile tab should offer Log out after relaunch")

        // 8. Logout → login screen.
        logOutAfterRelaunch.tap()
        XCTAssertTrue(app.buttons["button-Sign in"].waitForExistence(timeout: 10), "Logout should return to login")

        // 9. Login with the same credentials.
        let loginEmail = app.textFields["input-Email address"]
        loginEmail.tap()
        loginEmail.typeText(email)
        let loginPassword = app.secureTextFields["input-Password"]
        loginPassword.tap()
        loginPassword.typeText(password)
        app.buttons["button-Sign in"].tap()
        XCTAssertTrue(app.buttons["tab-TODAY"].waitForExistence(timeout: 15), "Login should reach the authenticated tab shell")
        // Dismiss the password-autofill save prompt if the simulator shows it,
        // so later tests inherit a clean foreground.
        let notNow = app.buttons["Not Now"]
        if notNow.waitForExistence(timeout: 3) {
            notNow.tap()
        }
    }

    // MARK: - Helpers

    private func tapButton(_ app: XCUIApplication, beginningWith prefix: String) {
        let button = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", prefix)).firstMatch
        XCTAssertTrue(button.waitForExistence(timeout: 5), "Button \(prefix)… should exist")
        button.tap()
    }

    private func field(_ app: XCUIApplication, idContaining fragment: String) -> XCUIElement {
        app.textFields.matching(
            NSPredicate(format: "identifier CONTAINS[c] %@", fragment)
        ).firstMatch
    }
}
