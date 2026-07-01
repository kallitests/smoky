# 🤖 Smoky — Autonomous Smoke Test Agent

> **A Claude-powered agent that watches your Jira board 24/7, writes Gherkin scenarios from User Stories, runs them through a Dockerized Playwright MCP pipeline, and publishes results to Slack and Power BI — zero human intervention.**

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions)](https://github.com/kallitests/smoky-playwright/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-MCP-green?style=flat-square&logo=playwright)](https://playwright.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-blueviolet?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](LICENSE)

---

## 🗺️ Table of Contents

- [Why this project exists (STAR)](#-why-this-project-exists-star)
- [How it works](#-how-it-works)
- [Workflow](#-workflow)
- [Stack](#-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running Smoky](#-running-smoky)
- [GitHub Actions Setup](#️-github-actions-setup)
- [Power BI Setup](#-power-bi-setup)
- [Slack Setup](#-slack-setup)
- [Error Handling](#-error-handling)
- [Roadmap](#-roadmap)

---

## 🎯 Why this project exists (STAR)

> A smoke test suite that writes itself, runs itself, and reports itself — because your QA engineers have better things to do than babysit regression scripts.

**Situation**

Most teams ship features faster than they can cover them. Smoke tests are the first line of defense before every release, yet they're almost always the first thing to rot: QA writes them by hand, developers forget to update them, and by the time a critical login or checkout flow breaks in staging, it's already too late — or nobody wrote the test for it in the first place. Meanwhile Jira fills up with tickets nobody has time to fully verify, and "we'll add tests later" quietly becomes "we never did."

**Task**

Build an agent that removes the bottleneck entirely: turn every Jira ticket into a verified, running smoke test — with no manual scripting, no waiting on QA bandwidth, and no human forgetting to close the loop. The agent had to be trustworthy enough to run unattended, which meant it also had to test *itself*.

**Action**

Smoky was built as an autonomous Claude agent that watches Jira, converts User Stories into Gherkin scenarios, self-validates its own output for hallucinations and coverage gaps, triggers a Dockerized Playwright MCP pipeline via GitHub Actions, and reports results in plain language to Slack, Power BI, and back onto the ticket itself — end to end, zero human intervention. On top of that, the agent's own output is continuously evaluated with DeepEval, RAGAS, and Promptfoo, so the AI generating the tests is held to the same rigor as the tests it generates.

**Result — the pain points it kills, and who feels the relief**

| Pain point (before) | What Smoky changes |
|---|---|
| Smoke tests written manually, days after the ticket is "done" | Tests exist within minutes of the ticket being marked ready |
| QA time burned on repetitive, low-value scripting | QA time redirected to exploratory testing and real edge cases |
| Regressions caught late, in staging or prod | Regressions caught at ticket level, before merge even lands |
| No visibility into test coverage or flakiness trends | Live Power BI dashboard: pass rate, flakiness, trend over 30 days |
| "Is it tested?" answered with a guess | Answered with a Slack report and a Jira status, every time |
| AI-generated content trusted blindly | AI output scored, gated, and audited like any other pipeline stage |

**Value delivered, by audience**

- **IT / Engineering** — one less manual step in the delivery pipeline, dockerized and CI-native, plugs into GitHub Actions without touching existing infrastructure.
- **Business (PO / PM / CEO)** — faster time-to-confidence on every release, fewer production incidents, and a dashboard that turns "is quality okay?" from a meeting question into a live number.
- **QA team** — freed from repetitive scripting to focus on high-value testing, with an AI teammate that documents its own reasoning and flags what it's unsure about instead of guessing silently.

This project isn't a toy demo — it's a working answer to a question every engineering org eventually asks: *can we trust an AI to test our software, and how do we prove it?*

---

## 💡 How it works

A developer creates a Jira ticket and adds the label `smoky-ready`.

Smoky detects it, reads the User Story, and takes over:

```
Jira ticket detected
        ↓
Claude reads the User Story
        ↓
Claude generates Gherkin scenarios (Happy Path + negative cases)
        ↓
Claude validates its own output (coherence score, hallucination check)
        ↓
GitHub Actions triggers the Dockerized Playwright MCP pipeline
        ↓
Results → Power BI dashboard + Slack report + Jira ticket updated
```

No configuration per ticket. No test code to write. The developer's job ends when they create the ticket.

---

## 🔁 Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SMOKY — FULL PIPELINE                           │
│                                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│  │  DEV     │    │   JIRA       │    │   SMOKY AGENT (Claude)       │  │
│  │          │───▶│  New ticket  │───▶│                              │  │
│  │  Creates │    │  label:      │    │  1. Detect ticket            │  │
│  │  ticket  │    │  smoky-ready │    │  2. Read User Story          │  │
│  └──────────┘    └──────────────┘    │  3. Generate Gherkin         │  │
│                                      │  4. Self-validate (score/10) │  │
│                                      │  5. Dispatch GitHub Actions   │  │
│                                      └──────────────┬───────────────┘  │
│                                                     │                  │
│                                                     ▼                  │
│                          ┌──────────────────────────────────────────┐  │
│                          │   GITHUB ACTIONS — CI/CD PIPELINE        │  │
│                          │                                          │  │
│                          │  Docker → Playwright MCP → Tests → JSON  │  │
│                          └──────────────────┬───────────────────────┘  │
│                                             │                          │
│                                             ▼                          │
│              ┌──────────────────────────────────────────────────────┐  │
│              │                    OUTPUTS                            │  │
│              │                                                       │  │
│              │  Power BI dashboard  ←── JSON results               │  │
│              │  Slack #smoky-results ←── NL report (Claude)        │  │
│              │  Jira ticket          ←── Status updated             │  │
│              └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Step by step

**Step 1 — Detection**
The Smoky watcher polls Jira every 5 minutes (or receives a webhook instantly).
Trigger: label `smoky-ready` on any ticket in the configured project.

**Step 2 — Gherkin generation**
Claude reads the User Story (`As a / I want / So that`) and the acceptance criteria.
It generates a `.feature` file with at least one Happy Path scenario and one negative scenario.
Selectors use `data-test` attributes. Nothing is invented — if information is missing, Claude adds a `# SMOKY_UNCERTAIN` comment.

**Step 3 — Self-validation**
Claude scores its own output out of 10 across four dimensions:
coherence with the story, absence of hallucinations, coverage (Happy Path + negative case), and Gherkin format.
A score below 6 blocks the pipeline and triggers a clarification request on the Jira ticket.

**Step 4 — GitHub Actions dispatch**
The agent sends a `repository_dispatch` event to GitHub Actions with the `.feature` file encoded in base64.
No file system sharing required between the agent and CI.

**Step 5 — Playwright MCP execution**
GitHub Actions decodes the `.feature` file, writes it to disk, and runs Playwright.
Playwright MCP translates each Gherkin step into browser actions: `navigate`, `fill`, `click`, `assert_visible`, `screenshot`.
Results are exported as JSON, HTML report, screenshots, and traces.

**Step 6 — Publishing**
Claude writes a natural-language Slack report from the JSON results.
Results are pushed to Power BI. The Jira ticket is transitioned to `Smoke Done` or `Smoke Failed`.

---

## 🧰 Stack

| Layer | Technology |
|---|---|
| LLM | [Claude Sonnet](https://anthropic.com) via Anthropic API |
| Agent orchestration | [LangGraph](https://langchain-ai.github.io/langgraph) state machine |
| Jira integration | Jira REST API v3 · APScheduler (polling) |
| Test execution | [Playwright MCP](https://github.com/microsoft/playwright-mcp) · TypeScript |
| Containerization | Docker · `mcr.microsoft.com/playwright` |
| CI/CD | GitHub Actions (`repository_dispatch`) |
| Reporting | Power BI REST API · Slack Incoming Webhooks |
| Observability | [LangSmith](https://smith.langchain.com) · Playwright Trace Viewer |
| Evaluation | [DeepEval](https://deepeval.com) · RAGAS |

---

## 📁 Project Structure

```
smoky-playwright/
├── .github/
│   └── workflows/
│       └── smoky.yml               # Main CI pipeline (repository_dispatch)
│
├── agent/
│   ├── smoky_agent.py              # LangGraph state machine — main orchestrator
│   ├── jira_watcher.py             # Ticket detection, polling, Jira API helpers
│   ├── gherkin_generator.py        # Claude Gherkin generation + self-validation
│   ├── github_dispatcher.py        # GitHub Actions trigger + results polling
│   └── report_publisher.py         # Slack + Power BI + Jira update
│
├── prompts/
│   ├── system_prompt.txt           # Claude system prompt for Gherkin generation
│   └── validation_prompt.txt       # Claude self-critique prompt
│
├── tests/
│   ├── features/                   # .feature files (generated dynamically, git-ignored)
│   └── step_definitions/           # Playwright MCP step implementations
│
├── docker/
│   ├── Dockerfile                  # Playwright runner image
│   └── docker-compose.yml          # Local development stack
│
├── utils/
│   └── env_check.py                # Pre-launch environment validator
│
├── .env.example                    # Environment variables template
├── .gitignore
├── playwright.config.ts            # Playwright config (reporters, timeouts, browsers)
├── package.json
├── requirements.txt
└── README.md
```

---

## 🔧 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- A Jira project with API access
- A GitHub repository with Actions enabled
- An Anthropic API key

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/kallitests/smoky-playwright.git
cd smoky-playwright
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node dependencies

```bash
npm install
```

### 4. Install Playwright browsers

```bash
npx playwright install chromium
```

### 5. Copy and fill the environment file

```bash
cp .env.example .env
# Edit .env with your API keys and URLs
```

### 6. Validate your environment

```bash
python utils/env_check.py
```

---

## ⚙️ Configuration

### Jira setup

1. Create a Jira API token at [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Add the label `smoky-ready` to any ticket you want Smoky to process
3. Optional: create Jira statuses `Smoke Done` and `Smoke Failed` for automatic transitions

### GitHub Secrets

Add these secrets to your GitHub repository (`Settings → Secrets → Actions`):

| Secret | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `JIRA_BASE_URL` | e.g. `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | Your Jira account email |
| `JIRA_API_TOKEN` | Your Jira API token |
| `JIRA_PROJECT_KEY` | e.g. `PROJ` |
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions |
| `STAGING_BASE_URL` | Base URL of your staging environment |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `LANGCHAIN_API_KEY` | LangSmith API key (optional) |

---

## ▶️ Running Smoky

### Start the Jira watcher (production mode)

```bash
python -m agent.jira_watcher
```

Polls Jira every 5 minutes. Runs indefinitely. Deploy on any server or container.

### Run Smoky on a specific ticket (manual)

```bash
python -c "from agent.smoky_agent import run_smoky; run_smoky('PROJ-142')"
```

### Run with Docker

```bash
# Start the agent
docker compose -f docker/docker-compose.yml up agent

# Run tests for a specific ticket
ISSUE_KEY=PROJ-142 docker compose -f docker/docker-compose.yml run smoky
```

### Run Playwright tests locally

```bash
npm run test:smoke
```

---

## ⚡ GitHub Actions Setup

The workflow triggers automatically via `repository_dispatch`. The Smoky Python agent sends the event — you don't trigger it manually in production.

To test the workflow manually from the GitHub UI:

1. Go to `Actions → Smoky — Playwright Smoke Tests`
2. Click `Run workflow`
3. Enter an issue key and target environment
4. Click `Run workflow`

The HTML report is uploaded as an artifact and retained for 14 days.

---

## 📊 Power BI Setup

1. Create a streaming dataset in Power BI with these columns:

| Column | Type |
|---|---|
| `issue_key` | Text |
| `passed` | Number |
| `failed` | Number |
| `total` | Number |
| `duration_ms` | Number |
| `environment` | Text |
| `conclusion` | Text |
| `run_id` | Text |

2. Copy the dataset ID and workspace ID into your `.env` file
3. Generate a Power BI access token and add it to `.env`

Smoky pushes one row per ticket run. Build your dashboard from there.

---

## 💬 Slack Setup

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable `Incoming Webhooks`
3. Create a webhook for your `#smoky-results` channel
4. Add the webhook URL to `.env` as `SLACK_WEBHOOK_URL`

Example Slack report:

```
Smoky | PROJ-142 | User authentication — Login flow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status  : ✅ All passed
Passed  : 2/2
Duration: 38s
Env     : staging

Scenarios:
✅ Successful login with valid credentials — 18s
✅ Login fails with invalid password — 20s

Open Jira ticket  |  Full report
```

---

## 🛡️ Error Handling

| Error scenario | Smoky's response |
|---|---|
| Jira ticket too vague | Adds clarification request as Jira comment + Slack alert |
| Claude validation score < 6 | Blocks pipeline, flags scenarios with `SMOKY_UNCERTAIN` |
| LLM timeout (> 30s) | Retries 3 times, then escalates to Slack |
| GitHub Actions failure | Auto re-run once, then Slack alert + Jira `Smoke Failed` |
| Flaky test (fails > 2 runs) | Tagged `@flaky`, included in separate flakiness report |
| Power BI API unavailable | Falls back to CSV artifact in GitHub Actions |
| Slack webhook down | Email fallback to configured address |

---

## 📌 Roadmap

### ✅ Phase 1 — MVP

- [x] Jira ticket detection (polling every 5 min)
- [x] Gherkin generation via Claude (Happy Path + negative cases)
- [x] Claude self-validation (coherence score + hallucination detection)
- [x] GitHub Actions dispatch via `repository_dispatch`
- [x] Dockerized Playwright MCP execution
- [x] Slack notification (text report)
- [x] Jira status transition on completion

### 🔜 Phase 2 — Consolidation

- [ ] Jira webhook (real-time — replaces polling)
- [ ] Power BI streaming dashboard
- [ ] DeepEval integration (LLM eval on Gherkin quality)
- [ ] Flakiness detection and reporting
- [ ] Natural-language failure diagnosis (Claude)
- [ ] Multi-ticket parallel processing

### 🔭 Phase 3 — Intelligence

- [ ] LangGraph parallel nodes (multiple tickets simultaneously)
- [ ] Prompt regression detection (alert if Gherkin quality drifts between versions)
- [ ] Claude vs GPT-4o benchmark on Gherkin quality
- [ ] REST API for external triggers (curl, Postman, webhooks)
- [ ] Minimal web UI for run status and history

### 🧪 Phase 4 — AI Testing (testing Smoky's own AI)

Smoky isn't just a tool that tests applications — it's an AI agent, which means **Smoky itself has to be tested**. A traditional test suite checks that code does what it's supposed to do; an LLM-based agent needs a different kind of scrutiny, because its output is non-deterministic, can drift over time, and can fail silently — a wrong Gherkin scenario looks exactly as plausible as a correct one until someone runs it.

**Why AI testing is mandatory here, not optional:**

- **Non-determinism** — the same Jira ticket can produce slightly different Gherkin output on two separate runs. Classic unit tests assume repeatable input → output; LLM output has to be evaluated on quality and correctness ranges, not exact equality.
- **Hallucination risk** — Claude could invent a `data-test` selector, an assumed field, or a business rule that was never in the User Story. An invented selector that "looks right" can pass code review and still test the wrong thing in production.
- **Silent quality drift** — a prompt tweak, a model version change, or a system prompt refactor can quietly degrade Gherkin quality without throwing any error. Without continuous evaluation, this kind of regression is invisible until test coverage has already eroded.
- **Trust in an unattended agent** — Smoky runs with zero human review of the generated scenarios before they hit CI. If nobody is checking Smoky's output, Smoky's own output quality has to be checked automatically, on every run.
- **Compounding downstream cost** — a bad Gherkin scenario doesn't just fail once. It gets committed, run repeatedly in CI, and can create false confidence ("smoke tests are green") while covering the wrong behavior entirely.

**Planned AI testing stack:**

- [ ] **DeepEval** — LLM-native evaluation framework to score each generated `.feature` file against the source User Story: relevance, faithfulness (no hallucinated selectors/steps), and completeness (Happy Path + negative case present). Runs as an automated gate in the CI pipeline, alongside Claude's own self-critique score.
- [ ] **RAGAS** — measures Gherkin/User Story consistency as a retrieval-augmented-generation-style faithfulness problem: does the generated scenario actually reflect the acceptance criteria, or did Claude fill gaps with assumptions?
- [ ] **Promptfoo** — regression testing between prompt/model versions. Every change to `system_prompt.txt` or `validation_prompt.txt` is benchmarked against a fixed set of reference tickets before merging, so a "small prompt tweak" can't silently tank Gherkin quality.
- [ ] **LangSmith** — full tracing and observability of every LLM call (ticket in → Gherkin out), so failures and quality drops can be diagnosed at the trace level, not just guessed at from the final output.
- [ ] **Pytest** — classic unit tests for the deterministic parts of the codebase (Jira parsing, GitHub dispatch payloads, Slack/Power BI formatting) — the non-AI plumbing around the AI core still needs conventional coverage.
- [ ] **Golden dataset of reference tickets** — a curated, versioned set of real-world Jira tickets with known-good expected Gherkin output, used as the baseline for every DeepEval/RAGAS/Promptfoo run.
- [ ] **Automated quality gate in CI** — a run is blocked from reaching production if the DeepEval/RAGAS score drops below threshold, exactly the same way a failing unit test blocks a deploy.

---

## 👤 Author

**Kallitests**
AI Quality Engineer · LLM Testing · Playwright MCP · Python

[![GitHub](https://img.shields.io/badge/GitHub-kallitests-181717?style=flat-square&logo=github)](https://github.com/kallitests)

---

## 📚 Related projects

- [smoke-tests-sentinel](https://github.com/kallitests/smoke-tests-sentinel) — the original Smoky prototype
- [Playwright Showroom](https://github.com/kallitests/playwright-showroom) — Playwright CLI & MCP reference repo

---

## License

MIT

---

*Built with 🤖 Claude (Anthropic) · 🎭 Playwright MCP · 🔗 LangGraph · 🐳 Docker*
