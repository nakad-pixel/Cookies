import pytest
from unittest.mock import Mock, patch

from src.secrets_manager import GitHubActionsManager, PublicKey, SecretsManager


class TestPublicKey:
    def test_public_key_creation(self):
        """Test PublicKey dataclass creation."""
        key = PublicKey(key_id="12345", key="base64encodedkey")
        assert key.key_id == "12345"
        assert key.key == "base64encodedkey"


class TestGitHubActionsManager:
    def test_manager_creation(self):
        """Test GitHubActionsManager initialization."""
        manager = GitHubActionsManager("https://api.github.com", "test-token")
        assert manager.github_api == "https://api.github.com"
        assert manager.token == "test-token"

    def test_headers_contains_auth(self):
        """Test that headers include authorization."""
        manager = GitHubActionsManager("https://api.github.com", "test-token")
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

        manager = GitHubActionsManager("https://api.github.com", "test-token")

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

        manager = GitHubActionsManager("https://api.github.com", "test-token")

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

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        pub_key = PublicKey(key_id="123", key=base64.b64encode(bytes(public_key)).decode())

        encrypted1 = manager.encrypt_secret(pub_key, "secret-value")
        encrypted2 = manager.encrypt_secret(pub_key, "secret-value")

        # Should be different due to random nonce
        assert encrypted1 != encrypted2

    @patch("src.secrets_manager.httpx.get")
    @patch("src.secrets_manager.httpx.put")
    def test_put_secret_flow(self, mock_put, mock_get):
        """Test the full put_secret flow."""
        import base64
        from nacl import public

        # Generate a valid 32-byte public key for testing
        private_key = public.PrivateKey.generate()
        valid_public_key = base64.b64encode(bytes(private_key.public_key)).decode()

        # Mock the public key fetch
        mock_get_response = Mock()
        mock_get_response.json.return_value = {"key_id": "123", "key": valid_public_key}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        # Mock the secret put
        mock_put_response = Mock()
        mock_put_response.raise_for_status = Mock()
        mock_put.return_value = mock_put_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.put_secret("owner/repo", "SECRET_NAME", "secret-value")

        assert mock_get.called
        assert mock_put.called

        # Verify the put was called with correct URL
        call_args = mock_put.call_args
        assert "owner/repo/actions/secrets/SECRET_NAME" in call_args[0][0]

    @patch("src.secrets_manager.httpx.post")
    def test_put_variable_flow(self, mock_post):
        """Test the put_variable flow."""
        mock_post_response = Mock()
        mock_post_response.raise_for_status = Mock()
        mock_post_response.status_code = 201
        mock_post.return_value = mock_post_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.put_variable("owner/repo", "VAR_NAME", "var-value")

        assert mock_post.called
        call_args = mock_post.call_args
        assert "owner/repo/actions/variables" in call_args[0][0]
        assert call_args[1]["json"]["name"] == "VAR_NAME"
        assert call_args[1]["json"]["value"] == "var-value"

    @patch("src.secrets_manager.httpx.post")
    @patch("src.secrets_manager.httpx.patch")
    def test_put_variable_updates_existing(self, mock_patch, mock_post):
        """Test that put_variable updates existing variable on 409."""
        mock_post_response = Mock()
        mock_post_response.status_code = 409
        mock_post_response.raise_for_status = Mock()
        mock_post.return_value = mock_post_response

        mock_patch_response = Mock()
        mock_patch_response.raise_for_status = Mock()
        mock_patch.return_value = mock_patch_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.put_variable("owner/repo", "VAR_NAME", "updated-value")

        assert mock_post.called
        assert mock_patch.called

    @patch("src.secrets_manager.httpx.delete")
    def test_delete_variable(self, mock_delete):
        """Test variable deletion."""
        mock_delete_response = Mock()
        mock_delete_response.status_code = 204
        mock_delete_response.raise_for_status = Mock()
        mock_delete.return_value = mock_delete_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.delete_variable("owner/repo", "VAR_NAME")

        assert mock_delete.called

    @patch("src.secrets_manager.httpx.delete")
    def test_delete_secret(self, mock_delete):
        """Test secret deletion."""
        mock_delete_response = Mock()
        mock_delete_response.status_code = 204
        mock_delete_response.raise_for_status = Mock()
        mock_delete.return_value = mock_delete_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.delete_secret("owner/repo", "SECRET_NAME")

        assert mock_delete.called


class TestSecretsManagerAlias:
    def test_alias_exists(self):
        """Test that SecretsManager is an alias for GitHubActionsManager."""
        assert SecretsManager is GitHubActionsManager
