#!/usr/bin/env python3
"""
agent/gherkin_generator.py — Gherkin scenario generator + Claude self-validation

Two responsibilities:
  1. generate() — sends the User Story to Claude, receives a .feature file
  2. validate() — Claude self-critiques its own output (coherence, hallucinations, coverage)
"""

import os
import re
import json
import logging
from anthropic import Anthropic

logger = logging.getLogger("smoky.gherkin")

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL  = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Prompt templates (loaded from prompts/ folder)
# ---------------------------------------------------------------------------

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def _load_prompt(name: str) -> str:
    path = os.path.join(PROMPTS_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# GherkinGenerator
# ---------------------------------------------------------------------------

class GherkinGenerator:

    def generate(
        self,
        issue_key: str,
        summary: str,
        description: str,
        acceptance_criteria: str,
        labels: list[str],
        priority: str,
    ) -> tuple[str, str]:
        """
        Sends the User Story to Claude and returns:
          - feature_content: the full .feature file as a string
          - file_name: e.g. "proj_142_login.feature"
        """
        system_prompt = _load_prompt("system_prompt.txt")

        user_message = f"""
Jira ticket: {issue_key}
Priority: {priority}
Labels: {', '.join(labels)}
Summary: {summary}

User Story:
{description}

Acceptance Criteria:
{acceptance_criteria or 'Not specified — infer from the User Story.'}

Generate the Gherkin .feature file now.
"""
        logger.info(f"[gherkin] Calling Claude for {issue_key}")

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        feature_content = response.content[0].text.strip()

        # Remove markdown code fences if Claude wrapped the output
        feature_content = re.sub(r"^```(?:gherkin)?\n?", "", feature_content)
        feature_content = re.sub(r"\n?```$", "", feature_content)

        # Build a clean file name from the issue key
        slug = re.sub(r"[^a-z0-9]+", "_", summary.lower())[:40].strip("_")
        file_name = f"{issue_key.lower().replace('-', '_')}_{slug}.feature"

        logger.info(f"[gherkin] Generated {file_name} ({len(feature_content)} chars)")
        return feature_content, file_name

    def validate(self, story: str, feature: str) -> tuple[float, list[str]]:
        """
        Claude self-critiques the generated Gherkin.
        Returns:
          - score: float 0–10
          - issues: list of detected problems (hallucinations, missing cases, etc.)
        """
        validation_prompt = _load_prompt("validation_prompt.txt")

        user_message = f"""
Original User Story:
{story}

Generated Gherkin:
{feature}

Evaluate the Gherkin and return ONLY a JSON object like:
{{
  "score": 8.5,
  "issues": [
    "Selector '[data-test=submit-btn]' may be invented — not mentioned in the story",
    "Missing negative case for empty password field"
  ],
  "has_happy_path": true,
  "has_negative_case": true,
  "has_hallucinations": false
}}
"""
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=validation_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown if present
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

        try:
            result = json.loads(raw)
            score  = float(result.get("score", 0))
            issues = result.get("issues", [])
            logger.info(f"[gherkin] Validation score: {score}/10 — {len(issues)} issue(s)")
            return score, issues
        except json.JSONDecodeError as e:
            logger.error(f"[gherkin] Failed to parse validation JSON: {e}")
            return 0.0, [f"Validation parsing error: {e}"]
