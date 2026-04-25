from __future__ import annotations

from typing import Dict, Type

from src.platform_logins.base import BasePlatformLogin
from src.platform_logins.github import GitHubLogin
from src.platform_logins.gitlab import GitLabLogin
from src.platform_logins.google import GoogleLogin
from src.platform_logins.aws import AWSLogin
from src.platform_logins.azure import AzureLogin

_REGISTRY: Dict[str, Type[BasePlatformLogin]] = {
    "github": GitHubLogin,
    "gitlab": GitLabLogin,
    "google": GoogleLogin,
    "aws": AWSLogin,
    "azure": AzureLogin,
}


def get_platform_login(platform: str) -> BasePlatformLogin:
    """Get a platform-specific login handler.

    Args:
        platform: Platform name (e.g., "github", "gitlab").

    Returns:
        Instance of BasePlatformLogin for the platform.

    Raises:
        ValueError: If the platform is not supported.
    """
    platform = platform.lower()
    if platform not in _REGISTRY:
        raise ValueError(f"Unsupported platform: {platform}")
    return _REGISTRY[platform]()
