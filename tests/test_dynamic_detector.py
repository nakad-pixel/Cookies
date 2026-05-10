from unittest.mock import MagicMock

import pytest

from src.discovery import RepoCandidate
from src.dynamic_detector import DynamicPlatformDetector, TargetPlatform


class TestDynamicPlatformDetector:
    def test_detect_buffer_from_readme(self):
        """README with https://buffer.com/login detects Buffer."""
        repo = MagicMock()
        readme = MagicMock()
        readme.decoded_content = b"Check out https://buffer.com/login for publishing."
        repo.get_contents.side_effect = lambda path: {
            "README.md": readme,
        }.get(path, MagicMock())

        candidate = RepoCandidate(name="test/buffer-tool", url="https://github.com/test/buffer-tool", confidence=0.9)
        candidate._repo_obj = repo  # type: ignore[attr-defined]

        targets = DynamicPlatformDetector.detect_from_repo(candidate)
        names = [t.name for t in targets]
        assert "buffer" in names

    def test_detect_multiple_platforms(self):
        """README with Buffer + Twitter links detects both."""
        repo = MagicMock()
        readme = MagicMock()
        readme.decoded_content = b"Uses https://buffer.com and https://twitter.com/login."
        repo.get_contents.side_effect = lambda path: {
            "README.md": readme,
        }.get(path, MagicMock())

        candidate = RepoCandidate(name="test/multi", url="https://github.com/test/multi", confidence=0.9)
        candidate._repo_obj = repo  # type: ignore[attr-defined]

        targets = DynamicPlatformDetector.detect_from_repo(candidate)
        names = [t.name for t in targets]
        assert "buffer" in names
        assert "twitter" in names

    def test_filters_cdn_domains(self):
        """README with cdn.jsdelivr.net is filtered out."""
        repo = MagicMock()
        readme = MagicMock()
        readme.decoded_content = b"Assets from https://cdn.jsdelivr.net/npm/lib."
        repo.get_contents.side_effect = lambda path: {
            "README.md": readme,
        }.get(path, MagicMock())

        candidate = RepoCandidate(name="test/cdn", url="https://github.com/test/cdn", confidence=0.9)
        candidate._repo_obj = repo  # type: ignore[attr-defined]

        targets = DynamicPlatformDetector.detect_from_repo(candidate)
        names = [t.name for t in targets]
        assert "jsdelivr" not in names
        assert "npm" not in names
        assert len(targets) == 0

    def test_groups_subdomains(self):
        """publish.buffer.com and buffer.com grouped as buffer."""
        repo = MagicMock()
        readme = MagicMock()
        readme.decoded_content = b"API at https://publish.buffer.com and https://buffer.com"
        repo.get_contents.side_effect = lambda path: {
            "README.md": readme,
        }.get(path, MagicMock())

        candidate = RepoCandidate(name="test/buffer", url="https://github.com/test/buffer", confidence=0.9)
        candidate._repo_obj = repo  # type: ignore[attr-defined]

        targets = DynamicPlatformDetector.detect_from_repo(candidate)
        names = [t.name for t in targets]
        assert names.count("buffer") == 1
        assert "buffer" in names

    def test_infers_login_url(self):
        """domain example.com -> https://example.com/login"""
        repo = MagicMock()
        readme = MagicMock()
        readme.decoded_content = b"Service at https://example.com"
        repo.get_contents.side_effect = lambda path: {
            "README.md": readme,
        }.get(path, MagicMock())

        candidate = RepoCandidate(name="test/example", url="https://github.com/test/example", confidence=0.9)
        candidate._repo_obj = repo  # type: ignore[attr-defined]

        targets = DynamicPlatformDetector.detect_from_repo(candidate)
        example = [t for t in targets if t.name == "example"]
        assert len(example) == 1
        assert example[0].login_url == "https://example.com/login"

    def test_confidence_scoring(self):
        """README source higher confidence than source file."""
        repo = MagicMock()
        readme = MagicMock()
        readme.decoded_content = b"https://myservice.com"
        source = MagicMock()
        source.decoded_content = b"https://myservice.com/api"
        repo.get_contents.side_effect = lambda path: {
            "README.md": readme,
            "app.py": source,
        }.get(path, MagicMock())
        repo.get_contents = lambda path: {
            "README.md": readme,
            "app.py": source,
        }.get(path, MagicMock())

        # Need to mock top-level listing so _fetch_source_files finds app.py
        top_item = MagicMock()
        top_item.type = "file"
        top_item.name = "app.py"
        top_item.path = "app.py"
        repo.get_contents.return_value = [top_item]
        # Override the specific side effect above for root listing
        def _get_contents(path):
            if path == "/":
                return [top_item]
            mapping = {
                "README.md": readme,
                "app.py": source,
            }
            return mapping.get(path, MagicMock())
        repo.get_contents.side_effect = _get_contents

        candidate = RepoCandidate(name="test/conf", url="https://github.com/test/conf", confidence=0.9)
        candidate._repo_obj = repo  # type: ignore[attr-defined]

        targets = DynamicPlatformDetector.detect_from_repo(candidate)
        myservice = [t for t in targets if t.name == "myservice"]
        assert len(myservice) == 1
        assert myservice[0].confidence == 0.7  # README confidence wins
