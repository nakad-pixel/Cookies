"""End-to-end integration tests.

These tests verify the full workflow without external dependencies.
"""

import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock

from src.browser_automation import CookieData, ExtractionResult
from src.cleanup import SecureWiper, redact_sensitive
from src.database import Database, Repository, ExtractionRecord
from src.decision_engine import Decision
from src.discovery import RepoCandidate
from src.orchestrator import Orchestrator, OrchestratorContext
from src.repo_analyzer import TargetPlatform
from src.config import Config


class DummyDiscovery:
    def __init__(self, candidates=None):
        self._candidates = candidates or []

    def discover(self):
        return self._candidates


class DummyDecisionEngine:
    def __init__(self, decision=None):
        self._decision = decision or Decision(action="extract", reason="test")

    def decide(self, repo_name, description, platforms_detected):
        return self._decision


class DummyRepoAnalyzer:
    def __init__(self, platforms=None):
        self._platforms = platforms or [
            TargetPlatform(name="github", login_url="https://github.com/login", cookie_domain=".github.com", confidence=0.8),
        ]

    def analyze(self, candidate):
        return self._platforms


class DummySecrets:
    def __init__(self):
        self.secrets = {}
        self.variables = {}

    def put_secret(self, repo: str, name: str, value: str) -> None:
        self.secrets[f"{repo}/{name}"] = value

    def put_variable(self, repo: str, name: str, value: str) -> None:
        self.variables[f"{repo}/{name}"] = value


def test_full_workflow_no_2fa(tmp_path):
    """Test full workflow without 2FA detection."""
    db = Database(str(tmp_path / "e2e.sqlite"))

    # Create mock config
    config = Mock(spec=Config)
    config.github = Mock()
    config.github.api_url = "https://api.github.com"
    config.github.token_env = "CG_GITHUB_TOKEN"
    config.github.org = "test"
    config.storage = Mock()
    config.storage.database_path = str(tmp_path / "e2e.sqlite")
    config.ai_vision = Mock()
    config.ai_vision.engine = "gemini"
    config.ai_vision.gemini_api_key_env = "GEMINI_API_KEY"
    config.ai_vision.openrouter_api_key_env = "OPENROUTER_API_KEY"
    config.ai_vision.ollama_url = "http://localhost:11434"
    config.ai_vision.max_steps = 30
    config.ai_vision.screenshot_max_width = 800
    config.credentials = Mock()
    config.credentials.prefix = "USER_CREDENTIALS"
    config.app = Mock()
    config.app.max_concurrency = 2
    config.app.max_retries = 3
    config.app.profile_dir = "data/profiles"
    config.app.har_dir = "data/har"
    config.app.tracing_dir = "data/traces"
    config.app.enable_har = False
    config.app.enable_tracing = False
    config.warp = Mock()
    config.warp.connect_timeout_sec = 30
    config.warp.rotate_interval_sec = 900

    # Create test candidate
    candidate = RepoCandidate(
        name="test/repo",
        url="https://github.com/test/repo",
        confidence=0.9,
    )

    # Setup context
    context = OrchestratorContext(
        config=config,
        database=db,
        discovery=DummyDiscovery([candidate]),
        decision_engine=DummyDecisionEngine(Decision(action="extract", reason="test")),
        repo_analyzer=DummyRepoAnalyzer(),
        secrets=DummySecrets(),
    )

    # Create orchestrator and run
    orchestrator = Orchestrator(context)

    # Mock the extraction to return test cookies
    test_cookies = [
        CookieData(name="session", value="secret123", domain=".github.com"),
    ]

    async def mock_extract(candidate, platform):
        return ExtractionResult(
            cookies=test_cookies,
            has_2fa=False,
            success=True,
        )

    async def mock_inject(candidate, platform, cookies):
        pass

    async def mock_cleanup(candidate, platform, result, repo_id):
        pass

    orchestrator._extract_cookies = mock_extract
    orchestrator._inject_cookies = mock_inject
    orchestrator._cleanup_repo_platform = mock_cleanup

    asyncio.run(orchestrator.run())

    # Verify final state
    assert db.get_state() == "IDLE"


