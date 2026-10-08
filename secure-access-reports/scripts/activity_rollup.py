#!/usr/bin/env python3
"""Per-person connectivity and activity rollup from hourly Secure Access identity totals.

Input: one or more JSON / JSONL files with one record per time window, collected by
calling get_top_identities(from_time=<from ms>, to_time=<to ms>, limit=200) for each
window printed by `day_windows.py --bucket hours --size N`. Each record:

  {"from": 1791356400000, "to": 1791363600000,
   "result": "<raw tool output string>"}            # or
   "data": [ ...get_top_identities data list... ]   # or
   "rows": [["Win11v1", "anyconnect", 745], ...]    # compact: label, type, requests

No destinations or browsing data are used: only request totals per identity per window.

Usage:
  python activity_rollup.py windows.jsonl [more.jsonl] --tz Asia/Jerusalem
         [--people people.csv] [--workdays sun,mon,tue,wed,thu]
         [--types anyconnect,ztna_client,directory_user,roaming]
         [--merge report.json]

people.csv (optional) maps platform identities to people:
  identity,person,department,location
  Win11v1,Dana Levi,Finance,remote
  dana@contoso.com,Dana Levi,Finance,
  Haifa-Branch-1,Yossi Cohen,Sales,office
'location' overrides the default (roaming client / ZTNA client = remote; others = unknown).
Without the file, every identity of the selected types is reported on its own.

Definitions (per identity, then combined per person):
  connected  window requests >= --connected-min per hour
  baseline   median requests per window during night hours (--night, default 0-5)
  active     window requests >= max(--active-min per hour, --mult x baseline)
  signal     'background' when the identity's busiest daytime windows never exceed the
             active threshold: its traffic is indistinguishable from idle background,
             so active hours are reported as not measurable.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
REMOTE_TYPES = {"anyconnect", "roaming", "ztna_client", "mobile_device", "chromebook"}
USER_DRIVEN = {"directory_user", "ztna_client", "saml_user", "google_user"}


def load_records(paths):
    recs = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            txt = f.read().strip()
        if not txt:
            continue
        if txt[0] == "[":
            recs.extend(json.loads(txt))
        else:
            recs.extend(json.loads(line) for line in txt.splitlines() if line.strip())
    return recs


def rows_of(rec):
    if "rows" in rec:
        return [(str(r[0]), str(r[1]), float(r[2] or 0)) for r in rec["rows"]]
    data = rec.get("data")
    if data is None and "result" in rec:
        res = rec["result"]
        obj = json.loads(res) if isinstance(res, str) else res
        if isinstance(obj, dict) and isinstance(obj.get("result"), str):
            obj = json.loads(obj["result"])
        data = obj.get("data", []) if isinstance(obj, dict) else obj
    out = []
    for it in data or []:
        ident = it.get("identity") or {}
        typ = (ident.get("type") or {}).get("type", "")
        req = (it.get("counts") or {}).get("requests", it.get("requests", 0))
        out.append((str(ident.get("label", "")), typ, float(req or 0)))
    return out


def hhmm(minutes: float) -> str:
    minutes = int(round(minutes))
    return f"{(minutes // 60) % 24:02d}:{minutes % 60:02d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--tz", default="UTC")
    ap.add_argument("--people")
    ap.add_argument("--workdays", default="sun,mon,tue,wed,thu")
    ap.add_argument("--types", default="anyconnect,roaming,ztna_client,directory_user")
    ap.add_argument("--connected-min", type=float, default=5, help="requests per hour to count as connected")
    ap.add_argument("--active-min", type=float, default=30, help="requests per hour floor for active")
    ap.add_argument("--mult", type=float, default=3.0, help="active = this many times the night baseline")
    ap.add_argument("--night", default="0-5", help="local hours used for the idle baseline, inclusive")
    ap.add_argument("--merge")
    a = ap.parse_args()

    tz = ZoneInfo(a.tz) if ZoneInfo else None
    workdays = {d.strip().lower()[:3] for d in a.workdays.split(",") if d.strip()}
    types = {t.strip() for t in a.types.split(",") if t.strip()}
    n0, n1 = (int(x) for x in a.night.split("-"))

    recs = load_records(a.files)
    if not recs:
        raise SystemExit("no window records found")

    # window grid
    windows = {}
    for r in recs:
        f = int(r["from"])
        t = int(r["to"])
        start = datetime.fromtimestamp(f / 1000, tz)
        windows[f] = {"start": start, "hours": max((t - f) / 3_600_000, 1e-6), "rows": rows_of(r)}
    wkeys = sorted(windows)
    bucket_h = round(statistics.median(windows[k]["hours"] for k in wkeys), 2)
    dates = sorted({windows[k]["start"].date() for k in wkeys})

    # people mapping
    mapping = {}
    if a.people:
        with open(a.people, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                ident = (row.get("identity") or "").strip()
                if ident:
                    mapping[ident.lower()] = {
                        "person": (row.get("person") or ident).strip(),
                        "department": (row.get("department") or "").strip(),
                        "location": (row.get("location") or "").strip().lower(),
                    }

    # per identity series
    ident_type = {}
    series = defaultdict(dict)  # label -> {wkey: requests}
    for k in wkeys:
        for label, typ, req in windows[k]["rows"]:
            if not label:
                continue
            # with a people file only mapped identities are reported; otherwise the selected types
            include = (label.lower() in mapping) if mapping else (typ in types)
            if not include:
                continue
            key = f"{label}|{typ}"
            ident_type[key] = typ
            series[key][k] = series[key].get(k, 0) + req

    # thresholds per identity
    ident_info = {}
    for key, ser in series.items():
        label = key.split("|", 1)[0]
        rates = {k: ser.get(k, 0) / windows[k]["hours"] for k in wkeys}
        online = [v for v in rates.values() if v >= a.connected_min]
        # idle baseline = typical traffic while the device is ON overnight (nights it was off don't count)
        night_on = [rates[k] for k in wkeys if n0 <= windows[k]["start"].hour <= n1 and rates[k] >= a.connected_min]
        if len(night_on) >= 3:
            baseline = statistics.median(night_on)
        elif ident_type[key] in USER_DRIVEN or len(online) < 5:
            baseline = 0.0  # account / ZTNA traffic only exists when someone uses it
        else:
            baseline = sorted(online)[int(len(online) * 0.2)]  # quietest fifth of online windows
        act_thr = max(a.active_min, a.mult * baseline)
        day_rates = [rates[k] for k in wkeys if 7 <= windows[k]["start"].hour <= 19]
        flat = baseline * a.mult > a.active_min and not any(v >= act_thr for v in day_rates)
        signal = "background" if flat else "ok"
        m = mapping.get(label.lower(), {})
        loc = m.get("location") or ("remote" if ident_type[key] in REMOTE_TYPES else "unknown")
        ident_info[key] = {"label": label, "baseline": baseline, "active_thr": act_thr, "signal": signal, "location": loc,
                             "person": m.get("person") or label, "department": m.get("department", ""),
                             "type": ident_type[key]}

    # combine per person
    people = defaultdict(list)
    for label, info in ident_info.items():
        people[info["person"]].append(label)

    out_people = []
    for person, labels in people.items():
        days = {}
        signal_ok = any(ident_info[l]["signal"] == "ok" for l in labels)
        last_seen = None
        for d in dates:
            dk = [k for k in wkeys if windows[k]["start"].date() == d]
            conn_h = act_h = 0.0
            first = last = None
            locs = set()
            for k in dk:
                w = windows[k]
                conn = act = False
                for l in labels:
                    rate = series[l].get(k, 0) / w["hours"]
                    if rate >= a.connected_min:
                        conn = True
                        locs.add(ident_info[l]["location"])
                    if ident_info[l]["signal"] == "ok" and rate >= ident_info[l]["active_thr"]:
                        act = True
                if conn:
                    conn_h += w["hours"]
                    end = w["start"] + timedelta(hours=w["hours"])
                    last_seen = max(last_seen, end) if last_seen else end
                if act:
                    act_h += w["hours"]
                    s_min = w["start"].hour * 60 + w["start"].minute
                    first = s_min if first is None else min(first, s_min)
                    last = s_min + w["hours"] * 60 if last is None else max(last, s_min + w["hours"] * 60)
            if conn_h == 0:
                status = "none"
            else:
                where = "remote" if "remote" in locs else "office" if "office" in locs else "seen"
                status = f"{where}_active" if act_h > 0 else f"{where}_connected"
            days[d.isoformat()] = {
                "status": status, "connected_hours": round(conn_h, 1),
                "active_hours": round(act_h, 1) if signal_ok else None,
                "first": hhmm(first) if first is not None else None,
                "last": hhmm(last) if last is not None else None,
                "workday": DAY_NAMES[d.weekday()] in workdays,
            }

        wd = [v for v in days.values() if v["workday"]]
        nwd = [v for v in days.values() if not v["workday"]]
        act_days = [v for v in wd if (v["active_hours"] or 0) > 0]

        def avg_time(key):
            vals = [int(v[key][:2]) * 60 + int(v[key][3:]) for v in act_days if v[key]]
            return hhmm(sum(vals) / len(vals)) if vals else None

        metrics = {
            "workdays": len(wd),
            "days_connected": sum(1 for v in wd if v["status"] != "none"),
            "days_remote": sum(1 for v in wd if v["status"].startswith("remote")),
            "days_office": sum(1 for v in wd if v["status"].startswith("office")),
            "days_active": len(act_days) if signal_ok else None,
            "avg_connected_hours": round(statistics.mean([v["connected_hours"] for v in wd if v["connected_hours"]] or [0]), 1),
            "avg_active_hours": round(statistics.mean([v["active_hours"] for v in act_days]), 1) if act_days else (0 if signal_ok else None),
            "avg_first": avg_time("first") if signal_ok else None,
            "avg_last": avg_time("last") if signal_ok else None,
            "offday_active_hours": round(sum(v["active_hours"] or 0 for v in nwd), 1) if signal_ok else None,
            "last_seen": last_seen.strftime("%Y-%m-%d %H:%M") if last_seen else None,
        }
        out_people.append({
            "name": person,
            "department": ident_info[labels[0]]["department"],
            "identities": [{"label": ident_info[l]["label"], "type": ident_info[l]["type"], "location": ident_info[l]["location"],
                            "baseline_per_hour": round(ident_info[l]["baseline"], 1), "signal": ident_info[l]["signal"]}
                           for l in labels],
            "signal": "ok" if signal_ok else "background",
            "days": days,
            "metrics": metrics,
        })

    # stable, non-judgemental order: department, then name
    out_people.sort(key=lambda p: (p["department"].lower(), p["name"].lower()))

    measurable = [p for p in out_people if p["signal"] == "ok"]
    summary = {
        "people": len(out_people),
        "workdays": len([d for d in dates if DAY_NAMES[d.weekday()] in workdays]),
        "connected_all_workdays": sum(1 for p in out_people if p["metrics"]["days_connected"] == p["metrics"]["workdays"] and p["metrics"]["workdays"]),
        "never_connected": sum(1 for p in out_people if p["metrics"]["days_connected"] == 0),
        "avg_remote_days": round(statistics.mean([p["metrics"]["days_remote"] for p in out_people] or [0]), 1),
        "avg_connected_hours": round(statistics.mean([p["metrics"]["avg_connected_hours"] for p in out_people] or [0]), 1),
        "avg_active_hours": round(statistics.mean([p["metrics"]["avg_active_hours"] for p in measurable if p["metrics"]["avg_active_hours"]] or [0]), 1),
        "measurable": len(measurable),
        "windows_received": len(wkeys),
        "windows_expected": int(round(len(dates) * 24 / bucket_h)) if bucket_h else len(wkeys),
    }
    activity = {
        "period": {"from": dates[0].isoformat(), "to": dates[-1].isoformat(), "tz": a.tz, "bucket_hours": bucket_h,
                   "workdays": sorted(workdays, key=DAY_NAMES.index), "dates": [d.isoformat() for d in dates]},
        "settings": {"connected_min_per_hour": a.connected_min, "active_min_per_hour": a.active_min,
                     "baseline_multiplier": a.mult, "night_hours": a.night},
        "summary": summary,
        "people": out_people,
    }

    if a.merge:
        with open(a.merge, encoding="utf-8") as f:
            rep = json.load(f)
        rep["activity"] = activity
        with open(a.merge, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        print(f"Merged activity for {len(out_people)} people over {len(dates)} days into {a.merge}")
        for p in out_people:
            m = p["metrics"]
            print(f"  {p['name']:<40} signal={p['signal']:<10} connected={m['days_connected']}/{m['workdays']} "
                  f"remote={m['days_remote']} active_days={m['days_active']} avg_active_h={m['avg_active_hours']}")
    else:
        print(json.dumps(activity, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
