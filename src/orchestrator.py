from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from src.browser_automation import BrowserAutomation, CookieData, ExtractionResult
from src.cleanup import SecureWiper
from src.config import Config, get_credentials_for_platform, get_env_value, get_github_token, load_config
from src.database import Database, ExtractionRecord, Repository
from src.decision_engine import DecisionEngine
from src.discovery import DiscoveryEngine, RepoCandidate
from src.logger import (
    log_cookie_extraction,
    log_event,
    log_secret_injection,
    log_variable_injection_warning,
    setup_logger,
)
from src.repo_analyzer import RepoAnalyzer, TargetPlatform
from src.retry_manager import RetryManager
from src.secrets_manager import GitHubActionsManager
from src.warp_manager import WarpManager


def _log_credential_status(config: Config, logger: logging.Logger) -> None:
    """Log which credential sources are available at startup."""
    sources_checked = []

    # Check unified JSON
    unified = get_env_value("USER_CREDENTIALS")
    if unified:
        try:
            parsed = json.loads(unified)
            if isinstance(parsed, dict):
                platform_keys = [k for k in parsed.keys() if k != "default"]
                has_default = "default" in parsed
                sources_checked.append(
                    f"USER_CREDENTIALS with {len(platform_keys)} platform(s)"
                    + (" + default" if has_default else "")
                )
            else:
                sources_checked.append("USER_CREDENTIALS set but not a valid JSON object")
        except json.JSONDecodeError:
            sources_checked.append("USER_CREDENTIALS set but invalid JSON")
    else:
        sources_checked.append("USER_CREDENTIALS: not set")

    # Check fallback
    fallback_user = get_env_value(config.credentials.fallback_username_env)
    fallback_pass = get_env_value(config.credentials.fallback_password_env)
    if fallback_user and fallback_pass:
        sources_checked.append(f"{config.credentials.fallback_username_env}: set")
    else:
        sources_checked.append(f"{config.credentials.fallback_username_env}: not set")

    log_event(logger, "Credential sources checked", sources=sources_checked)

    # Warn if absolutely nothing is configured
    if not unified and not (fallback_user and fallback_pass):
        log_event(
            logger,
            "WARNING: No credentials configured. All extractions will be skipped. "
            "Set either USER_CREDENTIALS (JSON with platform credentials) or "
            f"{config.credentials.fallback_username_env}/{config.credentials.fallback_password_env} "
            "as GitHub Secrets.",
            severity="WARNING",
        )


class State(str, Enum):
    """Orchestrator states following the ephemeral flow."""
    IDLE = "IDLE"
    DISCOVERING = "DISCOVERING"
    ANALYZING = "ANALYZING"
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
    decision_engine: DecisionEngine
    repo_analyzer: RepoAnalyzer
    secrets: GitHubActionsManager
    warp: Optional[WarpManager] = None
    browser: Optional[BrowserAutomation] = None


