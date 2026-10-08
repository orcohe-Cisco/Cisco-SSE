#!/usr/bin/env python3
"""Render a Cisco Secure Access executive report from a report.json file.

Usage:
    python render_report.py report.json --out OUT_DIR [--pdf] [--name FILE_STEM]

Produces OUT_DIR/<stem>.html (always) and OUT_DIR/<stem>.pdf (with --pdf, when
Playwright/Chromium or WeasyPrint is available). Standard library only for HTML.
See references/report-schema.md for the input format.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import math
import mimetypes
import os
import sys
from datetime import date, datetime

# --------------------------------------------------------------------------
# Labels (EN / HE)
# --------------------------------------------------------------------------
LABELS = {
    "en": {
        "exec_summary": "Executive Summary",
        "key_metrics": "Key Metrics",
        "trend": "Traffic & Enforcement Trend",
        "layers": "Enforcement by Security Layer",
        "threats": "Threat Landscape",
        "usage": "Internet Usage Profile",
        "users": "Users & Zero Trust Access",
        "infra": "Deployment Health",
        "findings": "Key Findings",
        "recs": "Recommendations",
        "method": "Scope & Methodology",
        "period": "Reporting period",
        "prepared_for": "Prepared for",
        "prepared_by": "Prepared by",
        "date": "Date",
        "posture": "Security posture",
        "posture_good": "Protected",
        "posture_watch": "Needs attention",
        "posture_risk": "At risk",
        "requests": "Requests",
        "blocked": "Blocked",
        "block_rate": "Block rate",
        "layer": "Layer",
        "share_blocks": "Share of blocks",
        "total_requests": "Total requests",
        "blocked_requests": "Blocked requests",
        "threat": "Threat",
        "type": "Type",
        "count": "Count",
        "category": "Category",
        "destination": "Destination",
        "identity": "Identity",
        "application": "Private application",
        "accesses": "Accesses",
        "signature": "IPS signature",
        "last_seen": "Last seen",
        "tunnel": "Network tunnel",
        "device": "Device",
        "status": "Status",
        "hubs": "Hubs up",
        "os": "OS",
        "version": "Client version",
        "priority": "Priority",
        "action": "Action",
        "rationale": "Why it matters",
        "owner": "Owner",
        "severity": "Severity",
        "sev_high": "High",
        "sev_medium": "Medium",
        "sev_low": "Low",
        "sev_info": "Info",
        "no_threats": "No security-category threats were recorded in this period.",
        "top_categories": "Top content categories",
        "top_destinations": "Top destinations",
        "top_identities": "Most active identities",
        "private_apps": "Private applications (ZTNA)",
        "tunnels": "Network tunnels",
        "roaming": "Roaming clients",
        "ips_title": "Intrusion prevention",
        "event_types": "Security events by type",
        "page": "Page",
        "of": "of",
        "daily_total": "Daily requests",
        "daily_blocked": "Daily blocked",
        "contents": "Contents",
        "act_overview": "Workforce Connectivity Overview",
        "act_grid": "Daily Connectivity by Person",
        "act_table": "Per-Person Summary",
        "act_notes": "How to Read This Report",
        "act_people": "People / devices",
        "act_workdays": "Workdays in period",
        "act_avg_conn": "Avg connected hours / day",
        "act_avg_active": "Avg active hours / day",
        "act_avg_remote": "Avg remote days / person",
        "act_never": "Not connected on any workday",
        "act_person": "Person",
        "act_dept": "Department",
        "act_days_conn": "Days connected",
        "act_days_remote": "Remote days",
        "act_days_active": "Active days",
        "act_first": "Typical start",
        "act_last": "Typical end",
        "act_hours": "Active h / day",
        "act_offday": "Off-day active h",
        "act_last_seen": "Last seen",
        "act_nm": "Not measurable",
        "lg_remote_active": "Remote, active",
        "lg_remote_connected": "Remote, connected only",
        "lg_office_active": "Office, active",
        "lg_office_connected": "Office, connected only",
        "lg_seen_active": "Active, location not attributed",
        "lg_seen_connected": "Connected, location not attributed",
        "lg_none": "Not seen",
        "lg_cell": "Number in cell = active hours",
        "act_note_1": "Connected means the device or user sent traffic through Secure Access. It does not mean the person was at the keyboard.",
        "act_note_2": "Active means traffic clearly above that device's own overnight background level ({mult}x its night median, minimum {amin} requests per hour), or user-driven traffic such as private-application (ZTNA) sessions. It indicates activity, not productivity or output.",
        "act_note_3": "Work done offline, in meetings, by phone, or on systems not routed through Secure Access is not visible in this data.",
        "act_note_4": "Office presence per person is visible only where office traffic is attributed to users; otherwise it appears under the site or tunnel.",
        "act_note_5": "Devices whose traffic is constant day and night are marked Not measurable: their activity cannot be separated from background.",
        "act_note_6": "Times are in {tz} at {bucket}-hour resolution. Data coverage: {recv} of {exp} time windows.",
        "act_note_7": "Use these figures as one input alongside the manager's knowledge of each role. They are not a sufficient basis on their own for performance or disciplinary decisions.",
    },
    "he": {
        "exec_summary": "תקציר מנהלים",
        "key_metrics": "מדדים מרכזיים",
        "trend": "מגמת תעבורה ואכיפה",
        "layers": "אכיפה לפי שכבת אבטחה",
        "threats": "תמונת איומים",
        "usage": "פרופיל שימוש באינטרנט",
        "users": "משתמשים וגישת Zero Trust",
        "infra": "תקינות הפריסה",
        "findings": "ממצאים עיקריים",
        "recs": "המלצות",
        "method": "היקף ומתודולוגיה",
        "period": "תקופת הדוח",
        "prepared_for": "הוכן עבור",
        "prepared_by": "הוכן על ידי",
        "date": "תאריך",
        "posture": "מצב אבטחה",
        "posture_good": "מוגן",
        "posture_watch": "דורש תשומת לב",
        "posture_risk": "בסיכון",
        "requests": "בקשות",
        "blocked": "נחסמו",
        "block_rate": "שיעור חסימה",
        "layer": "שכבה",
        "share_blocks": "חלק מהחסימות",
        "total_requests": "סך הבקשות",
        "blocked_requests": "בקשות שנחסמו",
        "threat": "איום",
        "type": "סוג",
        "count": "כמות",
        "category": "קטגוריה",
        "destination": "יעד",
        "identity": "זהות",
        "application": "אפליקציה פרטית",
        "accesses": "גישות",
        "signature": "חתימת IPS",
        "last_seen": "נראה לאחרונה",
        "tunnel": "מנהרת רשת",
        "device": "מכשיר",
        "status": "סטטוס",
        "hubs": "Hubs פעילים",
        "os": "מערכת הפעלה",
        "version": "גרסת לקוח",
        "priority": "עדיפות",
        "action": "פעולה",
        "rationale": "למה זה חשוב",
        "owner": "אחריות",
        "severity": "חומרה",
        "sev_high": "גבוהה",
        "sev_medium": "בינונית",
        "sev_low": "נמוכה",
        "sev_info": "מידע",
        "no_threats": "לא נרשמו איומים מקטגוריות אבטחה בתקופה זו.",
        "top_categories": "קטגוריות תוכן מובילות",
        "top_destinations": "יעדים מובילים",
        "top_identities": "הזהויות הפעילות ביותר",
        "private_apps": "אפליקציות פרטיות (ZTNA)",
        "tunnels": "מנהרות רשת",
        "roaming": "לקוחות קצה (Roaming)",
        "ips_title": "מניעת חדירות (IPS)",
        "event_types": "אירועי אבטחה לפי סוג",
        "page": "עמוד",
        "of": "מתוך",
        "daily_total": "בקשות יומיות",
        "daily_blocked": "חסימות יומיות",
        "contents": "תוכן עניינים",
        "act_overview": "סקירת קישוריות העובדים",
        "act_grid": "קישוריות יומית לפי עובד",
        "act_table": "סיכום לפי עובד",
        "act_notes": "איך לקרוא את הדוח",
        "act_people": "עובדים / מכשירים",
        "act_workdays": "ימי עבודה בתקופה",
        "act_avg_conn": "ממוצע שעות מחובר ביום",
        "act_avg_active": "ממוצע שעות פעילות ביום",
        "act_avg_remote": "ממוצע ימי עבודה מרחוק",
        "act_never": "לא התחברו באף יום עבודה",
        "act_person": "עובד",
        "act_dept": "מחלקה",
        "act_days_conn": "ימים מחובר",
        "act_days_remote": "ימים מרחוק",
        "act_days_active": "ימים פעילים",
        "act_first": "שעת התחלה אופיינית",
        "act_last": "שעת סיום אופיינית",
        "act_hours": "שעות פעילות ביום",
        "act_offday": "שעות פעילות בימי מנוחה",
        "act_last_seen": "נראה לאחרונה",
        "act_nm": "לא ניתן למדידה",
        "lg_remote_active": "מרחוק, פעיל",
        "lg_remote_connected": "מרחוק, מחובר בלבד",
        "lg_office_active": "משרד, פעיל",
        "lg_office_connected": "משרד, מחובר בלבד",
        "lg_seen_active": "פעיל, מיקום לא משויך",
        "lg_seen_connected": "מחובר, מיקום לא משויך",
        "lg_none": "לא נראה",
        "lg_cell": "המספר בתא = שעות פעילות",
        "act_note_1": "מחובר פירושו שהמכשיר או המשתמש שלחו תעבורה דרך Secure Access. אין בכך כדי להעיד שהעובד ישב מול המחשב.",
        "act_note_2": "פעיל פירושו תעבורה גבוהה בבירור מרמת הרקע הלילית של אותו מכשיר (פי {mult} מהחציון הלילי, לפחות {amin} בקשות לשעה), או תעבורה שמקורה במשתמש כמו גישה לאפליקציות פרטיות (ZTNA). זהו מדד לפעילות, לא לתפוקה.",
        "act_note_3": "עבודה ללא חיבור, בפגישות, בטלפון או במערכות שאינן עוברות דרך Secure Access אינה נראית בנתונים אלה.",
        "act_note_4": "נוכחות במשרד ברמת העובד נראית רק כאשר תעבורת המשרד משויכת למשתמשים; אחרת היא מופיעה תחת האתר או המנהרה.",
        "act_note_5": "מכשירים שהתעבורה שלהם קבועה ביום ובלילה מסומנים כ'לא ניתן למדידה', כי לא ניתן להפריד בין פעילות לרקע.",
        "act_note_6": "השעות לפי {tz} ברזולוציה של {bucket} שעות. כיסוי הנתונים: {recv} מתוך {exp} חלונות זמן.",
        "act_note_7": "יש להשתמש בנתונים כנקודת מידע אחת לצד היכרות המנהל עם כל תפקיד. הם אינם בסיס מספיק כשלעצמם להחלטות על ביצועים או למשמעת.",
    },
}

DEFAULT_BRAND = {
    "primary": "#0B2545",   # deep navy
    "accent": "#049FD9",    # Cisco-style blue
    "accent2": "#13A89E",   # teal
    "warn": "#E8A33D",
    "danger": "#C8423B",
    "ok": "#2E8B57",
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def num(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def fmt_int(v) -> str:
    return f"{int(round(num(v))):,}"


def fmt_compact(v) -> str:
    n = num(v)
    a = abs(n)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            s = f"{n / div:.2f}" if a / div < 10 else f"{n / div:.1f}" if a / div < 100 else f"{n / div:.0f}"
            s = s.rstrip("0").rstrip(".") if "." in s else s
            return s + suf
    return fmt_int(n)


def fmt_pct(v, digits=None) -> str:
    n = num(v)
    if digits is None:
        digits = 3 if 0 < n < 0.01 else 2 if n < 1 else 1
    return f"{n:.{digits}f}%"


def fmt_value(v, fmt: str | None) -> str:
    if isinstance(v, str) and not v.replace(",", "").replace(".", "").lstrip("-").isdigit():
        return esc(v)
    if fmt == "percent":
        return fmt_pct(v)
    if fmt == "int":
        return fmt_int(v)
    if fmt == "bytes":
        n = num(v)
        for div, suf in ((1 << 40, "TB"), (1 << 30, "GB"), (1 << 20, "MB"), (1 << 10, "KB")):
            if n >= div:
                return f"{n / div:.1f} {suf}"
        return f"{int(n)} B"
    return fmt_compact(v)


def nice_ceiling(v: float) -> float:
    if v <= 0:
        return 1.0
    exp = math.floor(math.log10(v))
    base = 10 ** exp
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * base:
            return m * base
    return 10 * base


def parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def short_ts(v) -> str:
    """'2026-10-02 18:00' -> '02 Oct 18:00'."""
    try:
        return datetime.strptime(str(v)[:16], "%Y-%m-%d %H:%M").strftime("%d %b %H:%M")
    except ValueError:
        return str(v or "—")


def embed_image(path_or_uri: str | None, base_dir: str) -> str | None:
    if not path_or_uri:
        return None
    if path_or_uri.startswith("data:"):
        return path_or_uri
    p = path_or_uri if os.path.isabs(path_or_uri) else os.path.join(base_dir, path_or_uri)
    if not os.path.isfile(p):
        return None
    mime = mimetypes.guess_type(p)[0] or "image/png"
    with open(p, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def trend_svg(series: list[dict], brand: dict, L: dict) -> str:
    pts = [s for s in series if parse_date(s.get("date"))]
    if len(pts) < 2:
        return ""
    W, H = 760, 250
    ml, mr, mt, mb = 56, 56, 18, 38
    cw, ch = W - ml - mr, H - mt - mb
    totals = [num(p.get("total")) for p in pts]
    blocks = [num(p.get("blocked")) for p in pts]
    tmax = nice_ceiling(max(totals) or 1)
    bmax = nice_ceiling((max(blocks) or 1) * 2.2)  # bars occupy the lower part of the plot
    n = len(pts)
    step = cw / (n - 1)
    bw = max(2.0, min(14.0, cw / n * 0.55))

    def x(i):
        return ml + i * step

    def yt(v):
        return mt + ch - (v / tmax) * ch

    def yb(v):
        return mt + ch - (v / bmax) * ch

    out = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" xmlns="http://www.w3.org/2000/svg" direction="ltr">']
    out.append(
        f'<defs><linearGradient id="gT" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{brand["accent"]}" stop-opacity="0.28"/>'
        f'<stop offset="1" stop-color="{brand["accent"]}" stop-opacity="0.02"/></linearGradient></defs>'
    )
    # grid + left axis
    for k in range(5):
        v = tmax * k / 4
        yy = yt(v)
        out.append(f'<line x1="{ml}" x2="{W - mr}" y1="{yy:.1f}" y2="{yy:.1f}" class="grid"/>')
        out.append(f'<text x="{ml - 8}" y="{yy + 4:.1f}" class="axis" text-anchor="end">{fmt_compact(v)}</text>')
        vb = bmax * k / 4
        out.append(
            f'<text x="{W - mr + 8}" y="{yy + 4:.1f}" class="axis" text-anchor="start" style="fill:{brand['danger']}">{fmt_compact(vb)}</text>'
        )
    # blocked bars (right axis)
    for i, b in enumerate(blocks):
        if b <= 0:
            continue
        yy = yb(b)
        out.append(
            f'<rect x="{x(i) - bw / 2:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{mt + ch - yy:.1f}" '
            f'rx="1.5" fill="{brand["danger"]}" opacity="0.7"/>'
        )
    # total area + line
    line = " ".join(f"{x(i):.1f},{yt(v):.1f}" for i, v in enumerate(totals))
    area = f"{x(0):.1f},{mt + ch:.1f} {line} {x(n - 1):.1f},{mt + ch:.1f}"
    out.append(f'<polygon points="{area}" fill="url(#gT)"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="{brand["accent"]}" stroke-width="2.2" stroke-linejoin="round"/>')
    # x labels
    every = max(1, round(n / 7))
    for i, p in enumerate(pts):
        if i % every == 0 or (i == n - 1 and (n - 1) % every >= every * 0.6):
            d = parse_date(p["date"])
            out.append(f'<text x="{x(i):.1f}" y="{H - 14}" class="axis" text-anchor="middle">{d.strftime("%d %b")}</text>')
    out.append("</svg>")
    legend = (
        f'<div class="legend"><span><i style="background:{brand["accent"]}"></i>{esc(L["daily_total"])}</span>'
        f'<span><i style="background:{brand["danger"]}"></i>{esc(L["daily_blocked"])}</span></div>'
    )
    return "".join(out) + legend


def donut_svg(parts: list[tuple[str, float]], colors: list[str], center_value: str, center_label: str) -> str:
    total = sum(v for _, v in parts)
    if total <= 0:
        return ""
    R, r, cx, cy = 80, 54, 95, 95
    out = [f'<svg viewBox="0 0 190 190" class="donut" xmlns="http://www.w3.org/2000/svg" direction="ltr">']
    ang = -math.pi / 2
    nonzero = [(lbl, v) for lbl, v in parts if v > 0]
    if len(nonzero) == 1:
        c = colors[[p[0] for p in parts].index(nonzero[0][0]) % len(colors)]
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{(R + r) / 2}" fill="none" stroke="{c}" stroke-width="{R - r}"/>')
    else:
        for i, (_, v) in enumerate(parts):
            if v <= 0:
                continue
            frac = v / total
            a2 = ang + frac * 2 * math.pi
            large = 1 if frac > 0.5 else 0
            x1, y1 = cx + R * math.cos(ang), cy + R * math.sin(ang)
            x2, y2 = cx + R * math.cos(a2), cy + R * math.sin(a2)
            x3, y3 = cx + r * math.cos(a2), cy + r * math.sin(a2)
            x4, y4 = cx + r * math.cos(ang), cy + r * math.sin(ang)
            out.append(
                f'<path d="M{x1:.2f},{y1:.2f} A{R},{R} 0 {large} 1 {x2:.2f},{y2:.2f} '
                f'L{x3:.2f},{y3:.2f} A{r},{r} 0 {large} 0 {x4:.2f},{y4:.2f} Z" fill="{colors[i % len(colors)]}" '
                f'stroke="#fff" stroke-width="1.5"/>'
            )
            ang = a2
    out.append(f'<text x="{cx}" y="{cy + 2}" text-anchor="middle" class="donut-v">{esc(center_value)}</text>')
    out.append(f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" class="donut-l">{esc(center_label)}</text>')
    out.append("</svg>")
    return "".join(out)


def hbars(items: list[dict], label_key: str, value_key: str, color: str, sub_key: str | None = None,
          max_items: int = 8, value_fmt=fmt_compact) -> str:
    rows = [i for i in items if num(i.get(value_key)) > 0][:max_items]
    if not rows:
        return ""
    vmax = max(num(i.get(value_key)) for i in rows)
    out = ['<div class="hbars">']
    for it in rows:
        v = num(it.get(value_key))
        w = max(1.5, v / vmax * 100)
        sub = f'<span class="hb-sub">{esc(it.get(sub_key))}</span>' if sub_key and it.get(sub_key) else ""
        out.append(
            f'<div class="hb-row"><div class="hb-label" title="{esc(it.get(label_key))}">{esc(it.get(label_key))}{sub}</div>'
            f'<div class="hb-track"><div class="hb-fill" style="width:{w:.1f}%;background:{color}"></div></div>'
            f'<div class="hb-val">{value_fmt(v)}</div></div>'
        )
    out.append("</div>")
    return "".join(out)


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------
class Doc:
    def __init__(self, data: dict, base_dir: str):
        self.d = data
        self.lang = data.get("lang", "en") if data.get("lang") in LABELS else "en"
        self.L = dict(LABELS[self.lang])
        self.L.update(data.get("labels") or {})
        self.brand = dict(DEFAULT_BRAND)
        self.brand.update({k: v for k, v in (data.get("brand") or {}).items() if isinstance(v, str) and v.startswith("#")})
        self.logo = embed_image((data.get("brand") or {}).get("logo"), base_dir)
        self.customer_logo = embed_image((data.get("brand") or {}).get("customer_logo"), base_dir)
        self.insights = data.get("insights") or {}
        self.sec_no = 0
        self.toc: list[str] = []

    # -- utilities
    def section(self, key: str, body, title_key: str | None = None, cls: str = "") -> str:
        """body: HTML string or list of HTML blocks. The heading, insight and first
        block are kept on the same page; later blocks may flow to the next page."""
        blocks = [b for b in (body if isinstance(body, list) else [body]) if b and b.strip()]
        if not blocks:
            return ""
        self.sec_no += 1
        title = self.L[title_key or key]
        self.toc.append(title)
        insight = self.insights.get(key)
        ins = f'<p class="insight">{esc(insight)}</p>' if insight else ""
        head = f'<div class="sec-head"><span class="sec-no">{self.sec_no:02d}</span><h2>{esc(title)}</h2></div>'
        lead = f'<div class="lead">{head}{ins}{blocks[0]}</div>'
        return f'<section class="sec {cls}" id="s-{key}">{lead}{"".join(blocks[1:])}</section>'

    @staticmethod
    def blk(title: str | None, content: str) -> str:
        if not content:
            return ""
        h = f"<h3>{esc(title)}</h3>" if title else ""
        return f'<div class="blk">{h}{content}</div>'

    def table(self, headers: list[str], rows: list[list[str]], num_cols: set[int] | None = None) -> str:
        num_cols = num_cols or set()
        th = "".join(f'<th class="{"n" if i in num_cols else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
        trs = []
        for r in rows:
            tds = "".join(f'<td class="{"n" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r))
            trs.append(f"<tr>{tds}</tr>")
        return f'<table class="tbl"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'

    def sev_badge(self, sev: str) -> str:
        sev = (sev or "info").lower()
        if sev not in ("high", "medium", "low", "info"):
            sev = "info"
        return f'<span class="badge sev-{sev}">{esc(self.L["sev_" + sev])}</span>'

    # -- cover
    def cover(self) -> str:
        r = self.d.get("report") or {}
        b = self.brand
        posture = self.d.get("posture") or {}
        level = (posture.get("level") or "").lower()
        pill = ""
        if level in ("good", "watch", "risk"):
            pill = f'<div class="pill pill-{level}"><span class="dot"></span>{esc(self.L["posture"])}: <b>{esc(self.L["posture_" + level])}</b></div>'
        logo = f'<img class="logo" src="{self.logo}" alt=""/>' if self.logo else ""
        clogo = f'<img class="clogo" src="{self.customer_logo}" alt=""/>' if self.customer_logo else ""
        meta_rows = []
        if r.get("customer"):
            meta_rows.append((self.L["prepared_for"], r["customer"]))
        if r.get("period_label"):
            meta_rows.append((self.L["period"], r["period_label"]))
        if r.get("prepared_by"):
            meta_rows.append((self.L["prepared_by"], r["prepared_by"]))
        meta_rows.append((self.L["date"], r.get("generated_on") or date.today().isoformat()))
        meta = "".join(f'<div class="cm"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k, v in meta_rows)
        classification = f'<div class="classif">{esc(r["classification"])}</div>' if r.get("classification") else ""
        return f"""
