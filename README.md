# Cookie Guardian

Cookie Guardian is an autonomous cookie management system that discovers, extracts, validates, and rotates authentication cookies across GitHub repositories. The implementation follows the specification in `PROMPT.md` with a modular, defensive architecture.

## Features
- State-machine orchestrator for discovery, extraction, injection, validation, and commit steps
- AES-256-GCM encryption for local artifacts
- Libsodium sealed boxes for GitHub Secrets
- SQLite (WAL mode) for resilient metadata storage
- Structured JSON logging
- Config-driven behavior with safe defaults

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python -m src.orchestrator
```

## Configuration
- Copy `.env.example` to `.env` and set required secrets.
- Adjust `config.yaml` for GitHub, GLM, and runtime settings.

## Testing

```bash
pytest
```

## Security
See [SECURITY.md](SECURITY.md) for security guidelines.
