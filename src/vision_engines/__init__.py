from __future__ import annotations

import os
from typing import Optional

from src.config import Config
from src.vision_engines.base import VisionEngine
from src.vision_engines.gemini_engine import GeminiVisionEngine
from src.vision_engines.openrouter_engine import OpenRouterVisionEngine
from src.vision_engines.local_engine import LocalVisionEngine
from src.vision_engines.rule_engine import RuleBasedVisionEngine


def create_vision_engine(config: Optional[Config] = None) -> VisionEngine:
    """Factory to create the best available vision engine.

    Tries: Gemini -> OpenRouter -> Local Ollama -> Rule-based
    """
    if config is None:
        from src.config import load_config

        config = load_config()

    ai_config = getattr(config, "ai_vision", None)

    gemini_key = None
    openrouter_key = None
    ollama_url = "http://localhost:11434"

    if ai_config:
        gemini_key = os.getenv(ai_config.gemini_api_key_env, "")
        openrouter_key = os.getenv(ai_config.openrouter_api_key_env, "")
        if ai_config.ollama_url:
            ollama_url = ai_config.ollama_url
    else:
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    # Try Gemini first
    if gemini_key:
        try:
            return GeminiVisionEngine(api_key=gemini_key)
        except Exception:
            pass

    # Fallback to OpenRouter
    if openrouter_key:
        try:
            return OpenRouterVisionEngine(api_key=openrouter_key)
        except Exception:
            pass

    # Fallback to local Ollama
    try:
        return LocalVisionEngine(base_url=ollama_url)
    except Exception:
        pass

    # Final fallback: rule-based (zero cost, zero API)
    return RuleBasedVisionEngine()
