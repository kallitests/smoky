#!/usr/bin/env python3
"""
agent/smoky_agent.py — Smoky main agent orchestrator (LangGraph)

This is the brain of Smoky. It orchestrates the full pipeline:
  Jira ticket detection → Cypress spec generation → Validation →
  GitHub Actions dispatch → Results publication (Slack + Power BI + Jira)

Each step is a LangGraph node. The graph handles retries, error branches,
and multi-ticket parallelism cleanly — no spaghetti code.
"""

import json
import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agent.jira_watcher import JiraWatcher
from agent.spec_generator import SpecGenerator
from agent.github_dispatcher import GitHubDispatcher
from agent.report_publisher import ReportPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smoky")

# ---------------------------------------------------------------------------
# Agent state — shared across all nodes in the graph
# ---------------------------------------------------------------------------

class SmokyState(TypedDict):
    # Input
    issue_key: str
    summary: str
    description: str
    acceptance_criteria: str
    labels: list[str]
    priority: str
    component: str
    environment: str

    # Generated
    spec_file_content: str
    spec_file_name: str
    validation_score: float
    validation_issues: list[str]

    # Execution
    dispatch_run_id: str
    test_results: dict

    # Output
    slack_message: str
    jira_comment: str
    error: str
    retry_count: int
    status: str  # pending | generating | validating | dispatched | done | failed


# ---------------------------------------------------------------------------
# Node 1 — Fetch ticket details from Jira
# ---------------------------------------------------------------------------

