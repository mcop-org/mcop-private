from __future__ import annotations
import re

from pathlib import Path
from datetime import datetime, timezone






def _postprocess_section_markers(html: str) -> str:
    """
    Replace list items like:
      <li>=== TRADING HEALTH ===</li>
    with a proper subheading + thin divider.
    Works even if the summary is already rendered into <li> elements.
    """
    def repl(m):
        title = m.group(1).strip()
        # Normalise HTML-escaped ampersands etc are already present; we keep as-is.
        return (
            '</ul>'
            f'<div class="mcop-section-title">{title}'
            '<div class="mcop-section-divider"></div></div>'
            '<ul>'
        )

    # Match both raw === and HTML-escaped ampersands inside the title
    return re.sub(r"<li>\s*===\s*(.+?)\s*===\s*</li>", repl, html)


def _render_summary_lines(payload, esc):
    """
    Renders payload["summary"] lines.
    Lines like: === TRADING HEALTH === become subheadings + divider.
    Everything else becomes <li>.
    """
    out = []
    lines = payload.get("summary", []) or []
    for line in lines:
        if isinstance(line, str):
            m = re.match(r"^\s*===\s*(.+?)\s*===\s*$", line)
            if m:
                title = esc(m.group(1).strip().title())
                out.append(f'</ul><div class="mcop-section-title">{title}<div class="mcop-section-divider"></div></div><ul>')
                continue
        out.append(f"<li>{esc(str(line))}</li>")
    return "\n".join(out)


def _gbp(x) -> str:
    try:
        return f"£{float(x):,.0f}"
    except Exception:
        return "£—"


def _gbp2(x) -> str:
    try:
        return f"£{float(x):,.2f}"
    except Exception:
        return "£—"


def _pct(x) -> str:
    try:
        return f"{float(x)*100:.0f}%"
    except Exception:
        return "—"


def _safe(s) -> str:
    # Minimal escaping for HTML
    if s is None:
        return ""
    s = str(s)
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def _badge_class(flag: str) -> str:
    f = (flag or "").upper()
    if f in ("OK", "GREEN"):
        return "badge badge-green"
    if f in ("WATCH", "AMBER", "WARNING"):
        return "badge badge-amber"
    if f in ("BLOCK", "RED"):
        return "badge badge-red"
    return "badge"


def _health_colour(score):
    if score is None:
        return None
    try:
        s = float(score)
    except Exception:
        return None
    if s >= 6.5:
        return "#2ecc71"  # green
    if s >= 4.0:
        return "#f39c12"  # amber
    return "#e74c3c"      # red


def write_weekly_brief(path: Path, payload: dict) -> None:
    """
    Writes a single-file HTML Weekly Brief.
    Expects payload keys:
      - base, stress, status_flag, exposure_flag, summary (list[str])
      - top_payables_60, top_receivables_60 (list of dicts)
      - container_exposure (dict)
      - trading_health_score (float) optional
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    base = payload.get("base", {}) or {}
    stress = payload.get("stress", {}) or {}
    container = payload.get("container_exposure", {}) or {}

    as_of = base.get("as_of", "—")
    status_flag = payload.get("status_flag", "—")
    exposure_flag = payload.get("exposure_flag", payload.get("container_exposure", {}).get("exposure_flag", "—"))

    cash_today = base.get("cash_on_hand", None)
    liq60 = base.get("liquidity_60", None)
    runway = base.get("runway_days", None)

    incoming_pre = container.get("incoming_precommitted_pct", None)
    stress_impact = None
    try:
        stress_impact = float(stress.get("liquidity_60", 0)) - float(base.get("liquidity_60", 0))
    except Exception:
        stress_impact = None

    health_score = payload.get("trading_health_score", None)
    dot_colour = _health_colour(health_score)

    summary_lines = payload.get("summary", []) or []

    top_payables = payload.get("top_payables_60", []) or []
    top_receivables = payload.get("top_receivables_60", []) or []


    # --- Visual bar metrics (derived from existing payload) ---
    # On-track coverage = 1 - (% of incoming value below target)
    pct_below = container.get("dynamic_precommit", {}).get("pct_incoming_value_below_target", None)
    try:
        pct_below = float(pct_below) if pct_below is not None else None
    except Exception:
        pct_below = None

    presell_compliance = None
    if pct_below is not None:
        presell_compliance = max(0.0, min(1.0, 1.0 - pct_below))

    # Exposure vs cash buffer ratio = uncommitted incoming / 60d liquidity
    deployment_ratio = container.get("capital_deployment_ratio", None)
    try:
        deployment_ratio = float(deployment_ratio) if deployment_ratio is not None else None
    except Exception:
        deployment_ratio = None

    def _bar_colour(kind: str, value: float):
        # Minimal traffic-light colour rules
        if kind == "presell":
            # higher is better
            if value >= 0.70: return "var(--green)"
            if value >= 0.40: return "var(--amber)"
            return "var(--red)"
        if kind == "deploy":
            # lower is better
            if value <= 0.20: return "var(--green)"
            if value <= 0.35: return "var(--amber)"
            return "var(--red)"
        return "var(--amber)"

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


    # --- HTML ---
    html = []
    html.append("<!doctype html>")
    html.append("<html lang='en'>")
    html.append("<head>")
    html.append("<meta charset='utf-8'/>")
    html.append("<meta name='viewport' content='width=device-width,initial-scale=1'/>")
    html.append("<title>MCOP Weekly Brief</title>")
    html.append("""
