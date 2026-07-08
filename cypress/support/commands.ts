/// <reference types="cypress" />

// =============================================================================
// cypress/support/commands.ts — Custom commands for the auth domain
// =============================================================================
// These commands are the single place that knows how to interact with the
// target application's sign-in/sign-out UI and API. Step definitions
// (cypress/e2e/**/*.steps.ts) call these commands instead of re-implementing
// selectors or request logic, so Gherkin steps stay declarative and the
// business logic (how to fill the form, how to call the API) lives in one
// place — per the spec's "step definitions implement scenarios only, no
// duplicated business logic" rule.
//
// Selectors and routes are grounded in the real target app for this example
// (cypress-io/cypress-realworld-app): data-test attributes and request
// shapes observed directly in its source (backend/auth.ts,
// cypress/support/commands.ts, cypress/tests/ui/auth.spec.ts).
// =============================================================================

const MOBILE_VIEWPORT_BREAKPOINT = 600;
const isMobile = () => Cypress.config("viewportWidth") < MOBILE_VIEWPORT_BREAKPOINT;

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      /** Fills and submits the sign-in form. Visits /signin first if needed. */
      signInUI(
        username: string,
        password: string,
        options?: { rememberMe?: boolean }
      ): Chainable<void>;
      /** Opens the sidenav (mobile only) and clicks sign-out. */
      signOutUI(): Chainable<void>;
      /** POST /login without going through the UI. */
      apiLogin(username: string, password: string): Chainable<Cypress.Response<unknown>>;
      /** POST /logout without going through the UI. */
      apiLogout(): Chainable<Cypress.Response<unknown>>;
      /** GET /checkAuth without going through the UI. */
      apiCheckAuth(): Chainable<Cypress.Response<unknown>>;
    }
  }
}

Cypress.Commands.add(
  "signInUI",
  (username: string, password: string, { rememberMe = false } = {}) => {
    cy.location("pathname", { log: false }).then((path) => {
      if (path !== "/signin") {
        cy.visit("/signin");
      }
    });

    cy.intercept("POST", "/login").as("loginRequest");

    cy.get('[data-test="signin-username"]').find("input").clear();
    cy.get('[data-test="signin-username"]').type(username);
    cy.get('[data-test="signin-password"]').find("input").clear();
    cy.get('[data-test="signin-password"]').type(password);

    if (rememberMe) {
      cy.get('[data-test="signin-remember-me"]').find("input").check();
    }

    cy.get('[data-test="signin-submit"]').click();
  }
);

Cypress.Commands.add("signOutUI", () => {
  if (isMobile()) {
    cy.get('[data-test="sidenav-toggle"]').click();
  }
  cy.get('[data-test="sidenav-signout"]').click();
});

Cypress.Commands.add("apiLogin", (username: string, password: string) => {
  return cy.request({
    method: "POST",
    url: "/login",
    body: { username, password },
    failOnStatusCode: false,
  });
});

Cypress.Commands.add("apiLogout", () => {
  return cy.request({
    method: "POST",
    url: "/logout",
    failOnStatusCode: false,
    followRedirect: false,
  });
});

Cypress.Commands.add("apiCheckAuth", () => {
  return cy.request({
    method: "GET",
    url: "/checkAuth",
    failOnStatusCode: false,
  });
});

export {};
