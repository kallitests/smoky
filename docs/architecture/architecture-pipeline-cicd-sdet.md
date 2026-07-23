# CI/CD Test Pipeline Architecture — From User Story to Full Test Pyramid

> [!NOTE]
> **Context document, not Smoky's own scope.** Smoky itself is deliberately narrow: it only generates and runs *smoke tests / pre-tests* (UI + API, happy path and unhappy path) on an app's most critical flows, to deliver a confidence verdict in under 5 minutes. This document describes the **broader, adjacent architecture** — the full non-regression / integration / validation test pyramid — that Smoky's smoke layer plugs into and that remains **the next layer to build on top of Smoky**, not a deliverable Smoky itself claims to own.

## Executive summary

The goal is to design, starting from a **User Story**, a complete and demonstrable CI/CD pipeline that covers the whole software-quality cycle: local code quality (pre-commit), automated tests at every level of the pyramid (unit, API, smoke, non-regression), orchestrated execution in CI/CD (GitHub Actions / GitLab CI), consolidated reporting (Cucumber, Cypress Cloud, Power BI), and multi-channel alerting (Teams, Slack, Discord, Gmail).

This document isn't just a list of tools: it's an architecture designed as an **internal product**, with end-to-end traceability between the business requirement (the User Story) and the test result reaching the right person, at the right time, on the right channel. That traceability is the foundation that Smoky's smoke-test agent layer sits on top of — Smoky owns the smoke slice of this pyramid; the rest (full non-regression, cross-browser, load) is the next layer to build.

One-line pitch: *"I built a pipeline that turns a User Story into executable tests, runs those tests on every commit, and automatically notifies the right person, with the right data, on the right tool — all observable in a business dashboard. Smoky is the AI agent that owns the smoke-test slice of that pipeline end to end."*

---

## 1. Founding principle: the User Story as single source of truth

Everything starts from the User Story, written as `As a... I want... so that...`, with acceptance criteria in Gherkin format (`Given / When / Then`).

**Why it matters**: rather than treating the User Story as a disposable Jira ticket, it becomes a **versioned artifact** in the repository (the `features/` folder). It acts as the contract between Product Owner, Dev, and QA. This discipline is what lets an LLM read the User Story and automatically generate Gherkin scenarios, then Cypress tests — BDD isn't a stylistic choice here, it's the bridge between business language and machine language. This is also the mechanism Smoky itself uses when grounding a generated smoke scenario in the ticket's real acceptance criteria.

Each User Story is tagged from the start with a criticality level (`@smoke`, `@regression`, `@critical`, `@api`) that later drives the CI execution strategy.

---

## 2. Global architecture — layered view

The architecture reads in 5 layers, from most local to most visible:

1. **Local quality layer** (pre-commit) — blocks errors before they're even pushed.
2. **Test layer** (test pyramid) — unit, API, UI smoke, UI regression.
3. **CI/CD orchestration layer** (GitHub Actions / GitLab CI) — triggers, parallelizes, isolates.
4. **Reporting layer** (Cucumber, Cypress Cloud, Power BI) — turns raw data into insight.
5. **Alerting layer** (Teams, Slack, Discord, Gmail) — pushes information to humans instead of making them go find it.

**Note**: this layered separation is deliberately modeled on a real enterprise architecture (observability + CI/CD + collaboration). Smoky's own smoke-test agent lives inside layers 2-5, scoped to the `@smoke` tier only; the rest of each layer (full regression, broader reporting, broader alerting) belongs to this wider pipeline, built independently of Smoky.

---

## 3. Repository organization

Recommended logical structure (description, not code):

- `features/`: Gherkin files, one per User Story, named `US-XXX-feature-name.feature`
- `cypress/e2e/`: UI step definitions and specs, organized by functional domain (not by test type)
- `cypress/api/`: API test specs, kept separate from UI tests to allow independent, faster execution
- `tests/unit/`: unit tests for utility functions, custom Cypress commands, and front-end business logic where applicable
- `.github/workflows/` and `.gitlab-ci.yml`: pipelines, one file per trigger (PR, merge, nightly)
- `.husky/`: pre-commit and pre-push hooks
- `reports/`: raw report output (git-ignored, published as a CI artifact)
- `docs/architecture/`: this kind of document, versioned and kept current

**Note**: physically separating API/UI/unit tests enables pipelines running at different speeds — feedback speed is a design criterion here, not an accident.

---

## 4. Step 1 — Local code quality (pre-commit)

