from __future__ import annotations

import base64
import json
from pathlib import Path


def _safe_json(value: object) -> str:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _logo_data_uri(filename: str) -> str:
    asset_path = Path(__file__).with_name("assets") / filename
    encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def write_reference_workspace_html(path: Path, dataset: dict) -> None:
    payload_json = _safe_json(dataset)
    snapshot_date = str(dataset.get("snapshot_date") or "-")
    logo_light = _logo_data_uri("logo-light.png")
    logo_dark = _logo_data_uri("logo-dark.png")
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MCOP Reference Workspace v1</title>
  <style>
    :root {{
      --bg: #eef3f8;
      --bg-strong: #f7fafc;
      --hero-glow: rgba(33, 83, 118, 0.16);
      --hero-warm: rgba(173, 111, 76, 0.12);
      --panel: rgba(255, 255, 255, 0.90);
      --panel-strong: #ffffff;
      --panel-soft: rgba(255, 255, 255, 0.72);
      --ink: #102033;
      --muted: #607086;
      --label: #314257;
      --line: rgba(16, 32, 51, 0.10);
      --line-strong: rgba(16, 32, 51, 0.16);
      --shadow-lg: 0 26px 70px rgba(16, 24, 40, 0.12);
      --shadow-md: 0 16px 34px rgba(16, 24, 40, 0.08);
      --accent: #215376;
      --accent-soft: rgba(33, 83, 118, 0.12);
      --warn: #a96a3e;
      --warn-soft: rgba(169, 106, 62, 0.14);
      --sans: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
    }}
    html[data-theme="dark"] {{
      --bg: #08111d;
      --bg-strong: #0d1726;
      --hero-glow: rgba(91, 192, 167, 0.16);
      --hero-warm: rgba(245, 159, 98, 0.10);
      --panel: rgba(10, 20, 34, 0.92);
      --panel-strong: #0f1c2f;
      --panel-soft: rgba(11, 21, 35, 0.78);
      --ink: #e6eef8;
      --muted: #96a7bc;
      --label: #ced9e7;
      --line: rgba(148, 163, 184, 0.16);
      --line-strong: rgba(148, 163, 184, 0.24);
      --shadow-lg: 0 26px 70px rgba(0, 0, 0, 0.34);
      --shadow-md: 0 16px 34px rgba(0, 0, 0, 0.22);
      --accent: #79b6de;
      --accent-soft: rgba(121, 182, 222, 0.16);
      --warn: #f2b27e;
      --warn-soft: rgba(242, 178, 126, 0.16);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: var(--sans);
      background:
        radial-gradient(circle at top left, var(--hero-glow), transparent 34%),
        radial-gradient(circle at top right, var(--hero-warm), transparent 26%),
        linear-gradient(180deg, var(--bg-strong) 0%, var(--bg) 100%);
    }}
    button, input {{ font: inherit; }}
    [hidden] {{ display: none !important; }}
    .shell {{
      width: min(1520px, calc(100vw - 32px));
      margin: 22px auto 34px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 28px;
      background: var(--panel);
      box-shadow: var(--shadow-lg);
      backdrop-filter: blur(16px);
    }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 14px 18px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: color-mix(in srgb, var(--panel-soft) 92%, transparent);
      box-shadow: var(--shadow-md);
      backdrop-filter: blur(16px);
    }}
    .topbar-brand {{
      display: flex;
      align-items: center;
      gap: 16px;
      min-width: 0;
    }}
    .brand-mark {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 104px;
      height: 52px;
      padding: 7px 12px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel-strong) 90%, transparent);
      box-shadow: var(--shadow-md);
      overflow: hidden;
      flex: 0 0 auto;
    }}
    .brand-logo {{
      display: block;
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }}
    .brand-logo-dark {{
      display: none;
    }}
    html[data-theme="dark"] .brand-logo-light {{
      display: none;
    }}
    html[data-theme="dark"] .brand-logo-dark {{
      display: block;
    }}
    .topbar-copy {{
      display: grid;
      gap: 2px;
      min-width: 0;
    }}
    .topbar-title {{
      margin: 0;
      font-size: 24px;
      line-height: 1;
      letter-spacing: -0.04em;
    }}
    .topbar-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .toolbar-chip, .theme-toggle, .module-nav-button {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel-strong) 88%, transparent);
      color: var(--label);
      box-shadow: var(--shadow-md);
    }}
    .toolbar-chip strong {{
      color: var(--ink);
      font-weight: 700;
    }}
    .theme-toggle, .module-nav-button, .sort-button, .reset-button {{
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, background-color 120ms ease;
    }}
    .theme-toggle:hover,
    .theme-toggle:focus-visible,
    .module-nav-button:hover,
    .module-nav-button:focus-visible,
    .sort-button:hover,
    .sort-button:focus-visible,
    .reset-button:hover,
    .reset-button:focus-visible {{
      transform: translateY(-1px);
      border-color: color-mix(in srgb, var(--accent) 30%, var(--line));
      outline: none;
    }}
    .module-nav-button.is-active {{
      color: var(--accent);
      border-color: color-mix(in srgb, var(--accent) 34%, var(--line));
      background: color-mix(in srgb, var(--accent-soft) 74%, var(--panel-strong));
    }}
    .workspace-shell {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: 228px minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }}
    .workspace-sidebar {{
      position: sticky;
      top: 22px;
      padding: 14px;
    }}
    .sidebar-label {{
      margin: 0 0 12px;
      padding: 0 6px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .module-nav {{
      display: grid;
      gap: 8px;
    }}
    .module-nav-button {{
      width: 100%;
      justify-content: flex-start;
      text-align: left;
      border-radius: 18px;
      white-space: normal;
      line-height: 1.35;
    }}
    .workspace-main {{
      min-width: 0;
    }}
    .hero {{
      padding: 28px;
      background:
        linear-gradient(145deg, color-mix(in srgb, var(--accent-soft) 65%, transparent), transparent 44%),
        linear-gradient(180deg, color-mix(in srgb, var(--panel-strong) 90%, transparent), var(--panel));
    }}
    .control-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }}
    .control-panel {{
      padding: 20px;
      display: grid;
      gap: 14px;
    }}
    .control-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .control-title {{
      margin: 0;
      font-size: 18px;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }}
    .view-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .reset-button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel-strong) 88%, transparent);
      color: var(--label);
      box-shadow: var(--shadow-md);
    }}
    .control-label {{
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .control-input {{
      width: 100%;
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel-strong) 94%, transparent);
      color: var(--ink);
      transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24);
    }}
    .control-input:focus {{
      outline: none;
      transform: translateY(-1px);
      border-color: color-mix(in srgb, var(--accent) 38%, var(--line));
      box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent-soft) 70%, transparent);
    }}
    .selected-reference-inline {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      min-height: 24px;
    }}
    .selected-reference-value {{
      margin: 0;
      font-size: 16px;
      line-height: 1;
      letter-spacing: -0.02em;
    }}
    .workspace-view {{
      margin-top: 18px;
    }}
    .view-frame {{
      padding: 24px;
    }}
    .view-title {{
      margin: 0;
      font-size: 24px;
      letter-spacing: -0.03em;
    }}
    .view-copy {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 16px;
      margin-top: 18px;
    }}
    .action-kpi-grid {{
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }}
    .kpi-card {{
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: color-mix(in srgb, var(--panel-strong) 92%, transparent);
      box-shadow: var(--shadow-md);
    }}
    .kpi-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .kpi-value {{
      margin-top: 12px;
      font-size: clamp(28px, 3vw, 40px);
      line-height: 1;
      letter-spacing: -0.04em;
    }}
    .kpi-status-wrap {{
      margin-top: 12px;
      min-height: 36px;
      display: flex;
      align-items: center;
    }}
    .kpi-meta {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }}
    .kpi-submeta {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}
    .table-shell {{
      margin-top: 18px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: color-mix(in srgb, var(--panel-strong) 94%, transparent);
      box-shadow: var(--shadow-md);
    }}
    .table-topbar {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 20px 20px 12px;
      align-items: end;
      flex-wrap: wrap;
    }}
    .table-title {{
      margin: 0;
      font-size: 22px;
      letter-spacing: -0.02em;
    }}
    .table-subtitle {{
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .table-filter {{
      width: min(320px, 100%);
    }}
    .table-filters {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: end;
    }}
    .table-filter.compact {{
      width: min(220px, 100%);
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      margin-top: 18px;
    }}
    .chart-card {{
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: color-mix(in srgb, var(--panel-strong) 92%, transparent);
      box-shadow: var(--shadow-md);
    }}
    .chart-title {{
      margin: 0;
      font-size: 18px;
      letter-spacing: -0.02em;
    }}
    .chart-copy {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}
    .chart-list {{
      margin-top: 16px;
      display: grid;
      gap: 12px;
    }}
    .chart-empty {{
      margin-top: 16px;
      color: var(--muted);
      font-size: 14px;
    }}
    .bar-row {{
      display: grid;
      gap: 6px;
    }}
    .bar-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      font-size: 13px;
    }}
    .bar-label {{
      font-weight: 700;
      color: var(--label);
    }}
    .bar-value {{
      color: var(--muted);
      white-space: nowrap;
    }}
    .bar-track {{
      width: 100%;
      height: 10px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--line) 64%, transparent);
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--warn) 34%, var(--accent)));
    }}
    .stacked-chart-list {{
      margin-top: 16px;
      display: grid;
      gap: 16px;
    }}
    .stack-row {{
      display: grid;
      gap: 8px;
    }}
    .stack-bar {{
      width: 100%;
      min-height: 14px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--line) 64%, transparent);
      overflow: hidden;
      display: flex;
    }}
    .stack-segment {{
      min-width: 2px;
      height: 14px;
    }}
    .stack-legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
      margin-top: 10px;
    }}
    .stack-legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 12px;
    }}
    .stack-swatch {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      flex: 0 0 auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      padding: 14px 20px;
      border-top: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{
      padding-top: 10px;
      padding-bottom: 10px;
      background: color-mix(in srgb, var(--panel-soft) 94%, transparent);
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    th.num, td.num {{
      text-align: right;
    }}
    .sort-button {{
      border: 0;
      background: transparent;
      color: inherit;
      font: inherit;
      padding: 0;
    }}
    .muted {{
      color: var(--muted);
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      padding: 5px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .pill.status-warm {{
      background: var(--warn-soft);
      color: var(--warn);
    }}
    .pill.status-bad {{
      background: color-mix(in srgb, #b13a3a 16%, transparent);
      color: #b13a3a;
    }}
    .pill.status-good {{
      background: color-mix(in srgb, #2f7d4a 16%, transparent);
      color: #2f7d4a;
    }}
    .pill.status-neutral {{
      background: var(--accent-soft);
      color: var(--accent);
    }}
    .empty {{
      padding: 28px 20px 36px;
      color: var(--muted);
      font-size: 15px;
    }}
    @media (max-width: 1280px) {{
      .kpi-grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 1120px) {{
      .workspace-shell {{
        grid-template-columns: 208px minmax(0, 1fr);
      }}
      .kpi-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .chart-grid {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 900px) {{
      .shell {{
        width: min(100vw - 18px, 1520px);
      }}
      .topbar {{
        align-items: flex-start;
      }}
      .workspace-shell {{
        grid-template-columns: 1fr;
      }}
      .workspace-sidebar {{
        position: static;
        padding: 12px;
      }}
      .module-nav {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 720px) {{
      .hero, .view-frame {{
        padding: 18px;
      }}
      .topbar-brand {{
        width: 100%;
      }}
      .topbar-actions {{
        width: 100%;
      }}
      .module-nav {{
        grid-template-columns: 1fr;
      }}
      .kpi-grid {{
        grid-template-columns: 1fr;
      }}
      th, td {{
        padding-left: 14px;
        padding-right: 14px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="topbar-brand">
        <div class="brand-mark" aria-hidden="true">
          <img class="brand-logo brand-logo-light" src="{logo_light}" alt="">
          <img class="brand-logo brand-logo-dark" src="{logo_dark}" alt="">
        </div>
        <div class="topbar-copy">
          <p class="muted" style="margin:0;">MCOP Reference Workspace v1</p>
          <h1 class="topbar-title">Reference Workspace</h1>
        </div>
      </div>
      <div class="topbar-actions">
        <div class="toolbar-chip">Snapshot: <strong>{snapshot_date}</strong></div>
        <button class="theme-toggle" id="theme-toggle" type="button" aria-pressed="false">Toggle Theme</button>
      </div>
    </header>

    <div class="workspace-shell">
      <aside class="workspace-sidebar panel">
        <p class="sidebar-label">Modules</p>
        <nav class="module-nav" aria-label="Workspace navigation">
          <button class="module-nav-button is-active" id="tab-reservation" type="button" data-tab="reservation" aria-pressed="true">Reservation Intelligence</button>
          <button class="module-nav-button" id="tab-product" type="button" data-tab="product" aria-pressed="false">Product Reference Intelligence</button>
          <button class="module-nav-button" id="tab-client" type="button" data-tab="client" aria-pressed="false">Client Intelligence</button>
          <button class="module-nav-button" id="tab-landed" type="button" data-tab="landed" aria-pressed="false">Landed Stock Intelligence</button>
          <button class="module-nav-button" id="tab-action" type="button" data-tab="action" aria-pressed="false">Reservation Risk / Action Queue</button>
        </nav>
      </aside>

      <div class="workspace-main">
        <section class="hero panel" id="shared-selector-panel">
          <div class="control-grid">
            <section class="control-panel panel">
              <div class="control-head">
                <div>
                  <p class="control-label">Reference Selector</p>
                  <h2 class="control-title">Choose Product Reference</h2>
                </div>
                <div class="toolbar-chip" id="selected-reference-chip"></div>
              </div>
              <div>
                <label class="control-label" for="reference-search">Product Reference</label>
                <input class="control-input" id="reference-search" list="reference-options" autocomplete="off" placeholder="Search or select a product reference">
                <datalist id="reference-options"></datalist>
              </div>
              <div class="selected-reference-inline">
                <div>
                  <span class="control-label" style="margin:0;">Selected Reference</span>
                  <p class="selected-reference-value" id="selected-reference-value">Select product</p>
                </div>
                <button class="reset-button" id="shared-selector-reset" type="button">Reset</button>
              </div>
            </section>
          </div>
        </section>

        <section class="workspace-view" id="reservation-view">
      <div class="panel view-frame">
        <div class="view-head">
          <h2 class="view-title">Reservation Intelligence</h2>
        </div>

        <section class="kpi-grid" aria-label="Reservation Intelligence KPIs">
          <article class="kpi-card">
            <div class="kpi-label">Reserved KG</div>
            <div class="kpi-value" id="reservation-kpi-kg">-</div>
            <div class="kpi-meta" id="reservation-kpi-bags">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Reserved Value</div>
            <div class="kpi-value" id="reservation-kpi-value">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Reserved %</div>
            <div class="kpi-value" id="reservation-kpi-reserved-pct">-</div>
            <div class="kpi-submeta" id="reservation-kpi-available-bags">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Clients</div>
            <div class="kpi-value" id="reservation-kpi-clients">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Landing Status</div>
            <div class="kpi-status-wrap" id="reservation-kpi-landing-status">-</div>
            <div class="kpi-submeta" id="reservation-kpi-landing-support">-</div>
          </article>
        </section>

        <section class="table-shell">
          <div class="table-topbar">
            <div>
              <h3 class="table-title">Reservation Details</h3>
            </div>
            <div class="table-filter">
              <label class="control-label" for="table-filter">Search reservation rows</label>
              <input class="control-input" id="table-filter" type="search" autocomplete="off" placeholder="Filter by company, status, warehouse, or reservation key">
            </div>
          </div>
          <div style="overflow:auto;">
            <table>
              <thead>
                <tr>
                  <th><button class="sort-button" data-sort="company_name" type="button">Company</button></th>
                  <th><button class="sort-button" data-sort="request_status" type="button">Reservation Status</button></th>
                  <th class="num"><button class="sort-button" data-sort="effective_bags" type="button">Reserved Bags</button></th>
                  <th class="num"><button class="sort-button" data-sort="reserved_kg" type="button">Reserved KG</button></th>
                  <th class="num"><button class="sort-button" data-sort="reserved_value_gbp" type="button">Reserved Value</button></th>
                  <th><button class="sort-button" data-sort="landing_status" type="button">Landing Status</button></th>
                  <th><button class="sort-button" data-sort="landing_date" type="button">Landing Date</button></th>
                  <th><button class="sort-button" data-sort="warehouse" type="button">Warehouse</button></th>
                  <th><button class="sort-button" data-sort="reservation_key" type="button">Reservation Key</button></th>
                </tr>
              </thead>
              <tbody id="reservation-table-body"></tbody>
            </table>
          </div>
          <div class="empty" id="reservation-empty" hidden>No reservation rows match the current filters.</div>
        </section>
      </div>
    </section>

    <section class="workspace-view" id="product-view" hidden>
      <div class="panel view-frame">
        <div class="view-head">
          <div>
            <h2 class="view-title">Product Reference Intelligence</h2>
            <p class="view-copy">Stock-only view of whether the selected reference looks early-stage, balanced, or at risk of landed build-up.</p>
          </div>
        </div>

        <section class="kpi-grid" aria-label="Product Reference Intelligence KPIs">
          <article class="kpi-card">
            <div class="kpi-label">Incoming Stock</div>
            <div class="kpi-value" id="product-kpi-incoming">-</div>
            <div class="kpi-meta" id="product-kpi-incoming-kg">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Landed Stock</div>
            <div class="kpi-value" id="product-kpi-landed">-</div>
            <div class="kpi-meta" id="product-kpi-landed-kg">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Landed Available</div>
            <div class="kpi-value" id="product-kpi-available">-</div>
            <div class="kpi-meta" id="product-kpi-available-kg">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Stock Health</div>
            <div class="kpi-status-wrap" id="product-kpi-health">-</div>
            <div class="kpi-submeta" id="product-kpi-health-meta">Safe stock-state classification only.</div>
          </article>
        </section>

        <section class="table-shell">
          <div class="table-topbar">
            <div>
              <h3 class="table-title">Stock Details by Lot / Warehouse</h3>
              <p class="table-subtitle">Default order shows landed available rows first, then other landed rows, then incoming rows.</p>
            </div>
          </div>
          <div style="overflow:auto;">
            <table>
              <thead>
                <tr>
                  <th>Product ID</th>
                  <th>Warehouse</th>
                  <th>Landing Status</th>
                  <th>Landing Date</th>
                  <th>Days Since Landing / Not landed</th>
                  <th class="num">Bags</th>
                  <th class="num">Bags Available</th>
                </tr>
              </thead>
              <tbody id="product-detail-body"></tbody>
            </table>
          </div>
          <div class="empty" id="product-detail-empty" hidden>No product rows match the selected reference.</div>
        </section>
      </div>
    </section>

    <section class="workspace-view" id="client-view" hidden>
      <div class="panel view-frame">
        <div class="view-head">
          <div>
            <h2 class="view-title">Client Intelligence</h2>
            <p class="view-copy">Reservation activity view, excluding rejected reservations.</p>
          </div>
        </div>

        <section class="table-shell" aria-label="Client Intelligence Filters">
          <div class="table-topbar">
            <div>
              <h3 class="table-title">Request Date</h3>
              <p class="table-subtitle">Applies to Client Intelligence only and uses the workspace snapshot date.</p>
            </div>
            <div class="table-filters">
              <div class="table-filter compact">
                <label class="control-label" for="client-date-preset">Date range</label>
                <select class="control-input" id="client-date-preset">
                  <option value="all">All request dates</option>
                  <option value="last-30">Last 30 days</option>
                  <option value="last-90">Last 90 days</option>
                  <option value="month-to-date">Month to date</option>
                  <option value="financial-year-to-date">Financial year to date</option>
                  <option value="custom">Custom range</option>
                </select>
              </div>
              <div class="table-filter compact" id="client-date-from-shell" hidden>
                <label class="control-label" for="client-date-from">From</label>
                <input class="control-input" id="client-date-from" type="date" inputmode="numeric">
              </div>
              <div class="table-filter compact" id="client-date-to-shell" hidden>
                <label class="control-label" for="client-date-to">To</label>
                <input class="control-input" id="client-date-to" type="date" inputmode="numeric">
              </div>
            </div>
          </div>
        </section>

        <section class="kpi-grid" aria-label="Client Intelligence KPIs">
          <article class="kpi-card">
            <div class="kpi-label">Clients With Reservation Activity</div>
            <div class="kpi-value" id="client-kpi-count">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Recorded Reservation Value</div>
            <div class="kpi-value" id="client-kpi-total-value">-</div>
            <div class="kpi-submeta" id="client-kpi-total-value-meta">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Largest Recorded Reservation Value</div>
            <div class="kpi-value" id="client-kpi-largest-value">-</div>
            <div class="kpi-submeta" id="client-kpi-largest-meta">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Clients Concentrated In One Reference</div>
            <div class="kpi-value" id="client-kpi-concentrated">-</div>
            <div class="kpi-submeta" id="client-kpi-concentrated-meta">Primary reference share at or above 80%.</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Client Concentration</div>
            <div class="kpi-value" id="client-kpi-top-five-share">-</div>
            <div class="kpi-submeta" id="client-kpi-top-ten-share">-</div>
            <div class="kpi-submeta" id="client-kpi-rest-share">-</div>
          </article>
        </section>

        <section class="chart-grid" aria-label="Client Intelligence Charts">
          <article class="chart-card">
            <h3 class="chart-title">Top Clients by Recorded Reservation Value</h3>
            <p class="chart-copy">Ranks clients by recorded reservation value for the selected request-date range.</p>
            <div class="chart-list" id="client-exposure-chart"></div>
            <div class="chart-empty" id="client-exposure-empty" hidden>No client activity for the selected date range.</div>
          </article>
          <article class="chart-card" style="grid-column: span 2;">
            <h3 class="chart-title">Recorded Reservation Value by Client and Reference</h3>
            <p class="chart-copy">Shows how recorded reservation value is distributed across product references for the selected date range.</p>
            <div class="stacked-chart-list" id="client-concentration-chart"></div>
            <div class="chart-empty" id="client-concentration-empty" hidden>No client concentration data for the selected date range.</div>
          </article>
        </section>

        <section class="table-shell">
          <div class="table-topbar">
            <div>
              <h3 class="table-title">Client Activity Details</h3>
              <p class="table-subtitle">Default order shows highest recorded reservation value first for the selected date range.</p>
            </div>
            <div class="table-filters">
              <div class="table-filter">
                <label class="control-label" for="client-table-filter">Search client rows</label>
                <input class="control-input" id="client-table-filter" type="search" autocomplete="off" placeholder="Filter by company, client ID, or reference">
              </div>
              <div class="table-filter compact">
                <label class="control-label" for="client-concentration-filter">Concentration</label>
                <select class="control-input" id="client-concentration-filter">
                  <option value="all">All Clients</option>
                  <option value="concentrated">80%+ One Reference</option>
                  <option value="multi">Multi-Reference</option>
                </select>
              </div>
            </div>
          </div>
          <div style="overflow:auto;">
            <table>
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Client ID</th>
                  <th class="num">Reservation Rows</th>
                  <th class="num">Reserved Bags Recorded</th>
                  <th class="num">Reserved KG Recorded</th>
                  <th class="num">Reserved Value GBP Recorded</th>
                  <th class="num">Distinct References</th>
                  <th>Primary Reference</th>
                  <th class="num">Primary Reference Share</th>
                  <th>Landing Mix</th>
                </tr>
              </thead>
              <tbody id="client-detail-body"></tbody>
            </table>
          </div>
          <div class="empty" id="client-detail-empty" hidden>No client rows match the current filters.</div>
        </section>
      </div>
    </section>

    <section class="workspace-view" id="landed-view" hidden>
      <div class="panel view-frame">
        <div class="view-head">
          <div>
            <h2 class="view-title">Landed Stock Intelligence</h2>
            <p class="view-copy">Landed-only operational view of unsold stock, aging exposure, and current warehouse concentration.</p>
          </div>
          <button class="reset-button" id="landed-reset" type="button">Reset</button>
        </div>

        <section class="kpi-grid" aria-label="Landed Stock Intelligence KPIs">
          <article class="kpi-card">
            <div class="kpi-label">Unsold Landed Bags</div>
            <div class="kpi-value" id="landed-kpi-unsold-bags">-</div>
            <div class="kpi-meta" id="landed-kpi-landed-bags">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Unsold Landed KG</div>
            <div class="kpi-value" id="landed-kpi-unsold-kg">-</div>
            <div class="kpi-submeta" id="landed-kpi-unsold-kg-meta">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Aged 180+ Bags</div>
            <div class="kpi-value" id="landed-kpi-aged-bags">-</div>
            <div class="kpi-submeta" id="landed-kpi-aged-meta">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Warehouses Exposed</div>
            <div class="kpi-value" id="landed-kpi-warehouses">-</div>
            <div class="kpi-submeta" id="landed-kpi-as-of">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Unsold Landed Value</div>
            <div class="kpi-value" id="landed-kpi-value">-</div>
            <div class="kpi-submeta" id="landed-kpi-value-meta">-</div>
          </article>
        </section>

        <section class="chart-grid" aria-label="Landed Stock Intelligence Charts">
          <article class="chart-card">
            <h3 class="chart-title">Aging Exposure</h3>
            <p class="chart-copy">Unsold landed bags by aging bucket. This isolates aging risk without mixing in incoming stock or reservation state.</p>
            <div class="chart-list" id="landed-aging-chart"></div>
            <div class="chart-empty" id="landed-aging-empty" hidden>No landed aging exposure in the current view.</div>
          </article>
          <article class="chart-card">
            <h3 class="chart-title">Warehouse Exposure</h3>
            <p class="chart-copy">Current unsold landed bags by warehouse, so operational follow-up can focus where exposure is sitting now.</p>
            <div class="chart-list" id="landed-warehouse-chart"></div>
            <div class="chart-empty" id="landed-warehouse-empty" hidden>No warehouse exposure in the current view.</div>
          </article>
          <article class="chart-card">
            <h3 class="chart-title">Largest Unsold References</h3>
            <p class="chart-copy">Shows which references currently hold the largest landed available exposure.</p>
            <div class="chart-list" id="landed-reference-chart"></div>
            <div class="chart-empty" id="landed-reference-empty" hidden>No reference exposure in the current view.</div>
          </article>
        </section>

        <section class="table-shell">
          <div class="table-topbar">
            <div>
              <h3 class="table-title">Landed Exposure Details</h3>
              <p class="table-subtitle">Landed rows with unsold exposure or incomplete availability data. Default order shows oldest landed exposure first.</p>
            </div>
            <div class="table-filters">
              <div class="table-filter">
                <label class="control-label" for="landed-table-filter">Search landed exposure</label>
                <input class="control-input" id="landed-table-filter" type="search" autocomplete="off" placeholder="Filter by reference, product ID, warehouse, or status">
              </div>
              <div class="table-filter compact">
                <label class="control-label" for="landed-warehouse-filter">Warehouse</label>
                <select class="control-input" id="landed-warehouse-filter"></select>
              </div>
              <div class="table-filter compact">
                <label class="control-label" for="landed-aging-filter">Aging Bucket</label>
                <select class="control-input" id="landed-aging-filter"></select>
              </div>
              <div class="table-filter compact">
                <label class="control-label" for="landed-status-filter">Data Status</label>
                <select class="control-input" id="landed-status-filter"></select>
              </div>
            </div>
          </div>
          <div style="overflow:auto;">
            <table>
              <thead>
                <tr>
                  <th>Product Reference</th>
                  <th>Product ID</th>
                  <th>Warehouse</th>
                  <th>Landing Date</th>
                  <th class="num">Days Since Landing</th>
                  <th>Aging Bucket</th>
                  <th class="num">Landed Bags</th>
                  <th class="num">Unsold Bags</th>
                  <th class="num">Unsold KG</th>
                  <th class="num">Unsold Value GBP</th>
                  <th>Data Status</th>
                </tr>
              </thead>
              <tbody id="landed-detail-body"></tbody>
            </table>
          </div>
          <div class="empty" id="landed-detail-empty" hidden>No landed rows match the current filters.</div>
        </section>
      </div>
    </section>

    <section class="workspace-view" id="action-view" hidden>
      <div class="panel view-frame">
        <div class="view-head">
          <div>
            <h2 class="view-title">Reservation Risk / Action Queue</h2>
            <p class="view-copy">Operational queue for open reservation exposure, expiry risk, landed-not-released balances, and follow-up priority.</p>
          </div>
        </div>

        <section class="kpi-grid action-kpi-grid" aria-label="Reservation Risk Action Queue KPIs">
          <article class="kpi-card">
            <div class="kpi-label">Open Reservations</div>
            <div class="kpi-value" id="action-kpi-open-reservations">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Open Reserved Bags</div>
            <div class="kpi-value" id="action-kpi-open-bags">-</div>
            <div class="kpi-submeta" id="action-kpi-open-bags-landed">-</div>
            <div class="kpi-submeta" id="action-kpi-open-bags-incoming">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Near-Expiry Reservations</div>
            <div class="kpi-value" id="action-kpi-near-expiry-reservations">-</div>
            <div class="kpi-submeta" id="action-kpi-near-expiry-meta">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Breached Reservations</div>
            <div class="kpi-value" id="action-kpi-breached-reservations">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Open Reserved Value</div>
            <div class="kpi-value" id="action-kpi-open-value">-</div>
            <div class="kpi-submeta" id="action-kpi-open-value-landed">-</div>
            <div class="kpi-submeta" id="action-kpi-open-value-incoming">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Open Exposure Reservations</div>
            <div class="kpi-value" id="action-kpi-open-exposure-reservations">-</div>
          </article>
          <article class="kpi-card">
            <div class="kpi-label">Action Now Reservations</div>
            <div class="kpi-value" id="action-kpi-action-now-reservations">-</div>
          </article>
        </section>

        <section class="chart-grid" aria-label="Reservation Risk Action Queue Charts">
          <article class="chart-card">
            <h3 class="chart-title">Action Bucket Rows</h3>
            <p class="chart-copy">Shows the active reservation queue by follow-up priority bucket.</p>
            <div class="chart-list" id="action-bucket-chart"></div>
            <div class="chart-empty" id="action-bucket-empty" hidden>No open reservation exposure in the current view.</div>
          </article>
          <article class="chart-card">
            <h3 class="chart-title">Open Bags by Expiry Bucket</h3>
            <p class="chart-copy">Shows open bags split between breached, near-expiry, longer-dated, and expiry-unknown reservations.</p>
            <div class="chart-list" id="action-expiry-chart"></div>
            <div class="chart-empty" id="action-expiry-empty" hidden>No open reservation exposure in the current view.</div>
          </article>
          <article class="chart-card">
            <h3 class="chart-title">Top References Not Released Yet</h3>
            <p class="chart-copy" id="action-reference-chart-copy">Ranks landed open reservation references by value where complete, otherwise by bags.</p>
            <div class="chart-list" id="action-reference-chart"></div>
            <div class="chart-empty" id="action-reference-empty" hidden>No landed open reservation references in the current view.</div>
          </article>
        </section>

        <section class="table-shell">
          <div class="table-topbar">
            <div>
              <h3 class="table-title">Action Queue Details</h3>
              <p class="table-subtitle">Default order shows breached first, then near-expiry, then landed-not-approved, then landed-not-released, then other open exposure.</p>
            </div>
            <div class="table-filters">
              <div class="table-filter">
                <label class="control-label" for="action-table-filter">Search action rows</label>
                <input class="control-input" id="action-table-filter" type="search" autocomplete="off" placeholder="Filter by company, client ID, reference, reservation key, or warehouse">
              </div>
              <div class="table-filter compact">
                <label class="control-label" for="action-bucket-filter">Action Bucket</label>
                <select class="control-input" id="action-bucket-filter"></select>
              </div>
              <div class="table-filter compact">
                <label class="control-label" for="action-landing-filter">Landing Status</label>
                <select class="control-input" id="action-landing-filter"></select>
              </div>
              <div class="table-filter compact">
                <label class="control-label" for="action-data-filter">Data Status</label>
                <select class="control-input" id="action-data-filter"></select>
              </div>
            </div>
          </div>
          <div style="overflow:auto;">
            <table>
              <thead>
                <tr>
                  <th>Action Priority</th>
                  <th>Action Bucket</th>
                  <th class="num">Days To Expiry</th>
                  <th>Expiry Date</th>
                  <th>Company</th>
                  <th>Client ID</th>
                  <th>Reservation Key</th>
                  <th>Product Reference</th>
                  <th>Product ID</th>
                  <th>Reservation Status</th>
                  <th>Approval Date</th>
                  <th class="num">Reservation Days</th>
                  <th class="num">Bags Remaining</th>
                  <th class="num">Remaining KG</th>
                  <th class="num">Remaining Value GBP</th>
                  <th>Landing Status</th>
                  <th>Landing Date</th>
                  <th>Warehouse</th>
                  <th>Data Status / Missing Fields</th>
                </tr>
              </thead>
              <tbody id="action-detail-body"></tbody>
            </table>
          </div>
          <div class="empty" id="action-detail-empty" hidden>No action rows match the current filters.</div>
        </section>
      </div>
    </section>
      </div>
    </div>
  </main>

  <script id="workspace-data" type="application/json">{payload_json}</script>
  <script>
    const data = JSON.parse(document.getElementById("workspace-data").textContent);
    const LANDED_AGING_BUCKETS = ["0-30", "31-60", "61-90", "91-180", "181-270", "270+"];
    const root = document.documentElement;
    const themeToggle = document.getElementById("theme-toggle");
    const sharedSelectorPanel = document.getElementById("shared-selector-panel");
    const referenceInput = document.getElementById("reference-search");
    const optionList = document.getElementById("reference-options");
    const selectedReferenceValueEl = document.getElementById("selected-reference-value");
    const selectedReferenceChipEl = document.getElementById("selected-reference-chip");
    const sharedSelectorResetButton = document.getElementById("shared-selector-reset");
    const landedResetButton = document.getElementById("landed-reset");
    const tableFilter = document.getElementById("table-filter");
    const tableBody = document.getElementById("reservation-table-body");
    const emptyState = document.getElementById("reservation-empty");
    const productDetailBody = document.getElementById("product-detail-body");
    const productDetailEmpty = document.getElementById("product-detail-empty");
    const clientDetailBody = document.getElementById("client-detail-body");
    const clientDetailEmpty = document.getElementById("client-detail-empty");
    const clientTableFilter = document.getElementById("client-table-filter");
    const clientConcentrationFilter = document.getElementById("client-concentration-filter");
    const clientDatePreset = document.getElementById("client-date-preset");
    const clientDateFromShell = document.getElementById("client-date-from-shell");
    const clientDateToShell = document.getElementById("client-date-to-shell");
    const clientDateFrom = document.getElementById("client-date-from");
    const clientDateTo = document.getElementById("client-date-to");
    const landedDetailBody = document.getElementById("landed-detail-body");
    const landedDetailEmpty = document.getElementById("landed-detail-empty");
    const landedTableFilter = document.getElementById("landed-table-filter");
    const landedWarehouseFilter = document.getElementById("landed-warehouse-filter");
    const landedAgingFilter = document.getElementById("landed-aging-filter");
    const landedStatusFilter = document.getElementById("landed-status-filter");
    const actionDetailBody = document.getElementById("action-detail-body");
    const actionDetailEmpty = document.getElementById("action-detail-empty");
    const actionTableFilter = document.getElementById("action-table-filter");
    const actionBucketFilter = document.getElementById("action-bucket-filter");
    const actionLandingFilter = document.getElementById("action-landing-filter");
    const actionDataFilter = document.getElementById("action-data-filter");
    const tabButtons = Array.from(document.querySelectorAll(".module-nav-button"));
    const sortButtons = Array.from(document.querySelectorAll("[data-sort]"));
    const reservationView = document.getElementById("reservation-view");
    const productView = document.getElementById("product-view");
    const clientView = document.getElementById("client-view");
    const landedView = document.getElementById("landed-view");
    const actionView = document.getElementById("action-view");

    const summaryByReference = new Map((data.reference_summary || []).map((row) => [row.product_reference, row]));
    const detailsByReference = new Map();
    const productSummaryByReference = new Map((data.product_reference_summary || []).map((row) => [row.product_reference, row]));
    const productDetailsByReference = new Map();
    const clientActivityRows = Array.isArray(data.client_activity_rows) ? data.client_activity_rows : [];
    const landedSummary = data.landed_stock_summary || {{}};
    const landedAgingRaw = Array.isArray(data.landed_stock_aging) ? data.landed_stock_aging : [];
    const landedWarehouseExposure = Array.isArray(data.landed_stock_warehouse_exposure) ? data.landed_stock_warehouse_exposure : [];
    const landedReferenceExposure = Array.isArray(data.landed_stock_reference_exposure) ? data.landed_stock_reference_exposure : [];
    const landedDetails = Array.isArray(data.landed_stock_details) ? data.landed_stock_details : [];
    const actionQueue = data.reservation_action_queue || {{}};
    const actionSummary = actionQueue.summary || {{}};
    const actionBucketCounts = Array.isArray(actionQueue.action_bucket_counts) ? actionQueue.action_bucket_counts : [];
    const actionExpiryBuckets = Array.isArray(actionQueue.open_bags_by_expiry_bucket) ? actionQueue.open_bags_by_expiry_bucket : [];
    const actionTopReferences = actionQueue.top_landed_references || {{ rows: [] }};
    const actionDetails = Array.isArray(actionQueue.details) ? actionQueue.details : [];
    const landedAgingByBucket = new Map(
      landedAgingRaw.map((row) => [String(row.aging_bucket || "").trim(), Number(row.unsold_bags || 0)])
    );
    const landedAging = LANDED_AGING_BUCKETS.map((bucket) => ({{
      aging_bucket: bucket,
      unsold_bags: landedAgingByBucket.get(bucket) || 0,
    }}));
    for (const row of data.reservation_details || []) {{
      const key = row.product_reference || "";
      if (!detailsByReference.has(key)) {{
        detailsByReference.set(key, []);
      }}
      detailsByReference.get(key).push(row);
    }}
    for (const row of data.product_landing_profile || []) {{
      const key = row.product_reference || "";
      if (!productDetailsByReference.has(key)) {{
        productDetailsByReference.set(key, []);
      }}
      productDetailsByReference.get(key).push(row);
    }}

    let state = {{
      selectedReference: data.default_reference || "",
      filterText: "",
      landedFilterText: "",
      landedWarehouse: "all",
      landedAgingBucket: "all",
      landedStatus: "all",
      clientFilterText: "",
      clientConcentration: "all",
      clientDatePreset: "all",
      clientDateFrom: "",
      clientDateTo: "",
      sortKey: "company_name",
      sortDirection: "asc",
      actionFilterText: "",
      actionBucket: "all",
      actionLanding: "all",
      actionDataStatus: "all",
      activeTab: "reservation",
    }};

    function canonicalAgingBucket(value) {{
      const label = String(value ?? "").trim();
      return LANDED_AGING_BUCKETS.includes(label) ? label : "Date unavailable";
    }}

    function currentSelectedReference() {{
      return state.selectedReference;
    }}

    function setCurrentSelectedReference(value) {{
      state.selectedReference = value;
    }}

    function normaliseSelectedReferenceForActiveTab() {{
      const validOptions = new Set((data.reference_options || []).map((row) => String(row.product_reference || "").trim()).filter(Boolean));
      const selected = currentSelectedReference().trim();
      if (!selected) {{
        return;
      }}
      if (validOptions.has(selected)) {{
        return;
      }}
      setCurrentSelectedReference("");
    }}

    function escapeHtml(value) {{
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function formatNumber(value, digits = 0) {{
      const number = Number(value || 0);
      return Number.isFinite(number)
        ? number.toLocaleString("en-GB", {{
            minimumFractionDigits: digits,
            maximumFractionDigits: digits,
          }})
        : "-";
    }}

    function formatMoney(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number)
        ? "GBP " + number.toLocaleString("en-GB", {{
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }})
        : "GBP -";
    }}

    function formatKilos(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number)
        ? number.toLocaleString("en-GB", {{
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }}) + " kg"
        : "- kg";
    }}

    function formatBags(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number)
        ? formatNumber(number, 0) + " bags"
        : "Unavailable";
    }}

    function formatKgOrUnavailable(value, isAvailable) {{
      if (!isAvailable) {{
        return "Unavailable";
      }}
      return formatKilos(value);
    }}

    function formatCompactMoney(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number)
        ? "GBP " + number.toLocaleString("en-GB", {{
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }})
        : "Unavailable";
    }}

    function formatPercent(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number)
        ? number.toLocaleString("en-GB", {{
            style: "percent",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }})
        : "-%";
    }}

    function formatPercentOrUnavailable(value, isAvailable) {{
      if (!isAvailable || value === null || value === undefined) {{
        return "Unavailable";
      }}
      return formatPercent(value);
    }}

    function clientLabel(row) {{
      const company = String(row.company_name || "").trim() || "Unknown";
      const clientId = String(row.client_id || "").trim();
      return clientId ? company + " (" + clientId + ")" : company;
    }}

    function compareValues(left, right) {{
      const leftNumber = Number(left);
      const rightNumber = Number(right);
      if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {{
        return leftNumber - rightNumber;
      }}
      return String(left ?? "").localeCompare(String(right ?? ""), "en", {{ sensitivity: "base" }});
    }}

    function currentDetails() {{
      const rows = [...(detailsByReference.get(state.selectedReference) || [])];
      const filterText = state.filterText.trim().toLowerCase();
      const filtered = filterText
        ? rows.filter((row) => {{
            const haystack = [
              row.company_name,
              row.request_status,
              row.warehouse,
              row.reservation_key,
              row.client_id,
            ].join(" ").toLowerCase();
            return haystack.includes(filterText);
          }})
        : rows;

      filtered.sort((a, b) => {{
        const direction = state.sortDirection === "asc" ? 1 : -1;
        const primary = compareValues(a[state.sortKey], b[state.sortKey]);
        if (primary !== 0) {{
          return primary * direction;
        }}
        return compareValues(a.id_request, b.id_request);
      }});
      return filtered;
    }}

    function renderOptions() {{
      const options = (data.reference_options || []).map((row) => {{
        const landingStatus = row.landing_status || "Unknown";
        const reservationState = row.has_reservations ? "Reservations live" : "No reservations";
        const label = row.product_reference + " | " + landingStatus + " | " + reservationState;
        return '<option value="' + escapeHtml(row.product_reference) + '" label="' + escapeHtml(label) + '"></option>';
      }});
      optionList.innerHTML = options.join("");
    }}

    function statusTone(value) {{
      const status = String(value ?? "").trim().toLowerCase();
      if (status === "landed not approved" || status === "p3 landed not approved" || status === "breached" || status === "p1 breached") {{
        return "status-bad";
      }}
      if (status === "incoming" || status === "created") {{
        return "status-warm";
      }}
      if (status === "landed" || status === "completed") {{
        return "status-good";
      }}
      return "status-neutral";
    }}

    function renderStatusChip(value) {{
      const label = String(value ?? "").trim() || "-";
      return "<span class='pill " + statusTone(label) + "'>" + escapeHtml(label) + "</span>";
    }}

    function formatDateLabel(value) {{
      const text = String(value ?? "").trim();
      if (!/^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(text)) {{
        return "";
      }}
      const [year, month, day] = text.split("-").map(Number);
      const date = new Date(Date.UTC(year, month - 1, day));
      return date.toLocaleDateString("en-GB", {{
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }});
    }}

    function dayDiff(fromDate, toDate) {{
      if (!/^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(fromDate) || !/^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(toDate)) {{
        return null;
      }}
      const from = new Date(fromDate + "T00:00:00Z");
      const to = new Date(toDate + "T00:00:00Z");
      const diff = Math.round((to.getTime() - from.getTime()) / 86400000);
      return Number.isFinite(diff) ? diff : null;
    }}

    function landingSupportText(summary, rows) {{
      if (!summary) {{
        return "Landing date not available for this reference.";
      }}
      const status = String(summary.landing_status ?? "").trim().toLowerCase();
      const snapshotDate = String(data.snapshot_date ?? "").trim();
      const datedRows = rows
        .map((row) => String(row.landing_date ?? "").trim())
        .filter((value) => /^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(value));
      const uniqueDates = [...new Set(datedRows)].sort();
      if (uniqueDates.length !== 1) {{
        return "Landing date not available for this reference.";
      }}
      const landingDate = uniqueDates[0];
      const landingLabel = formatDateLabel(landingDate);
      if (!landingLabel) {{
        return "Landing date not available for this reference.";
      }}
      const diff = dayDiff(snapshotDate, landingDate);
      if (status === "incoming") {{
        if (diff === null) {{
          return "Expected on " + landingLabel + ".";
        }}
        if (diff > 0) {{
          return "Expected on " + landingLabel + ", in " + formatNumber(diff, 0) + " days.";
        }}
        if (diff === 0) {{
          return "Expected to land today, " + landingLabel + ".";
        }}
        return "Expected on " + landingLabel + ".";
      }}
      if (status === "landed") {{
        if (diff === null || diff >= 0) {{
          return "Recorded as landed on " + landingLabel + ".";
        }}
        const daysSinceLanding = Math.abs(diff);
        return "Recorded as landed on " + landingLabel + ", " + formatNumber(daysSinceLanding, 0) + " days ago.";
      }}
      return "Landing date not available for this reference.";
    }}

    function renderSelection() {{
      const selectedReference = currentSelectedReference() || "Select product";
      const summary = summaryByReference.get(state.selectedReference);
      const landingStatus = currentSelectedReference() ? (summary?.landing_status || "Unknown") : "Not selected";
      selectedReferenceValueEl.textContent = selectedReference;
      selectedReferenceChipEl.innerHTML =
        "<span>Reference: <strong>" + escapeHtml(selectedReference) + "</strong></span>" +
        renderStatusChip(landingStatus);
      referenceInput.value = currentSelectedReference() || "";
    }}

    function resetSharedSelectorView() {{
      state.selectedReference = "";
      state.filterText = "";
      state.sortKey = "company_name";
      state.sortDirection = "asc";
      tableFilter.value = "";
      render();
    }}

    function resetLandedView() {{
      state.landedFilterText = "";
      state.landedWarehouse = "all";
      state.landedAgingBucket = "all";
      state.landedStatus = "all";
      landedTableFilter.value = "";
      landedWarehouseFilter.value = "all";
      landedAgingFilter.value = "all";
      landedStatusFilter.value = "all";
      render();
    }}

    function normaliseIsoDate(value) {{
      const text = String(value ?? "").trim();
      return /^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(text) ? text : "";
    }}

    function dateFromIso(value) {{
      const text = normaliseIsoDate(value);
      if (!text) {{
        return null;
      }}
      const [year, month, day] = text.split("-").map(Number);
      return new Date(Date.UTC(year, month - 1, day));
    }}

    function isoFromDate(date) {{
      if (!(date instanceof Date) || Number.isNaN(date.getTime())) {{
        return "";
      }}
      return date.toISOString().slice(0, 10);
    }}

    function addDays(value, days) {{
      const base = dateFromIso(value);
      if (!base) {{
        return "";
      }}
      const next = new Date(base.getTime());
      next.setUTCDate(next.getUTCDate() + days);
      return isoFromDate(next);
    }}

    function snapshotAnchorDate() {{
      return normaliseIsoDate(data.snapshot_date || "");
    }}

    function financialYearStart(value) {{
      const anchor = dateFromIso(value);
      if (!anchor) {{
        return "";
      }}
      const year = anchor.getUTCMonth() >= 7 ? anchor.getUTCFullYear() : anchor.getUTCFullYear() - 1;
      return isoFromDate(new Date(Date.UTC(year, 7, 1)));
    }}

    function monthStart(value) {{
      const anchor = dateFromIso(value);
      if (!anchor) {{
        return "";
      }}
      return isoFromDate(new Date(Date.UTC(anchor.getUTCFullYear(), anchor.getUTCMonth(), 1)));
    }}

    function currentClientDateRange() {{
      const anchor = snapshotAnchorDate();
      if (state.clientDatePreset === "all") {{
        return {{ from: "", to: "", anchored: false }};
      }}
      if (state.clientDatePreset === "custom") {{
        const from = normaliseIsoDate(state.clientDateFrom);
        const to = normaliseIsoDate(state.clientDateTo);
        return {{
          from,
          to,
          anchored: Boolean(from || to),
        }};
      }}
      if (!anchor) {{
        return {{ from: "", to: "", anchored: false }};
      }}
      if (state.clientDatePreset === "last-30") {{
        return {{ from: addDays(anchor, -29), to: anchor, anchored: true }};
      }}
      if (state.clientDatePreset === "last-90") {{
        return {{ from: addDays(anchor, -89), to: anchor, anchored: true }};
      }}
      if (state.clientDatePreset === "month-to-date") {{
        return {{ from: monthStart(anchor), to: anchor, anchored: true }};
      }}
      if (state.clientDatePreset === "financial-year-to-date") {{
        return {{ from: financialYearStart(anchor), to: anchor, anchored: true }};
      }}
      return {{ from: "", to: "", anchored: false }};
    }}

    function currentClientActivityRows() {{
      const range = currentClientDateRange();
      if (!range.anchored) {{
        return clientActivityRows;
      }}
      return clientActivityRows.filter((row) => {{
        const requestDate = normaliseIsoDate(row.request_date || "");
        if (!requestDate) {{
          return false;
        }}
        if (range.from && requestDate < range.from) {{
          return false;
        }}
        if (range.to && requestDate > range.to) {{
          return false;
        }}
        return true;
      }});
    }}

    function aggregateClientMetrics(rows) {{
      if (!rows.length) {{
        return {{
          summary: {{
            clients_with_current_exposure: 0,
            total_current_reserved_value_gbp: 0,
            total_current_reserved_value_available: true,
            largest_client_company_name: "",
            largest_client_id: "",
            largest_client_reserved_value_gbp: 0,
            largest_client_reserved_value_available: true,
            clients_concentrated_in_one_reference: 0,
            concentration_top_five_share: null,
            concentration_top_ten_share: null,
            concentration_rest_share: null,
            concentration_share_available: false,
          }},
          details: [],
          topExposure: [],
          concentration: [],
        }};
      }}

      const clientGroups = new Map();
      for (const row of rows) {{
        const clientKey = String(row.client_key || row.client_id || row.company_name || "").trim();
        if (!clientKey) {{
          continue;
        }}
        if (!clientGroups.has(clientKey)) {{
          clientGroups.set(clientKey, []);
        }}
        clientGroups.get(clientKey).push(row);
      }}

      const details = [];
      const concentration = [];
      for (const [clientKey, group] of [...clientGroups.entries()].sort((a, b) => a[0].localeCompare(b[0], "en", {{ sensitivity: "base" }}))) {{
        const clientId = String(group[0].client_id || "").trim();
        const companyCandidates = [...new Set(group.map((row) => String(row.company_name || "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b, "en", {{ sensitivity: "base" }}));
        const companyName = companyCandidates[0] || clientId || clientKey;
        const reservationRowCount = group.length;
        const reservedBags = group.reduce((sum, row) => sum + Number(row.effective_bags || 0), 0);
        const reservedKg = group.reduce((sum, row) => sum + Number(row.reserved_kg || 0), 0);
        const reservedValue = group.reduce((sum, row) => sum + Number(row.reserved_value_gbp || 0), 0);
        const valueAvailable = group.every((row) => Boolean(row.reserved_value_available));
        const distinctReferenceCount = new Set(group.map((row) => String(row.product_reference || "").trim()).filter(Boolean)).size;
        const landingStatuses = [...new Set(group.map((row) => String(row.landing_status || "").trim().toLowerCase()).filter((value) => value === "incoming" || value === "landed"))].sort();
        let landingMix = "Unknown";
        if (landingStatuses.length === 1) {{
          landingMix = landingStatuses[0].charAt(0).toUpperCase() + landingStatuses[0].slice(1);
        }} else if (landingStatuses.length > 1) {{
          landingMix = "Mixed";
        }}

        const referenceMap = new Map();
        for (const row of group) {{
          const reference = String(row.product_reference || "").trim();
          if (!reference) {{
            continue;
          }}
          if (!referenceMap.has(reference)) {{
            referenceMap.set(reference, {{
              product_reference: reference,
              reserved_value_gbp: 0,
              reserved_kg: 0,
              reserved_bags: 0,
            }});
          }}
          const entry = referenceMap.get(reference);
          entry.reserved_value_gbp += Number(row.reserved_value_gbp || 0);
          entry.reserved_kg += Number(row.reserved_kg || 0);
          entry.reserved_bags += Number(row.effective_bags || 0);
        }}

        const referenceGroups = [...referenceMap.values()].sort((left, right) => {{
          const valueDiff = Number(right.reserved_value_gbp || 0) - Number(left.reserved_value_gbp || 0);
          if (valueDiff !== 0) {{
            return valueDiff;
          }}
          const kgDiff = Number(right.reserved_kg || 0) - Number(left.reserved_kg || 0);
          if (kgDiff !== 0) {{
            return kgDiff;
          }}
          return String(left.product_reference || "").localeCompare(String(right.product_reference || ""), "en", {{ sensitivity: "base" }});
        }});

        let primaryReference = "";
        let primaryReferenceShare = null;
        let primaryReferenceShareAvailable = false;
        if (referenceGroups.length) {{
          const primaryRow = referenceGroups[0];
          primaryReference = String(primaryRow.product_reference || "").trim();
          if (valueAvailable && reservedValue > 0) {{
            primaryReferenceShare = Number(primaryRow.reserved_value_gbp || 0) / reservedValue;
            primaryReferenceShareAvailable = true;
          }} else if (reservedKg > 0) {{
            primaryReferenceShare = Number(primaryRow.reserved_kg || 0) / reservedKg;
            primaryReferenceShareAvailable = true;
          }}
          for (const referenceRow of referenceGroups) {{
            concentration.push({{
              company_name: companyName,
              client_id: clientId,
              product_reference: referenceRow.product_reference,
              reserved_value_gbp: Number(referenceRow.reserved_value_gbp.toFixed(2)),
            }});
          }}
        }}

        details.push({{
          company_name: companyName,
          client_id: clientId,
          reservation_row_count: reservationRowCount,
          reserved_bags: Number(reservedBags.toFixed(4)),
          reserved_kg: Number(reservedKg.toFixed(4)),
          reserved_value_gbp: Number(reservedValue.toFixed(2)),
          reserved_value_available: valueAvailable,
          distinct_reference_count: distinctReferenceCount,
          primary_reference: primaryReference,
          primary_reference_share: primaryReferenceShare === null ? null : Number(primaryReferenceShare.toFixed(4)),
          primary_reference_share_available: primaryReferenceShareAvailable,
          landing_mix: landingMix,
        }});
      }}

      details.sort((left, right) => {{
        const valueDiff = Number(right.reserved_value_gbp || 0) - Number(left.reserved_value_gbp || 0);
        if (valueDiff !== 0) {{
          return valueDiff;
        }}
        const kgDiff = Number(right.reserved_kg || 0) - Number(left.reserved_kg || 0);
        if (kgDiff !== 0) {{
          return kgDiff;
        }}
        const companyDiff = String(left.company_name || "").localeCompare(String(right.company_name || ""), "en", {{ sensitivity: "base" }});
        if (companyDiff !== 0) {{
          return companyDiff;
        }}
        return String(left.client_id || "").localeCompare(String(right.client_id || ""), "en", {{ sensitivity: "base" }});
      }});

      concentration.sort((left, right) => {{
        const leftDetail = details.find((row) => String(row.company_name || "") === String(left.company_name || "") && String(row.client_id || "") === String(left.client_id || ""));
        const rightDetail = details.find((row) => String(row.company_name || "") === String(right.company_name || "") && String(row.client_id || "") === String(right.client_id || ""));
        const clientValueDiff = Number(rightDetail?.reserved_value_gbp || 0) - Number(leftDetail?.reserved_value_gbp || 0);
        if (clientValueDiff !== 0) {{
          return clientValueDiff;
        }}
        const companyDiff = String(left.company_name || "").localeCompare(String(right.company_name || ""), "en", {{ sensitivity: "base" }});
        if (companyDiff !== 0) {{
          return companyDiff;
        }}
        const valueDiff = Number(right.reserved_value_gbp || 0) - Number(left.reserved_value_gbp || 0);
        if (valueDiff !== 0) {{
          return valueDiff;
        }}
        return String(left.product_reference || "").localeCompare(String(right.product_reference || ""), "en", {{ sensitivity: "base" }});
      }});

      const rankedClientKeys = new Set(details.filter((row) => Number(row.reserved_bags || 0) > 0).map((row) => String(row.client_id || "").trim() || String(row.company_name || "").trim()));
      const rankedValues = details
        .map((row) => Number(row.reserved_value_gbp || 0))
        .filter((value) => Number.isFinite(value) && value > 0);
      const totalReservedValue = Number(rows.reduce((sum, row) => sum + Number(row.reserved_value_gbp || 0), 0).toFixed(2));
      const totalValueAvailable = rows.every((row) => Boolean(row.reserved_value_available));
      let concentrationTopFiveShare = null;
      let concentrationTopTenShare = null;
      let concentrationRestShare = null;
      let concentrationShareAvailable = false;
      if (totalValueAvailable && totalReservedValue > 0) {{
        const topFiveValue = rankedValues.slice(0, 5).reduce((sum, value) => sum + value, 0);
        const topTenValue = rankedValues.slice(0, 10).reduce((sum, value) => sum + value, 0);
        concentrationTopFiveShare = topFiveValue / totalReservedValue;
        concentrationTopTenShare = topTenValue / totalReservedValue;
        concentrationRestShare = Math.max(0, (totalReservedValue - topTenValue) / totalReservedValue);
        concentrationShareAvailable = true;
      }}
      const summary = {{
        clients_with_current_exposure: rankedClientKeys.size,
        total_current_reserved_value_gbp: totalReservedValue,
        total_current_reserved_value_available: totalValueAvailable,
        largest_client_company_name: details[0]?.company_name || "",
        largest_client_id: details[0]?.client_id || "",
        largest_client_reserved_value_gbp: Number((details[0]?.reserved_value_gbp || 0).toFixed(2)),
        largest_client_reserved_value_available: Boolean(details[0]?.reserved_value_available ?? true),
        clients_concentrated_in_one_reference: details.filter((row) => Boolean(row.primary_reference_share_available) && row.primary_reference_share !== null && Number(row.primary_reference_share || 0) >= 0.8).length,
        concentration_top_five_share: concentrationTopFiveShare === null ? null : Number(concentrationTopFiveShare.toFixed(4)),
        concentration_top_ten_share: concentrationTopTenShare === null ? null : Number(concentrationTopTenShare.toFixed(4)),
        concentration_rest_share: concentrationRestShare === null ? null : Number(concentrationRestShare.toFixed(4)),
        concentration_share_available: concentrationShareAvailable,
      }};
      const topExposure = details.slice(0, 10).map((row) => ({{
        company_name: row.company_name,
        client_id: row.client_id,
        reserved_value_gbp: row.reserved_value_gbp,
      }}));
      return {{ summary, details, topExposure, concentration }};
    }}

    function currentClientMetrics() {{
      const filteredRows = currentClientActivityRows();
      const aggregated = aggregateClientMetrics(filteredRows);
      return {{
        ...aggregated,
        filteredRows,
      }};
    }}

    function renderClientDateControls() {{
      const showCustomRange = state.clientDatePreset === "custom";
      clientDatePreset.value = state.clientDatePreset;
      clientDateFromShell.hidden = !showCustomRange;
      clientDateToShell.hidden = !showCustomRange;
      clientDateFrom.value = state.clientDateFrom;
      clientDateTo.value = state.clientDateTo;
    }}

    function renderReservationKpis() {{
      const summary = summaryByReference.get(state.selectedReference);
      const rows = detailsByReference.get(state.selectedReference) || [];
      const kg = document.getElementById("reservation-kpi-kg");
      const bags = document.getElementById("reservation-kpi-bags");
      const value = document.getElementById("reservation-kpi-value");
      const reservedPct = document.getElementById("reservation-kpi-reserved-pct");
      const availableBags = document.getElementById("reservation-kpi-available-bags");
      const clients = document.getElementById("reservation-kpi-clients");
      const landingStatus = document.getElementById("reservation-kpi-landing-status");
      const landingSupport = document.getElementById("reservation-kpi-landing-support");

      if (!summary) {{
        kg.textContent = "0 kg";
        bags.textContent = "0 reserved bags";
        value.textContent = "GBP 0";
        reservedPct.textContent = "0%";
        availableBags.textContent = "0 bags still available";
        clients.textContent = "0";
        landingStatus.innerHTML = renderStatusChip("No reservations");
        landingSupport.textContent = "Landing date not available for this reference.";
        return;
      }}

      kg.textContent = formatKilos(summary.reserved_kg);
      bags.textContent = formatNumber(summary.reserved_bags, 0) + " reserved bags";
      value.textContent = formatMoney(summary.reserved_value_gbp);
      reservedPct.textContent = formatPercent(summary.reserved_pct);
      availableBags.textContent = formatNumber(summary.bags_available, 0) + " bags still available";
      clients.textContent = formatNumber(summary.client_count, 0);
      landingStatus.innerHTML = renderStatusChip(summary.landing_status || "-");
      landingSupport.textContent = landingSupportText(summary, rows);
    }}

    function formatReservationKey(value) {{
      const text = String(value ?? "").trim();
      if (!text) {{
        return "-";
      }}
      const number = Number(text);
      if (Number.isFinite(number) && /^-?\\d+\\.0+$/.test(text)) {{
        return formatNumber(number, 0);
      }}
      return text;
    }}

    function renderReservationTable() {{
      const rows = currentDetails();
      emptyState.hidden = rows.length > 0;
      tableBody.innerHTML = rows.map((row) => {{
        const reservationKey = formatReservationKey(row.reservation_key || row.id_request || "-");
        return "<tr>" +
          "<td><strong>" + escapeHtml(row.company_name || "-") + "</strong></td>" +
          "<td>" + renderStatusChip(row.request_status || "-") + "</td>" +
          "<td class='num'>" + escapeHtml(formatNumber(row.effective_bags, 0)) + "</td>" +
          "<td class='num'>" + escapeHtml(formatKilos(row.reserved_kg)) + "</td>" +
          "<td class='num'>" + escapeHtml(formatMoney(row.reserved_value_gbp)) + "</td>" +
          "<td>" + renderStatusChip(row.landing_status || "-") + "</td>" +
          "<td>" + escapeHtml(row.landing_date || "-") + "</td>" +
          "<td>" + escapeHtml(row.warehouse || "-") + "</td>" +
          "<td><span class='muted'>" + escapeHtml(reservationKey) + "</span></td>" +
        "</tr>";
      }}).join("");
    }}

    function renderProductKpis() {{
      const summary = productSummaryByReference.get(state.selectedReference);
      const incoming = document.getElementById("product-kpi-incoming");
      const incomingKg = document.getElementById("product-kpi-incoming-kg");
      const landed = document.getElementById("product-kpi-landed");
      const landedKg = document.getElementById("product-kpi-landed-kg");
      const available = document.getElementById("product-kpi-available");
      const availableKg = document.getElementById("product-kpi-available-kg");
      const health = document.getElementById("product-kpi-health");
      const healthMeta = document.getElementById("product-kpi-health-meta");

      if (!summary) {{
        incoming.textContent = "0 bags";
        incomingKg.textContent = "0 kg";
        landed.textContent = "0 bags";
        landedKg.textContent = "0 kg";
        available.textContent = "Unavailable";
        availableKg.textContent = "Unavailable";
        health.innerHTML = renderStatusChip("Data Incomplete");
        healthMeta.textContent = "Safe stock-state classification only.";
        return;
      }}

      incoming.textContent = summary.incoming_bags_available ? formatBags(summary.incoming_bags) : "Unavailable";
      incomingKg.textContent = formatKgOrUnavailable(summary.incoming_kg, summary.incoming_kg_available);
      landed.textContent = summary.landed_bags_available ? formatBags(summary.landed_bags) : "Unavailable";
      landedKg.textContent = formatKgOrUnavailable(summary.landed_kg, summary.landed_kg_available);
      available.textContent = summary.landed_available_bags_available ? formatBags(summary.landed_available_bags) : "Unavailable";
      availableKg.textContent = formatKgOrUnavailable(summary.landed_available_kg, summary.landed_available_kg_available);
      health.innerHTML = renderStatusChip(summary.stock_health || "Data Incomplete");
      healthMeta.textContent = "Safe stock-state classification only.";
    }}

    function renderProductTable() {{
      const rows = productDetailsByReference.get(state.selectedReference) || [];
      productDetailEmpty.hidden = rows.length > 0;
      productDetailBody.innerHTML = rows.map((row) => {{
        const bags = row.bags === null ? "Unavailable" : formatNumber(row.bags, 0);
        const availableBags = row.bags_available === null ? "Unavailable" : formatNumber(row.bags_available, 0);
        const landingStatus = String(row.landing_status || "").trim().toLowerCase();
        let daysLabel = "Date unavailable";
        if (landingStatus === "incoming") {{
          daysLabel = "Not landed";
        }} else if (landingStatus === "landed") {{
          const diff = dayDiff(row.landing_date || "", data.snapshot_date || "");
          if (diff !== null && diff >= 0) {{
            daysLabel = formatNumber(diff, 0) + " days";
          }}
        }}
        return "<tr>" +
          "<td><strong>" + escapeHtml(row.product_id || "-") + "</strong></td>" +
          "<td>" + escapeHtml(row.warehouse || "-") + "</td>" +
          "<td>" + renderStatusChip(row.landing_status || "-") + "</td>" +
          "<td>" + escapeHtml(row.landing_date || "-") + "</td>" +
          "<td>" + escapeHtml(daysLabel) + "</td>" +
          "<td class='num'>" + escapeHtml(bags) + "</td>" +
          "<td class='num'>" + escapeHtml(availableBags) + "</td>" +
        "</tr>";
      }}).join("");
    }}

    function currentClientDetails() {{
      const clientMetrics = currentClientMetrics();
      const text = state.clientFilterText.trim().toLowerCase();
      return clientMetrics.details.filter((row) => {{
        const share = Number(row.primary_reference_share || 0);
        const shareAvailable = Boolean(row.primary_reference_share_available);
        if (state.clientConcentration === "concentrated" && (!shareAvailable || share < 0.8)) {{
          return false;
        }}
        if (state.clientConcentration === "multi" && shareAvailable && share >= 0.8) {{
          return false;
        }}
        if (!text) {{
          return true;
        }}
        const haystack = [
          row.company_name,
          row.client_id,
          row.primary_reference,
        ].join(" ").toLowerCase();
        return haystack.includes(text);
      }});
    }}

    function currentLandedDetails() {{
      const text = state.landedFilterText.trim().toLowerCase();
      return landedDetails.filter((row) => {{
        if (state.landedWarehouse !== "all" && (row.warehouse || "Unknown") !== state.landedWarehouse) {{
          return false;
        }}
        if (state.landedAgingBucket !== "all" && canonicalAgingBucket(row.aging_bucket) !== state.landedAgingBucket) {{
          return false;
        }}
        if (state.landedStatus === "incomplete" && String(row.data_status || "").trim().toLowerCase() === "complete") {{
          return false;
        }}
        if (state.landedStatus === "complete" && String(row.data_status || "").trim().toLowerCase() !== "complete") {{
          return false;
        }}
        if (!text) {{
          return true;
        }}
        const haystack = [
          row.product_reference,
          row.product_id,
          row.warehouse,
          row.aging_bucket,
          row.data_status,
        ].join(" ").toLowerCase();
        return haystack.includes(text);
      }});
    }}

    function renderBarChart(containerId, emptyId, rows, labelKey, valueKey, formatter, showZeroRows = false) {{
      const container = document.getElementById(containerId);
      const empty = document.getElementById(emptyId);
      const filteredRows = showZeroRows ? rows : rows.filter((row) => Number(row[valueKey] || 0) > 0);
      empty.hidden = filteredRows.length > 0;
      if (!filteredRows.length) {{
        container.innerHTML = "";
        return;
      }}
      const maxValue = Math.max(...filteredRows.map((row) => Number(row[valueKey] || 0)), 0);
      container.innerHTML = filteredRows.map((row) => {{
        const rawValue = Number(row[valueKey] || 0);
        const width = maxValue > 0 ? Math.max((rawValue / maxValue) * 100, 2) : 0;
        return "<div class='bar-row'>" +
          "<div class='bar-head'>" +
            "<span class='bar-label'>" + escapeHtml(row[labelKey] || "-") + "</span>" +
            "<span class='bar-value'>" + escapeHtml(formatter(rawValue)) + "</span>" +
          "</div>" +
          "<div class='bar-track'><div class='bar-fill' style='width:" + escapeHtml(formatNumber(width, 2)) + "%'></div></div>" +
        "</div>";
      }}).join("");
    }}

    function renderStackedBarChart(containerId, emptyId, clients, segments) {{
      const container = document.getElementById(containerId);
      const empty = document.getElementById(emptyId);
      const topClients = clients.filter((row) => Number(row.reserved_value_gbp || 0) > 0).slice(0, 8);
      if (!topClients.length) {{
        empty.hidden = false;
        container.innerHTML = "";
        return;
      }}

      const clientKeys = topClients.map((row) => clientLabel(row));
      const segmentRows = segments.filter((row) => clientKeys.includes(clientLabel(row)));
      const references = [...new Set(segmentRows.map((row) => String(row.product_reference || "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b, "en", {{ sensitivity: "base" }}));
      const palette = ["#215376", "#a96a3e", "#2f7d4a", "#8f4f8b", "#8a6d1d", "#56657a", "#6e8f2a", "#b35656"];
      const colorByReference = new Map(references.map((reference, index) => [reference, palette[index % palette.length]]));
      empty.hidden = false;

      container.innerHTML = topClients.map((client) => {{
        const total = Number(client.reserved_value_gbp || 0);
        const rows = segmentRows.filter((row) => clientLabel(row) === clientLabel(client) && Number(row.reserved_value_gbp || 0) > 0);
        if (!rows.length || total <= 0) {{
          return "";
        }}
        empty.hidden = true;
        const segmentsHtml = rows.map((row) => {{
          const value = Number(row.reserved_value_gbp || 0);
          const width = Math.max((value / total) * 100, 2);
          return "<div class='stack-segment' title='" + escapeHtml(row.product_reference + ": " + formatCompactMoney(value)) + "' style='width:" + escapeHtml(formatNumber(width, 2)) + "%;background:" + escapeHtml(colorByReference.get(row.product_reference) || "#215376") + ";'></div>";
        }}).join("");
        const legendHtml = rows.map((row) => {{
          return "<span class='stack-legend-item'>" +
            "<span class='stack-swatch' style='background:" + escapeHtml(colorByReference.get(row.product_reference) || "#215376") + ";'></span>" +
            "<span>" + escapeHtml(row.product_reference || "-") + " | " + escapeHtml(formatCompactMoney(row.reserved_value_gbp)) + "</span>" +
          "</span>";
        }}).join("");
        return "<div class='stack-row'>" +
          "<div class='bar-head'>" +
            "<span class='bar-label'>" + escapeHtml(clientLabel(client)) + "</span>" +
            "<span class='bar-value'>" + escapeHtml(formatCompactMoney(total)) + "</span>" +
          "</div>" +
          "<div class='stack-bar'>" + segmentsHtml + "</div>" +
          "<div class='stack-legend'>" + legendHtml + "</div>" +
        "</div>";
      }}).filter(Boolean).join("");
    }}

    function renderLandedFilters() {{
      const warehouses = ["all", ...new Set(landedDetails.map((row) => row.warehouse || "Unknown").filter(Boolean).sort((a, b) => a.localeCompare(b, "en", {{ sensitivity: "base" }})))];
      landedWarehouseFilter.innerHTML = warehouses.map((value) => {{
        const label = value === "all" ? "All Warehouses" : value;
        return '<option value="' + escapeHtml(value) + '">' + escapeHtml(label) + '</option>';
      }}).join("");
      landedWarehouseFilter.value = warehouses.includes(state.landedWarehouse) ? state.landedWarehouse : "all";

      const agingOptions = ["all", ...LANDED_AGING_BUCKETS, "Date unavailable"];
      landedAgingFilter.innerHTML = agingOptions.map((value) => {{
        const label = value === "all" ? "All Aging Buckets" : value;
        return '<option value="' + escapeHtml(value) + '">' + escapeHtml(label) + '</option>';
      }}).join("");
      landedAgingFilter.value = agingOptions.includes(state.landedAgingBucket) ? state.landedAgingBucket : "all";

      landedStatusFilter.innerHTML = [
        ['all', 'All Data Status'],
        ['incomplete', 'Incomplete Only'],
        ['complete', 'Complete Only'],
      ].map((entry) => '<option value="' + escapeHtml(entry[0]) + '">' + escapeHtml(entry[1]) + '</option>').join("");
      landedStatusFilter.value = state.landedStatus;
    }}

    function renderLandedKpis() {{
      const unsoldBags = document.getElementById("landed-kpi-unsold-bags");
      const landedBags = document.getElementById("landed-kpi-landed-bags");
      const unsoldKg = document.getElementById("landed-kpi-unsold-kg");
      const unsoldKgMeta = document.getElementById("landed-kpi-unsold-kg-meta");
      const agedBags = document.getElementById("landed-kpi-aged-bags");
      const agedMeta = document.getElementById("landed-kpi-aged-meta");
      const warehouses = document.getElementById("landed-kpi-warehouses");
      const asOf = document.getElementById("landed-kpi-as-of");
      const value = document.getElementById("landed-kpi-value");
      const valueMeta = document.getElementById("landed-kpi-value-meta");

      unsoldBags.textContent = formatBags(landedSummary.unsold_landed_bags);
      landedBags.textContent = formatNumber(landedSummary.landed_bags, 0) + " landed bags recorded";
      unsoldKg.textContent = landedSummary.unsold_landed_kg_available ? formatKilos(landedSummary.unsold_landed_kg) : "Unavailable";
      unsoldKgMeta.textContent = landedSummary.unsold_landed_kg_available
        ? "Complete across all unsold landed rows."
        : "Missing bag size on one or more unsold landed rows.";
      agedBags.textContent = formatBags(landedSummary.aged_180_plus_bags);
      agedMeta.textContent = "Rows in the 181-270 and 270+ buckets.";
      warehouses.textContent = formatNumber(landedSummary.warehouses_exposed, 0);
      asOf.textContent = landedSummary.as_of_date ? "As of " + landedSummary.as_of_date : "As-of date unavailable";
      value.textContent = landedSummary.unsold_landed_value_available
        ? formatCompactMoney(landedSummary.unsold_landed_value_gbp)
        : "Unavailable";
      valueMeta.textContent = landedSummary.value_completeness_status || "Unavailable";
    }}

    function renderClientKpis() {{
      const clientMetrics = currentClientMetrics();
      const count = document.getElementById("client-kpi-count");
      const totalValue = document.getElementById("client-kpi-total-value");
      const totalValueMeta = document.getElementById("client-kpi-total-value-meta");
      const largestValue = document.getElementById("client-kpi-largest-value");
      const largestMeta = document.getElementById("client-kpi-largest-meta");
      const concentrated = document.getElementById("client-kpi-concentrated");
      const topFiveShare = document.getElementById("client-kpi-top-five-share");
      const topTenShare = document.getElementById("client-kpi-top-ten-share");
      const restShare = document.getElementById("client-kpi-rest-share");

      count.textContent = formatNumber(clientMetrics.summary.clients_with_current_exposure || 0, 0);
      totalValue.textContent = clientMetrics.summary.total_current_reserved_value_available
        ? formatCompactMoney(clientMetrics.summary.total_current_reserved_value_gbp)
        : "Unavailable";
      totalValueMeta.textContent = clientMetrics.summary.total_current_reserved_value_available
        ? "Complete across recorded client rows in the selected request-date range."
        : "Unavailable on one or more recorded client rows due to missing kg or price.";
      largestValue.textContent = clientMetrics.summary.largest_client_reserved_value_available
        ? formatCompactMoney(clientMetrics.summary.largest_client_reserved_value_gbp)
        : "Unavailable";
      largestMeta.textContent = clientMetrics.summary.largest_client_company_name
        ? clientLabel({{ company_name: clientMetrics.summary.largest_client_company_name, client_id: clientMetrics.summary.largest_client_id }})
        : "No client activity in the selected date range.";
      concentrated.textContent = formatNumber(clientMetrics.summary.clients_concentrated_in_one_reference || 0, 0);
      if (clientMetrics.summary.concentration_share_available) {{
        topFiveShare.textContent = formatPercent(clientMetrics.summary.concentration_top_five_share);
        topTenShare.textContent = "Top 10: " + formatPercent(clientMetrics.summary.concentration_top_ten_share);
        restShare.textContent = "Rest: " + formatPercent(clientMetrics.summary.concentration_rest_share);
      }} else {{
        topFiveShare.textContent = "No concentration view";
        topTenShare.textContent = "Top 10: unavailable for this range";
        restShare.textContent = "Rest: unavailable for this range";
      }}
    }}

    function renderClientCharts() {{
      const clientMetrics = currentClientMetrics();
      renderBarChart("client-exposure-chart", "client-exposure-empty", clientMetrics.topExposure, "company_name", "reserved_value_gbp", (value) => formatCompactMoney(value));
      renderStackedBarChart("client-concentration-chart", "client-concentration-empty", clientMetrics.topExposure, clientMetrics.concentration);
    }}

    function renderClientTable() {{
      const rows = currentClientDetails();
      clientDetailEmpty.hidden = rows.length > 0;
      clientDetailBody.innerHTML = rows.map((row) => {{
        const reservedValue = row.reserved_value_available ? formatCompactMoney(row.reserved_value_gbp) : "Unavailable";
        const primaryReferenceShare = formatPercentOrUnavailable(row.primary_reference_share, row.primary_reference_share_available);
        return "<tr>" +
          "<td><strong>" + escapeHtml(row.company_name || "-") + "</strong></td>" +
          "<td>" + escapeHtml(row.client_id || "-") + "</td>" +
          "<td class='num'>" + escapeHtml(formatNumber(row.reservation_row_count, 0)) + "</td>" +
          "<td class='num'>" + escapeHtml(formatNumber(row.reserved_bags, 0)) + "</td>" +
          "<td class='num'>" + escapeHtml(formatKilos(row.reserved_kg)) + "</td>" +
          "<td class='num'>" + escapeHtml(reservedValue) + "</td>" +
          "<td class='num'>" + escapeHtml(formatNumber(row.distinct_reference_count, 0)) + "</td>" +
          "<td>" + escapeHtml(row.primary_reference || "-") + "</td>" +
          "<td class='num'>" + escapeHtml(primaryReferenceShare) + "</td>" +
          "<td>" + renderStatusChip(row.landing_mix || "-") + "</td>" +
        "</tr>";
      }}).join("");
    }}

    function renderLandedCharts() {{
      renderBarChart("landed-aging-chart", "landed-aging-empty", landedAging, "aging_bucket", "unsold_bags", (value) => formatNumber(value, 0) + " bags", true);
      renderBarChart("landed-warehouse-chart", "landed-warehouse-empty", landedWarehouseExposure, "warehouse", "unsold_bags", (value) => formatNumber(value, 0) + " bags");
      renderBarChart("landed-reference-chart", "landed-reference-empty", landedReferenceExposure.slice(0, 8), "product_reference", "unsold_bags", (value) => formatNumber(value, 0) + " bags");
    }}

    function renderLandedTable() {{
      const rows = currentLandedDetails();
      landedDetailEmpty.hidden = rows.length > 0;
      landedDetailBody.innerHTML = rows.map((row) => {{
        const days = row.days_since_landing === null ? "Unavailable" : formatNumber(row.days_since_landing, 0);
        const landedBags = row.landed_bags === null ? "Unavailable" : formatNumber(row.landed_bags, 0);
        const unsoldBags = row.unsold_bags === null ? "Unavailable" : formatNumber(row.unsold_bags, 0);
        const unsoldKg = row.unsold_kg === null ? "Unavailable" : formatKilos(row.unsold_kg);
        const unsoldValue = row.unsold_value_gbp === null ? "Unavailable" : formatCompactMoney(row.unsold_value_gbp);
        return "<tr>" +
          "<td><strong>" + escapeHtml(row.product_reference || "-") + "</strong></td>" +
          "<td>" + escapeHtml(row.product_id || "-") + "</td>" +
          "<td>" + escapeHtml(row.warehouse || "Unknown") + "</td>" +
          "<td>" + escapeHtml(row.landing_date || "-") + "</td>" +
          "<td class='num'>" + escapeHtml(days) + "</td>" +
          "<td>" + escapeHtml(row.aging_bucket || "-") + "</td>" +
          "<td class='num'>" + escapeHtml(landedBags) + "</td>" +
          "<td class='num'>" + escapeHtml(unsoldBags) + "</td>" +
          "<td class='num'>" + escapeHtml(unsoldKg) + "</td>" +
          "<td class='num'>" + escapeHtml(unsoldValue) + "</td>" +
          "<td>" + escapeHtml(row.data_status || "-") + "</td>" +
        "</tr>";
      }}).join("");
    }}

    function currentActionDetails() {{
      const text = state.actionFilterText.trim().toLowerCase();
      return actionDetails.filter((row) => {{
        if (state.actionBucket !== "all" && String(row.action_bucket || "") !== state.actionBucket) {{
          return false;
        }}
        if (state.actionLanding !== "all" && String(row.landing_status || "") !== state.actionLanding) {{
          return false;
        }}
        const dataStatus = String(row.data_status || "").trim().toLowerCase();
        if (state.actionDataStatus === "incomplete" && dataStatus === "complete") {{
          return false;
        }}
        if (state.actionDataStatus === "complete" && dataStatus !== "complete") {{
          return false;
        }}
        if (!text) {{
          return true;
        }}
        const haystack = [
          row.company_name,
          row.client_id,
          row.reservation_key,
          row.product_reference,
          row.product_id,
          row.warehouse,
        ].join(" ").toLowerCase();
        return haystack.includes(text);
      }});
    }}

    function renderActionFilters() {{
      const bucketOptions = ["all", "Breached", "Near Expiry", "Landed Not Approved", "Landed Not Released", "Open Exposure"];
      actionBucketFilter.innerHTML = bucketOptions.map((value) => {{
        const label = value === "all" ? "All Buckets" : value;
        return '<option value="' + escapeHtml(value) + '">' + escapeHtml(label) + '</option>';
      }}).join("");
      actionBucketFilter.value = bucketOptions.includes(state.actionBucket) ? state.actionBucket : "all";

      const landingOptions = ["all", ...new Set(actionDetails.map((row) => String(row.landing_status || "").trim()).filter(Boolean).sort((a, b) => a.localeCompare(b, "en", {{ sensitivity: "base" }})))];
      actionLandingFilter.innerHTML = landingOptions.map((value) => {{
        const label = value === "all" ? "All Landing Status" : value;
        return '<option value="' + escapeHtml(value) + '">' + escapeHtml(label) + '</option>';
      }}).join("");
      actionLandingFilter.value = landingOptions.includes(state.actionLanding) ? state.actionLanding : "all";

      actionDataFilter.innerHTML = [
        ["all", "All Data Status"],
        ["incomplete", "Incomplete Only"],
        ["complete", "Complete Only"],
      ].map((entry) => '<option value="' + escapeHtml(entry[0]) + '">' + escapeHtml(entry[1]) + '</option>').join("");
      actionDataFilter.value = state.actionDataStatus;
    }}

    function renderActionKpis() {{
      const openReservations = document.getElementById("action-kpi-open-reservations");
      const openBags = document.getElementById("action-kpi-open-bags");
      const openBagsLanded = document.getElementById("action-kpi-open-bags-landed");
      const openBagsIncoming = document.getElementById("action-kpi-open-bags-incoming");
      const nearExpiry = document.getElementById("action-kpi-near-expiry-reservations");
      const nearExpiryMeta = document.getElementById("action-kpi-near-expiry-meta");
      const breached = document.getElementById("action-kpi-breached-reservations");
      const openValue = document.getElementById("action-kpi-open-value");
      const openValueLanded = document.getElementById("action-kpi-open-value-landed");
      const openValueIncoming = document.getElementById("action-kpi-open-value-incoming");
      const openExposure = document.getElementById("action-kpi-open-exposure-reservations");
      const actionNow = document.getElementById("action-kpi-action-now-reservations");

      openReservations.textContent = formatNumber(actionSummary.open_reservations || 0, 0);
      openBags.textContent = formatBags(actionSummary.open_reserved_bags || 0);
      openBagsLanded.textContent = "Landed: " + formatBags(actionSummary.open_reserved_bags_landed || 0);
      openBagsIncoming.textContent = "Incoming: " + formatBags(actionSummary.open_reserved_bags_incoming || 0);
      nearExpiry.textContent = formatNumber(actionSummary.near_expiry_reservations || 0, 0);
      nearExpiryMeta.textContent = "Threshold: " + formatNumber(actionSummary.near_expiry_threshold_days || 0, 0) + " days to expiry.";
      breached.textContent = formatNumber(actionSummary.breached_reservations || 0, 0);
      openValue.textContent = actionSummary.open_reserved_value_available
        ? formatCompactMoney(actionSummary.open_reserved_value_gbp)
        : "Unavailable";
      openValueLanded.textContent = "Landed: " + (
        actionSummary.open_reserved_value_landed_available
          ? formatCompactMoney(actionSummary.open_reserved_value_landed_gbp)
          : "Unavailable"
      );
      openValueIncoming.textContent = "Incoming: " + (
        actionSummary.open_reserved_value_incoming_available
          ? formatCompactMoney(actionSummary.open_reserved_value_incoming_gbp)
          : "Unavailable"
      );
      openExposure.textContent = formatNumber(actionSummary.open_exposure_reservations || 0, 0);
      actionNow.textContent = formatNumber(actionSummary.action_now_reservations || 0, 0);
    }}

    function renderActionCharts() {{
      renderBarChart("action-bucket-chart", "action-bucket-empty", actionBucketCounts, "action_bucket", "row_count", (value) => formatNumber(value, 0) + " rows", true);
      renderBarChart("action-expiry-chart", "action-expiry-empty", actionExpiryBuckets, "expiry_bucket", "open_bags", (value) => formatNumber(value, 0) + " bags", true);
      const chartCopy = document.getElementById("action-reference-chart-copy");
      chartCopy.textContent = String(actionTopReferences.status || "").trim() || "No landed open reservation references in the current view.";
      renderBarChart(
        "action-reference-chart",
        "action-reference-empty",
        Array.isArray(actionTopReferences.rows) ? actionTopReferences.rows : [],
        "product_reference",
        actionTopReferences.metric === "open_bags" ? "open_bags" : "remaining_value_gbp",
        (value) => actionTopReferences.metric === "open_bags" ? formatNumber(value, 0) + " bags" : formatCompactMoney(value)
      );
    }}

    function renderActionTable() {{
      const rows = currentActionDetails();
      actionDetailEmpty.hidden = rows.length > 0;
      actionDetailBody.innerHTML = rows.map((row) => {{
        const daysToExpiry = row.days_to_expiry === null ? "Unavailable" : formatNumber(row.days_to_expiry, 0);
        const reservationDays = row.reservation_days === null ? "Unavailable" : formatNumber(row.reservation_days, 0);
        const remainingKg = row.remaining_kg === null ? "Unavailable" : formatKilos(row.remaining_kg);
        const remainingValue = row.remaining_value_gbp === null ? "Unavailable" : formatCompactMoney(row.remaining_value_gbp);
        return "<tr>" +
          "<td><strong>" + escapeHtml(row.action_priority || "-") + "</strong></td>" +
          "<td>" + renderStatusChip(row.action_bucket || "-") + "</td>" +
          "<td class='num'>" + escapeHtml(daysToExpiry) + "</td>" +
          "<td>" + escapeHtml(row.expiry_date || "-") + "</td>" +
          "<td><strong>" + escapeHtml(row.company_name || "-") + "</strong></td>" +
          "<td>" + escapeHtml(row.client_id || "-") + "</td>" +
          "<td><span class='muted'>" + escapeHtml(formatReservationKey(row.reservation_key || "-")) + "</span></td>" +
          "<td>" + escapeHtml(row.product_reference || "-") + "</td>" +
          "<td>" + escapeHtml(row.product_id || "-") + "</td>" +
          "<td>" + renderStatusChip(row.request_status || "-") + "</td>" +
          "<td>" + escapeHtml(row.approval_date || "-") + "</td>" +
          "<td class='num'>" + escapeHtml(reservationDays) + "</td>" +
          "<td class='num'>" + escapeHtml(formatNumber(row.bags_remaining, 0)) + "</td>" +
          "<td class='num'>" + escapeHtml(remainingKg) + "</td>" +
          "<td class='num'>" + escapeHtml(remainingValue) + "</td>" +
          "<td>" + renderStatusChip(row.landing_status || "-") + "</td>" +
          "<td>" + escapeHtml(row.landing_date || "-") + "</td>" +
          "<td>" + escapeHtml(row.warehouse || "-") + "</td>" +
          "<td>" + escapeHtml(row.data_status || "-") + "</td>" +
        "</tr>";
      }}).join("");
    }}

    function renderTabs() {{
      const reservationActive = state.activeTab === "reservation";
      const productActive = state.activeTab === "product";
      const clientActive = state.activeTab === "client";
      const landedActive = state.activeTab === "landed";
      const actionActive = state.activeTab === "action";
      sharedSelectorPanel.hidden = landedActive || clientActive || actionActive;
      reservationView.hidden = !reservationActive;
      productView.hidden = !productActive;
      clientView.hidden = !clientActive;
      landedView.hidden = !landedActive;
      actionView.hidden = !actionActive;
      for (const button of tabButtons) {{
        const isActive = button.dataset.tab === state.activeTab;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", isActive ? "true" : "false");
      }}
    }}

    function render() {{
      normaliseSelectedReferenceForActiveTab();
      renderOptions();
      renderSelection();
      renderReservationKpis();
      renderReservationTable();
      renderProductKpis();
      renderProductTable();
      renderClientDateControls();
      renderClientKpis();
      renderClientCharts();
      renderClientTable();
      renderLandedFilters();
      renderLandedKpis();
      renderLandedCharts();
      renderLandedTable();
      renderActionFilters();
      renderActionKpis();
      renderActionCharts();
      renderActionTable();
      renderTabs();
    }}

    function applyTheme(theme) {{
      const nextTheme = theme === "dark" ? "dark" : "light";
      root.setAttribute("data-theme", nextTheme);
      themeToggle.setAttribute("aria-pressed", nextTheme === "dark" ? "true" : "false");
      themeToggle.textContent = nextTheme === "dark" ? "Light Theme" : "Dark Theme";
    }}

    const storedTheme = localStorage.getItem("mcop-reference-workspace-theme");
    applyTheme(storedTheme);

    themeToggle.addEventListener("click", () => {{
      const nextTheme = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      localStorage.setItem("mcop-reference-workspace-theme", nextTheme);
      applyTheme(nextTheme);
    }});

    referenceInput.addEventListener("change", () => {{
      setCurrentSelectedReference(referenceInput.value.trim());
      render();
    }});
    referenceInput.addEventListener("input", () => {{
      if (!referenceInput.value.trim()) {{
        setCurrentSelectedReference("");
        render();
      }}
    }});
    tableFilter.addEventListener("input", () => {{
      state.filterText = tableFilter.value;
      renderReservationTable();
    }});
    clientTableFilter.addEventListener("input", () => {{
      state.clientFilterText = clientTableFilter.value;
      renderClientTable();
    }});
    clientConcentrationFilter.addEventListener("change", () => {{
      state.clientConcentration = clientConcentrationFilter.value;
      renderClientTable();
    }});
    clientDatePreset.addEventListener("change", () => {{
      state.clientDatePreset = clientDatePreset.value;
      render();
    }});
    clientDateFrom.addEventListener("change", () => {{
      state.clientDateFrom = normaliseIsoDate(clientDateFrom.value);
      render();
    }});
    clientDateTo.addEventListener("change", () => {{
      state.clientDateTo = normaliseIsoDate(clientDateTo.value);
      render();
    }});
    landedTableFilter.addEventListener("input", () => {{
      state.landedFilterText = landedTableFilter.value;
      renderLandedTable();
    }});
    landedWarehouseFilter.addEventListener("change", () => {{
      state.landedWarehouse = landedWarehouseFilter.value;
      renderLandedTable();
    }});
    landedAgingFilter.addEventListener("change", () => {{
      state.landedAgingBucket = landedAgingFilter.value;
      renderLandedTable();
    }});
    landedStatusFilter.addEventListener("change", () => {{
      state.landedStatus = landedStatusFilter.value;
      renderLandedTable();
    }});
    actionTableFilter.addEventListener("input", () => {{
      state.actionFilterText = actionTableFilter.value;
      renderActionTable();
    }});
    actionBucketFilter.addEventListener("change", () => {{
      state.actionBucket = actionBucketFilter.value;
      renderActionTable();
    }});
    actionLandingFilter.addEventListener("change", () => {{
      state.actionLanding = actionLandingFilter.value;
      renderActionTable();
    }});
    actionDataFilter.addEventListener("change", () => {{
      state.actionDataStatus = actionDataFilter.value;
      renderActionTable();
    }});
    sharedSelectorResetButton.addEventListener("click", () => {{
      resetSharedSelectorView();
    }});
    landedResetButton.addEventListener("click", () => {{
      resetLandedView();
    }});
    for (const button of sortButtons) {{
      button.addEventListener("click", () => {{
        const nextKey = button.dataset.sort || "company_name";
        if (state.sortKey === nextKey) {{
          state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
        }} else {{
          state.sortKey = nextKey;
          state.sortDirection = "asc";
        }}
        renderReservationTable();
      }});
    }}
    for (const button of tabButtons) {{
      button.addEventListener("click", () => {{
        state.activeTab = button.dataset.tab || "reservation";
        render();
      }});
    }}

    render();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
