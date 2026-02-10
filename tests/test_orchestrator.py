import asyncio

from src.database import Database
from src.glm_engine import GlmDecision
from src.orchestrator import Orchestrator, OrchestratorContext


class DummyDiscovery:
    def discover(self):
        return []


class DummyGlm:
    def decide(self, prompt: str) -> GlmDecision:
        return GlmDecision(action="ok", reason="unit test")


class DummySecrets:
    pass


def test_orchestrator_run(tmp_path) -> None:
    db = Database(str(tmp_path / "test.sqlite"))
    orchestrator = Orchestrator(
        OrchestratorContext(database=db, discovery=DummyDiscovery(), glm=DummyGlm(), secrets=DummySecrets())
    )
    asyncio.run(orchestrator.run())
    assert db.get_state() == "IDLE"
