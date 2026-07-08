module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2021: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:cypress/recommended",
    "prettier",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
  },
  plugins: ["@typescript-eslint", "cypress"],
  ignorePatterns: [
    "node_modules/",
    "cypress/e2e/generated/",
    "cypress-report/",
    "cypress/videos/",
    "cypress/screenshots/",
    "coverage/",
    "*.cjs",
  ],
  rules: {
    "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/no-explicit-any": "off",
    "@typescript-eslint/no-namespace": "off"
  },
};
