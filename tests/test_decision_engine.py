import pytest

from src.decision_engine import DecisionEngine, Decision, GlmEngine, GlmDecision


class TestDecisionEngine:
    def test_decision_engine_extract_when_platforms_detected(self):
        """Test extract decision when platforms are detected with high confidence."""
        engine = DecisionEngine()
        from src.repo_analyzer import TargetPlatform
        platforms = [
            TargetPlatform(name="github", login_url="https://github.com/login", cookie_domain=".github.com", confidence=0.8),
        ]
        decision = engine.decide("test/repo", None, platforms)
        assert decision.action == "extract"
        assert "0.80" in decision.reason or "0.8" in decision.reason

    def test_decision_engine_skip_when_no_platforms_low_confidence(self):
        """Test skip decision when no platforms and no auth keywords."""
        engine = DecisionEngine()
        decision = engine.decide("test/repo", "A simple static site.", [])
        assert decision.action == "skip"

    def test_decision_engine_extract_when_auth_keywords(self):
        """Test extract decision when auth keywords found in description."""
        engine = DecisionEngine()
        decision = engine.decide("test/repo", "API scraper with token authentication", [])
        assert decision.action == "extract"

    def test_decision_engine_threshold(self):
        """Test that confidence threshold is respected."""
        engine = DecisionEngine()
        from src.repo_analyzer import TargetPlatform
        platforms = [
            TargetPlatform(name="github", login_url="https://github.com/login", cookie_domain=".github.com", confidence=0.1),
        ]
        decision = engine.decide("test/repo", "static site", platforms)
        # Below threshold, falls back to auth keyword check
        assert decision.action == "skip"


class TestGlmEngineBackwardCompatibility:
    def test_glm_engine_is_decision_engine(self):
        """Test that GlmEngine inherits from DecisionEngine."""
        engine = GlmEngine()
        assert isinstance(engine, DecisionEngine)

    def test_glm_decision_is_decision(self):
        """Test that GlmDecision is an alias for Decision."""
        assert GlmDecision is Decision

    def test_should_extract_cookies_legacy(self):
        """Test legacy should_extract_cookies method."""
        engine = GlmEngine()
        decision = engine.should_extract_cookies("test/github-repo")
        assert decision.action == "extract"

    def test_glm_engine_accepts_legacy_params(self):
        """Test that GlmEngine accepts old constructor params."""
        engine = GlmEngine(
            api_url="https://example.com",
            api_key="test-key",
            model="test-model",
            monthly_budget_usd=0.5,
        )
        assert engine.api_url == "https://example.com"
        assert engine.api_key == "test-key"
        assert engine.model == "test-model"
        assert engine.monthly_budget_usd == 0.5
