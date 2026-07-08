#!/usr/bin/env python3
"""
agent/flakiness_tracker.py — Redis-backed flakiness tracking

Records the last N results per test (pass/fail) in Redis and computes a
flakiness percentage: how often a test's outcome flips between consecutive
runs. This is the metric spec section 9 calls for ("Taux de flakiness par
test") and doubles as the "intermediate store" from section 7.3 — results
land here first, then get read by reporting_service.py before the Power BI
push.
"""

import os
import json
import logging
from datetime import datetime, timezone

import redis

logger = logging.getLogger("smoky.flakiness")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
HISTORY_SIZE = int(os.environ.get("FLAKINESS_HISTORY_SIZE", "20"))

_client = None


def get_client() -> "redis.Redis":
    """Lazily creates a single shared Redis connection."""
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def _key(test_name: str) -> str:
    return f"smoky:test-history:{test_name}"


def record_result(test_name: str, passed: bool, duration_ms: int = 0, run_id: str = "") -> None:
    """Appends a pass/fail result to the test's rolling history (capped at HISTORY_SIZE)."""
    client = get_client()
    entry = json.dumps(
        {
            "passed": passed,
            "duration_ms": duration_ms,
            "run_id": run_id,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    key = _key(test_name)
    client.lpush(key, entry)
    client.ltrim(key, 0, HISTORY_SIZE - 1)


def get_history(test_name: str) -> list[dict]:
    client = get_client()
    raw = client.lrange(_key(test_name), 0, -1)
    return [json.loads(r) for r in raw]


def get_flakiness(test_name: str) -> float:
    """
    Flakiness % = proportion of consecutive-run pairs where the outcome
    flipped (pass<->fail), out of the available history. A test that always
    passes or always fails scores 0% — flakiness measures *inconsistency*,
    not failure rate.
    """
    history = get_history(test_name)
    if len(history) < 2:
        return 0.0

    flips = sum(
        1 for i in range(len(history) - 1) if history[i]["passed"] != history[i + 1]["passed"]
    )
    return round(100 * flips / (len(history) - 1), 1)


def get_all_tracked_tests() -> list[str]:
    client = get_client()
    keys = client.keys("smoky:test-history:*")
    prefix = "smoky:test-history:"
    return [k[len(prefix):] for k in keys]


def get_flakiness_report() -> dict:
    """Returns {test_name: flakiness_pct} for every tracked test — the input
    to the Power BI 'flakiness %' KPI (spec section 7.3)."""
    return {name: get_flakiness(name) for name in get_all_tracked_tests()}


def record_run_results(scenarios: list[dict], run_id: str = "") -> None:
    """Convenience: records every scenario in a smoky-results.json payload."""
    for sc in scenarios:
        record_result(
            test_name=sc.get("name", "unknown"),
            passed=sc.get("status") == "passed",
            duration_ms=sc.get("duration_ms", 0),
            run_id=run_id,
        )
