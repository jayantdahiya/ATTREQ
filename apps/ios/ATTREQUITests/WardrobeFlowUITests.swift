import XCTest

/// M2 smoke flow: library-photo upload into the wardrobe against the live
/// local backend. The account is provisioned via direct API calls (fast,
/// avoids re-driving the register wizard), then the UI is exercised:
/// login → Wardrobe tab → Library tile → system photo picker → item appears.
final class WardrobeFlowUITests: XCTestCase {

    private let apiBase = URL(string: "http://localhost:8001/api/v1")!

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    func testLibraryUploadShowsItemInGrid() throws {
        let email = "uitest-wardrobe+\(Int(Date().timeIntervalSince1970))@attreq.dev"
        let password = "Sup3rSecret!"
        try provisionOnboardedAccount(email: email, password: password)

        let app = XCUIApplication()
        // -uitest-autopick-photo: the Library tile feeds a synthetic JPEG
        // through the real upload path (PHPicker's remote view doesn't
        // reliably accept synthesized taps on this OS).
        app.launchArguments = ["-reset-auth", "-uitest-autopick-photo"]
        app.launch()

        // Login through the UI.
        let emailField = app.textFields["input-Email address"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 10))
        emailField.tap()
        emailField.typeText(email)
        let passwordField = app.secureTextFields["input-Password"]
        passwordField.tap()
        passwordField.typeText(password)
        app.buttons["button-Sign in"].tap()

        // Wardrobe tab → empty grid initially. The password-autofill save
        // prompt can race in at any point after sign-in and swallow taps, so
        // retry: dismiss the prompt if present, re-tap, check for the tile.
        let wardrobeTab = app.buttons["tab-WARDROBE"]
        XCTAssertTrue(wardrobeTab.waitForExistence(timeout: 15), "Tab shell should appear")

        let libraryTile = app.descendants(matching: .any)
            .matching(identifier: "tile-library").firstMatch
        var tileVisible = false
        for _ in 0 ..< 4 {
            dismissSavePasswordPromptIfPresent(app)
            if wardrobeTab.isHittable {
                wardrobeTab.tap()
            }
            if libraryTile.waitForExistence(timeout: 4) {
                tileVisible = true
                break
            }
        }
        if !tileVisible {
            print("=== A11Y TREE DUMP START ===")
            print(app.debugDescription)
            print("=== A11Y TREE DUMP END ===")
            XCTFail("Library tile should exist")
        }
        libraryTile.tap()

        // The tile (in -uitest-autopick-photo mode) uploads a synthetic JPEG
        // through the real multipart → backend → polling path.
        // Upload → item card appears in the grid (any status).
        let itemCard = app.descendants(matching: .any)
            .matching(NSPredicate(format: "identifier BEGINSWITH 'wardrobe-item-'"))
            .firstMatch
        XCTAssertTrue(itemCard.waitForExistence(timeout: 45), "Uploaded item should appear in the wardrobe grid")
    }

    /// The simulator's password-autofill "Save Password?" sheet steals taps
    /// after a successful sign-in; dismiss it when it shows up.
    private func dismissSavePasswordPromptIfPresent(_ app: XCUIApplication) {
        let notNow = app.buttons["Not Now"]
        if notNow.waitForExistence(timeout: 3) {
            notNow.tap()
        }
    }

    // MARK: - API provisioning

    private func provisionOnboardedAccount(email: String, password: String) throws {
        // Register (JSON).
        var register = URLRequest(url: apiBase.appendingPathComponent("auth/register"))
        register.httpMethod = "POST"
        register.setValue("application/json", forHTTPHeaderField: "Content-Type")
        register.httpBody = try JSONSerialization.data(withJSONObject: [
            "email": email, "password": password, "full_name": "UI Wardrobe Test",
        ])
        _ = try send(register)

        // Login (OAuth2 form) → access token.
        var login = URLRequest(url: apiBase.appendingPathComponent("auth/login"))
        login.httpMethod = "POST"
        login.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        var form = CharacterSet.alphanumerics
        form.insert(charactersIn: "-._~")
        let encodedEmail = email.addingPercentEncoding(withAllowedCharacters: form) ?? email
        let encodedPassword = password.addingPercentEncoding(withAllowedCharacters: form) ?? password
        login.httpBody = "username=\(encodedEmail)&password=\(encodedPassword)".data(using: .utf8)
        let loginData = try send(login)
        guard let json = try JSONSerialization.jsonObject(with: loginData) as? [String: Any],
              let token = json["access_token"] as? String else {
            XCTFail("Login provisioning did not return an access token")
            return
        }

        // Complete onboarding so the gate routes straight to tabs.
        var complete = URLRequest(url: apiBase.appendingPathComponent("users/onboarding/complete"))
        complete.httpMethod = "POST"
        complete.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        _ = try send(complete)
    }

    private func send(_ request: URLRequest) throws -> Data {
        let expectation = expectation(description: "api call")
        nonisolated(unsafe) var result: (Data?, URLResponse?, Error?)
        URLSession.shared.dataTask(with: request) { data, response, error in
            result = (data, response, error)
            expectation.fulfill()
        }.resume()
        wait(for: [expectation], timeout: 15)
        if let error = result.2 { throw error }
        let status = (result.1 as? HTTPURLResponse)?.statusCode ?? 0
        guard (200 ..< 300).contains(status), let data = result.0 else {
            throw NSError(domain: "provisioning", code: status, userInfo: [
                NSLocalizedDescriptionKey: "API provisioning failed with status \(status)",
            ])
        }
        return data
    }
}
