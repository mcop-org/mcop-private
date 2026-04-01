from __future__ import annotations


def build_action_queue_readmodel(dataset: dict[str, object]) -> dict[str, object]:
    queue = dict(dataset.get("reservation_action_queue") or {})
    details = list(queue.get("details") or [])
    buckets = sorted(
        {
            str(row.get("action_bucket") or "").strip()
            for row in details
            if str(row.get("action_bucket") or "").strip()
        }
    )
    landing_statuses = sorted(
        {
            str(row.get("landing_status") or "").strip()
            for row in details
            if str(row.get("landing_status") or "").strip()
        }
    )
    data_statuses = sorted(
        {
            str(row.get("data_status") or "").strip()
            for row in details
            if str(row.get("data_status") or "").strip()
        }
    )
    return {
        "snapshot_date": str(dataset.get("snapshot_date") or ""),
        "summary": dict(queue.get("summary") or {}),
        "top_landed_references": dict(queue.get("top_landed_references") or {}),
        "action_bucket_counts": list(queue.get("action_bucket_counts") or []),
        "open_bags_by_expiry_bucket": list(queue.get("open_bags_by_expiry_bucket") or []),
        "details": details,
        "expired_draft_workflow": dict(queue.get("expired_draft_workflow") or {}),
        "filters": {
            "action_buckets": buckets,
            "landing_statuses": landing_statuses,
            "data_statuses": data_statuses,
        },
    }
