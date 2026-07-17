//
//  WardrobeViewModel.swift
//  ATTREQ
//
//  Observable state for the Wardrobe screen (M2): list + client-side category
//  filter, multipart upload, and status polling while items are pending/processing.
//

import Foundation
import Observation

/// Category chips on the wardrobe screen (artboard 06:
/// All/Tops/Bottoms/Outer/Accents/Shoes). Backend categories are free text
/// (M2 roadmap gap), so filtering buckets each item by case-insensitive
/// substring match — same rules and precedence as RN `toneForCategory` in
/// `wardrobe-screen.tsx`, with its `bag` tone folded into Accents (no Bag chip).
enum WardrobeFilter: String, CaseIterable, Sendable {
    case all
    case tops
    case bottoms
    case outer
    case accents
    case shoes

    /// Chip label as designed.
    var label: String {
        switch self {
        case .all: "All"
        case .tops: "Tops"
        case .bottoms: "Bottoms"
        case .outer: "Outer"
        case .accents: "Accents"
        case .shoes: "Shoes"
        }
    }

    /// Which chip a free-text backend category belongs to. Every category
    /// lands in exactly one bucket; unrecognized text falls back to Tops
    /// (mirrors the RN default tone). Terms cover the closed vocabulary the
    /// backend classifiers emit (`services/ai/groq_classifier.py`
    /// `CLASSIFICATION_PROMPT`) plus future-proof shoe/accessory words;
    /// precedence is bottoms → shoes → outer → accents → tops, first match
    /// wins (same ordering as RN `toneForCategory`). Note dress/jumpsuit/
    /// romper deliberately fall through to Tops, matching RN.
    static func bucket(for category: String?) -> WardrobeFilter {
        let value = category?.lowercased() ?? ""
        if value.contains("bottom") || value.contains("pant") || value.contains("trouser")
            || value.contains("jean") || value.contains("skirt") || value.contains("short")
            || value.contains("chino") || value.contains("legging") {
            return .bottoms
        }
        if value.contains("shoe") || value.contains("sneaker") || value.contains("sandal")
            || value.contains("boot") || value.contains("heel") {
            return .shoes
        }
        if value.contains("outer") || value.contains("coat") || value.contains("jacket")
            || value.contains("blazer") {
            return .outer
        }
        if value.contains("bag") || value.contains("belt") || value.contains("hat")
            || value.contains("scarf") || value.contains("jewel") || value.contains("accessor") {
            return .accents
        }
        return .tops
    }

    func matches(_ category: String?) -> Bool {
        self == .all || Self.bucket(for: category) == self
    }
}

/// Drives `WardrobeScreen`. Owned by `MainTabsView` so state survives tab switches.
@MainActor
@Observable
final class WardrobeViewModel {
    // MARK: State (read by WardrobeScreen)

    /// Full first page (newest first, page size 50 — matches the RN app).
    private(set) var items: [WardrobeItem] = []
    /// True only during the initial load (grid shows a spinner).
    private(set) var isLoading = false
    /// True while an upload is in flight (tiles disabled, "Uploading" row shown).
    private(set) var isUploading = false
    /// Last load/upload failure, rendered as a banner; cleared on next success.
    var errorMessage: String?
    /// Selected category chip; filtering is client-side.
    var selectedCategory: WardrobeFilter = .all

    /// Items under the selected chip.
    var filteredItems: [WardrobeItem] {
        selectedCategory == .all ? items : items.filter { selectedCategory.matches($0.category) }
    }

    /// Server-side total across all pages (the "N pieces" line).
    private(set) var totalCount = 0

    /// Highest page currently loaded into `items` (pages 2+ are appended by
    /// `loadMoreIfNeeded`).
    @ObservationIgnored private var currentPage = 1
    /// Total pages reported by the last list response.
    @ObservationIgnored private var totalPages = 1
    /// True while a next-page fetch is in flight (prevents duplicate loads).
    @ObservationIgnored private var isLoadingMore = false

    /// Human-readable recency of the newest item ("2 hours ago", "yesterday"),
    /// for the "— last added …" suffix. `nil` when the wardrobe is empty.
    var lastAddedRelative: String? {
        guard let newest = items.map(\.createdAt).max() else { return nil }
        if Date.now.timeIntervalSince(newest) < 60 {
            return "just now"
        }
        let formatter = RelativeDateTimeFormatter()
        formatter.dateTimeStyle = .named
        return formatter.localizedString(for: newest, relativeTo: .now)
    }