<style>
:root{
  --bg:#0b1020;
  --panel:#101a33;
  --panel2:#0f1730;
  --text:#e9eefc;
  --muted:#a7b3d6;
  --line:rgba(255,255,255,.08);
  --green:#2ecc71;
  --amber:#f39c12;
  --red:#e74c3c;
  --shadow: 0 10px 30px rgba(0,0,0,.35);
  --radius: 16px;
  --radius2: 12px;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:var(--sans);
  background: radial-gradient(1200px 800px at 15% 10%, #192a5a 0%, var(--bg) 55%) fixed;
  color:var(--text);
}
.wrap{max-width:1100px;margin:0 auto;padding:28px 18px 48px;}
.header{
  display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:18px;
}
.h1{font-size:28px;font-weight:800;letter-spacing:.2px;margin:0}
.sub{color:var(--muted);margin-top:6px;font-size:13px}
.pills{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end}
.badge{
  border:1px solid var(--line);
  padding:7px 10px;border-radius:999px;
  font-size:12px;color:var(--muted);
  background: rgba(255,255,255,.04);
  display:inline-flex;align-items:center;gap:8px;
}
.badge-dot{width:9px;height:9px;border-radius:50%}
.badge-green .badge-dot{background:var(--green)}
.badge-amber .badge-dot{background:var(--amber)}
.badge-red .badge-dot{background:var(--red)}
.badge strong{color:var(--text);font-weight:700}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;margin-top:14px}
.card{
  grid-column: span 3;
  background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:14px 14px 12px;
  box-shadow: var(--shadow);
}
.card.small{grid-column: span 3;}
.card.wide{grid-column: span 6;}
.card.full{grid-column: span 12;}
.k{color:var(--muted);font-size:12px;margin:0 0 8px 0}
.v{font-size:26px;font-weight:850;letter-spacing:.2px;margin:0}
.v.small{font-size:22px}
.row{display:flex;justify-content:space-between;align-items:center;gap:10px}
.hr{height:1px;background:var(--line);margin:12px 0}
ul{margin:0;padding-left:18px}
li{margin:7px 0;color:var(--text)}
.muted{color:var(--muted)}

table{width:100%;border-collapse:collapse;overflow:hidden;border-radius:var(--radius2)}
th,td{padding:10px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:13px}
th{color:var(--muted);font-weight:700;background:rgba(255,255,255,.03)}
tr:hover td{background:rgba(255,255,255,.02)}
td.mono{font-family:var(--mono);color:var(--muted);font-size:12px}
.healthline{
  display:flex;align-items:center;gap:10px;margin-top:8px;color:var(--muted);font-size:13px
}
.healthdot{
  width:10px;height:10px;border-radius:50%;
  display:inline-block;flex:0 0 auto;
  box-shadow: 0 0 0 3px rgba(255,255,255,.06);
}
.footer{margin-top:18px;color:var(--muted);font-size:12px}
@media (max-width: 900px){
  .card.small{grid-column: span 6;}
  .card.wide{grid-column: span 12;}
}
@media (max-width: 560px){
  .card.small{grid-column: span 12;}
  .pills{justify-content:flex-start}
}

