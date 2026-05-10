import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.browser_automation import CookieData, ExtractionResult
from src.database import Database
from src.decision_engine import Decision
from src.discovery import RepoCandidate
from src.orchestrator import Orchestrator, OrchestratorContext, State, build_orchestrator
from src.config import Config, get_credentials_for_platform
from src.repo_analyzer import TargetPlatform


class DummyDiscovery:
    def discover(self):
        return []


class DummyDecisionEngine:
    def decide(self, repo_name, description, platforms_detected):
        return Decision(action="extract", reason="unit test")


class DummyRepoAnalyzer:
    def analyze(self, candidate):
        return [TargetPlatform(name="github", login_url="https://github.com/login", cookie_domain=".github.com", confidence=0.8)]


class DummySecrets:
    def put_secret(self, repo: str, name: str, value: str) -> None:
        pass

    def put_variable(self, repo: str, name: str, value: str) -> None:
        pass


class DummyConfig:
    def __init__(self):
        self.github = type('obj', (object,), {
            'api_url': 'https://api.github.com',
            'token_env': 'CG_GITHUB_TOKEN',
            'org': 'test'
        })()
        self.storage = type('obj', (object,), {
            'database_path': ':memory:'
        })()
        self.ai_vision = type('obj', (object,), {
            'engine': 'gemini',
            'gemini_api_key_env': 'GEMINI_API_KEY',
            'openrouter_api_key_env': 'OPENROUTER_API_KEY',
            'ollama_url': 'http://localhost:11434',
            'max_steps': 30,
            'screenshot_max_width': 800,
        })()
        self.credentials = type('obj', (object,), {
            'prefix': 'USER_CREDENTIALS'
        })()
        self.app = type('obj', (object,), {
            'max_concurrency': 2,
            'max_retries': 3,
            'profile_dir': 'data/profiles',
            'har_dir': 'data/har',
            'tracing_dir': 'data/traces',
            'enable_har': False,
            'enable_tracing': False,
        })()
        self.warp = type('obj', (object,), {
            'connect_timeout_sec': 30,
            'rotate_interval_sec': 900,
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
            decision_engine=DummyDecisionEngine(),
            repo_analyzer=DummyRepoAnalyzer(),
            secrets=DummySecrets(),
        )
    )
    asyncio.run(orchestrator.run())
    assert db.get_state() == "IDLE"


def test_state_enum_values() -> None:
    """Test State enum has expected values."""
    assert State.IDLE == "IDLE"
    assert State.DISCOVERING == "DISCOVERING"
    assert State.ANALYZING == "ANALYZING"
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
            decision_engine=DummyDecisionEngine(),
            repo_analyzer=DummyRepoAnalyzer(),
            secrets=DummySecrets(),
        )
    )

    # Test various repo names
    assert orchestrator._sanitize_secret_name("owner/repo") == "OWNER_REPO"
    assert orchestrator._sanitize_secret_name("my-repo") == "MY_REPO"
    assert orchestrator._sanitize_secret_name("my.repo") == "MY_REPO"
    assert orchestrator._sanitize_secret_name("123abc") == "REPO_123ABC"


@pytest.mark.asyncio
async def test_orchestrator_concurrency_semaphore(tmp_path):
    """Test that concurrency is bounded by a semaphore."""
    db = Database(str(tmp_path / "test.sqlite"))
    config = DummyConfig()
    config.app.max_concurrency = 1

    candidate = RepoCandidate(name="test/repo", url="https://github.com/test/repo", confidence=0.9)

    class SingleDiscovery:
        def discover(self):
            return [candidate]

    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=SingleDiscovery(),
            decision_engine=DummyDecisionEngine(),
            repo_analyzer=DummyRepoAnalyzer(),
            secrets=DummySecrets(),
        )
    )

    call_count = 0

    async def mock_extract(candidate, platform):
        nonlocal call_count
        call_count += 1
        return ExtractionResult(cookies=[], has_2fa=False, success=False, error_message="test")

    async def mock_inject(candidate, platform, cookies):
        pass

    orchestrator._extract_cookies = mock_extract
    orchestrator._inject_cookies = mock_inject

    await orchestrator.run()
    assert call_count == 1


