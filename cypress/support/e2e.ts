// =============================================================================
// cypress/support/e2e.ts — Cypress support file
// =============================================================================
// Loaded before every spec (Gherkin features, API specs, and agent-generated
// specs alike). Registers:
//   - custom commands (signInUI, signOutUI, apiLogin, apiLogout, apiCheckAuth)
//   - @cypress/grep: enables --env grepTags=@smoke / @{issue_key} filtering
//     for non-BDD specs (cypress/api/, cypress/e2e/generated/)
//   - cypress-mochawesome-reporter: per-test screenshot embedding in the report
// =============================================================================

import "./commands";
import "@cypress/grep";
import "cypress-mochawesome-reporter/register";