.bar-block{margin-top:8px}
.bar-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:6px}
.bar-title{font-size:13px;font-weight:800;color:#d8e1ff}
.bar-sub{font-size:12px;color:var(--muted)}
.bar-track{
  width:100%;
  height:10px;
  border-radius:999px;
  background: rgba(255,255,255,.08);
  overflow:hidden;
  border:1px solid var(--line);
}
.bar-fill{
  height:100%;
  border-radius:999px;
  box-shadow: 0 0 0 3px rgba(255,255,255,.04) inset;
}

/* --- Section headings (minimalist) --- */
.mcop-section-title{
  margin: 18px 0 8px 0;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: .02em;
}
.mcop-section-divider{
  height: 1px;
  width: 100%;
  opacity: .18;
  background: currentColor;
  margin: 6px 0 12px 0;
}
</style>

    """)

    html.append("</head>")
    html.append("<body>")
    html.append("<div class='wrap'>")

    # Header
    html.append("<div class='header'>")
    html.append("<div>")
    html.append("<h1 class='h1'>MCOP Weekly Brief</h1>")
    html.append(f"<div class='sub'>As of <strong>{_safe(as_of)}</strong></div>")
    if health_score is not None:
        label = "Green — healthy" if float(health_score) >= 6.5 else ("Amber — needs attention" if float(health_score) >= 4.0 else "Red — fragile")
        dot = f"<span class='healthdot' style='background:{dot_colour}'></span>" if dot_colour else ""
        html.append(f"<div class='healthline'>Trading Health: <strong style='color:var(--text)'>{_safe(health_score)}/10</strong> {dot} <span class='muted'>{_safe(label)}</span></div>")
    html.append("</div>")

    html.append("<div class='pills'>")
    html.append(f"<span class='{_badge_class(status_flag)}'><span class='badge-dot'></span><strong>Status</strong>&nbsp;{_safe(status_flag)}</span>")
    html.append(f"<span class='{_badge_class(exposure_flag)}'><span class='badge-dot'></span><strong>Exposure</strong>&nbsp;{_safe(exposure_flag)}</span>")
    html.append("</div>")
    html.append("</div>")

    # Top metric cards
    html.append("<div class='grid'>")

    html.append("<div class='card small'>")
    html.append("<p class='k'>Cash today</p>")
    html.append(f"<p class='v'>{_safe(_gbp(cash_today))}</p>")
    html.append("</div>")

    html.append("<div class='card small'>")
    html.append("<p class='k'>Liquidity (60d)</p>")
    html.append(f"<p class='v'>{_safe(_gbp(liq60))}</p>")
    html.append("</div>")

    html.append("<div class='card small'>")
    html.append("<p class='k'>Runway</p>")
    try:
        rd = int(round(float(runway)))
    except Exception:
        rd = None
    html.append(f"<p class='v'>{rd if rd is not None else '—'} days</p>")
    html.append("</div>")

    html.append("<div class='card small'>")
    html.append("<p class='k'>Already reserved</p>")
    html.append(f"<p class='v'>{_safe(_pct(incoming_pre))}</p>")
    html.append("</div>")

    # Operational bars (Phase 2.1) — display only
    html.append("<div class='card full'>")
    html.append("<p class='section-title'>Operational bars</p>")
    html.append("<div class='hr'></div>")

    # On-track coverage bar
    if presell_compliance is not None:
        colour = _bar_colour("presell", presell_compliance)
        pct_txt = f"{presell_compliance*100:.0f}%"
        html.append("<div class='bar-block'>")
        html.append(f"<div class='bar-head'><div class='bar-title'>On-track coverage</div><div class='bar-sub'>{pct_txt}</div></div>")
        html.append("<div class='bar-track'>")
        html.append(f"<div class='bar-fill' style='width:{presell_compliance*100:.1f}%;background:{colour}'></div>")
        html.append("</div>")
        html.append("<div class='bar-sub' style='margin-top:6px'>Share of incoming value that is sold early enough to meet our timing rules.</div>")
        html.append("</div>")

    # Exposure vs cash buffer bar
    if deployment_ratio is not None:
        # cap to 100% visually, but keep text real
        width = min(max(deployment_ratio, 0.0), 1.0) * 100.0
        colour = _bar_colour("deploy", deployment_ratio)
        pct_txt = f"{deployment_ratio*100:.0f}%"
        html.append("<div class='bar-block'>")
        html.append(f"<div class='bar-head'><div class='bar-title'>Exposure vs cash buffer</div><div class='bar-sub'>{pct_txt}</div></div>")
        html.append("<div class='bar-track'>")
        html.append(f"<div class='bar-fill' style='width:{width:.1f}%;background:{colour}'></div>")
        html.append("</div>")
        html.append("<div class='bar-sub' style='margin-top:6px'>Unsold incoming compared to our 60-day liquidity cushion.</div>")
        html.append("</div>")

    html.append("</div>")

    # Stress impact card
    html.append("<div class='card wide'>")
    html.append("<p class='section-title'>Stress Impact</p>")
    html.append("<div class='hr'></div>")
    html.append(f"<div class='row'><div class='muted'>Base liquidity (60d)</div><div class='v small'>{_safe(_gbp(base.get('liquidity_60')))}</div></div>")
    html.append(f"<div class='row'><div class='muted'>Stress liquidity (60d)</div><div class='v small'>{_safe(_gbp(stress.get('liquidity_60')))}</div></div>")
    if stress_impact is not None:
        html.append(f"<div class='row'><div class='muted'>Impact under stress</div><div class='v small'>{_safe(_gbp(stress_impact))}</div></div>")
    html.append("</div>")

    # Summary card
    html.append("<div class='card wide'>")
    html.append("<p class='section-title'>Summary</p>")
    html.append("<div class='hr'></div>")
    html.append("<ul>")
    for line in summary_lines:
        if str(line).strip() == "":
            continue
        html.append(f"<li>{_safe(line)}</li>")
    html.append("</ul>")
    html.append("</div>")

    # Top payables/receivables
    def _render_table(title: str, rows: list[dict]) -> str:
        out = []
        out.append("<div class='card full'>")
        out.append(f"<p class='section-title'>{_safe(title)}</p>")
        out.append("<div class='hr'></div>")
        out.append("<table>")
        out.append("<thead><tr><th>Product</th><th>Date</th><th>Amount</th></tr></thead>")
        out.append("<tbody>")
        if not rows:
            out.append("<tr><td colspan='3' class='muted'>No items.</td></tr>")
        else:
            for r in rows[:5]:
                prod = r.get("product_reference") or r.get("product_id") or "—"
                date = r.get("date") or "—"
                amt = r.get("amount")
                out.append(f"<tr><td><strong>{_safe(prod)}</strong> <span class='mono'>({_safe(r.get('product_id','—'))})</span></td>"
                           f"<td class='mono'>{_safe(date)}</td>"
                           f"<td><strong>{_safe(_gbp2(amt))}</strong></td></tr>")
        out.append("</tbody></table></div>")
        return "\n".join(out)

    html.append(_render_table("Top payables (next 60d)", top_payables))
    html.append(_render_table("Top receivables (next 60d)", top_receivables))

    html.append("</div>")  # grid

    
    # Drift signals card
    drift = payload.get("drift_signals", [])
    if drift:
        html.append("<div class='card full'>")
        html.append("<p class='section-title'>Drift Signals</p>")
        html.append("<div class='hr'></div>")
        html.append("<ul>")
        for d in drift:
            html.append(f"<li>{_safe(d)}</li>")
        html.append("</ul>")
        html.append("</div>")

    html.append(f"<div class='footer'>Generated by MCOP • {now_utc}</div>")
    html.append("</div></body></html>")

    path.write_text("\n".join(html), encoding="utf-8")
