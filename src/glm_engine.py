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
    def __init__(self, api_url: str, api_key: str | None, model: str, monthly_budget_usd: float) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.monthly_budget_usd = monthly_budget_usd
        self.cache: Dict[str, GlmDecision] = {}

    def decide(self, prompt: str) -> GlmDecision:
        cache_key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        if not self.api_key:
            decision = GlmDecision(action="fallback", reason="Missing API key, using rule-based decision")
            self.cache[cache_key] = decision
            return decision
        decision = self._call_api(prompt)
        self.cache[cache_key] = decision
        return decision

    def _call_api(self, prompt: str) -> GlmDecision:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a cookie guardian decision engine. Respond with JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        response = httpx.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed: Dict[str, Any] = json.loads(content)
        return GlmDecision(action=str(parsed.get("action", "unknown")), reason=str(parsed.get("reason", "")))
