from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from src.browser_automation import BrowserAutomation, CookieData, ExtractionResult
from src.cleanup import SecureWiper
from src.config import Config, get_credentials_for_platform, get_env_value, load_config
from src.database import Database, ExtractionRecord, Repository
from src.discovery import DiscoveryEngine, RepoCandidate
from src.glm_engine import GlmDecision, GlmEngine
from src.logger import log_cookie_extraction, log_event, log_secret_injection, setup_logger
from src.secrets_manager import SecretsManager
from src.warp_manager import WarpManager


class State(str, Enum):
    """Orchestrator states following the ephemeral flow."""
    IDLE = "IDLE"
    DISCOVERING = "DISCOVERING"
    EXTRACTING = "EXTRACTING"
    INJECTING = "INJECTING"
    CLEANUP = "CLEANUP"
    COMPLETED = "COMPLETED"


@dataclass
class OrchestratorContext:
    """Context for the orchestrator."""
    config: Config
    database: Database
    discovery: DiscoveryEngine
    glm: GlmEngine
    secrets: SecretsManager
    warp: Optional[WarpManager] = None
    browser: Optional[BrowserAutomation] = None


class Orchestrator:
    """Main orchestrator implementing ephemeral cookie handling.

    Flow: DISCOVER → EXTRACT → INJECT → CLEANUP
    - Cookies are extracted into memory only
    - Immediately injected to GitHub Secrets
    - Wiped from memory immediately after injection
    - No persistent local storage of cookie values
    """

    def __init__(self, context: OrchestratorContext) -> None:
        self.context = context
        self.logger = setup_logger("cookie-guardian")
        self._extracted_cookies: List[CookieData] = []  # Track for cleanup

    async def run(self) -> None:
        """Run the main orchestrator workflow."""
        try:
            # Phase 1: Discovery
            await self._transition(State.DISCOVERING)
            candidates = await self._discover_repositories()

            if not candidates:
                log_event(self.logger, "No repositories found requiring cookies")
                await self._transition(State.IDLE)
                return

            # Phase 2-4: For each candidate, extract, inject, cleanup
            for candidate in candidates:
                await self._process_repository(candidate)

            await self._transition(State.COMPLETED)
            log_event(self.logger, "Orchestrator run completed successfully")

        except Exception as e:
            log_event(self.logger, "Orchestrator failed", error=str(e))
            raise
        finally:
            # Ensure cleanup runs even on failure
            await self._cleanup()

    async def _discover_repositories(self) -> List[RepoCandidate]:
        """Discover repositories that may need cookies."""
        log_event(self.logger, "Starting repository discovery")
        candidates = self.context.discovery.discover()

        # Filter to repositories that likely need authentication
        filtered = []
        for candidate in candidates:
            # Use GLM to analyze if this repo needs cookies
            decision = self.context.glm.decide(
                f"Analyze repository {candidate.name} at {candidate.url}. "
                "Does this repository likely require authentication cookies for external services? "
                "Respond with action: 'extract' if likely, 'skip' if not."
            )
            log_event(
                self.logger,
                "GLM decision for repository",
                repo=candidate.name,
                action=decision.action,
                reason=decision.reason
            )

            if decision.action.lower() in ("extract", "yes", "true"):
                filtered.append(candidate)
                # Store in database
                self.context.database.add_repository(
                    Repository(
                        name=candidate.name,
                        url=candidate.url,
                        requires_cookies=True
                    )
                )

        log_event(self.logger, f"Discovered {len(filtered)} repositories requiring cookies")
        return filtered

    async def _process_repository(self, candidate: RepoCandidate) -> None:
        """Process a single repository: extract → inject → cleanup."""
        log_event(self.logger, "Processing repository", repo=candidate.name)

        # Get the repository ID from database
        repos = self.context.database.list_repositories()
        repo_id = None
        for repo in repos:
            if repo.name == candidate.name:
                # Find the ID by querying - we need to store this properly
                break

        # Phase 2: Extraction
        extraction_result = await self._extract_cookies(candidate)

        if extraction_result.has_2fa:
            log_event(
                self.logger,
                f"Skipping {candidate.name} - 2FA detected",
                repo=candidate.name,
                status="skipped_2fa"
            )
            self._record_extraction(candidate, extraction_result)
            return

        if not extraction_result.success:
            log_event(
                self.logger,
                f"Extraction failed for {candidate.name}",
                repo=candidate.name,
                error=extraction_result.error_message
            )
            self._record_extraction(candidate, extraction_result)
            return

        # Track cookies for cleanup
        self._extracted_cookies.extend(extraction_result.cookies)

        # Phase 3: Injection
        await self._inject_cookies(candidate, extraction_result.cookies)

        # Phase 4: Cleanup (immediate)
        await self._cleanup_repository(candidate, extraction_result)

    async def _extract_cookies(self, candidate: RepoCandidate) -> ExtractionResult:
        """Extract cookies for a repository."""
        await self._transition(State.EXTRACTING)

        # Rotate IP if WARP is available
        if self.context.warp:
            try:
                self.context.warp.rotate_ip()
                log_event(self.logger, "WARP IP rotated")
            except Exception as e:
                log_event(self.logger, "WARP rotation failed", error=str(e))

        # Determine platform from repository
        platform = self._detect_platform(candidate)

        # Get credentials if available
        credentials = get_credentials_for_platform(platform, self.context.config)

        # Extract cookies using browser automation
        browser = self.context.browser or BrowserAutomation(headless=True)

        login_url = self._get_login_url(platform, candidate)

        result = browser.extract_cookies(
            url=login_url,
            username=credentials.get("username") if credentials else None,
            password=credentials.get("password") if credentials else None,
            platform=platform
        )

        log_cookie_extraction(
            self.logger,
            platform=platform,
            cookie_count=len(result.cookies),
            has_2fa=result.has_2fa
        )

        return result

    async def _inject_cookies(self, candidate: RepoCandidate, cookies: List[CookieData]) -> None:
        """Inject cookies to GitHub Secrets."""
        await self._transition(State.INJECTING)

        if not cookies:
            log_event(self.logger, "No cookies to inject", repo=candidate.name)
            return

        # Serialize cookies as JSON (this is the last time we see the values)
        cookies_data = [
            {
                "name": c.name,
                "value": c.value,  # This is the sensitive value being injected
                "domain": c.domain,
                "expires": c.expires,
                "secure": c.secure,
                "httpOnly": c.http_only,
            }
            for c in cookies
        ]
        cookies_json = json.dumps(cookies_data)

        # Inject to GitHub Secrets
        secret_name = f"COOKIES_{self._sanitize_secret_name(candidate.name)}"

        try:
            self.context.secrets.put_secret(candidate.name, secret_name, cookies_json)
            log_secret_injection(self.logger, candidate.name, secret_name)
        except Exception as e:
            log_event(self.logger, "Secret injection failed", repo=candidate.name, error=str(e))
            raise

    async def _cleanup_repository(
        self,
        candidate: RepoCandidate,
        extraction_result: ExtractionResult
    ) -> None:
        """Cleanup sensitive data for a single repository."""
        await self._transition(State.CLEANUP)

        # Wipe all cookie values from memory
        extraction_result.wipe_cookies()

        # Record metadata (no sensitive values)
        self._record_extraction(candidate, extraction_result)

        log_event(
            self.logger,
            "Cleanup completed - cookie values wiped from memory",
            repo=candidate.name
        )

    def _record_extraction(self, candidate: RepoCandidate, result: ExtractionResult) -> None:
        """Record extraction metadata to database."""
        # Note: This only records metadata, not cookie values
        record = ExtractionRecord(
            repository_id=0,  # Would need to fetch actual ID
            platform=self._detect_platform(candidate),
            cookie_count=len(result.cookies),
            has_2fa=result.has_2fa,
            success=result.success,
            error_message=result.error_message,
            expires_at=None,  # Could parse from cookies
        )

        self.context.database.add_audit_event(
            event_type="extraction",
            repository_name=candidate.name,
            platform=record.platform,
            status="success" if result.success else ("2fa" if result.has_2fa else "failed"),
            message=f"Extracted {record.cookie_count} cookies" if result.success else result.error_message
        )

    async def _cleanup(self) -> None:
        """Final cleanup - ensure all sensitive data is wiped."""
        # Wipe any remaining cookie data
        for cookie in self._extracted_cookies:
            cookie.wipe()
        self._extracted_cookies = []

        # Force garbage collection
        SecureWiper.force_gc()

        # Clear any temp files
        SecureWiper.clear_temp_files(pattern="cookie_*")

        await self._transition(State.IDLE)

    async def _transition(self, state: State) -> None:
        """Transition to a new state."""
        self.context.database.set_state(state.value)
        log_event(self.logger, "state_transition", state=state.value)

    def _detect_platform(self, candidate: RepoCandidate) -> str:
        """Detect the platform from repository name or URL."""
        name_lower = candidate.name.lower()
        url_lower = candidate.url.lower()

        if "github" in name_lower or "github" in url_lower:
            return "github"
        elif "gitlab" in name_lower or "gitlab" in url_lower:
            return "gitlab"
        elif "google" in name_lower or "gcp" in name_lower:
            return "google"
        elif "aws" in name_lower or "amazon" in name_lower:
            return "aws"
        elif "azure" in name_lower or "microsoft" in name_lower:
            return "azure"
        else:
            return "generic"

    def _get_login_url(self, platform: str, candidate: RepoCandidate) -> str:
        """Get the login URL for a platform."""
        platform_urls = {
            "github": "https://github.com/login",
            "gitlab": "https://gitlab.com/users/sign_in",
            "google": "https://accounts.google.com/signin",
            "aws": "https://signin.aws.amazon.com/signin",
            "azure": "https://login.microsoftonline.com/",
        }
        return platform_urls.get(platform, candidate.url)

    def _sanitize_secret_name(self, repo_name: str) -> str:
        """Convert repo name to valid GitHub secret name."""
        # Replace invalid characters with underscores
        sanitized = repo_name.replace("/", "_").replace("-", "_").replace(".", "_")
        # Remove any non-alphanumeric characters except underscore
        sanitized = "".join(c if c.isalnum() or c == "_" else "" for c in sanitized)
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "REPO_" + sanitized
        return sanitized.upper()


def build_orchestrator() -> Orchestrator:
    """Build and configure the orchestrator."""
    config = load_config()
    token = get_env_value(config.github.token_env)
    if not token:
        raise RuntimeError("Missing GitHub token")

    glm_key = get_env_value(config.glm.api_key_env)

    # Initialize components
    database = Database(config.storage.database_path)
    discovery = DiscoveryEngine(token=token, org=config.github.org)
    glm = GlmEngine(
        api_url=config.glm.api_url,
        api_key=glm_key,
        model=config.glm.model,
        monthly_budget_usd=config.glm.monthly_budget_usd,
    )
    secrets = SecretsManager(config.github.api_url, token)

    # Optional components
    warp: Optional[WarpManager] = None
    try:
        warp = WarpManager(connect_timeout_sec=config.warp.connect_timeout_sec)
    except Exception:
        pass  # WARP is optional

    browser = BrowserAutomation(headless=True)

    context = OrchestratorContext(
        config=config,
        database=database,
        discovery=discovery,
        glm=glm,
        secrets=secrets,
        warp=warp,
        browser=browser,
    )

    return Orchestrator(context)


if __name__ == "__main__":
    asyncio.run(build_orchestrator().run())
