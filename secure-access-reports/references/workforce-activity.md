# Workforce connectivity report

A per-person view of when employees were connected through Secure Access, from where (remote vs office, when attributable), and how many hours show activity above each device's idle background. Built only from request **totals** per identity per time window; no destinations, URLs or categories are collected.

## Before collecting anything
1. **Confirm disclosure.** Ask once per customer/tenant whether employees are informed that their connectivity is monitored (IT / acceptable-use policy). If not confirmed, offer a department-level report instead: map identities to departments in `people.csv` (`person` = department name) so no individual appears.
2. **Get the identity map** if available: `people.csv` with `identity,person,department,location` (template: `assets/people_template.csv`). One person can have several identities (laptop roaming client, directory account, ZTNA client). Without it, each identity is reported on its own under its platform label.
3. **Settle the window**: period (default 14 days; max ~30), customer time zone, workweek (Israel default `sun,mon,tue,wed,thu`).

## Collect
```bash
python scripts/day_windows.py --days 14 --tz Asia/Jerusalem --bucket hours --size 2 --compact
```
For every window call `get_top_identities(from_time=<from>, to_time=<to>, limit=200)` (in parallel batches). Write one JSON line per window to `windows.jsonl`, compact form:
```json
{"from": 1791356400000, "to": 1791363600000, "rows": [["LT-DLEVI", "anyconnect", 745], ["dana@contoso.com", "directory_user", 1740]]}
```
`rows` = `[identity.label, identity.type.type, counts.requests]`. Keep every row; the rollup filters types. Omit e-mail addresses in labels only if the user asks for anonymization (map them in `people.csv` instead).

Volume: 12 calls per day at 2-hour buckets (14 days = 168 calls). For 30 days use `--size 4` or run two 14-day batches. If a call fails, skip it; the report states coverage (windows received vs expected).

Do **not** call activity/event tools (`get_activity_*`), `get_top_destinations`, `get_top_urls` or category tools for this report: they expose what people browsed, which this report deliberately excludes.

## Roll up and render
```bash
python scripts/activity_rollup.py windows.jsonl --tz Asia/Jerusalem --people people.csv --merge report.json
python scripts/render_report.py report.json --out <dir> --pdf
```
`report.json` needs `report` (title, customer, period_label, classification e.g. "Confidential – HR and management only"), optional `posture.headline` (leave out `posture.level`: the security-posture pill does not apply), `summary`, `insights.act_grid` / `insights.act_table`, `methodology`. Example: `assets/example_activity_report.json`.

Rollup options: `--workdays`, `--connected-min` (req/h, default 5), `--active-min` (req/h floor, default 30), `--mult` (× idle baseline, default 3), `--night 0-5`, `--types`.

## What the metrics mean
| Metric | Meaning | Reliability |
|---|---|---|
| Connected (day / hours) | The person's device or account sent traffic in that window. | High. Answers "was the laptop on and protected". |
| Remote day | Traffic came from a roaming client or ZTNA client (off the office network). | High for remote. Office presence per person is visible only if office traffic is user-attributed or a person-specific identity is mapped with `location=office`. |
| Active hours | Windows with traffic ≥ max(active-min, mult × that identity's overnight idle level), or user-driven traffic (directory account, ZTNA). | Indicator only. Background apps can inflate it; offline work, meetings and phone calls are invisible. 2-hour buckets → start/end times ±1 h. |
| Not measurable | Identity whose traffic is flat day and night (heavy telemetry, always-on sync). | Correctly withheld; do not guess. |

Live validation (lab tenant, Oct 2026): a Windows 11 roaming client produced ~720 requests/hour at 03:00 and at 10:00 alike → flagged as background; the same laptop's ZTNA client and the user account appeared only 14:00–22:00 → those hours counted as active.

## Writing rules for this report
- Describe patterns; never judge people. No "lazy", "unproductive", "slacking", "idle employee", no productivity scores, no ranking or "bottom N" lists. Order is department, then name (the rollup does this).
- Phrase observations as facts with context: "Active hours average 5.2 h/day, consistently ending at 14:00" (fine) vs "Lior works half days" (not supported by the data).
- Name individuals in the summary only for patterns that warrant a manager's conversation, and frame them that way ("worth a conversation rather than a conclusion").
- State coverage and limits in the summary if coverage < 90% or more than 10% of people are not measurable.
- The fixed "How to Read This Report" section always renders; do not remove or soften it.
- Classification on the cover: restrict to HR / management.
