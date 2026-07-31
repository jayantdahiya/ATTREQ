//
//  ReminderScheduler.swift
//  ATTREQ
//
//  Local "daily reminder" notification for the Profile screen (M5-WP1).
//  RN counterpart: apps/mobile/src/lib/storage/notifications.ts
//  (enableDailyReminder / disableDailyReminder / getReminderStatus).
//
//  One repeating UNCalendarNotificationTrigger at 8:00 local time, with the
//  enabled flag persisted in UserDefaults so the Profile toggle reflects it
//  across launches. Permission handling: `.notDetermined` prompts inline;
//  `.denied` fails fast so the caller can flip the toggle back and show a hint.
//

import Foundation
import UserNotifications

/// Schedules and cancels the local daily-reminder notification.
@MainActor
final class ReminderScheduler {
    /// Stable identifier so re-enabling replaces (never duplicates) the request.
    static let requestIdentifier = "attreq.daily-reminder"
    private static let defaultsKey = "attreq.dailyReminderEnabled"

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    /// Last persisted toggle state (source of truth for the Profile toggle on load).
    var isEnabled: Bool {
        defaults.bool(forKey: Self.defaultsKey)
    }

    /// Reconciles the persisted flag against the system authorization status
    /// (the user may have revoked notifications in Settings while the flag
    /// still reads `true`). Returns the reconciled enabled state; if the flag
    /// was on but permission is now denied, persists `false` and cancels any
    /// stale pending request.
    func reconciledEnabled() async -> Bool {
        guard isEnabled else { return false }
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        if settings.authorizationStatus == .denied {
            disable()
            return false
        }
        return true
    }

    /// Requests notification permission (when undetermined) and schedules the
    /// repeating 8:00 local reminder.
    ///
    /// Returns `false` when permission is denied or scheduling fails — the
    /// caller flips the toggle back and surfaces an inline hint (the graceful
    /// permission-denied path required by the milestone).
    func enable() async -> Bool {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()
        switch settings.authorizationStatus {
        case .notDetermined:
            let granted = (try? await center.requestAuthorization(options: [.alert, .sound])) ?? false
            guard granted else {
                persist(false)
                return false
            }
        case .denied:
            persist(false)
            return false
        default:
            break // authorized / provisional / ephemeral — good to schedule.
        }

        let content = UNMutableNotificationContent()
        content.title = "Time to pick today's look"
        content.body = "A quiet minute with your wardrobe before the day decides for you."
        content.sound = .default

        var eight = DateComponents()
        eight.hour = 8
        eight.minute = 0
        let trigger = UNCalendarNotificationTrigger(dateMatching: eight, repeats: true)
        let request = UNNotificationRequest(
            identifier: Self.requestIdentifier,
            content: content,
            trigger: trigger
        )

        center.removePendingNotificationRequests(withIdentifiers: [Self.requestIdentifier])
        do {
            try await center.add(request)
        } catch {
            persist(false)
            return false
        }
        persist(true)
        return true
    }

    /// Cancels the pending reminder and persists the off state.
    func disable() {
        UNUserNotificationCenter.current()
            .removePendingNotificationRequests(withIdentifiers: [Self.requestIdentifier])
        persist(false)
    }

    private func persist(_ enabled: Bool) {
        defaults.set(enabled, forKey: Self.defaultsKey)
    }
}
