import pytest
from unittest.mock import patch

from src.config import (
    load_config,
    _resolve_config_path,
    get_env_value,
    get_credentials_for_platform,
    Config,
    AppConfig,
    GitHubConfig,
    StorageConfig,
    AiVisionConfig,
)


class TestLoadConfig:
    def test_load_default_config(self, tmp_path):
        """Test loading default configuration."""
        # Create a minimal config file
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""
app:
  name: test-app
  max_concurrency: 5

github:
  org: test-org
""")
        config = load_config(config_path)

        assert isinstance(config, Config)
        assert config.app.name == "test-app"
        assert config.app.max_concurrency == 5
        assert config.github.org == "test-org"

    def test_load_config_uses_defaults(self, tmp_path):
        """Test that config uses defaults for missing values."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""
app:
  name: test
""")
        config = load_config(config_path)

        assert config.app.name == "test"
        assert config.app.max_concurrency == 3  # Default
        assert config.app.profile_dir == "data/profiles"
        assert config.app.max_retries == 3
        assert config.github.api_url == "https://api.github.com"  # Default

    def test_storage_config_no_encryption(self, tmp_path):
        """Test that storage config does not include encryption."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""
storage:
  database_path: data/test.sqlite
""")
        config = load_config(config_path)

        assert config.storage.database_path == "data/test.sqlite"
        # Should not have encryption_key_env attribute
        assert not hasattr(config.storage, 'encryption_key_env')

    def test_ai_vision_config(self, tmp_path):
        """Test that ai_vision config is parsed correctly."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""
ai_vision:
  engine: openrouter
  gemini_api_key_env: MY_GEMINI_KEY
  max_steps: 20
""")
        config = load_config(config_path)

        assert isinstance(config.ai_vision, AiVisionConfig)
        assert config.ai_vision.engine == "openrouter"
        assert config.ai_vision.gemini_api_key_env == "MY_GEMINI_KEY"
        assert config.ai_vision.max_steps == 20
        assert config.ai_vision.screenshot_max_width == 800  # Default

    def test_no_glm_section(self, tmp_path):
        """Test that old glm section is not required."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""
app:
  name: test
""")
        config = load_config(config_path)
        # Should not have glm attribute
        assert not hasattr(config, 'glm')


class TestGetEnvValue:
    def test_get_env_value_returns_value(self):
        """Test getting an environment variable value."""
        with patch.dict("os.environ", {"TEST_VAR": "test_value"}):
            result = get_env_value("TEST_VAR")
            assert result == "test_value"

    def test_get_env_value_returns_default(self):
        """Test getting default when env var not set."""
        result = get_env_value("NONEXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_get_env_value_empty_returns_default(self):
        """Test that empty string returns default."""
        with patch.dict("os.environ", {"EMPTY_VAR": ""}):
            result = get_env_value("EMPTY_VAR", "default")
            assert result == "default"

    def test_get_env_value_none_returns_default(self):
        """Test that None returns default."""
        result = get_env_value("NONEXISTENT", "fallback")
        assert result == "fallback"


class TestGetCredentialsForPlatform:
    def test_get_credentials_success(self):
        """Test successful credential retrieval."""
        creds_json = '{"username": "testuser", "password": "testpass"}'
        with patch.dict("os.environ", {"USER_CREDENTIALS_GITHUB": creds_json}):
            result = get_credentials_for_platform("github")

        assert result is not None
        assert result["username"] == "testuser"
        assert result["password"] == "testpass"

    def test_get_credentials_missing_env(self):
        """Test when credentials env var is not set."""
        result = get_credentials_for_platform("nonexistent")
        assert result is None

    def test_get_credentials_invalid_json(self):
        """Test handling of invalid JSON."""
        with patch.dict("os.environ", {"USER_CREDENTIALS_GITHUB": "not json"}):
            result = get_credentials_for_platform("github")

        assert result is None

    def test_get_credentials_custom_prefix(self, tmp_path):
        """Test getting credentials with custom prefix."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""
credentials:
  prefix: MY_CREDS
