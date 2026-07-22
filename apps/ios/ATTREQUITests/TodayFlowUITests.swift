import XCTest

/// M4 smoke flow: daily suggestion → Wear → History, against the live local
/// backend. The account, location, and a top+bottom wardrobe pair are
/// provisioned via direct API calls (the bulk endpoint takes explicit
/// categories, so no classifier key is needed); keyless weather falls back to
/// the backend's default weather, so suggestions always generate.
final class TodayFlowUITests: XCTestCase {

    private let apiBase = URL(string: "http://localhost:8001/api/v1")!

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    func testWearSuggestionShowsInHistory() throws {
        let email = "uitest-today+\(Int(Date().timeIntervalSince1970))@attreq.dev"
        let password = "Sup3rSecret!"
        try provisionAccountWithWardrobe(email: email, password: password)

        let app = XCUIApplication()
        app.launchArguments = ["-reset-auth"]
        app.launch()

        // Login.
        let emailField = app.textFields["input-Email address"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 10))
        emailField.tap()
        emailField.typeText(email)
        let passwordField = app.secureTextFields["input-Password"]
        passwordField.tap()
        passwordField.typeText(password)
        app.buttons["button-Sign in"].tap()

        // Today tab is the landing tab; a suggestion card should appear.
        XCTAssertTrue(app.buttons["tab-TODAY"].waitForExistence(timeout: 15), "Tab shell should appear")
        dismissSavePasswordPromptIfPresent(app)

        let wearButton = app.buttons["button-Wear this"]
        XCTAssertTrue(wearButton.waitForExistence(timeout: 30), "A daily suggestion should render")
        wearButton.tap()

        // Wear → outfit recorded; History should show one entry. A successful
        // wear marks the History view model stale, so entering the History
        // tab re-fires its `.task` `load()`, which refetches.
        let historyTab = app.buttons["tab-HISTORY"]
        // Retry pattern: the wear POSTs complete asynchronously, so the stale
        // mark may land after the first History entry.
        var entryVisible = false
        let entry = app.descendants(matching: .any)
            .matching(NSPredicate(format: "identifier BEGINSWITH 'history-entry-'"))
            .firstMatch
        for _ in 0 ..< 4 {
            dismissSavePasswordPromptIfPresent(app)
            if historyTab.isHittable {
                historyTab.tap()
            }
            if entry.waitForExistence(timeout: 5) {
                entryVisible = true
                break
            }
            // Bounce via Today and back: History was marked stale by the
            // wear, so re-entering the tab re-runs `load()` and refetches.
            app.buttons["tab-TODAY"].tap()
        }
        XCTAssertTrue(entryVisible, "The worn outfit should appear in History")

        // The entry should carry the Worn pill (no feedback was given).
        XCTAssertTrue(
            app.staticTexts["WORN"].firstMatch.exists || app.staticTexts["Worn"].firstMatch.exists,
            "History entry should show the Worn status pill"
        )
    }

    // MARK: - Helpers

    private func dismissSavePasswordPromptIfPresent(_ app: XCUIApplication) {
        let notNow = app.buttons["Not Now"]
        if notNow.waitForExistence(timeout: 3) {
            notNow.tap()
        }
    }

    // MARK: - API provisioning

    private func provisionAccountWithWardrobe(email: String, password: String) throws {
        var register = URLRequest(url: apiBase.appendingPathComponent("auth/register"))
        register.httpMethod = "POST"
        register.setValue("application/json", forHTTPHeaderField: "Content-Type")
        register.httpBody = try JSONSerialization.data(withJSONObject: [
            "email": email, "password": password, "full_name": "Today Test",
        ])
        _ = try send(register)

        var form = CharacterSet.alphanumerics
        form.insert(charactersIn: "-._~")
        var login = URLRequest(url: apiBase.appendingPathComponent("auth/login"))
        login.httpMethod = "POST"
        login.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        let encodedEmail = email.addingPercentEncoding(withAllowedCharacters: form) ?? email
        let encodedPassword = password.addingPercentEncoding(withAllowedCharacters: form) ?? password
        login.httpBody = "username=\(encodedEmail)&password=\(encodedPassword)".data(using: .utf8)
        let loginData = try send(login)
        guard let json = try JSONSerialization.jsonObject(with: loginData) as? [String: Any],
              let token = json["access_token"] as? String else {
            XCTFail("Login provisioning did not return an access token")
            return
        }

        try authorizedPost(
            path: "users/onboarding/complete", token: token, body: nil
        )
        try authorizedRequest(
            path: "users/me/location", method: "PATCH", token: token,
            body: ["lat": 45.4642, "lon": 9.19, "city": "Milan"]
        )
        // Bulk-add a classified top + bottom so the recommendation algorithm
        // can pair an outfit without any classifier key.
        var bulk = URLRequest(url: apiBase.appendingPathComponent("wardrobe/items/bulk"))
        bulk.httpMethod = "POST"
        bulk.setValue("application/json", forHTTPHeaderField: "Content-Type")
        bulk.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        // Categories are literal "top"/"bottom": the backend algorithm slots
        // by substring match on those words (known taxonomy gap — see roadmap
        // M2), and all seasons are set so the weather filter can't exclude
        // the pair under the keyless default weather.
        let allSeasons = ["summer", "winter", "spring", "fall"]
        bulk.httpBody = try JSONSerialization.data(withJSONObject: [
            [
                "category": "top", "subcategory": "t-shirt", "color_primary": "white",
                "pattern": "solid", "season": allSeasons, "occasion": ["casual"],
                "confidence": 0.95, "original_image_url": "/uploads/wardrobe/test-top.jpg",
                "classification_source": "uitest",
            ],
            [
                "category": "bottom", "subcategory": "jeans", "color_primary": "blue",
                "pattern": "solid", "season": allSeasons, "occasion": ["casual"],
                "confidence": 0.95, "original_image_url": "/uploads/wardrobe/test-bottom.jpg",
                "classification_source": "uitest",
            ],
        ])
        _ = try send(bulk)
    }

    private func authorizedPost(path: String, token: String, body: [String: Any]?) throws {
        try authorizedRequest(path: path, method: "POST", token: token, body: body)
    }

    private func authorizedRequest(path: String, method: String, token: String, body: [String: Any]?) throws {
        var request = URLRequest(url: apiBase.appendingPathComponent(path))
        request.httpMethod = method
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        _ = try send(request)
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
                NSLocalizedDescriptionKey: "API provisioning failed with status \(status) for \(request.url?.path ?? "?")",
            ])
        }
        return data
    }
}
