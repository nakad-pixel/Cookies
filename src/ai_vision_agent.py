from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from src.action_executor import ActionExecutor
from src.captcha_detector import CaptchaDetector
from src.logger import log_2fa_detected
from src.vision_engines.base import VisionEngine
from src.vision_engines.models import ActionType, AgentAction, VisionContext

logger = logging.getLogger("ai-vision-agent")


try:
    from PIL import Image
except ImportError:
    Image = None


try:
    from patchright.async_api import Page
except ImportError:
    Page = None


@dataclass
class CookieData:
    name: str
    value: str
    domain: str
    expires: int | None = None
    secure: bool = True
    http_only: bool = True

    def wipe(self) -> None:
        from src.cleanup import SecureWiper
        SecureWiper.wipe_string(self.value)
        self.value = ""


@dataclass
class ExtractionResult:
    cookies: List[CookieData] = field(default_factory=list)
    has_2fa: bool = False
    has_captcha: bool = False
    success: bool = False
    error_message: Optional[str] = None

    def wipe_cookies(self) -> None:
        for cookie in self.cookies:
            cookie.wipe()
        self.cookies = []


class AiVisionAgent:
    """AI vision loop: screenshot -> analyze -> act -> repeat."""

    def __init__(
        self,
        vision_engine: VisionEngine,
        max_steps: int = 30,
        screenshot_max_width: int = 800,
    ) -> None:
        self.vision_engine = vision_engine
        self.max_steps = max_steps
        self.screenshot_max_width = screenshot_max_width

    async def run_extraction(
        self,
        page: Page,
        platform: str,
        credentials: dict,
        max_steps: Optional[int] = None,
    ) -> ExtractionResult:
        """Run the AI vision loop to log in and extract cookies.

        Args:
            page: Patchright page object.
            platform: Platform name.
            credentials: Dict with 'username' and 'password'.
            max_steps: Override max steps.

        Returns:
            ExtractionResult with cookies or failure status.
        """
        if Page is not None and not isinstance(page, Page):
            # Allow mocks in tests
            pass

        steps = max_steps or self.max_steps
        history: List[dict] = []
        executor = ActionExecutor(page, credentials)
        loop_detector: dict[tuple[str, str], int] = {}
        context = VisionContext(
            url=page.url if hasattr(page, "url") else "",
            goal=f"Log in to {platform} and extract session cookies",
            platform=platform,
            history=history,
        )

        for step in range(steps):
            # Screenshot
            screenshot_b64 = await self._take_screenshot(page)

            # DOM fallback: detect CAPTCHA
            captcha_task = asyncio.create_task(CaptchaDetector.detect_any(page))

            # Build context with latest page info
            try:
                title = await page.title()
                content = await page.content()
                context.url = page.url if hasattr(page, "url") else context.url
                context.history.append({
                    "step": step,
                    "page_title": title,
                    "page_content": content[:2000],  # Truncate for prompt size
                })
            except Exception:
                pass

            # AI analysis
            action = await self.vision_engine.analyze_screenshot(screenshot_b64, context)
            logger.info(
                f"Step {step}: {action.action.value} target={action.target} conf={action.confidence}"
            )

            # Wait for CAPTCHA detection
            captcha_result = await captcha_task
            if captcha_result.present and action.action not in (
                ActionType.DETECTED_CAPTCHA,
                ActionType.LOGIN_SUCCESS,
            ):
                logger.warning(f"DOM CAPTCHA fallback detected: {captcha_result.type}")
                action = AgentAction(
                    thought=f"DOM fallback detected {captcha_result.type}",
                    action=ActionType.DETECTED_CAPTCHA,
                    confidence=0.9,
                )

            # Loop detection
            action_key = (action.action.value, action.target)
            loop_detector[action_key] = loop_detector.get(action_key, 0) + 1
            if loop_detector[action_key] > 3:
                return ExtractionResult(
                    success=False,
                    error_message=f"Loop detected for action {action_key}",
                )

            # Low confidence -> wait and retry
            if action.confidence < 0.5 and action.action not in (
                ActionType.DETECTED_2FA,
                ActionType.DETECTED_CAPTCHA,
                ActionType.LOGIN_SUCCESS,
                ActionType.ERROR,
            ):
                action = AgentAction(
                    thought="Low confidence — waiting",
                    action=ActionType.WAIT,
                    confidence=0.0,
                )

            # Terminal states
            if action.action == ActionType.DETECTED_2FA:
                log_2fa_detected(logger, platform)
                return ExtractionResult(has_2fa=True)

            if action.action == ActionType.DETECTED_CAPTCHA:
                return ExtractionResult(has_captcha=True)

            if action.action == ActionType.LOGIN_SUCCESS:
                cookies = await self._extract_cookies(page)
                return ExtractionResult(success=True, cookies=cookies)

            if action.action == ActionType.ERROR:
                return ExtractionResult(
                    success=False,
                    error_message=f"AI error: {action.thought}",
                )

            # Execute action
            result = await executor.execute(action)
            if not result.get("success"):
                logger.warning(f"Action failed: {result.get('error')}")

            # Auto-wait after navigate/click
            if action.action in (ActionType.NAVIGATE, ActionType.CLICK):
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass

        return ExtractionResult(
            success=False,
            error_message=f"Max steps ({steps}) reached without login success",
        )

    async def _take_screenshot(self, page: Page) -> str:
        """Take screenshot, resize, compress, return base64 JPEG."""
        try:
            png_bytes = await page.screenshot(type="png")
        except Exception:
            return ""

        if Image is None:
            # Fallback: base64 raw PNG
            return base64.b64encode(png_bytes).decode("utf-8")

        try:
            image = Image.open(io.BytesIO(png_bytes))
            width, height = image.size
            if width > self.screenshot_max_width:
                ratio = self.screenshot_max_width / width
                new_height = int(height * ratio)
                image = image.resize((self.screenshot_max_width, new_height), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=85, optimize=True)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            return base64.b64encode(png_bytes).decode("utf-8")

    async def _extract_cookies(self, page: Page) -> List[CookieData]:
        """Extract cookies from the browser context."""
        try:
            context = page.context
            raw_cookies = await context.cookies()
            return [
                CookieData(
                    name=cookie["name"],
                    value=cookie["value"],
                    domain=cookie.get("domain", ""),
                    expires=cookie.get("expires"),
                    secure=cookie.get("secure", True),
                    http_only=cookie.get("httpOnly", True),
                )
                for cookie in raw_cookies
            ]
        except Exception as exc:
            logger.warning(f"Cookie extraction failed: {exc}")
            return []
