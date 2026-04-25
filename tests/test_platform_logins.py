import pytest
from unittest.mock import AsyncMock, MagicMock

from src.platform_logins import get_platform_login
from src.platform_logins.base import BasePlatformLogin, TwoFactorAuthError
from src.platform_logins.github import GitHubLogin
from src.platform_logins.gitlab import GitLabLogin
from src.platform_logins.google import GoogleLogin
from src.platform_logins.aws import AWSLogin
from src.platform_logins.azure import AzureLogin


class TestGetPlatformLogin:
    def test_get_github(self):
        login = get_platform_login("github")
        assert isinstance(login, GitHubLogin)

    def test_get_gitlab(self):
        login = get_platform_login("gitlab")
        assert isinstance(login, GitLabLogin)

    def test_get_google(self):
        login = get_platform_login("google")
        assert isinstance(login, GoogleLogin)

    def test_get_aws(self):
        login = get_platform_login("aws")
        assert isinstance(login, AWSLogin)

    def test_get_azure(self):
        login = get_platform_login("azure")
        assert isinstance(login, AzureLogin)

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unsupported platform"):
            get_platform_login("unknown")


class TestGitHubLogin:
    @pytest.mark.asyncio
    async def test_login_runs(self):
        page = MagicMock()
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        login = GitHubLogin()
        await login.login(page, {"username": "user", "password": "pass"})
        assert page.goto.called

    @pytest.mark.asyncio
    async def test_is_logged_in_true(self):
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=1)

        login = GitHubLogin()
        assert await login.is_logged_in(page) is True

    @pytest.mark.asyncio
    async def test_is_logged_in_false(self):
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        login = GitHubLogin()
        assert await login.is_logged_in(page) is False


class TestGitLabLogin:
    @pytest.mark.asyncio
    async def test_login_runs(self):
        page = MagicMock()
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        login = GitLabLogin()
        await login.login(page, {"username": "user", "password": "pass"})
        assert page.goto.called


class TestGoogleLogin:
    @pytest.mark.asyncio
    async def test_login_runs(self):
        page = MagicMock()
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        login = GoogleLogin()
        await login.login(page, {"username": "user", "password": "pass"})
        assert page.goto.called


class TestAWSLogin:
    @pytest.mark.asyncio
    async def test_login_runs(self):
        page = MagicMock()
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        login = AWSLogin()
        await login.login(page, {"username": "user", "password": "pass"})
        assert page.goto.called


class TestAzureLogin:
    @pytest.mark.asyncio
    async def test_login_runs(self):
        page = MagicMock()
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        login = AzureLogin()
        await login.login(page, {"username": "user", "password": "pass"})
        assert page.goto.called


class TestTwoFactorAuthError:
    def test_is_exception(self):
        with pytest.raises(TwoFactorAuthError):
            raise TwoFactorAuthError("2FA required")
