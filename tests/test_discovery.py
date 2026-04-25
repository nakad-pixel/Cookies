import pytest
from unittest.mock import Mock, MagicMock, patch

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
        mock_github = MagicMock()
        mock_org = MagicMock()
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_repo.html_url = "https://github.com/test/repo"
        mock_repo.stargazers_count = 100

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
        mock_github = MagicMock()
        mock_org = MagicMock()

        mock_repo1 = MagicMock()
        mock_repo1.full_name = "test/repo1"
        mock_repo1.html_url = "https://github.com/test/repo1"
        mock_repo1.stargazers_count = 5000
        mock_repo1.get_contents.return_value = []

        mock_repo2 = MagicMock()
        mock_repo2.full_name = "test/repo2"
        mock_repo2.html_url = "https://github.com/test/repo2"
        mock_repo2.stargazers_count = 100
        mock_repo2.get_contents.return_value = []

        mock_org.get_repos.return_value = [mock_repo2, mock_repo1]
        mock_github.get_organization.return_value = mock_org
        mock_github_class.return_value = mock_github

        engine = DiscoveryEngine("test-token", "test-org")
        candidates = engine.discover()

        assert len(candidates) == 2
        assert candidates[0].confidence >= candidates[1].confidence

    @patch("src.discovery.Github")
    def test_score_repo_with_auth_readme(self, mock_github_class):
        """Test improved scoring when README contains auth keywords."""
        mock_github = MagicMock()
        mock_repo = MagicMock()
        mock_repo.stargazers_count = 0

        mock_readme = MagicMock()
        mock_readme.decoded_content = b"This repo uses API tokens and login sessions for scraping."

        def side_effect(path):
            if path == "README.md":
                return mock_readme
            raise Exception("not found")

        mock_repo.get_contents.side_effect = side_effect
        mock_github_class.return_value = mock_github

        engine = DiscoveryEngine("test-token", "test-org")
        score = engine._score_repo(mock_repo)
        assert score > 0.2

    @patch("src.discovery.Github")
    def test_score_repo_with_dependency_file(self, mock_github_class):
        """Test improved scoring when dependency files contain HTTP client libraries."""
        mock_github = MagicMock()
        mock_repo = MagicMock()
        mock_repo.stargazers_count = 0

        mock_req = MagicMock()
        mock_req.decoded_content = b"requests\nhttpx\nselenium\n"

        def side_effect(path):
            if path == "requirements.txt":
                return mock_req
            raise Exception("not found")

        mock_repo.get_contents.side_effect = side_effect
        mock_github_class.return_value = mock_github

        engine = DiscoveryEngine("test-token", "test-org")
        score = engine._score_repo(mock_repo)
        assert score > 0.1

    @patch("src.discovery.Github")
    def test_score_repo_with_env_file(self, mock_github_class):
        """Test improved scoring when .env.example contains auth env vars."""
        mock_github = MagicMock()
        mock_repo = MagicMock()
        mock_repo.stargazers_count = 0

        mock_env = MagicMock()
        mock_env.decoded_content = b"API_KEY=\nSECRET=\n"

        def side_effect(path):
            if path == ".env.example":
                return mock_env
            raise Exception("not found")

        mock_repo.get_contents.side_effect = side_effect
        mock_github_class.return_value = mock_github

        engine = DiscoveryEngine("test-token", "test-org")
        score = engine._score_repo(mock_repo)
        assert score >= 0.2
