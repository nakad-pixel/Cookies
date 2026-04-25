import pytest
from unittest.mock import AsyncMock, MagicMock

from src.human_behavior import (
    human_like_typing,
    human_like_mouse_move,
    human_like_click,
    random_human_wait,
    emulate_scroll,
)


class TestRandomHumanWait:
    @pytest.mark.asyncio
    async def test_wait_runs(self):
        """Test that random_human_wait completes without error."""
        await random_human_wait(min_sec=0.01, max_sec=0.02)


class TestHumanLikeTyping:
    @pytest.mark.asyncio
    async def test_typing_with_seed(self):
        """Test human_like typing with seed for reproducibility."""
        page = MagicMock()
        element = MagicMock()
        page.locator.return_value = element
        element.click = AsyncMock()
        element.type = AsyncMock()

        await human_like_typing(page, "#input", "hello", random_seed=42)
        assert element.click.called
        assert element.type.call_count == len("hello")

    @pytest.mark.asyncio
    async def test_typing_empty_string(self):
        """Test typing an empty string."""
        page = MagicMock()
        element = MagicMock()
        page.locator.return_value = element
        element.click = AsyncMock()
        element.type = AsyncMock()

        await human_like_typing(page, "#input", "", random_seed=42)
        assert element.click.called
        assert element.type.call_count == 0


class TestHumanLikeMouseMove:
    @pytest.mark.asyncio
    async def test_mouse_move_runs(self):
        """Test that human_like_mouse_move completes without error."""
        page = MagicMock()
        page.evaluate = AsyncMock(return_value={"x": 0, "y": 0})
        page.mouse = MagicMock()
        page.mouse.move = AsyncMock()

        await human_like_mouse_move(page, 100, 100, steps=5, random_seed=42)
        assert page.mouse.move.call_count == 5


class TestHumanLikeClick:
    @pytest.mark.asyncio
    async def test_click_runs(self):
        """Test that human_like_click completes without error."""
        page = MagicMock()
        element = MagicMock()
        page.locator.return_value = element
        element.bounding_box = AsyncMock(return_value={"x": 10, "y": 10, "width": 20, "height": 20})
        page.evaluate = AsyncMock(return_value={"x": 0, "y": 0})
        page.mouse = MagicMock()
        page.mouse.move = AsyncMock()
        page.mouse.click = AsyncMock()

        await human_like_click(page, "#btn", random_seed=42)
        assert page.mouse.click.called

    @pytest.mark.asyncio
    async def test_click_fallback_when_no_box(self):
        """Test click fallback when bounding box is unavailable."""
        page = MagicMock()
        element = MagicMock()
        page.locator.return_value = element
        element.bounding_box = AsyncMock(return_value=None)
        element.click = AsyncMock()

        await human_like_click(page, "#btn", random_seed=42)
        assert element.click.called


class TestEmulateScroll:
    @pytest.mark.asyncio
    async def test_scroll_runs(self):
        """Test that emulate_scroll completes without error."""
        page = MagicMock()
        page.evaluate = AsyncMock()

        await emulate_scroll(page, max_scrolls=2, random_seed=42)
        assert page.evaluate.called
