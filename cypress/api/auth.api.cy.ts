// =============================================================================
// cypress/api/auth.api.cy.ts
// =============================================================================
// API-level coverage for US-001 (login/logout), kept physically separate
// from the UI spec (spec section 3: "cypress/api/ ... séparées des tests UI
// pour permettre une exécution indépendante et plus rapide"). No browser
// navigation here — cy.request only, so this runs first in the pipeline and
// fails fast before any UI test bothers to spin up a browser.
//
// Tags follow the same convention as agent-generated specs (@cypress/grep,
// title-based): @smoke, @regression, @critical, @api.
//
// Routes and response shapes grounded in cypress-io/cypress-realworld-app
// (backend/auth.ts): POST /login, POST /logout, GET /checkAuth.
// =============================================================================

import { validateCredentials } from "../support/helpers/loginValidation";

describe("Auth API — /login, /logout, /checkAuth @api @US-001", () => {
  let testUser: { username: string; password: string };

  before(() => {
    cy.fixture("testUser").then((user) => {
      testUser = user;
    });
  });

  beforeEach(() => {
    cy.clearCookie("connect.sid");
  });

  it("POST /login responds 200 with the authenticated user for valid credentials @smoke @critical", () => {
    const start = Date.now();

    cy.apiLogin(testUser.username, testUser.password).then((response) => {
      const latencyMs = Date.now() - start;

      expect(response.status, "status").to.eq(200);
      expect(response.body, "body shape").to.have.property("user");
      expect(response.body.user, "user id present").to.have.property("id");
      expect(response.body.user, "no password leak in response").to.not.have.property("password");
      expect(latencyMs, "latency budget").to.be.lessThan(2000);
    });
  });

  it("POST /login responds 401 for an incorrect password @regression", () => {
    cy.apiLogin(testUser.username, "wrong-password").then((response) => {
      expect(response.status).to.eq(401);
    });
  });

  it("POST /login responds 401 for a non-existent username @regression", () => {
    cy.apiLogin("does-not-exist-user", testUser.password).then((response) => {
      expect(response.status).to.eq(401);
    });
  });

  it("GET /checkAuth responds 401 with an explicit error when not authenticated @regression", () => {
    cy.apiCheckAuth().then((response) => {
      expect(response.status).to.eq(401);
      expect(response.body).to.deep.equal({ error: "User is unauthorized" });
    });
  });

  it("GET /checkAuth responds 200 with the current user once authenticated @smoke", () => {
    cy.apiLogin(testUser.username, testUser.password).then(() => {
      cy.apiCheckAuth().then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property("user");
        expect(response.body.user.username).to.eq(testUser.username);
      });
    });
  });

  it("POST /logout clears the session so a subsequent auth check is unauthorized @smoke @critical", () => {
    cy.apiLogin(testUser.username, testUser.password).then(() => {
      cy.apiLogout().then((logoutResponse) => {
        expect(logoutResponse.status, "logout redirect status").to.be.oneOf([
          301, 302, 303, 307, 308,
        ]);

        cy.apiCheckAuth().then((checkResponse) => {
          expect(checkResponse.status).to.eq(401);
        });
      });
    });
  });

  it("validateCredentials helper agrees with the server's minimum password length @regression", () => {
    // Cross-check: the unit-tested client-side rule (tests/unit/loginValidation.spec.ts)
    // should reject the same short password the server would never even see
    // submitted through the real UI form (submit button stays disabled).
    const result = validateCredentials({ username: testUser.username, password: "abc" });
    expect(result.valid).to.eq(false);
    expect(result.errors.password).to.eq("Password must contain at least 4 characters");
  });
});
