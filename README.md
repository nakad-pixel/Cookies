# Cookie Guardian

A simplified, production-ready cookie management system for GitHub repositories. **No 2FA support** - the system cleanly skips accounts that require two-factor authentication.

## Key Features

- **Ephemeral Cookie Handling**: Cookies exist in memory only during extraction, then are immediately injected to GitHub Secrets and wiped
- **2FA Detection**: Automatically detects and skips accounts requiring 2FA with clear logging
- **No Local Encryption**: No encryption keys needed - sensitive data never touches disk
- **Metadata-Only Database**: SQLite stores only repository names and timestamps, never cookie values
- **Redacted Logging**: All logs are automatically redacted to remove sensitive values
- **Stealth Browser Automation**: Uses Playwright with anti-detection measures
- **WARP IP Rotation**: Optional Cloudflare WARP integration for IP rotation

## Limitations

⚠️ **This system does NOT support 2FA/MFA authentication.**

If a platform requires 2FA, the system will:
1. Detect the 2FA requirement
2. Log: "2FA detected on {platform} - skipping (2FA not supported)"
3. Move to the next repository

## Quick Start

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Initialize database (metadata only)
python scripts/init_db.py

# Set required environment variables
export GITHUB_TOKEN="your-github-token"
export GLM_API_KEY="your-glm-api-key"  # Optional, for AI analysis

# Optional: Set credentials for authenticated platforms
export USER_CREDENTIALS_GITHUB='{"username": "user", "password": "pass"}'

# Run the orchestrator
python -m src.orchestrator
```

## Configuration

Edit `config.yaml` to adjust settings:

```yaml
github:
  org: your-org-name
  token_env: GITHUB_TOKEN

logging:
  level: INFO
  json: true

storage:
  database_path: data/cookie_guardian.sqlite  # Metadata only
```

## Security Model

### Data Flow

1. **Discovery**: Scan repositories to identify cookie requirements
2. **Extraction**: Extract cookies into memory only (never written to disk)
3. **Injection**: Immediately inject cookies to GitHub Secrets via API
4. **Cleanup**: Securely wipe all cookie values from memory

### What Gets Stored

- ✅ Repository names and URLs
- ✅ Extraction timestamps and success/failure status
- ✅ Cookie count and 2FA detection results
- ❌ **Cookie values are NEVER stored locally**

### GitHub Secrets

The system injects cookies to GitHub Secrets using Libsodium sealed boxes (required by GitHub API). Secrets are named:
- `COOKIES_{REPO_NAME}` - Contains JSON array of cookies

## Required GitHub Secrets

Set these in your repository's GitHub Secrets:

- `GITHUB_TOKEN` - GitHub API token with repo access
- `GLM_API_KEY` - API key for GLM-4-Air (optional)
- `USER_CREDENTIALS_{PLATFORM}` - JSON with username/password (optional)
  - Example: `USER_CREDENTIALS_GITHUB='{"username": "user", "password": "pass"}'`

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
│   ├── browser_automation.py  # Playwright with 2FA detection
│   ├── cleanup.py             # Secure data wiping
│   ├── discovery.py           # GitHub repo discovery
│   ├── glm_engine.py          # AI decision engine
│   ├── secrets_manager.py     # GitHub Secrets injection
│   ├── warp_manager.py        # WARP CLI wrapper
│   ├── utils.py               # Utility functions
│   └── orchestrator.py        # Main workflow
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
