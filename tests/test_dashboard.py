from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.dashboard import render_dashboard_html


def test_dashboard_renders_six_panels_from_jsonl(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    timestamp = (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    records = [
        {"ts": timestamp, "event": "request_received"},
        {
            "ts": timestamp,
            "event": "response_sent",
            "latency_ms": 250,
            "ttft_ms": 50,
            "tokens_in": 30,
            "tokens_out": 60,
            "cost_usd": 0.001,
            "quality_score": 0.8,
            "tool_success": True,
        },
    ]
    log_path = tmp_path / "logs.jsonl"
    log_path.write_text("\n".join(json.dumps(row) for row in records), encoding="utf-8")

    page = render_dashboard_html(log_path=log_path, now=now)

    assert page.count('<section class="panel"') == 6
    assert "250 ms P95" in page
    assert "TTFT P95 50 ms" in page
    assert "Retrieval success 100.0%" in page
    assert "last 60 minutes" in page