def fetch_ticket(state: SmokyState) -> SmokyState:
    """
    Reads the full ticket content from Jira API.
    Enriches the state with description, acceptance criteria, labels, priority.
    """
    logger.info(f"[smoky] Fetching ticket {state['issue_key']}")
    watcher = JiraWatcher()
    try:
        ticket = watcher.get_ticket_details(state["issue_key"])
        return {
            **state,
            "summary": ticket["summary"],
            "description": ticket["description"],
            "acceptance_criteria": ticket.get("acceptance_criteria", ""),
            "labels": ticket.get("labels", []),
            "priority": ticket.get("priority", "Major"),
            "component": ticket.get("component", "unknown"),
            "status": "fetched",
        }
    except Exception as e:
        logger.error(f"[smoky] Failed to fetch ticket: {e}")
        return {**state, "error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# Node 2 — Generate Cypress spec via Claude
# ---------------------------------------------------------------------------

def generate_spec(state: SmokyState) -> SmokyState:
    """
    Sends the User Story to Claude and receives a runnable Cypress spec.
    Ensures at least 1 Happy Path and 1 negative scenario are present.
    """
    logger.info(f"[smoky] Generating Cypress spec for {state['issue_key']}")
    generator = SpecGenerator()
    try:
        spec_content, file_name = generator.generate(
            issue_key=state["issue_key"],
            summary=state["summary"],
            description=state["description"],
            acceptance_criteria=state["acceptance_criteria"],
            labels=state["labels"],
            priority=state["priority"],
        )
        return {
            **state,
            "spec_file_content": spec_content,
            "spec_file_name": file_name,
            "status": "generated",
        }
    except Exception as e:
        logger.error(f"[smoky] Spec generation failed: {e}")
        return {**state, "error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# Node 3 — Validate spec quality (Claude self-critique)
# ---------------------------------------------------------------------------

def validate_spec(state: SmokyState) -> SmokyState:
    """
    Claude validates its own output:
      - Coherence score (0–10) vs the original User Story
      - Hallucination detection (invented selectors)
      - Coverage check (Happy Path + negative case present)
    Blocks dispatch if score < 6.
    """
    logger.info(f"[smoky] Validating Cypress spec for {state['issue_key']}")
    generator = SpecGenerator()
    try:
        score, issues = generator.validate(
            story=state["description"],
            spec=state["spec_file_content"],
        )
        logger.info(f"[smoky] Validation score: {score}/10 | Issues: {issues}")
        return {
            **state,
            "validation_score": score,
            "validation_issues": issues,
            "status": "validated" if score >= 6 else "validation_failed",
        }
    except Exception as e:
        return {**state, "error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# Node 4 — Dispatch to GitHub Actions
# ---------------------------------------------------------------------------

def dispatch_pipeline(state: SmokyState) -> SmokyState:
    """
    Sends a repository_dispatch event to GitHub Actions with:
      - The Cypress spec file content (base64 encoded)
      - The issue key, priority, and target environment
    GitHub Actions picks it up and runs the Dockerized Cypress pipeline.
    """
    logger.info(f"[smoky] Dispatching pipeline for {state['issue_key']}")
    dispatcher = GitHubDispatcher()
    try:
        run_id = dispatcher.dispatch(
            issue_key=state["issue_key"],
            spec_file_name=state["spec_file_name"],
            spec_file_content=state["spec_file_content"],
            priority=state["priority"],
            environment=state.get("environment", "staging"),
        )
        return {**state, "dispatch_run_id": run_id, "status": "dispatched"}
    except Exception as e:
        return {**state, "error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# Node 5 — Poll GitHub Actions for results
# ---------------------------------------------------------------------------

def poll_results(state: SmokyState) -> SmokyState:
    """
    Polls the GitHub Actions run until completion (timeout: 10 min).
    Downloads the JSON results artifact when the run finishes.
    """
    logger.info(f"[smoky] Polling results for run {state['dispatch_run_id']}")
    dispatcher = GitHubDispatcher()
    try:
        results = dispatcher.poll_until_complete(
            run_id=state["dispatch_run_id"],
            timeout_seconds=600,
            poll_interval=15,
        )
        return {**state, "test_results": results, "status": "results_ready"}
    except Exception as e:
        return {**state, "error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# Node 6 — Publish results (Slack + Power BI + Jira + Teams/Discord/Gmail)
# ---------------------------------------------------------------------------

def publish_results(state: SmokyState) -> SmokyState:
    """
    Claude generates a natural-language Slack report from the JSON results.
    Publishes to:
      - Slack #smoky-results channel (every run)
      - Power BI dataset, annotated with flakiness (every run)
      - Jira ticket (comment + status transition)
      - Teams/Discord (immediate) or Gmail digest queue (batched), per the
        severity-routed escalation rule in spec section 8 — only on failure
    """
    logger.info(f"[smoky] Publishing results for {state['issue_key']}")
    publisher = ReportPublisher()
    try:
        slack_msg = publisher.build_slack_message(
            issue_key=state["issue_key"],
            summary=state["summary"],
            results=state["test_results"],
        )
        publisher.send_slack(slack_msg)

        flakiness = publisher.record_flakiness(state["test_results"])
        avg_flakiness = round(sum(flakiness.values()) / len(flakiness), 1) if flakiness else 0.0
        publisher.push_powerbi(state["issue_key"], state["test_results"], avg_flakiness_pct=avg_flakiness)

        publisher.update_jira(state["issue_key"], state["test_results"])

        is_critical_smoke = state.get("priority", "Major") in ("Blocker", "Critical")
        publisher.escalate(state["issue_key"], state["test_results"], is_critical_smoke=is_critical_smoke)

        return {
            **state,
            "slack_message": slack_msg,
            "status": "done",
        }
    except Exception as e:
        return {**state, "error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# Node — Error handler (sends alert to Slack + updates Jira)
# ---------------------------------------------------------------------------

def handle_error(state: SmokyState) -> SmokyState:
    """
    Catches any pipeline failure and:
      - Notifies Slack with the error details
      - Transitions the Jira ticket to 'Smoke Failed'
      - Logs the full error for LangSmith tracing
    """
    logger.error(f"[smoky] Error on {state['issue_key']}: {state.get('error')}")
    publisher = ReportPublisher()
    try:
        publisher.send_slack_error(
            issue_key=state["issue_key"],
            error=state.get("error", "Unknown error"),
            step=state.get("status", "unknown"),
        )
        publisher.update_jira_failed(state["issue_key"], state.get("error", ""))
    except Exception as e:
        logger.error(f"[smoky] Error handler itself failed: {e}")
    return {**state, "status": "error_handled"}


# ---------------------------------------------------------------------------
# Routing functions — decide which node to go to next
# ---------------------------------------------------------------------------

def route_after_validation(state: SmokyState) -> str:
    """Routes to dispatch if validation passed, error handler otherwise."""
    if state["status"] == "validated":
        return "dispatch_pipeline"
    return "handle_error"


def route_after_fetch(state: SmokyState) -> str:
    """Routes to spec generation if fetch succeeded."""
    if state["status"] == "failed":
        return "handle_error"
    return "generate_spec"


def route_after_dispatch(state: SmokyState) -> str:
    """Routes to result polling if dispatch succeeded."""
    if state["status"] == "failed":
        return "handle_error"
    return "poll_results"


def route_after_results(state: SmokyState) -> str:
    """Routes to publishing if results are ready."""
    if state["status"] == "failed":
        return "handle_error"
    return "publish_results"


# ---------------------------------------------------------------------------
# Build the LangGraph state machine
# ---------------------------------------------------------------------------

def build_smoky_graph() -> StateGraph:
    """
    Assembles the full Smoky agent graph.
    Each node is a pure function that receives and returns SmokyState.
    """
    graph = StateGraph(SmokyState)

    # Register nodes
    graph.add_node("fetch_ticket", fetch_ticket)
    graph.add_node("generate_spec", generate_spec)
    graph.add_node("validate_spec", validate_spec)
    graph.add_node("dispatch_pipeline", dispatch_pipeline)
    graph.add_node("poll_results", poll_results)
    graph.add_node("publish_results", publish_results)
    graph.add_node("handle_error", handle_error)

    # Entry point
    graph.set_entry_point("fetch_ticket")

    # Edges with routing
    graph.add_conditional_edges("fetch_ticket", route_after_fetch)
    graph.add_edge("generate_spec", "validate_spec")
    graph.add_conditional_edges("validate_spec", route_after_validation)
    graph.add_conditional_edges("dispatch_pipeline", route_after_dispatch)
    graph.add_conditional_edges("poll_results", route_after_results)
    graph.add_edge("publish_results", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Entry point — run Smoky on a single ticket
# ---------------------------------------------------------------------------

def run_smoky(issue_key: str, environment: str = "staging") -> dict:
    """
    Run the full Smoky pipeline for a given Jira ticket.
    Called by jira_watcher.py for each detected ticket.
    """
    graph = build_smoky_graph()
    initial_state: SmokyState = {
        "issue_key": issue_key,
        "summary": "",
        "description": "",
        "acceptance_criteria": "",
        "labels": [],
        "priority": "Major",
        "component": "unknown",
        "environment": environment,
        "spec_file_content": "",
        "spec_file_name": "",
        "validation_score": 0.0,
        "validation_issues": [],
        "dispatch_run_id": "",
        "test_results": {},
        "slack_message": "",
        "jira_comment": "",
        "error": "",
        "retry_count": 0,
        "status": "pending",
    }
    final_state = graph.invoke(initial_state)
    logger.info(f"[smoky] Pipeline complete for {issue_key} — status: {final_state['status']}")
    return final_state


if __name__ == "__main__":
    import sys
    issue_key = sys.argv[1] if len(sys.argv) > 1 else "PROJ-001"
    run_smoky(issue_key)
