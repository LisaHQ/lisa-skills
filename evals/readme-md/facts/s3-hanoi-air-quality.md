# Fact sheet: s3-hanoi-air-quality

Request: "Write a README for this folder so collaborators know what's in it and how to use it." (create mode)
Kind: dataset folder. Reader: collaborators/analysts who will use the data.

## Ground truth

- Content: hourly PM2.5, PM10, temperature, relative humidity from **5 stations** (HN01-HN05) in Hanoi, from **2024-01-01 00:00 to 2024-03-31 23:00**, **local time ICT (UTC+07:00)**.
- Source: Example Air Network (EAN), volunteer **low-cost optical sensors** (EAN-200 / EAN-210). Co-located with a reference monitor one week per quarter; **exported PM2.5 already corrected** with `pm25 = 0.72 * raw + 1.8`.
- Files: `raw/stations.csv` (5 rows: station_id, name, district, lat, lon, elevation_m, sensor_model, installed_on); `raw/pm25_hourly_2024-01.csv` (3,720 rows), `-02.csv` (3,480 rows; 2024 is a leap year, 29 days), `-03.csv` (3,720 rows) = **10,920 hourly rows**; `processed/daily_mean_2024Q1.csv` (**455 rows** = 5 stations x 91 days); `scripts/aggregate_daily.py`; `SOURCE.md`; `QC_FLAGS.txt`.
- Hourly columns: station_id, timestamp_local (`YYYY-MM-DD HH:MM`), pm25_ugm3 (µg/m³), pm10_ugm3 (µg/m³), temp_c (°C), rh_pct (%), qc_flag.
- Missing values: **-999** in any numeric column.
- QC flags: 0 valid; 1 sensor warm-up after power loss; 2 out of plausible range (PM2.5 < 0 or > 1000); 3 excluded manually (maintenance/calibration).
- Derived counts (recounted from the files): qc_flag 0 = 10,617 rows, 1 = 178, 2 = 54, 3 = 71. **213 rows hold -999** (one cell each: pm25 48, pm10 46, temp 49, rh 70); **208 of them have qc_flag 0**, including all 48 missing PM2.5 values, so filtering on qc_flag alone does not remove -999. Every daily row has both means (minimum 20 valid hours), so the >= 18 rule empties no day in this release.
- Daily file columns: station_id, date, pm25_mean_ugm3, pm10_mean_ugm3, pm25_valid_hours. Rules: only qc_flag 0, -999 excluded, **mean requires >= 18 valid hours else empty**, days in local time. Regenerate with `python scripts/aggregate_daily.py` from the dataset folder (stdlib only).
- License: **CC BY-NC 4.0 (non-commercial)**. Citation: "Example Air Network (2024). Hanoi PM2.5 hourly observations, Q1 2024 (v1.1)." Version **v1.1** (2024-04-15: removed duplicate February HN03 rows; re-ran aggregation); v1.0 2024-04-05. Contact: data@example.invalid.

## Core points a strong README highlights

1. What/where/when in one line (5 stations, Hanoi, Q1 2024, hourly PM2.5/PM10 + weather).
2. File map with row counts; data dictionary with units.
3. Pitfalls: -999 missing code, qc_flag filtering, local time UTC+7, correction already applied, low-cost sensor limitations.
4. How to load/filter (snippet) and how the daily file is derived (>=18 valid hours).
5. License NC + citation + contact + version.

## Traps (judge explicitly)

- Wrong license (e.g., CC BY 4.0 without NC) or omitting the non-commercial restriction -> major.
- Saying timestamps are UTC -> major.
- Wrong missing code, wrong QC meanings, wrong units -> major each.
- Wrong row/station counts or date range -> major (minor if off by trivial rounding).
- Saying the correction must still be applied by users -> major.
- Invented methods (e.g., "reference-grade monitors", "WHO-certified"), invented DOI/URL -> major.
- Loading snippet that ignores -999 / qc_flag when presenting "clean" data -> minor.

## Judge notes

- Recount rows, flags, and `-999` cells yourself; run any code snippet against a copy of `scenario/` and check it handles every numeric column it claims to clean.
