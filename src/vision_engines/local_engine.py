from __future__ import annotations

import json
import logging

import httpx

from src.vision_engines.base import VisionEngine
from src.vision_engines.models import AgentAction, VisionContext

logger = logging.getLogger("vision-engine")


class LocalVisionEngine(VisionEngine):
    """Local Ollama vision fallback using LLaVA or llama3.2-vision."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llava") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        # Quick connectivity check
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f"Ollama not reachable at {self.base_url}: {exc}") from exc

    async def analyze_screenshot(self, screenshot_b64: str, context: VisionContext) -> AgentAction:
        prompt = self._build_prompt(context)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [screenshot_b64],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate", json=payload
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "")
                return self._parse_response(text)
        except Exception as exc:
            logger.warning(f"Local Ollama vision call failed: {exc}")
            return AgentAction(
                thought=f"Local Ollama error: {exc}",
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
