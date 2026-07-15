import Foundation

/// Type-safe representation of arbitrary JSON, used for backend fields typed as
/// `dict[str, Any]` (e.g. `StyleDnaPhoto.perPhotoExtraction`, `Outfit.weatherContext`).
///
/// Key handling: on the modern Foundation JSON coders (iOS 17+),
/// `.convertFromSnakeCase`/`.convertToSnakeCase` do NOT rewrite the String keys
/// of `[String: JSONValue]` dictionaries — keys pass through verbatim (e.g.
/// `"quality_reason"` stays `"quality_reason"`). Look up and build keys in the
/// backend's snake_case form. Pinned by ModelDecodingTests and
/// StyleDnaRepositoryTests.
enum JSONValue: Codable, Sendable, Equatable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let bool = try? container.decode(Bool.self) {
            self = .bool(bool)
        } else if let number = try? container.decode(Double.self) {
            self = .number(number)
        } else if let string = try? container.decode(String.self) {
            self = .string(string)
        } else if let array = try? container.decode([JSONValue].self) {
            self = .array(array)
        } else if let object = try? container.decode([String: JSONValue].self) {
            self = .object(object)
        } else {
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Value is not valid JSON"
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value): try container.encode(value)
        case .number(let value): try container.encode(value)
        case .bool(let value): try container.encode(value)
        case .object(let value): try container.encode(value)
        case .array(let value): try container.encode(value)
        case .null: try container.encodeNil()
        }
    }
}
