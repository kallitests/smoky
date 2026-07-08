# =============================================================================
# Dockerfile — Smoky Cypress Runner
# =============================================================================
# Uses the official Cypress browsers image: Node.js + Chrome/Firefox/Edge
# pre-installed. No separate browser install step needed in CI.
# Pin/verify the tag against https://github.com/cypress-io/cypress-docker-images
# when bumping Cypress versions.
# =============================================================================

FROM cypress/browsers:node20.16.0-chrome127-ff128

WORKDIR /app

# Copy dependency files first — Docker layer caching
COPY package.json package-lock.json* ./

# Install Node dependencies (ci = exact versions from lock file)
RUN npm ci

# Copy test source
COPY . .

# Environment variables passed at runtime by GitHub Actions
ENV CI=true

# Default: run all @smoke tagged tests in Chrome
CMD ["npx", "cypress", "run", "--browser", "chrome", "--env", "grepTags=@smoke"]
