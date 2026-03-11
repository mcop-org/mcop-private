from __future__ import annotations

from pathlib import Path


def _safe(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _money(value: object) -> str:
    try:
        return f"GBP {float(value):,.0f}"
    except Exception:
        return "GBP -"


def _number(value: object, digits: int = 1) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return "-"


def _percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.0f}%"
    except Exception:
        return "-"


def _intish(value: object) -> str:
    try:
        return f"{int(round(float(value)))}"
    except Exception:
        return "-"


def _kg(value: object) -> str:
    try:
        return f"{float(value):,.0f} kg"
    except Exception:
        return "- kg"


def _status_class(flag: object) -> str:
    text = str(flag or "").upper()
    if text in {"OK", "GREEN"}:
        return "status-green"
    if text in {"WATCH", "AMBER", "WARNING"}:
        return "status-amber"
    if text in {"BLOCK", "RED"}:
        return "status-red"
    return "status-neutral"


def _status_rank(flag: object) -> int:
    text = str(flag or "").upper()
    order = {"BLOCK": 0, "RED": 0, "WATCH": 1, "AMBER": 1, "OK": 2, "GREEN": 2}
    return order.get(text, 3)


def _sort_event_rows(rows: object) -> list[dict]:
    events = [row for row in (rows or []) if isinstance(row, dict)]
    return sorted(
        events,
        key=lambda row: (
            str(row.get("date") or ""),
            -float(row.get("amount", 0.0) or 0.0),
            str(
                row.get("label")
                or row.get("product_reference")
                or row.get("product_id")
                or ""
            ),
        ),
    )


def _sort_risk_rows(rows: object) -> list[dict]:
    risks = [row for row in (rows or []) if isinstance(row, dict)]
    return sorted(
        risks,
        key=lambda row: (
            999999 if row.get("days_to_landing") is None else int(row.get("days_to_landing")),
            -float(row.get("shortfall_value_gbp", 0.0) or 0.0),
            str(row.get("product_reference") or row.get("product_id") or ""),
        ),
    )


def _extract_actions(payload: dict) -> list[str]:
    action_lines: list[str] = []
    prefixes = ("Action:", "Priority:", "7-day target:", "This week's move:", "This week’s move:")
    for item in payload.get("summary", []) or []:
        if not isinstance(item, str):
            continue
        if item.startswith(prefixes):
            action_lines.append(item)
    return sorted(set(action_lines))[:5]


def _extract_summary_lines(payload: dict) -> list[str]:
    lines = []
    for item in payload.get("summary", []) or []:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text.startswith("==="):
            continue
        lines.append(text)
    return lines[:12]


def _extract_alerts(payload: dict) -> list[tuple[str, str]]:
    alerts: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for label, value in (
        ("Liquidity", payload.get("status_flag")),
        ("Exposure", payload.get("exposure_flag")),
        ("Cash 14d", (payload.get("pinch_14d") or {}).get("cash_alert")),
        ("Cash 30d", (payload.get("pinch_30d") or {}).get("cash_alert")),
    ):
        pair = (label, str(value or "-"))
        if pair not in seen:
            seen.add(pair)
            alerts.append(pair)
    return sorted(alerts, key=lambda item: (_status_rank(item[1]), item[0]))


