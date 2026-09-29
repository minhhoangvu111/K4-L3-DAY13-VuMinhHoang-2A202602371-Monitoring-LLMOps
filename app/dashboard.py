from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
WINDOW_MINUTES = 60
WIDTH = 600
HEIGHT = 110


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile / 100
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _read_records(path: Path, now: datetime) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        except (ValueError, KeyError, TypeError):
            continue
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if cutoff <= timestamp <= now:
            record["_timestamp"] = timestamp.astimezone(timezone.utc)
            records.append(record)
    return records


def _chart(values: list[float], threshold: float, operator: str) -> str:
    if not values:
        values = [0.0] * WINDOW_MINUTES
    low = min(0.0, min(values))
    high = max(max(values), threshold, 1.0)
    padding = 10
    inner_height = HEIGHT - padding * 2
    points = []
    for index, value in enumerate(values):
        x = index * WIDTH / max(len(values) - 1, 1)
        y = HEIGHT - padding - ((value - low) / (high - low or 1)) * inner_height
        points.append(f"{x:.1f},{y:.1f}")
    threshold_y = HEIGHT - padding - ((threshold - low) / (high - low or 1)) * inner_height
    threshold_line = (
        f'<line x1="0" y1="{threshold_y:.1f}" x2="{WIDTH}" y2="{threshold_y:.1f}" '
        'stroke="#c0841a" stroke-dasharray="6 5" stroke-width="2" />'
    )
    return (
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Metric over the last 60 minutes">'
        '<path d="M0 100 H600" stroke="#e2e8f0" stroke-width="1" />'
        f'{threshold_line}<polyline points="{" ".join(points)}" fill="none" '
        'stroke="#2563eb" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" />'
        '</svg>'
    )


