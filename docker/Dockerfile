# =============================================================================
# Dockerfile — Smoky Playwright MCP Runner
# =============================================================================
# Uses the official Playwright image: Node.js + all browsers pre-installed.
# No npx playwright install needed — runs out of the box in any CI pipeline.
# =============================================================================

FROM mcr.microsoft.com/playwright:v1.44.0-jammy

WORKDIR /app

# Copy dependency files first — Docker layer caching
COPY package.json package-lock.json* ./

# Install Node dependencies (ci = exact versions from lock file)
RUN npm ci

# Copy test source
COPY . .

# Environment variables passed at runtime by GitHub Actions
ENV PLAYWRIGHT_MCP=true
ENV CI=true

# Default: run all @smoke tagged tests in Chromium
CMD ["npx", "playwright", "test", "--grep", "@smoke", "--project=chromium"]
