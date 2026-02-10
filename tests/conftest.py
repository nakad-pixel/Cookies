import pytest
from pathlib import Path

from src.database import Database


@pytest.fixture()
def temp_db(tmp_path: Path) -> Database:
    """Create a temporary database for testing."""
    return Database(str(tmp_path / "test.sqlite"))


@pytest.fixture()
def sample_repository():
    """Return a sample repository for testing."""
    from src.database import Repository
    return Repository(
        name="test/repo",
        url="https://github.com/test/repo",
        requires_cookies=True,
    )


@pytest.fixture()
def sample_extraction_result():
    """Return a sample extraction result for testing."""
    from src.browser_automation import CookieData, ExtractionResult
    return ExtractionResult(
        cookies=[
            CookieData(name="session", value="test123", domain=".github.com"),
            CookieData(name="auth", value="test456", domain=".github.com"),
        ],
        cookie_count=2,
        has_2fa=False,
        success=True,
    )
