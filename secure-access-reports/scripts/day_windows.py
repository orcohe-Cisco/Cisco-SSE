#!/usr/bin/env python3
"""Print time windows as epoch-millisecond from/to pairs for the reports API.

The Secure Access reports API accepts epoch milliseconds for from/to, so one
call per window gives consistent per-day / per-hour figures.

Usage:
    python day_windows.py --days 30 [--tz Asia/Jerusalem] [--bucket day|week|hours] [--size 2]
                          [--include-today] [--compact]

  --bucket day    one window per calendar day (default)
  --bucket week   7-day windows (for 90-day trends)
  --bucket hours  windows of --size hours (1, 2, 3, 4, 6, 8, 12) covering every hour of every day

Output: JSON list of {"date": "YYYY-MM-DD", "hour": H, "from": ms, "to": ms}
("hour" only for --bucket hours). --compact prints one window per line.
By default the current (partial) day is excluded.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, time, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--tz", default="UTC")
    ap.add_argument("--bucket", choices=["day", "week", "hours"], default="day")
    ap.add_argument("--size", type=int, default=1, help="hours per bucket with --bucket hours")
    ap.add_argument("--include-today", action="store_true")
    ap.add_argument("--compact", action="store_true")
    a = ap.parse_args()
    if a.bucket == "hours" and 24 % a.size:
        ap.error("--size must divide 24")

    tz = ZoneInfo(a.tz) if ZoneInfo else None
    now = datetime.now(tz)
    now_ms = int(now.timestamp() * 1000)
    end_day = now.date() + timedelta(days=1) if a.include_today else now.date()
    start_day = end_day - timedelta(days=a.days)

    out = []
    if a.bucket == "hours":
        d = start_day
        while d < end_day:
            for h in range(0, 24, a.size):
                f = datetime.combine(d, time(h), tz)
                t = f + timedelta(hours=a.size)
                f_ms, t_ms = int(f.timestamp() * 1000), min(int(t.timestamp() * 1000), now_ms)
                if f_ms < t_ms:
                    out.append({"date": d.isoformat(), "hour": h, "from": f_ms, "to": t_ms})
            d += timedelta(days=1)
    else:
        step = timedelta(days=7 if a.bucket == "week" else 1)
        d = start_day
        while d < end_day:
            nxt = min(d + step, end_day)
            f = datetime.combine(d, time.min, tz)
            t = datetime.combine(nxt, time.min, tz)
            out.append({"date": d.isoformat(), "from": int(f.timestamp() * 1000), "to": min(int(t.timestamp() * 1000), now_ms)})
            d = nxt

    if a.compact:
        print("[\n" + ",\n".join(json.dumps(w) for w in out) + "\n]")
    else:
        print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
