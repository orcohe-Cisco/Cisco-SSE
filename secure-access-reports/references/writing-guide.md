# Writing guide for the executive report

## Voice
- Write for a CISO or IT director who has two minutes. Conclusion first, evidence second, detail last.
- Every claim carries a number from the data: "19.5K requests blocked (0.29%)", not "many requests were blocked".
- Plain business language. Explain technical terms by effect: "intrusion prevention stopped 16,201 exploit attempts" rather than "Snort SID 23626 fired".
- Confident and factual. No hedging stacks ("it seems that possibly"), no marketing superlatives ("world-class", "unparalleled"), no exclamation marks.
- Neutral about the vendor: the report shows what the platform did, it does not sell it. A recommendation may name a capability the customer has not enabled, with the reason.
- Never mention how the report was produced (no AI, assistant, model, MCP, connector, automation). Authorship = `prepared_by`.
- Dates as "4–5 October" (EN) / "4–5 באוקטובר" (HE). Period label states the length: "(30 days)".

## Posture rubric
Pick the level from evidence, then justify it in the headline.

| Level | Use when |
|---|---|
| `good` – Protected | Coverage complete (all tunnels up, roaming clients protected), no unresolved high-severity finding, threats blocked with no sign of successful compromise. |
| `watch` – Needs attention | Any medium finding still open: a coverage gap (tunnel down, hub down, unprotected/outdated clients), sustained IPS or malware activity from one source, policy misconfiguration causing blocks of legitimate access, rising block trend. |
| `risk` – At risk | Any high finding: allowed traffic to malware/C2/phishing categories, repeated detections on the same host, a site without protection, AMP retrospective malware, decryption disabled where policy expects inspection and threats are rising. |

Low volume alone is not risk; a quiet lab tenant can be `good`.

## Section by section
**Headline (posture.headline)** – one sentence, ≤ 35 words, the overall verdict plus the two most telling numbers.

**Summary bullets** – 3–5. Suggested order: coverage → threat picture → biggest change/anomaly → access (ZTNA) → what to do next. Each bullet one idea, one or two numbers.

**KPIs** – 8 tiles: requests inspected, blocked, block rate, top security signal (IPS blocks / threats blocked), identities, private apps, tunnels up, roaming clients protected. Use `tone` sparingly: `bad` only for a number that needs action.

**Insights** – one sentence per section explaining what the chart means, not what it shows. "Blocks cluster on 4–5 October, matching the IPS burst" beats "The chart shows daily requests and blocks".

**Findings** – 3–6, ordered high → info. Title is a short noun phrase; detail gives evidence and impact. Include at least one positive finding when deserved (it builds credibility). Do not repeat the same fact in summary, findings and recommendations with the same words.

**Recommendations** – 3–5, each actionable within a quarter.
- `action`: imperative verb + object ("Trace the source of IPS signature 1:23626").
- `rationale`: the risk reduced or value gained.
- `owner`: a team, not a person, unless the user names one.
- P1 = this month, tied to a high/medium finding; P2 = this quarter; P3 = improvement.

## Recommendation library (use only when the data supports it)
| Signal in the data | Recommendation |
|---|---|
| IPS burst from one signature / host | Identify and remediate the source host; confirm the signature is in block mode for all tunnels. |
| Allowed requests to security categories | Move the category to block; review the identities involved. |
| Low proxy share vs DNS | Extend SWG (proxy) coverage to all users, not DNS-only. |
| No or little decryption activity | Enable SSL decryption for high-risk and SaaS upload categories, with privacy exemptions (finance, health). |
| Default-rule blocks on private apps | Align ZTNA access rules and posture profiles with intended groups. |
| Unresolved private app entries | Clean up application definitions and DNS for private resources. |
| Tunnel or hub down / single hub | Restore redundancy; configure the secondary hub. |
| Roaming clients outdated / not protected | Standardize the Secure Client version; enforce module deployment through MDM/GPO. |
| Many destination lists stale or duplicate | Consolidate destination lists; set an owner and review cadence. |
| Generative AI category present | Define a GenAI usage policy; consider AI access controls and DLP for prompts. |
| Filter-avoidance / encrypted DNS seen | Block encrypted-DNS bypass and filter-avoidance categories. |

## Hebrew reports (`lang: "he"`)
- Write natively in Hebrew business register, not a literal translation. Short sentences.
- Keep product and technical names in English: Secure Access, DNS, Firewall, IPS, ZTNA, SWG, Hub, Posture.
- Numbers stay Western digits with separators; percentages as "0.29%".
- Prefer "בקשות שנחסמו" over "חסימות" when you mean requests; "מנהרות" for tunnels; "לקוחות קצה" for roaming clients; "המלצות" / "ממצאים".
- Mixed-direction strings: put the English term at the start or end of the clause where possible to avoid bidi jumps.
- Owner values in Hebrew (צוות SOC, צוות רשת, אבטחת מידע).

## Final check
- Do the numbers in the headline, bullets and findings match the raw results?
- Is every recommendation traceable to a finding or data point?
- Would the reader know in 90 seconds whether they are protected and what to do next?
- No placeholder text, no tooling or authorship mentions, no personal data for external reports.
