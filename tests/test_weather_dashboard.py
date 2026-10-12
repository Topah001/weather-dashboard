import unittest
from unittest.mock import patch
from urllib.error import URLError

from weather_dashboard import WeatherError, describe_weather_code, format_weather, get_weather


class WeatherFormattingTests(unittest.TestCase):
    def setUp(self):
        self.place = {"name": "Oslo", "admin1": "Oslo", "country": "Norway"}
        self.current = {
            "temperature_2m": 12.34,
            "apparent_temperature": 10.5,
            "relative_humidity_2m": 71,
            "wind_speed_10m": 8.26,
            "weather_code": 3,
        }

    def test_code_descriptions_include_unknown_fallback(self):
        self.assertEqual(describe_weather_code(0), "Clear sky")
        self.assertEqual(describe_weather_code(95), "Thunderstorm")
        self.assertEqual(describe_weather_code(999), "Unknown conditions")

    def test_formats_current_weather(self):
        output = format_weather(self.place, self.current)
        self.assertIn("Current weather for Oslo, Oslo, Norway", output)
        self.assertIn("Conditions: Overcast", output)
        self.assertIn("Temperature: 12.3 °C (feels like 10.5 °C)", output)
        self.assertIn("Humidity: 71%", output)
        self.assertIn("Wind: 8.3 km/h", output)

    def test_missing_weather_fields_raise_a_useful_error(self):
        with self.assertRaisesRegex(WeatherError, "incomplete or invalid"):
            format_weather(self.place, {})

    @patch("weather_dashboard.fetch_json")
    def test_unknown_location_does_not_request_forecast(self, fetch):
        fetch.return_value = {"results": []}
        with self.assertRaisesRegex(WeatherError, "No matching location"):
            get_weather("Nowhere")
        fetch.assert_called_once()

    @patch("weather_dashboard.fetch_json")
    def test_successful_lookup_uses_geocoded_coordinates(self, fetch):
        fetch.side_effect = [
            {"results": [self.place | {"latitude": 59.9, "longitude": 10.7}]},
            {"current": self.current},
        ]
        self.assertIn("Overcast", get_weather("Oslo"))
        self.assertEqual(fetch.call_count, 2)
        self.assertIn("latitude=59.9", fetch.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
