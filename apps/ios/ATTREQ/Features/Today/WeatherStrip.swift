//
//  WeatherStrip.swift
//  ATTREQ
//
//  Weather strip (M4, artboard 05). Pixel source:
//  assets/design/ios-redesign-v2/attreq-app.jsx → ATTREQWeatherStrip.
//  Surface card radius 14, 11v/14h padding: location icon + city on the left;
//  display-20 temperature + 1pt divider + mono condition on the right.
//
//  Degrades gracefully when the backend runs keyless (no OPENWEATHER_API_KEY):
//  `weather == nil` renders the city with "—" for temperature and condition.
//

import SwiftUI

/// Compact weather summary strip shown under the Today header.
struct WeatherStrip: View {
    /// City from the user profile (`saved_city` / `location`), not the weather payload.
    let city: String?
    let weather: WeatherData?

    private static let shape = RoundedRectangle(cornerRadius: 14, style: .continuous)

    private var temperatureText: String {
        guard let weather else { return "—" }
        return "\(Int(weather.temp.rounded()))°"
    }

    private var cityText: String {
        guard let city, !city.isEmpty else { return "—" }
        return city
    }

    var body: some View {
        HStack(alignment: .center) {
            HStack(spacing: 6) {
                AttreqIcon.location.view(size: 12, color: Theme.t3)
                Text(cityText)
                    .font(.attreqBody(13))
                    .foregroundStyle(Theme.t2)
                    .lineLimit(1)
            }

            Spacer(minLength: 12)

            HStack(spacing: 8) {
                Text(temperatureText)
                    .font(.attreqDisplay(20, weight: .semiBold))
                    .foregroundStyle(Theme.text)
                Rectangle()
                    .fill(Theme.border)
                    .frame(width: 1, height: 14)
                MonoLabel(weather?.condition ?? "—")
                    .lineLimit(1)
            }
        }
        .padding(.vertical, 11)
        .padding(.horizontal, 14)
        .background(Self.shape.fill(Theme.surface))
        .overlay(Self.shape.strokeBorder(Theme.border, lineWidth: 1))
        .accessibilityElement(children: .combine)
    }
}

// MARK: - Previews

#Preview("Weather strip") {
    VStack(spacing: 14) {
        WeatherStrip(
            city: "Milan, IT",
            weather: WeatherData(
                temp: 22.3,
                feelsLike: 21.0,
                condition: "Partly cloudy",
                description: "scattered clouds",
                humidity: 58,
                windSpeed: 3.4,
                icon: "02d"
            )
        )
        // Keyless / degraded: no weather payload.
        WeatherStrip(city: "Milan, IT", weather: nil)
        // No profile city either.
        WeatherStrip(city: nil, weather: nil)
    }
    .padding(24)
    .background(Theme.bg)
}
