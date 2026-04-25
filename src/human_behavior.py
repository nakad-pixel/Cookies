from __future__ import annotations

import asyncio
import math
import random
from typing import Optional


def _gaussian_delay(mean: float = 80.0, std: float = 30.0, min_delay: float = 20.0) -> float:
    """Return a random delay based on a Gaussian distribution."""
    delay = random.gauss(mean, std)
    return max(min_delay, delay) / 1000.0


async def random_human_wait(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """Wait for a randomized duration."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def human_like_typing(
    page,
    selector: str,
    text: str,
    mean_ms: float = 80.0,
    std_ms: float = 30.0,
    random_seed: Optional[int] = None,
) -> None:
    """Type text with realistic human delays between keystrokes.

    Args:
        page: Patchright page object.
        selector: CSS selector for the input element.
        text: Text to type.
        mean_ms: Mean delay between keystrokes in milliseconds.
        std_ms: Standard deviation of delay in milliseconds.
        random_seed: Optional seed for reproducibility in tests.
    """
    if random_seed is not None:
        random.seed(random_seed)
    element = page.locator(selector)
    await element.click()
    for i, char in enumerate(text):
        await element.type(char, delay=_gaussian_delay(mean_ms, std_ms) * 1000)
        # Occasional hesitation after a few characters
        if i > 0 and i % random.randint(4, 8) == 0:
            await asyncio.sleep(random.uniform(0.2, 0.5))


async def human_like_mouse_move(
    page,
    x: int,
    y: int,
    steps: int = 25,
    random_seed: Optional[int] = None,
) -> None:
    """Move the mouse along a quadratic Bezier curve to the target.

    Args:
        page: Patchright page object.
        x: Target X coordinate.
        y: Target Y coordinate.
        steps: Number of interpolation steps.
        random_seed: Optional seed for reproducibility in tests.
    """
    if random_seed is not None:
        random.seed(random_seed)

    current = await page.evaluate("() => ({x: window.mouseX || 0, y: window.mouseY || 0})")
    start_x = current.get("x", 0)
    start_y = current.get("y", 0)

    # Control point for quadratic Bezier
    cp_x = (start_x + x) / 2 + random.randint(-50, 50)
    cp_y = (start_y + y) / 2 + random.randint(-50, 50)

    for t in range(1, steps + 1):
        t_norm = t / steps
        # Quadratic Bezier: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
        bx = (1 - t_norm) ** 2 * start_x + 2 * (1 - t_norm) * t_norm * cp_x + t_norm ** 2 * x
        by = (1 - t_norm) ** 2 * start_y + 2 * (1 - t_norm) * t_norm * cp_y + t_norm ** 2 * y
        # Small overshoot/undershoot
        bx += random.randint(-2, 2)
        by += random.randint(-2, 2)
        await page.mouse.move(int(bx), int(by))
        await asyncio.sleep(random.uniform(0.005, 0.015))


async def human_like_click(
    page,
    selector: str,
    random_seed: Optional[int] = None,
) -> None:
    """Click an element after moving the mouse with a Bezier curve.

    Args:
        page: Patchright page object.
        selector: CSS selector for the element.
        random_seed: Optional seed for reproducibility in tests.
    """
    if random_seed is not None:
        random.seed(random_seed)

    element = page.locator(selector)
    box = await element.bounding_box()
    if not box:
        await element.click()
        return

    target_x = int(box["x"] + box["width"] / 2 + random.randint(-5, 5))
    target_y = int(box["y"] + box["height"] / 2 + random.randint(-5, 5))

    await human_like_mouse_move(page, target_x, target_y, random_seed=random_seed)
    await asyncio.sleep(random.uniform(0.05, 0.2))
    await page.mouse.click(target_x, target_y)


async def emulate_scroll(
    page,
    max_scrolls: int = 5,
    random_seed: Optional[int] = None,
) -> None:
    """Scroll down in random increments with pauses, sometimes scroll back up.

    Args:
        page: Patchright page object.
        max_scrolls: Maximum number of scroll actions.
        random_seed: Optional seed for reproducibility in tests.
    """
    if random_seed is not None:
        random.seed(random_seed)

    for _ in range(random.randint(1, max_scrolls)):
        scroll_y = random.randint(200, 800)
        await page.evaluate(f"window.scrollBy(0, {scroll_y})")
        await asyncio.sleep(random.uniform(0.3, 1.0))
        # Occasionally scroll back up slightly
        if random.random() < 0.2:
            await page.evaluate(f"window.scrollBy(0, -{random.randint(50, 150)})")
            await asyncio.sleep(random.uniform(0.2, 0.5))
