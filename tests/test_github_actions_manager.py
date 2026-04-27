import pytest
from unittest.mock import Mock, patch

from src.secrets_manager import GitHubActionsManager, PublicKey


class TestGitHubActionsManager:
    def test_creation(self):
        manager = GitHubActionsManager("https://api.github.com", "test-token")
        assert manager.github_api == "https://api.github.com"
        assert manager.token == "test-token"

    @patch("src.secrets_manager.httpx.get")
    def test_get_public_key_caches_result(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"key_id": "123", "key": "YWJj"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        key1 = manager.get_public_key("owner/repo")
        assert mock_get.call_count == 1
        key2 = manager.get_public_key("owner/repo")
        assert mock_get.call_count == 1
        assert key1.key_id == key2.key_id

    @patch("src.secrets_manager.httpx.get")
    @patch("src.secrets_manager.httpx.put")
    def test_put_secret_flow(self, mock_put, mock_get):
        mock_get_response = Mock()
        mock_get_response.json.return_value = {"key_id": "123", "key": "YWJj"}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        mock_put_response = Mock()
        mock_put_response.raise_for_status = Mock()
        mock_put.return_value = mock_put_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.put_secret("owner/repo", "SECRET_NAME", "secret-value")

        assert mock_get.called
        assert mock_put.called

    @patch("src.secrets_manager.httpx.post")
    def test_put_variable_flow(self, mock_post):
        mock_post_response = Mock()
        mock_post_response.raise_for_status = Mock()
        mock_post_response.status_code = 201
        mock_post.return_value = mock_post_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.put_variable("owner/repo", "VAR_NAME", "var-value")

        assert mock_post.called
        call_args = mock_post.call_args
        assert call_args[1]["json"]["name"] == "VAR_NAME"
        assert call_args[1]["json"]["value"] == "var-value"

    @patch("src.secrets_manager.httpx.delete")
    def test_delete_variable(self, mock_delete):
        mock_delete_response = Mock()
        mock_delete_response.status_code = 204
        mock_delete_response.raise_for_status = Mock()
        mock_delete.return_value = mock_delete_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.delete_variable("owner/repo", "VAR_NAME")

        assert mock_delete.called

    @patch("src.secrets_manager.httpx.delete")
    def test_delete_secret(self, mock_delete):
        mock_delete_response = Mock()
        mock_delete_response.status_code = 204
        mock_delete_response.raise_for_status = Mock()
        mock_delete.return_value = mock_delete_response

        manager = GitHubActionsManager("https://api.github.com", "test-token")
        manager.delete_secret("owner/repo", "SECRET_NAME")

        assert mock_delete.called
