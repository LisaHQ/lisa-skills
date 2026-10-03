"""Scenario s3: dataset folder 'hanoi-air-quality' (create mode, materials)."""
import csv
import io
import math
import random
from datetime import datetime, timedelta

from fixture import w

ROOT = "s3-hanoi-air-quality"

STATIONS = [
    ("HN01", "Hoan Kiem Lake", "Hoan Kiem", 21.0285, 105.8522, 12, "EAN-200", "2023-06-01"),
    ("HN02", "My Dinh Stadium", "Nam Tu Liem", 21.0205, 105.7637, 9, "EAN-200", "2023-06-01"),
    ("HN03", "Cau Giay Park", "Cau Giay", 21.0313, 105.7967, 11, "EAN-200", "2023-07-15"),
    ("HN04", "Long Bien Bridge", "Long Bien", 21.0434, 105.8601, 8, "EAN-210", "2023-09-01"),
    ("HN05", "Ha Dong Market", "Ha Dong", 20.9714, 105.7788, 7, "EAN-210", "2023-11-20"),
]


def _csv(rows, header):
    buf = io.StringIO()
    wr = csv.writer(buf, lineterminator="\n")
    wr.writerow(header)
    wr.writerows(rows)
    return buf.getvalue()


def build(base):
    r = base / ROOT
    rnd = random.Random(20240405)
    w(r / "raw/stations.csv", _csv(STATIONS, [
        "station_id", "name", "district", "lat", "lon", "elevation_m", "sensor_model", "installed_on"]))

    month_base = {1: 72.0, 2: 58.0, 3: 46.0}
    hourly = {}
    for month, days in ((1, 31), (2, 29), (3, 31)):
        rows = []
        start = datetime(2024, month, 1)
        for d in range(days):
            for h in range(24):
                ts = start + timedelta(days=d, hours=h)
                for sid, *_ in STATIONS:
                    diurnal = 1 + 0.35 * math.cos((h - 7) / 24 * 2 * math.pi)
                    pm25 = max(3.0, rnd.gauss(month_base[month] * diurnal, 12))
                    pm10 = pm25 * rnd.uniform(1.3, 1.8)
                    temp = rnd.gauss({1: 17, 2: 19, 3: 23}[month] + 4 * math.sin((h - 9) / 24 * 2 * math.pi), 1.5)
                    rh = min(100, max(35, rnd.gauss(80, 8)))
                    flag = 0
                    roll = rnd.random()
                    if roll < 0.015:
                        flag = 1
                    elif roll < 0.020:
                        flag = 2
                        pm25 = rnd.choice([1450.0, -5.0])
                    elif roll < 0.026:
                        flag = 3
                    row = [sid, ts.strftime("%Y-%m-%d %H:%M"), f"{pm25:.1f}", f"{pm10:.1f}",
                           f"{temp:.1f}", f"{rh:.0f}", flag]
                    if rnd.random() < 0.02:
                        col = rnd.choice([2, 3, 4, 5])
                        row[col] = "-999"
                    rows.append(row)
                    hourly.setdefault((sid, ts.date()), []).append(row)
        w(r / f"raw/pm25_hourly_2024-{month:02d}.csv", _csv(rows, [
            "station_id", "timestamp_local", "pm25_ugm3", "pm10_ugm3", "temp_c", "rh_pct", "qc_flag"]))

    w(r / "scripts/aggregate_daily.py", '''\
"""Build processed/daily_mean_2024Q1.csv from the raw hourly files.

Rules:
- Use only rows with qc_flag == 0.
- Treat -999 as missing.
- A daily mean needs at least 18 valid hourly values; otherwise the cell is empty.
- Days follow local time (ICT, UTC+07:00), the same clock as timestamp_local.

Run from the dataset folder:  python scripts/aggregate_daily.py
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_VALID_HOURS = 18
MISSING = -999.0


def main() -> None:
    values = defaultdict(lambda: {"pm25": [], "pm10": []})
    days = set()
    for path in sorted((ROOT / "raw").glob("pm25_hourly_2024-*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = (row["station_id"], row["timestamp_local"][:10])
                days.add(key)
                if row["qc_flag"] != "0":
                    continue
                for col, name in (("pm25_ugm3", "pm25"), ("pm10_ugm3", "pm10")):
                    value = float(row[col])
                    if value != MISSING:
                        values[key][name].append(value)

    out = ROOT / "processed" / "daily_mean_2024Q1.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\\n")
        writer.writerow(["station_id", "date", "pm25_mean_ugm3", "pm10_mean_ugm3", "pm25_valid_hours"])
        for key in sorted(days):
            pm25, pm10 = values[key]["pm25"], values[key]["pm10"]
            mean = lambda xs: f"{sum(xs) / len(xs):.1f}" if len(xs) >= MIN_VALID_HOURS else ""
            writer.writerow([*key, mean(pm25), mean(pm10), len(pm25)])


if __name__ == "__main__":
    main()
''')
    # Build the processed file with the same rules as the script.
    out_rows = []
    for (sid, day), rows in sorted(hourly.items()):
        pm25 = [float(x[2]) for x in rows if x[6] == 0 and x[2] != "-999"]
        pm10 = [float(x[3]) for x in rows if x[6] == 0 and x[3] != "-999"]
        mean = lambda xs: f"{sum(xs) / len(xs):.1f}" if len(xs) >= 18 else ""
        out_rows.append([sid, day.isoformat(), mean(pm25), mean(pm10), len(pm25)])
    w(r / "processed/daily_mean_2024Q1.csv", _csv(out_rows, [
        "station_id", "date", "pm25_mean_ugm3", "pm10_mean_ugm3", "pm25_valid_hours"]))

    w(r / "SOURCE.md", '''\
# Source notes

- Collected by: Example Air Network (EAN), a volunteer network of low-cost sensors.
- Period: 2024-01-01 00:00 to 2024-03-31 23:00, hourly, local time (ICT, UTC+07:00).
- Sensors: EAN-200 and EAN-210 optical particle counters. Each sensor is
  co-located with a reference monitor for one week per quarter. Exported PM2.5
  values already include the correction `pm25 = 0.72 * raw + 1.8`.
- Contact: data@example.invalid

## License

Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0):
https://creativecommons.org/licenses/by-nc/4.0/

## How to cite

Example Air Network (2024). *Hanoi PM2.5 hourly observations, Q1 2024* (v1.1).

## Versions

- v1.1 (2024-04-15): removed duplicate February rows for HN03; re-ran the daily aggregation.
- v1.0 (2024-04-05): first release.
''')
    w(r / "QC_FLAGS.txt", '''\
qc_flag values
0  valid
1  sensor warm-up after a power loss (first hour back online)
2  value outside the plausible range (PM2.5 < 0 or > 1000 ug/m3)
3  excluded manually (maintenance or calibration visit)

Missing measurements are written as -999 in any numeric column.
''')
