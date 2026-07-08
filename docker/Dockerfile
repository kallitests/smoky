# =============================================================================
# Dockerfile — Smoky Cypress Runner
# =============================================================================
# Base: cypress/browsers — official Cypress image with OS deps + Chrome/
# Firefox/Edge preinstalled, no Cypress binary baked in (we install our own
# pinned version via npm ci, matching package.json exactly).
#
# Tag is a frozen, version-specific tag (not `latest`), per Cypress's own
# guidance: "use a corresponding frozen image tag rather than a convenience
# tag" (frozen tags are immutable; `latest`/short tags can change without
# notice). Verified current at build time — bump deliberately, don't chase
# `latest` automatically.
#   https://github.com/cypress-io/cypress-docker-images
# =============================================================================

FROM cypress/browsers:node-24.18.0-chrome-150.0.7871.46-1-ff-152.0.5-edge-150.0.4078.48-1 AS base

WORKDIR /app

# Copy dependency files first — Docker layer caching
COPY package.json package-lock.json* ./

# Install Node dependencies (ci = exact versions from lock file)
RUN npm ci

# Copy source
COPY . .

# Environment
ENV CI=true
ENV NODE_ENV=test

# -----------------------------------------------------------------------------
# Run as the non-root "node" user the base image provides (not root) —
# and work around two documented cypress-docker-images issues that only
# show up under a non-root user:
#   1. "EACCES ... binary_state.json" — Cypress needs write access to its
#      binary cache dir when re-verifying an npm-installed binary.
#   2. "Fontconfig error: No writable cache directories" — needs a writable
#      $HOME for the non-root user.
# https://github.com/cypress-io/cypress-docker-images (README, "Known problems")
# -----------------------------------------------------------------------------
ENV HOME=/home/node
RUN mkdir -p /home/node/.cache/Cypress \
  && chown -R node:node /app /home/node \
  && chmod -R 777 /home/node/.cache/Cypress

USER node

# Verify the installed binary matches package.json at build time — fails
# the build early instead of failing silently at test-run time
RUN npx cypress verify

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD npx cypress verify || exit 1

# Default: run all @smoke tagged tests in Chrome. Overridden per-service in
# docker-compose.yml (lint/unit/api/smoke/regression all reuse this image).
CMD ["npx", "cypress", "run", "--browser", "chrome", "--env", "grepTags=@smoke"]
