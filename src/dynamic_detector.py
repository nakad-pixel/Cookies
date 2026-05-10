from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import List, Set

from src.discovery import RepoCandidate


@dataclass
class TargetPlatform:
    name: str
    login_url: str
    cookie_domain: str
    confidence: float


class DynamicPlatformDetector:
    """Dynamically detect external authentication platforms from repository contents."""

    BLOCKLIST: Set[str] = {
        "github.com",
        "api.github.com",
        "raw.githubusercontent.com",
        "githubusercontent.com",
        "npmjs.com",
        "registry.npmjs.org",
        "pypi.org",
        "files.pythonhosted.org",
        "googleapis.com",
        "ajax.googleapis.com",
        "fonts.googleapis.com",
        "storage.googleapis.com",
        "cdn.jsdelivr.net",
        "cdnjs.cloudflare.com",
        "unpkg.com",
        "jsdelivr.net",
        "cloudflare.com",
        "bootstrapcdn.com",
        "stackpath.bootstrapcdn.com",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "w3.org",
        "schema.org",
        "opengraphprotocol.org",
        "ogp.me",
        "gravatar.com",
        "fontawesome.com",
        "fonts.gstatic.com",
        "gstatic.com",
        "googletagmanager.com",
        "google-analytics.com",
        "analytics.google.com",
        "doubleclick.net",
        "googleadservices.com",
        "googleusercontent.com",
        "twimg.com",
        "fbcdn.net",
        "instagram.com",
        "cdninstagram.com",
        "youtube.com",
        "youtu.be",
        "ytimg.com",
        "googlevideo.com",
        "microsoft.com",
        "office.net",
        "office365.com",
        "microsoftonline.com",
        "apple.com",
        "mzstatic.com",
        "akamaized.net",
        "amazonaws.com",
        "s3.amazonaws.com",
        "cloudfront.net",
        "fastly.net",
        "azureedge.net",
        "jsdmirror.com",
    }

    URL_PATTERN = re.compile(r"https?://[^/\s\"'`]+", re.IGNORECASE)
    TLD_PATTERN = re.compile(r"\.[a-z]{2,}$", re.IGNORECASE)

    @classmethod
    def _extract_urls_from_text(cls, text: str) -> List[str]:
        """Extract all URLs from a text block."""
        return cls.URL_PATTERN.findall(text)

    @classmethod
    def _is_service_domain(cls, domain: str) -> bool:
        """Check if a domain is a real service domain (not CDN, not IP, has valid TLD)."""
        domain = domain.lower().strip()
        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]

        # Not IP address
        try:
            ipaddress.ip_address(domain)
            return False
        except ValueError:
            pass

        # Not in blocklist
        if domain in cls.BLOCKLIST:
            return False
        # Also check if any blocklist entry is a suffix match for common CDN patterns
        for blocked in cls.BLOCKLIST:
            if domain == blocked or domain.endswith("." + blocked):
                return False

        # Must have a valid-looking TLD (at least 2 chars after last dot)
        if "." not in domain:
            return False
        tld_part = domain.rsplit(".", 1)[-1]
        if len(tld_part) < 2:
            return False

        return True

    @classmethod
    def _domain_to_platform_name(cls, domain: str) -> str:
        """Extract a platform name from a domain.

        Examples:
            publish.buffer.com -> buffer
            buffer.com -> buffer
            auth.twitter.com -> twitter
        """
        domain = domain.lower().strip()
        parts = domain.split(".")
        # Remove common TLDs and subdomains to get the root domain name
        # We keep the second-level domain as the platform name
        if len(parts) >= 2:
            return parts[-2]
        return parts[0]

    @classmethod
    def _infer_login_urls(cls, domain: str) -> List[str]:
        """Return candidate login URLs for a domain."""
        return [
            f"https://{domain}/login",
            f"https://{domain}/signin",
            f"https://{domain}/auth/login",
            f"https://accounts.{domain}/login",
            f"https://auth.{domain}/login",
        ]

    @classmethod
    def _domain_from_url(cls, url: str) -> str:
        """Extract domain from a URL."""
        # Strip protocol
        url = url.lower().strip()
        if url.startswith("https://"):
            url = url[8:]
        elif url.startswith("http://"):
            url = url[7:]
        # Take only the domain part (before first /)
        return url.split("/")[0]

    @classmethod
    def detect_from_repo(cls, candidate: RepoCandidate) -> List[TargetPlatform]:
        """Detect target platforms from repository contents.

        1. Extract all URLs from README.md, source files, .env.example, docker-compose.yml, dependencies
        2. Filter to service domains only
        3. Group subdomains to root domain
        4. For each unique domain, create TargetPlatform
        5. Return sorted by confidence desc
        """
        sources: List[tuple[str, float]] = []

        repo = getattr(candidate, "_repo_obj", None)

        if repo is not None:
            # README
            readme_text = cls._fetch_readme(repo)
            if readme_text:
                for url in cls._extract_urls_from_text(readme_text):
                    sources.append((url, 0.7))

            # .env.example and docker-compose.yml
            env_text = cls._fetch_env_files(repo)
            if env_text:
                for url in cls._extract_urls_from_text(env_text):
                    sources.append((url, 0.6))

            # Source files
            source_text = cls._fetch_source_files(repo)
            if source_text:
                for url in cls._extract_urls_from_text(source_text):
                    sources.append((url, 0.5))

            # Dependencies
            dep_text = cls._fetch_dependencies(repo)
            if dep_text:
                for url in cls._extract_urls_from_text(dep_text):
                    sources.append((url, 0.4))

        # Fallback: candidate name/url
        fallback_text = f"{candidate.name} {candidate.url}"
        for url in cls._extract_urls_from_text(fallback_text):
            sources.append((url, 0.3))

        # Filter and group domains
        domain_confidence: dict[str, float] = {}
        domain_sources: dict[str, str] = {}

        for url, conf in sources:
            domain = cls._domain_from_url(url)
            if not cls._is_service_domain(domain):
                continue
            # Group to root domain for naming
            root_name = cls._domain_to_platform_name(domain)
            if root_name not in domain_confidence or conf > domain_confidence[root_name]:
                domain_confidence[root_name] = conf
                domain_sources[root_name] = domain

        # Build TargetPlatform list
        targets: List[TargetPlatform] = []
        for name, conf in domain_confidence.items():
            domain = domain_sources[name]
            login_urls = cls._infer_login_urls(domain)
            targets.append(
                TargetPlatform(
                    name=name,
                    login_url=login_urls[0],
                    cookie_domain=domain,
                    confidence=conf,
                )
            )

        targets.sort(key=lambda t: t.confidence, reverse=True)
        return targets

    @classmethod
    def _fetch_readme(cls, repo) -> str:
        try:
            readme = repo.get_contents("README.md")
            if hasattr(readme, "decoded_content"):
                return readme.decoded_content.decode("utf-8", errors="ignore")
        except Exception:
            pass
        return ""

    @classmethod
    def _fetch_env_files(cls, repo) -> str:
        contents: List[str] = []
        for filename in (".env.example", ".env.sample", "docker-compose.yml", "docker-compose.yaml"):
            try:
                file_content = repo.get_contents(filename)
                dc = getattr(file_content, "decoded_content", None)
                if isinstance(dc, bytes):
                    contents.append(dc.decode("utf-8", errors="ignore"))
                elif isinstance(dc, str):
                    contents.append(dc)
            except Exception:
                continue
        return "\n".join(contents)

    @classmethod
    def _fetch_source_files(cls, repo) -> str:
        contents: List[str] = []
        try:
            items = repo.get_contents("/")
            for item in items:
                if getattr(item, "type", None) != "file":
                    continue
                if not getattr(item, "name", "").endswith((".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".php")):
                    continue
                try:
                    file_content = repo.get_contents(getattr(item, "path", ""))
                    dc = getattr(file_content, "decoded_content", None)
                    if isinstance(dc, bytes):
                        contents.append(dc.decode("utf-8", errors="ignore"))
                    elif isinstance(dc, str):
                        contents.append(dc)
                except Exception:
                    continue
        except Exception:
            pass
        return "\n".join(contents)

    @classmethod
    def _fetch_dependencies(cls, repo) -> str:
        files = ["requirements.txt", "package.json", "Cargo.toml", "go.mod", "pyproject.toml", "composer.json", "Gemfile"]
        contents: List[str] = []
        for filename in files:
            try:
                file_content = repo.get_contents(filename)
                dc = getattr(file_content, "decoded_content", None)
                if isinstance(dc, bytes):
                    contents.append(dc.decode("utf-8", errors="ignore"))
                elif isinstance(dc, str):
                    contents.append(dc)
            except Exception:
                continue
        return "\n".join(contents)
