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
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MCOP Reference Workspace v1</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: rgba(255, 251, 245, 0.88);
      --panel-strong: #fffaf2;
      --ink: #1f2933;
      --muted: #5f6c76;
      --line: rgba(31, 41, 51, 0.12);
      --accent: #0f766e;
      --accent-soft: rgba(15, 118, 110, 0.12);
      --warn: #a16207;
      --shadow: 0 24px 70px rgba(43, 37, 28, 0.12);
      --radius: 22px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 34%),
        radial-gradient(circle at top right, rgba(161, 98, 7, 0.10), transparent 28%),
        linear-gradient(180deg, #fbf7f0 0%, var(--bg) 100%);
    }}
    .shell {{
      width: min(1200px, calc(100vw - 32px));
      margin: 24px auto 40px;
    }}
    .hero {{
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 30px;
      background: linear-gradient(135deg, rgba(255,255,255,0.82), rgba(255,248,238,0.96));
      box-shadow: var(--shadow);
    }}
    .eyebrow {{
      margin: 0 0 10px;
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    h1 {{
      margin: 0;
      font-size: clamp(32px, 4vw, 52px);
      line-height: 0.95;
      font-weight: 700;
    }}
    .hero-copy {{
      margin: 14px 0 0;
      max-width: 700px;
      color: var(--muted);
      font-size: 17px;
      line-height: 1.5;
    }}
    .toolbar {{
      display: grid;
      grid-template-columns: minmax(0, 1.75fr) minmax(220px, 0.55fr);
      gap: 16px;
      margin-top: 24px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel);
      backdrop-filter: blur(12px);
      box-shadow: var(--shadow);
    }}
    .control-panel {{
      padding: 20px;
    }}
    .control-label {{
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .control-input {{
      width: 100%;
      padding: 14px 16px;
      border-radius: 14px;
      border: 1px solid rgba(31, 41, 51, 0.18);
      background: rgba(255,255,255,0.92);
      color: var(--ink);
      font: inherit;
    }}
    .snapshot-card {{
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .snapshot-label {{
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .snapshot-date {{
      margin-top: 8px;
      font-size: 24px;
      font-weight: 700;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 16px;
      margin-top: 18px;
    }}
    .kpi {{
      padding: 18px;
      min-height: 132px;
    }}
    .kpi-label {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .kpi-value {{
      margin-top: 12px;
      font-size: clamp(28px, 3vw, 42px);
      line-height: 1;
      font-weight: 700;
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
    .note {{
      margin-top: 18px;
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid rgba(161, 98, 7, 0.22);
      background: rgba(161, 98, 7, 0.08);
      color: var(--warn);
      font-size: 14px;
      line-height: 1.45;
    }}
    .table-shell {{
      margin-top: 18px;
      overflow: hidden;
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
      font-size: 24px;
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
      background: rgba(255,255,255,0.58);
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    .sort-button {{
      border: 0;
      background: transparent;
      color: inherit;
      font: inherit;
      padding: 0;
      cursor: pointer;
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
    .empty {{
      padding: 28px 20px 36px;
      color: var(--muted);
      font-size: 15px;
    }}
    .selected-reference {{
      margin-top: 22px;
      font-size: 14px;
      color: var(--muted);
    }}
    @media (max-width: 1120px) {{
      .grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 980px) {{
      .toolbar, .grid {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 720px) {{
      .shell {{
        width: min(100vw - 16px, 1200px);
        margin-top: 8px;
      }}
      .hero {{
        padding: 18px;
        border-radius: 22px;
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
    <section class="hero">
      <p class="eyebrow">MCOP Reference Workspace v1</p>
      <h1>Reservation reference drill-down</h1>
      <p class="hero-copy">Standalone reference-level workspace for reservation analytics. Select a product reference to inspect reservation status, client attachment, and row-level reservation detail.</p>
      <div class="toolbar">
        <section class="panel control-panel">
          <label class="control-label" for="reference-search">Product reference selector</label>
          <input class="control-input" id="reference-search" list="reference-options" autocomplete="off" placeholder="Search or select a product reference">
          <datalist id="reference-options"></datalist>
          <div class="selected-reference" id="selected-reference">Reference: -</div>
        </section>
        <section class="panel snapshot-card">
          <div class="snapshot-label">Reservation Snapshot</div>
          <div class="snapshot-date">{snapshot_date}</div>
          <div class="muted">Based on the latest reservation activity included in this view.</div>
        </section>
      </div>
    </section>

    <section class="grid" aria-label="Reference KPIs">
      <article class="panel kpi">
        <div class="kpi-label">Reserved KG</div>
        <div class="kpi-value" id="kpi-kg">-</div>
        <div class="kpi-meta" id="kpi-bags">-</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Reserved Value</div>
        <div class="kpi-value" id="kpi-value">-</div>
        <div class="kpi-meta" id="kpi-rows">-</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Reserved %</div>
        <div class="kpi-value" id="kpi-reserved-pct">-</div>
        <div class="kpi-submeta" id="kpi-available-bags">-</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Clients</div>
        <div class="kpi-value" id="kpi-clients">-</div>
        <div class="kpi-meta">Distinct clients attached to the selected reservation reference.</div>
      </article>
      <article class="panel kpi">
        <div class="kpi-label">Landing Status</div>
        <div class="kpi-value" id="kpi-landing-status">-</div>
        <div class="kpi-meta" id="kpi-landing-meta">-</div>
      </article>
    </section>

    <section class="note panel" id="reservation-note"></section>

    <section class="panel table-shell">
      <div class="table-topbar">
        <div>
          <h2 class="table-title">Reservation detail</h2>
          <p class="table-subtitle">Latest non-rejected reservation row per reservation key, filtered to the selected product reference.</p>
        </div>
        <div class="table-filter">
          <label class="control-label" for="table-filter">Row filter</label>
          <input class="control-input" id="table-filter" type="search" autocomplete="off" placeholder="Filter by client, status, warehouse, or reservation id">
        </div>
      </div>
      <div style="overflow:auto;">
        <table>
          <thead>
            <tr>
              <th><button class="sort-button" data-sort="company_name" type="button">Client</button></th>
              <th><button class="sort-button" data-sort="request_status" type="button">Reservation Status</button></th>
              <th><button class="sort-button" data-sort="effective_bags" type="button">Reserved Bags</button></th>
              <th><button class="sort-button" data-sort="reserved_kg" type="button">Reserved KG</button></th>
              <th><button class="sort-button" data-sort="reserved_value_gbp" type="button">Reserved Value</button></th>
              <th><button class="sort-button" data-sort="landing_status" type="button">Landing Status</button></th>
              <th><button class="sort-button" data-sort="landing_date" type="button">Landing Date</button></th>
              <th><button class="sort-button" data-sort="warehouse" type="button">Warehouse</button></th>
              <th><button class="sort-button" data-sort="reservation_key" type="button">Reservation Key</button></th>
            </tr>
          </thead>
          <tbody id="reservation-table-body"></tbody>
        </table>
      </div>
      <div class="empty" id="reservation-empty" hidden>No reservation rows match the current reference and filter.</div>
    </section>
  </main>

  <script id="workspace-data" type="application/json">{payload_json}</script>
  <script>
    const data = JSON.parse(document.getElementById("workspace-data").textContent);
    const referenceInput = document.getElementById("reference-search");
    const optionList = document.getElementById("reference-options");
    const noteEl = document.getElementById("reservation-note");
    const selectedReferenceEl = document.getElementById("selected-reference");
    const tableFilter = document.getElementById("table-filter");
    const tableBody = document.getElementById("reservation-table-body");
    const emptyState = document.getElementById("reservation-empty");
    const sortButtons = Array.from(document.querySelectorAll("[data-sort]"));

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

    function buildLandingMeta(summary) {{
      const status = summary?.landing_status || "Unknown";
      const landingDate = summary?.landing_date || "";
      if (!landingDate) {{
        return status === "Unknown" ? "Landing date not available." : "Landing date not available for this reference.";
      }}
      if (landingDate === "multiple") {{
        return "Landing dates vary across this reference.";
      }}

      const formattedDate = formatLongDate(landingDate);
      if (!formattedDate) {{
        return "Landing date available but not in a displayable format.";
      }}

      const diff = dayDiff(data.snapshot_date, landingDate);
      if (status === "Incoming") {{
        if (diff === null) {{
          return "Expected to land on " + formattedDate + ".";
        }}
        if (diff > 0) {{
          return "Expected to land on " + formattedDate + ", in " + formatNumber(diff, 0) + " days.";
        }}
        if (diff === 0) {{
          return "Expected to land today, " + formattedDate + ".";
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
        const reservationState = row.has_reservations ? "reservations" : "no reservations";
        const label = row.product_reference + " - " + landingStatus + " - " + reservationState;
        return '<option value="' + escapeHtml(row.product_reference) + '" label="' + escapeHtml(label) + '"></option>';
      }});
      optionList.innerHTML = options.join("");
    }}

    function renderKpis() {{
      const summary = summaryByReference.get(state.selectedReference);
      const kg = document.getElementById("kpi-kg");
      const bags = document.getElementById("kpi-bags");
      const value = document.getElementById("kpi-value");
      const rows = document.getElementById("kpi-rows");
      const reservedPct = document.getElementById("kpi-reserved-pct");
      const availableBags = document.getElementById("kpi-available-bags");
      const clients = document.getElementById("kpi-clients");
      const landingStatus = document.getElementById("kpi-landing-status");
      const landingMeta = document.getElementById("kpi-landing-meta");

      if (!summary) {{
        kg.textContent = "0 kg";
        bags.textContent = "0 reserved bags";
        value.textContent = "GBP 0";
        rows.textContent = "0 reservation rows";
        reservedPct.textContent = "0%";
        availableBags.textContent = "0 bags still available";
        clients.textContent = "0";
        landingStatus.textContent = "Unknown";
        landingMeta.textContent = "Landing date not available.";
        return;
      }}

      kg.textContent = formatKilos(summary.reserved_kg);
      bags.textContent = formatNumber(summary.reserved_bags, 0) + " reserved bags";
      value.textContent = formatMoney(summary.reserved_value_gbp);
      rows.textContent = formatNumber(summary.reservation_row_count, 0) + " reservation rows";
      reservedPct.textContent = formatPercent(summary.reserved_pct);
      availableBags.textContent = formatNumber(summary.bags_available, 0) + " bags still available";
      clients.textContent = formatNumber(summary.client_count, 0);
      landingStatus.textContent = summary.landing_status || "Unknown";
      landingMeta.textContent = buildLandingMeta(summary);
    }}

    function renderTable() {{
      const rows = currentDetails();
      emptyState.hidden = rows.length > 0;
      tableBody.innerHTML = rows.map((row) => {{
        return "<tr>" +
          "<td><strong>" + escapeHtml(row.company_name || "-") + "</strong></td>" +
          "<td><span class='pill'>" + escapeHtml(row.request_status || "-") + "</span></td>" +
          "<td>" + escapeHtml(formatNumber(row.effective_bags, 0)) + "</td>" +
          "<td>" + escapeHtml(formatKilos(row.reserved_kg)) + "</td>" +
          "<td>" + escapeHtml(formatMoney(row.reserved_value_gbp)) + "</td>" +
          "<td>" + escapeHtml(row.landing_status || "-") + "</td>" +
          "<td>" + escapeHtml(row.landing_date || "-") + "</td>" +
          "<td>" + escapeHtml(row.warehouse || "-") + "</td>" +
          "<td><span class='muted'>" + escapeHtml(row.reservation_key || row.id_request || "-") + "</span></td>" +
        "</tr>";
      }}).join("");
    }}

    function renderSelectionLabel() {{
      selectedReferenceEl.textContent = "Reference: " + (state.selectedReference || "-");
      referenceInput.value = state.selectedReference || "";
    }}

    function render() {{
      renderSelectionLabel();
      renderKpis();
      renderTable();
      noteEl.textContent = (data.notes && data.notes[0]) || "";
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

    renderOptions();
    render();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
