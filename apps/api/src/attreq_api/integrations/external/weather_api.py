"""OpenWeatherMap API service for ATTREQ backend."""

import logging
from typing import Any

import httpx

from attreq_api.config.settings import settings
from attreq_api.services.cache.redis_client import redis_cache

logger = logging.getLogger(__name__)


class WeatherAPIService:
    """Service for fetching weather data from OpenWeatherMap API."""

    def __init__(self):
        """Initialize weather API service."""
        self.api_key = settings.openweather_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.cache_ttl = 3600  # 1 hour in seconds

    async def get_current_weather(self, lat: float, lon: float) -> dict[str, Any]:
        """Fetch current weather by coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Weather data dict with keys: temp, condition, description, humidity, wind_speed
        """
        # Check cache first
        cache_key = f"weather:{lat}:{lon}"
        cached_weather = await redis_cache.get(cache_key)

        if cached_weather:
            logger.info(f"Weather data retrieved from cache for {lat},{lon}")
            return cached_weather

        # Fetch from API
        weather_data = await self._fetch_weather(lat=lat, lon=lon)

        # Cache the result
        if weather_data:
            await redis_cache.set(cache_key, weather_data, ttl=self.cache_ttl)

        return weather_data

    async def get_weather_by_city(self, city: str) -> dict[str, Any]:
        """Fetch current weather by city name.

        Args:
            city: City name (e.g., "London", "New York")

        Returns:
            Weather data dict with keys: temp, condition, description, humidity, wind_speed
        """
        # Check cache first
        cache_key = f"weather:city:{city.lower()}"
        cached_weather = await redis_cache.get(cache_key)

        if cached_weather:
            logger.info(f"Weather data retrieved from cache for {city}")
            return cached_weather

        # Fetch from API
        weather_data = await self._fetch_weather(city=city)

        # Cache the result
        if weather_data:
            await redis_cache.set(cache_key, weather_data, ttl=self.cache_ttl)

        return weather_data

    async def _fetch_weather(
        self, lat: float | None = None, lon: float | None = None, city: str | None = None
    ) -> dict[str, Any]:
        """Internal method to fetch weather from OpenWeatherMap API.

        Args:
            lat: Latitude (optional)
            lon: Longitude (optional)
            city: City name (optional)

        Returns:
            Standardized weather data dict
        """
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured, using default weather")
            return self._get_default_weather()

        try:
            # Build query parameters
            params = {
                "appid": self.api_key,
                "units": "metric",  # Celsius
            }

            if lat is not None and lon is not None:
                params["lat"] = lat
                params["lon"] = lon
            elif city:
                params["q"] = city
            else:
                logger.error("Either lat/lon or city must be provided")
                return self._get_default_weather()

            # Make API request with timeout and retries
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                # Parse and standardize response
                weather_data = {
                    "temp": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "condition": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "icon": data["weather"][0]["icon"],
                }

                logger.info(
                    f"Weather fetched: {weather_data['temp']}°C, {weather_data['condition']}"
                )
                return weather_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching weather: {e.response.status_code} - {e.response.text}"
            )
            return self._get_default_weather()
        except httpx.TimeoutException:
            logger.error("Timeout fetching weather from OpenWeatherMap")
            return self._get_default_weather()
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return self._get_default_weather()

    def _get_default_weather(self) -> dict[str, Any]:
        """Get default weather data as fallback.

        Returns:
            Default weather data (moderate temperature, clear conditions)
        """
        return {
            "temp": 20.0,
            "feels_like": 20.0,
            "condition": "Clear",
            "description": "clear sky",
            "humidity": 50,
            "wind_speed": 5.0,
            "icon": "01d",
        }


# Global instance
weather_service = WeatherAPIService()
