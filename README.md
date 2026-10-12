# Weather Dashboard

A small Python 3.13 command-line dashboard for current conditions by place name. It uses Open-Meteo's free geocoding and forecast APIs; no API key or third-party Python package is needed.

## Internet requirement

An internet connection is required when retrieving a location or its weather. Network requests have a 10-second timeout. Errors (including unknown locations, service/network failures, malformed responses, and timeouts) are reported in plain language.

## Run

```powershell
python weather_dashboard.py "Reykjavik"
```

Temperatures are shown in Celsius. Open-Meteo service/API availability and terms apply. No location history or other user data is saved.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Formatting and weather-code tests use no network.
