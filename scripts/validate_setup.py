#!/usr/bin/env python3
"""Validate Cookie Guardian setup.

This script checks that all required configuration and dependencies are in place.
"""

import json
import sys

from src.config import load_config, get_env_value


def check_env_var(name: str, required: bool = True) -> tuple[bool, str]:
    """Check if an environment variable is set."""
    value = get_env_value(name)
    if value:
        return True, f"✓ {name} is set"
    elif required:
        return False, f"✗ {name} is REQUIRED but not set"
    else:
        return True, f"○ {name} is optional and not set"


def check_config() -> list[tuple[bool, str]]:
    """Check configuration file."""
    try:
        config = load_config()
        return [
            (True, f"✓ Config loaded: {config.app.name}"),
            (True, f"✓ Database path: {config.storage.database_path}"),
            (True, f"✓ GitHub org: {config.github.org}"),
        ]
    except Exception as e:
        return [(False, f"✗ Failed to load config: {e}")]


def check_dependencies() -> list[tuple[bool, str]]:
    """Check Python dependencies."""
    results = []

    try:
        import yaml
        results.append((True, "✓ PyYAML installed"))
    except ImportError:
        results.append((False, "✗ PyYAML not installed"))

    try:
        import nacl
        results.append((True, "✓ PyNaCl installed (for GitHub Secrets)"))
    except ImportError:
        results.append((False, "✗ PyNaCl not installed"))

    try:
        import playwright
        results.append((True, "✓ Playwright installed (for browser automation)"))
    except ImportError:
        results.append((False, "✗ Playwright not installed"))

    try:
        import httpx
        results.append((True, "✓ httpx installed"))
    except ImportError:
        results.append((False, "✗ httpx not installed"))

    return results


def main() -> int:
    """Run all validation checks."""
    print("=" * 60)
    print("Cookie Guardian Setup Validation")
    print("=" * 60)
    print()

    all_passed = True

    # Check configuration
    print("Configuration:")
    print("-" * 40)
    for passed, message in check_config():
        print(f"  {message}")
        all_passed = all_passed and passed
    print()

    # Check required environment variables
    print("Required Environment Variables:")
    print("-" * 40)
    for passed, message in [
        check_env_var("GITHUB_TOKEN", required=True),
    ]:
        print(f"  {message}")
        all_passed = all_passed and passed
    print()

    # Check optional environment variables
    print("Optional Environment Variables:")
    print("-" * 40)
    for passed, message in [
        check_env_var("GLM_API_KEY", required=False),
        check_env_var("USER_CREDENTIALS_GITHUB", required=False),
        check_env_var("USER_CREDENTIALS_GITLAB", required=False),
    ]:
        print(f"  {message}")
    print()

    # Check dependencies
    print("Dependencies:")
    print("-" * 40)
    for passed, message in check_dependencies():
        print(f"  {message}")
        all_passed = all_passed and passed
    print()

    # Print summary
    print("=" * 60)
    if all_passed:
        print("✓ All required checks passed!")
        print()
        print("You can now run the orchestrator:")
        print("  python -m src.orchestrator")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
