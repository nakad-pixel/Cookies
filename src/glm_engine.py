from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict


@dataclass
class GlmDecision:
    action: str
    reason: str


class GlmEngine:
    """Zero-cost rule-based decision engine replacing the paid GLM API.

    Uses keyword matching against repository metadata to decide whether
    cookie extraction is likely needed. No external API calls are made.
    """

    PLATFORM_KEYWORDS = [
        "github", "gitlab", "aws", "azure", "google", "gcp",
    ]

    AUTH_KEYWORDS = [
        "api", "scrap", "auth", "login", "session",
        "cookie", "token", "bot", "automation",
    ]

    def __init__(self, api_url: str = "", api_key: str | None = None, model: str = "", monthly_budget_usd: float = 0.0) -> None:
        # Keep signature for backward compatibility but ignore paid API params
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.monthly_budget_usd = monthly_budget_usd
        self.cache: Dict[str, GlmDecision] = {}

    def decide(self, prompt: str) -> GlmDecision:
        """Make a rule-based decision from a free-form prompt.

        Args:
            prompt: The decision prompt (usually contains repo name/URL).

        Returns:
            GlmDecision with action and reason.
        """
        cache_key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]

        decision = self._rule_based_decision(prompt)
        self.cache[cache_key] = decision
        return decision

    def should_extract_cookies(self, repo_name: str, repo_description: str | None = None) -> GlmDecision:
        """Determine if a repository likely needs cookie extraction.

        Args:
            repo_name: Full repository name (owner/repo).
            repo_description: Optional repository description.

        Returns:
            GlmDecision with action "extract" or "skip".
        """
        text = f"{repo_name} {repo_description or ''}".lower()
        return self._rule_based_decision(text)

    def _rule_based_decision(self, text: str) -> GlmDecision:
        text_lower = text.lower()

        has_platform = any(kw in text_lower for kw in self.PLATFORM_KEYWORDS)
        has_auth = any(kw in text_lower for kw in self.AUTH_KEYWORDS)

        if has_platform and has_auth:
            return GlmDecision(
                action="extract",
                reason="Repository metadata indicates platform + auth keywords",
            )
        if has_auth:
            return GlmDecision(
                action="extract",
                reason="Auth-related keywords found in repository metadata",
            )
        if has_platform:
            return GlmDecision(
                action="extract",
                reason="Platform keyword found; may require external auth",
            )
        return GlmDecision(
            action="skip",
            reason="No platform or auth indicators detected",
        )
