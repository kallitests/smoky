#!/usr/bin/env python3
"""
agent/reporting_service.py — Standalone reporting consumer

Reads a smoky-results.json (produced by any workflow's "Build results JSON"
step, or by `npm run test:smoke` + a local export) and pushes it through the
same flakiness-tracking + Power BI pipeline the Jira-agent flow uses. This
is what the `reporting` docker-compose service runs — useful for local runs
and for the CI workflows that aren't driven by the agent (pr.yml, main.yml,
nightly.yml all produce results the agent itself never sees).

Usage: python -m agent.reporting_service [path/to/results.json]
"""

import sys
import json
import logging

from agent.report_publisher import ReportPublisher
from agent.flakiness_tracker import get_flakiness_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smoky.reporting")

DEFAULT_RESULTS_PATH = "smoky-results/results.json"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RESULTS_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            results = json.load(f)
    except FileNotFoundError:
        logger.error(f"[reporting] No results file at {path} — nothing to report")
        sys.exit(1)

    issue_key = results.get("issue_key", "local-run")

    publisher = ReportPublisher()
    flakiness = publisher.record_flakiness(results)
    avg_flakiness = round(sum(flakiness.values()) / len(flakiness), 1) if flakiness else 0.0

    publisher.push_powerbi(issue_key, results, avg_flakiness_pct=avg_flakiness)

    logger.info(f"[reporting] Pushed {issue_key} — avg flakiness {avg_flakiness}%")
    logger.info(f"[reporting] Flakiness by test: {json.dumps(flakiness, indent=2)}")


if __name__ == "__main__":
    main()
