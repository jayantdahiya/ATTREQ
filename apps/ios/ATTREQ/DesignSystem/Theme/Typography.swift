import SwiftUI

/// Weights available in the bundled Cormorant Garamond serif family.
public enum AttreqSerifWeight {
    case regular, medium, semiBold

    fileprivate func postScriptName(italic: Bool) -> String {
        switch (self, italic) {
        case (.regular, false): "CormorantGaramond-Regular"
        case (.medium, false): "CormorantGaramond-Medium"
        case (.semiBold, false): "CormorantGaramond-SemiBold"
        case (.regular, true): "CormorantGaramond-Italic"
        case (.medium, true): "CormorantGaramond-MediumItalic"
        case (.semiBold, true): "CormorantGaramond-SemiBoldItalic"
        }
    }
}

/// Weights available in the bundled DM Sans family.
public enum AttreqSansWeight {
    case light, regular, medium, semiBold

    fileprivate var postScriptName: String {
        switch self {
        case .light: "DMSans-Light"
        case .regular: "DMSans-Regular"
        case .medium: "DMSans-Medium"
        case .semiBold: "DMSans-SemiBold"
        }
    }
}

/// Weights available in the bundled IBM Plex Mono family.
public enum AttreqMonoWeight {
    case regular, medium

    fileprivate var postScriptName: String {
        switch self {
        case .regular: "IBMPlexMono-Regular"
        case .medium: "IBMPlexMono-Medium"
        }
    }
}

public extension Font {
    /// Cormorant Garamond — display/headline serif (`ATTREQ_F.display`).
    static func attreqDisplay(
        _ size: CGFloat,
        weight: AttreqSerifWeight = .semiBold,
        italic: Bool = false
    ) -> Font {
        .custom(weight.postScriptName(italic: italic), size: size)
    }

    /// DM Sans — body/UI sans (`ATTREQ_F.body`).
    static func attreqBody(
        _ size: CGFloat,
        weight: AttreqSansWeight = .regular
    ) -> Font {
        .custom(weight.postScriptName, size: size)
    }

    /// IBM Plex Mono — labels/metadata mono (`ATTREQ_F.mono`).
    static func attreqMono(
        _ size: CGFloat,
        weight: AttreqMonoWeight = .regular
    ) -> Font {
        .custom(weight.postScriptName, size: size)
    }
}
