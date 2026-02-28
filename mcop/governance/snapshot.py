
import json
from pathlib import Path

def extract_snapshot(html_text: str):
    return {
        "has_trading_health": "Trading Health" in html_text,
        "has_top_payables": "Top 5 Payables" in html_text,
        "has_top_receivables": "Top 5 Receivables" in html_text,
        "summary_line_count": html_text.count("<li>")
    }

def compare_snapshots(old, new):
    issues = []

    for k in old:
        if old[k] != new.get(k):
            issues.append(f"{k} changed (was {old[k]}, now {new.get(k)})")

    return issues

def run_snapshot_check(out_dir: Path, html_path: Path):
    snapshot_path = out_dir / "report_snapshot.json"

    html_text = html_path.read_text(encoding="utf-8")
    new_snapshot = extract_snapshot(html_text)

    if snapshot_path.exists():
        old_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        issues = compare_snapshots(old_snapshot, new_snapshot)
    else:
        issues = []

    snapshot_path.write_text(json.dumps(new_snapshot, indent=2), encoding="utf-8")

    return issues
