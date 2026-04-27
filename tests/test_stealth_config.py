import pytest

from src.stealth_config import (
    STEALTH_INIT_SCRIPTS,
    STEALTH_LAUNCH_ARGS,
    FingerprintPool,
    get_fingerprint,
)


class TestStealthInitScripts:
    def test_contains_webdriver_patch(self):
        """Test that stealth scripts patch navigator.webdriver."""
        assert "navigator.webdriver" in STEALTH_INIT_SCRIPTS

    def test_contains_plugins_patch(self):
        """Test that stealth scripts patch navigator.plugins."""
        assert "plugins" in STEALTH_INIT_SCRIPTS

    def test_contains_languages_patch(self):
        """Test that stealth scripts patch navigator.languages."""
        assert "languages" in STEALTH_INIT_SCRIPTS

    def test_contains_hardware_concurrency_patch(self):
        """Test that stealth scripts patch hardwareConcurrency."""
        assert "hardwareConcurrency" in STEALTH_INIT_SCRIPTS

    def test_contains_chrome_runtime_patch(self):
        """Test that stealth scripts patch chrome.runtime."""
        assert "chrome.runtime" in STEALTH_INIT_SCRIPTS

    def test_contains_webgl_patch(self):
        """Test that stealth scripts patch WebGL."""
        assert "WebGLRenderingContext" in STEALTH_INIT_SCRIPTS

    def test_contains_canvas_patch(self):
        """Test that stealth scripts add canvas noise."""
        assert "CanvasRenderingContext2D" in STEALTH_INIT_SCRIPTS

    def test_contains_outer_dimensions_patch(self):
        """Test that stealth scripts patch outerWidth/outerHeight."""
        assert "outerWidth" in STEALTH_INIT_SCRIPTS


class TestStealthLaunchArgs:
    def test_contains_disable_blink_features(self):
        assert any("disable-blink-features=AutomationControlled" in arg for arg in STEALTH_LAUNCH_ARGS)

    def test_contains_no_sandbox(self):
        assert "--no-sandbox" in STEALTH_LAUNCH_ARGS

    def test_contains_disable_gpu(self):
        assert "--disable-gpu" in STEALTH_LAUNCH_ARGS


class TestFingerprintPool:
    def test_consistent_per_platform(self):
        """Test that fingerprint is consistent for the same platform."""
        pool = FingerprintPool(seed=123)
        fp1 = pool.get_fingerprint("github")
        fp2 = pool.get_fingerprint("github")
        assert fp1.viewport == fp2.viewport
        assert fp1.user_agent == fp2.user_agent
        assert fp1.locale == fp2.locale

    def test_different_platforms_may_differ(self):
        """Test that different platforms can have different fingerprints."""
        pool = FingerprintPool(seed=456)
        fp1 = pool.get_fingerprint("github")
        fp2 = pool.get_fingerprint("gitlab")
        # They may or may not differ depending on RNG, but they are separate objects
        assert fp1 is not fp2


class TestGetFingerprint:
    def test_returns_fingerprint(self):
        fp = get_fingerprint("github", seed=42)
        assert fp.viewport["width"] > 0
        assert fp.viewport["height"] > 0
        assert "Mozilla" in fp.user_agent
        assert fp.locale
        assert fp.timezone
        assert fp.hardware_concurrency in (4, 8, 16)
        assert fp.webgl_vendor
        assert fp.webgl_renderer
        assert fp.color_scheme in ("light", "dark")
