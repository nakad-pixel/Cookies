from __future__ import annotations

import asyncio
import logging
from typing import Optional

from src.human_behavior import human_like_click, human_like_typing, random_human_wait, emulate_scroll
from src.logger import redact_sensitive_data
from src.vision_engines.models import ActionType, AgentAction

logger = logging.getLogger("action-executor")


class ActionExecutor:
    """Translates AgentAction into patchright commands."""

    def __init__(self, page, credentials: Optional[dict] = None) -> None:
        self.page = page
        self.credentials = credentials or {}

    async def execute(self, action: AgentAction) -> dict:
        """Execute an AgentAction on the page.

        Returns:
            Dict with 'success' bool and optional 'error' message.
        """
        try:
            result = await self._do_execute(action)
            return result
        except Exception as exc:
            logger.warning(f"Action execution failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def _do_execute(self, action: AgentAction) -> dict:
        action_type = action.action

        if action_type == ActionType.CLICK:
            return await self._execute_click(action)

        if action_type == ActionType.TYPE:
            return await self._execute_type(action)

        if action_type == ActionType.SCROLL:
            return await self._execute_scroll(action)

        if action_type == ActionType.WAIT:
            return await self._execute_wait(action)

        if action_type == ActionType.NAVIGATE:
            return await self._execute_navigate(action)

        if action_type in (ActionType.DETECTED_2FA, ActionType.DETECTED_CAPTCHA, ActionType.LOGIN_SUCCESS, ActionType.ERROR):
            # Terminal actions — no page interaction needed
            return {"success": True}

        return {"success": False, "error": f"Unknown action type: {action_type}"}

    async def _execute_click(self, action: AgentAction) -> dict:
        target = action.target
        if not target:
            return {"success": False, "error": "No target for CLICK"}

        try:
            locator = self.page.locator(target).first
            await locator.wait_for(timeout=5000)
            await human_like_click(self.page, target)
            await self.page.wait_for_load_state("networkidle")
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": f"Click failed: {exc}"}

    async def _execute_type(self, action: AgentAction) -> dict:
        target = action.target
        value = action.value
        if not target:
            return {"success": False, "error": "No target for TYPE"}

        # Substitute credentials placeholders
        if value == "{{username}}":
            value = self.credentials.get("username", "")
        elif value == "{{password}}":
            value = self.credentials.get("password", "")

        if not value:
            return {"success": False, "error": "No value to type"}

        try:
            locator = self.page.locator(target).first
            await locator.wait_for(timeout=5000)
            await human_like_typing(self.page, target, value)
            log_value = redact_sensitive_data(value)
            logger.info(f"Typed into {target}: {log_value}")
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": f"Type failed: {exc}"}

    async def _execute_scroll(self, action: AgentAction) -> dict:
        direction = action.value or "down"
        try:
            if direction == "down":
                await emulate_scroll(self.page, max_scrolls=3)
            else:
                await self.page.evaluate("window.scrollBy(0, -500)")
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": f"Scroll failed: {exc}"}

    async def _execute_wait(self, action: AgentAction) -> dict:
        seconds = 3.0
        try:
            seconds = float(action.value or "3")
        except ValueError:
            pass
        await random_human_wait(seconds - 1, seconds + 1)
        return {"success": True}

    async def _execute_navigate(self, action: AgentAction) -> dict:
        url = action.value
        if not url:
            return {"success": False, "error": "No URL for NAVIGATE"}
        try:
            await self.page.goto(url, wait_until="networkidle")
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": f"Navigate failed: {exc}"}
