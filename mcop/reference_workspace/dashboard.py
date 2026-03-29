from __future__ import annotations

import json
from pathlib import Path


def _safe_json(value: object) -> str:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def write_reference_workspace_html(path: Path, dataset: dict) -> None:
    payload_json = _safe_json(dataset)
    snapshot_date = str(dataset.get("snapshot_date") or "-")
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
      width: min(1340px, calc(100vw - 32px));
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
    .topbar-copy {{
      display: grid;
      gap: 2px;
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
    .toolbar-chip, .theme-toggle, .tab-button {{
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
    .theme-toggle, .tab-button, .sort-button {{
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, background-color 120ms ease;
    }}
    .theme-toggle:hover,
    .theme-toggle:focus-visible,
    .tab-button:hover,
    .tab-button:focus-visible,
    .sort-button:hover,
    .sort-button:focus-visible {{
      transform: translateY(-1px);
      border-color: color-mix(in srgb, var(--accent) 30%, var(--line));
      outline: none;
    }}
    .tab-button.is-active {{
      color: var(--accent);
      border-color: color-mix(in srgb, var(--accent) 34%, var(--line));
      background: color-mix(in srgb, var(--accent-soft) 74%, var(--panel-strong));
    }}
    .hero {{
      margin-top: 18px;
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
    .tab-strip {{
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
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
      .kpi-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 900px) {{
      .shell {{
        width: min(100vw - 18px, 1340px);
      }}
      .topbar {{
        align-items: flex-start;
      }}
    }}
    @media (max-width: 720px) {{
      .hero, .view-frame {{
        padding: 18px;
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
      <div class="topbar-copy">
        <p class="muted" style="margin:0;">MCOP Reference Workspace v1</p>
        <h1 class="topbar-title">Reference Workspace</h1>
      </div>
      <div class="topbar-actions">
        <div class="toolbar-chip">Snapshot: <strong>{snapshot_date}</strong></div>
        <button class="theme-toggle" id="theme-toggle" type="button" aria-pressed="false">Toggle Theme</button>
      </div>
    </header>

    <section class="hero panel">
      <div class="control-grid">
        <section class="control-panel panel">
          <div class="control-head">
            <div>
              <p class="control-label">Reference Selector</p>
              <h2 class="control-title">Choose product reference</h2>
            </div>
            <div class="toolbar-chip" id="selected-reference-chip"></div>
          </div>
          <div>
            <label class="control-label" for="reference-search">Search product reference</label>
            <input class="control-input" id="reference-search" list="reference-options" autocomplete="off" placeholder="Search or select a product reference">
            <datalist id="reference-options"></datalist>
          </div>
          <div class="selected-reference-inline">
            <span class="control-label" style="margin:0;">Selected Reference</span>
            <p class="selected-reference-value" id="selected-reference-value">-</p>
          </div>
        </section>
      </div>
    </section>

    <nav class="tab-strip" aria-label="Workspace tabs">
      <button class="tab-button is-active" id="tab-reservation" type="button" data-tab="reservation" aria-pressed="true">Reservation Intelligence</button>
      <button class="tab-button" id="tab-product" type="button" data-tab="product" aria-pressed="false">Product Reference Intelligence</button>
    </nav>

    <section class="workspace-view" id="reservation-view">
      <div class="panel view-frame">
        <h2 class="view-title">Reservation Intelligence</h2>

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
              <h3 class="table-title">Reservation detail</h3>
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
          <div class="empty" id="reservation-empty" hidden>No reservation rows match the current reference and search.</div>
        </section>
      </div>
    </section>

    <section class="workspace-view" id="product-view" hidden>
      <div class="panel view-frame">
        <h2 class="view-title">Product Reference Intelligence</h2>
        <p class="view-copy">Stock-only view of whether the selected reference looks early-stage, balanced, or at risk of landed build-up.</p>

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
              <h3 class="table-title">Current Stock Exposure by Lot/Warehouse</h3>
              <p class="table-subtitle">Most concerning landed-available rows appear first, followed by other landed rows, then incoming rows.</p>
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
          <div class="empty" id="product-detail-empty" hidden>No product rows match the current reference.</div>
        </section>
      </div>
    </section>
  </main>

  <script id="workspace-data" type="application/json">{payload_json}</script>
  <script>
    const data = JSON.parse(document.getElementById("workspace-data").textContent);
    const root = document.documentElement;
    const themeToggle = document.getElementById("theme-toggle");
    const referenceInput = document.getElementById("reference-search");
    const optionList = document.getElementById("reference-options");
    const selectedReferenceValueEl = document.getElementById("selected-reference-value");
    const selectedReferenceChipEl = document.getElementById("selected-reference-chip");
    const tableFilter = document.getElementById("table-filter");
    const tableBody = document.getElementById("reservation-table-body");
    const emptyState = document.getElementById("reservation-empty");
    const productDetailBody = document.getElementById("product-detail-body");
    const productDetailEmpty = document.getElementById("product-detail-empty");
    const tabButtons = Array.from(document.querySelectorAll(".tab-button"));
    const sortButtons = Array.from(document.querySelectorAll("[data-sort]"));
    const reservationView = document.getElementById("reservation-view");
    const productView = document.getElementById("product-view");

    const summaryByReference = new Map((data.reference_summary || []).map((row) => [row.product_reference, row]));
    const detailsByReference = new Map();
    const productSummaryByReference = new Map((data.product_reference_summary || []).map((row) => [row.product_reference, row]));
    const productDetailsByReference = new Map();
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
      sortKey: "company_name",
      sortDirection: "asc",
      activeTab: "reservation",
    }};

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
      const selectedReference = state.selectedReference || "-";
      const summary = summaryByReference.get(state.selectedReference);
      const landingStatus = summary?.landing_status || "Unknown";
      selectedReferenceValueEl.textContent = selectedReference;
      selectedReferenceChipEl.innerHTML =
        "<span>Reference: <strong>" + escapeHtml(selectedReference) + "</strong></span>" +
        renderStatusChip(landingStatus);
      referenceInput.value = state.selectedReference || "";
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

    function renderTabs() {{
      const reservationActive = state.activeTab === "reservation";
      reservationView.hidden = !reservationActive;
      productView.hidden = reservationActive;
      for (const button of tabButtons) {{
        const isActive = button.dataset.tab === state.activeTab;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", isActive ? "true" : "false");
      }}
    }}

    function render() {{
      renderSelection();
      renderReservationKpis();
      renderReservationTable();
      renderProductKpis();
      renderProductTable();
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
      state.selectedReference = referenceInput.value.trim();
      render();
    }});
    referenceInput.addEventListener("input", () => {{
      if (!referenceInput.value.trim()) {{
        state.selectedReference = "";
        render();
      }}
    }});
    tableFilter.addEventListener("input", () => {{
      state.filterText = tableFilter.value;
      renderReservationTable();
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
        renderTabs();
      }});
    }}

    renderOptions();
    render();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
