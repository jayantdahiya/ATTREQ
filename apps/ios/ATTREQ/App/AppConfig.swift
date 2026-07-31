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

    /// Backend origin — `apiBaseURL` minus its `/api/v1` suffix
    /// (e.g. `http://localhost:8001`). Media paths the backend returns
    /// (`/uploads/...`) are relative to this, not to the versioned base
    /// (mirrors RN `backendBaseUrl` / `resolveApiImageUrl`).
    static var apiOrigin: URL {
        var raw = apiBaseURL.absoluteString
        while raw.hasSuffix("/") {
            raw.removeLast()
        }
        if raw.lowercased().hasSuffix("/api/v1") {
            raw = String(raw.dropLast("/api/v1".count))
        }
        return URL(string: raw) ?? apiBaseURL
    }

    /// Resolves a backend media path to an absolute URL.
    ///
    /// - Already-absolute `http(s)` URLs pass through unchanged (S3 storage).
    /// - Relative paths (`/uploads/originals/x.jpg`, with or without the
    ///   leading slash) resolve against `apiOrigin`.
    /// - `nil`/empty input returns `nil`.
    static func absoluteMediaURL(_ path: String?) -> URL? {
        guard let path, !path.isEmpty else { return nil }
        let lowered = path.lowercased()
        if lowered.hasPrefix("http://") || lowered.hasPrefix("https://") {
            return URL(string: path)
        }
        let relative = path.hasPrefix("/") ? String(path.dropFirst()) : path
        return apiOrigin.appending(path: relative)
    }
}