Before a single test runs in CI, quality is checked locally via Git hooks:

- **Pre-commit**: linter (ESLint with dedicated Cypress/Testing Library rules), formatter (Prettier), staged-files-only check (lint-staged) to stay fast.
- **Commit-msg**: commit format validation (Conventional Commits: `feat`, `fix`, `test`, `chore`...) — this format is later reused to generate an automatic changelog and feed DORA metrics.
- **Pre-push**: runs unit tests and a subset of critical smoke tests, to avoid polluting CI with obvious errors.

**Note**: the guiding principle is "*fail fast, fail local*." Every minute saved locally is a minute of CI saved.

---

## 5. Step 2 — The test pyramid

### 5.1 Unit tests
Target pure logic: custom Cypress commands, helpers, data transformers, dynamic fixtures. Run on every commit, in seconds, with a minimum coverage threshold as a quality gate (e.g. 80%).

### 5.2 API tests
Validate interface contracts independently of the UI (HTTP statuses, response schemas, response times, error cases). Run first in the pipeline because they're fast and cheap — if they fail, there's no point running UI tests that depend on the same services.

### 5.3 Smoke tests — Smoky's scope
Minimal, critical subset of the user journey (login, creating a key resource, checkout flow...), covering happy paths and their unhappy-path counterparts. Tagged `@smoke` from the User Story onward. Target: under 5 minutes of execution, triggered on **every Pull Request**. **This is the layer Smoky, the AI agent described in the main [README](../../README.md) and [spec](../specs/smoky-spec-v1-en.txt), owns end to end** — from reading the Jira ticket to publishing the verdict.

### 5.4 Non-regression tests — the next layer beyond Smoky
Full suite covering the complete set of journeys and edge cases. Longer-running, executed on merge to the main branch and in nightly builds, with parallelization and cross-browser execution. **Out of Smoky's current scope by design** — this is the layer to build on top of what Smoky delivers, not something Smoky generates or maintains today.

### 5.5 The BDD ↔ User Story link
Each Gherkin scenario is directly traceable back to its source User Story. Cypress step definitions implement these scenarios without duplicating business logic already described elsewhere. Cucumber becomes the shared language between the test report and the product ticket.

**Pyramid principle**: the strategy isn't "test everything everywhere all the time" but "the right level of test at the right point in the code's lifecycle."

---

## 6. Step 3 — CI/CD pipeline (GitHub Actions & GitLab CI)

### 6.1 Trigger strategy
- **On Pull Request**: lint + unit tests + API tests + smoke UI tests → feedback in under 10 minutes. This is the trigger Smoky's own `smoky.yml` workflow participates in.
- **On merge to `main`**: full non-regression suite + extended API tests + reporting artifact build.
- **Nightly / scheduled**: full cross-browser suite, light load tests, dependency audit.
- **Manual (workflow_dispatch)**: ability to re-run a tag-filtered suite on demand.

### 6.2 Job structure
Jobs are split to maximize parallelism: a "quality" job (lint/format), a "unit" job, an "API" job, a "UI smoke" job, and a "UI regression" job sharded across multiple runners. Each job publishes its results as an independent CI artifact, so one job's failure doesn't block the others' results from surfacing.

### 6.3 Isolation and environments
Docker containers guarantee reproducibility (same image locally, in CI, and for demos) — this is also why Smoky's own Cypress pipeline is dockerized, multi-stage, and runs as a non-root user. Environments (dev/staging) are handled via dedicated Cypress config files and secrets stored in the CI platform's native secret manager (never in plaintext in the repo).

### 6.4 Quality gates
The pipeline blocks a merge if: unit test coverage falls below threshold, lint fails, a critical smoke test is red, or an abnormal flakiness rate is detected across recent runs. These rules are configured as required checks on the protected branch.

**Note**: framing the pipeline as a **series of progressive quality gates** rather than a single monolithic block tells a clear story: a pipeline sized to give fast feedback without sacrificing long-term rigor.

---

## 7. Step 4 — Consolidated reporting

### 7.1 Cucumber Reports
Generates an HTML report readable by a non-technical audience (Product Owner), organized by feature/scenario, with screenshots attached to failing steps.

### 7.2 Cypress Cloud (cypress.io)
Centralizes runs, video replay of failures, automatic flakiness detection, execution-time trend analytics — serves as the technical source of truth for the QA/Dev team, mainly for the non-regression suite described in 5.4.

