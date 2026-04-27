from __future__ import annotations

from abc import ABC, abstractmethod

from src.vision_engines.models import AgentAction, VisionContext


class VisionEngine(ABC):
    """Abstract base class for AI vision engines."""

    @abstractmethod
    async def analyze_screenshot(self, screenshot_b64: str, context: VisionContext) -> AgentAction:
        """Analyze a screenshot and decide the next action.

        Args:
            screenshot_b64: Base64-encoded JPEG screenshot.
            context: Current vision context (URL, goal, history, platform).

        Returns:
            AgentAction with the next step.
        """
        ...
