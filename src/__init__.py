"""Cookie Guardian - AI-Vision-driven ephemeral cookie management system.

This package provides a dynamic cookie management system with:
- AI-Vision browser agent (screenshot -> analyze -> act loop)
- Dynamic platform detection from repository contents
- Ephemeral cookie handling (memory only, no local persistence)
- 2FA detection and skip behavior
- Automatic log redaction
- GitHub Secrets AND Variables integration
"""

__version__ = "3.0.0"

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
