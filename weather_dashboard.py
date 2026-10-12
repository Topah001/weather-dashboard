"""Fetch and display current weather from the no-key Open-Meteo APIs."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TIMEOUT_SECONDS = 10
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
     95: "Thunderstorm",
     96: "Thunderstorm with slight hail",
     99: "Thunderstorm with heavy hail",
}


class WeatherError(RuntimeError):
     """A useful, user-facing weather lookup or API error."""


def describe_weather_code(code: int) -> str:
     return WEATHER_CODES.get(code, "Unknown conditions")


def format_weather(place: dict[str, Any], current: dict[str, Any]) -> str:
     """Format a geocoding result and Open-Meteo current-conditions object."""
     try:
         name = str(place["name"]).strip()
         region = str(place.get("admin1") or "").strip()
         country = str(place.get("country") or "").strip()
         temperature = float(current["temperature_2m"])
         apparent = float(current["apparent_temperature"])
         humidity = int(current["relative_humidity_2m"])
         wind = float(current["wind_speed_10m"])
         code = int(current["weather_code"])
     except (KeyError, TypeError, ValueError) as exc:
         raise WeatherError("The weather service returned incomplete or invalid current conditions.") from exc
     if not name:
         raise WeatherError("The weather service returned a location without a name.")
     location = ", ".join(part for part in (name, region, country) if part)
     return (
         f"Current weather for {location}\n"
         f"Conditions: {describe_weather_code(code)}\n"
         f"Temperature: {temperature:.1f} °C (feels like {apparent:.1f} °C)\n"
         f"Humidity: {humidity}%\n"
         f"Wind: {wind:.1f} km/h"
     )


def fetch_json(url: str, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
     request = Request(url, headers={"User-Agent": "WeatherDashboard/1.0"})
     try:
         with urlopen(request, timeout=timeout) as response:
             payload = json.loads(response.read().decode("utf-8"))
     except HTTPError as exc:
         raise WeatherError(f"Weather service returned HTTP {exc.code}.") from exc
     except (URLError, TimeoutError, OSError) as exc:
         if isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError):
             message = "The request timed out."
         elif isinstance(exc, TimeoutError):
             message = "The request timed out."
         else:
             message = "Could not connect to the weather service. Check your internet connection."
         raise WeatherError(message) from exc
     except (UnicodeDecodeError, json.JSONDecodeError) as exc:
         raise WeatherError("The weather service returned an invalid response.") from exc
     if not isinstance(payload, dict):
         raise WeatherError("The weather service returned an invalid response.")
     return payload


def get_weather(location: str) -> str:
     location = location.strip()
     if not location:
         raise WeatherError("Enter a place name to look up.")
     geocode_url = GEOCODING_URL + "?" + urlencode(
         {"name": location, "count": 1, "language": "en", "format": "json"}
     )
     geocoding = fetch_json(geocode_url)
     results = geocoding.get("results")
     if not isinstance(results, list) or not results:
         raise WeatherError(f"No matching location found for {location!r}. Check the spelling and try again.")
     place = results[0]
     try:
         latitude, longitude = float(place["latitude"]), float(place["longitude"])
     except (KeyError, TypeError, ValueError) as exc:
         raise WeatherError("The location service returned invalid coordinates.") from exc
     forecast_url = FORECAST_URL + "?" + urlencode(
         {
             "latitude": latitude,
             "longitude": longitude,
             "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
             "timezone": "auto",
         }
     )
     forecast = fetch_json(forecast_url)
     current = forecast.get("current")
     if not isinstance(current, dict):
         raise WeatherError("The forecast service did not return current weather conditions.")
     return format_weather(place, current)


def main(argv: list[str] | None = None) -> int:
     parser = argparse.ArgumentParser(description=__doc__)
     parser.add_argument("location", nargs="?", help="place name (for example, Reykjavik)")
     args = parser.parse_args(argv)
     location = args.location or input("Enter a location: ")
     try:
         print(get_weather(location))
     except WeatherError as exc:
         print(f"Weather lookup failed: {exc}", file=sys.stderr)
         return 2
     return 0


if __name__ == "__main__":
     raise SystemExit(main())
