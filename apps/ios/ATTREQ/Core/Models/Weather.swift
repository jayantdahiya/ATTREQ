import Foundation

/// Mirrors backend `WeatherData` (`schemas/recommendation.py`) / TS `WeatherData`.
struct WeatherData: Codable, Sendable, Equatable {
    /// Temperature in Celsius.
    let temp: Double
    /// Feels-like temperature in Celsius.
    let feelsLike: Double
    /// Condition summary, e.g. `"Clear"`, `"Rain"`.
    let condition: String
    /// Detailed description, e.g. `"clear sky"`.
    let description: String
    /// Humidity percentage.
    let humidity: Int
    /// Wind speed in m/s.
    let windSpeed: Double
    /// Weather icon code, e.g. `"01d"`.
    let icon: String
}
