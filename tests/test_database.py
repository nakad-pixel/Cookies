import pytest

from src.database import Database, Repository, ExtractionRecord


class TestRepository:
    def test_repository_creation(self):
        """Test Repository dataclass creation."""
        repo = Repository(
            name="test/repo",
            url="https://github.com/test/repo",
            requires_cookies=True,
        )
        assert repo.name == "test/repo"
        assert repo.requires_cookies is True


class TestExtractionRecord:
    def test_extraction_record_creation(self):
        """Test ExtractionRecord dataclass creation."""
        record = ExtractionRecord(
            repository_id=1,
            platform="github",
            cookie_count=3,
            has_2fa=False,
            success=True,
        )
        assert record.platform == "github"
        assert record.cookie_count == 3
        assert record.has_2fa is False


class TestDatabase:
    def test_database_initializes_state(self, tmp_path):
        """Test that database initializes with IDLE state."""
        db = Database(str(tmp_path / "test.sqlite"))
        assert db.get_state() == "IDLE"

    def test_set_and_get_state(self, tmp_path):
        """Test setting and getting state."""
        db = Database(str(tmp_path / "test.sqlite"))
        db.set_state("EXTRACTING")
        assert db.get_state() == "EXTRACTING"

    def test_add_and_list_repositories(self, tmp_path):
        """Test adding and listing repositories."""
        db = Database(str(tmp_path / "test.sqlite"))
        repo = Repository(
            name="test/repo",
            url="https://github.com/test/repo",
            requires_cookies=True,
        )
        repo_id = db.add_repository(repo)
        assert repo_id > 0

        repos = db.list_repositories()
        assert len(repos) == 1
        assert repos[0].name == "test/repo"
        assert repos[0].requires_cookies is True

    def test_list_repositories_filter_by_cookies(self, tmp_path):
        """Test filtering repositories by cookie requirement."""
        db = Database(str(tmp_path / "test.sqlite"))

        db.add_repository(Repository("repo1", "url1", requires_cookies=True))
        db.add_repository(Repository("repo2", "url2", requires_cookies=False))
        db.add_repository(Repository("repo3", "url3", requires_cookies=True))

        cookie_repos = db.list_repositories(requires_cookies=True)
        assert len(cookie_repos) == 2

        no_cookie_repos = db.list_repositories(requires_cookies=False)
        assert len(no_cookie_repos) == 1

    def test_add_audit_event(self, tmp_path):
        """Test adding audit events."""
        db = Database(str(tmp_path / "test.sqlite"))
        db.add_audit_event(
            event_type="extraction",
            repository_name="test/repo",
            platform="github",
            status="success",
            message="Extracted 3 cookies",
        )
        # If no exception raised, test passes

    def test_add_platform_config(self, tmp_path):
        """Test adding platform configuration."""
        db = Database(str(tmp_path / "test.sqlite"))
        config_id = db.add_platform_config(
            platform_name="github",
            login_url="https://github.com/login",
            cookie_domain=".github.com",
            requires_auth=True,
        )
        assert config_id > 0

        config = db.get_platform_config("github")
        assert config is not None
        assert config["platform_name"] == "github"
        assert config["login_url"] == "https://github.com/login"
        assert config["requires_auth"] is True

    def test_get_nonexistent_platform_config(self, tmp_path):
        """Test getting config for non-existent platform."""
        db = Database(str(tmp_path / "test.sqlite"))
        config = db.get_platform_config("nonexistent")
        assert config is None

    def test_repository_update_on_conflict(self, tmp_path):
        """Test that adding same repository updates it."""
        db = Database(str(tmp_path / "test.sqlite"))

        db.add_repository(Repository("test/repo", "https://old-url", requires_cookies=False))
        db.add_repository(Repository("test/repo", "https://new-url", requires_cookies=True))

        repos = db.list_repositories()
        assert len(repos) == 1
        assert repos[0].url == "https://new-url"
        assert repos[0].requires_cookies is True
