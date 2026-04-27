# Cookie Guardian

A fully dynamic AI-Vision-driven browser agent for ephemeral cookie management in GitHub repositories. Uses `patchright` for advanced anti-detection browser automation, an AI vision loop (screenshot → analyze → act) with zero-cost free-tier vision APIs, dynamic platform detection from repo contents, and injects cookies as both GitHub Secrets **and** GitHub Variables.

## Key Features

- **AI-Vision Browser Agent**: Screenshot → AI analysis → action loop using Gemini 2.0 Flash (free tier), OpenRouter, local Ollama, or rule-based fallback
- **Dynamic Platform Detection**: Analyzes repository README, dependencies, source files, and workflows to determine which external platforms need cookies
- **Ephemeral Cookie Handling**: Cookies exist in memory only during extraction, then are immediately injected to GitHub Secrets + Variables and wiped
- **2FA Detection**: Automatically detects and skips accounts requiring 2FA with clear logging
- **CAPTCHA Detection**: Detects reCAPTCHA, hCaptcha, Cloudflare Turnstile, and JS challenges (both AI and DOM fallback)
- **Persistent Browser Profiles**: Session state persists per platform across runs (reduces login friction)
- **Production-Grade Anti-Detection**: `patchright` + stealth args + CDP evasion + realistic fingerprinting
- **Human-Like Behavior**: Bezier mouse curves, realistic typing, random waits, scroll emulation
- **Zero Cost**: Primary engine is Gemini 2.0 Flash free tier (1,500 RPM, no credit card). Falls back through OpenRouter → Ollama → Rule-based
- **No Local Encryption**: No encryption keys needed — sensitive data never touches disk
- **Metadata-Only Database**: SQLite stores only repository names and timestamps, never cookie values
- **Redacted Logging**: All logs are automatically redacted to remove sensitive values
- **WARP IP Rotation**: Optional Cloudflare WARP integration for IP rotation
- **Async & Concurrent**: Fully async orchestrator with bounded concurrency via semaphores

## Limitations

⚠️ **This system does NOT support 2FA/MFA authentication.**

If a platform requires 2FA, the system will:
1. Detect the 2FA requirement
2. Log: "2FA detected on {platform} - skipping (2FA not supported)"
3. Move to the next repository

If a CAPTCHA is encountered, the system will skip the platform cleanly.

## Quick Start

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
patchright install chromium

# Initialize database (metadata only)
python scripts/init_db.py

# Set required environment variables
export CG_GITHUB_TOKEN="your-github-token"

# Optional: Set AI vision API keys (zero-cost free tier)
export GEMINI_API_KEY="your-gemini-key"      # Primary - Gemini 2.0 Flash free tier
export OPENROUTER_API_KEY="your-openrouter-key"  # Fallback

# Optional: Set credentials for authenticated platforms
export USER_CREDENTIALS_GITHUB='{"username": "user", "password": "pass"}'

# Run the orchestrator
python -m src.orchestrator
```

## Configuration

Edit `config.yaml` to adjust settings:

```yaml
app:
  name: cookie-guardian
  max_concurrency: 3
  shard_id: 0
  shard_total: 3
  profile_dir: data/profiles
  max_retries: 3
  har_dir: data/har
  tracing_dir: data/traces
  enable_har: false
  enable_tracing: false

github:
  org: your-org-name
  token_env: CG_GITHUB_TOKEN

logging:
  level: INFO
  json: true

storage:
  database_path: data/cookie_guardian.sqlite  # Metadata only

ai_vision:
  engine: gemini
  gemini_api_key_env: GEMINI_API_KEY
  openrouter_api_key_env: OPENROUTER_API_KEY
  ollama_url: http://localhost:11434
  max_steps: 30
  screenshot_max_width: 800

warp:
  connect_timeout_sec: 30
  rotate_interval_sec: 900
