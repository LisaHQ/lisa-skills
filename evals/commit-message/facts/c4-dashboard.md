# Fact sheet: c4-dashboard

Request: "Write a commit message for these changes." Default `auto`.

## Repository state

```text
 M requirements.txt        two purposes in one file: adds httpx==0.27.0 (new runtime dependency)
                           and upgrades flask 3.0.2 → 3.0.3
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
- Flask moves from 3.0.2 to 3.0.3, a routine patch upgrade. Nothing in the
  repository shows a defect, a vulnerability, or a reason for it.

## Core points

1. Group by purpose, not by file: httpx stays with the forecast feat, and the
   Flask upgrade gets its own `build` bullet.
2. A feat for the forecast client that keeps the new httpx dependency.
3. The integration gap: the dashboard does not use the client yet.
4. The settings gap: `forecast_timeout` and `city` are not read.
5. A recommendation to commit the Flask upgrade separately is welcome.

Example of a strong message:

```text
Add a weather forecast client

- feat(weather): Add `fetch_forecast` to read tomorrow's forecast for a city
  through httpx, now a runtime dependency (0.27.0). Nothing calls it yet, and
  the new [weather] settings are not read.
- build: Upgrade Flask from 3.0.2 to 3.0.3.
```

## Traps

- Omitting the httpx dependency → major.
- Omitting the Flask upgrade → major.
- Typing the Flask upgrade as fix, or calling it a security or vulnerability
  fix → major (invented; a version change alone does not establish a defect).
- Citing release-note contents for Flask 3.0.3 (fixes, security) that the
  repository does not show → major (invented).
- Claiming the dashboard shows a weather tile or forecast → major.
- Claiming the timeout or city is configurable through settings → major.
- Folding the Flask upgrade into the forecast bullet → C deduction.
- Typing the Flask upgrade as chore instead of build → C minor.
- Separate chore bullet for the settings is acceptable if it says nothing
  reads them.

## Judge notes

- `git diff HEAD -- requirements.txt` shows `-flask==3.0.2`,
  `+flask==3.0.3`, and `+httpx==0.27.0`.
- An attribution trailer such as `Co-Authored-By:` is neutral.
