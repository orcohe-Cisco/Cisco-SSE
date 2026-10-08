# report.json schema

All keys except `report` are optional. A section renders only when its data is present. See `assets/example_report.json` for a complete file.

```jsonc
{
  "lang": "en",                         // "en" | "he" (Hebrew → RTL layout, Hebrew labels)
  "labels": { "recs": "Next steps" },   // optional overrides for any built-in heading/label

  "brand": {
    "primary": "#0B2545",               // cover gradient, headings
    "accent":  "#049FD9",               // charts, highlights
    "accent2": "#13A89E", "warn": "#E8A33D", "danger": "#C8423B", "ok": "#2E8B57",
    "logo": "assets/logo.png",          // optional; path relative to report.json, or data: URI. Shown white on the cover.
    "customer_logo": "customer.png"     // optional; shown on a white chip on the cover
  },

  "report": {
    "title": "Executive Security Report",
    "subtitle": "30-day review of internet, private access and network security",
    "eyebrow": "Cisco Secure Access",   // small caps line above the title
    "customer": "Contoso Ltd.",
    "period_label": "8 Sep – 7 Oct 2026 (30 days)",
    "generated_on": "2026-10-08",
    "prepared_by": "Name, Title, Company",
    "classification": "Confidential"    // printed on cover and footer
  },

  "posture": {
    "level": "good",                    // "good" (Protected) | "watch" (Needs attention) | "risk" (At risk)
    "headline": "One sentence: the conclusion, with the 1–2 numbers that prove it."
  },
  "summary": ["3–5 bullets, each one quantified idea"],

  "kpis": [                             // 4 or 8 tiles read best (grid of 4)
    {"label": "Requests inspected", "value": 6593051},                       // compact: 6.59M
    {"label": "Block rate", "value": 0.295, "format": "percent"},            // value already in %
    {"label": "IPS blocks", "value": 16201, "format": "int", "tone": "bad", "note": "One signature"},
    {"label": "Tunnels up", "value": "2 / 2", "tone": "good"}                // strings print as-is
  ],                                    // format: compact (default) | int | percent | bytes ; tone: good | warn | bad

  "insights": {                         // one "so-what" sentence shown under a section heading
    "exec_summary": "", "findings": "", "trend": "", "layers": "", "threats": "",
    "usage": "", "users": "", "infra": "", "recs": ""
  },

  "findings": [
    {"severity": "high|medium|low|info", "title": "Short noun phrase", "detail": "Evidence + impact, 1–2 sentences."}
  ],

  "trend": {"series": [{"date": "2026-09-08", "total": 233698, "blocked": 1}]},   // ≥2 points; blocked on right axis

  "layers": [{"name": "Firewall / IPS", "requests": 3643897, "blocked": 19355}],  // donut of blocks + table

  "threats": {
    "items": [{"name": "Threat or domain", "type": "Malware", "count": 12}],      // empty → "no threats" callout
    "note": "Optional custom text for the empty-state callout",
    "event_types": [{"name": "URL security", "count": 87}]
  },
  "ips": [{"signature": "1:23626", "description": "Rule / signature name", "blocked": 16201, "last_seen": "2026-10-08"}],

  "categories":   [{"name": "Computers and Internet", "count": 1156916}],
  "destinations": [{"name": "www.example.com", "requests": 598897}],
  "identities":   [{"name": "Finance site", "type": "Network", "requests": 2308200, "blocked": 101}],
  "private_apps": [{"name": "ERP portal", "count": 103}],

  "infrastructure": {
    "tunnels": [{"name": "HQ-FTD", "type": "FTD", "status": "Connected", "hubs_up": "2 / 2"}],
    "roaming": [{"name": "LAPTOP-01", "os": "Windows 11", "status": "Protected", "version": "5.1.20.333"}]
  },

  "recommendations": [
    {"priority": "P1", "action": "Imperative, specific", "rationale": "Risk reduced / value", "owner": "Team"}
  ],

  "methodology": ["Data source…", "Period…", "Notes on estimates, exclusions, failed calls"],  // string or list

  "activity": { … }                     // workforce connectivity block, written by scripts/activity_rollup.py --merge.
                                        // Do not hand-edit; renders Overview KPIs, person × day grid, per-person table
                                        // and the fixed "How to Read This Report" notes. Insight keys: act_grid, act_table.
}
```

Section order in the output: Executive Summary (with KPIs) → Key Findings → Trend → Layers → Threats (+IPS, event types) → Usage → Users & ZTNA → Deployment Health → Workforce sections (when `activity` is present) → Recommendations → Scope & Methodology. Sections are numbered automatically.

Status cells are green for: connected, up, protected, active, online, VA, encrypted; amber otherwise.
