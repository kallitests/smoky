import { defineConfig } from "cypress";
import createBundler from "@bahmutov/cypress-esbuild-preprocessor";
import { addCucumberPreprocessorPlugin } from "@badeball/cypress-cucumber-preprocessor";
import { createEsbuildPlugin } from "@badeball/cypress-cucumber-preprocessor/esbuild";

// =============================================================================
// Smoky — Cypress configuration
// =============================================================================
// Two families of specs, per docs/architecture/architecture-pipeline-cicd-sdet.md:
//
//   1. Hand-authored, BDD-traced User Stories:
//      features/**/*.feature  (Gherkin, source of truth for the story)
//      cypress/e2e/**/*.steps.ts  (step definitions, matched by the
//        cypress-cucumber-preprocessor "stepDefinitions" glob in package.json)
//      Tag filtering: --env tags="@smoke" (cucumber tag expressions, AND/OR/NOT)
//
//   2. Agent-generated, per-Jira-ticket smoke specs (no BDD layer — see
//      agent/spec_generator.py):
//      cypress/e2e/generated/**/*.cy.ts
//      Tag filtering: --env grepTags="@smoke+@{issue_key}" (@cypress/grep)
//
//   API specs (cypress/api/) also use plain @cypress/grep title tags — they
//   are not run through Cucumber since the spec doc scopes BDD to UI stories.
//
// Both tag mechanisms can be passed together: the two plugins each only look
// at the spec type they own, so `--env tags=@smoke,grepTags=@smoke` is safe.
//
// Cross-browser (Firefox/Edge) is driven from CI with `--browser <name>`, not
// via Cypress "projects" — the nightly workflow runs this same config once
// per browser in a matrix.
// =============================================================================

export default defineConfig({
  e2e: {
    // Base URL — injected by GitHub Actions from secrets
    baseUrl: process.env.BASE_URL || "http://localhost:3000",

    specPattern: [
      "features/**/*.feature",
      "cypress/api/**/*.cy.ts",
      "cypress/e2e/generated/**/*.cy.ts",
    ],
    supportFile: "cypress/support/e2e.ts",

    // Only load specs that actually match the active tag filter — avoids
    // loading step definitions / support code for filtered-out features
    env: {
      filterSpecs: true,
      omitFiltered: true,
    },

    // Retry once in CI to reduce flakiness noise
    retries: {
      runMode: process.env.CI ? 1 : 0,
      openMode: 0,
    },

    // Record video always in CI (agent needs a link for Slack); off locally
    video: !!process.env.CI,

    // Screenshot on failure
    screenshotOnRunFailure: true,

    // Timeouts — smoke tests should be fast
    defaultCommandTimeout: 10_000,
    pageLoadTimeout: 15_000,

    // Reporter: cypress-mochawesome-reporter merges per-spec results into a
    // single HTML report with embedded failure screenshots (Gherkin scenarios
    // run as mocha describe/it blocks under the hood, so the report stays
    // organized by feature/scenario — this is what satisfies the spec's
    // "Cucumber HTML report" requirement without a second reporting tool),
    // plus a JSON file the Smoky agent / CI step reads to build
    // smoky-results.json
    reporter: "cypress-mochawesome-reporter",
    reporterOptions: {
      reportDir: "cypress-report",
      overwrite: false,
      html: true,
      json: true,
    },

    async setupNodeEvents(on, config) {
      await addCucumberPreprocessorPlugin(on, config);

      on(
        "file:preprocessor",
        createBundler({
          plugins: [createEsbuildPlugin(config)],
        })
      );

      // eslint-disable-next-line @typescript-eslint/no-var-requires
      require("cypress-mochawesome-reporter/plugin")(on);
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      require("@cypress/grep/src/plugin")(config);

      return config;
    },
  },
});
