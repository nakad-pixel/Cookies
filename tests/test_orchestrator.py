import asyncio
import pytest

from src.database import Database
from src.glm_engine import GlmDecision
from src.orchestrator import Orchestrator, OrchestratorContext, State, build_orchestrator
from src.config import Config


class DummyDiscovery:
    def discover(self):
        return []


class DummyGlm:
    def decide(self, prompt: str) -> GlmDecision:
        return GlmDecision(action="ok", reason="unit test")


class DummySecrets:
    def put_secret(self, repo: str, name: str, value: str) -> None:
        pass


class DummyConfig:
    def __init__(self):
        self.github = type('obj', (object,), {
            'api_url': 'https://api.github.com',
            'token_env': 'GITHUB_TOKEN',
            'org': 'test'
        })()
        self.storage = type('obj', (object,), {
            'database_path': ':memory:'
        })()
        self.glm = type('obj', (object,), {
            'api_url': 'https://api.example.com',
            'api_key_env': 'GLM_API_KEY',
            'model': 'test',
            'monthly_budget_usd': 0.1
        })()
        self.credentials = type('obj', (object,), {
            'prefix': 'USER_CREDENTIALS'
        })()


def test_orchestrator_run_empty_repos(tmp_path) -> None:
    """Test orchestrator run with no repositories."""
    db = Database(str(tmp_path / "test.sqlite"))
    config = DummyConfig()
    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=DummyDiscovery(),
            glm=DummyGlm(),
            secrets=DummySecrets(),
        )
    )
    asyncio.run(orchestrator.run())
    assert db.get_state() == "IDLE"


def test_state_enum_values() -> None:
    """Test State enum has expected values."""
    assert State.IDLE == "IDLE"
    assert State.DISCOVERING == "DISCOVERING"
    assert State.EXTRACTING == "EXTRACTING"
    assert State.INJECTING == "INJECTING"
    assert State.CLEANUP == "CLEANUP"
    assert State.COMPLETED == "COMPLETED"


def test_orchestrator_sanitize_secret_name() -> None:
    """Test secret name sanitization."""
    db = Database(":memory:")
    config = DummyConfig()
    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=DummyDiscovery(),
            glm=DummyGlm(),
            secrets=DummySecrets(),
        )
    )

    # Test various repo names
    assert orchestrator._sanitize_secret_name("owner/repo") == "OWNER_REPO"
    assert orchestrator._sanitize_secret_name("my-repo") == "MY_REPO"
    assert orchestrator._sanitize_secret_name("my.repo") == "MY_REPO"
    assert orchestrator._sanitize_secret_name("123abc") == "REPO_123ABC"


def test_orchestrator_detect_platform() -> None:
    """Test platform detection from repository."""
    from src.discovery import RepoCandidate

    db = Database(":memory:")
    config = DummyConfig()
    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=DummyDiscovery(),
            glm=DummyGlm(),
            secrets=DummySecrets(),
        )
    )

    github_repo = RepoCandidate(name="test/github-repo", url="https://github.com/test", confidence=0.8)
    gitlab_repo = RepoCandidate(name="test/gitlab-repo", url="https://gitlab.com/test", confidence=0.8)
    aws_repo = RepoCandidate(name="test/aws-repo", url="https://aws.amazon.com", confidence=0.8)
    unknown_repo = RepoCandidate(name="test/unknown", url="https://example.com", confidence=0.8)

    assert orchestrator._detect_platform(github_repo) == "github"
    assert orchestrator._detect_platform(gitlab_repo) == "gitlab"
    assert orchestrator._detect_platform(aws_repo) == "aws"
    assert orchestrator._detect_platform(unknown_repo) == "generic"


def test_orchestrator_get_login_url() -> None:
    """Test login URL generation for platforms."""
    from src.discovery import RepoCandidate

    db = Database(":memory:")
    config = DummyConfig()
    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=DummyDiscovery(),
            glm=DummyGlm(),
            secrets=DummySecrets(),
        )
    )

    repo = RepoCandidate(name="test/repo", url="https://example.com", confidence=0.8)

    assert orchestrator._get_login_url("github", repo) == "https://github.com/login"
    assert orchestrator._get_login_url("gitlab", repo) == "https://gitlab.com/users/sign_in"
    assert orchestrator._get_login_url("google", repo) == "https://accounts.google.com/signin"
    assert orchestrator._get_login_url("unknown", repo) == "https://example.com"