class Orchestrator:
    """Main orchestrator implementing ephemeral cookie handling.

    Flow: DISCOVER → ANALYZE → EXTRACT → INJECT → CLEANUP
    - Cookies are extracted into memory only
    - Immediately injected to GitHub Secrets AND Variables
    - Wiped from memory immediately after injection
    - No persistent local storage of cookie values
    """

    def __init__(self, context: OrchestratorContext) -> None:
        self.context = context
        self.logger = setup_logger(
            "cookie-guardian",
            log_file=os.environ.get("CG_LOG_FILE"),
        )
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

            # Phase 2: Analyze each candidate to find target platforms
            await self._transition(State.ANALYZING)
            repo_platform_pairs: List[Tuple[RepoCandidate, TargetPlatform, int]] = []
            for candidate in candidates:
                platforms = self.context.repo_analyzer.analyze(candidate)
                decision = self.context.decision_engine.decide(
                    repo_name=candidate.name,
                    description=None,
                    platforms_detected=platforms,
                )
                log_event(
                    self.logger,
                    "Decision for repository",
                    repo=candidate.name,
                    action=decision.action,
                    reason=decision.reason,
                )
                if decision.action.lower() in ("extract", "yes", "true"):
                    # Store in database and capture the real repo ID
                    repo_id = self.context.database.add_repository(
                        Repository(
                            name=candidate.name,
                            url=candidate.url,
                            requires_cookies=True,
                        )
                    )
                    for platform in platforms:
                        repo_platform_pairs.append((candidate, platform, repo_id))

            if not repo_platform_pairs:
                log_event(self.logger, "No (repo, platform) pairs to process")
                await self._transition(State.IDLE)
                return

            # Phase 3-5: Process (repo, platform) pairs with bounded concurrency
            semaphore = asyncio.Semaphore(self.context.config.app.max_concurrency)

            async def _process_with_semaphore(
                candidate: RepoCandidate,
                platform: TargetPlatform,
                repo_id: int,
            ) -> None:
                async with semaphore:
                    await self._process_repo_platform(candidate, platform, repo_id)

            await asyncio.gather(*[
                _process_with_semaphore(c, p, rid)
                for c, p, rid in repo_platform_pairs
            ])

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
        log_event(self.logger, f"Discovered {len(candidates)} candidate repositories")
        return candidates

    async def _process_repo_platform(
        self,
        candidate: RepoCandidate,
        platform: TargetPlatform,
        repo_id: int,
    ) -> None:
        """Process a single (repo, platform) pair: extract → inject → cleanup."""
        log_event(
            self.logger,
            "Processing repository-platform pair",
            repo=candidate.name,
            platform=platform.name,
        )

        # Phase 3: Extraction
        extraction_result = await self._extract_cookies(candidate, platform)

        if extraction_result.has_2fa:
            log_event(
                self.logger,
                f"Skipping {candidate.name} - 2FA detected",
                repo=candidate.name,
                platform=platform.name,
                status="skipped_2fa",
            )
            self._record_extraction(candidate, platform, extraction_result, repo_id=repo_id)
            return

        if extraction_result.has_captcha:
            log_event(
                self.logger,
                f"Skipping {candidate.name} - CAPTCHA detected",
                repo=candidate.name,
                platform=platform.name,
                status="skipped_captcha",
            )
            self._record_extraction(candidate, platform, extraction_result, repo_id=repo_id)
            return

        if not extraction_result.success:
            log_event(
                self.logger,
                f"Extraction failed for {candidate.name}",
                repo=candidate.name,
                platform=platform.name,
                error=extraction_result.error_message,
            )
            self._record_extraction(candidate, platform, extraction_result, repo_id=repo_id)
            return

        # Track cookies for cleanup
        self._extracted_cookies.extend(extraction_result.cookies)

        # Phase 4: Injection (both Secret and Variable)
        await self._inject_cookies(candidate, platform, extraction_result.cookies)

        # Phase 5: Cleanup (immediate)
        await self._cleanup_repo_platform(candidate, platform, extraction_result, repo_id=repo_id)

    async def _extract_cookies(
        self,
        candidate: RepoCandidate,
        platform: TargetPlatform,
    ) -> ExtractionResult:
        """Extract cookies for a (repo, platform) pair with retry/backoff and WARP rotation."""
        await self._transition(State.EXTRACTING)

        # Rotate IP if WARP is available (async)
        if self.context.warp:
            try:
                await self.context.warp.rotate_ip_async()
                log_event(self.logger, "WARP IP rotated")
            except Exception as e:
                log_event(self.logger, "WARP rotation failed", error=str(e))

        result = get_credentials_for_platform(platform.name, self.context.config)
        if result:
            credentials, source = result
            log_event(self.logger, f"Using {source} credentials for {platform.name}",
                      platform=platform.name, credential_source=source)
        else:
            log_event(
                self.logger,
                f"No credentials for {platform.name}, skipping extraction. "
                f"Checked: USER_CREDENTIALS['{platform.name}'], USER_CREDENTIALS['default'], "
                f"USER_CREDENTIALS_{platform.name.upper()}, {self.context.config.credentials.fallback_username_env}",
                platform=platform.name,
            )
            return ExtractionResult(
                success=False,
                error_message=f"No credentials for {platform.name}",
            )

        browser = self.context.browser or BrowserAutomation(headless=True)

        retry_manager = RetryManager(
            max_attempts=self.context.config.app.max_retries,
            multiplier=2.0,
            min_wait=5.0,
            max_wait=60.0,
        )

        @retry_manager.retry_with_warp_rotation(
            warp=self.context.warp,
            exceptions=(Exception,),
        )
        async def _do_extract() -> ExtractionResult:
            return await browser.extract_cookies(
                url=platform.login_url,
                username=credentials.get("username") if credentials else None,
                password=credentials.get("password") if credentials else None,
                platform=platform.name,
            )

        result = await _do_extract()

        log_cookie_extraction(
            self.logger,
            platform=platform.name,
            cookie_count=len(result.cookies),
            has_2fa=result.has_2fa,
        )

        return result

    async def _inject_cookies(
        self,
        candidate: RepoCandidate,
        platform: TargetPlatform,
        cookies: List[CookieData],
    ) -> None:
        """Inject cookies to GitHub Secrets AND Variables."""
        await self._transition(State.INJECTING)

        if not cookies:
            log_event(self.logger, "No cookies to inject", repo=candidate.name)
            return

        # Serialize cookies as JSON (this is the last time we see the values)
        cookies_data = [
            {
                "name": c.name,
                "value": c.value,  # Sensitive value
                "domain": c.domain,
                "expires": c.expires,
                "secure": c.secure,
                "httpOnly": c.http_only,
            }
            for c in cookies
        ]
        cookies_json = json.dumps(cookies_data)

        secret_name = self._sanitize_secret_name(f"COOKIES_{platform.name}_{candidate.name}")

        # Inject to GitHub Secrets
        try:
            self.context.secrets.put_secret(candidate.name, secret_name, cookies_json)
            log_secret_injection(self.logger, candidate.name, secret_name)
        except Exception as e:
            log_event(self.logger, "Secret injection failed", repo=candidate.name, error=str(e))
            raise

        # Inject to GitHub Variables (with security warning)
        try:
            self.context.secrets.put_variable(candidate.name, secret_name, cookies_json)
            log_variable_injection_warning(self.logger, candidate.name, secret_name)
        except Exception as e:
            log_event(self.logger, "Variable injection failed", repo=candidate.name, error=str(e))
            # Don't raise — variable injection is best-effort

    async def _cleanup_repo_platform(
        self,
        candidate: RepoCandidate,
        platform: TargetPlatform,
        extraction_result: ExtractionResult,
        repo_id: int,
    ) -> None:
        """Cleanup sensitive data for a single (repo, platform) pair."""
        await self._transition(State.CLEANUP)

        # Wipe all cookie values from memory
        extraction_result.wipe_cookies()

        # Record metadata (no sensitive values)
        self._record_extraction(candidate, platform, extraction_result, repo_id=repo_id)

        log_event(
            self.logger,
            "Cleanup completed - cookie values wiped from memory",
            repo=candidate.name,
            platform=platform.name,
        )

    def _record_extraction(
        self,
        candidate: RepoCandidate,
        platform: TargetPlatform,
        result: ExtractionResult,
        repo_id: int,
    ) -> None:
        """Record extraction metadata to database."""
        record = ExtractionRecord(
            repository_id=repo_id,
            platform=platform.name,
            cookie_count=len(result.cookies),
            has_2fa=result.has_2fa,
            success=result.success,
            error_message=result.error_message,
            expires_at=None,
        )

        self.context.database.add_audit_event(
            event_type="extraction",
            repository_name=candidate.name,
            platform=record.platform,
            status="success" if result.success else ("2fa" if result.has_2fa else "failed"),
            message=f"Extracted {record.cookie_count} cookies" if result.success else result.error_message,
        )

        # Also record in extractions table
        try:
            self.context.database.record_extraction(record)
        except Exception:
            pass

    async def _cleanup(self) -> None:
        """Final cleanup - ensure all sensitive data is wiped."""
        # Wipe any remaining cookie data
        for cookie in self._extracted_cookies:
            cookie.wipe()
        self._extracted_cookies = []

        # Close browser if we created it
        if self.context.browser:
            try:
                await self.context.browser.close()
            except Exception:
                pass

        # Force garbage collection
        SecureWiper.force_gc()

        # Clear any temp files
        SecureWiper.clear_temp_files(pattern="cookie_*")

        await self._transition(State.IDLE)

    async def _transition(self, state: State) -> None:
        """Transition to a new state."""
        self.context.database.set_state(state.value)
        log_event(self.logger, "state_transition", state=state.value)

    def _sanitize_secret_name(self, name: str) -> str:
        """Convert name to valid GitHub secret/variable name."""
        sanitized = name.replace("/", "_").replace("-", "_").replace(".", "_")
        sanitized = "".join(c if c.isalnum() or c == "_" else "" for c in sanitized)
        if sanitized and not sanitized[0].isalpha():
            sanitized = "REPO_" + sanitized
        return sanitized.upper()