### 7.3 Power BI — the bridge to business reporting
Structured results (from Cucumber and Cypress JSON/JUnit exports) are pushed to an intermediate store — for Smoky's own smoke-test results this is Redis, which also historizes flakiness — then consumed by Power BI via a connector or scheduled refresh. The semantic model exposes metrics such as: pass rate per module, average execution time, flakiness rate, number of regressions per sprint, correlation between User Story and failure rate.

**Note**: Power BI is what distinguishes this from a plain Cypress project — it shows the ability to speak to a non-technical audience (management, product) with business KPIs.

---

## 8. Step 5 — Intelligent, multi-channel alerting

The guiding principle is **routing by severity and by audience**, not broadcasting the same message everywhere:

- **Slack / Teams**: real-time technical notifications in dev/QA team channels on every pipeline failure, with a direct link to the run and the failure video. This is Smoky's primary channel for `@smoke`/`@critical` results.
- **Discord**: dedicated demo/portfolio channel, useful to show a custom webhook with a formatted embed (status, duration, link).
- **Gmail**: daily or weekly summary report (digest), aimed at a less technical audience, batched rather than sent per-failure.
- **Conditional escalation**: a failure on a critical smoke test triggers an immediate, distinct alert from a failure on a secondary regression test — prioritization logic built into the pipeline rather than left to a human. Smoky implements this today: severity-based routing across Slack/Teams/Discord plus the batched Gmail digest.

**Note**: alerting here isn't "wire up a webhook" — it's deciding **who needs to know what, in what form, at what frequency**.

---

## 9. Observability and metrics

Beyond pass/fail, the pipeline should expose steering metrics:

- Flakiness rate per test (to identify tests that need rewriting) — historized in Redis for Smoky's smoke layer.
- Average execution time per suite (to detect performance drift).
- DORA-style indicators adapted to testing (deployment frequency, mean time to detect a regression, mean time to resolve).
- Correlation between User Story complexity and the failure rate of its associated tests.

**Note**: measuring the quality of the pipeline itself (not just the quality of the product under test) is what lets you say "I know how to evolve a test system over time, not just write it once." This is also why Smoky's own output is continuously evaluated with DeepEval, RAGAS, and Promptfoo — see the [README](../../README.md#-roadmap) and [spec](../specs/smoky-spec-v1-en.txt).

---

## 10. Security and governance

- No plaintext secrets: exclusive use of native CI secret managers.
- Automatic dependency scanning (npm audit, Dependabot or equivalent) integrated in a weekly pipeline.
- Minimal permissions on tokens used by workflows (least-privilege principle).
- Strict separation between demo webhooks (Discord) and production channels (Slack/Teams) to avoid leaking real information during a demo.

---

## 11. Roadmap — where Smoky fits, and what's beyond it

This pipeline is designed as a foundation with two things layered on top of it, at different scopes:

**Already delivered by Smoky (see the [README](../../README.md) and [spec](../specs/smoky-spec-v1-en.txt)):**

1. **Scenario generation** — reads a User Story in natural language and generates the corresponding Cypress smoke spec, grounded in the Gherkin acceptance criteria and the target app's real code.
2. **Self-validation** — scores its own output before triggering (consistency check, hallucination detection).
3. **Dockerized execution** — multi-stage, non-root Cypress pipeline via GitHub Actions.
4. **Result publishing** — Slack, Power BI (Redis-historized flakiness), and the Jira ticket itself.
5. **Severity-based alerting** — Slack/Teams/Discord plus a batched Gmail digest.
6. **Continuous self-evaluation** — Smoky's own output is scored with DeepEval, RAGAS, and Promptfoo.

**Still to build, beyond Smoky's current scope (the next layer):**

1. **Full non-regression / integration / validation suite** — the complete pyramid described in section 5.4, not just the `@smoke` slice.
2. **Auto-triage of failures** — automatic analysis of failure logs/videos to distinguish a real bug from environment-related flakiness, with a natural-language summary sent to Slack/Teams.
3. **Self-healing selectors** — detection of UI selectors broken by a DOM change, with a proposed fix.
4. **Automatic narrative reporting** — natural-language executive summary of a test run, injected directly into the digest email and the Power BI report.

**Closing note**: *"What Smoky demonstrates today is a narrow but complete AI agent that owns the smoke-test slice of a CI/CD test pipeline, end to end — no human writing or babysitting the scripts. What comes next, on the same foundation, is the full non-regression/integration/validation layer, plus deeper self-healing and auto-triage capabilities — with a human kept in the loop for the decisions that matter."*