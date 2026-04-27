#!/usr/bin/env python3
"""Validate Cookie Guardian setup.

This script checks that all required configuration and dependencies are in place.
"""

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
        import patchright
        results.append((True, "✓ Patchright installed (for browser automation)"))
    except ImportError:
        results.append((False, "✗ Patchright not installed"))

    try:
        import httpx
        results.append((True, "✓ httpx installed"))
    except ImportError:
        results.append((False, "✗ httpx not installed"))

    try:
        from PIL import Image
        results.append((True, "✓ Pillow installed (for screenshot compression)"))
    except ImportError:
        results.append((False, "✗ Pillow not installed"))

    try:
        import google.generativeai
        results.append((True, "✓ google-generativeai installed (for Gemini AI vision)"))
    except ImportError:
        results.append((False, "✗ google-generativeai not installed"))

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
    primary_passed, primary_message = check_env_var("CG_GITHUB_TOKEN", required=True)
    print(f"  {primary_message}")
    all_passed = all_passed and primary_passed

    if not primary_passed:
        fallback_value = get_env_value("GITHUB_TOKEN")
        if fallback_value:
            warnings.warn(
                "GITHUB_TOKEN is set but CG_GITHUB_TOKEN is preferred. "
                "GITHUB_TOKEN is a reserved secret in GitHub Actions and is repo-scoped, "
                "so it cannot inject secrets into other repositories. "
                "Create a personal access token and set it as CG_GITHUB_TOKEN.",
                stacklevel=1,
            )
            print("  ⚠ GITHUB_TOKEN fallback detected (not recommended for cross-repo injection)")
    print()

    # Check optional environment variables
    print("Optional Environment Variables:")
    print("-" * 40)
    for passed, message in [
        check_env_var("GEMINI_API_KEY", required=False),
        check_env_var("OPENROUTER_API_KEY", required=False),
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