```

## Security Model

### Data Flow

1. **Discovery**: Scan repositories to identify candidates
2. **Analysis**: Dynamically detect which platforms need cookies from repo contents
3. **Extraction**: AI vision agent logs into platforms, extracts cookies into memory only
4. **Injection**: Immediately inject cookies to GitHub Secrets AND Variables via API
5. **Cleanup**: Securely wipe all cookie values from memory

### Dual Injection: Secrets + Variables

The system injects cookies as **both** GitHub Secrets **and** GitHub Variables:

- **GitHub Secrets**: Encrypted with Libsodium sealed boxes. Not visible in UI.
- **GitHub Variables**: **Visible in the UI to anyone with read access.** The system logs a prominent security warning when injecting variables.

⚠️ **Use Variables with caution** — they are unencrypted and visible. They are implemented as explicitly requested for compatibility with workflows that need variable access.

### What Gets Stored

- ✅ Repository names and URLs
- ✅ Extraction timestamps and success/failure status
- ✅ Cookie count, 2FA, and CAPTCHA detection results
- ❌ **Cookie values are NEVER stored locally**

### Browser Profiles

Persistent browser profiles are stored in `data/profiles/{platform}/`. This includes session cookies and localStorage managed by the browser engine. Actual extracted cookie values remain in memory only during the extraction window and are wiped immediately after injection.

### GitHub Secrets

The system injects cookies to GitHub Secrets using Libsodium sealed boxes (required by GitHub API). Secrets are named:
- `COOKIES_{PLATFORM}_{REPO_NAME}` - Contains JSON array of cookies

### GitHub Variables

Variables are named the same as secrets but are **unencrypted and visible**:
- `COOKIES_{PLATFORM}_{REPO_NAME}` - Contains JSON array of cookies (visible in UI)

## Required GitHub Secrets

Set these in your repository's GitHub Secrets:

- `CG_GITHUB_TOKEN` - GitHub API token with repo access. **Do not use `GITHUB_TOKEN`** — it is a reserved secret name in GitHub Actions that is auto-generated and repo-scoped, so it cannot be created manually and lacks the cross-repo permissions needed for Cookie Guardian to inject secrets into other repositories.
- `GEMINI_API_KEY` - (Optional) Gemini 2.0 Flash free tier API key
- `OPENROUTER_API_KEY` - (Optional) OpenRouter API key for fallback
- `USER_CREDENTIALS_{PLATFORM}` - JSON with username/password (optional)
  - Example: `USER_CREDENTIALS_GITHUB='{"username": "user", "password": "pass"}'`

> **Note:** The default `GITHUB_TOKEN` secret provided by GitHub Actions is scoped to the current repository only and cannot write secrets to other repositories. For Cookie Guardian to work across multiple repositories, you must create a **Personal Access Token (PAT)** with `repo`, `workflow`, and `read:org` scopes, and add it as `CG_GITHUB_TOKEN` in your repository secrets.

## AI Vision Engine

The system uses a cascading vision engine factory:

1. **Gemini 2.0 Flash** (free tier, 1,500 RPM, no credit card)
2. **OpenRouter** (free vision models)
3. **Local Ollama** (LLaVA or llama3.2-vision)
4. **Rule-Based** (zero cost, zero API, DOM heuristics)

Configure via `config.yaml` or environment variables. The factory automatically tries each engine in order based on available API keys and connectivity.

## Anti-Detection Measures

- **Patchright**: Drop-in replacement for Playwright with built-in anti-detection patches
- **Stealth Launch Args**: Disables automation flags, isolations, sandbox for CI
- **CDP Evasion**: Patches `navigator.webdriver`, `chrome.runtime`, `WebGL`, `plugins`, `Notification.permission`
- **Canvas Noise**: Slight noise added to Canvas 2D reads
- **Fingerprint Randomization**: Rotates viewport, locale, timezone, user-agent, WebGL vendor/renderer per platform
- **Human Behavior**: Mouse Bezier curves, realistic typing with Gaussian delays, scroll emulation, random pauses
- **Header Randomization**: Realistic `Sec-Ch-Ua`, `Accept-Language`, and other headers per platform

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_browser_automation.py

# Run with verbose output
pytest -v
```

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Discovery     │────▶│  Analysis    │────▶│   Extraction     │
│  (GitHub API)   │     │(RepoAnalyzer)│     │(AI Vision Agent) │
└─────────────────┘     └──────────────┘     └──────────────────┘
                                                      │
                                                      ▼
                                               ┌──────────────────┐
                                               │ Screenshot Loop  │
                                               │ (Vision Engine)  │
                                               └──────────────────┘
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              ▼                       ▼                       ▼
                    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
                    │   Secret     │         │   Variable   │         │     WIPE     │
                    │ (Libsodium)  │         │  (Visible)   │         │(Memory Clear)│
                    └──────────────┘         └──────────────┘         └──────────────┘
```

## Development

### Project Structure

```
.
├── src/
│   ├── config.py              # Configuration management
│   ├── logger.py              # Redacted JSON logging
│   ├── database.py            # Metadata-only SQLite
│   ├── browser_automation.py  # Patchright async automation
│   ├── browser_context.py     # Persistent profile manager
│   ├── cleanup.py             # Secure data wiping
│   ├── discovery.py           # GitHub repo discovery with auth scoring
│   ├── decision_engine.py     # Zero-cost rule-based decision engine
│   ├── repo_analyzer.py       # Dynamic repo content analysis
│   ├── platform_registry.py   # Central platform metadata registry
│   ├── ai_vision_agent.py     # Screenshot loop orchestrator
│   ├── action_executor.py     # Action-to-patchright translator
│   ├── secrets_manager.py     # GitHub Secrets + Variables injection
│   ├── warp_manager.py        # WARP CLI wrapper (sync + async)
│   ├── retry_manager.py       # Tenacity retry with WARP rotation
│   ├── human_behavior.py      # Human-like typing / mouse / scroll
│   ├── stealth_config.py      # Stealth JS patches and fingerprints
│   ├── captcha_detector.py    # CAPTCHA / challenge detection
│   ├── header_fingerprinter.py # Randomized request headers
│   ├── vision_engines/        # AI vision engine implementations
│   │   ├── __init__.py        # Factory
│   │   ├── base.py            # Abstract base class
│   │   ├── models.py          # Dataclasses and enums
│   │   ├── gemini_engine.py   # Gemini 2.0 Flash free tier
│   │   ├── openrouter_engine.py # OpenRouter free vision fallback
│   │   ├── local_engine.py    # Ollama local vision fallback
│   │   └── rule_engine.py     # DOM selector heuristic fallback
│   ├── platform_logins/       # Platform-specific login modules (legacy)
│   │   ├── base.py
│   │   ├── github.py
│   │   ├── gitlab.py
│   │   ├── google.py
│   │   ├── aws.py
│   │   └── azure.py
│   └── orchestrator.py        # Main async workflow
├── scripts/
│   ├── init_db.py             # Database initialization
│   ├── test_warp.py           # WARP connection test
│   └── validate_setup.py      # Setup validation
├── tests/                     # Test suite
├── .github/workflows/         # CI/CD workflows
├── config.yaml                # Configuration
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## License

MIT
