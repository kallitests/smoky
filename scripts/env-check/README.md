# env_check.py — Pre-launch Environment Validator

Validates that everything is in place before running a project. Catches all blocking issues upfront — no more mid-run crashes on a missing variable or an expired token.

## What it checks

| Phase | Check |
|---|---|
| **Python version** | Requires 3.11+ |
| **.env file** | Present · parsable · no syntax errors · `--fix` auto-creates from `.env.example` |
| **Placeholder detection** | Flags unfilled values: `<YOUR_KEY>`, `xxx`, `changeme`, `REPLACE_ME` |
| **Required variables** | Presence + format validation (API key patterns, URL shape, email…) |
| **Optional variables** | Warns if Slack, Teams, OpenAI, LangSmith are absent — does not block |
| **Network connectivity** | TCP socket check on all external services defined in the config |
| **Python packages** | Import check + minimum version for all required dependencies |
| **Docker** | Binary in PATH · daemon running |
| **Playwright browsers** | Chromium (or others) installed via `playwright install` |

## Usage

```bash
python env_check.py                    # standard colored output
python env_check.py --strict           # warnings = failures (CI gate)
python env_check.py --ci               # compact output for CI logs
python env_check.py --fix              # auto-create .env from .env.example
python env_check.py --env /path/.env   # explicit .env path
```

Exit code `0` = ready · Exit code `1` = blocking issues found.
Safe to use as a gate step in any CI/CD pipeline before running tests.

## Requirements

Standard library only — no external dependencies.