<section class="cover" style="--p:{b['primary']};--a:{b['accent']}">
  <div class="cover-top">{logo}<div class="spacer"></div>{clogo}{classification}</div>
  <div class="cover-mid">
    <div class="eyebrow">{esc(r.get('eyebrow') or 'Cisco Secure Access')}</div>
    <h1>{esc(r.get('title') or 'Executive Security Report')}</h1>
    {f'<div class="subtitle">{esc(r.get("subtitle"))}</div>' if r.get('subtitle') else ''}
    {pill}
  </div>
  <div class="cover-meta">{meta}</div>
  <svg class="cover-art" viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <g fill="none" stroke="#fff" stroke-opacity="0.09">
      <circle cx="420" cy="180" r="90"/><circle cx="420" cy="180" r="150"/><circle cx="420" cy="180" r="210"/>
      <circle cx="420" cy="180" r="270"/><circle cx="420" cy="180" r="330"/>
    </g>
    <circle cx="420" cy="180" r="34" fill="{b['accent']}" fill-opacity="0.55"/>
  </svg>
</section>"""

    # -- executive summary
    def exec_summary(self) -> str:
        posture = self.d.get("posture") or {}
        summary = self.d.get("summary") or []
        parts = []
        if posture.get("headline"):
            level = (posture.get("level") or "good").lower()
            parts.append(f'<div class="headline hl-{esc(level)}">{esc(posture["headline"])}</div>')
        if summary:
            parts.append('<ul class="summary">' + "".join(f"<li>{esc(s)}</li>" for s in summary) + "</ul>")
        return self.section("exec_summary", ["".join(parts), self.kpis()])

    def kpis(self) -> str:
        items = self.d.get("kpis") or []
        if not items:
            return ""
        out = ['<div class="kpis">']
        for k in items[:8]:
            tone = (k.get("tone") or "").lower()
            out.append(
                f'<div class="kpi tone-{esc(tone)}"><div class="kpi-v">{fmt_value(k.get("value"), k.get("format"))}</div>'
                f'<div class="kpi-l">{esc(k.get("label"))}</div>'
                + (f'<div class="kpi-n">{esc(k.get("note"))}</div>' if k.get("note") else "")
                + "</div>"
            )
        out.append("</div>")
        return "".join(out)

    def trend(self) -> str:
        t = self.d.get("trend") or {}
        svg = trend_svg(t.get("series") or [], self.brand, self.L)
        return self.section("trend", f'<div class="card">{svg}</div>' if svg else "", cls="keep")

    def layers(self) -> str:
        layers = [l for l in (self.d.get("layers") or []) if num(l.get("requests")) > 0 or num(l.get("blocked")) > 0]
        if not layers:
            return ""
        b = self.brand
        palette = [b["danger"], b["accent"], b["warn"], b["accent2"], b["primary"], "#8E7CC3", "#7F8C8D"]
        total_blocked = sum(num(l.get("blocked")) for l in layers)
        donut = donut_svg([(l.get("name", ""), num(l.get("blocked"))) for l in layers], palette,
                          fmt_compact(total_blocked), self.L["blocked"])
        rows = []
        for i, l in enumerate(layers):
            req, blk = num(l.get("requests")), num(l.get("blocked"))
            rate = (blk / req * 100) if req else 0
            share = (blk / total_blocked * 100) if total_blocked else 0
            sw = f'<i class="sw" style="background:{palette[i % len(palette)]}"></i>'
            rows.append([f"{sw}{esc(l.get('name'))}", fmt_int(req), fmt_int(blk), fmt_pct(rate), fmt_pct(share, 1)])
        tbl = self.table([self.L["layer"], self.L["requests"], self.L["blocked"], self.L["block_rate"], self.L["share_blocks"]],
                         rows, {1, 2, 3, 4})
        body = f'<div class="split"><div class="split-chart">{donut}</div><div class="split-main">{tbl}</div></div>' if donut else tbl
        return self.section("layers", body, cls="keep")

    def threats(self) -> str:
        t = self.d.get("threats") or {}
        items = t.get("items") or []
        ips = self.d.get("ips") or []
        parts = []
        if items:
            rows = [[esc(i.get("name")), esc(i.get("type") or "—"), fmt_int(i.get("count"))] for i in items[:10]]
            parts.append(self.blk(None, self.table([self.L["threat"], self.L["type"], self.L["count"]], rows, {2})))
        elif t.get("show_empty", True) and (t or ips or self.d.get("layers")):
            parts.append(f'<div class="callout ok">{esc(t.get("note") or self.L["no_threats"])}</div>')
        if ips:
            rows = [[esc(i.get("signature")), esc(i.get("description") or "—"), fmt_int(i.get("blocked")), esc(i.get("last_seen") or "—")]
                    for i in ips[:10]]
            parts.append(self.blk(self.L["ips_title"], self.table([self.L["signature"], self.L["type"], self.L["blocked"], self.L["last_seen"]], rows, {2})))
        ev = t.get("event_types") or []
        if ev:
            parts.append(self.blk(self.L["event_types"], hbars(ev, "name", "count", self.brand["warn"], max_items=6, value_fmt=fmt_int)))
        return self.section("threats", parts)

    def usage(self) -> str:
        cats = self.d.get("categories") or []
        dests = self.d.get("destinations") or []
        cols = []
        if cats:
            cols.append(f'<div class="col"><h3>{esc(self.L["top_categories"])}</h3>{hbars(cats, "name", "count", self.brand["accent"])}</div>')
        if dests:
            cols.append(f'<div class="col"><h3>{esc(self.L["top_destinations"])}</h3>{hbars(dests, "name", "requests", self.brand["primary"])}</div>')
        return self.section("usage", f'<div class="cols">{"".join(cols)}</div>' if cols else "")

    def users(self) -> str:
        ids = self.d.get("identities") or []
        apps = self.d.get("private_apps") or []
        parts = []
        if ids:
            rows = [[esc(i.get("name")), esc(i.get("type") or "—"), fmt_compact(i.get("requests")), fmt_int(i.get("blocked"))] for i in ids[:8]]
            parts.append(self.blk(self.L["top_identities"], self.table([self.L["identity"], self.L["type"], self.L["requests"], self.L["blocked"]], rows, {2, 3})))
        if apps:
            parts.append(self.blk(self.L["private_apps"], hbars(apps, "name", "count", self.brand["accent2"], value_fmt=fmt_int)))
        return self.section("users", parts)

    def infra(self) -> str:
        inf = self.d.get("infrastructure") or {}
        parts = []
        tunnels = inf.get("tunnels") or []
        roaming = inf.get("roaming") or []

        def status_cell(s):
            s0 = str(s or "—")
            good = s0.lower() in ("connected", "up", "protected", "active", "online", "va", "encrypted")
            return f'<span class="st {"st-ok" if good else "st-warn"}"><i></i>{esc(s0)}</span>'

        if tunnels:
            rows = [[esc(t.get("name")), esc(t.get("type") or "—"), status_cell(t.get("status")), esc(t.get("hubs_up") or "—")] for t in tunnels]
            parts.append(self.blk(self.L["tunnels"], self.table([self.L["tunnel"], self.L["type"], self.L["status"], self.L["hubs"]], rows)))
        if roaming:
            rows = [[esc(r.get("name")), esc(r.get("os") or "—"), status_cell(r.get("status")), esc(r.get("version") or "—")] for r in roaming[:15]]
            more = f'<p class="muted">+ {len(roaming) - 15}</p>' if len(roaming) > 15 else ""
            parts.append(self.blk(self.L["roaming"], self.table([self.L["device"], self.L["os"], self.L["status"], self.L["version"]], rows) + more))
        return self.section("infra", parts)

    def findings(self) -> str:
        items = self.d.get("findings") or []
        if not items:
            return ""
        out = ['<div class="findings">']
        for f in items:
            out.append(
                f'<div class="finding sevb-{esc((f.get("severity") or "info").lower())}">'
                f'<div class="f-head">{self.sev_badge(f.get("severity"))}<b>{esc(f.get("title"))}</b></div>'
                f'<p>{esc(f.get("detail"))}</p></div>'
            )
        out.append("</div>")
        return self.section("findings", "".join(out))

    def recs(self) -> str:
        items = self.d.get("recommendations") or []
        if not items:
            return ""
        rows = []
        for r in items:
            p = str(r.get("priority") or "").upper()
            pcls = {"P1": "high", "P2": "medium", "P3": "low"}.get(p, "info")
            rows.append([f'<span class="badge sev-{pcls}">{esc(p or "—")}</span>',
                         f'<b>{esc(r.get("action"))}</b>', esc(r.get("rationale") or ""), esc(r.get("owner") or "—")])
        return self.section("recs", self.table([self.L["priority"], self.L["action"], self.L["rationale"], self.L["owner"]], rows), cls="recs")

    def method(self) -> str:
        m = self.d.get("methodology")
        if not m:
            return ""
        if isinstance(m, list):
            body = '<ul class="method">' + "".join(f"<li>{esc(x)}</li>" for x in m) + "</ul>"
        else:
            body = f'<p class="method">{esc(m)}</p>'
        return self.section("method", body, cls="appendix")


    # -- workforce activity
    ACT_COLORS = {
        "remote_active": ("#0B6FA4", "#fff"), "remote_connected": ("#BFE3F4", "#0B2545"),
        "office_active": ("#0B2545", "#fff"), "office_connected": ("#C9D3E0", "#0B2545"),
        "seen_active": ("#13A89E", "#fff"), "seen_connected": ("#BCE8E4", "#0B2545"),
        "none": ("#F1F3F6", "#9AA5B1"),
    }

    def act_overview(self) -> str:
        a = self.d.get("activity") or {}
        sm = a.get("summary") or {}
        if not sm:
            return ""
        L = self.L
        tiles = [
            (L["act_people"], fmt_int(sm.get("people")), ""),
            (L["act_workdays"], fmt_int(sm.get("workdays")), ""),
            (L["act_avg_conn"], f'{num(sm.get("avg_connected_hours")):.1f}', ""),
            (L["act_avg_active"], f'{num(sm.get("avg_active_hours")):.1f}' if sm.get("measurable") else "—", ""),
            (L["act_avg_remote"], f'{num(sm.get("avg_remote_days")):.1f}', ""),
            (L["act_never"], fmt_int(sm.get("never_connected")), "warn" if sm.get("never_connected") else ""),
        ]
        kp = '<div class="kpis kpis-6">' + "".join(
            f'<div class="kpi tone-{t}"><div class="kpi-v">{esc(v)}</div><div class="kpi-l">{esc(l)}</div></div>' for l, v, t in tiles) + "</div>"
        return self.section("act_overview", kp)

    def act_grid(self) -> str:
        a = self.d.get("activity") or {}
        people = a.get("people") or []
        dates = (a.get("period") or {}).get("dates") or []
        if not people or not dates:
            return ""
        wd = set((a.get("period") or {}).get("workdays") or [])
        names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        heb = ["ב׳", "ג׳", "ד׳", "ה׳", "ו׳", "ש׳", "א׳"]
        heads = []
        for ds in dates:
            d = parse_date(ds)
            off = names[d.weekday()] not in wd
            lbl = heb[d.weekday()] if self.lang == "he" else d.strftime("%a")[:2]
            heads.append(f'<th class="{"off" if off else ""}"><span>{esc(lbl)}</span><b>{d.day}</b></th>')
        rows = []
        for p in people:
            cells = []
            for ds in dates:
                day = (p.get("days") or {}).get(ds) or {"status": "none"}
                st = day.get("status", "none")
                bg, fg = self.ACT_COLORS.get(st, self.ACT_COLORS["none"])
                ah = day.get("active_hours")
                txt = f"{ah:g}" if ah else ("·" if st != "none" else "")
                tip = f'{ds}: {self.L.get("lg_" + st, st)}'
                if day.get("first"):
                    tip += f' {day["first"]}–{day["last"]}'
                cells.append(f'<td style="background:{bg};color:{fg}" title="{esc(tip)}">{esc(txt)}</td>')
            dept = f'<span class="g-dept">{esc(p.get("department"))}</span>' if p.get("department") else ""
            rows.append(f'<tr><th class="g-name">{esc(p.get("name"))}{dept}</th>{"".join(cells)}</tr>')
        used = {((p.get("days") or {}).get(ds) or {}).get("status", "none") for p in people for ds in dates}
        order = ["remote_active", "remote_connected", "office_active", "office_connected", "seen_active", "seen_connected", "none"]
        legend = '<div class="g-legend">' + "".join(
            f'<span><i style="background:{self.ACT_COLORS[k][0]}"></i>{esc(self.L["lg_" + k])}</span>' for k in order if k in used
        ) + f'<span class="muted">{esc(self.L["lg_cell"])}</span></div>'
        grid = (f'<table class="grid"><thead><tr><th class="g-name"></th>{"".join(heads)}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table>')
        return self.section("act_grid", [legend + grid])

    def act_table(self) -> str:
        a = self.d.get("activity") or {}
        people = a.get("people") or []
        if not people:
            return ""
        L = self.L
        nm = f'<span class="muted">{esc(L["act_nm"])}</span>'
        rows = []
        for p in people:
            m = p.get("metrics") or {}
            ok = p.get("signal") == "ok"
            wdays = m.get("workdays") or 0
            rows.append([
                f'<b>{esc(p.get("name"))}</b>' + (f'<br><span class="muted">{esc(p.get("department"))}</span>' if p.get("department") else ""),
                f'{fmt_int(m.get("days_connected"))} / {fmt_int(wdays)}',
                fmt_int(m.get("days_remote")),
                fmt_int(m.get("days_active")) if ok else nm,
                esc(m.get("avg_first") or "—") if ok else "—",
                esc(m.get("avg_last") or "—") if ok else "—",
                f'{num(m.get("avg_active_hours")):.1f}' if ok else "—",
                f'{num(m.get("offday_active_hours")):g}' if ok else "—",
                f'<span class="nw">{esc(short_ts(m.get("last_seen")))}</span>',
            ])
        tbl = self.table([L["act_person"], L["act_days_conn"], L["act_days_remote"], L["act_days_active"], L["act_first"],
                          L["act_last"], L["act_hours"], L["act_offday"], L["act_last_seen"]], rows, {1, 2, 3, 4, 5, 6, 7})
        return self.section("act_table", [f'<div class="act-tbl">{tbl}</div>'])

    def act_notes(self) -> str:
        a = self.d.get("activity") or {}
        if not a:
            return ""
        st, per, sm = a.get("settings") or {}, a.get("period") or {}, a.get("summary") or {}
        vals = {"mult": f'{num(st.get("baseline_multiplier"), 3):g}', "amin": f'{num(st.get("active_min_per_hour"), 30):g}',
                "tz": per.get("tz", "UTC"), "bucket": f'{num(per.get("bucket_hours"), 1):g}',
                "recv": sm.get("windows_received", "—"), "exp": sm.get("windows_expected", "—")}
        items = [self.L[f"act_note_{i}"].format(**vals) for i in range(1, 8)]
        return self.section("act_notes", '<ul class="notes">' + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>", cls="notes-sec")

    # -- assemble
    def render(self) -> str:
        b = self.brand
        body = "".join([
            self.exec_summary(), self.findings(), self.trend(), self.layers(), self.threats(),
            self.usage(), self.users(), self.infra(),
            self.act_overview(), self.act_grid(), self.act_table(), self.act_notes(),
            self.recs(), self.method(),
        ])
        r = self.d.get("report") or {}
        title = f'{r.get("title") or "Executive Security Report"} — {r.get("customer") or ""}'.strip(" —")
        dir_ = "rtl" if self.lang == "he" else "ltr"
        footer_txt = " · ".join(x for x in [r.get("customer"), r.get("period_label"), r.get("classification")] if x)
        css = CSS.replace("%PRIMARY%", b["primary"]).replace("%ACCENT%", b["accent"]).replace("%ACCENT2%", b["accent2"]) \
                 .replace("%WARN%", b["warn"]).replace("%DANGER%", b["danger"]).replace("%OK%", b["ok"])
        return f"""<!doctype html>
