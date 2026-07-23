# 🤖 Smoky — Autonomous AI Agent for Cypress Smoke Tests

> [!NOTE]
> **Personal side project**, built independently for the portfolio of my microenterprise **Kallitests** — outside of any client engagement. Core expertise stays Cypress test automation; Smoky adds an agentic AI layer on top of it, plus a dockerized CI/CD chain that industrializes the whole thing.

> [!WARNING]
> **🚧 Work in Progress** — This project is under active construction. Some features described below (Phase 2/3/4 of the roadmap) are not fully implemented yet. Expect breaking changes, incomplete modules, and evolving docs. Not production-ready.

> **A Claude-powered agent that watches your Jira board 24/7, turns User Stories into verified Cypress smoke tests, runs them through a Dockerized Cypress pipeline, and publishes results to Slack, Power BI, and the ticket itself — a confidence verdict in under 5 minutes, zero human intervention.**

**Scope, on purpose:** Smoky only writes and runs *smoke tests / pre-tests* — UI and API — covering happy paths and their opposite, unhappy paths (error cases, edge cases), on an app's most critical flows. The goal is a fast confidence verdict, not exhaustive coverage. A full non-regression / integration / validation suite is the next layer to build on top of what Smoky delivers, not something Smoky claims to replace.

[![Status](https://img.shields.io/badge/status-work%20in%20progress-red?style=flat-square&logo=progress)](#-why-this-project-exists-star)

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions)](https://github.com/kallitests/smoky-cypress/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![Cypress](https://img.shields.io/badge/Cypress-13-green?style=flat-square&logo=cypress)](https://www.cypress.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-blueviolet?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](LICENSE)

---

## 🗺️ Table of Contents

- [Why this project exists (STAR)](#-why-this-project-exists-star)
- [How it works](#-how-it-works)
- [Workflow](#-workflow)
- [Smoky-RAG](#-smoky-rag)
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

Smoky was built as an autonomous Claude agent that watches Jira, converts User Stories directly into runnable Cypress spec files, self-validates its own output for hallucinations and coverage gaps, triggers a Dockerized Cypress pipeline via GitHub Actions, and reports results in plain language to Slack, Power BI, and back onto the ticket itself — end to end, zero human intervention. On top of that, the agent's own output is continuously evaluated with DeepEval, RAGAS, and Promptfoo, so the AI generating the tests is held to the same rigor as the tests it generates.

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

The value add is **Cypress + DevOps + AI**: Cypress automation is the core skill, GitHub Actions and Docker industrialize it end to end, and the agentic AI layer generates, validates, and maintains the smoke scenarios continuously — no human writing or babysitting scripts.

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
Claude generates a Cypress spec (Happy Path + negative cases)
        ↓
Claude validates its own output (coherence score, hallucination check)
        ↓
GitHub Actions triggers the Dockerized Cypress pipeline
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
│                                      │  3. Generate Cypress spec  │  │
│                                      │  4. Self-validate (score/10) │  │
│                                      │  5. Dispatch GitHub Actions   │  │
│                                      └──────────────┬───────────────┘  │
│                                                     │                  │
│                                                     ▼                  │
│                          ┌──────────────────────────────────────────┐  │
│                          │   GITHUB ACTIONS — CI/CD PIPELINE        │  │
│                          │                                          │  │
│                          │  Docker → Cypress → Tests → JSON      │  │
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

**Step 2 — Cypress spec generation**
Claude reads the User Story (`As a / I want / So that`) and the acceptance criteria.
It generates a complete Cypress `.cy.ts` spec file directly — no Gherkin/BDD intermediate layer — with at least one Happy Path test and one negative-case test.
Selectors use `data-test` attributes. Nothing is invented — if information is missing, Claude adds a `// SMOKY_UNCERTAIN` comment.

**Step 3 — Self-validation**
Claude scores its own output out of 10 across four dimensions:
coherence with the story, absence of hallucinations, coverage (Happy Path + negative case), and valid Cypress spec format.
A score below 6 blocks the pipeline and triggers a clarification request on the Jira ticket.

**Step 4 — GitHub Actions dispatch**
The agent sends a `repository_dispatch` event to GitHub Actions with the `.cy.ts` spec file encoded in base64.
No file system sharing required between the agent and CI.

**Step 5 — Cypress execution**
GitHub Actions decodes the spec file, writes it to `cypress/e2e/generated/`, and runs Cypress with `@cypress/grep` filtering by `@smoke` + issue key tags.
Results are exported as JSON (mochawesome), an HTML report, screenshots, and videos on failure.

**Step 6 — Publishing**
Claude writes a natural-language Slack report from the JSON results.
Results are pushed to Power BI. The Jira ticket is transitioned to `Smoke Done` or `Smoke Failed`.

---

## 🧠 Smoky-RAG

> [!NOTE]
> **Planned for Phase 2** — Smoky-RAG is designed but not yet wired into `agent/spec_generator.py`. See [`docs/specs/smoky-rag-spec-v1-en.txt`](docs/specs/smoky-rag-spec-v1-en.txt) for the full design.

Step 2 above (Cypress spec generation) works from the Jira ticket alone. That's often not enough: a ticket rarely repeats a business rule that's already documented in a PRD, the selectors already used in a neighboring spec, or the response codes exposed by the actual API. **Smoky-RAG** is the retrieval layer that closes that gap — it doesn't replace the ticket, it completes it.

```
Step 1 (Jira detection) ──▶ [Smoky-RAG: retrieval + rerank] ──▶
Step 2 (Cypress generation, enriched with retrieved context) ──▶
Steps 3-6 (unchanged)
```

**What it indexes:** PRDs, past User Stories, existing Test Cases, API docs (OpenAPI/Swagger), resolved Jira tickets, Confluence pages, Release Notes, Requirements — continuously synced into a vector store (Qdrant), embedded with Voyage AI.

**What it does at generation time:**
1. Builds a query from the ticket's summary, description, and acceptance criteria
2. Retrieves the top-k most relevant chunks, reranks down to the top 3-4
3. Injects them into the Claude prompt as a `RETRIEVED CONTEXT` block, each item tagged with its source (`jira`, `confluence`, `cypress_spec`, `openapi`, `prd`)
4. If retrieved context contradicts the ticket, Claude prioritizes the ticket and flags the conflict with a `// RAG_CONFLICT` comment instead of silently picking one

**What it unlocks:**

| Capability | Example |
|---|---|
| Faster test case generation | Reuses patterns from PRDs/User Stories instead of starting from a blank ticket |
| Better requirement analysis | Flags ambiguities by comparing the ticket to its PRD/Requirements |
| Intelligent bug investigation | Surfaces similar historical defects from resolved Jira tickets |
| Smarter regression testing | Identifies modules impacted by a Release Note automatically |
| API testing assistance | Generates request/response assertions straight from the OpenAPI spec |
| Knowledge search | Natural-language Q&A across Jira/Confluence/docs (`/smoky-ask` on Slack) |
| Faster onboarding | New QA/devs get sourced, natural-language answers instead of digging through 4 tools |

Retrieval quality is evaluated with **RAGAS** — faithfulness ≥ 0.85, context precision ≥ 0.80, context recall ≥ 0.75 — the same evaluation stack already planned for Smoky's own output in [Phase 4](#-roadmap).

---

## 🧰 Stack

| Layer | Technology |
|---|---|
| LLM | [Claude Sonnet](https://anthropic.com) via Anthropic API |
| Agent orchestration | [LangGraph](https://langchain-ai.github.io/langgraph) state machine |
| Jira integration | Jira REST API v3 · APScheduler (polling) |
| Test execution | [Cypress](https://www.cypress.io) · TypeScript · `@cypress/grep` |
| BDD | `@badeball/cypress-cucumber-preprocessor` · Gherkin (`features/`) |
| Unit tests | [Vitest](https://vitest.dev) · 80% coverage threshold |
| Local quality gate | Husky · lint-staged · ESLint · Prettier · commitlint (Conventional Commits) |
| Containerization | Docker · `cypress/browsers` |
| CI/CD | GitHub Actions — `pr.yml` / `main.yml` / `nightly.yml` / `smoky.yml` (`repository_dispatch`) |
| Reporting | Power BI REST API (flakiness history in Redis) · Slack Incoming Webhooks · `cypress-mochawesome-reporter` · Cypress Cloud (used by the adjacent, non-regression full-pyramid tooling below) |
| Observability | [LangSmith](https://smith.langchain.com) · Cypress screenshots/videos |
| Evaluation | [DeepEval](https://deepeval.com) · RAGAS |
| RAG — embeddings | [Voyage AI](https://www.voyageai.com) (`voyage-3`) |
| RAG — vector store | [Qdrant](https://qdrant.tech) |
| RAG — reranking | Cross-encoder (`bge-reranker`) or Claude |
| RAG — ingestion sources | Jira · Confluence REST API · Cypress spec repo · OpenAPI/Swagger |

---

## 📁 Project Structure

```
smoky-cypress/
├── .github/
│   └── workflows/
│       ├── smoky.yml               # Jira-agent dispatch + manual tag-filtered run — Smoky's own smoke-test pipeline
│       ├── pr.yml                  # PR: lint + unit + API + smoke (parallel jobs)
│       ├── main.yml                # Merge-to-main: full regression (Cypress Cloud) — adjacent to Smoky, the "next layer" beyond smoke scope
│       └── nightly.yml             # Nightly: cross-browser + dependency audit
│
├── .husky/
│   ├── pre-commit                  # lint-staged (ESLint + Prettier on staged files)
│   ├── commit-msg                  # commitlint (Conventional Commits)
│   └── pre-push                    # unit tests + @smoke subset
│
├── features/
│   └── US-001-login-logout.feature # Gherkin User Story — source of truth, 1:1 traceable
│
├── cypress/
│   ├── e2e/
│   │   ├── auth/
│   │   │   └── login-logout.steps.ts   # Step defs for US-001 (UI only)
│   │   └── generated/               # Agent-generated .cy.ts specs (no BDD layer, git-ignored)
│   ├── api/
│   │   └── auth.api.cy.ts           # API spec, independent of UI, runs first
│   ├── support/
│   │   ├── e2e.ts                   # commands + @cypress/grep + reporter registration
│   │   ├── commands.ts               # signInUI/signOutUI/apiLogin/apiLogout/apiCheckAuth
│   │   └── helpers/
│   │       └── loginValidation.ts    # pure logic, unit-tested separately
│   └── fixtures/
│       └── testUser.json
│
├── tests/
│   └── unit/
│       └── loginValidation.spec.ts   # Vitest — no browser, runs in seconds
│
├── agent/
│   ├── smoky_agent.py              # LangGraph state machine — main orchestrator
│   ├── jira_watcher.py             # Ticket detection, polling, Jira API helpers
│   ├── spec_generator.py           # Claude Cypress spec generation + self-validation
│   ├── github_dispatcher.py        # GitHub Actions trigger + results polling
│   └── report_publisher.py         # Slack + Power BI + Jira update
│
├── rag/                             # Smoky-RAG — retrieval layer (Phase 2, see above)
│   ├── ingestion/
│   │   ├── jira_ingest.py          # Sync resolved tickets -> chunks
│   │   ├── confluence_ingest.py    # Sync product/QA pages -> chunks
│   │   ├── cypress_spec_ingest.py  # Sync validated specs -> chunks
│   │   ├── openapi_ingest.py       # Swagger/OpenAPI parsing -> chunks
│   │   └── chunker.py              # Shared chunking + overlap logic
│   ├── retriever.py                 # Vector search + reranking
│   ├── vector_store.py              # Qdrant/pgvector client wrapper
│   ├── embeddings.py                # Voyage AI / Claude Embeddings wrapper
│   └── prompt_context_builder.py    # Formats retrieved chunks for the prompt
│
├── prompts/
│   ├── system_prompt.txt           # Claude system prompt for Cypress spec generation
│   ├── validation_prompt.txt       # Claude self-critique prompt
│   └── rag_context_template.txt    # Smoky-RAG context injection template
│
├── evals/
│   └── ragas_eval.py                # RAGAS faithfulness / context precision & recall
│
├── docker/
│   ├── Dockerfile                  # Cypress runner image
│   ├── Dockerfile.agent            # Python agent image
│   └── docker-compose.yml          # Local development stack
│
├── docs/
│   ├── architecture/
│   │   └── architecture-pipeline-cicd-sdet.md  # Target architecture (this layer's spec)
│   └── specs/
│       ├── smoky-spec-v1-en.txt    # AI agent technical spec
│       └── smoky-rag-spec-v1-en.txt # Smoky-RAG technical spec
│
├── utils/
│   └── env_check.py                # Pre-launch environment validator
│
├── .env.example                    # Environment variables template
├── .eslintrc.cjs / .prettierrc.json / commitlint.config.js
├── .gitignore
├── cypress.config.ts               # Cypress + Cucumber preprocessor + grep + reporter
├── vitest.config.ts                # Unit test runner, 80% coverage threshold
├── tsconfig.json
├── package.json
├── requirements.txt
└── README.md
```

---

## 📗 Example User Story — US-001 Login/Logout

Demonstrates the smoke layer Smoky owns, plus the adjacent full-pyramid
tooling (unit/API/regression) this repo also carries as a demo of the "next
layer" mentioned above, against
[cypress-realworld-app](https://github.com/cypress-io/cypress-realworld-app)
(selectors/routes grounded in its real source, not invented):

- **Unit** — `tests/unit/loginValidation.spec.ts` tests the pure validation helper
- **API** — `cypress/api/auth.api.cy.ts` hits `/login`, `/logout`, `/checkAuth` directly
- **UI / BDD** — `features/US-001-login-logout.feature` + `cypress/e2e/auth/login-logout.steps.ts`
- **Tags** — `@smoke @critical` (must pass every PR), `@regression` (merge/nightly), `@api`

Run just this story locally:

```bash
npm run test:unit
BASE_URL=https://<your-rwa-instance> npm run test:api
BASE_URL=https://<your-rwa-instance> npx cypress run --env tags=@smoke,grepTags=@smoke
```

> **Note on architecture**: this reinstates Gherkin/BDD for hand-authored User
> Stories, which supersedes an earlier decision in this repo's history to have
> the Jira agent generate plain `.cy.ts` specs directly with no BDD layer. Both
> now coexist by design: the agent's fully-autonomous per-ticket flow
> (`agent/spec_generator.py`) still writes plain specs into
> `cypress/e2e/generated/` for speed and zero step-definition maintenance,
> while curated, higher-value stories like this one get full Gherkin
> traceability. See `docs/architecture/architecture-pipeline-cicd-sdet.md`.

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
git clone https://github.com/kallitests/smoky-cypress.git
cd smoky-cypress
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node dependencies

```bash
npm install
```

Cypress downloads its own browser binary automatically as part of `npm install` — no separate browser install step needed (verify anytime with `npx cypress verify`).

### 4. Copy and fill the environment file

```bash
cp .env.example .env
# Edit .env with your API keys and URLs
```

### 5. Validate your environment

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
| `TEAMS_WEBHOOK_URL` | Teams Adaptive Card webhook (optional — @critical alerts) |
| `DISCORD_WEBHOOK_URL` | Discord webhook (optional — demo channel, @critical alerts) |
| `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` / `GMAIL_DIGEST_TO` | Gmail digest (optional — batched, non-critical) |
| `REDIS_URL` | Flakiness store — point at a managed Redis in CI, not a container |
| `CYPRESS_RECORD_KEY` | Cypress Cloud (optional — used by `main.yml`/`nightly.yml`) |
| `LANGCHAIN_API_KEY` | LangSmith API key (optional) |
| `VOYAGE_API_KEY` | Voyage AI embeddings key (Smoky-RAG, Phase 2) |
| `QDRANT_URL` / `QDRANT_API_KEY` / `QDRANT_COLLECTION` | Vector store connection (Smoky-RAG) |
| `CONFLUENCE_BASE_URL` / `CONFLUENCE_EMAIL` / `CONFLUENCE_API_TOKEN` / `CONFLUENCE_SPACE_KEYS` | Confluence ingestion (Smoky-RAG) |
| `OPENAPI_SPEC_URL` | OpenAPI/Swagger source for API-scenario ingestion (Smoky-RAG) |

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

The full stack — lint, unit, API, smoke, regression, the Jira agent, Redis,
reporting, and alerting — is defined in `docker/docker-compose.yml`. Every
service builds from one of three images: `docker/Dockerfile` (Cypress +
browsers, for api/smoke/regression), `docker/Dockerfile.node` (lean Node
only, for lint/unit — no browser, no Cypress binary), or
`docker/Dockerfile.agent` (Python, for agent/smoky/reporting/alerting).

```bash
cd docker

# Start Redis first — flakiness tracking + the Gmail digest queue depend on it
docker compose up redis -d

# Local quality gate
docker compose run lint
docker compose run unit

# Test pyramid
docker compose run api
docker compose run smoke
docker compose run regression

# Start the agent (long-running, watches Jira)
docker compose up agent

# Run a single ticket end-to-end
ISSUE_KEY=PROJ-142 docker compose run smoky

# Push a results.json through flakiness tracking -> Power BI
docker compose run reporting

# Flush the batched Gmail digest
docker compose run alerting
```

### Run Cypress tests locally

```bash
npm run test:smoke
npm run test:regression
npm run test:api
npm run test:unit
```

---

## ⚡ GitHub Actions Setup

The workflow triggers automatically via `repository_dispatch`. The Smoky Python agent sends the event — you don't trigger it manually in production.

To test the workflow manually from the GitHub UI:

1. Go to `Actions → Smoky — Cypress Smoke Tests`
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

Add an `avg_flakiness_pct` (Number) column too — `agent/flakiness_tracker.py`
computes it from the last 20 runs per test (stored in Redis) and
`push_powerbi()` includes it on every push.

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
- [x] Cypress spec generation via Claude (Happy Path + negative cases, no Gherkin/BDD layer)
- [x] Claude self-validation (coherence score + hallucination detection)
- [x] GitHub Actions dispatch via `repository_dispatch`
- [x] Dockerized Cypress execution
- [x] Slack notification (text report)
- [x] Jira status transition on completion

### 🔜 Phase 2 — Consolidation

- [ ] Jira webhook (real-time — replaces polling)
- [ ] Power BI streaming dashboard
- [ ] DeepEval integration (LLM eval on generated spec quality)
- [ ] Flakiness detection and reporting
- [ ] Natural-language failure diagnosis (Claude)
- [ ] Multi-ticket parallel processing
- [ ] **Smoky-RAG MVP** — Jira + Confluence ingestion, Qdrant vector store, simple top-k retrieval wired into `spec_generator.py` (see [Smoky-RAG](#-smoky-rag))
- [ ] Smoky-RAG: Cypress spec + OpenAPI ingestion, reranking, `// RAG_CONFLICT` detection, continuous RAGAS evaluation

### 🔭 Phase 3 — Intelligence

- [ ] LangGraph parallel nodes (multiple tickets simultaneously)
- [ ] Prompt regression detection (alert if spec quality drifts between versions)
- [ ] Claude vs GPT-4o benchmark on spec quality
- [ ] REST API for external triggers (curl, Postman, webhooks)
- [ ] Minimal web UI for run status and history
- [ ] Smoky-RAG: similar-bug search from historical Jira tickets (Intelligent Bug Investigation)
- [ ] Smoky-RAG: automated Release Note impact analysis on affected modules
- [ ] Smoky-RAG: `/smoky-ask` Slack command for natural-language Knowledge Search

### 🧪 Phase 4 — AI Testing (testing Smoky's own AI)

Smoky isn't just a tool that tests applications — it's an AI agent, which means **Smoky itself has to be tested**. A traditional test suite checks that code does what it's supposed to do; an LLM-based agent needs a different kind of scrutiny, because its output is non-deterministic, can drift over time, and can fail silently — a wrong Cypress spec looks exactly as plausible as a correct one until someone runs it.

**Why AI testing is mandatory here, not optional:**

- **Non-determinism** — the same Jira ticket can produce slightly different spec output on two separate runs. Classic unit tests assume repeatable input → output; LLM output has to be evaluated on quality and correctness ranges, not exact equality.
- **Hallucination risk** — Claude could invent a `data-test` selector, an assumed field, or a business rule that was never in the User Story. An invented selector that "looks right" can pass code review and still test the wrong thing in production.
- **Silent quality drift** — a prompt tweak, a model version change, or a system prompt refactor can quietly degrade spec quality without throwing any error. Without continuous evaluation, this kind of regression is invisible until test coverage has already eroded.
- **Trust in an unattended agent** — Smoky runs with zero human review of the generated specs before they hit CI. If nobody is checking Smoky's output, Smoky's own output quality has to be checked automatically, on every run.
- **Compounding downstream cost** — a bad Cypress spec doesn't just fail once. It gets committed, run repeatedly in CI, and can create false confidence ("smoke tests are green") while covering the wrong behavior entirely.

**Planned AI testing stack:**

- [ ] **DeepEval** — LLM-native evaluation framework to score each generated `.cy.ts` spec against the source User Story: relevance, faithfulness (no hallucinated selectors/steps), and completeness (Happy Path + negative case present). Runs as an automated gate in the CI pipeline, alongside Claude's own self-critique score.
- [ ] **RAGAS** — measures spec/User Story consistency as a retrieval-augmented-generation-style faithfulness problem: does the generated spec actually reflect the acceptance criteria, or did Claude fill gaps with assumptions?
- [ ] **Promptfoo** — regression testing between prompt/model versions. Every change to `system_prompt.txt` or `validation_prompt.txt` is benchmarked against a fixed set of reference tickets before merging, so a "small prompt tweak" can't silently tank spec quality.
- [ ] **LangSmith** — full tracing and observability of every LLM call (ticket in → spec out), so failures and quality drops can be diagnosed at the trace level, not just guessed at from the final output.
- [ ] **Pytest** — classic unit tests for the deterministic parts of the codebase (Jira parsing, GitHub dispatch payloads, Slack/Power BI formatting) — the non-AI plumbing around the AI core still needs conventional coverage.
- [ ] **Golden dataset of reference tickets** — a curated, versioned set of real-world Jira tickets with known-good expected spec output, used as the baseline for every DeepEval/RAGAS/Promptfoo run.
- [ ] **Automated quality gate in CI** — a run is blocked from reaching production if the DeepEval/RAGAS score drops below threshold, exactly the same way a failing unit test blocks a deploy.

---

## 👤 Author

**Kallitests**
AI Quality Engineer · LLM Testing · Cypress · Python

[![GitHub](https://img.shields.io/badge/GitHub-kallitests-181717?style=flat-square&logo=github)](https://github.com/kallitests)

---

## 📚 Related projects

- [smoke-tests-sentinel](https://github.com/kallitests/smoke-tests-sentinel) — the original Smoky prototype
- [Playwright Showroom](https://github.com/kallitests/playwright-showroom) — Playwright CLI & MCP reference repo

---

## License

MIT

---

*Built with 🤖 Claude (Anthropic) · 🌲 Cypress · 🔗 LangGraph · 🐳 Docker*
