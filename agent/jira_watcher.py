#!/usr/bin/env python3
"""
agent/jira_watcher.py — Jira ticket detector and scheduler

Two detection modes:
  1. Polling mode  — cron every 5 min (MVP, zero infra)
  2. Webhook mode  — FastAPI endpoint receiving Jira events (Phase 2)

Trigger condition: Jira label "smoky-ready" OR status "Ready for Smoke Test"
"""

import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from apscheduler.schedulers.blocking import BlockingScheduler
from agent.smoky_agent import run_smoky

logger = logging.getLogger("smoky.jira")

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"]
JIRA_EMAIL    = os.environ["JIRA_EMAIL"]
JIRA_TOKEN    = os.environ["JIRA_API_TOKEN"]
JIRA_PROJECT  = os.environ["JIRA_PROJECT_KEY"]
JIRA_LABEL    = os.environ.get("JIRA_SMOKY_LABEL", "smoky-ready")

auth    = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Jira API helpers
# ---------------------------------------------------------------------------

def search_smoky_tickets() -> list[dict]:
    """
    Returns all tickets labelled 'smoky-ready' that haven't been processed yet.
    JQL excludes tickets already transitioned to 'Smoke Done' or 'Smoke Failed'.
    """
    jql = (
        f'project = "{JIRA_PROJECT}" '
        f'AND labels = "{JIRA_LABEL}" '
        f'AND status NOT IN ("Smoke Done", "Smoke Failed", "Done")'
    )
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {"jql": jql, "fields": "summary,description,labels,priority,components"}
    resp = requests.get(url, headers=headers, auth=auth, params=params)
    resp.raise_for_status()
    return resp.json().get("issues", [])


def get_ticket_details(issue_key: str) -> dict:
    """
    Fetches the full content of a Jira ticket.
    Extracts: summary, description, acceptance criteria (custom field),
    labels, priority, and component.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    resp = requests.get(url, headers=headers, auth=auth)
    resp.raise_for_status()
    fields = resp.json()["fields"]

    # Acceptance criteria may live in a custom field — adjust the key for your instance
    ac_field = "customfield_10016"
    acceptance_criteria = ""
    if ac_field in fields and fields[ac_field]:
        # Handle both plain text and Atlassian Document Format (ADF)
        ac = fields[ac_field]
        if isinstance(ac, str):
            acceptance_criteria = ac
        elif isinstance(ac, dict) and "content" in ac:
            acceptance_criteria = _extract_adf_text(ac)

    return {
        "issue_key": issue_key,
        "summary": fields.get("summary", ""),
        "description": _extract_description(fields.get("description")),
        "acceptance_criteria": acceptance_criteria,
        "labels": fields.get("labels", []),
        "priority": fields.get("priority", {}).get("name", "Major"),
        "component": (fields.get("components") or [{}])[0].get("name", "unknown"),
    }


def _extract_description(description) -> str:
    """
    Jira description comes in Atlassian Document Format (ADF) — a nested JSON.
    This helper extracts plain text from ADF recursively.
    Falls back to str() if the format is unexpected.
    """
    if description is None:
        return ""
    if isinstance(description, str):
        return description
    if isinstance(description, dict) and "content" in description:
        return _extract_adf_text(description)
    return str(description)


def _extract_adf_text(node: dict) -> str:
    """Recursively extracts text from an ADF node."""
    texts = []
    if node.get("type") == "text":
        texts.append(node.get("text", ""))
    for child in node.get("content", []):
        texts.append(_extract_adf_text(child))
    return " ".join(filter(None, texts))


def transition_ticket(issue_key: str, transition_name: str) -> bool:
    """
    Transitions a Jira ticket to a new status by name.
    Looks up the transition ID first (Jira requires the ID, not the name).
    """
    # Get available transitions
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    resp = requests.get(url, headers=headers, auth=auth)
    if resp.status_code != 200:
        return False
    transitions = {t["name"]: t["id"] for t in resp.json().get("transitions", [])}

    transition_id = transitions.get(transition_name)
    if not transition_id:
        logger.warning(f"[jira] Transition '{transition_name}' not found for {issue_key}")
        return False

    payload = {"transition": {"id": transition_id}}
    resp = requests.post(url, json=payload, headers=headers, auth=auth)
    return resp.status_code == 204


def add_comment(issue_key: str, comment: str) -> bool:
    """Adds a plain-text comment to a Jira ticket."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}],
        }
    }
    resp = requests.post(url, json=payload, headers=headers, auth=auth)
    return resp.status_code == 201


# ---------------------------------------------------------------------------
# JiraWatcher class — used by smoky_agent.py
# ---------------------------------------------------------------------------

class JiraWatcher:
    """Thin wrapper exposing Jira operations to the agent."""

    def get_ticket_details(self, issue_key: str) -> dict:
        return get_ticket_details(issue_key)

    def transition(self, issue_key: str, status: str) -> bool:
        return transition_ticket(issue_key, status)

    def comment(self, issue_key: str, text: str) -> bool:
        return add_comment(issue_key, text)


# ---------------------------------------------------------------------------
# Polling loop — runs every 5 minutes
# ---------------------------------------------------------------------------

def polling_loop():
    """
    Main polling function called by the scheduler.
    Finds all smoky-ready tickets and triggers the Smoky pipeline for each.
    """
    logger.info("[jira] Polling for smoky-ready tickets...")
    try:
        tickets = search_smoky_tickets()
        logger.info(f"[jira] Found {len(tickets)} ticket(s) to process")
        for ticket in tickets:
            issue_key = ticket["key"]
            logger.info(f"[jira] Processing {issue_key}")
            # Immediately transition to 'In Progress' to avoid double-processing
            transition_ticket(issue_key, "In Progress")
            run_smoky(issue_key)
    except Exception as e:
        logger.error(f"[jira] Polling error: {e}")


if __name__ == "__main__":
    # Start the scheduler — polls Jira every 5 minutes
    scheduler = BlockingScheduler()
    scheduler.add_job(polling_loop, "interval", minutes=5, id="smoky_poll")
    logger.info("[jira] Smoky watcher started — polling every 5 minutes")
    polling_loop()  # Run once immediately on startup
    scheduler.start()