def render_dashboard_html(
    log_path: Path = LOG_PATH,
    config_path: Path = CONFIG_PATH,
    now: datetime | None = None,
) -> str:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    dashboard = config["dashboard"]
    records = _read_records(log_path, now)
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    retrievals = [r for r in records if r.get("tool_success") is not None]
    retrieval_success = sum(r.get("tool_success") is True for r in retrievals)
    retrieval_rate = retrieval_success / len(retrievals) * 100 if retrievals else 0.0
    error_rate = len(failures) / len(requests) * 100 if requests else 0.0
    latency = [float(r.get("latency_ms", 0)) for r in responses]
    ttft = [float(r.get("ttft_ms", 0)) for r in responses]
    tokens_in = sum(int(r.get("tokens_in", 0)) for r in responses)
    tokens_out = sum(int(r.get("tokens_out", 0)) for r in responses)
    total_cost = sum(float(r.get("cost_usd", 0)) for r in responses)
    quality = [float(r.get("quality_score", 0)) for r in responses]

    buckets: list[list[dict[str, Any]]] = [[] for _ in range(WINDOW_MINUTES)]
    cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    for record in records:
        index = int((record["_timestamp"] - cutoff).total_seconds() // 60)
        if 0 <= index < WINDOW_MINUTES:
            buckets[index].append(record)

    def panel_series(panel_id: str) -> list[float]:
        result: list[float] = []
        for bucket in buckets:
            bucket_responses = [r for r in bucket if r.get("event") == "response_sent"]
            bucket_requests = [r for r in bucket if r.get("event") == "request_received"]
            bucket_failures = [r for r in bucket if r.get("event") == "request_failed"]
            bucket_retrievals = [r for r in bucket if r.get("tool_success") is not None]
            if panel_id == "latency":
                result.append(_percentile([float(r.get("latency_ms", 0)) for r in bucket_responses], 95))
            elif panel_id == "traffic":
                result.append(float(len(bucket_requests)))
            elif panel_id == "errors":
                result.append(len(bucket_failures) / len(bucket_requests) * 100 if bucket_requests else 0)
            elif panel_id == "cost":
                result.append(sum(float(r.get("cost_usd", 0)) for r in bucket_responses))
            elif panel_id == "tokens":
                result.append(float(sum(int(r.get("tokens_in", 0)) + int(r.get("tokens_out", 0)) for r in bucket_responses)))
            else:
                values = [float(r.get("quality_score", 0)) for r in bucket_responses]
                result.append(mean(values) if values else 0.0)
        return result

    kpis = {
        "latency": (
            f"{_percentile(latency, 95):.0f} ms P95",
            f"P50 {_percentile(latency, 50):.0f} ms · P99 {_percentile(latency, 99):.0f} ms · TTFT P95 {_percentile(ttft, 95):.0f} ms",
        ),
        "traffic": (f"{len(requests)} requests", f"{len(requests) / WINDOW_MINUTES:.2f} requests/min average"),
        "errors": (f"{error_rate:.2f}% errors", f"Retrieval success {retrieval_rate:.1f}% · {len(failures)} failed / {len(requests)} requests"),
        "cost": (f"${total_cost:.4f}", "Total estimated cost in the selected window"),
        "tokens": (f"{tokens_in:,} in / {tokens_out:,} out", f"{tokens_in + tokens_out:,} total tokens"),
        "quality": (f"{mean(quality) if quality else 0.0:.2f} / 1.00", f"Mean quality proxy across {len(quality)} responses"),
    }

    panels = []
    for panel in dashboard["panels"]:
        panel_id = panel["id"]
        threshold = panel["threshold"]
        kpi, detail = kpis[panel_id]
        panel_threshold = float(threshold["value"])
        panels.append(
            f'<section class="panel" id="panel-{html.escape(panel_id)}">'
            f'<div class="panel-heading"><h2>{html.escape(panel["title"])}</h2>'
            f'<span class="unit">{html.escape(panel["unit"])}</span></div>'
            f'<div class="kpi">{html.escape(kpi)}</div><p>{html.escape(detail)}</p>'
            f'{_chart(panel_series(panel_id), panel_threshold, threshold["operator"])}'
            f'<div class="threshold">Threshold: {threshold["operator"]} {panel_threshold:g} {html.escape(panel["unit"])}</div>'
            '</section>'
        )

    updated = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(dashboard["title"])}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f1f5f9;color:#172033;font:15px/1.45 Segoe UI,Arial,sans-serif}}
main{{max-width:1440px;margin:auto;padding:28px}}header{{display:flex;justify-content:space-between;align-items:end;gap:16px;margin-bottom:22px}}
h1{{font-size:25px;margin:0}}header p{{margin:5px 0 0;color:#64748b}}.updated{{color:#64748b;font-size:13px;text-align:right}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.panel{{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;box-shadow:0 2px 7px #0f172a0a}}
.panel-heading{{display:flex;justify-content:space-between;gap:10px;align-items:start}}h2{{font-size:16px;margin:0}}.unit{{color:#64748b;font-size:12px}}.kpi{{font-weight:700;font-size:25px;margin-top:14px}}.panel p{{color:#64748b;margin:4px 0 9px;min-height:22px;font-size:13px}}
svg{{width:100%;height:100px;overflow:visible}}.threshold{{font-size:12px;color:#8a5a00}}footer{{font-size:12px;color:#64748b;margin-top:18px}}
@media(max-width:760px){{main{{padding:16px}}header{{display:block}}.updated{{text-align:left;margin-top:10px}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><header><div><h1>{html.escape(dashboard["title"])}</h1>
<p>Live view from data/logs.jsonl · last {WINDOW_MINUTES} minutes · auto refresh {dashboard["refresh_seconds"]}s</p></div>
<div class="updated">Updated {updated}<br>Threshold lines shown in amber</div></header>
<div class="grid">{"".join(panels)}</div><footer>Metrics help identify the symptom; use correlation_id to continue from logs to the matching Langfuse trace.</footer>
</main></body></html>'''
