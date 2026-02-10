from src.glm_engine import GlmEngine


def test_glm_fallback() -> None:
    engine = GlmEngine(api_url="http://example.com", api_key=None, model="glm", monthly_budget_usd=0.2)
    decision = engine.decide("test")
    assert decision.action == "fallback"
