import pytest
from unittest.mock import Mock, patch

from src.secrets_manager import SecretsManager, PublicKey


class TestPublicKey:
    def test_public_key_creation(self):
        """Test PublicKey dataclass creation."""
        key = PublicKey(key_id="12345", key="base64encodedkey")
        assert key.key_id == "12345"
        assert key.key == "base64encodedkey"


class TestSecretsManager:
    def test_secrets_manager_creation(self):
        """Test SecretsManager initialization."""
        manager = SecretsManager("https://api.github.com", "test-token")
        assert manager.github_api == "https://api.github.com"
        assert manager.token == "test-token"

    def test_headers_contains_auth(self):
        """Test that headers include authorization."""
        manager = SecretsManager("https://api.github.com", "test-token")
        headers = manager._headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Accept"] == "application/vnd.github+json"

    @patch("src.secrets_manager.httpx.get")
    def test_get_public_key_caches_result(self, mock_get):
        """Test that public keys are cached."""
        mock_response = Mock()
        mock_response.json.return_value = {"key_id": "123", "key": "YWJj"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = SecretsManager("https://api.github.com", "test-token")

        # First call should hit the API
        key1 = manager.get_public_key("owner/repo")
        assert mock_get.call_count == 1

        # Second call should use cache
        key2 = manager.get_public_key("owner/repo")
        assert mock_get.call_count == 1  # No additional API call
        assert key1.key_id == key2.key_id

    @patch("src.secrets_manager.httpx.get")
    def test_get_public_key_different_repos(self, mock_get):
        """Test fetching keys for different repos."""
        mock_response = Mock()
        mock_response.json.return_value = {"key_id": "123", "key": "YWJj"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = SecretsManager("https://api.github.com", "test-token")

        manager.get_public_key("owner/repo1")
        manager.get_public_key("owner/repo2")

        assert mock_get.call_count == 2

    def test_encrypt_secret_produces_different_output(self):
        """Test that encryption produces different output each time."""
        import base64
        from nacl import public

        # Generate a key pair for testing
        private_key = public.PrivateKey.generate()
        public_key = private_key.public_key

        manager = SecretsManager("https://api.github.com", "test-token")
        pub_key = PublicKey(key_id="123", key=base64.b64encode(bytes(public_key)).decode())

        encrypted1 = manager.encrypt_secret(pub_key, "secret-value")
        encrypted2 = manager.encrypt_secret(pub_key, "secret-value")

        # Should be different due to random nonce
        assert encrypted1 != encrypted2

    @patch("src.secrets_manager.httpx.get")
    @patch("src.secrets_manager.httpx.put")
    def test_put_secret_flow(self, mock_put, mock_get):
        """Test the full put_secret flow."""
        # Mock the public key fetch
        mock_get_response = Mock()
        mock_get_response.json.return_value = {"key_id": "123", "key": "YWJj"}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        # Mock the secret put
        mock_put_response = Mock()
        mock_put_response.raise_for_status = Mock()
        mock_put.return_value = mock_put_response

        manager = SecretsManager("https://api.github.com", "test-token")
        manager.put_secret("owner/repo", "SECRET_NAME", "secret-value")

        assert mock_get.called
        assert mock_put.called

        # Verify the put was called with correct URL
        call_args = mock_put.call_args
        assert "owner/repo/actions/secrets/SECRET_NAME" in call_args[0][0]
