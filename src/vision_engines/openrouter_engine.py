from __future__ import annotations

import json
import logging

import httpx

from src.vision_engines.base import VisionEngine
from src.vision_engines.models import AgentAction, VisionContext

logger = logging.getLogger("vision-engine")


class OpenRouterVisionEngine(VisionEngine):
    """OpenRouter free vision model fallback."""

    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-exp:free") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"

    async def analyze_screenshot(self, screenshot_b64: str, context: VisionContext) -> AgentAction:
        prompt = self._build_prompt(context)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}"},
                        },
                    ],
                }
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return self._parse_response(text)
        except Exception as exc:
            logger.warning(f"OpenRouter vision call failed: {exc}")
            return AgentAction(
                thought=f"OpenRouter error: {exc}",
                action="ERROR",
                confidence=0.0,
            )

    def _build_prompt(self, context: VisionContext) -> str:
        history_text = ""
        if context.history:
            history_text = "Previous actions:\n" + "\n".join(
                f"- {h.get('action')} {h.get('target', '')}" for h in context.history[-5:]
            )

        return (
            f"You are an AI browser automation agent. Goal: {context.goal}\n"
            f"Current URL: {context.url}\n"
            f"Platform: {context.platform}\n"
            f"{history_text}\n\n"
            "Analyze the screenshot and return a JSON object with:\n"
            "- thought: brief reasoning\n"
            "- action: one of [CLICK, TYPE, SCROLL, WAIT, NAVIGATE, DETECTED_2FA, DETECTED_CAPTCHA, LOGIN_SUCCESS, ERROR]\n"
            "- target: CSS selector or element description (if applicable)\n"
            "- value: text to type or URL to navigate (if applicable)\n"
            "- confidence: 0.0 to 1.0\n\n"
            "Return ONLY valid JSON. No markdown."
        )

    def _parse_response(self, text: str) -> AgentAction:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            data = json.loads(text)
            return AgentAction.from_dict(data)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    data = json.loads(text[start : end + 1])
                    return AgentAction.from_dict(data)
                except json.JSONDecodeError:
                    pass
            return AgentAction(
                thought=f"Failed to parse JSON from: {text[:200]}",
                action="ERROR",
                confidence=0.0,
            )
