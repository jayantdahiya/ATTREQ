import Testing
@testable import ATTREQ

struct SmokeTests {
    @Test func designSystemTokensResolve() {
        #expect(GarmentTone.allCases.count == 5)
        #expect(AttreqTab.allCases.count == 4)
    }
}
