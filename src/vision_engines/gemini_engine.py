from __future__ import annotations

import json
import logging
from typing import Optional

from src.vision_engines.base import VisionEngine
from src.vision_engines.models import AgentAction, VisionContext

logger = logging.getLogger("vision-engine")


class GeminiVisionEngine(VisionEngine):
    """Gemini 2.0 Flash free-tier vision engine."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp") -> None:
        self.api_key = api_key
        self.model = model
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(model_name=model)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Gemini client: {exc}") from exc

    async def analyze_screenshot(self, screenshot_b64: str, context: VisionContext) -> AgentAction:
        try:
            import google.generativeai as genai
        except ImportError:
            return AgentAction(
                thought="google-generativeai not installed",
                action_type="ERROR",
                confidence=0.0,
            )

        prompt = self._build_prompt(context)

        try:
            response = await self._client.generate_content_async(
                [
                    prompt,
                    {"mime_type": "image/jpeg", "data": screenshot_b64},
                ]
            )
            text = response.text or ""
            return self._parse_response(text)
        except Exception as exc:
            logger.warning(f"Gemini vision call failed: {exc}")
            return AgentAction(
                thought=f"Gemini error: {exc}",
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
        # Strip markdown code blocks
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            data = json.loads(text)
            return AgentAction.from_dict(data)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
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
