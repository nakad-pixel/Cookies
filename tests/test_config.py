import pytest
from unittest.mock import patch

from src.config import (
    load_config,
    get_env_value,
    get_credentials_for_platform,
    Config,
    AppConfig,
    GitHubConfig,
    StorageConfig,
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


class TestConfigClasses:
    def test_app_config_frozen(self):
        """Test that AppConfig is immutable."""
        config = AppConfig(name="test", max_concurrency=3, shard_id=0, shard_total=1)
        with pytest.raises(Exception):  # FrozenInstanceError
            config.name = "modified"

    def test_github_config_creation(self):
        """Test GitHubConfig creation."""
        config = GitHubConfig(
            api_url="https://api.github.com",
            graphql_url="https://api.github.com/graphql",
            org="test-org",
            token_env="GITHUB_TOKEN",
        )
        assert config.org == "test-org"
        assert config.token_env == "GITHUB_TOKEN"

    def test_storage_config_creation(self):
        """Test StorageConfig creation."""
        config = StorageConfig(database_path="data/test.sqlite")
        assert config.database_path == "data/test.sqlite"
