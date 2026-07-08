import { defineConfig } from "vitest/config";

// =============================================================================
// vitest.config.ts — unit test runner (spec section 5.1)
// =============================================================================
// Targets only pure logic: custom Cypress commands' underlying helpers,
// utilities, data transformers. No Cypress/browser APIs here — that's what
// cypress/api and features/ are for. Runs in seconds, on every commit
// (pre-push hook) and on every PR (.github/workflows/pr.yml).
// =============================================================================

export default defineConfig({
  test: {
    include: ["tests/unit/**/*.spec.ts"],
    environment: "node",
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json-summary"],
      include: ["cypress/support/helpers/**/*.ts"],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
});
