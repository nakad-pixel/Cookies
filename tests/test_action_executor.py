import pytest
from unittest.mock import AsyncMock, MagicMock

from src.action_executor import ActionExecutor
from src.vision_engines.models import ActionType, AgentAction


class TestActionExecutor:
    @pytest.mark.asyncio
    async def test_click_executes(self):
        page = MagicMock()
        locator = MagicMock()
        page.locator.return_value = locator
        locator.first = locator
        locator.wait_for = AsyncMock()

        executor = ActionExecutor(page)
        action = AgentAction(
            thought="Click login",
            action=ActionType.CLICK,
            target="#login-btn",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result["success"] is True
        assert page.mouse.click.called or locator.click.called

    @pytest.mark.asyncio
    async def test_type_with_value(self):
        page = MagicMock()
        element = MagicMock()
        page.locator.return_value = element
        element.first = element
        element.wait_for = AsyncMock()
        element.type = AsyncMock()
        element.click = AsyncMock()

        executor = ActionExecutor(page, credentials={"username": "user", "password": "pass"})
        action = AgentAction(
            thought="Type username",
            action=ActionType.TYPE,
            target="#username",
            value="testuser",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result["success"] is True
        assert element.type.called

    @pytest.mark.asyncio
    async def test_type_with_placeholder(self):
        page = MagicMock()
        element = MagicMock()
        page.locator.return_value = element
        element.first = element
        element.wait_for = AsyncMock()
        element.type = AsyncMock()
        element.click = AsyncMock()

        executor = ActionExecutor(page, credentials={"username": "user", "password": "pass"})
        action = AgentAction(
            thought="Type username placeholder",
            action=ActionType.TYPE,
            target="#username",
            value="{{username}}",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_type_no_target_fails(self):
        page = MagicMock()
        executor = ActionExecutor(page)
        action = AgentAction(
            thought="Type nowhere",
            action=ActionType.TYPE,
            value="test",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_scroll_executes(self):
        page = MagicMock()
        page.evaluate = AsyncMock()

        executor = ActionExecutor(page)
        action = AgentAction(
            thought="Scroll down",
            action=ActionType.SCROLL,
            value="down",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_wait_executes(self):
        page = MagicMock()
        executor = ActionExecutor(page)
        action = AgentAction(
            thought="Wait",
            action=ActionType.WAIT,
            value="1",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_navigate_executes(self):
        page = MagicMock()
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()

        executor = ActionExecutor(page)
        action = AgentAction(
            thought="Go to login",
            action=ActionType.NAVIGATE,
            value="https://example.com/login",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result["success"] is True
        assert page.goto.called

    @pytest.mark.asyncio
    async def test_terminal_actions_succeed(self):
        page = MagicMock()
        executor = ActionExecutor(page)

        for action_type in (ActionType.DETECTED_2FA, ActionType.DETECTED_CAPTCHA, ActionType.LOGIN_SUCCESS, ActionType.ERROR):
            action = AgentAction(
                thought="Terminal",
                action=action_type,
                confidence=1.0,
            )
            result = await executor.execute(action)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_unknown_action_fails(self):
        # This shouldn't normally happen, but test coverage
        page = MagicMock()
        executor = ActionExecutor(page)
        # Create an action with an invalid type using object.__new__ to bypass enum
        action = MagicMock()
        action.action = "INVALID"
        action.target = ""
        action.value = ""
        result = await executor.execute(action)
        assert result["success"] is False
