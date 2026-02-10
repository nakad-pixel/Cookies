"""Cookie Guardian - Ephemeral cookie management system.

This package provides a simplified cookie management system with:
- Ephemeral cookie handling (memory only, no local persistence)
- 2FA detection and skip behavior
- Automatic log redaction
- GitHub Secrets integration
"""

__version__ = "2.0.0"

from src.browser_automation import BrowserAutomation, CookieData, ExtractionResult
from src.config import load_config
from src.database import Database
from src.orchestrator import Orchestrator, build_orchestrator

__all__ = [
    "BrowserAutomation",
    "CookieData",
    "Database",
    "ExtractionResult",
    "Orchestrator",
    "build_orchestrator",
    "load_config",
]
