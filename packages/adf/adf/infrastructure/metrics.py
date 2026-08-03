"""Prometheus metrics."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "adf_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

agent_runs_total = Counter(
    "adf_agent_runs_total",
    "Total agent runs",
    ["agent_type", "provider", "state"],
)

webhook_events_total = Counter(
    "adf_webhook_events_total",
    "Total GitHub webhook deliveries",
    ["event_type", "result"],
)

request_latency_seconds = Histogram(
    "adf_request_latency_seconds",
    "Request latency",
    ["path"],
)
