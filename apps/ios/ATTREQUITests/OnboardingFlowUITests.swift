import XCTest

/// M3 smoke flow: the full Style DNA onboarding path against the live local
/// backend — photo grid (via the -uitest-autopick-photos hook), build DNA,
/// results, review, completion → tab shell. Works with or without a
/// classifier key (a nil style_dna takes the graceful-failure branch).
final class OnboardingFlowUITests: XCTestCase {

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    func testFullOnboardingWithPhotos() throws {
        var app = XCUIApplication()
        app.launchArguments = ["-reset-auth", "-uitest-autopick-photos"]
        app.launch()

        // Register a fresh account through the wizard (fastest reliable route
        // to the onboarding gate in-app).
        XCTAssertTrue(app.buttons["button-Sign in"].waitForExistence(timeout: 10))
        app.buttons["link-create-account"].tap()

        let email = "uitest-onboarding+\(Int(Date().timeIntervalSince1970))@attreq.dev"
        let emailField = app.textFields["input-Email address"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 5))
        emailField.tap()
        emailField.typeText(email)
        let nameField = app.textFields["input-Full name"]
        nameField.tap()
        nameField.typeText("Onboarding Test")
        let passwordField = app.secureTextFields["input-Password"]
        passwordField.tap()
        passwordField.typeText("Sup3rSecret!")
        let confirmField = app.secureTextFields["input-Confirm password"]
        confirmField.tap()
        confirmField.typeText("Sup3rSecret!")
        tapButton(app, beginningWith: "button-Continue")

        XCTAssertTrue(app.buttons["chip-Minimal"].waitForExistence(timeout: 5))
        app.buttons["chip-Minimal"].tap()
        tapButton(app, beginningWith: "button-Continue")

        let cityField = app.textFields
            .matching(NSPredicate(format: "identifier CONTAINS[c] 'city'")).firstMatch
        XCTAssertTrue(cityField.waitForExistence(timeout: 5))
        cityField.tap()
        cityField.typeText("Milan")
        tapButton(app, beginningWith: "button-Create account")

        // Onboarding: upload screen. Tap an empty tile — the autopick hook
        // appends 3 synthetic photos.
        let firstTile = app.descendants(matching: .any)
            .matching(NSPredicate(format: "identifier BEGINSWITH 'styledna-tile-'"))
            .firstMatch
        XCTAssertTrue(firstTile.waitForExistence(timeout: 20), "Photo grid should appear")
        firstTile.tap()

        // Build CTA enables at >=3 photos; upload + extraction can take a while.
        let buildButton = app.buttons["button-Build my Style DNA →"]
        XCTAssertTrue(buildButton.waitForExistence(timeout: 5))
        XCTAssertTrue(
            waitUntilEnabled(buildButton, timeout: 10),
            "Build CTA should enable once 3 photos are added"
        )
        buildButton.tap()

        // Two legitimate outcomes, depending on whether the backend has a
        // classifier key configured:
        //  A) extraction ran → results step → (review) → complete;
        //  B) no usable photos (backend 422) → error surfaces on the upload
        //     screen → skip still completes onboarding (degraded-mode UX).
        let continueButton = app.buttons.matching(
            NSPredicate(format: "identifier == 'button-Review items →' OR identifier == 'button-Looks right →'")
        ).firstMatch
        let skipLink = app.descendants(matching: .any)
            .matching(identifier: "link-skip-onboarding").firstMatch

        let deadline = Date().addingTimeInterval(60)
        var tookResultsPath = false
        while Date() < deadline {
            if continueButton.exists {
                tookResultsPath = true
                break
            }
            // Upload finished with a failure: build button interactable again
            // on the upload screen (skip link only exists on that screen).
            if buildButton.exists, buildButton.isEnabled, skipLink.exists {
                break
            }
            RunLoop.current.run(until: Date().addingTimeInterval(0.5))
        }

        if tookResultsPath {
            continueButton.tap()
            // Review step (if shown) → confirm; either way we must land on tabs.
            let confirmReview = app.buttons["button-Looks right →"]
            if confirmReview.waitForExistence(timeout: 5) {
                confirmReview.tap()
            }
        } else {
            XCTAssertTrue(skipLink.exists, "Degraded mode: upload screen with skip link should remain after a failed extraction")
            skipLink.tap()
        }

        XCTAssertTrue(app.buttons["tab-TODAY"].waitForExistence(timeout: 20), "Onboarding should land on the tab shell")

        // The gate must not reappear on relaunch.
        app.terminate()
        app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.buttons["tab-TODAY"].waitForExistence(timeout: 15), "Completed onboarding must persist")
    }

    // MARK: - Helpers

    private func tapButton(_ app: XCUIApplication, beginningWith prefix: String) {
        let button = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", prefix)).firstMatch
        XCTAssertTrue(button.waitForExistence(timeout: 5), "Button \(prefix)… should exist")
        button.tap()
    }

    private func waitUntilEnabled(_ element: XCUIElement, timeout: TimeInterval) -> Bool {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if element.isEnabled { return true }
            RunLoop.current.run(until: Date().addingTimeInterval(0.25))
        }
        return element.isEnabled
    }
}