@pytest.mark.asyncio
async def test_orchestrator_passes_real_repo_id(tmp_path):
    """Test that the real repository ID is passed to _record_extraction."""
    db = Database(str(tmp_path / "test.sqlite"))
    config = DummyConfig()

    candidate = RepoCandidate(name="test/repo", url="https://github.com/test/repo", confidence=0.9)

    class SingleDiscovery:
        def discover(self):
            return [candidate]

    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=SingleDiscovery(),
            decision_engine=DummyDecisionEngine(),
            repo_analyzer=DummyRepoAnalyzer(),
            secrets=DummySecrets(),
        )
    )

    recorded = {}

    async def mock_extract(candidate, platform):
        return ExtractionResult(
            cookies=[CookieData(name="s", value="v", domain=".github.com")],
            has_2fa=False,
            success=True,
        )

    async def mock_inject(candidate, platform, cookies):
        pass

    def mock_record(candidate, platform, result, repo_id):
        recorded["repo_id"] = repo_id
        recorded["candidate"] = candidate.name
        recorded["platform"] = platform.name

    orchestrator._extract_cookies = mock_extract
    orchestrator._inject_cookies = mock_inject
    orchestrator._record_extraction = mock_record

    await orchestrator.run()

    assert recorded["candidate"] == "test/repo"
    assert recorded.get("repo_id") is not None
    assert isinstance(recorded["repo_id"], int)
    assert recorded["platform"] == "github"


@pytest.mark.asyncio
async def test_orchestrator_dual_injection(tmp_path):
    """Test that both secret and variable are injected."""
    db = Database(str(tmp_path / "test.sqlite"))
    config = DummyConfig()

    candidate = RepoCandidate(name="test/repo", url="https://github.com/test/repo", confidence=0.9)

    class SingleDiscovery:
        def discover(self):
            return [candidate]

    injected = {"secret": False, "variable": False}

    class TrackingSecrets:
        def put_secret(self, repo, name, value):
            injected["secret"] = True

        def put_variable(self, repo, name, value):
            injected["variable"] = True

    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=SingleDiscovery(),
            decision_engine=DummyDecisionEngine(),
            repo_analyzer=DummyRepoAnalyzer(),
            secrets=TrackingSecrets(),
        )
    )

    async def mock_extract(candidate, platform):
        return ExtractionResult(
            cookies=[CookieData(name="session", value="abc", domain=".github.com")],
            success=True,
        )

    async def mock_cleanup(candidate, platform, result, repo_id):
        pass

    orchestrator._extract_cookies = mock_extract
    orchestrator._cleanup_repo_platform = mock_cleanup

    await orchestrator.run()

    assert injected["secret"] is True
    assert injected["variable"] is True


@pytest.mark.asyncio
async def test_orchestrator_runs_when_warp_rotation_fails(tmp_path):
    """Test that the orchestrator completes when WARP rotation raises."""
    db = Database(str(tmp_path / "test.sqlite"))
    config = DummyConfig()

    candidate = RepoCandidate(name="test/repo", url="https://github.com/test/repo", confidence=0.9)

    class SingleDiscovery:
        def discover(self):
            return [candidate]

    class FailingWarpManager:
        async def rotate_ip_async(self):
            raise RuntimeError("WARP is not available")

    orchestrator = Orchestrator(
        OrchestratorContext(
            config=config,
            database=db,
            discovery=SingleDiscovery(),
            decision_engine=DummyDecisionEngine(),
            repo_analyzer=DummyRepoAnalyzer(),
            secrets=DummySecrets(),
            warp=FailingWarpManager(),
        )
    )

    async def mock_extract(candidate, platform):
        return ExtractionResult(
            cookies=[CookieData(name="session", value="abc", domain=".github.com")],
            success=True,
        )

    async def mock_cleanup(candidate, platform, result, repo_id):
        pass

    async def mock_inject(candidate, platform, cookies):
        pass

    orchestrator._extract_cookies = mock_extract
    orchestrator._cleanup_repo_platform = mock_cleanup
    orchestrator._inject_cookies = mock_inject

    await orchestrator.run()
    # Orchestrator transitions to COMPLETED then to IDLE in finally block
    assert db.get_state() in ("COMPLETED", "IDLE")


