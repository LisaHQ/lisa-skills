# Fact sheet: c4-dashboard

Request: "Write a commit message for these changes." Default `auto`.

## Repository state

```text
 M requirements.txt        adds httpx==0.27.0 (new runtime dependency)
 M config/settings.toml    adds [weather] city = "Hanoi", forecast_timeout = 10
?? app/weather.py          new fetch_forecast(city, client=None) using httpx, hard-coded timeout 5.0
?? tests/                  tests/test_weather.py with a fake client
```

## Correct selection

Working-tree view for every file, including both untracked additions.

## Net change and gaps

- `app/weather.py` adds `fetch_forecast(city)`, which calls
  `https://api.example.invalid/v1/forecast` through httpx and returns
  tomorrow's high, low, and summary. Nothing imports it: `app/main.py` still
  renders only the clock and news tiles.
- httpx 0.27.0 becomes a runtime dependency.
- The new `[weather]` settings are read by nothing; `fetch_forecast` uses a
  hard-coded 5-second timeout and takes the city as an argument.
- A test covers the response mapping with a fake client.

## Core points

1. A feat for the forecast client that keeps the new httpx dependency.
2. The integration gap: the dashboard does not use the client yet.
3. The settings gap: `forecast_timeout` and `city` are not read.

Example of a strong message:

```text
Add a weather forecast client

- feat(weather): Add `fetch_forecast` to read tomorrow's forecast for a city
  through httpx, now a runtime dependency (0.27.0). Nothing calls it yet, and
  the new [weather] settings are not read.
```

## Traps

- Omitting the httpx dependency → major.
- Claiming the dashboard shows a weather tile or forecast → major.
- Claiming the timeout or city is configurable through settings → major.
- Separate chore bullet for the settings is acceptable if it says nothing
  reads them.
