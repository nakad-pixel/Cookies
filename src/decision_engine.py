from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.repo_analyzer import TargetPlatform


@dataclass
class Decision:
    action: str
    reason: str


class DecisionEngine:
    """Pure rule-based decision engine for repo analysis. Zero cost, zero API calls."""

    CONFIDENCE_THRESHOLD = 0.3

    def decide(
        self,
        repo_name: str,
        description: str | None,
        platforms_detected: List[TargetPlatform],
    ) -> Decision:
        """Decide whether to extract cookies for a repository.

        Args:
            repo_name: Full repository name.
            description: Optional repository description.
            platforms_detected: Platforms detected by RepoAnalyzer.

        Returns:
            Decision with action "extract" or "skip".
        """
        if platforms_detected:
            max_confidence = max(p.confidence for p in platforms_detected)
            if max_confidence >= self.CONFIDENCE_THRESHOLD:
                return Decision(
                    action="extract",
                    reason=f"Detected {len(platforms_detected)} platforms with confidence {max_confidence:.2f}",
                )

        text = f"{repo_name} {description or ''}".lower()
        auth_keywords = ["api", "scrap", "auth", "login", "session", "cookie", "token", "bot", "automation"]
        has_auth = any(kw in text for kw in auth_keywords)

        if has_auth:
            return Decision(
                action="extract",
                reason="Auth-related keywords found in repository metadata",
            )

        return Decision(
            action="skip",
            reason="No platforms detected and no auth indicators found",
        )


# Backward compatibility alias
class GlmEngine(DecisionEngine):
    """Backward-compatible alias for DecisionEngine."""

    def __init__(self, api_url: str = "", api_key: str | None = None, model: str = "", monthly_budget_usd: float = 0.0) -> None:
        super().__init__()
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.monthly_budget_usd = monthly_budget_usd
        self.cache: Dict[str, Decision] = {}

    def should_extract_cookies(self, repo_name: str, repo_description: str | None = None) -> Decision:
        """Legacy method signature for compatibility."""
        return self.decide(repo_name, repo_description, [])

    def decide(self, prompt: str | None = None, repo_name: str = "", repo_description: str | None = None, platforms_detected: List[TargetPlatform] | None = None) -> Decision:
        """Overloaded decide for backward compat."""
        if platforms_detected is not None:
            return super().decide(repo_name or (prompt or ""), repo_description, platforms_detected)
        text = f"{repo_name or (prompt or '')} {repo_description or ''}".lower()
        return super().decide(repo_name or (prompt or ""), repo_description, [])


# Backward compatibility for GlmDecision
GlmDecision = Decision
