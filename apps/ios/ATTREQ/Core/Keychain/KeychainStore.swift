import Foundation
import Security

/// Thin wrapper over the iOS keychain for string secrets (`kSecClassGenericPassword`).
/// Works in the simulator and in host-app unit tests without extra entitlements.
struct KeychainStore: Sendable {
    enum KeychainError: Error {
        case unexpectedStatus(OSStatus)
        case invalidData
    }

    let service: String

    init(service: String = "com.attreq.ios") {
        self.service = service
    }

    /// Returns the stored value for `key`, or `nil` if absent.
    func get(_ key: String) throws -> String? {
        var query = baseQuery(for: key)
        query[kSecReturnData as String] = kCFBooleanTrue
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        switch status {
        case errSecSuccess:
            guard let data = result as? Data, let value = String(data: data, encoding: .utf8) else {
                throw KeychainError.invalidData
            }
            return value
        case errSecItemNotFound:
            return nil
        default:
            throw KeychainError.unexpectedStatus(status)
        }
    }

    /// Stores `value` under `key`, overwriting any existing item.
    /// Items are device-only (never migrated to a new device via backup) and
    /// readable after first unlock, so background refreshes keep working.
    func set(_ value: String, for key: String) throws {
        let data = Data(value.utf8)
        let query = baseQuery(for: key)

        // Accessibility is asserted on update too, so items created before this
        // policy (or with a different one) are migrated on their next write.
        let update: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]
        let updateStatus = SecItemUpdate(query as CFDictionary, update as CFDictionary)
        switch updateStatus {
        case errSecSuccess:
            return
        case errSecItemNotFound:
            var add = query
            add[kSecValueData as String] = data
            add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
            let addStatus = SecItemAdd(add as CFDictionary, nil)
            guard addStatus == errSecSuccess else {
                throw KeychainError.unexpectedStatus(addStatus)
            }
        default:
            throw KeychainError.unexpectedStatus(updateStatus)
        }
    }

    /// Removes the item for `key`. Missing items are not an error.
    func delete(_ key: String) throws {
        let status = SecItemDelete(baseQuery(for: key) as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.unexpectedStatus(status)
        }
    }

    private func baseQuery(for key: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
        ]
    }
}