<html lang="{self.lang}" dir="{dir_}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)}</title>
<style>{css}</style>
</head>
<body>
{self.cover()}
<main class="content">
{body}
</main>
<div class="screen-footer">{esc(footer_txt)}</div>
</body>
</html>"""


CSS = r"""
:root{--p:%PRIMARY%;--a:%ACCENT%;--a2:%ACCENT2%;--warn:%WARN%;--danger:%DANGER%;--ok:%OK%;
--ink:#1B2430;--muted:#5D6B7A;--line:#E3E8EE;--bg:#F5F7FA;--card:#FFFFFF}
*{box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;background:#E9EDF2;color:var(--ink);
font-family:"Segoe UI","Heebo","Assistant","Helvetica Neue",Arial,"DejaVu Sans",sans-serif;font-size:10.5pt;line-height:1.5}
.cover,.content{width:210mm;margin:0 auto;background:#fff}
.content{padding:16mm 18mm 18mm;margin-top:10mm;margin-bottom:10mm;box-shadow:0 2px 18px rgba(11,37,69,.08)}
/* cover */
.cover{position:relative;overflow:hidden;min-height:297mm;background:linear-gradient(155deg,var(--p) 0%,#123B6B 62%,#0E4E7E 100%);
color:#fff;padding:18mm 18mm 20mm;display:flex;flex-direction:column;margin-top:10mm}
.cover-art{position:absolute;right:-48mm;top:-28mm;width:190mm;height:190mm;pointer-events:none}
[dir=rtl] .cover-art{right:auto;left:-48mm;transform:scaleX(-1)}
.cover-top{display:flex;align-items:center;gap:6mm;position:relative;z-index:1}
.cover-top .spacer{flex:1}
.logo{height:11mm;filter:brightness(0) invert(1)}
.clogo{height:12mm;background:#fff;border-radius:2mm;padding:1.5mm 2.5mm}
.classif{font-size:8pt;letter-spacing:.14em;text-transform:uppercase;border:1px solid rgba(255,255,255,.45);padding:1.2mm 3mm;border-radius:10mm}
.cover-mid{flex:1;display:flex;flex-direction:column;justify-content:center;position:relative;z-index:1;max-width:150mm}
.eyebrow{font-size:10pt;letter-spacing:.2em;text-transform:uppercase;color:#9FD8F0;margin-bottom:5mm}
[dir=rtl] .eyebrow{letter-spacing:.05em}
.cover h1{font-size:34pt;line-height:1.1;margin:0 0 5mm;font-weight:700;letter-spacing:-.01em}
.subtitle{font-size:14pt;color:#D6E6F2;font-weight:300;margin-bottom:8mm}
.pill{display:inline-flex;align-items:center;gap:2.5mm;align-self:flex-start;background:rgba(255,255,255,.1);
border:1px solid rgba(255,255,255,.25);border-radius:10mm;padding:2mm 5mm;font-size:10pt}
.pill .dot{width:3mm;height:3mm;border-radius:50%}
.pill-good .dot{background:#4ED19A}.pill-watch .dot{background:#F5C451}.pill-risk .dot{background:#FF6B61}
.cover-meta{display:grid;grid-template-columns:repeat(2,1fr);gap:5mm 10mm;border-top:1px solid rgba(255,255,255,.25);padding-top:7mm;position:relative;z-index:1}
.cm span{display:block;font-size:8pt;text-transform:uppercase;letter-spacing:.12em;color:#9FB7CC}
[dir=rtl] .cm span{letter-spacing:.02em}
.cm b{font-size:11.5pt;font-weight:600}
/* sections */
.sec{margin:0 0 11mm;break-inside:auto}
.sec.keep{break-inside:avoid}
.lead,.blk{break-inside:avoid}
.lead:has(.grid),.lead:has(.act-tbl){break-inside:auto}
.sec-head,.g-legend{break-after:avoid}
.act-tbl thead,.grid thead{display:table-header-group}
.blk{margin-top:0}
.sec-head+.insight,.sec-head+.kpis,.sec-head+.card,.sec-head+.tbl{break-before:avoid}
.sec-head{display:flex;align-items:baseline;gap:3.5mm;border-bottom:2px solid var(--p);padding-bottom:2mm;margin-bottom:4.5mm;break-after:avoid}
.sec-no{font-size:10pt;font-weight:700;color:var(--a);font-variant-numeric:tabular-nums}
h2{font-size:16pt;margin:0;color:var(--p);font-weight:700;letter-spacing:-.005em}
h3{font-size:10.5pt;margin:6mm 0 2.5mm;color:var(--p);text-transform:uppercase;letter-spacing:.06em;font-weight:700;break-after:avoid}
[dir=rtl] h3{letter-spacing:0}
.insight{margin:0 0 4mm;padding:3mm 4mm;background:#EEF6FB;border-inline-start:3px solid var(--a);color:#24384D;border-radius:0 1.5mm 1.5mm 0}
[dir=rtl] .insight{border-radius:1.5mm 0 0 1.5mm}
.headline{font-size:13.5pt;font-weight:600;line-height:1.4;color:var(--p);margin-bottom:4mm}
.summary{margin:0 0 6mm;padding-inline-start:5mm}
.summary li{margin-bottom:2mm}
.summary li::marker{color:var(--a)}
/* KPIs */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:3.5mm;break-inside:avoid}
.kpi{background:var(--bg);border-radius:2.5mm;padding:4mm 4mm 3.5mm;border-top:3px solid var(--a)}
.kpi.tone-good{border-top-color:var(--ok)}.kpi.tone-warn{border-top-color:var(--warn)}.kpi.tone-bad{border-top-color:var(--danger)}
.kpi-v{font-size:19pt;font-weight:700;color:var(--p);line-height:1.1;font-variant-numeric:tabular-nums;direction:ltr;unicode-bidi:isolate}
[dir=rtl] .kpi-v{text-align:right}
.kpi-l{font-size:8.6pt;color:var(--muted);margin-top:1.2mm;font-weight:600}
.kpi-n{font-size:7.8pt;color:var(--muted);margin-top:.8mm}
/* charts */
.card{background:#fff;border:1px solid var(--line);border-radius:2.5mm;padding:4mm;break-inside:avoid}
.chart{width:100%;height:auto;display:block}
.chart .grid{stroke:#E8EDF3;stroke-width:1}
.chart .axis{font-size:10px;fill:#6B7A89;font-family:inherit}
.legend{display:flex;gap:6mm;font-size:8.5pt;color:var(--muted);margin-top:1mm;padding-inline-start:2mm}
.legend i{display:inline-block;width:3mm;height:3mm;border-radius:.8mm;margin-inline-end:1.5mm;vertical-align:-1px}
.split{display:flex;gap:6mm;align-items:center;break-inside:avoid}
.split-chart{flex:0 0 48mm}.split-main{flex:1}
.donut{width:48mm;height:48mm}
.donut-v{font-size:22px;font-weight:700;fill:var(--p);font-family:inherit}
.donut-l{font-size:10px;fill:#6B7A89;font-family:inherit;text-transform:uppercase;letter-spacing:.08em}
.sw{display:inline-block;width:2.6mm;height:2.6mm;border-radius:.6mm;margin-inline-end:2mm;vertical-align:0}
.hbars{display:flex;flex-direction:column;gap:2mm;break-inside:avoid}
.hb-row{display:grid;grid-template-columns:42% 1fr 15mm;align-items:center;gap:2.5mm;font-size:9pt}
.hb-label{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hb-sub{color:var(--muted);font-size:8pt;margin-inline-start:1.5mm}
.hb-track{background:#EEF2F6;border-radius:1mm;height:3.4mm;overflow:hidden}
.hb-fill{height:100%;border-radius:1mm}
.hb-val{text-align:end;font-variant-numeric:tabular-nums;font-weight:600;color:var(--p);direction:ltr;unicode-bidi:isolate}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:8mm}
.cols .col h3{margin-top:0}
/* tables */
.tbl{width:100%;border-collapse:collapse;font-size:9pt;break-inside:auto}
.tbl th{text-align:start;font-size:7.8pt;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:700;
padding:2mm 2.5mm;border-bottom:1.5px solid var(--p)}
[dir=rtl] .tbl th{letter-spacing:0}
.tbl td{padding:2.3mm 2.5mm;border-bottom:1px solid var(--line);vertical-align:top}
.tbl tr{break-inside:avoid}
.tbl tbody tr:nth-child(even) td{background:#FAFBFD}
.tbl td:first-child{white-space:nowrap}
.tbl .n{text-align:end;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl td.n{direction:ltr;unicode-bidi:isolate}
.recs .tbl td:nth-child(2){width:34%}.recs .tbl td:nth-child(1){width:13mm}
.badge{display:inline-block;font-size:7.5pt;font-weight:700;padding:.6mm 2.2mm;border-radius:1mm;letter-spacing:.04em;white-space:nowrap}
.sev-high{background:#FBE5E3;color:#A1302A}.sev-medium{background:#FDF1DC;color:#8A5A0B}
.sev-low{background:#E3F2EA;color:#1F6B43}.sev-info{background:#E6F1F8;color:#1C5A80}
.st{display:inline-flex;align-items:center;gap:1.5mm;font-weight:600}
.st i{width:2.2mm;height:2.2mm;border-radius:50%}
.st-ok{color:#1F6B43}.st-ok i{background:var(--ok)}.st-warn{color:#8A5A0B}.st-warn i{background:var(--warn)}
/* findings */
.findings{display:grid;grid-template-columns:1fr 1fr;gap:3.5mm}
.finding{background:var(--bg);border-radius:2mm;padding:3.5mm 4mm;border-inline-start:3px solid #9AB;break-inside:avoid}
.finding p{margin:1.5mm 0 0;font-size:9.2pt;color:#34465A}
.f-head{display:flex;gap:2.5mm;align-items:center}
.sevb-high{border-inline-start-color:var(--danger)}.sevb-medium{border-inline-start-color:var(--warn)}
.sevb-low{border-inline-start-color:var(--ok)}.sevb-info{border-inline-start-color:var(--a)}
.callout{padding:3.5mm 4mm;border-radius:2mm;font-weight:600}
.callout.ok{background:#E8F5EE;color:#1F6B43}
.muted{color:var(--muted)}
.method{color:#45566A;font-size:9pt}
.method li{margin-bottom:1.2mm}
.screen-footer{width:210mm;margin:0 auto 10mm;text-align:center;font-size:8pt;color:#7A8796}

/* workforce activity */
.kpis-6{grid-template-columns:repeat(3,1fr)}
.grid{border-collapse:separate;border-spacing:1.2px;width:100%;table-layout:fixed;font-size:7.5pt}
.grid th,.grid td{text-align:center;padding:0;height:6.2mm;border-radius:1mm;font-variant-numeric:tabular-nums}
.grid td{font-weight:700}
.grid thead th{font-weight:600;color:var(--muted);height:auto;padding-bottom:1mm;line-height:1.15}
.grid thead th span{display:block;font-size:6.5pt;text-transform:uppercase}
.grid thead th b{display:block;font-size:8pt;color:var(--ink)}
.grid thead th.off b,.grid thead th.off span{color:#B0B8C2}
.grid th.g-name{width:38mm;text-align:start;padding-inline-end:2mm;font-weight:600;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.g-dept{display:block;font-weight:400;color:var(--muted);font-size:6.8pt}
.grid tr{break-inside:avoid}
.grid thead{display:table-header-group}
.g-legend{display:flex;flex-wrap:wrap;gap:2mm 5mm;font-size:8pt;color:var(--muted);margin-bottom:3mm}
.g-legend i{display:inline-block;width:3mm;height:3mm;border-radius:.8mm;margin-inline-end:1.5mm;vertical-align:-1px}
.act-tbl .tbl{font-size:8.2pt;table-layout:auto}
.act-tbl .tbl th{white-space:normal;letter-spacing:.02em;line-height:1.25;vertical-align:bottom}
.act-tbl .tbl td{padding:2mm 1.6mm}
.act-tbl .tbl td:first-child{white-space:normal;min-width:32mm}
.nw{white-space:nowrap;direction:ltr;unicode-bidi:isolate;display:inline-block}
.notes{margin:0;padding-inline-start:5mm;color:#34465A;font-size:9pt}
.notes li{margin-bottom:1.6mm}
.notes-sec .lead{background:#FBF7EE;border-radius:2mm;padding:0 4mm 3mm}
.notes-sec .sec-head{border-bottom-color:var(--warn)}
@media print{
  body{background:#fff}
  .cover,.content{margin:0;box-shadow:none;width:auto}
  .cover{min-height:auto;height:297mm;break-after:page;padding:18mm}
  .content{padding:0}
  .screen-footer{display:none}
  .sec.recs,.sec.appendix{break-before:auto}
}
@page{size:A4;margin:16mm 16mm 18mm}
@page:first{margin:0}
@media screen and (max-width:820px){
  .cover,.content,.screen-footer{width:auto;margin:0}
  .content{padding:6mm 4.5mm}
  .kpis{grid-template-columns:repeat(2,1fr)}
  .cols,.findings{grid-template-columns:1fr}
  .split{flex-direction:column}
  .cover{min-height:auto;padding:10mm 6mm}
  .cover h1{font-size:24pt}
}
"""


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def to_pdf(html_path: str, pdf_path: str, footer_text: str, lang: str) -> str | None:
    L = LABELS.get(lang, LABELS["en"])
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        footer = (
            '<div style="width:100%;font-size:7.5px;color:#7A8796;padding:0 16mm;display:flex;justify-content:space-between;'
            f'font-family:Segoe UI,Arial,sans-serif;direction:{"rtl" if lang == "he" else "ltr"}">'
            f'<span>{esc(footer_text)}</span>'
            f'<span>{esc(L["page"])} <span class="pageNumber"></span> {esc(L["of"])} <span class="totalPages"></span></span></div>'
        )
        try:
            from pypdf import PdfReader, PdfWriter  # type: ignore
        except ImportError:
            PdfReader = PdfWriter = None  # type: ignore
        url = "file://" + os.path.abspath(html_path)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_timeout(300)
            if PdfReader is None:
                page.pdf(path=pdf_path, format="A4", print_background=True, prefer_css_page_size=True,
                         display_header_footer=True, header_template="<div></div>", footer_template=footer)
            else:
                # Two passes so the cover carries no footer and body pages are numbered.
                cover_tmp, body_tmp = pdf_path + ".cover.tmp", pdf_path + ".body.tmp"
                page.add_style_tag(content=".content{display:none!important}")
                page.pdf(path=cover_tmp, format="A4", print_background=True, prefer_css_page_size=True)
                page.goto(url)
                page.add_style_tag(content=".cover{display:none!important}@page:first{margin:16mm 16mm 18mm}")
                page.wait_for_timeout(200)
                page.pdf(path=body_tmp, format="A4", print_background=True, prefer_css_page_size=True,
                         display_header_footer=True, header_template="<div></div>", footer_template=footer)
                w = PdfWriter()
                w.add_page(PdfReader(cover_tmp).pages[0])
                for pg in PdfReader(body_tmp).pages:
                    w.add_page(pg)
                with open(pdf_path, "wb") as f:
                    w.write(f)
                os.remove(cover_tmp)
                os.remove(body_tmp)
            browser.close()
        return "playwright"
    except Exception as e:  # noqa: BLE001
        err = e
    try:
        from weasyprint import HTML  # type: ignore

        HTML(filename=html_path).write_pdf(pdf_path)
        return "weasyprint"
    except Exception as e2:  # noqa: BLE001
        print(f"PDF export unavailable ({type(err).__name__}: {err}; {type(e2).__name__}). "
              "Open the HTML and use Print > Save as PDF.", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_json")
    ap.add_argument("--out", default=".")
    ap.add_argument("--name", default=None, help="output file stem (default derived from customer and date)")
    ap.add_argument("--pdf", action="store_true", help="also export a PDF")
    a = ap.parse_args()

    with open(a.report_json, encoding="utf-8") as f:
        data = json.load(f)
    base_dir = os.path.dirname(os.path.abspath(a.report_json))
    doc = Doc(data, base_dir)
    out_html = doc.render()

    r = data.get("report") or {}
    stem = a.name or "_".join(
        x for x in ["SecureAccess_Executive_Report", "".join(c for c in (r.get("customer") or "") if c.isalnum() or c in "-_"),
                    (r.get("generated_on") or date.today().isoformat())] if x)
    os.makedirs(a.out, exist_ok=True)
    html_path = os.path.join(a.out, stem + ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(out_html)
    print(f"HTML: {html_path}")
    print(f"Sections: {', '.join(doc.toc)}")
    if a.pdf:
        pdf_path = os.path.join(a.out, stem + ".pdf")
        footer = " · ".join(x for x in [r.get("customer"), r.get("period_label"), r.get("classification")] if x)
        engine = to_pdf(html_path, pdf_path, footer, doc.lang)
        if engine:
            print(f"PDF:  {pdf_path} (via {engine})")


if __name__ == "__main__":
    main()
