from __future__ import annotations

import asyncio
import subprocess
import time
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass(frozen=True)
class WarpStatus:
    connected: bool
    ip: str | None


class WarpCliError(RuntimeError):
    """Raised when the WARP CLI is unavailable or returns an error."""


class WarpManager:
    def __init__(self, connect_timeout_sec: int = 30, accept_tos: bool = False) -> None:
        self.connect_timeout_sec = connect_timeout_sec
        self.accept_tos = accept_tos

    def _run(self, cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        """Run a warp-cli command, optionally inserting --accept-tos after the binary."""
        full_cmd = list(cmd)
        if self.accept_tos and len(full_cmd) > 0:
            # Insert --accept-tos immediately after the 'warp-cli' binary (index 1)
            full_cmd.insert(1, "--accept-tos")
        try:
            return subprocess.run(full_cmd, **kwargs)
        except FileNotFoundError as exc:
            raise WarpCliError("warp-cli is not installed or not in PATH") from exc

    def register(self) -> None:
        self._run(["warp-cli", "registration", "new"], check=True)

    def mode_proxy(self) -> None:
        self._run(["warp-cli", "mode", "proxy"], check=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def connect(self) -> None:
        self._run(["warp-cli", "connect"], check=True)
        self._wait_for_connection()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def disconnect(self) -> None:
        self._run(["warp-cli", "disconnect"], check=True)

    def rotate_ip(self) -> None:
        self.disconnect()
        time.sleep(2)
        self.connect()

    def status(self) -> WarpStatus:
        result = self._run(["warp-cli", "status"], check=False, capture_output=True, text=True)
        output = result.stdout.lower()
        connected = "connected" in output and "disconnected" not in output
        ip = None
        for line in result.stdout.splitlines():
            if "ip" in line.lower():
                ip = line.split(":", 1)[-1].strip()
                break
        return WarpStatus(connected=connected, ip=ip)

    def _wait_for_connection(self) -> None:
        deadline = time.time() + self.connect_timeout_sec
        while time.time() < deadline:
            if self.status().connected:
                return
            time.sleep(2)
        raise TimeoutError("WARP connection timed out")

    # Async wrappers

    async def connect_async(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.connect)

    async def mode_proxy_async(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.mode_proxy)

    async def disconnect_async(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.disconnect)

    async def rotate_ip_async(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.rotate_ip)

    async def status_async(self) -> WarpStatus:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.status)

    def get_ip(self) -> str | None:
        """Return current public IP via external service."""
        try:
            response = httpx.get("https://api.ipify.org?format=json", timeout=10)
            response.raise_for_status()
            return response.json().get("ip")
        except Exception:
            return None

    async def get_ip_async(self) -> str | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_ip)