    // MARK: Dependencies

    private let repository: WardrobeRepository
    /// Time between status polls while any item is pending/processing (~2s).
    private let pollInterval: Duration
    /// Give up polling after this long even if items never reach a terminal state (~90s).
    private let pollCap: Duration

    @ObservationIgnored private var pollTask: Task<Void, Never>?

    init(
        repository: WardrobeRepository,
        pollInterval: Duration = .seconds(2),
        pollCap: Duration = .seconds(90)
    ) {
        self.repository = repository
        self.pollInterval = pollInterval
        self.pollCap = pollCap
    }

    // MARK: Loading

    /// First load when the screen appears. Safe to call repeatedly
    /// (`.task` re-fires on tab switches) — only fetches when empty.
    func loadInitial() async {
        guard items.isEmpty, !isLoading else { return }
        isLoading = true
        defer { isLoading = false }
        await fetch(surfaceError: true)
    }

    /// Pull-to-refresh: reload of page 1 (resets pagination), then resume
    /// polling if anything is still processing.
    func refresh() async {
        await fetch(surfaceError: true)
        guard !Task.isCancelled else { return }
        startPollingIfNeeded()
    }

    /// Fetches page 1 into `items`/`totalCount`, resetting pagination. When
    /// `surfaceError` is false failures are ignored and the last good list
    /// stays. Cancellation (screen left, refresh gesture interrupted) is
    /// never an error — the last good state stays and nothing is surfaced.
    private func fetch(surfaceError: Bool) async {
        do {
            let response = try await repository.list()
            items = response.items
            totalCount = response.total
            currentPage = response.page
            totalPages = response.totalPages
            if surfaceError {
                errorMessage = nil
            }
        } catch {
            guard !Self.isCancellation(error) else { return }
            if surfaceError {
                errorMessage = Self.message(for: error, fallback: "Couldn't load your wardrobe.")
            }
        }
    }

    /// Background refetch of page 1 (polls, post-upload) that MERGES by id
    /// instead of replacing: refreshed items overwrite their loaded copies,
    /// genuinely new items are prepended, and pages appended via
    /// `loadMoreIfNeeded` are kept. Failures (including cancellation) are
    /// silent — the last good list stays.
    private func fetchPageOneMerging() async {
        do {
            let response = try await repository.list()
            totalCount = response.total
            totalPages = response.totalPages
            var merged = items
            var fresh: [WardrobeItem] = []
            for item in response.items {
                if let index = merged.firstIndex(where: { $0.id == item.id }) {
                    merged[index] = item
                } else {
                    fresh.append(item)
                }
            }
            items = fresh + merged
        } catch {
            // Background fetch — never surfaces errors.
        }
    }

    /// True for errors that mean "this request was cancelled" rather than an
    /// actual failure — `CancellationError`, `URLError.cancelled`, and either
    /// of those wrapped in `APIError.network` by `APIClient.send`.
    private static func isCancellation(_ error: any Error) -> Bool {
        if error is CancellationError { return true }
        if (error as? URLError)?.code == .cancelled { return true }
        if case let APIError.network(underlying) = error {
            return isCancellation(underlying)
        }
        return false
    }

    // MARK: Pagination

    /// How close to the end of `items` a card must be to prefetch the next page.
    private static let loadMoreThreshold = 6

    /// Called from each grid card's `.onAppear`: when `currentItem` is within
    /// the last `loadMoreThreshold` items, more pages exist, and no next-page
    /// fetch is already running, fetches the next page and appends it.
    /// Failures are silent — scrolling again retries.
    func loadMoreIfNeeded(currentItem: WardrobeItem) async {
        guard !isLoadingMore, !isLoading, currentPage < totalPages else { return }
        guard let index = items.firstIndex(where: { $0.id == currentItem.id }),
              index >= items.count - Self.loadMoreThreshold else { return }
        isLoadingMore = true
        defer { isLoadingMore = false }
        do {
            let response = try await repository.list(page: currentPage + 1)
            currentPage = response.page
            totalPages = response.totalPages
            totalCount = response.total
            // A concurrent poll merge may already have prepended some of these.
            let loadedIDs = Set(items.map(\.id))
            items += response.items.filter { !loadedIDs.contains($0.id) }
        } catch {
            // Silent (includes cancellation); the next .onAppear retries.
        }
    }

