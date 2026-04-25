from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class BrowserContextManager:
    """Manages persistent browser profiles per platform."""

    def __init__(self, profile_dir: str = "data/profiles") -> None:
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def get_profile_path(self, platform: str) -> Path:
        """Return the profile path for a platform."""
        return self.profile_dir / platform

    def ensure_profile(self, platform: str) -> Path:
        """Ensure the profile directory exists for a platform."""
        path = self.get_profile_path(platform)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def cleanup_old_profiles(self, max_age_days: int = 30) -> int:
        """Remove profiles older than max_age_days.

        Returns:
            Number of profiles removed.
        """
        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0
        for platform_dir in self.profile_dir.iterdir():
            if not platform_dir.is_dir():
                continue
            try:
                mtime = datetime.fromtimestamp(platform_dir.stat().st_mtime)
                if mtime < cutoff:
                    shutil.rmtree(platform_dir)
                    removed += 1
            except OSError:
                continue
        return removed

    def list_profiles(self) -> list[str]:
        """List all existing platform profiles."""
        return [d.name for d in self.profile_dir.iterdir() if d.is_dir()]
