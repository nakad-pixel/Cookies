from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PlatformMetadata:
    name: str
    domains: List[str]
    login_url: str
    cookie_domains: List[str]
    auth_indicators: List[str]
    sdk_packages: List[str]


PLATFORM_REGISTRY: Dict[str, PlatformMetadata] = {
    "linkedin": PlatformMetadata(
        name="linkedin",
        domains=["linkedin.com", "www.linkedin.com"],
        login_url="https://www.linkedin.com/",
        cookie_domains=[".linkedin.com", "www.linkedin.com"],
        auth_indicators=["li_at", "JSESSIONID"],
        sdk_packages=["linkedin-api", "linkedin-scraper"],
    ),
    "twitter": PlatformMetadata(
        name="twitter",
        domains=["twitter.com", "x.com"],
        login_url="https://x.com/",
        cookie_domains=[".twitter.com", ".x.com", "twitter.com", "x.com"],
        auth_indicators=["auth_token", "ct0"],
        sdk_packages=["tweepy", "twitter-api-client"],
    ),
    "facebook": PlatformMetadata(
        name="facebook",
        domains=["facebook.com", "www.facebook.com"],
        login_url="https://www.facebook.com/",
        cookie_domains=[".facebook.com", "www.facebook.com"],
        auth_indicators=["c_user", "xs"],
        sdk_packages=["facebook-sdk", "pyfacebook"],
    ),
    "instagram": PlatformMetadata(
        name="instagram",
        domains=["instagram.com", "www.instagram.com"],
        login_url="https://www.instagram.com/",
        cookie_domains=[".instagram.com", "www.instagram.com"],
        auth_indicators=["sessionid", "ds_user_id"],
        sdk_packages=["instaloader", "instagram-private-api"],
    ),
    "reddit": PlatformMetadata(
        name="reddit",
        domains=["reddit.com", "www.reddit.com"],
        login_url="https://www.reddit.com/",
        cookie_domains=[".reddit.com", "www.reddit.com"],
        auth_indicators=["reddit_session", "token_v2"],
        sdk_packages=["praw", "asyncpraw"],
    ),
    "tiktok": PlatformMetadata(
        name="tiktok",
        domains=["tiktok.com", "www.tiktok.com"],
        login_url="https://www.tiktok.com/",
        cookie_domains=[".tiktok.com", "www.tiktok.com"],
        auth_indicators=["sessionid", "msToken"],
        sdk_packages=["TikTokApi"],
    ),
    "pinterest": PlatformMetadata(
        name="pinterest",
        domains=["pinterest.com", "www.pinterest.com"],
        login_url="https://www.pinterest.com/",
        cookie_domains=[".pinterest.com", "www.pinterest.com"],
        auth_indicators=["_auth", "_pinterest_sess"],
        sdk_packages=["py3-pinterest"],
    ),
    "youtube": PlatformMetadata(
        name="youtube",
        domains=["youtube.com", "www.youtube.com"],
        login_url="https://www.youtube.com/",
        cookie_domains=[".youtube.com", ".google.com"],
        auth_indicators=["LOGIN_INFO", "APISID"],
        sdk_packages=["youtube-dl", "yt-dlp"],
    ),
    "netflix": PlatformMetadata(
        name="netflix",
        domains=["netflix.com", "www.netflix.com"],
        login_url="https://www.netflix.com/",
        cookie_domains=[".netflix.com", "www.netflix.com"],
        auth_indicators=["NetflixId", "SecureNetflixId"],
        sdk_packages=[],
    ),
    "spotify": PlatformMetadata(
        name="spotify",
        domains=["spotify.com", "open.spotify.com"],
        login_url="https://open.spotify.com/",
        cookie_domains=[".spotify.com", "open.spotify.com", "accounts.spotify.com"],
        auth_indicators=["sp_dc", "sp_key"],
        sdk_packages=["spotipy"],
    ),
    "github": PlatformMetadata(
        name="github",
        domains=["github.com", "api.github.com"],
        login_url="https://github.com/",
        cookie_domains=[".github.com", "github.com"],
        auth_indicators=["user_session", "dotcom_user"],
        sdk_packages=["PyGithub", "github3.py"],
    ),
    "gitlab": PlatformMetadata(
        name="gitlab",
        domains=["gitlab.com"],
        login_url="https://gitlab.com/",
        cookie_domains=[".gitlab.com", "gitlab.com"],
        auth_indicators=["_gitlab_session"],
        sdk_packages=["python-gitlab"],
    ),
    "google": PlatformMetadata(
        name="google",
        domains=["google.com", "accounts.google.com"],
        login_url="https://accounts.google.com/",
        cookie_domains=[".google.com", "accounts.google.com"],
        auth_indicators=["APISID", "SSID", "SAPISID"],
        sdk_packages=["google-api-python-client", "google-auth"],
    ),
    "aws": PlatformMetadata(
        name="aws",
        domains=["aws.amazon.com", "signin.aws.amazon.com"],
        login_url="https://aws.amazon.com/",
        cookie_domains=[".amazon.com", ".aws.amazon.com"],
        auth_indicators=["aws-userInfo", "aws-creds"],
        sdk_packages=["boto3", "botocore"],
    ),
    "azure": PlatformMetadata(
        name="azure",
        domains=["azure.com", "login.microsoftonline.com"],
        login_url="https://azure.com/",
        cookie_domains=[".microsoftonline.com", ".azure.com"],
        auth_indicators=["ESTSAUTH", "ESTSAUTHPERSISTENT"],
        sdk_packages=["azure-identity", "azure-mgmt-resource"],
    ),
}


def get_platform_metadata(name: str) -> Optional[PlatformMetadata]:
    """Get metadata for a known platform."""
    return PLATFORM_REGISTRY.get(name.lower())


def infer_login_url(domain: str) -> str:
    """Infer a starting (homepage) URL from a domain."""
    domain = domain.lower().strip()
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    return f"{domain.rstrip('/')}/"


def detect_platform_from_text(text: str) -> List[str]:
    """Detect platform names from free-form text."""
    text_lower = text.lower()
    found: List[str] = []
    for name, meta in PLATFORM_REGISTRY.items():
        for domain in meta.domains:
            if domain.lower() in text_lower:
                found.append(name)
                break
        if name not in found:
            for indicator in meta.auth_indicators:
                if indicator.lower() in text_lower:
                    found.append(name)
                    break
        if name not in found:
            for pkg in meta.sdk_packages:
                if pkg.lower() in text_lower:
                    found.append(name)
                    break
    return found
