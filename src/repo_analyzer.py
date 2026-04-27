from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from src.discovery import RepoCandidate
from src.platform_registry import PLATFORM_REGISTRY, PlatformMetadata, infer_login_url


@dataclass
class TargetPlatform:
    name: str
    login_url: str
    cookie_domain: str
    confidence: float


class RepoAnalyzer:
    """Analyze repository contents to determine target platforms for cookie extraction."""

    def __init__(self, github_client=None) -> None:
        self.github_client = github_client

    def analyze(self, candidate: RepoCandidate) -> List[TargetPlatform]:
        """Analyze a repository and return target platforms.

        Args:
            candidate: Discovered repository candidate.

        Returns:
            List of TargetPlatform with confidence scores.
        """
        targets: List[TargetPlatform] = []
        seen: set[str] = set()

        # Try to get the repo object from the candidate if available
        repo = getattr(candidate, "_repo_obj", None)
        if repo is None and self.github_client:
            try:
                repo = self.github_client.get_repo(candidate.name)
            except Exception:
                repo = None

        if repo is None:
            # Fallback: use URL/name-based detection
            return self._fallback_detect(candidate)

        # Scan README
        readme_text = self._fetch_readme(repo)
        if readme_text:
            for name in self._detect_platforms_in_text(readme_text):
                if name not in seen:
                    seen.add(name)
                    meta = PLATFORM_REGISTRY.get(name)
                    if meta:
                        targets.append(self._target_from_meta(meta, confidence=0.8))

        # Scan dependency files
        dep_text = self._fetch_dependencies(repo)
        if dep_text:
            for name in self._detect_platforms_in_text(dep_text):
                if name not in seen:
                    seen.add(name)
                    meta = PLATFORM_REGISTRY.get(name)
                    if meta:
                        targets.append(self._target_from_meta(meta, confidence=0.7))

        # Scan source files for API URLs
        api_domains = self._scan_source_files(repo)
        for domain in api_domains:
            matched = False
            for name, meta in PLATFORM_REGISTRY.items():
                if name in seen:
                    continue
                for d in meta.domains:
                    if d in domain:
                        seen.add(name)
                        targets.append(self._target_from_meta(meta, confidence=0.6))
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                # Dynamic inference
                inferred = infer_login_url(domain)
                targets.append(
                    TargetPlatform(
                        name=domain,
                        login_url=inferred,
                        cookie_domain=domain,
                        confidence=0.4,
                    )
                )

        # Scan workflows for env var references
        wf_text = self._fetch_workflows(repo)
        if wf_text:
            for name in self._detect_platforms_in_text(wf_text):
                if name not in seen:
                    seen.add(name)
                    meta = PLATFORM_REGISTRY.get(name)
                    if meta:
                        targets.append(self._target_from_meta(meta, confidence=0.6))

        return targets

    def _fallback_detect(self, candidate: RepoCandidate) -> List[TargetPlatform]:
        """Fallback detection from repo name/URL only."""
        text = f"{candidate.name} {candidate.url}".lower()
        targets: List[TargetPlatform] = []
        seen: set[str] = set()
        for name, meta in PLATFORM_REGISTRY.items():
            for domain in meta.domains:
                if domain in text:
                    seen.add(name)
                    targets.append(self._target_from_meta(meta, confidence=0.5))
                    break
        return targets

    def _target_from_meta(self, meta: PlatformMetadata, confidence: float) -> TargetPlatform:
        return TargetPlatform(
            name=meta.name,
            login_url=meta.login_url,
            cookie_domain=meta.cookie_domains[0] if meta.cookie_domains else meta.domains[0],
            confidence=confidence,
        )

    def _detect_platforms_in_text(self, text: str) -> List[str]:
        """Find platform names in text using registry keywords."""
        text_lower = text.lower()
        found: List[str] = []
        for name, meta in PLATFORM_REGISTRY.items():
            for domain in meta.domains:
                if domain.lower() in text_lower:
                    found.append(name)
                    break
            if name not in found:
                for pkg in meta.sdk_packages:
                    if pkg.lower() in text_lower:
                        found.append(name)
                        break
            if name not in found:
                for indicator in meta.auth_indicators:
                    if indicator.lower() in text_lower:
                        found.append(name)
                        break
        return found

    def _fetch_readme(self, repo) -> str:
        """Fetch README.md content."""
        try:
            readme = repo.get_contents("README.md")
            if hasattr(readme, "decoded_content"):
                return readme.decoded_content.decode("utf-8", errors="ignore")
        except Exception:
            pass
        return ""

    def _fetch_dependencies(self, repo) -> str:
        """Fetch dependency file contents."""
        files = ["requirements.txt", "package.json", "Cargo.toml", "go.mod", "pyproject.toml"]
        contents: List[str] = []
        for filename in files:
            try:
                file_content = repo.get_contents(filename)
                if hasattr(file_content, "decoded_content"):
                    contents.append(file_content.decoded_content.decode("utf-8", errors="ignore"))
            except Exception:
                continue
        return "\n".join(contents)

    def _scan_source_files(self, repo) -> List[str]:
        """Scan top-level source files for API base URLs."""
        domains: List[str] = []
        url_pattern = re.compile(r"https?://([^/\s\"'`]+)", re.IGNORECASE)
        try:
            contents = repo.get_contents("/")
            for item in contents:
                if item.type != "file":
                    continue
                if not item.name.endswith((".py", ".js", ".ts", ".go", ".rs", ".java")):
                    continue
                try:
                    file_content = repo.get_contents(item.path)
                    if hasattr(file_content, "decoded_content"):
                        text = file_content.decoded_content.decode("utf-8", errors="ignore")
                        found = url_pattern.findall(text)
                        domains.extend(found)
                except Exception:
                    continue
        except Exception:
            pass
        # Deduplicate and filter
        seen: set[str] = set()
        result: List[str] = []
        for d in domains:
            d = d.lower().strip()
            if d not in seen and not d.endswith((".png", ".jpg", ".jpeg", ".gif", ".css", ".js")):
                seen.add(d)
                result.append(d)
        return result

    def _fetch_workflows(self, repo) -> str:
        """Fetch GitHub Actions workflow contents."""
        contents: List[str] = []
        try:
            workflows = repo.get_contents(".github/workflows")
            if not isinstance(workflows, list):
                workflows = [workflows]
            for wf in workflows:
                if hasattr(wf, "decoded_content"):
                    contents.append(wf.decoded_content.decode("utf-8", errors="ignore"))
        except Exception:
            pass
        return "\n".join(contents)
