// =============================================================================
// cypress/support/helpers/loginValidation.ts
// =============================================================================
// Pure, framework-free logic — no Cypress APIs here. This is what the spec
// (docs/architecture/architecture-pipeline-cicd-sdet.md, section 5.1) means
// by "unit tests target custom commands/helpers": this function is exercised
// directly by tests/unit/loginValidation.spec.ts (Vitest, no browser), and
// reused by the signInUI command / step definitions so the validation rule
// isn't duplicated in the Gherkin step implementations.
//
// Mirrors the Real World App's own client-side sign-in validation (observed
// in cypress-io/cypress-realworld-app's SignInForm — see
// cypress/tests/ui/auth.spec.ts "should display login errors" for the exact
// copy asserted here):
//   - username is required
//   - password must be at least 4 characters
// =============================================================================

export interface Credentials {
  username: string;
  password: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: Partial<Record<keyof Credentials, string>>;
}

export function validateCredentials({ username, password }: Credentials): ValidationResult {
  const errors: ValidationResult["errors"] = {};

  if (!username || username.trim().length === 0) {
    errors.username = "Username is required";
  }

  if (!password || password.length < 4) {
    errors.password = "Password must contain at least 4 characters";
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  };
}