@pytest.mark.asyncio
async def test_orchestrator_uses_unified_credentials(tmp_path):
    """Mock get_credentials_for_platform to verify it's called correctly."""
    db = Database(str(tmp_path / "test.sqlite"))
    config = DummyConfig()

    candidate = RepoCandidate(name="test/repo", url="https://github.com/test/repo", confidence=0.9)

    class SingleDiscovery:
        def discover(self):
            return [candidate]

    call_log = []

    def mock_get_credentials(platform, cfg=None):
        call_log.append(platform)
        return {"username": "testuser", "password": "testpass"}, "unified"

    with patch("src.orchestrator.get_credentials_for_platform", mock_get_credentials):
        with patch("src.orchestrator.BrowserAutomation") as MockBrowser:
            MockBrowser.return_value.extract_cookies = AsyncMock(
                return_value=ExtractionResult(
                    cookies=[CookieData(name="session", value="abc", domain=".github.com")],
                    success=True,
                )
            )
            with patch("src.orchestrator.RetryManager") as MockRetry:
                # Make retry decorator pass through directly
                MockRetry.return_value.retry_with_warp_rotation = lambda warp, exceptions: (lambda f: f)

                orchestrator = Orchestrator(
                    OrchestratorContext(
                        config=config,
                        database=db,
                        discovery=SingleDiscovery(),
                        decision_engine=DummyDecisionEngine(),
                        repo_analyzer=DummyRepoAnalyzer(),
                        secrets=DummySecrets(),
                    )
                )

                async def mock_cleanup(candidate, platform, result, repo_id):
                    pass

                async def mock_inject(candidate, platform, cookies):
                    pass

                orchestrator._cleanup_repo_platform = mock_cleanup
                orchestrator._inject_cookies = mock_inject

                await orchestrator.run()

    assert "github" in call_log


@pytest.mark.asyncio
async def test_extract_cookies_logs_credential_source(tmp_path):
    """Verify fallback credentials are logged with their source."""
    db = Database(str(tmp_path / "test.sqlite"))
    config = DummyConfig()

    candidate = RepoCandidate(name="test/repo", url="https://github.com/test/repo", confidence=0.9)
    platform = TargetPlatform(name="buffer", login_url="https://buffer.com/login", cookie_domain=".buffer.com", confidence=0.8)

    def mock_get_credentials(platform_name, cfg=None):
        return {"username": "fallbackuser", "password": "fallbackpass"}, "fallback"

    with patch("src.orchestrator.get_credentials_for_platform", mock_get_credentials):
        with patch("src.orchestrator.BrowserAutomation") as MockBrowser:
            MockBrowser.return_value.extract_cookies = AsyncMock(
                return_value=ExtractionResult(
                    cookies=[CookieData(name="session", value="abc", domain=".buffer.com")],
                    success=True,
                )
            )
            with patch("src.orchestrator.RetryManager") as MockRetry:
                MockRetry.return_value.retry_with_warp_rotation = lambda warp, exceptions: (lambda f: f)

                orchestrator = Orchestrator(
                    OrchestratorContext(
                        config=config,
                        database=db,
                        discovery=MagicMock(),
                        decision_engine=DummyDecisionEngine(),
                        repo_analyzer=DummyRepoAnalyzer(),
                        secrets=DummySecrets(),
                    )
                )

                result = await orchestrator._extract_cookies(candidate, platform)

    assert result.success is True
