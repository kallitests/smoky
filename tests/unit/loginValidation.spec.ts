import { describe, it, expect } from "vitest";
import { validateCredentials } from "../../cypress/support/helpers/loginValidation";

// =============================================================================
// tests/unit/loginValidation.spec.ts
// =============================================================================
// Unit tests for the pure validation helper backing cy.signInUI() and the
// "Client-side validation blocks incomplete credentials" scenario in
// features/US-001-login-logout.feature. No Cypress runtime involved — this
// is the fast, every-commit layer of the pyramid (spec section 5.1).
// =============================================================================

describe("validateCredentials", () => {
  it("is valid for a well-formed username and a password of 4+ characters", () => {
    const result = validateCredentials({ username: "standard_user", password: "s3cret" });

    expect(result.valid).toBe(true);
    expect(result.errors).toEqual({});
  });

  it("flags a missing username", () => {
    const result = validateCredentials({ username: "", password: "s3cret" });

    expect(result.valid).toBe(false);
    expect(result.errors.username).toBe("Username is required");
    expect(result.errors.password).toBeUndefined();
  });

  it("flags a whitespace-only username as missing", () => {
    const result = validateCredentials({ username: "   ", password: "s3cret" });

    expect(result.valid).toBe(false);
    expect(result.errors.username).toBe("Username is required");
  });

  it("flags a password shorter than 4 characters", () => {
    const result = validateCredentials({ username: "standard_user", password: "abc" });

    expect(result.valid).toBe(false);
    expect(result.errors.password).toBe("Password must contain at least 4 characters");
    expect(result.errors.username).toBeUndefined();
  });

  it("accepts a password of exactly 4 characters (boundary)", () => {
    const result = validateCredentials({ username: "standard_user", password: "abcd" });

    expect(result.valid).toBe(true);
  });

  it("flags both fields when username and password are both invalid", () => {
    const result = validateCredentials({ username: "", password: "ab" });

    expect(result.valid).toBe(false);
    expect(result.errors.username).toBe("Username is required");
    expect(result.errors.password).toBe("Password must contain at least 4 characters");
  });
});
