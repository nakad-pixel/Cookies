import pytest

from src.platform_registry import (
    PLATFORM_REGISTRY,
    PlatformMetadata,
    get_platform_metadata,
    infer_login_url,
    detect_platform_from_text,
)


class TestPlatformRegistry:
    def test_registry_has_common_platforms(self):
        assert "github" in PLATFORM_REGISTRY
        assert "linkedin" in PLATFORM_REGISTRY
        assert "twitter" in PLATFORM_REGISTRY
        assert "google" in PLATFORM_REGISTRY
        assert "aws" in PLATFORM_REGISTRY
        assert "azure" in PLATFORM_REGISTRY

    def test_github_metadata(self):
        meta = PLATFORM_REGISTRY["github"]
        assert meta.login_url == "https://github.com/login"
        assert ".github.com" in meta.cookie_domains

    def test_get_platform_metadata_found(self):
        meta = get_platform_metadata("github")
        assert meta is not None
        assert meta.name == "github"

    def test_get_platform_metadata_not_found(self):
        meta = get_platform_metadata("nonexistent")
        assert meta is None

    def test_infer_login_url(self):
        url = infer_login_url("example.com")
        assert url == "https://example.com/login"

    def test_infer_login_url_with_https(self):
        url = infer_login_url("https://example.com")
        assert url == "https://example.com/login"

    def test_detect_platform_from_text(self):
        text = "This project uses linkedin.com and twitter.com APIs."
        found = detect_platform_from_text(text)
        assert "linkedin" in found
        assert "twitter" in found

    def test_detect_platform_from_text_with_sdk(self):
        text = "Requires spotipy and tweepy for API access."
        found = detect_platform_from_text(text)
        assert "spotify" in found
        assert "twitter" in found