""")
        config = load_config(config_path)

        creds_json = '{"username": "user", "password": "pass"}'
        with patch.dict("os.environ", {"MY_CREDS_AWS": creds_json}):
            result = get_credentials_for_platform("aws", config)

        assert result is not None
        assert result["username"] == "user"


class TestResolveConfigPath:
    def test_env_var_override(self, tmp_path):
        """COOKIE_GUARDIAN_CONFIG overrides everything when the file exists."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("app:\n  name: env-override\n")
        with patch.dict("os.environ", {"COOKIE_GUARDIAN_CONFIG": str(config_path)}):
            resolved = _resolve_config_path()
        assert resolved == config_path

    def test_env_var_missing_raises(self, tmp_path):
        """If COOKIE_GUARDIAN_CONFIG points to a missing file, fail fast."""
        missing = tmp_path / "missing.yaml"
        with patch.dict("os.environ", {"COOKIE_GUARDIAN_CONFIG": str(missing)}):
            with pytest.raises(FileNotFoundError) as exc_info:
                _resolve_config_path()
        assert "COOKIE_GUARDIAN_CONFIG is set but file not found" in str(exc_info.value)

    def test_package_relative_fallback(self, tmp_path, monkeypatch):
        """When env var is absent and package-relative config exists, use it."""
        fake_package = tmp_path / "src" / "config.py"
        fake_package.parent.mkdir(parents=True)
        fake_package.write_text("")
        pkg_config = tmp_path / "config.yaml"
        pkg_config.write_text("app:\n  name: pkg-relative\n")

        with patch.dict("os.environ", {}, clear=True):
            with patch("src.config.__file__", str(fake_package)):
                resolved = _resolve_config_path()
        assert resolved == pkg_config

    def test_cwd_fallback(self, tmp_path, monkeypatch):
        """When package-relative is missing and CWD config exists, use it."""
        fake_package = tmp_path / "src" / "config.py"
        fake_package.parent.mkdir(parents=True)
        fake_package.write_text("")
        cwd_config = tmp_path / "config.yaml"
        cwd_config.write_text("app:\n  name: cwd-fallback\n")

        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            with patch("src.config.__file__", str(fake_package)):
                resolved = _resolve_config_path()
        assert resolved == cwd_config

    def test_missing_config_error_message(self, tmp_path, monkeypatch):
        """When no config is found anywhere, raise with actionable message."""
        fake_package = tmp_path / "src" / "config.py"
        fake_package.parent.mkdir(parents=True)
        fake_package.write_text("")

        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            with patch("src.config.__file__", str(fake_package)):
                with pytest.raises(FileNotFoundError) as exc_info:
                    _resolve_config_path()
        msg = str(exc_info.value)
        assert "config.yaml not found" in msg
        assert "config.yaml.example" in msg
        assert "COOKIE_GUARDIAN_CONFIG" in msg


class TestConfigClasses:
    def test_app_config_frozen(self):
        """Test that AppConfig is immutable."""
        config = AppConfig(
            name="test",
            max_concurrency=3,
            shard_id=0,
            shard_total=1,
            profile_dir="data/profiles",
            max_retries=3,
            har_dir="data/har",
            tracing_dir="data/traces",
            enable_har=False,
            enable_tracing=False,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            config.name = "modified"

    def test_github_config_creation(self):
        """Test GitHubConfig creation."""
        config = GitHubConfig(
            api_url="https://api.github.com",
            graphql_url="https://api.github.com/graphql",
            org="test-org",
            token_env="CG_GITHUB_TOKEN",
        )
        assert config.org == "test-org"
        assert config.token_env == "CG_GITHUB_TOKEN"

    def test_storage_config_creation(self):
        """Test StorageConfig creation."""
        config = StorageConfig(database_path="data/test.sqlite")
        assert config.database_path == "data/test.sqlite"

    def test_ai_vision_config_creation(self):
        """Test AiVisionConfig creation."""
        config = AiVisionConfig(
            engine="gemini",
            gemini_api_key_env="GEMINI_API_KEY",
            openrouter_api_key_env="OPENROUTER_API_KEY",
            ollama_url="http://localhost:11434",
            max_steps=30,
            screenshot_max_width=800,
        )
        assert config.engine == "gemini"
        assert config.max_steps == 30