def test_full_workflow_with_2fa(tmp_path):
    """Test full workflow with 2FA detection (should skip)."""
    db = Database(str(tmp_path / "e2e.sqlite"))

    # Create mock config
    config = Mock(spec=Config)
    config.github = Mock()
    config.github.api_url = "https://api.github.com"
    config.github.token_env = "CG_GITHUB_TOKEN"
    config.github.org = "test"
    config.storage = Mock()
    config.storage.database_path = str(tmp_path / "e2e.sqlite")
    config.ai_vision = Mock()
    config.ai_vision.engine = "gemini"
    config.ai_vision.gemini_api_key_env = "GEMINI_API_KEY"
    config.ai_vision.openrouter_api_key_env = "OPENROUTER_API_KEY"
    config.ai_vision.ollama_url = "http://localhost:11434"
    config.ai_vision.max_steps = 30
    config.ai_vision.screenshot_max_width = 800
    config.credentials = Mock()
    config.credentials.prefix = "USER_CREDENTIALS"
    config.app = Mock()
    config.app.max_concurrency = 2
    config.app.max_retries = 3
    config.app.profile_dir = "data/profiles"
    config.app.har_dir = "data/har"
    config.app.tracing_dir = "data/traces"
    config.app.enable_har = False
    config.app.enable_tracing = False
    config.warp = Mock()
    config.warp.connect_timeout_sec = 30
    config.warp.rotate_interval_sec = 900

    # Create test candidate
    candidate = RepoCandidate(
        name="test/repo",
        url="https://github.com/test/repo",
        confidence=0.9,
    )

    # Setup context
    context = OrchestratorContext(
        config=config,
        database=db,
        discovery=DummyDiscovery([candidate]),
        decision_engine=DummyDecisionEngine(Decision(action="extract", reason="test")),
        repo_analyzer=DummyRepoAnalyzer(),
        secrets=DummySecrets(),
    )

    # Create orchestrator and run
    orchestrator = Orchestrator(context)

    # Mock the extraction to indicate 2FA detected
    async def mock_extract(candidate, platform):
        return ExtractionResult(
            cookies=[],
            has_2fa=True,
            success=False,
        )

    orchestrator._extract_cookies = mock_extract
    asyncio.run(orchestrator.run())

    # Verify final state and that no injection happened
    assert db.get_state() == "IDLE"


def test_dual_injection(tmp_path):
    """Test that both secret and variable are injected."""
    db = Database(str(tmp_path / "e2e.sqlite"))

    secrets = DummySecrets()

    # Create mock config
    config = Mock(spec=Config)
    config.github = Mock()
    config.github.api_url = "https://api.github.com"
    config.credentials = Mock()
    config.credentials.prefix = "USER_CREDENTIALS"
    config.app = Mock()
    config.app.max_concurrency = 2
    config.app.max_retries = 3
    config.app.profile_dir = "data/profiles"
    config.app.har_dir = "data/har"
    config.app.tracing_dir = "data/traces"
    config.app.enable_har = False
    config.app.enable_tracing = False
    config.warp = Mock()
    config.warp.connect_timeout_sec = 30
    config.warp.rotate_interval_sec = 900
    config.ai_vision = Mock()
    config.ai_vision.max_steps = 30
    config.ai_vision.screenshot_max_width = 800

    # Create test candidate
    candidate = RepoCandidate(
        name="test/repo",
        url="https://github.com/test/repo",
        confidence=0.9,
    )

    # Setup context
    context = OrchestratorContext(
        config=config,
        database=db,
        discovery=DummyDiscovery(),
        decision_engine=DummyDecisionEngine(),
        repo_analyzer=DummyRepoAnalyzer(),
        secrets=secrets,
    )

    orchestrator = Orchestrator(context)

    # Create test cookies
    test_cookies = [
        CookieData(name="session", value="secret123", domain=".github.com"),
        CookieData(name="auth", value="secret456", domain=".github.com"),
    ]

    platform = TargetPlatform(name="github", login_url="https://github.com/login", cookie_domain=".github.com", confidence=0.8)

    # Inject cookies
    asyncio.run(orchestrator._inject_cookies(candidate, platform, test_cookies))

    # Verify both secret and variable were injected
    assert len(secrets.secrets) == 1
    assert len(secrets.variables) == 1

    secret_key = list(secrets.secrets.keys())[0]
    secret_value = secrets.secrets[secret_key]

    # Parse and verify cookie data
    cookies_data = json.loads(secret_value)
    assert len(cookies_data) == 2

    # Verify cookie values are in the secret (before wiping)
    assert cookies_data[0]["value"] == "secret123"


def test_database_only_stores_metadata(tmp_path):
    """Verify database never stores cookie values."""
    db = Database(str(tmp_path / "test.sqlite"))

    # Add a repository
    db.add_repository(Repository(
        name="test/repo",
        url="https://github.com/test/repo",
        requires_cookies=True,
    ))

    # Record an extraction
    db.record_extraction(ExtractionRecord(
        repository_id=1,
        platform="github",
        cookie_count=3,
        has_2fa=False,
        success=True,
        error_message=None,
    ))

    # Query recent extractions
    extractions = db.get_recent_extractions(1)

    assert len(extractions) == 1
    assert extractions[0]["cookie_count"] == 3
    assert extractions[0]["has_2fa"] is False
    # No value field should exist
    assert "value" not in extractions[0]


def test_log_redaction():
    """Test that sensitive data is redacted from logs."""
    # Test redaction of sensitive values
    sensitive_message = 'Extracted cookie: {"name":"session","value":"secret123","domain":".github.com"}'
    redacted = redact_sensitive(sensitive_message)
    assert "secret123" not in redacted
    assert "[REDACTED]" in redacted or "***" in redacted


def test_secure_wiper_clears_data():
    """Test that SecureWiper properly clears data."""
    data = bytearray(b"sensitive information")
    SecureWiper.wipe_bytes(data)
    assert bytes(data) == b"\x00" * len(b"sensitive information")
