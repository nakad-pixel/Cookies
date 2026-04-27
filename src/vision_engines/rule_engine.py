from __future__ import annotations

import logging
from typing import Optional

from src.vision_engines.base import VisionEngine
from src.vision_engines.models import ActionType, AgentAction, VisionContext

logger = logging.getLogger("vision-engine")


class RuleBasedVisionEngine(VisionEngine):
    """Zero-cost rule-based vision fallback using DOM heuristics.

    No AI, no API keys, no network calls. Uses known selectors and page content.
    """

    USERNAME_SELECTORS = [
        'input[name="username"]',
        'input[name="login"]',
        'input[name="email"]',
        'input[type="email"]',
        'input[id="username"]',
        'input[id="login"]',
        'input[id="email"]',
        'input[placeholder*="username" i]',
        'input[placeholder*="email" i]',
    ]

    PASSWORD_SELECTORS = [
        'input[name="password"]',
        'input[type="password"]',
        'input[id="password"]',
        'input[placeholder*="password" i]',
    ]

    SUBMIT_SELECTORS = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Sign in")',
        'button:has-text("Log in")',
        'button:has-text("Login")',
        'button:has-text("Continue")',
        'button:has-text("Next")',
    ]

    TWO_FA_PATTERNS = [
        "two-factor",
        "two factor",
        "2fa",
        "authenticator",
        "verification code",
        "security code",
        "sms code",
        "backup code",
        "auth code",
        "enter code",
        "verify your identity",
        "additional verification",
    ]

    CAPTCHA_PATTERNS = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "i'm not a robot",
        "security check",
        "challenge",
    ]

    async def analyze_screenshot(self, screenshot_b64: str, context: VisionContext) -> AgentAction:
        # Rule engine doesn't use screenshots; it relies on page state
        # This is called when we have no AI available. We return WAIT to let
        # the caller query DOM and feed us title/content in history.
        history = context.history or []
        page_title = ""
        page_content = ""

        for entry in reversed(history):
            if entry.get("page_title"):
                page_title = entry["page_title"].lower()
            if entry.get("page_content"):
                page_content = entry["page_content"].lower()
            if page_title and page_content:
                break

        # Detect 2FA
        for pattern in self.TWO_FA_PATTERNS:
            if pattern in page_title or pattern in page_content:
                return AgentAction(
                    thought="Rule engine detected 2FA indicator",
                    action=ActionType.DETECTED_2FA,
                    confidence=0.8,
                )

        # Detect CAPTCHA
        for pattern in self.CAPTCHA_PATTERNS:
            if pattern in page_title or pattern in page_content:
                return AgentAction(
                    thought="Rule engine detected CAPTCHA indicator",
                    action=ActionType.DETECTED_CAPTCHA,
                    confidence=0.8,
                )

        # Detect login success
        if any(ind in page_content for ind in ["logout", "sign out", "dashboard", "welcome", "account"]):
            if any(ind in page_title for ind in ["home", "dashboard", "account", "profile"]):
                return AgentAction(
                    thought="Rule engine detected logged-in state",
                    action=ActionType.LOGIN_SUCCESS,
                    confidence=0.7,
                )

        # If we have no page info yet, wait for caller to provide it
        if not page_content and not page_title:
            return AgentAction(
                thought="Rule engine waiting for page content",
                action=ActionType.WAIT,
                confidence=0.5,
            )

        # We have page info but no clear state — suggest generic login selectors
        # The action executor will validate these exist before acting
        if any(s.split("=")[-1].strip('"').lower() in page_content for s in self.USERNAME_SELECTORS[:3]):
            return AgentAction(
                thought="Rule engine suggests typing username",
                action=ActionType.TYPE,
                target='input[name="username"], input[name="login"], input[type="email"]',
                value="{{username}}",
                confidence=0.5,
            )

        if any(s.split("=")[-1].strip('"').lower() in page_content for s in self.PASSWORD_SELECTORS[:3]):
            return AgentAction(
                thought="Rule engine suggests typing password",
                action=ActionType.TYPE,
                target='input[name="password"], input[type="password"]',
                value="{{password}}",
                confidence=0.5,
            )

        if any(ind in page_content for ind in ["sign in", "log in", "login", "continue"]):
            return AgentAction(
                thought="Rule engine suggests clicking submit",
                action=ActionType.CLICK,
                target='button[type="submit"], input[type="submit"]',
                confidence=0.5,
            )

        return AgentAction(
            thought="Rule engine uncertain — waiting",
            action=ActionType.WAIT,
            confidence=0.3,
        )