def build_orchestrator() -> Orchestrator:
    """Build and configure the orchestrator."""
    config = load_config()
    token = get_github_token(config)
    if not token:
        raise RuntimeError("Missing GitHub token. Set CG_GITHUB_TOKEN environment variable.")

    # Initialize components
    database = Database(config.storage.database_path)
    discovery = DiscoveryEngine(token=token, org=config.github.org)
    decision_engine = DecisionEngine()
    repo_analyzer = RepoAnalyzer()
    secrets = GitHubActionsManager(config.github.api_url, token)

    # Optional components
    warp: Optional[WarpManager] = None
    try:
        # In CI (GitHub Actions), WARP requires --accept-tos
        in_ci = bool(os.environ.get("GITHUB_ACTIONS") or os.environ.get("CI"))
        warp = WarpManager(
            connect_timeout_sec=config.warp.connect_timeout_sec,
            accept_tos=in_ci,
        )
    except Exception:
        pass  # WARP is optional

    browser = BrowserAutomation(
        headless=True,
        profile_dir=config.app.profile_dir,
        enable_har=config.app.enable_har,
        har_dir=config.app.har_dir,
        enable_tracing=config.app.enable_tracing,
        tracing_dir=config.app.tracing_dir,
    )

    context = OrchestratorContext(
        config=config,
        database=database,
        discovery=discovery,
        decision_engine=decision_engine,
        repo_analyzer=repo_analyzer,
        secrets=secrets,
        warp=warp,
        browser=browser,
    )

    orchestrator = Orchestrator(context)
    _log_credential_status(config, orchestrator.logger)
    return orchestrator


if __name__ == "__main__":
    asyncio.run(build_orchestrator().run())
