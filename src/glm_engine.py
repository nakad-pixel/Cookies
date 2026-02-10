from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict

import httpx


@dataclass
class GlmDecision:
    action: str
    reason: str


class GlmEngine:
    """Simplified GLM-4-Air decision engine for repository analysis.

    This engine provides AI-powered decisions but uses fail-fast behavior:
    - If API fails, returns a fallback decision
    - No complex retry logic
    - Results are cached to minimize API calls
    """

    def __init__(self, api_url: str, api_key: str | None, model: str, monthly_budget_usd: float) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.monthly_budget_usd = monthly_budget_usd
        self.cache: Dict[str, GlmDecision] = {}

    def decide(self, prompt: str) -> GlmDecision:
        """Make a decision based on the prompt.

        Uses caching to minimize API calls. Falls back to rule-based
        decision if API key is missing or call fails.

        Args:
            prompt: The decision prompt

        Returns:
            GlmDecision with action and reason
        """
        cache_key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]

        # If no API key, use fallback
        if not self.api_key:
            decision = GlmDecision(action="fallback", reason="Missing API key, using rule-based decision")
            self.cache[cache_key] = decision
            return decision

        # Try API call
        try:
            decision = self._call_api(prompt)
            self.cache[cache_key] = decision
            return decision
        except Exception as e:
            # Fail fast - return fallback on any error
            decision = GlmDecision(action="fallback", reason=f"API call failed: {str(e)[:50]}")
            self.cache[cache_key] = decision
            return decision

    def _call_api(self, prompt: str) -> GlmDecision:
        """Call the GLM API.

        Args:
            prompt: The decision prompt

        Returns:
            Parsed GlmDecision

        Raises:
            httpx.HTTPError: On API failure
            json.JSONDecodeError: On invalid response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a cookie guardian decision engine. Respond with JSON containing 'action' and 'reason' fields."
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        response = httpx.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed: Dict[str, Any] = json.loads(content)

        return GlmDecision(
            action=str(parsed.get("action", "unknown")),
            reason=str(parsed.get("reason", ""))
        )

    def should_extract_cookies(self, repo_name: str, repo_description: str | None = None) -> GlmDecision:
        """Determine if a repository likely needs cookie extraction.

        Args:
            repo_name: Full repository name (owner/repo)
            repo_description: Optional repository description

        Returns:
            GlmDecision with action "extract" or "skip"
        """
        description = repo_description or "No description"
        prompt = f"""Analyze repository: {repo_name}
Description: {description}

Does this repository likely require authentication cookies for external services?
Consider: API integrations, data scraping, automated testing, etc.

Respond with JSON:
{{
    "action": "extract" or "skip",
    "reason": "brief explanation"
}}"""
        return self.decide(prompt)
