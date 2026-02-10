import pytest
from unittest.mock import Mock, MagicMock

from src.discovery import (
    DiscoveryEngine,
    RepoCandidate,
    score_cookie_names,
    COOKIE_PATTERNS,
)


class TestRepoCandidate:
    def test_candidate_creation(self):
        """Test RepoCandidate dataclass creation."""
        candidate = RepoCandidate(
            name="test/repo",
            url="https://github.com/test/repo",
            confidence=0.85,
        )
        assert candidate.name == "test/repo"
        assert candidate.confidence == 0.85


class TestScoreCookieNames:
    def test_empty_list_returns_zero(self):
        """Test that empty list scores zero."""
        assert score_cookie_names([]) == 0.0

    def test_all_hits_score_high(self):
        """Test that all matching names score high."""
        score = score_cookie_names(["session_id", "auth_token", "csrf_token"])
        assert score > 0.8

    def test_no_hits_score_low(self):
        """Test that no matching names score low."""
        score = score_cookie_names(["foo", "bar", "baz"])
        assert score < 0.2

    def test_partial_hits_moderate_score(self):
        """Test that partial hits give moderate score."""
        score = score_cookie_names(["session_id", "foo", "bar"])
        assert 0.3 < score < 0.7

    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive."""
        score1 = score_cookie_names(["SESSION_ID"])
        score2 = score_cookie_names(["session_id"])
        assert score1 == score2


class TestCookiePatterns:
    def test_patterns_exist(self):
        """Test that cookie patterns are defined."""
        assert len(COOKIE_PATTERNS) > 0

    def test_session_pattern_matches(self):
        """Test session pattern matching."""
        session_pattern = next(p for p in COOKIE_PATTERNS if "session" in str(p.pattern))
        assert session_pattern.search("session_id")
        assert session_pattern.search("SESSION")

    def test_auth_pattern_matches(self):
        """Test auth pattern matching."""
        auth_pattern = next(p for p in COOKIE_PATTERNS if "auth" in str(p.pattern))
        assert auth_pattern.search("auth_token")
        assert auth_pattern.search("authenticated")


class TestDiscoveryEngine:
    @patch("src.discovery.Github")
    def test_discovery_engine_creation(self, mock_github):
        """Test DiscoveryEngine initialization."""
        engine = DiscoveryEngine("test-token", "test-org")
        assert engine.org == "test-org"

    @patch("src.discovery.Github")
    def test_discover_returns_candidates(self, mock_github_class):
        """Test that discover returns repository candidates."""
        # Setup mock
        mock_github = MagicMock()
        mock_org = MagicMock()
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_repo.html_url = "https://github.com/test/repo"
        mock_repo.stargazers_count = 100

        # Mock get_contents to return files
        mock_file = MagicMock()
        mock_file.type = "file"
        mock_file.name = ".env.example"
        mock_repo.get_contents.return_value = [mock_file]

        mock_org.get_repos.return_value = [mock_repo]
        mock_github.get_organization.return_value = mock_org
        mock_github_class.return_value = mock_github

        engine = DiscoveryEngine("test-token", "test-org")
        candidates = engine.discover()

        assert len(candidates) == 1
        assert candidates[0].name == "test/repo"
        assert candidates[0].confidence > 0

    @patch("src.discovery.Github")
    def test_discover_sorts_by_confidence(self, mock_github_class):
        """Test that discover sorts candidates by confidence."""
        # Setup mock with multiple repos
        mock_github = MagicMock()
        mock_org = MagicMock()

        mock_repo1 = MagicMock()
        mock_repo1.full_name = "test/repo1"
        mock_repo1.html_url = "https://github.com/test/repo1"
        mock_repo1.stargazers_count = 5000  # High stars
        mock_repo1.get_contents.return_value = []

        mock_repo2 = MagicMock()
        mock_repo2.full_name = "test/repo2"
        mock_repo2.html_url = "https://github.com/test/repo2"
        mock_repo2.stargazers_count = 100  # Low stars
        mock_repo2.get_contents.return_value = []

        mock_org.get_repos.return_value = [mock_repo2, mock_repo1]
        mock_github.get_organization.return_value = mock_org
        mock_github_class.return_value = mock_github

        engine = DiscoveryEngine("test-token", "test-org")
        candidates = engine.discover()

        assert len(candidates) == 2
        # Should be sorted by confidence (high stars first)
        assert candidates[0].confidence >= candidates[1].confidence

    @patch("src.discovery.Github")
    def test_score_repo_with_config_files(self, mock_github_class):
        """Test repository scoring with config files."""
        mock_github = MagicMock()
        mock_repo = MagicMock()
        mock_repo.stargazers_count = 0

        # Create mock files
        mock_env = MagicMock()
        mock_env.type = "file"
        mock_env.name = ".env"

        mock_yaml = MagicMock()
        mock_yaml.type = "file"
        mock_yaml.name = "config.yaml"

        mock_repo.get_contents.return_value = [mock_env, mock_yaml]
        mock_github_class.return_value = mock_github

        engine = DiscoveryEngine("test-token", "test-org")
        score = engine._score_repo(mock_repo)

        # Should get 0.1 for each config file
        assert score > 0.1


# Need to import patch at module level
from unittest.mock import patch
