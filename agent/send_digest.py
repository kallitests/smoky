#!/usr/bin/env python3
"""
agent/send_digest.py — Drains the Redis-batched regression-failure queue and
sends one Gmail digest (spec section 8: "rapport de synthèse quotidien ou
hebdomadaire"). Meant to run periodically — e.g. `docker compose run
alerting`, or a scheduled workflow calling this script — not on every
pipeline run (that's what escalate() in report_publisher.py routes away
from immediate alerts).
"""

import json
import logging
from datetime import datetime, timezone

from agent.flakiness_tracker import get_client
from agent.report_publisher import ReportPublisher, DIGEST_QUEUE_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smoky.digest")


def drain_queue() -> list:
    """Pops every entry off the digest queue (FIFO) and parses it back to a dict."""
    redis_client = get_client()
    runs = []
    while True:
        raw = redis_client.lpop(DIGEST_QUEUE_KEY)
        if raw is None:
            break
        runs.append(json.loads(raw))
    return runs


def main():
    runs = drain_queue()
    if not runs:
        logger.info("[digest] Nothing queued — skipping")
        return

    publisher = ReportPublisher()
    subject = f"Smoky digest — {datetime.now(timezone.utc).strftime('%Y-%m-%d')} ({len(runs)} run(s))"
    sent = publisher.send_gmail_digest(subject, runs)
    if not sent:
        logger.warning("[digest] Gmail not configured — runs were drained but not delivered")


if __name__ == "__main__":
    main()
