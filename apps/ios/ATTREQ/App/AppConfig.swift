//
//  AppConfig.swift
//  ATTREQ
//
//  Compile-time app configuration (M1).
//

import Foundation

/// Static app configuration.
enum AppConfig {
    /// Versioned API base URL (includes `/api/v1`).
    ///
    /// Resolution order:
    /// 1. `ATTREQ_API_URL` environment variable (Xcode scheme launch environment,
    ///    or `XCUIApplication.launchEnvironment` in UI tests).
    /// 2. Debug default: local backend at `http://localhost:8001/api/v1`.
    ///
    /// Release currently falls back to the same local URL — the production base URL
    /// lands with the beta backend deployment (M5).
    static let apiBaseURL: URL = {
        if let raw = ProcessInfo.processInfo.environment["ATTREQ_API_URL"],
           let url = URL(string: raw),
           url.scheme != nil {
            return url
        }
        return URL(string: "http://localhost:8001/api/v1")!
    }()
}
