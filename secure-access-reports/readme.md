---
name: secure-access-reports
description: Create executive security reports and workforce connectivity (remote-work) reports as PDF/HTML, in English or Hebrew, from Cisco Secure Access data via its MCP connector.
dependencies: python>=3.10, pypdf, playwright
---

# Secure Access Reports

Two report types share one renderer:
- **Executive security report** (default) – the workflow below.
- **Workforce connectivity report** – per-person connected days, remote days and active hours. Read `references/workforce-activity.md` and follow it instead of steps 2–4 below; it has its own consent check, collection method and writing rules. Both can be combined in one report.json when the user wants both.

## Executive security report

Turns Cisco Secure Access telemetry into a professional executive report: cover page, executive summary with posture rating, KPI tiles, findings, trend and enforcement charts, threat landscape, usage, Zero Trust access, deployment health, prioritized recommendations and methodology. Output is an A4 PDF plus a responsive HTML version, in English or Hebrew (RTL).

The quality bar: a CISO should be able to read page 2 in 90 seconds and know (1) are we protected, (2) what changed, (3) what we should do next. Every number traces back to a connector call.

## Workflow

### 1. Scope (ask once, only for what is missing)
Collect in a single question, with defaults:
- **Customer / tenant name** for the cover (no default; required).
- **Period**: default last 30 days (`-30days` → `now`). Supported: `-7days`, `-30days`, `-90days` (90 days may be slow; reports API retention applies).
- **Language**: English (default) or Hebrew.
- **Audience**: executive/board (default, less technical) or IT/security management (more operational detail).
- **Prepared by** line (name, title, company) – optional.
- **Distribution**: internal or external. External → anonymize user identities (see Privacy).

If the user already gave these, do not ask. If nobody is available to answer, use defaults and state them in one line.

### 2. Collect data (read-only)
Read `references/tool-map.md` first. It lists the exact call set, parameters, response shapes, field mappings and known API quirks. Connector tool names vary by client (`get_security_summary`, `cisco-secure-access:get_security_summary`, `mcp__…__get_security_summary`); match on the suffix.

Run the **core set** in parallel; add the **optional set** when the audience is IT/security or the core data points at it. Never call write tools (`create_*`, `add_*`, `remove_*`, `update_*`, `delete_*`).

For the trend chart, run `scripts/day_windows.py --days <N> --tz <customer zone>` and call `get_security_summary` once per window (epoch-ms `from_time`/`to_time`, in parallel). This keeps the chart consistent with the headline totals and avoids the oversized hourly endpoints.

### 3. Analyze
Compute before writing anything:
- Block rate = blocked / requests (overall and per layer).
- Layer share of blocks; which layer dominates.
- Trend: average daily volume, peak day, block spikes (days > 3× the median of non-zero days), and whether they coincide with IPS/threat activity. Drop partial first/last days from the chart.
- Threat concentration: top threat, top signature, share of blocks it represents.
- Coverage: tunnels connected and hubs up; roaming clients protected vs total; outdated client versions.
- ZTNA: unique private resources, top apps, blocked/default-rule hits.
- Posture level using the rubric in `references/writing-guide.md`.

Headline numbers (requests, blocked, identities) come from `get_security_summary`. The time series is for shape only; its daily sums can differ from the summary, so never mix them in one sentence.

### 4. Write the narrative
Follow `references/writing-guide.md`. In short: lead with the conclusion, quantify every claim, one idea per bullet, "so-what" in each section insight, findings ranked by severity, recommendations that are specific, owned and prioritized (P1–P3). For Hebrew, write natively (not translated English) and keep product names in English.

### 5. Build `report.json` and render
Schema: `references/report-schema.md`. A complete example: `assets/example_report.json`.

```bash
python scripts/render_report.py report.json --out <output_dir> --pdf
```
PDF export uses Playwright/Chromium (pip `playwright` + `playwright install chromium`, and `pypdf` for a footer-free cover) or WeasyPrint as fallback. If neither is installable, deliver the HTML; it has print CSS and saves to PDF from any browser.

Sections render only when their data exists, so omit keys rather than filling them with zeros or placeholders.

### 6. Verify, then deliver
- Rasterize the PDF (`pdftoppm -r 60 -png`) and look at every page: no stranded headings, no overflowing tables, charts present, correct direction for Hebrew.
- Re-check every number in the summary and findings against the raw results.
- Search the rendered HTML for leftover placeholders (`TODO`, `XXX`, `{`, `None`, `nan`).
- Deliver the PDF (primary) and HTML. In the reply give one or two sentences on the key takeaway, not a recap of the report.

## Hard rules
- **No fabricated data.** If a call fails or returns `{}`, the section is omitted or states "no events recorded" – never estimated. Mention failed calls in the methodology list.
- **Read-only.** This skill never changes tenant configuration.
- **No authorship tooling in the deliverable.** The report must not mention AI, assistants, language models, MCP, "connector", "generated by" or similar. Methodology names the data source as the Cisco Secure Access Reports/Policies/Deployments APIs. Authorship is the `prepared_by` value only.
- **Workforce data stays at connectivity level.** Never collect or show which sites, URLs or categories a named person used, never score, rank or label people (e.g. "lazy", "unproductive"), and run per-person reports only after confirming employees were informed of monitoring (otherwise department-level only).
- **Privacy.** For external distribution, replace user names and emails with role labels or initials (`User A`, `Finance user`) and keep only network/site names. Never print API keys, tokens, org IDs or internal tunnel auth IDs.
- **Numbers formatting.** Compact in tiles and charts (6.59M), full with separators in tables (3,643,897), percentages with sensible precision (0.29%, 99.4%).
