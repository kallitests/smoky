#!/usr/bin/env python3
"""
agent/spec_generator.py — Cypress spec generator + Claude self-validation

Two responsibilities:
  1. generate() — sends the User Story to Claude, receives a runnable Cypress
     .cy.ts spec file directly (no Gherkin/BDD intermediate layer — Claude
     writes test code, and self-validation checks that code against the story)
  2. validate() — Claude self-critiques its own output (coherence, hallucinations, coverage)
"""

import os
import re
import json
import logging
from anthropic import Anthropic

logger = logging.getLogger("smoky.spec")

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
# SpecGenerator
# ---------------------------------------------------------------------------

class SpecGenerator:

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
          - spec_content: the full Cypress .cy.ts spec as a string
          - file_name: e.g. "proj_142_login.cy.ts"
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

Generate the Cypress spec file now.
"""
        logger.info(f"[spec] Calling Claude for {issue_key}")

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        spec_content = response.content[0].text.strip()

        # Remove markdown code fences if Claude wrapped the output
        spec_content = re.sub(r"^```(?:ts|typescript|javascript|js)?\n?", "", spec_content)
        spec_content = re.sub(r"\n?```$", "", spec_content)

        # Build a clean file name from the issue key
        slug = re.sub(r"[^a-z0-9]+", "_", summary.lower())[:40].strip("_")
        file_name = f"{issue_key.lower().replace('-', '_')}_{slug}.cy.ts"

        logger.info(f"[spec] Generated {file_name} ({len(spec_content)} chars)")
        return spec_content, file_name

    def validate(self, story: str, spec: str) -> tuple[float, list[str]]:
        """
        Claude self-critiques the generated Cypress spec.
        Returns:
          - score: float 0–10
          - issues: list of detected problems (hallucinations, missing cases, etc.)
        """
        validation_prompt = _load_prompt("validation_prompt.txt")

        user_message = f"""
Original User Story:
{story}

Generated Cypress spec:
{spec}

Evaluate the spec and return ONLY a JSON object like:
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
            logger.info(f"[spec] Validation score: {score}/10 — {len(issues)} issue(s)")
            return score, issues
        except json.JSONDecodeError as e:
            logger.error(f"[spec] Failed to parse validation JSON: {e}")
            return 0.0, [f"Validation parsing error: {e}"]
