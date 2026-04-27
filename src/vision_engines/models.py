from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ActionType(Enum):
    CLICK = "CLICK"
    TYPE = "TYPE"
    SCROLL = "SCROLL"
    WAIT = "WAIT"
    NAVIGATE = "NAVIGATE"
    DETECTED_2FA = "DETECTED_2FA"
    DETECTED_CAPTCHA = "DETECTED_CAPTCHA"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    ERROR = "ERROR"


@dataclass
class VisionContext:
    url: str
    goal: str
    platform: str
    history: List[dict] = field(default_factory=list)


@dataclass
class AgentAction:
    thought: str
    action: ActionType
    target: str = ""
    value: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "thought": self.thought,
            "action": self.action.value,
            "target": self.target,
            "value": self.value,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentAction":
        action_str = data.get("action", "ERROR")
        try:
            action_type = ActionType(action_str)
        except ValueError:
            action_type = ActionType.ERROR
        return cls(
            thought=data.get("thought", ""),
            action=action_type,
            target=data.get("target", ""),
            value=data.get("value", ""),
            confidence=float(data.get("confidence", 0.0)),
        )
