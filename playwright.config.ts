import { defineConfig, devices } from "@playwright/test";

// =============================================================================
// Smoky — Playwright configuration
// =============================================================================
// Smoke tests run fast, on Chromium only by default.
// Tags @smoke and @{issue_key} are used by GitHub Actions to filter tests.
// =============================================================================

export default defineConfig({
  testDir: "./tests",

  // Run tests in parallel — each spec file gets its own worker
  fullyParallel: true,

  // Fail the build if test.only() was accidentally committed
  forbidOnly: !!process.env.CI,

  // Retry once in CI to reduce flakiness noise
  retries: process.env.CI ? 1 : 0,

  // 2 workers in CI (GitHub Actions runner has 2 vCPUs)
  workers: process.env.CI ? 2 : undefined,

  // Reporters: HTML for humans, JSON for the Smoky agent to consume
  reporter: [
    ["html", { open: "never", outputFolder: "playwright-report" }],
    ["json", { outputFile: "test-results/results.json" }],
    ["list"],
  ],

  use: {
    // Base URL — injected by GitHub Actions from secrets
    baseURL: process.env.BASE_URL || "http://localhost:3000",

    // Capture trace on first retry — open with: npx playwright show-trace trace.zip
    trace: "on-first-retry",

    // Record video on failure
    video: "on-first-retry",

    // Screenshot on failure
    screenshot: "only-on-failure",

    // Timeouts — smoke tests should be fast
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },

  projects: [
    {
      // Default project for CI smoke runs
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      // Optional: run cross-browser on PRs
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],
});
