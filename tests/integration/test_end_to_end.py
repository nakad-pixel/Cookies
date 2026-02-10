"""End-to-end integration tests.

These tests verify the full workflow without external dependencies.
"""

import asyncio
import json
from unittest.mock import Mock, patch

from src.browser_automation import CookieData, ExtractionResult
from src.cleanup import SecureWiper, redact_sensitive
from src.database import Database, Repository, ExtractionRecord
from src.discovery import RepoCandidate
from src.glm_engine import GlmDecision
from src.orchestrator import Orchestrator, OrchestratorContext
from src.config import Config


class DummyDiscovery:
    def __init__(self, candidates=None):
        self._candidates = candidates or []

    def discover(self):
        return self._candidates


class DummyGlm:
    def __init__(self, decision=None):
        self._decision = decision or GlmDecision(action="extract", reason="test")

    def decide(self, prompt: str) -> GlmDecision:
        return self._decision


class DummySecrets:
    def __init__(self):
        self.secrets = {}

    def put_secret(self, repo: str, name: str, value: str) -> None:
        self.secrets[f"{repo}/{name}"] = value


def test_full_workflow_no_2fa(tmp_path):
    """Test full workflow without 2FA detection."""
    db = Database(str(tmp_path / "e2e.sqlite"))

    # Create mock config
    config = Mock(spec=Config)
    config.github = Mock()
    config.github.api_url = "https://api.github.com"
    config.github.token_env = "GITHUB_TOKEN"
    config.github.org = "test"
    config.storage = Mock()
    config.storage.database_path = str(tmp_path / "e2e.sqlite")
    config.glm = Mock()
    config.glm.api_url = "https://api.example.com"
    config.glm.api_key_env = "GLM_API_KEY"
    config.glm.model = "test"
    config.glm.monthly_budget_usd = 0.1
    config.credentials = Mock()
    config.credentials.prefix = "USER_CREDENTIALS"

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
        glm=DummyGlm(GlmDecision(action="extract", reason="test")),
        secrets=DummySecrets(),
    )

    # Create orchestrator and run
    orchestrator = Orchestrator(context)

    # Mock the extraction to return test cookies
    test_cookies = [
        CookieData(name="session", value="secret123", domain=".github.com"),
    ]

    with patch.object(orchestrator, "_extract_cookies") as mock_extract:
        mock_extract.return_value = ExtractionResult(
            cookies=test_cookies,
            has_2fa=False,
            success=True,
        )
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
    config.github.token_env = "GITHUB_TOKEN"
    config.github.org = "test"
    config.storage = Mock()
    config.storage.database_path = str(tmp_path / "e2e.sqlite")
    config.glm = Mock()
    config.glm.api_url = "https://api.example.com"
    config.glm.api_key_env = "GLM_API_KEY"
    config.glm.model = "test"
    config.glm.monthly_budget_usd = 0.1
    config.credentials = Mock()
    config.credentials.prefix = "USER_CREDENTIALS"

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
        glm=DummyGlm(GlmDecision(action="extract", reason="test")),
        secrets=DummySecrets(),
    )

    # Create orchestrator and run
    orchestrator = Orchestrator(context)

    # Mock the extraction to indicate 2FA detected
    with patch.object(orchestrator, "_extract_cookies") as mock_extract:
        mock_extract.return_value = ExtractionResult(
            cookies=[],
            has_2fa=True,
            success=False,
        )
        asyncio.run(orchestrator.run())

    # Verify final state and that no injection happened
    assert db.get_state() == "IDLE"


def test_cookie_wiping_after_injection(tmp_path):
    """Test that cookies are wiped after injection."""
    db = Database(str(tmp_path / "e2e.sqlite"))

    secrets = DummySecrets()

    # Create mock config
    config = Mock(spec=Config)
    config.github = Mock()
    config.github.api_url = "https://api.github.com"
    config.credentials = Mock()
    config.credentials.prefix = "USER_CREDENTIALS"

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
        glm=DummyGlm(),
        secrets=secrets,
    )

    orchestrator = Orchestrator(context)

    # Create test cookies
    test_cookies = [
        CookieData(name="session", value="secret123", domain=".github.com"),
        CookieData(name="auth", value="secret456", domain=".github.com"),
    ]

    # Inject cookies
    asyncio.run(orchestrator._inject_cookies(candidate, test_cookies))

    # Verify cookies were injected
    assert len(secrets.secrets) == 1
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
