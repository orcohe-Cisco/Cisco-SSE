# Secure Access connector: data collection map

Server: CiscoDevNet `secure-access-mcp-community` (Streamable HTTP, 70+ tools). All report tools are read-only and take `from_time` / `to_time`.

## Time parameters
- Relative strings: `-7days`, `-30days`, `-90days`, `now`. A relative pair such as `-4days` → `-3days` is a rolling 24h window, not a calendar day.
- Epoch milliseconds also work (`"1791147600000"`), and give exact calendar windows. Use `scripts/day_windows.py --days 30 --tz Asia/Jerusalem` (or the customer's zone) to generate them.
- Use the same `from`/`to` for every call in a report so totals reconcile.

## Core set (always)
Run these in parallel for the report period.

| Report field | Tool | Params | Response → mapping |
|---|---|---|---|
| Headline KPIs | `get_security_summary` | period | `data.requests`, `data.requestsblocked`, `data.requestsallowed`, `data.identities`, `data.domains`, `data.applications`, `data.categories`, `data.files`. `meta.counting:"estimated"` → say "estimated" in methodology. |
| All-type total | `get_total_requests` | period | `data.count`; `meta.successful` lists which layers answered (dns, firewall, proxy, swa, ip, intrusion, ztna, decryption). Can exceed the summary total because it adds ZTNA/IP/intrusion counters; use the summary for the headline. |
| Layers | `get_security_summary_by_type` × `dns`, `proxy`, `firewall` | period, `report_type` | `data.requests`, `data.requestsblocked` → `layers[]`. DNS + proxy + firewall blocked = summary blocked. |
| IPS | `get_summaries_by_rule_intrusion` | period, `limit: 10` | `data[].signatures[]` → `{generatorid}:{id}` as signature, `counts.blocked`, `counts.detected`, `counts.wouldblock`, `lasteventat` (epoch ms) → `ips[]`. IPS blocks are counted inside the firewall layer: show them as a share of firewall blocks, do not add them. |
| Threats | `get_top_threats`, `get_top_threat_types` | period, `limit: 10` | `{}` means none recorded → leave `threats.items` empty (renderer prints the "no threats" callout). |
| Event types | `get_top_event_types` | period | `data[]` `{eventtype, count}`; keep count > 0 → `threats.event_types` (humanize: `url_security` → "URL security"). |
| Categories | `get_top_categories_by_type` with `report_type: dns` | period, `limit: 10` | `data[].category.label`, `count` → `categories[]`. Skip `type: security` rows here; report them under threats. |
| Destinations | `get_top_destinations` | period, `limit: 8` | `data[].domain`, `counts.requests`, `counts.blockedrequests` → `destinations[]`. Drop resolver IPs (e.g. `208.67.222.222`) and note it. |
| Identities | `get_top_identities` | period, `limit: 8` | `data[].identity.label`, `identity.type.label`, `counts.requests`, `counts.blockedrequests` → `identities[]`. |
| Private apps | `get_top_resources`, `get_unique_resources` | period | `data[].application.label` (missing label → "Unresolved application"), `count` → `private_apps[]`; `data.count` → KPI. |
| Tunnels | `list_network_tunnels` | – | `network_tunnels[]`: `name`, `deviceType`, `status`, hubs `status.status == "UP"` → `hubs_up: "2 / 2"`. Never print `authId`, CIDRs or org IDs. |
| Roaming clients | `list_roaming_computers` | – | `roaming_computers[]`: `name`, `osVersionName`, `swgStatus` (or `status`), `version`, `lastSync`. For large fleets report counts (protected / total, % on latest version) and list only exceptions. |
| Trend | `get_security_summary` per window from `day_windows.py` | `from_time`/`to_time` = window ms | `data.requests`, `data.requestsblocked` → `trend.series[] = {date, total, blocked}`. 30 small calls; use `--bucket week` for 90 days. |

## Optional set (IT/security audience, or when core data points there)
| Purpose | Tool | Notes |
|---|---|---|
| ZTNA detail | `get_activity_ztna` (`limit: 50`) | Blocked attempts, default-rule hits, which identities. Default window is `-1days`; pass the report period. |
| Rule effectiveness | `list_access_rules` + `get_summaries_by_rule_hitcount(rule_ids="a,b,c")` | Unused rules (0 hits) and rules carrying most traffic. `list_access_rules` can be large. |
| Firewall rules | `get_summaries_by_rule_firewall_hitcount` | Needs rule IDs. |
| Malware | `get_activity_amp`, `get_top_files` | `{}` = none. |
| Decryption coverage | `get_activity_decryption` | Supports an SSL-inspection recommendation. |
| Web detail | `get_top_urls`, `get_top_categories_by_type("proxy")` | |
| Bandwidth | `get_bandwidth_by_timerange` | Large, hourly. |
| Destination-list hygiene | `audit_stale_lists`, `destination_usage_summary`, `find_repeating_destinations` | Good for a "policy hygiene" finding. |
| Domain context | `investigate_domain`, `get_domain_categorization` | For a named threat domain only. |
| Multi-org (MSSP) | `list_child_organizations`, `get_multi_org_report` | Only if present in the client. |

## Known quirks
- `get_top_categories` and other tools without a `limit` argument can fail with `400 missing required parameters ['from','to','offset']`. Use the `_by_type` variant or `get_summaries_by_category`.
- `get_security_summary_by_type("ztna")` returns 404. ZTNA data comes from `get_top_resources`, `get_unique_resources`, `get_activity_ztna`.
- `get_requests_by_timerange` / `get_requests_by_hour` return hourly points for the whole window (≈720 for 30 days, ~150 KB) regardless of `limit`. Prefer the per-day summary approach. If a client saved the raw result to a file, `scripts/aggregate_timeseries.py file1 [file2…] --merge report.json` rolls it up to days. Its daily sums run higher than the summary (they include firewall/IPS event counters), so label them as "events" if used.
- `get_summaries_by_category` includes deprecated categories (`deprecated: true`, e.g. "Software/Technology") that duplicate current ones; filter them out.
- Activity tools default to `-1days`. An empty result for 24h is common in quiet tenants; widen to the report period before concluding "no activity".
- Responses are JSON strings inside `{"result": "..."}`; parse the inner string.
- Timeouts happen on broad `list_*` calls. Retry once; if it fails again, omit that section and list it in methodology.
