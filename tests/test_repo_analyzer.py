import pytest
from unittest.mock import MagicMock

from src.discovery import RepoCandidate
from src.repo_analyzer import RepoAnalyzer, TargetPlatform


class TestRepoAnalyzer:
    def test_fallback_detect_from_name(self):
        """Test fallback detection from repo name/url."""
        analyzer = RepoAnalyzer()
        candidate = RepoCandidate(
            name="my-org/github-scraper",
            url="https://github.com/my-org/github-scraper",
            confidence=0.9,
        )
        targets = analyzer._fallback_detect(candidate)
        assert len(targets) >= 1
        assert any(t.name == "github" for t in targets)

    def test_detect_platforms_in_text(self):
        analyzer = RepoAnalyzer()
        text = "This project uses the LinkedIn API and Twitter scraping."
        found = analyzer._detect_platforms_in_text(text)
        assert "linkedin" in found
        assert "twitter" in found

    def test_analyze_with_repo_object(self):
        analyzer = RepoAnalyzer()
        candidate = RepoCandidate(
            name="test/repo",
            url="https://github.com/test/repo",
            confidence=0.9,
        )

        mock_repo = MagicMock()
        mock_readme = MagicMock()
        mock_readme.decoded_content = b"This project scrapes Instagram and uses spotipy."
        mock_repo.get_contents.side_effect = lambda path: {
            "README.md": mock_readme,
        }.get(path, MagicMock())

        candidate._repo_obj = mock_repo  # type: ignore[attr-defined]

        targets = analyzer.analyze(candidate)
        names = [t.name for t in targets]
        assert "instagram" in names or "spotify" in names

    def test_analyze_without_repo_object(self):
        analyzer = RepoAnalyzer()
        candidate = RepoCandidate(
            name="test/linkedin-bot",
            url="https://github.com/test/linkedin-bot",
            confidence=0.9,
        )
        targets = analyzer.analyze(candidate)
        names = [t.name for t in targets]
        assert "linkedin" in names

    def test_target_platform_dataclass(self):
        tp = TargetPlatform(
            name="github",
            login_url="https://github.com/login",
            cookie_domain=".github.com",
            confidence=0.8,
        )
        assert tp.name == "github"
        assert tp.confidence == 0.8
