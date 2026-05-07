from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass(frozen=True)
class AppConfig:
    name: str
    max_concurrency: int
    shard_id: int
    shard_total: int
    profile_dir: str
    max_retries: int
    har_dir: str
    tracing_dir: str
    enable_har: bool
    enable_tracing: bool


@dataclass(frozen=True)
class GitHubConfig:
    api_url: str
    graphql_url: str
    org: str
    token_env: str


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    json: bool


@dataclass(frozen=True)
class StorageConfig:
    """Storage configuration - NO encryption keys, metadata only."""
    database_path: str


@dataclass(frozen=True)
class AiVisionConfig:
    engine: str
    gemini_api_key_env: str
    openrouter_api_key_env: str
    ollama_url: str
    max_steps: int
    screenshot_max_width: int


@dataclass(frozen=True)
class WarpConfig:
    connect_timeout_sec: int
    rotate_interval_sec: int


@dataclass(frozen=True)
class CredentialsConfig:
    """Configuration for credential environment variable names.

    USER_CREDENTIALS_{PLATFORM} should contain JSON with username and password.
    Example: USER_CREDENTIALS_GITHUB='{"username": "user", "password": "pass"}'
    """
    prefix: str = "USER_CREDENTIALS"


@dataclass(frozen=True)
class Config:
    app: AppConfig
    github: GitHubConfig
    logging: LoggingConfig
    storage: StorageConfig
    ai_vision: AiVisionConfig
    warp: WarpConfig
    credentials: CredentialsConfig


def _resolve_config_path() -> Path:
    """Resolve config.yaml using env var, package-relative, or CWD-relative discovery."""
    env_path = os.environ.get("COOKIE_GUARDIAN_CONFIG")
    if env_path:
        env_file = Path(env_path)
        if env_file.is_file():
            return env_file
        raise FileNotFoundError(
            f"COOKIE_GUARDIAN_CONFIG is set but file not found: {env_file.resolve()}\n"
            f"Please check the path or unset the variable to use automatic discovery."
        )

    package_relative = Path(__file__).resolve().parent.parent / "config.yaml"
    if package_relative.is_file():
        return package_relative

    cwd_relative = Path.cwd() / "config.yaml"
    if cwd_relative.is_file():
        return cwd_relative

    raise FileNotFoundError(
        "config.yaml not found. Searched in:\n"
        f"  1. Package-relative: {package_relative}\n"
        f"  2. CWD-relative:     {cwd_relative}\n"
        "\n"
        "To fix this:\n"
        "  • Copy config.yaml.example to config.yaml and edit it, or\n"
        "  • Set COOKIE_GUARDIAN_CONFIG=/path/to/config.yaml"
    )


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_config(path: Path | None = None) -> Config:
    config_path = path or _resolve_config_path()
    raw = _load_yaml(config_path)

    app = raw.get("app", {})
    github = raw.get("github", {})
    logging_cfg = raw.get("logging", {})
    storage = raw.get("storage", {})
    ai_vision = raw.get("ai_vision", {})
    warp = raw.get("warp", {})
    credentials = raw.get("credentials", {})

    return Config(
        app=AppConfig(
            name=app.get("name", "cookie-guardian"),
            max_concurrency=int(app.get("max_concurrency", 3)),
            shard_id=int(app.get("shard_id", 0)),
            shard_total=int(app.get("shard_total", 1)),
            profile_dir=str(app.get("profile_dir", "data/profiles")),
            max_retries=int(app.get("max_retries", 3)),
            har_dir=str(app.get("har_dir", "data/har")),
            tracing_dir=str(app.get("tracing_dir", "data/traces")),
            enable_har=bool(app.get("enable_har", False)),
            enable_tracing=bool(app.get("enable_tracing", False)),
        ),
        github=GitHubConfig(
            api_url=github.get("api_url", "https://api.github.com"),
            graphql_url=github.get("graphql_url", "https://api.github.com/graphql"),
            org=github.get("org", ""),
            token_env=github.get("token_env", "CG_GITHUB_TOKEN"),
        ),
        logging=LoggingConfig(
            level=str(logging_cfg.get("level", "INFO")),
            json=bool(logging_cfg.get("json", True)),
        ),
        storage=StorageConfig(
            database_path=storage.get("database_path", "data/cookie_guardian.sqlite"),
        ),
        ai_vision=AiVisionConfig(
            engine=ai_vision.get("engine", "gemini"),
            gemini_api_key_env=ai_vision.get("gemini_api_key_env", "GEMINI_API_KEY"),
            openrouter_api_key_env=ai_vision.get("openrouter_api_key_env", "OPENROUTER_API_KEY"),
            ollama_url=ai_vision.get("ollama_url", "http://localhost:11434"),
            max_steps=int(ai_vision.get("max_steps", 30)),
            screenshot_max_width=int(ai_vision.get("screenshot_max_width", 800)),
        ),
        warp=WarpConfig(
            connect_timeout_sec=int(warp.get("connect_timeout_sec", 30)),
            rotate_interval_sec=int(warp.get("rotate_interval_sec", 900)),
        ),
        credentials=CredentialsConfig(
            prefix=credentials.get("prefix", "USER_CREDENTIALS"),
        ),
    )


def get_env_value(env_key: str, default: str | None = None) -> str | None:
    """Get a value from environment variables."""
    value = os.getenv(env_key, default)
    return value if value not in ("", None) else default


def get_credentials_for_platform(platform: str, config: Config | None = None) -> Dict[str, str] | None:
    """Get credentials for a platform from environment variables.

    First checks USER_CREDENTIALS env var for a unified JSON object mapping
    platform names to credential dicts. Falls back to USER_CREDENTIALS_{PLATFORM}.

    Args:
        platform: The platform name (e.g., "github", "gitlab")
        config: Optional config object

    Returns:
        Dict with 'username' and 'password' or None if not found
    """
    if config is None:
        config = load_config()

    # Try unified credentials first
    unified_json = get_env_value("USER_CREDENTIALS")
    if unified_json:
        try:
            creds_map = json.loads(unified_json)
            if isinstance(creds_map, dict) and platform.lower() in creds_map:
                entry = creds_map[platform.lower()]
                return {"username": entry.get("username", ""), "password": entry.get("password", "")}
        except json.JSONDecodeError:
            pass

    # Fall back to per-platform env var
    env_var = f"{config.credentials.prefix}_{platform.upper()}"
    credentials_json = get_env_value(env_var)
    if not credentials_json:
        return None

    try:
        creds = json.loads(credentials_json)
        return {"username": creds.get("username", ""), "password": creds.get("password", "")}
    except json.JSONDecodeError:
        return None


def get_github_token(config: Config | None = None) -> str | None:
    """Get the GitHub token with backward compatibility.

    Checks CG_GITHUB_TOKEN first, then falls back to GITHUB_TOKEN with a warning.

    Args:
        config: Optional config object

    Returns:
        The token value or None if not found
    """
    if config is None:
        config = load_config()

    token = get_env_value(config.github.token_env)
    if token:
        return token

    # Backward compatibility: fallback to legacy GITHUB_TOKEN
    fallback = get_env_value("GITHUB_TOKEN")
    if fallback:
        warnings.warn(
            "GITHUB_TOKEN is deprecated. Use CG_GITHUB_TOKEN instead. "
            "GITHUB_TOKEN is a reserved secret in GitHub Actions and is repo-scoped, "
            "so it cannot inject secrets into other repositories.",
            stacklevel=2,
        )
        return fallback

    return None
