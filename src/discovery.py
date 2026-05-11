from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from github import Github, GithubException

from src.platform_registry import detect_platform_from_text


COOKIE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"session(_id)?",
        r"auth(_token)?",
        r"jwt",
        r"csrf",
        r"remember_me",
        r"access(_token)?",
        r"refresh(_token)?",
    ]
]

AUTH_KEYWORDS = [
    "api", "scrap", "auth", "login", "session",
    "cookie", "token", "bot", "automation", "crawl",
]

HTTP_CLIENT_LIBRARIES = [
    "requests", "httpx", "axios", "fetch",
    "selenium", "playwright", "puppeteer", "patchright",
]


@dataclass
class RepoCandidate:
    name: str
    url: str
    confidence: float


class DiscoveryEngine:
    def __init__(self, token: str, org: str) -> None:
        self.client = Github(token)
        self.org = org

    def discover(self) -> List[RepoCandidate]:
        """Discover repositories that may need cookies.

        Tries organization first, then falls back to user account.
        """
        repos = self._get_repos()
        candidates: List[RepoCandidate] = []
        for repo in repos:
            confidence = self._score_repo(repo)
            if confidence > 0:
                candidate = RepoCandidate(name=repo.full_name, url=repo.html_url, confidence=confidence)
                # Attach repo object for downstream analysis
                candidate._repo_obj = repo  # type: ignore[attr-defined]
                candidates.append(candidate)
        return sorted(candidates, key=lambda c: c.confidence, reverse=True)

    def _get_repos(self):
        """Get repos from org or user account."""
        try:
            org = self.client.get_organization(self.org)
            return org.get_repos()
        except GithubException as exc:
            if exc.status == 404:
                # Not an organization — try user account
                user = self.client.get_user(self.org)
                return user.get_repos()
            raise

    def _score_repo(self, repo: object) -> float:
        score = 0.0

        # Base score from file extensions / config files
        contents = repo.get_contents("/")
        for item in contents:
            if item.type == "file" and item.name.endswith((".env", ".yaml", ".yml", ".json", ".py", ".js")):
                score += 0.1

        # Analyze specific files for auth indicators
        score += self._analyze_readme(repo)
        score += self._analyze_dependency_files(repo)
        score += self._analyze_env_files(repo)
        score += self._analyze_workflows(repo)

        # Platform detection as a major scoring factor
        score += self._analyze_platform_detection(repo)

        # Stars capped at +0.2
        score += min(repo.stargazers_count / 1000, 0.2)

        return min(score, 1.0)

    def _analyze_readme(self, repo: object) -> float:
        """Scan README.md for auth/scraper keywords and platform domains."""
        try:
            readme = repo.get_contents("README.md")
            if hasattr(readme, "decoded_content"):
                content = readme.decoded_content.decode("utf-8", errors="ignore").lower()
            else:
                return 0.0
            hits = sum(1 for kw in AUTH_KEYWORDS if kw in content)
            # Add platform detection bonus
            platforms = detect_platform_from_text(content)
            platform_bonus = min(len(platforms) * 0.15, 0.4)
            return min(hits * 0.1, 0.4) + platform_bonus
        except Exception:
            return 0.0

    def _analyze_dependency_files(self, repo: object) -> float:
        """Check package files for HTTP client libraries and platform SDKs."""
        files_to_check = ["requirements.txt", "package.json", "Cargo.toml", "go.mod", "pyproject.toml"]
        found = 0
        platform_sdk_found = False
        for filename in files_to_check:
            try:
                file_content = repo.get_contents(filename)
                if hasattr(file_content, "decoded_content"):
                    content = file_content.decoded_content.decode("utf-8", errors="ignore").lower()
                    for lib in HTTP_CLIENT_LIBRARIES:
                        if lib in content:
                            found += 1
                            break
                    from src.platform_registry import PLATFORM_REGISTRY
                    for meta in PLATFORM_REGISTRY.values():
                        for pkg in meta.sdk_packages:
                            if pkg.lower() in content:
                                platform_sdk_found = True
                                break
                        if platform_sdk_found:
                            break
            except Exception:
                continue
        score = min(found * 0.15, 0.3)
        if platform_sdk_found:
            score += 0.2
        return min(score, 0.5)

    def _analyze_env_files(self, repo: object) -> float:
        """Check for .env.example and docker-compose.yml with auth env vars."""
        bonus = 0.0
        try:
            env_ex = repo.get_contents(".env.example")
            if hasattr(env_ex, "decoded_content"):
                content = env_ex.decoded_content.decode("utf-8", errors="ignore").lower()
                if any(kw in content for kw in ["api_key", "token", "secret", "password", "cookie", "auth"]):
                    bonus += 0.2
        except Exception:
            pass

        try:
            dc = repo.get_contents("docker-compose.yml")
            if hasattr(dc, "decoded_content"):
                content = dc.decoded_content.decode("utf-8", errors="ignore").lower()
                if any(kw in content for kw in ["api_key", "token", "secret", "password", "cookie", "auth"]):
                    bonus += 0.2
        except Exception:
            pass

        return min(bonus, 0.4)

    def _analyze_workflows(self, repo: object) -> float:
        """Check GitHub Actions workflows for cookie/auth secrets references."""
        try:
            workflows = repo.get_contents(".github/workflows")
            if not isinstance(workflows, list):
                workflows = [workflows]
            for wf in workflows:
                if hasattr(wf, "decoded_content"):
                    content = wf.decoded_content.decode("utf-8", errors="ignore").lower()
                    if any(kw in content for kw in ["secret", "cookie", "auth", "token", "api_key"]):
                        return 0.3
        except Exception:
            pass
        return 0.0

    def _analyze_platform_detection(self, repo: object) -> float:
        """Score based on platforms detected in repo name and description."""
        try:
            text = f"{repo.full_name} {repo.description or ''}".lower()
        except Exception:
            return 0.0
        platforms = detect_platform_from_text(text)
        return min(len(platforms) * 0.15, 0.3)


def score_cookie_names(names: Iterable[str]) -> float:
    hits = 0
    total = 0
    for name in names:
        total += 1
        if any(pattern.search(name) for pattern in COOKIE_PATTERNS):
            hits += 1
    if total == 0:
        return 0.0
    return min(1.0, hits / total + 0.1)
