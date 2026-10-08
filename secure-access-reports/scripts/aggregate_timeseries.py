#!/usr/bin/env python3
"""Roll hourly Secure Access time-series data up to daily totals.

Accepts the raw output of get_requests_by_timerange / get_requests_by_hour
(or their *_type variants) in any of these shapes:
  {"result": "<json string>"}   (MCP wrapper, as saved by the client)
  {"data": [...]}                (API body)
  [...]                          (bare list)

Usage:
    python aggregate_timeseries.py raw.json [raw2.json ...] [--merge report.json]

Several files (e.g. one per week) are combined. Prints the daily series as JSON.
With --merge, writes it into report.json under trend.series.
"""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from datetime import datetime, timezone


def load_points(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        obj = json.load(f)
    if isinstance(obj, dict) and isinstance(obj.get("result"), str):
        obj = json.loads(obj["result"])
    if isinstance(obj, dict):
        obj = obj.get("data", [])
    return obj if isinstance(obj, list) else []


def day_of(p: dict) -> str | None:
    if p.get("date"):
        return str(p["date"])[:10]
    ts = p.get("timestamp")
    if ts:
        return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--merge", help="report.json to update with trend.series")
    a = ap.parse_args()

    seen: set = set()
    days: dict[str, dict] = {}
    for path in a.files:
        for p in load_points(path):
            key = (p.get("timestamp"), p.get("date"), p.get("time"))
            if key in seen:
                continue
            seen.add(key)
            d = day_of(p)
            if not d:
                continue
            c = p.get("counts") or {}
            row = days.setdefault(d, {"date": d, "total": 0, "blocked": 0, "allowed": 0})
            row["total"] += int(c.get("requests", p.get("count", 0)) or 0)
            row["blocked"] += int(c.get("blockedrequests", 0) or 0)
            row["allowed"] += int(c.get("allowedrequests", 0) or 0)

    series = list(OrderedDict(sorted(days.items())).values())
    if a.merge:
        with open(a.merge, encoding="utf-8") as f:
            rep = json.load(f)
        rep.setdefault("trend", {})["series"] = series
        with open(a.merge, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        print(f"Merged {len(series)} days into {a.merge}")
    else:
        print(json.dumps(series, indent=1))


if __name__ == "__main__":
    main()
