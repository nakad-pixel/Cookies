# Cookie Guardian

A production-ready, zero-cost cookie management system for GitHub repositories. Uses `patchright` for advanced anti-detection browser automation, human-like behavioral patterns, persistent browser profiles, and rule-based decision-making with no paid AI APIs.

## Key Features

- **Ephemeral Cookie Handling**: Cookies exist in memory only during extraction, then are immediately injected to GitHub Secrets and wiped
- **2FA Detection**: Automatically detects and skips accounts requiring 2FA with clear logging
- **CAPTCHA Detection**: Detects reCAPTCHA, hCaptcha, Cloudflare Turnstile, and JS challenges
- **Persistent Browser Profiles**: Session state persists per platform across runs (reduces login friction)
- **Production-Grade Anti-Detection**: `patchright` + stealth args + CDP evasion + realistic fingerprinting
- **Human-Like Behavior**: Bezier mouse curves, realistic typing, random waits, scroll emulation
- **Zero Cost**: No paid AI APIs — rule-based decisions only
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
export GITHUB_TOKEN="your-github-token"

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
  token_env: GITHUB_TOKEN

logging:
  level: INFO
  json: true

storage:
  database_path: data/cookie_guardian.sqlite  # Metadata only

warp:
  connect_timeout_sec: 30
  rotate_interval_sec: 900
```

## Security Model

### Data Flow

1. **Discovery**: Scan repositories to identify cookie requirements using rule-based analysis
2. **Extraction**: Extract cookies into memory only (never written to disk)
3. **Injection**: Immediately inject cookies to GitHub Secrets via API
4. **Cleanup**: Securely wipe all cookie values from memory

### What Gets Stored

- ✅ Repository names and URLs
- ✅ Extraction timestamps and success/failure status
- ✅ Cookie count, 2FA, and CAPTCHA detection results
- ❌ **Cookie values are NEVER stored locally**

### Browser Profiles

Persistent browser profiles are stored in `data/profiles/{platform}/`. This includes session cookies and localStorage managed by the browser engine. Actual extracted cookie values remain in memory only during the extraction window and are wiped immediately after injection.

### GitHub Secrets

The system injects cookies to GitHub Secrets using Libsodium sealed boxes (required by GitHub API). Secrets are named:
- `COOKIES_{REPO_NAME}` - Contains JSON array of cookies

## Required GitHub Secrets

Set these in your repository's GitHub Secrets:

- `GITHUB_TOKEN` - GitHub API token with repo access
- `USER_CREDENTIALS_{PLATFORM}` - JSON with username/password (optional)
  - Example: `USER_CREDENTIALS_GITHUB='{"username": "user", "password": "pass"}'`

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
┌─────────────────┐     ┌──────────────┐     ┌────────────────┐
│   Discovery     │────▶│  Extraction  │────▶│   Injection    │
│  (GitHub API)   │     │  (Browser)   │     │ (GitHub API)   │
└─────────────────┘     └──────────────┘     └────────────────┘
                                                        │
                                                        ▼
                                               ┌────────────────┐
                                               │ GitHub Secrets │
                                               │ (Libsodium)    │
                                               └────────────────┘
                                                        │
                                                        ▼
                                               ┌────────────────┐
                                               │     WIPE       │
                                               │ (Memory Clear) │
                                               └────────────────┘
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
│   ├── glm_engine.py          # Zero-cost rule-based engine
│   ├── secrets_manager.py     # GitHub Secrets injection
│   ├── warp_manager.py        # WARP CLI wrapper (sync + async)
│   ├── retry_manager.py       # Tenacity retry with WARP rotation
│   ├── human_behavior.py      # Human-like typing / mouse / scroll
│   ├── stealth_config.py      # Stealth JS patches and fingerprints
│   ├── captcha_detector.py    # CAPTCHA / challenge detection
│   ├── header_fingerprinter.py # Randomized request headers
│   ├── platform_logins/       # Platform-specific login modules
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
