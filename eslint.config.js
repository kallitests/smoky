// =============================================================================
// eslint.config.js — flat config (required by ESLint 9+, no more .eslintrc)
// =============================================================================
const js = require("@eslint/js");
const tseslint = require("typescript-eslint");
const cypressPlugin = require("eslint-plugin-cypress");
const eslintConfigPrettier = require("eslint-config-prettier");

module.exports = tseslint.config(
  {
    ignores: [
      "node_modules/**",
      "cypress/e2e/generated/**",
      "cypress-report/**",
      "cypress/videos/**",
      "cypress/screenshots/**",
      "cypress/downloads/**",
      "coverage/**",
      "docker/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["cypress/**/*.ts", "features/**/*.ts", "tests/**/*.ts"],
    plugins: { cypress: cypressPlugin },
    languageOptions: {
      globals: {
        cy: "readonly",
        Cypress: "readonly",
        expect: "readonly",
        assert: "readonly",
      },
    },
    rules: {
      ...cypressPlugin.configs.recommended.rules,
    },
  },
  {
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-namespace": "off",
    },
  },
  eslintConfigPrettier
);
