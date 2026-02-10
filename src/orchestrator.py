from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum

from src.config import get_env_value, load_config
from src.database import Database, Repository
from src.discovery import DiscoveryEngine
from src.glm_engine import GlmEngine
from src.logger import log_event, setup_logger
from src.secrets_manager import SecretsManager


class State(str, Enum):
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    EXTRACTING = "EXTRACTING"
    INJECTING = "INJECTING"
    VALIDATING = "VALIDATING"
    COMMITTING = "COMMITTING"


@dataclass
class OrchestratorContext:
    database: Database
    discovery: DiscoveryEngine
    glm: GlmEngine
    secrets: SecretsManager


class Orchestrator:
    def __init__(self, context: OrchestratorContext) -> None:
        self.context = context
        self.logger = setup_logger("cookie-guardian")

    async def run(self) -> None:
        await self._transition(State.SCANNING)
        candidates = self.context.discovery.discover()
        for candidate in candidates:
            self.context.database.add_repository(Repository(name=candidate.name, url=candidate.url))

        await self._transition(State.EXTRACTING)
        decision = self.context.glm.decide("Evaluate extraction strategy")
        log_event(self.logger, "glm_decision", action=decision.action, reason=decision.reason)

        await self._transition(State.INJECTING)
        await asyncio.sleep(0.1)

        await self._transition(State.VALIDATING)
        await asyncio.sleep(0.1)

        await self._transition(State.COMMITTING)
        self.context.database.add_audit_event("run_complete", "{}")
        await self._transition(State.IDLE)

    async def _transition(self, state: State) -> None:
        self.context.database.set_state(state.value)
        log_event(self.logger, "state_transition", state=state.value)


def build_orchestrator() -> Orchestrator:
    config = load_config()
    token = get_env_value(config.github.token_env)
    if not token:
        raise RuntimeError("Missing GitHub token")

    glm_key = get_env_value(config.glm.api_key_env)
    database = Database(config.storage.database_path)
    discovery = DiscoveryEngine(token=token, org=config.github.org)
    glm = GlmEngine(
        api_url=config.glm.api_url,
        api_key=glm_key,
        model=config.glm.model,
        monthly_budget_usd=config.glm.monthly_budget_usd,
    )
    secrets = SecretsManager(config.github.api_url, token)

    return Orchestrator(
        OrchestratorContext(database=database, discovery=discovery, glm=glm, secrets=secrets)
    )


if __name__ == "__main__":
    asyncio.run(build_orchestrator().run())
