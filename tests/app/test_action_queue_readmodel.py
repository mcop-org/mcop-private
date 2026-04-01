from __future__ import annotations

from app.readmodels.action_queue import build_action_queue_readmodel


def test_action_queue_readmodel_shapes_filters_and_chart_sections() -> None:
    payload = build_action_queue_readmodel(
        {
            "snapshot_date": "2026-03-03",
            "reservation_action_queue": {
                "summary": {"open_reservations": 2},
                "action_bucket_counts": [{"action_bucket": "Breached", "row_count": 1}],
                "open_bags_by_expiry_bucket": [{"expiry_bucket": "Breached", "open_bags": 4.0}],
                "details": [
                    {
                        "action_priority": "P2 Near Expiry",
                        "action_bucket": "Near Expiry",
                        "landing_status": "Incoming",
                        "data_status": "Complete",
                    },
                    {
                        "action_priority": "P1 Breached",
                        "action_bucket": "Breached",
                        "landing_status": "Landed",
                        "data_status": "Approval date unavailable",
                    },
                ],
            },
        }
    )

    assert payload["filters"]["action_buckets"] == ["Breached", "Near Expiry"]
    assert payload["filters"]["landing_statuses"] == ["Incoming", "Landed"]
    assert payload["filters"]["data_statuses"] == ["Approval date unavailable", "Complete"]
    assert payload["action_bucket_counts"] == [{"action_bucket": "Breached", "row_count": 1}]
    assert payload["open_bags_by_expiry_bucket"] == [{"expiry_bucket": "Breached", "open_bags": 4.0}]


def test_action_queue_readmodel_excludes_empty_filter_values() -> None:
    payload = build_action_queue_readmodel(
        {
            "snapshot_date": "2026-03-03",
            "reservation_action_queue": {
                "details": [
                    {
                        "action_bucket": "Near Expiry",
                        "landing_status": "Incoming",
                        "data_status": "Complete",
                    },
                    {
                        "action_bucket": "",
                        "landing_status": "",
                        "data_status": "",
                    },
                    {
                        "action_bucket": "Breached",
                        "landing_status": "Landed",
                        "data_status": "Approval date unavailable",
                    },
                ],
            },
        }
    )

    assert payload["filters"]["action_buckets"] == ["Breached", "Near Expiry"]
    assert payload["filters"]["landing_statuses"] == ["Incoming", "Landed"]
    assert payload["filters"]["data_statuses"] == ["Approval date unavailable", "Complete"]