def _stacked_meter_svg(items: list[tuple[str, float, str]], total: float, label: str) -> str:
    width = 520
    height = 24
    if total <= 0:
        return (
            "<svg viewBox='0 0 520 24' role='img' aria-label='No data'>"
            "<rect x='0' y='0' width='520' height='24' rx='12' fill='var(--track)' />"
            "</svg>"
        )

    x = 0.0
    parts = [f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='{_safe(label)}'>"]
    for _, value, color in items:
        segment = max(float(value or 0.0), 0.0)
        seg_width = (segment / total) * width
        if seg_width <= 0:
            continue
        parts.append(
            f"<rect x='{x:.3f}' y='0' width='{seg_width:.3f}' height='{height}' rx='12' fill='{color}' />"
        )
        x += seg_width
    parts.append("</svg>")
    return "".join(parts)


def _hbar_chart_svg(rows: list[tuple[str, float, str]], max_value: float, label: str) -> str:
    width = 520
    row_height = 34
    label_x = 0
    bar_x = 180
    chart_width = 320
    total_height = max(len(rows), 1) * row_height
    parts = [f"<svg viewBox='0 0 {width} {total_height}' role='img' aria-label='{_safe(label)}'>"]
    if max_value <= 0:
        parts.append(
            f"<text x='{bar_x}' y='{row_height / 2:.1f}' fill='var(--muted)' font-size='12'>No items</text>"
        )
    else:
        for idx, (name, value, color) in enumerate(rows):
            y = idx * row_height
            bar_width = (max(float(value or 0.0), 0.0) / max_value) * chart_width
            parts.append(
                f"<text x='{label_x}' y='{y + 20}' fill='var(--muted)' font-size='12'>{_safe(name)}</text>"
            )
            parts.append(
                f"<rect x='{bar_x}' y='{y + 6}' width='{chart_width}' height='14' rx='7' fill='var(--track)' />"
            )
            parts.append(
                f"<rect x='{bar_x}' y='{y + 6}' width='{bar_width:.3f}' height='14' rx='7' fill='{color}' />"
            )
        parts.append("</svg>")
    return "".join(parts)


def _compact_date(value: object) -> str:
    text = str(value or "")
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return f"{text[5:7]}/{text[8:10]}"
    return text or "-"


def _stacked_column_chart_svg(rows: list[dict], label: str) -> str:
    width = 560
    height = 260
    left = 28
    right = 18
    top = 20
    bottom = 42
    inner_width = width - left - right
    inner_height = height - top - bottom
    count = max(len(rows), 1)
    slot = inner_width / count
    bar_width = min(42.0, slot * 0.56)
    max_total = max([float(row.get("total", 0.0) or 0.0) for row in rows] + [1.0])
    parts = [f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='{_safe(label)}'>"]
    parts.append(
        f"<line x1='{left}' y1='{top + inner_height}' x2='{width - right}' y2='{top + inner_height}' "
        "stroke='var(--line-strong)' stroke-width='1' />"
    )
    if not rows:
        parts.append(
            f"<text x='{left}' y='{top + (inner_height / 2):.1f}' fill='var(--muted)' font-size='12'>No incoming lots</text>"
        )
        parts.append("</svg>")
        return "".join(parts)

    for idx, row in enumerate(rows):
        reserved = max(float(row.get("reserved", 0.0) or 0.0), 0.0)
        unreserved = max(float(row.get("unreserved", 0.0) or 0.0), 0.0)
        total = max(reserved + unreserved, 0.0)
        x = left + idx * slot + (slot - bar_width) / 2
        reserved_height = (reserved / max_total) * inner_height
        unreserved_height = (unreserved / max_total) * inner_height
        base_y = top + inner_height
        parts.append(
            f"<rect x='{x:.3f}' y='{base_y - (reserved_height + unreserved_height):.3f}' width='{bar_width:.3f}' "
            f"height='{reserved_height + unreserved_height:.3f}' rx='14' fill='var(--track-strong)' />"
        )
        if unreserved_height > 0:
            parts.append(
                f"<rect x='{x:.3f}' y='{base_y - unreserved_height:.3f}' width='{bar_width:.3f}' "
                f"height='{unreserved_height:.3f}' rx='14' fill='#d06e3d' />"
            )
        if reserved_height > 0:
            parts.append(
                f"<rect x='{x:.3f}' y='{base_y - (unreserved_height + reserved_height):.3f}' width='{bar_width:.3f}' "
                f"height='{reserved_height:.3f}' rx='14' fill='#2a6a58' />"
            )
        parts.append(
            f"<text x='{x + (bar_width / 2):.3f}' y='{height - 16}' text-anchor='middle' fill='var(--muted)' font-size='11'>{_safe(row.get('label') or '-')}</text>"
        )
        parts.append(
            f"<text x='{x + (bar_width / 2):.3f}' y='{max(top + 12.0, base_y - total / max_total * inner_height - 8):.3f}' text-anchor='middle' fill='var(--muted)' font-size='10'>{_safe(_intish(total / 1000.0))}k</text>"
        )
    parts.append("</svg>")
    return "".join(parts)


def _line_chart_svg(rows: list[tuple[str, float]], label: str) -> str:
    width = 560
    height = 240
    left = 34
    right = 34
    top = 28
    bottom = 38
    inner_width = width - left - right
    inner_height = height - top - bottom
    max_value = max([float(value or 0.0) for _, value in rows] + [1.0])
    parts = [f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='{_safe(label)}'>"]
    base_y = top + inner_height
    parts.append(
        f"<line x1='{left}' y1='{base_y}' x2='{width - right}' y2='{base_y}' stroke='var(--line-strong)' stroke-width='1' />"
    )
    if not rows:
        parts.append(
            f"<text x='{left}' y='{top + (inner_height / 2):.1f}' fill='var(--muted)' font-size='12'>No release activity</text>"
        )
        parts.append("</svg>")
        return "".join(parts)

    if len(rows) == 1:
        points = [(left + inner_width / 2, base_y - (rows[0][1] / max_value) * inner_height)]
    else:
        step = inner_width / (len(rows) - 1)
        points = [
            (left + idx * step, base_y - (float(value or 0.0) / max_value) * inner_height)
            for idx, (_, value) in enumerate(rows)
        ]

    path = " ".join(
        [f"M {points[0][0]:.3f} {points[0][1]:.3f}"] +
        [f"L {x:.3f} {y:.3f}" for x, y in points[1:]]
    )
    area = " ".join(
        [f"M {points[0][0]:.3f} {base_y:.3f}", f"L {points[0][0]:.3f} {points[0][1]:.3f}"] +
        [f"L {x:.3f} {y:.3f}" for x, y in points[1:]] +
        [f"L {points[-1][0]:.3f} {base_y:.3f}", "Z"]
    )
    parts.append(f"<path d='{area}' fill='var(--accent-soft)' />")
    parts.append(f"<path d='{path}' fill='none' stroke='var(--accent)' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' />")
    label_left = left + 10
    label_right = width - right - 10
    for idx, ((x, y), (date_label, value)) in enumerate(zip(points, rows)):
        clamped_x = min(max(x, label_left), label_right)
        if len(points) == 1:
            text_anchor = "middle"
        elif idx == 0:
            text_anchor = "start"
        elif idx == len(points) - 1:
            text_anchor = "end"
        else:
            text_anchor = "middle"
        parts.append(f"<circle cx='{x:.3f}' cy='{y:.3f}' r='4.5' fill='var(--panel-strong)' stroke='var(--accent)' stroke-width='2' />")
        parts.append(f"<text x='{x:.3f}' y='{height - 14}' text-anchor='middle' fill='var(--muted)' font-size='11'>{_safe(date_label)}</text>")
        parts.append(
            f"<text x='{clamped_x:.3f}' y='{max(top + 14.0, y - 12.0):.3f}' text-anchor='{text_anchor}' "
            f"fill='var(--muted)' font-size='10'>{_safe(_intish(value / 1000.0))}k</text>"
        )
    parts.append("</svg>")
    return "".join(parts)


def _render_event_table(title: str, rows: list[dict]) -> str:
    body = []
    for row in rows[:5]:
        label = row.get("label") or row.get("product_reference") or row.get("product_id") or "-"
        body.append(
            "<tr>"
            f"<td>{_safe(row.get('date') or '-')}</td>"
            f"<td>{_safe(label)}</td>"
            f"<td class='num'>{_money(row.get('amount'))}</td>"
            "</tr>"
        )
    if not body:
        body.append("<tr><td colspan='3' class='empty'>No items</td></tr>")

    return (
        "<section class='panel'>"
        f"<div class='section-head'><h3>{_safe(title)}</h3><p>Sorted for deterministic review.</p></div>"
        "<table>"
        "<thead><tr><th>Date</th><th>Reference</th><th class='num'>Amount</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table>"
        "</section>"
    )


def _render_risk_table(rows: list[dict]) -> str:
    body = []
    for row in rows[:5]:
        label = row.get("product_reference") or row.get("product_id") or "-"
        body.append(
            "<tr>"
            f"<td>{_safe(label)}</td>"
            f"<td class='num'>{_money(row.get('shortfall_value_gbp'))}</td>"
            f"<td class='num'>{_intish(row.get('days_to_landing'))}</td>"
            "</tr>"
        )
    if not body:
        body.append("<tr><td colspan='3' class='empty'>No at-risk incoming coffees</td></tr>")

    return (
        "<section class='panel'>"
        "<div class='section-head'><h3>Incoming Pre-sell Gap Queue</h3><p>Highest shortfall by value and landing urgency.</p></div>"
        "<table>"
        "<thead><tr><th>Reference</th><th class='num'>Gap</th><th class='num'>Days</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table>"
        "</section>"
    )


def write_dashboard_html(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    base = payload.get("base", {}) or {}
    container = payload.get("container_exposure", {}) or {}
    landed = payload.get("landed_aging", {}) or {}
    pinch_14d = payload.get("pinch_14d", {}) or {}
    pinch_30d = payload.get("pinch_30d", {}) or {}
    dynamic_precommit = container.get("dynamic_precommit", {}) or {}

    alerts = _extract_alerts(payload)
    actions = _extract_actions(payload)
    summary_lines = _extract_summary_lines(payload)
    payables = _sort_event_rows(payload.get("top_payables_60"))
    receivables = _sort_event_rows(payload.get("top_receivables_60"))
    incoming_risks = _sort_risk_rows(container.get("top_at_risk_incoming"))

    incoming_total_kg = float(container.get("incoming_total_kg") or 0.0)
    incoming_reserved_kg = float(container.get("incoming_reserved_kg") or 0.0)
    incoming_reserved_pct = container.get("incoming_reserved_balance_pct", container.get("incoming_precommitted_pct"))
    incoming_unreserved_kg = max(incoming_total_kg - incoming_reserved_kg, 0.0)
    incoming_total_value = float(container.get("incoming_capital_total_gbp") or 0.0)
    incoming_unreserved_value = float(container.get("incoming_uncommitted_gbp") or 0.0)
    incoming_reserved_value = max(incoming_total_value - incoming_unreserved_value, 0.0)

    aging_buckets = landed.get("buckets", {}) or {}
    top_traps = landed.get("top_cash_traps", []) or []
    top_incoming = container.get("breakdown_top_incoming", []) or []
    incoming_by_landing = container.get("incoming_by_landing_date", []) or []
    reservation_pipeline = payload.get("reservation_pipeline_by_status", []) or []
    released_value_trend = payload.get("released_value_trend", []) or []

    alert_html = "".join(
        f"<div class='status-pill {_status_class(value)}'><span>{_safe(label)}</span><strong>{_safe(value)}</strong></div>"
        for label, value in alerts
    )
    action_html = "".join(
        f"<li><span class='bullet-index'>{idx + 1:02d}</span><span>{_safe(item)}</span></li>"
        for idx, item in enumerate(actions)
    ) or "<li><span class='bullet-index'>00</span><span>No immediate actions</span></li>"
    summary_html = "".join(f"<li>{_safe(item)}</li>" for item in summary_lines) or "<li>No summary lines</li>"

    incoming_landing_chart = _stacked_column_chart_svg(
        [
            {
                "label": _compact_date(row.get("landing_date")),
                "reserved": float(row.get("reserved_value_gbp") or 0.0),
                "unreserved": float(row.get("unreserved_value_gbp") or 0.0),
                "total": float(row.get("total_value_gbp") or 0.0),
            }
            for row in incoming_by_landing[:6]
        ],
        "Incoming reserved versus unreserved by landing date",
    )
    incoming_landing_chart_kg = _stacked_column_chart_svg(
        [
            {
                "label": _compact_date(row.get("landing_date")),
                "reserved": float(row.get("reserved_kg") or 0.0),
                "unreserved": float(row.get("unreserved_kg") or 0.0),
                "total": float(row.get("total_kg") or 0.0),
            }
            for row in incoming_by_landing[:6]
        ],
        "Incoming reserved versus unreserved kg by landing date",
    )

    risk_rows = [
        (
            str(row.get("product_reference") or row.get("product_id") or "-"),
            float(row.get("shortfall_value_gbp") or 0.0),
            "#d06e3d",
        )
        for row in incoming_risks[:5]
    ]
    risk_chart = _hbar_chart_svg(
        risk_rows,
        max([value for _, value, _ in risk_rows] + [1.0]),
        "Top incoming shortfalls",
    )

    aging_rows = [
        ("0-30", float(aging_buckets.get("0_30", 0.0) or 0.0), "#6bb08a"),
        ("30-60", float(aging_buckets.get("30_60", 0.0) or 0.0), "#c2aa52"),
        ("60-90", float(aging_buckets.get("60_90", 0.0) or 0.0), "#d7814e"),
        ("90+", float(aging_buckets.get("90_plus", 0.0) or 0.0), "#c95b49"),
    ]
    aging_chart = _hbar_chart_svg(
        aging_rows,
        max([value for _, value, _ in aging_rows] + [1.0]),
        "Landed aging chart",
    )
    pipeline_rows = [
        (
            str(row.get("status") or "-"),
            float(row.get("value_gbp") or 0.0),
            "#255f52" if str(row.get("status") or "").lower() in {"approved", "completed"} else "#d06e3d",
        )
        for row in reservation_pipeline
    ]
    pipeline_chart = _hbar_chart_svg(
        pipeline_rows,
        max([value for _, value, _ in pipeline_rows] + [1.0]),
        "Reservation pipeline by status",
    )
    release_line_chart = _line_chart_svg(
        [(_compact_date(row.get("date")), float(row.get("value_gbp") or 0.0)) for row in released_value_trend],
        "Released value trend",
    )

    incoming_spotlight = []
    for row in top_incoming[:4]:
        incoming_spotlight.append(
            "<li>"
            f"<strong>{_safe(row.get('product_reference') or row.get('product_id') or '-')}</strong>"
            f"<span>{_money(row.get('incoming_value_gbp'))}</span>"
            f"<em>{_percent(row.get('precommit_pct_product'))} reserved balance</em>"
            "</li>"
        )
    if not incoming_spotlight:
        incoming_spotlight.append("<li><strong>No incoming lots</strong><span>-</span><em>No active incoming exposure</em></li>")

    trap_rows = []
    for row in top_traps[:5]:
        trap_rows.append(
            "<li>"
            f"<strong>{_safe(row.get('label') or '-')}</strong>"
            f"<span>{_money(row.get('unsold_value'))}</span>"
            f"<em>{_intish(row.get('days_since_landing'))} days</em>"
            "</li>"
        )
    if not trap_rows:
        trap_rows.append("<li><strong>No cash traps</strong><span>-</span><em>No landed aging issues</em></li>")

    kpi_cards = [
        ("Cash on Hand", _money(base.get("cash_on_hand")), "Live snapshot from cash history", "tone-neutral"),
        ("Liquidity 60d", _money(base.get("liquidity_60")), "Projected 60-day position", "tone-neutral"),
        ("Runway", f"{_intish(base.get('runway_days'))} days", "Current burn-derived runway", "tone-neutral"),
        ("Trading Health", f"{_number(payload.get('trading_health_score'))}/10", "Composite operating score", "tone-neutral"),
        ("Incoming Reserved Balance", _percent(incoming_reserved_pct), f"{_money(incoming_reserved_value)} reserved across incoming lots", "tone-good"),
        ("Incoming Open Value", _money(incoming_unreserved_value), "Value still open on incoming lots", "tone-warn"),
        ("Value Below Target", _money(dynamic_precommit.get("value_below_target_gbp")), "Incoming value below target pre-sell discipline", "tone-warn"),
        ("Landed Unsold", _money(landed.get("total_unsold_value")), "Capital sitting in landed stock", "tone-alert"),
    ]
    card_html = "".join(
        "<article class='metric-card {tone}'>"
        f"<div class='eyebrow'>{_safe(title)}</div>"
        f"<div class='metric'>{_safe(value)}</div>"
        f"<div class='meta'>{_safe(help_text)}</div>"
        "</article>".format(tone=tone)
        for title, value, help_text, tone in kpi_cards
    )
    incoming_value_cards = (
        "<div class='meter-copy incoming-view' data-exposure-view='value'>"
        "<div class='mini-stat'>"
        "<div class='label'>Reserved value</div>"
        f"<strong>{_money(incoming_reserved_value)}</strong>"
        "</div>"
        "<div class='mini-stat'>"
        "<div class='label'>Unreserved value</div>"
        f"<strong>{_money(incoming_unreserved_value)}</strong>"
        "</div>"
        "</div>"
    )
    incoming_kg_cards = (
        "<div class='meter-copy incoming-view' data-exposure-view='kg' hidden>"
        "<div class='mini-stat'>"
        "<div class='label'>Reserved kg</div>"
        f"<strong>{_kg(incoming_reserved_kg)}</strong>"
        "</div>"
        "<div class='mini-stat'>"
        "<div class='label'>Unreserved kg</div>"
        f"<strong>{_kg(incoming_unreserved_kg)}</strong>"
        "</div>"
        "</div>"
    )

    html = f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MCOP Dashboard v1</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --bg-elevated: rgba(255, 255, 255, 0.84);
      --panel: rgba(255, 255, 255, 0.9);
      --panel-strong: #ffffff;
      --ink: #111827;
      --muted: #667085;
      --line: rgba(17, 24, 39, 0.08);
      --track: rgba(148, 163, 184, 0.18);
      --shadow-lg: 0 24px 60px rgba(15, 23, 42, 0.10);
      --shadow-md: 0 14px 32px rgba(15, 23, 42, 0.08);
      --accent: #255f52;
      --accent-soft: rgba(37, 95, 82, 0.10);
      --warn: #d06e3d;
      --warn-soft: rgba(208, 110, 61, 0.12);
      --alert: #c95b49;
      --alert-soft: rgba(201, 91, 73, 0.12);
      --good: #2f7d62;
      --good-soft: rgba(47, 125, 98, 0.12);
      --navy: #132238;
      --sans: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      --mono: "SFMono-Regular", "Menlo", monospace;
    }}
    html[data-theme="dark"] {{
      --bg: #07111f;
      --bg-elevated: rgba(10, 18, 32, 0.88);
      --panel: rgba(11, 19, 35, 0.92);
      --panel-strong: #111c31;
      --ink: #e5edf8;
      --muted: #93a4bd;
      --line: rgba(148, 163, 184, 0.16);
      --track: rgba(148, 163, 184, 0.18);
      --shadow-lg: 0 24px 60px rgba(0, 0, 0, 0.34);
      --shadow-md: 0 14px 32px rgba(0, 0, 0, 0.24);
      --accent: #5bc0a7;
      --accent-soft: rgba(91, 192, 167, 0.12);
      --warn: #f59f62;
      --warn-soft: rgba(245, 159, 98, 0.14);
      --alert: #f47d6d;
      --alert-soft: rgba(244, 125, 109, 0.14);
      --good: #68d2a8;
      --good-soft: rgba(104, 210, 168, 0.14);
      --navy: #0b1528;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: var(--sans);
      background:
        radial-gradient(circle at top left, rgba(37, 95, 82, 0.18), transparent 30%),
        radial-gradient(circle at top right, rgba(208, 110, 61, 0.14), transparent 28%),
        linear-gradient(180deg, var(--bg) 0%, color-mix(in srgb, var(--bg) 90%, #ffffff 10%) 100%);
    }}
    a {{ color: inherit; text-decoration: none; }}
    button {{ font: inherit; }}
    .app-shell {{
      min-height: 100vh;
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
      gap: 22px;
      padding: 22px;
    }}
    .sidebar {{
      position: sticky;
      top: 22px;
      align-self: start;
      background: var(--bg-elevated);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow-lg);
      padding: 22px 18px;
      backdrop-filter: blur(16px);
    }}
    .brand {{
      padding-bottom: 20px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 20px;
    }}
    .brand-kicker {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    .brand-dot {{
      width: 11px;
      height: 11px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--accent), var(--warn));
      box-shadow: 0 0 0 6px color-mix(in srgb, var(--accent) 15%, transparent);
    }}
    .brand h1 {{
      margin: 14px 0 8px;
      font-size: 28px;
      line-height: 1.05;
      letter-spacing: -0.04em;
    }}
    .brand p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
      font-size: 14px;
    }}
    .sidebar-nav {{
      display: grid;
      gap: 8px;
      margin-bottom: 22px;
    }}
    .nav-link {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 14px;
      border-radius: 16px;
      color: var(--muted);
      border: 1px solid transparent;
      transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease;
    }}
    .nav-link:hover {{
      background: var(--panel);
      border-color: var(--line);
      color: var(--ink);
    }}
    .sidebar-meta {{
      display: grid;
      gap: 12px;
    }}
    .mini-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px;
      box-shadow: var(--shadow-md);
    }}
    .mini-card .label {{
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.10em;
      font-size: 11px;
      margin-bottom: 6px;
    }}
    .mini-card .value {{
      font-size: 22px;
      line-height: 1.05;
      letter-spacing: -0.03em;
    }}
    .main {{
      min-width: 0;
      display: grid;
      gap: 28px;
    }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 12px 16px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: color-mix(in srgb, var(--bg-elevated) 92%, transparent);
      backdrop-filter: blur(18px);
      box-shadow: var(--shadow-md);
    }}
    .topbar-title {{
      display: grid;
      gap: 4px;
    }}
    .topbar-title h2 {{
      margin: 0;
      font-size: 26px;
      line-height: 1;
      letter-spacing: -0.04em;
    }}
    .topbar-title p {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .topbar-controls {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .chip-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .chip, .theme-toggle, .tab-button {{
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--panel);
      color: var(--ink);
      padding: 10px 14px;
      cursor: pointer;
      transition: transform 120ms ease, background-color 120ms ease, border-color 120ms ease;
    }}
    .chip:hover, .theme-toggle:hover, .tab-button:hover {{
      transform: translateY(-1px);
      border-color: color-mix(in srgb, var(--accent) 30%, var(--line));
    }}
    .theme-toggle {{
      padding: 7px 11px;
      font-size: 12px;
      font-weight: 500;
      color: var(--muted);
      background: color-mix(in srgb, var(--panel-strong) 82%, transparent);
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.35fr 0.95fr;
      gap: 18px;
    }}
    .hero-card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow-lg);
    }}
    .hero-card {{
      padding: 24px;
      background:
        linear-gradient(145deg, color-mix(in srgb, var(--accent-soft) 60%, transparent), transparent 42%),
        linear-gradient(180deg, color-mix(in srgb, var(--panel-strong) 88%, transparent), var(--panel));
    }}
    .hero-card h3, .panel h3 {{
      margin: 0;
      font-size: 24px;
      line-height: 1.05;
      letter-spacing: -0.03em;
    }}
    .hero-card p {{
      margin: 12px 0 18px;
      max-width: 60ch;
      color: var(--muted);
      line-height: 1.55;
    }}
    .status-strip {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 9px 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--panel-strong);
      font-size: 13px;
    }}
    .status-pill span {{
      color: var(--muted);
    }}
    .status-green strong {{ color: var(--good); }}
    .status-amber strong {{ color: var(--warn); }}
    .status-red strong {{ color: var(--alert); }}
    .hero-highlights {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .hero-stat {{
      border-radius: 20px;
      padding: 16px;
      background: color-mix(in srgb, var(--panel-strong) 88%, transparent);
      border: 1px solid var(--line);
    }}
    .hero-stat .label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.10em;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .hero-stat .value {{
      font-size: 28px;
      line-height: 1.02;
      letter-spacing: -0.04em;
    }}
    .panel {{
      padding: 22px;
    }}
    .section-stack {{
      display: grid;
      gap: 26px;
    }}
    .section-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 16px;
    }}
    .section-head p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .action-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 12px;
    }}
    .action-list li {{
      display: grid;
      grid-template-columns: 38px minmax(0, 1fr);
      gap: 12px;
      align-items: start;
      padding: 12px;
      border-radius: 18px;
      background: color-mix(in srgb, var(--warn-soft) 45%, var(--panel-strong));
      border: 1px solid var(--line);
    }}
    .bullet-index {{
      display: inline-grid;
      place-items: center;
      width: 38px;
      height: 38px;
      border-radius: 12px;
      background: var(--navy);
      color: #fff;
      font-family: var(--mono);
      font-size: 12px;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }}
    .metric-card {{
      border-radius: 22px;
      padding: 18px;
      border: 1px solid var(--line);
      background: var(--panel);
      box-shadow: var(--shadow-md);
      min-height: 156px;
    }}
    .metric-card.tone-good {{ background: linear-gradient(180deg, var(--good-soft), var(--panel)); }}
    .metric-card.tone-warn {{ background: linear-gradient(180deg, var(--warn-soft), var(--panel)); }}
    .metric-card.tone-alert {{ background: linear-gradient(180deg, var(--alert-soft), var(--panel)); }}
    .eyebrow {{
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.10em;
      font-size: 11px;
      margin-bottom: 10px;
    }}
    .metric {{
      font-size: 34px;
      line-height: 1;
      letter-spacing: -0.05em;
      margin-bottom: 10px;
    }}
    .meta {{
      color: var(--muted);
      line-height: 1.5;
      font-size: 14px;
    }}
    .section-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .subgrid {{
      display: grid;
      gap: 18px;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 14px;
    }}
    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    .chart-note {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    .swatch {{
      width: 12px;
      height: 12px;
      border-radius: 999px;
    }}
    svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .chart-shell {{
      padding: 8px 2px 0;
    }}
    .line-panel {{
      min-height: 100%;
    }}
    .meter-copy {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .meter-copy .mini-stat {{
      padding: 12px;
      border-radius: 16px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
    }}
    .mini-stat strong {{
      display: block;
      margin-top: 4px;
      font-size: 18px;
      letter-spacing: -0.03em;
    }}
    .tab-strip {{
      display: inline-flex;
      gap: 8px;
      margin-bottom: 14px;
      padding: 6px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--panel-strong) 94%, transparent);
      border: 1px solid var(--line);
    }}
    .tab-button.is-active {{
      background: var(--navy);
      color: #fff;
      border-color: transparent;
    }}
    .incoming-toggle {{
      margin-bottom: 10px;
      padding: 4px;
      gap: 4px;
    }}
    .incoming-toggle .tab-button {{
      padding: 7px 11px;
      font-size: 12px;
      font-weight: 600;
    }}
    [hidden] {{ display: none !important; }}
    .rank-list {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 12px;
    }}
    .rank-list li {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px 14px;
      padding: 14px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: var(--panel-strong);
    }}
    .rank-list em {{
      color: var(--muted);
      font-style: normal;
      grid-column: 1 / -1;
    }}
    details {{
      border: 1px solid var(--line);
      border-radius: 20px;
      background: var(--panel-strong);
      overflow: hidden;
    }}
    details summary {{
      cursor: pointer;
      list-style: none;
      padding: 16px 18px;
      font-weight: 600;
    }}
    details summary::-webkit-details-marker {{
      display: none;
    }}
    .detail-body {{
      padding: 0 18px 18px;
      color: var(--muted);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 0;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.10em;
    }}
    .num {{ text-align: right; }}
    .empty {{
      color: var(--muted);
      text-align: center;
      padding: 18px 0;
    }}
    .summary-list {{
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 10px;
    }}
    .foot {{
      padding: 14px 2px 0;
      color: var(--muted);
      font-size: 12px;
      text-align: right;
    }}
    @media (max-width: 1180px) {{
      .app-shell {{
        grid-template-columns: 1fr;
      }}
      .sidebar {{
        position: static;
      }}
      .metric-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 900px) {{
      .hero,
      .section-grid {{
        grid-template-columns: 1fr;
      }}
      .hero-highlights {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 720px) {{
      .app-shell {{
        padding: 14px;
      }}
      .metric-grid {{
        grid-template-columns: 1fr;
      }}
      .topbar {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .meter-copy {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-kicker"><span class="brand-dot"></span> Mercanta Capital Ops</div>
        <h1>MCOP Dashboard v1</h1>
        <p>Modern operating view for liquidity, incoming exposure, landed stock, and next actions.</p>
      </div>
      <nav class="sidebar-nav">
        <a class="nav-link" href="#overview"><span>Overview</span><span>01</span></a>
        <a class="nav-link" href="#incoming"><span>Incoming Exposure</span><span>02</span></a>
        <a class="nav-link" href="#landed"><span>Landed Stock</span><span>03</span></a>
        <a class="nav-link" href="#cashflow"><span>Cash Flow</span><span>04</span></a>
        <a class="nav-link" href="#briefing"><span>Briefing</span><span>05</span></a>
      </nav>
      <div class="sidebar-meta">
        <div class="mini-card">
          <div class="label">Snapshot</div>
          <div class="value">{_safe(base.get("as_of") or "-")}</div>
        </div>
        <div class="mini-card">
          <div class="label">Exposure</div>
          <div class="value">{_safe(payload.get("exposure_flag") or "-")}</div>
        </div>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-title">
          <h2>Modern ops workspace</h2>
          <p>Single-file deterministic dashboard generated from the latest committed dataset and current reporting payload.</p>
        </div>
        <div class="topbar-controls">
          <div class="chip-row">
            <a class="chip" href="#overview">Overview</a>
            <a class="chip" href="#incoming">Incoming</a>
            <a class="chip" href="#landed">Landed</a>
            <a class="chip" href="#cashflow">Cash</a>
          </div>
          <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Toggle light and dark mode">Dark mode</button>
        </div>
      </header>

      <section class="hero" id="overview">
        <article class="hero-card">
          <div class="status-strip">{alert_html}</div>
          <h3>Liquidity and stock risk in one operating surface.</h3>
          <p>The dashboard now separates incoming reservation balance, landed cash traps, and near-term cash view into clearer operational sections. Labels are aligned to the underlying calculations rather than narrative wording.</p>
          <div class="hero-highlights">
            <div class="hero-stat">
              <div class="label">Reserved balance</div>
              <div class="value">{_percent(incoming_reserved_pct)}</div>
            </div>
            <div class="hero-stat">
              <div class="label">Open incoming value</div>
              <div class="value">{_money(incoming_unreserved_value)}</div>
            </div>
            <div class="hero-stat">
              <div class="label">Landed aging flag</div>
              <div class="value">{_safe(landed.get("flag") or "-")}</div>
            </div>
          </div>
        </article>

        <aside class="panel">
          <div class="section-head">
            <h3>Immediate Actions</h3>
            <p>Operational focus pulled from the current summary payload.</p>
          </div>
          <ul class="action-list">{action_html}</ul>
        </aside>
      </section>

      <section class="metric-grid">{card_html}</section>

      <section class="section-grid" id="incoming">
        <section class="panel">
          <div class="section-head">
            <h3>Incoming Exposure</h3>
            <p>Current reservation-balance logic, grouped by landing date.</p>
          </div>
          <div class="tab-strip incoming-toggle" role="tablist" aria-label="Incoming exposure view">
            <button class="tab-button is-active" type="button" data-exposure-toggle="value" aria-pressed="true">Value</button>
            <button class="tab-button" type="button" data-exposure-toggle="kg" aria-pressed="false">KG</button>
          </div>
          <div class="chart-shell incoming-view" data-exposure-view="value">{incoming_landing_chart}</div>
          <div class="chart-shell incoming-view" data-exposure-view="kg" hidden>{incoming_landing_chart_kg}</div>
          {incoming_value_cards}
          {incoming_kg_cards}
          <div class="legend incoming-view" data-exposure-view="value">
            <div class="legend-item"><span class="swatch" style="background:#2a6a58"></span>Reserved value</div>
            <div class="legend-item"><span class="swatch" style="background:#d06e3d"></span>Unreserved value</div>
          </div>
          <div class="legend incoming-view" data-exposure-view="kg" hidden>
            <div class="legend-item"><span class="swatch" style="background:#2a6a58"></span>Reserved kg</div>
            <div class="legend-item"><span class="swatch" style="background:#d06e3d"></span>Unreserved kg</div>
          </div>
          <p class="chart-note">Landing dates are shown in chronological order with deterministic aggregation.</p>
          <details>
            <summary>Top incoming lots</summary>
            <div class="detail-body">
              <ul class="rank-list">{''.join(incoming_spotlight)}</ul>
            </div>
          </details>
        </section>

        <div class="subgrid section-stack">
          <section class="panel">
            <div class="section-head">
              <h3>Reservation Pipeline by Status</h3>
              <p>Latest effective reservation state, valued in GBP.</p>
            </div>
            <div class="chart-shell">{pipeline_chart}</div>
          </section>
          <section class="panel">
            <div class="section-head">
              <h3>Top Incoming Shortfalls</h3>
              <p>Value gap to target pre-sell, ranked deterministically.</p>
            </div>
            <div class="chart-shell">{risk_chart}</div>
          </section>
          {_render_risk_table(incoming_risks)}
        </div>
      </section>

      <section class="section-grid" id="landed">
        <section class="panel">
          <div class="section-head">
            <h3>Landed Stock Aging</h3>
            <p>Cash tied up in landed unsold inventory.</p>
          </div>
          <div class="chart-shell">{aging_chart}</div>
          <div class="legend">
            <div class="legend-item"><span class="swatch" style="background:#6bb08a"></span>0-30 days</div>
            <div class="legend-item"><span class="swatch" style="background:#c2aa52"></span>30-60 days</div>
            <div class="legend-item"><span class="swatch" style="background:#d7814e"></span>60-90 days</div>
            <div class="legend-item"><span class="swatch" style="background:#c95b49"></span>90+ days</div>
          </div>
        </section>
        <section class="panel">
          <div class="section-head">
            <h3>Top Cash Traps</h3>
            <p>Largest landed positions by trapped value.</p>
          </div>
          <ul class="rank-list">{''.join(trap_rows)}</ul>
        </section>
      </section>

      <section class="section-grid" id="cashflow">
        <section class="panel line-panel">
          <div class="section-head">
            <h3>Released Value Trend</h3>
            <p>Release activity only, using dispatch date with approved fallbacks.</p>
          </div>
          <div class="chart-shell">{release_line_chart}</div>
        </section>
        <div class="subgrid section-stack">
          {_render_event_table("Top Payables 60d", payables)}
          {_render_event_table("Top Receivables 60d", receivables)}
        </div>
      </section>

      <section class="section-grid" id="briefing">
        <section class="panel">
          <div class="section-head">
            <h3>Executive Briefing</h3>
            <p>Condensed narrative with cleaner hierarchy.</p>
          </div>
          <ul class="summary-list">{summary_html}</ul>
        </section>
        <section class="panel">
          <div class="section-head">
            <h3>Cash Pulse</h3>
            <p>Near-term alerting from 14-day and 30-day views.</p>
          </div>
          <div class="meter-copy">
            <div class="mini-stat">
              <div class="label">14-day alert</div>
              <strong>{_safe(pinch_14d.get("cash_alert") or "-")}</strong>
            </div>
            <div class="mini-stat">
              <div class="label">30-day alert</div>
              <strong>{_safe(pinch_30d.get("cash_alert") or "-")}</strong>
            </div>
            <div class="mini-stat">
              <div class="label">14-day net</div>
              <strong>{_money(pinch_14d.get("net_gbp"))}</strong>
            </div>
            <div class="mini-stat">
              <div class="label">30-day net</div>
              <strong>{_money(pinch_30d.get("net_gbp"))}</strong>
            </div>
          </div>
        </section>
      </section>

      <div class="foot">Generated for as_of {_safe(base.get("as_of") or "-")}</div>
    </main>
  </div>
  <script>
    (function() {{
      var root = document.documentElement;
      var storedTheme = localStorage.getItem("mcop-dashboard-theme");
      if (storedTheme === "dark" || storedTheme === "light") {{
        root.setAttribute("data-theme", storedTheme);
      }}

      var themeToggle = document.getElementById("theme-toggle");
      function syncThemeLabel() {{
        themeToggle.textContent = root.getAttribute("data-theme") === "dark" ? "Light mode" : "Dark mode";
      }}
      syncThemeLabel();
      themeToggle.addEventListener("click", function() {{
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", next);
        localStorage.setItem("mcop-dashboard-theme", next);
        syncThemeLabel();
      }});

      var exposureButtons = Array.prototype.slice.call(document.querySelectorAll("[data-exposure-toggle]"));
      var exposureViews = Array.prototype.slice.call(document.querySelectorAll("[data-exposure-view]"));
      function syncExposureView(nextView) {{
        exposureButtons.forEach(function(button) {{
          var active = button.getAttribute("data-exposure-toggle") === nextView;
          button.classList.toggle("is-active", active);
          button.setAttribute("aria-pressed", active ? "true" : "false");
        }});
        exposureViews.forEach(function(node) {{
          node.hidden = node.getAttribute("data-exposure-view") !== nextView;
        }});
      }}
      exposureButtons.forEach(function(button) {{
        button.addEventListener("click", function() {{
          syncExposureView(button.getAttribute("data-exposure-toggle"));
        }});
      }});
      syncExposureView("value");

    }})();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
