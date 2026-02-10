from __future__ import annotations

import os
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
    database_path: str
    encryption_key_env: str


@dataclass(frozen=True)
class GlmConfig:
    api_url: str
    api_key_env: str
    model: str
    monthly_budget_usd: float


@dataclass(frozen=True)
class WarpConfig:
    connect_timeout_sec: int
    rotate_interval_sec: int


@dataclass(frozen=True)
class Config:
    app: AppConfig
    github: GitHubConfig
    logging: LoggingConfig
    storage: StorageConfig
    glm: GlmConfig
    warp: WarpConfig


DEFAULT_CONFIG_PATH = Path("/home/engine/project/config.yaml")


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_config(path: Path | None = None) -> Config:
    config_path = path or DEFAULT_CONFIG_PATH
    raw = _load_yaml(config_path)

    app = raw.get("app", {})
    github = raw.get("github", {})
    logging_cfg = raw.get("logging", {})
    storage = raw.get("storage", {})
    glm = raw.get("glm", {})
    warp = raw.get("warp", {})

    return Config(
        app=AppConfig(
            name=app.get("name", "cookie-guardian"),
            max_concurrency=int(app.get("max_concurrency", 3)),
            shard_id=int(app.get("shard_id", 0)),
            shard_total=int(app.get("shard_total", 1)),
        ),
        github=GitHubConfig(
            api_url=github.get("api_url", "https://api.github.com"),
            graphql_url=github.get("graphql_url", "https://api.github.com/graphql"),
            org=github.get("org", ""),
            token_env=github.get("token_env", "GITHUB_TOKEN"),
        ),
        logging=LoggingConfig(
            level=str(logging_cfg.get("level", "INFO")),
            json=bool(logging_cfg.get("json", True)),
        ),
        storage=StorageConfig(
            database_path=storage.get("database_path", "data/cookie_guardian.sqlite"),
            encryption_key_env=storage.get("encryption_key_env", "COOKIE_GUARDIAN_KEY"),
        ),
        glm=GlmConfig(
            api_url=glm.get("api_url", "https://open.bigmodel.cn"),
            api_key_env=glm.get("api_key_env", "GLM_API_KEY"),
            model=glm.get("model", "glm-4-air"),
            monthly_budget_usd=float(glm.get("monthly_budget_usd", 0.2)),
        ),
        warp=WarpConfig(
            connect_timeout_sec=int(warp.get("connect_timeout_sec", 30)),
            rotate_interval_sec=int(warp.get("rotate_interval_sec", 900)),
        ),
    )


def get_env_value(env_key: str, default: str | None = None) -> str | None:
    value = os.getenv(env_key, default)
    return value if value not in ("", None) else default
