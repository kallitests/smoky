// =============================================================================
// cypress/e2e/auth/login-logout.steps.ts
// =============================================================================
// Step definitions for features/US-001-login-logout.feature (UI scenarios).
// API-level coverage for the same story lives in cypress/api/auth.api.cy.ts
// as a plain Cypress spec — see the note at the bottom of the feature file.
//
// These steps are intentionally thin: all UI interaction logic lives in
// cypress/support/commands.ts (signInUI, signOutUI, apiCheckAuth) and
// cypress/support/helpers/loginValidation.ts. Steps only orchestrate — they
// don't know a selector, per the spec's rule that step definitions implement
// scenarios without duplicating business logic already described elsewhere.
//
// Values shared between steps within a scenario use Cypress aliases
// (cy.as / cy.get('@alias')) rather than closures, since Cypress commands
// are queued asynchronously — this is the standard Cypress pattern for
// passing data between steps/commands in the same test.
// =============================================================================

import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

Given("the application is seeded with a known test user", () => {
  cy.fixture("testUser").as("testUser");
});

Given("I am on the sign-in page", () => {
  cy.visit("/signin");
});

Given("I am signed in", function () {
  cy.fixture("testUser").then((user) => {
    cy.wrap(user).as("testUser");
    cy.signInUI(user.username, user.password);
    cy.location("pathname").should("eq", "/");
  });
});

When("I sign in with valid credentials", function () {
  cy.get("@testUser").then((user: any) => {
    cy.signInUI(user.username, user.password);
  });
});

When("I sign in with valid credentials and check {string}", function (_label: string) {
  cy.get("@testUser").then((user: any) => {
    cy.signInUI(user.username, user.password, { rememberMe: true });
  });
});

When("I sign in with an incorrect password", function () {
  cy.get("@testUser").then((user: any) => {
    cy.signInUI(user.username, "wrong-password");
  });
});

When("I enter {string} as username and {string} as password", (username: string, password: string) => {
  cy.visit("/signin");
  if (username) {
    cy.get('[data-test="signin-username"]').type(username);
  }
  cy.get('[data-test="signin-username"]').find("input").blur();

  if (password) {
    cy.get('[data-test="signin-password"]').type(password);
  }
  cy.get('[data-test="signin-password"]').find("input").blur();
});

When("I sign out", () => {
  cy.signOutUI();
});

Then("I should be redirected to the home page", () => {
  cy.location("pathname").should("eq", "/");
});

Then("I should be redirected to the sign-in page", () => {
  cy.location("pathname").should("eq", "/signin");
});

Then("a session cookie should be set", () => {
  cy.getCookie("connect.sid").should("exist");
});

Then("the session cookie should have an expiry date roughly {int} days out", (days: number) => {
  cy.getCookie("connect.sid").should("have.property", "expiry");
  cy.getCookie("connect.sid").then((cookie) => {
    const expiryMs = (cookie!.expiry as number) * 1000;
    const daysFromNow = (expiryMs - Date.now()) / (1000 * 60 * 60 * 24);
    expect(daysFromNow).to.be.closeTo(days, 2);
  });
});

Then("I should see the error message {string}", (message: string) => {
  cy.get('[data-test="signin-error"]').should("be.visible").and("have.text", message);
});

Then("I should remain on the sign-in page", () => {
  cy.location("pathname").should("eq", "/signin");
});

Then("I should see the validation message {string}", (message: string) => {
  cy.contains(message).should("be.visible");
});

Then("the sign-in button should be disabled", () => {
  cy.get('[data-test="signin-submit"]').should("be.disabled");
});

Then("I should no longer be authenticated", () => {
  cy.apiCheckAuth().its("status").should("eq", 401);
});
