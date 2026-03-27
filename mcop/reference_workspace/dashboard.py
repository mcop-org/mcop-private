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
      --good: #2f7a63;
      --good-soft: rgba(47, 122, 99, 0.12);
      --warn: #a96a3e;
      --warn-soft: rgba(169, 106, 62, 0.14);
      --neutral: #6b7280;
      --neutral-soft: rgba(107, 114, 128, 0.14);
      --sans: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      --mono: "SFMono-Regular", "Menlo", monospace;
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
      --good: #73d0a7;
      --good-soft: rgba(115, 208, 167, 0.14);
      --warn: #f2b27e;
      --warn-soft: rgba(242, 178, 126, 0.16);
      --neutral: #b2becd;
      --neutral-soft: rgba(178, 190, 205, 0.14);
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
    .toolbar-chip, .theme-toggle {{
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
    .theme-toggle {{
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, background-color 120ms ease;
    }}
    .theme-toggle:hover, .theme-toggle:focus-visible {{
      transform: translateY(-1px);
      border-color: color-mix(in srgb, var(--accent) 30%, var(--line));
      outline: none;
    }}
    .hero {{
      margin-top: 18px;
      padding: 28px;
      background:
        linear-gradient(145deg, color-mix(in srgb, var(--accent-soft) 65%, transparent), transparent 44%),
        linear-gradient(180deg, color-mix(in srgb, var(--panel-strong) 90%, transparent), var(--panel));
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 0;
    }}
    .hero-main {{
      min-width: 0;
    }}
    .hero-main h1 {{
      margin: 0;
      font-size: clamp(34px, 4.6vw, 54px);
      line-height: 0.95;
      letter-spacing: -0.05em;
    }}
    .control-grid {{
      margin-top: 18px;
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
    .control-input::placeholder {{
      color: color-mix(in srgb, var(--muted) 84%, transparent);
    }}
    .control-input:hover {{
      border-color: var(--line-strong);
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
      min-height: 32px;
    }}
    .selected-reference-value {{
      margin: 0;
      font-size: 20px;
      line-height: 1;
      letter-spacing: -0.03em;
    }}
    .kpi-grid {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 16px;
    }}
    .kpi {{
      min-height: 152px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      background:
        linear-gradient(180deg, color-mix(in srgb, var(--panel-strong) 86%, transparent), var(--panel));
    }}
    .kpi.is-accent {{
      background:
        linear-gradient(180deg, color-mix(in srgb, var(--accent-soft) 70%, transparent), transparent 34%),
        linear-gradient(180deg, color-mix(in srgb, var(--panel-strong) 86%, transparent), var(--panel));
    }}
    .kpi-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .kpi-value {{
      font-size: clamp(28px, 3.1vw, 42px);
      line-height: 0.95;
      letter-spacing: -0.04em;
      font-weight: 700;
    }}
    .kpi-meta {{
      color: var(--label);
      font-size: 14px;
      line-height: 1.35;
    }}
    .status-cluster {{
      margin-top: auto;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 32px;
      padding: 7px 12px;
      border-radius: 999px;
      border: 1px solid transparent;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.03em;
      white-space: nowrap;
    }}
    .chip::before {{
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
      opacity: 0.85;
    }}
    .chip.is-landed, .chip.is-completed, .chip.is-approved, .chip.is-available {{
      color: var(--good);
      background: var(--good-soft);
      border-color: color-mix(in srgb, var(--good) 18%, var(--line));
    }}
    .chip.is-incoming, .chip.is-created, .chip.is-pending {{
      color: var(--warn);
      background: var(--warn-soft);
      border-color: color-mix(in srgb, var(--warn) 18%, var(--line));
    }}
    .chip.is-unknown, .chip.is-neutral, .chip.is-rejected {{
      color: var(--neutral);
      background: var(--neutral-soft);
      border-color: color-mix(in srgb, var(--neutral) 18%, var(--line));
    }}
    .table-shell {{
      margin-top: 18px;
      overflow: hidden;
    }}
    .table-topbar {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 360px);
      gap: 16px;
      align-items: end;
      padding: 22px 22px 16px;
      border-bottom: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel-strong) 72%, transparent);
    }}
    .table-title {{
      margin: 0;
      font-size: 24px;
      line-height: 1.05;
      letter-spacing: -0.03em;
    }}
    .table-subtitle {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }}
    .table-wrap {{
      overflow: auto;
      padding: 6px 10px 12px;
    }}
    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      min-width: 1060px;
    }}
    thead th {{
      position: sticky;
      top: 0;
      z-index: 1;
      padding: 11px 12px 12px;
      text-align: left;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      background: color-mix(in srgb, var(--panel-strong) 94%, transparent);
      border-bottom: 1px solid var(--line);
    }}
    thead th.num {{
      text-align: right;
    }}
    tbody td {{
      padding: 13px 12px;
      border-bottom: 1px solid var(--line);
      vertical-align: middle;
      font-size: 14px;
      color: var(--label);
    }}
    tbody tr:nth-child(odd) td {{
      background: color-mix(in srgb, var(--panel-strong) 62%, transparent);
    }}
    tbody tr:hover td {{
      background: color-mix(in srgb, var(--accent-soft) 24%, var(--panel-strong));
    }}
    td.num {{
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: var(--ink);
    }}
    td.date {{
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: var(--ink);
      white-space: nowrap;
    }}
    .sort-button {{
      border: 0;
      padding: 0;
      background: transparent;
      color: inherit;
      font: inherit;
      text-transform: inherit;
      letter-spacing: inherit;
      cursor: pointer;
    }}
    .sort-button:hover, .sort-button:focus-visible {{
      color: var(--label);
      outline: none;
    }}
    .table-company {{
      display: block;
    }}
    .table-company strong {{
      color: var(--ink);
      font-size: 14px;
    }}
    .mono {{
      font-family: var(--mono);
      font-size: 12px;
    }}
    .empty {{
      margin: 14px;
      padding: 28px;
      border-radius: 22px;
      border: 1px dashed var(--line-strong);
      background: color-mix(in srgb, var(--panel-strong) 78%, transparent);
      color: var(--muted);
      font-size: 15px;
      line-height: 1.55;
      text-align: center;
    }}
    @media (max-width: 1200px) {{
      .kpi-grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 980px) {{
      .shell {{
        width: min(100vw - 18px, 1340px);
        margin-top: 10px;
      }}
      .topbar, .hero-grid, .control-grid, .table-topbar {{
        grid-template-columns: 1fr;
      }}
      .topbar {{
        display: grid;
      }}
      .topbar-actions {{
        justify-content: flex-start;
      }}
      .kpi-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 640px) {{
      .hero {{
        padding: 18px;
      }}
      .control-panel, .kpi, .table-topbar {{
        padding: 16px;
      }}
      .kpi-grid {{
        grid-template-columns: 1fr;
      }}
      .selected-reference-inline {{
        align-items: flex-start;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="topbar-copy">
        <h2 class="topbar-title">Reference Workspace</h2>
      </div>
      <div class="topbar-actions">
        <div class="toolbar-chip">Snapshot: <strong>{snapshot_date}</strong></div>
        <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Toggle light and dark mode">Dark mode</button>
      </div>
    </header>

    <section class="hero panel">
      <div class="hero-grid">
        <div class="hero-main">
          <h1>Reservation detail</h1>
        </div>
      </div>

      <div class="control-grid">
        <section class="panel control-panel">
          <div class="control-head">
            <h3 class="control-title">Reference selector</h3>
            <div class="selected-reference-inline">
              <h4 class="selected-reference-value" id="selected-reference-value">-</h4>
              <div id="selected-reference-chip"></div>
            </div>
          </div>
          <div>
            <label class="control-label" for="reference-search">Product reference</label>
            <input class="control-input" id="reference-search" list="reference-options" autocomplete="off" placeholder="Search or select a product reference">
            <datalist id="reference-options"></datalist>
          </div>
        </section>
      </div>
    </section>

    <section class="kpi-grid" aria-label="Reference KPIs">
      <article class="panel kpi is-accent">
        <div class="kpi-label">Reserved KG</div>
        <div class="kpi-value" id="kpi-kg">-</div>
        <div class="kpi-meta" id="kpi-bags">-</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Reserved Value</div>
        <div class="kpi-value" id="kpi-value">-</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Reserved %</div>
        <div class="kpi-value" id="kpi-reserved-pct">-</div>
        <div class="kpi-meta" id="kpi-available-bags">-</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Clients</div>
        <div class="kpi-value" id="kpi-clients">-</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Landing Status</div>
        <div class="kpi-value" id="kpi-landing-status">-</div>
        <div class="kpi-meta" id="kpi-landing-meta">-</div>
        <div class="status-cluster" id="kpi-landing-chips"></div>
      </article>
    </section>

    <section class="panel table-shell">
      <div class="table-topbar">
        <div>
          <h2 class="table-title">Reservation detail</h2>
        </div>
        <div>
          <label class="control-label" for="table-filter">Search reservation rows</label>
          <input class="control-input" id="table-filter" type="search" autocomplete="off" placeholder="Filter by company, status, warehouse, or reservation key">
        </div>
      </div>
      <div class="table-wrap">
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
  </main>

  <script id="workspace-data" type="application/json">{payload_json}</script>
  <script>
    const data = JSON.parse(document.getElementById("workspace-data").textContent);
    const root = document.documentElement;
    const referenceInput = document.getElementById("reference-search");
    const optionList = document.getElementById("reference-options");
    const selectedReferenceValueEl = document.getElementById("selected-reference-value");
    const selectedReferenceChipEl = document.getElementById("selected-reference-chip");
    const tableFilter = document.getElementById("table-filter");
    const tableBody = document.getElementById("reservation-table-body");
    const emptyState = document.getElementById("reservation-empty");
    const sortButtons = Array.from(document.querySelectorAll("[data-sort]"));
    const themeToggle = document.getElementById("theme-toggle");

    const summaryByReference = new Map((data.reference_summary || []).map((row) => [row.product_reference, row]));
    const detailsByReference = new Map();
    for (const row of data.reservation_details || []) {{
      const key = row.product_reference || "";
      if (!detailsByReference.has(key)) {{
        detailsByReference.set(key, []);
      }}
      detailsByReference.get(key).push(row);
    }}

    let state = {{
      selectedReference: data.default_reference || "",
      filterText: "",
      sortKey: "company_name",
      sortDirection: "asc",
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
      return Number.isFinite(number) ? number.toLocaleString("en-GB", {{
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }}) : "-";
    }}

    function formatMoney(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number) ? "GBP " + number.toLocaleString("en-GB", {{
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }}) : "GBP -";
    }}

    function formatPercent(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number) ? (number * 100).toLocaleString("en-GB", {{
        minimumFractionDigits: 0,
        maximumFractionDigits: 1,
      }}) + "%" : "-";
    }}

    function formatKilos(value) {{
      const number = Number(value || 0);
      return Number.isFinite(number) ? number.toLocaleString("en-GB", {{
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }}) + " kg" : "- kg";
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

    function compareValues(left, right) {{
      const leftNumber = Number(left);
      const rightNumber = Number(right);
      if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {{
        return leftNumber - rightNumber;
      }}
      return String(left ?? "").localeCompare(String(right ?? ""), "en", {{ sensitivity: "base" }});
    }}

    function parseIsoDate(value) {{
      if (!/^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(String(value || ""))) {{
        return null;
      }}
      const parsed = new Date(String(value) + "T00:00:00Z");
      return Number.isNaN(parsed.getTime()) ? null : parsed;
    }}

    function formatLongDate(value) {{
      const parsed = parseIsoDate(value);
      if (!parsed) {{
        return "";
      }}
      return parsed.toLocaleDateString("en-GB", {{
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }});
    }}

    function dayDiff(fromValue, toValue) {{
      const fromDate = parseIsoDate(fromValue);
      const toDate = parseIsoDate(toValue);
      if (!fromDate || !toDate) {{
        return null;
      }}
      const msPerDay = 24 * 60 * 60 * 1000;
      return Math.round((toDate.getTime() - fromDate.getTime()) / msPerDay);
    }}

    function statusTone(value) {{
      const normalized = String(value || "").trim().toLowerCase();
      if (["landed", "completed", "approved", "available"].includes(normalized)) {{
        return "is-landed";
      }}
      if (["incoming", "created", "pending"].includes(normalized)) {{
        return "is-incoming";
      }}
      if (["unknown", "rejected", ""].includes(normalized)) {{
        return "is-unknown";
      }}
      return "is-neutral";
    }}

    function titleCaseWords(value) {{
      return String(value || "")
        .trim()
        .split(/\\s+/)
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
        .join(" ");
    }}

    function renderChip(value, labelPrefix = "") {{
      const text = titleCaseWords(value) || "Unknown";
      const prefix = labelPrefix ? escapeHtml(labelPrefix) + ": " : "";
      return '<span class="chip ' + statusTone(text) + '">' + prefix + escapeHtml(text) + '</span>';
    }}

    function buildLandingMeta(summary) {{
      const status = summary?.landing_status || "Unknown";
      const landingDate = summary?.landing_date || "";
      if (!landingDate) {{
        return status === "Unknown" ? "Landing date not available." : "Landing date not available for this reference.";
      }}
      if (landingDate === "multiple") {{
        return "Landing timing varies across this reference.";
      }}

      const formattedDate = formatLongDate(landingDate);
      if (!formattedDate) {{
        return "Landing date is present but not in a displayable format.";
      }}

      const diff = dayDiff(data.snapshot_date, landingDate);
      if (status === "Incoming") {{
        if (diff === null) {{
          return "Expected to land on " + formattedDate + ".";
        }}
        if (diff > 0) {{
          return "Expected on " + formattedDate + ", in " + formatNumber(diff, 0) + " days.";
        }}
        if (diff === 0) {{
          return "Expected today, " + formattedDate + ".";
        }}
        return "Expected landing date was " + formattedDate + ".";
      }}
      if (status === "Landed") {{
        if (diff === null) {{
          return "Landed on " + formattedDate + ".";
        }}
        if (diff > 0) {{
          return "Landed on " + formattedDate + ", " + formatNumber(diff, 0) + " days ago.";
        }}
        if (diff === 0) {{
          return "Landed today, " + formattedDate + ".";
        }}
        return "Recorded as landed on " + formattedDate + ".";
      }}
      return "Landing date " + formattedDate + ".";
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

    function renderSelectedReference(summary) {{
      selectedReferenceValueEl.textContent = state.selectedReference || "-";
      referenceInput.value = state.selectedReference || "";
      selectedReferenceChipEl.innerHTML = renderChip(summary?.landing_status || "Unknown");
    }}

    function renderKpis() {{
      const summary = summaryByReference.get(state.selectedReference);
      const kg = document.getElementById("kpi-kg");
      const bags = document.getElementById("kpi-bags");
      const value = document.getElementById("kpi-value");
      const reservedPct = document.getElementById("kpi-reserved-pct");
      const availableBags = document.getElementById("kpi-available-bags");
      const clients = document.getElementById("kpi-clients");
      const landingStatus = document.getElementById("kpi-landing-status");
      const landingMeta = document.getElementById("kpi-landing-meta");
      const landingChips = document.getElementById("kpi-landing-chips");

      if (!summary) {{
        kg.textContent = "0 kg";
        bags.textContent = "0 reserved bags";
        value.textContent = "GBP 0";
        reservedPct.textContent = "0%";
        availableBags.textContent = "0 available bags";
        clients.textContent = "0";
        landingStatus.textContent = "Unknown";
        landingMeta.textContent = "Landing date not available.";
        landingChips.innerHTML = renderChip("Unknown");
        renderSelectedReference(null);
        return;
      }}

      kg.textContent = formatKilos(summary.reserved_kg);
      bags.textContent = formatNumber(summary.reserved_bags, 0) + " reserved bags";
      value.textContent = formatMoney(summary.reserved_value_gbp);
      reservedPct.textContent = formatPercent(summary.reserved_pct);
      availableBags.textContent = formatNumber(summary.bags_available, 0) + " available bags";
      clients.textContent = formatNumber(summary.client_count, 0);
      landingStatus.textContent = titleCaseWords(summary.landing_status || "Unknown") || "Unknown";
      landingMeta.textContent = buildLandingMeta(summary);
      landingChips.innerHTML = renderChip(summary.landing_status || "Unknown");
      renderSelectedReference(summary);
    }}

    function renderTable() {{
      const rows = currentDetails();
      emptyState.hidden = rows.length > 0;
      tableBody.innerHTML = rows.map((row) => {{
        const reservationKey = formatReservationKey(row.reservation_key || row.id_request || "-");
        const landingDate = formatLongDate(row.landing_date) || row.landing_date || "-";
        return "<tr>" +
          "<td><div class='table-company'><strong>" + escapeHtml(row.company_name || "-") + "</strong></div></td>" +
          "<td>" + renderChip(row.request_status || "Unknown") + "</td>" +
          "<td class='num'>" + escapeHtml(formatNumber(row.effective_bags, 0)) + "</td>" +
          "<td class='num'>" + escapeHtml(formatKilos(row.reserved_kg)) + "</td>" +
          "<td class='num'>" + escapeHtml(formatMoney(row.reserved_value_gbp)) + "</td>" +
          "<td>" + renderChip(row.landing_status || "Unknown") + "</td>" +
          "<td class='date'>" + escapeHtml(landingDate) + "</td>" +
          "<td>" + escapeHtml(row.warehouse || "-") + "</td>" +
          "<td><span class='mono'>" + escapeHtml(reservationKey) + "</span></td>" +
        "</tr>";
      }}).join("");
    }}

    function render() {{
      renderKpis();
      renderTable();
    }}

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
      renderTable();
    }});
    for (const button of sortButtons) {{
      button.addEventListener("click", () => {{
        const key = button.dataset.sort;
        if (state.sortKey === key) {{
          state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
        }} else {{
          state.sortKey = key;
          state.sortDirection = "asc";
        }}
        renderTable();
      }});
    }}

    (function syncTheme() {{
      try {{
        const storedTheme = localStorage.getItem("mcop-reference-workspace-theme");
        if (storedTheme === "dark" || storedTheme === "light") {{
          root.setAttribute("data-theme", storedTheme);
        }}
      }} catch (error) {{
      }}

      function syncThemeLabel() {{
        themeToggle.textContent = root.getAttribute("data-theme") === "dark" ? "Light mode" : "Dark mode";
      }}

      themeToggle.addEventListener("click", () => {{
        const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", next);
        try {{
          localStorage.setItem("mcop-reference-workspace-theme", next);
        }} catch (error) {{
        }}
        syncThemeLabel();
      }});

      syncThemeLabel();
    }})();

    renderOptions();
    render();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
