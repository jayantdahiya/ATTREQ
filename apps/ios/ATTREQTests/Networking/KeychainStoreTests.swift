import Foundation
import Testing
@testable import ATTREQ

struct KeychainStoreTests {
    private func makeStore() -> KeychainStore {
        KeychainStore(service: "com.attreq.ios.tests.keychain.\(UUID().uuidString)")
    }

    @Test func roundtripOverwriteAndDelete() throws {
        let store = makeStore()
        defer { try? store.delete("token") }

        let missing = try store.get("token")
        #expect(missing == nil)

        try store.set("value-1", for: "token")
        let stored = try store.get("token")
        #expect(stored == "value-1")

        // Overwrite must replace, not fail on the existing item.
        try store.set("value-2", for: "token")
        let overwritten = try store.get("token")
        #expect(overwritten == "value-2")

        try store.delete("token")
        let deleted = try store.get("token")
        #expect(deleted == nil)

        // Deleting a missing key is not an error.
        try store.delete("token")
    }

    @Test func keysAreIndependent() throws {
        let store = makeStore()
        defer {
            try? store.delete("auth.access_token")
            try? store.delete("auth.refresh_token")
        }

        try store.set("access-abc", for: "auth.access_token")
        try store.set("refresh-xyz", for: "auth.refresh_token")

        let access = try store.get("auth.access_token")
        let refresh = try store.get("auth.refresh_token")
        #expect(access == "access-abc")
        #expect(refresh == "refresh-xyz")

        try store.delete("auth.access_token")
        let accessAfterDelete = try store.get("auth.access_token")
        let refreshUntouched = try store.get("auth.refresh_token")
        #expect(accessAfterDelete == nil)
        #expect(refreshUntouched == "refresh-xyz")
    }

    @Test func servicesAreIsolated() throws {
        let storeA = makeStore()
        let storeB = makeStore()
        defer {
            try? storeA.delete("token")
            try? storeB.delete("token")
        }

        try storeA.set("only-in-a", for: "token")

        let fromB = try storeB.get("token")
        #expect(fromB == nil)
        let fromA = try storeA.get("token")
        #expect(fromA == "only-in-a")
    }

    @Test func handlesNonASCIIValues() throws {
        let store = makeStore()
        defer { try? store.delete("token") }

        let jwtish = "eyJhbGciOiJIUzI1NiJ9.tøkén-値-🔐"
        try store.set(jwtish, for: "token")
        let roundtripped = try store.get("token")
        #expect(roundtripped == jwtish)
    }
}
