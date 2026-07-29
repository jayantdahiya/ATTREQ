import Testing
@testable import ATTREQ

struct SmokeTests {
    @Test func designSystemTokensResolve() {
        #expect(GarmentTone.allCases.count == 5)
        // RI-7 added the Stats tab (today/wardrobe/stats/history/profile).
        #expect(AttreqTab.allCases.count == 5)
    }
}