    // MARK: Upload

    /// Uploads a JPEG (the photo pipeline always JPEG-encodes), refetches the
    /// list so the new pending item appears, and starts status polling.
    /// Uploads an image; returns `true` on a successful upload so the screen
    /// can notify the tab shell (which invalidates the Profile Pieces stat).
    @discardableResult
    func upload(imageData: Data) async -> Bool {
        guard !isUploading else { return false }
        isUploading = true
        defer { isUploading = false }
        do {
            let response = try await repository.upload(imageData: imageData)
            errorMessage = nil
            await fetchPageOneMerging()
            // If the refetch failed (or hasn't caught up), surface the new
            // piece immediately as an optimistic pending placeholder; the
            // next successful poll/refresh replaces it via the id merge.
            if !items.contains(where: { $0.id == response.id }) {
                items.insert(Self.pendingPlaceholder(for: response), at: 0)
                totalCount += 1
            }
            // Restart the poller so this upload gets a fresh poll deadline
            // instead of inheriting an old loop's near-expired 90s cap.
            stopPolling()
            startPollingIfNeeded()
            return true
        } catch {
            errorMessage = Self.message(for: error, fallback: "Upload failed. Please try again.")
            return false
        }
    }

    /// Optimistic stand-in for a just-uploaded item when the follow-up
    /// refetch failed: enough fields for the card (image URL + pending badge).
    private static func pendingPlaceholder(for response: WardrobeUploadResponse) -> WardrobeItem {
        WardrobeItem(
            id: response.id,
            userId: "",
            originalImageUrl: response.originalImageUrl,
            processedImageUrl: nil,
            thumbnailUrl: nil,
            category: nil,
            colorPrimary: nil,
            colorSecondary: nil,
            pattern: nil,
            season: nil,
            occasion: nil,
            detectionConfidence: nil,
            classificationSource: nil,
            processingStatus: .pending,
            wearCount: 0,
            lastWorn: nil,
            createdAt: Date(),
            updatedAt: Date()
        )
    }

    // MARK: Polling

    /// True while the AI pipeline still owes us a terminal status for any item.
    private var hasActiveProcessing: Bool {
        items.contains { $0.processingStatus == .pending || $0.processingStatus == .processing }
    }

    /// Refetches the list every `pollInterval` while any item is
    /// pending/processing; stops when all items are terminal or after
    /// `pollCap`. Idempotent — a live poll loop is never duplicated.
    func startPollingIfNeeded() {
        guard pollTask == nil, hasActiveProcessing else { return }
        pollTask = Task { [weak self] in
            let clock = ContinuousClock()
            let deadline = clock.now.advanced(by: self?.pollCap ?? .zero)
            defer {
                // Cancellation means `stopPolling()` already cleared (or
                // replaced) `pollTask` — only a natural exit clears it here.
                if !Task.isCancelled {
                    self?.pollTask = nil
                }
            }
            while let self, !Task.isCancelled {
                try? await clock.sleep(for: self.pollInterval)
                guard !Task.isCancelled else { return }
                await self.fetchPageOneMerging()
                guard self.hasActiveProcessing, clock.now < deadline else { return }
            }
        }
    }

    /// Cancels the poll loop (screen disappears). `startPollingIfNeeded()`
    /// resumes it on the next appearance.
    func stopPolling() {
        pollTask?.cancel()
        pollTask = nil
    }

    // MARK: Errors

    private static func message(for error: any Error, fallback: String) -> String {
        switch error {
        case APIError.network:
            return "Can't reach ATTREQ. Check your connection."
        case let APIError.http(_, body):
            // FastAPI error bodies carry a human-readable string `detail`
            // (e.g. "Only JPG and PNG images are supported").
            if let object = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
               let detail = object["detail"] as? String,
               !detail.isEmpty {
                return detail
            }
            return fallback
        default:
            return fallback
        }
    }
}
