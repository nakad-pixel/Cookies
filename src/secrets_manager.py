from __future__ import annotations

import base64
from dataclasses import dataclass

import httpx
from nacl import public


@dataclass
class PublicKey:
    key_id: str
    key: str


class GitHubActionsManager:
    """Manages GitHub Secrets and Variables injection."""

    def __init__(self, github_api: str, token: str) -> None:
        self.github_api = github_api.rstrip("/")
        self.token = token
        self._cache: dict[str, PublicKey] = {}

    def get_public_key(self, repo: str) -> PublicKey:
        if repo in self._cache:
            return self._cache[repo]
        url = f"{self.github_api}/repos/{repo}/actions/secrets/public-key"
        response = httpx.get(url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        key = PublicKey(key_id=data["key_id"], key=data["key"])
        self._cache[repo] = key
        return key

    def validate_token_permissions(self, repo: str) -> bool:
        """Check if the token can read and write secrets to a repo."""
        try:
            # Try to get the public key (required for secret creation)
            self.get_public_key(repo)
            return True
        except Exception:
            return False

    def encrypt_secret(self, public_key: PublicKey, value: str) -> str:
        key = public.PublicKey(base64.b64decode(public_key.key))
        sealed_box = public.SealedBox(key)
        encrypted = sealed_box.encrypt(value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    def put_secret(self, repo: str, name: str, value: str) -> None:
        public_key = self.get_public_key(repo)
        encrypted_value = self.encrypt_secret(public_key, value)
        url = f"{self.github_api}/repos/{repo}/actions/secrets/{name}"
        payload = {"encrypted_value": encrypted_value, "key_id": public_key.key_id}
        response = httpx.put(url, headers=self._headers(), json=payload, timeout=30)
        response.raise_for_status()

    def delete_secret(self, repo: str, name: str) -> None:
        url = f"{self.github_api}/repos/{repo}/actions/secrets/{name}"
        response = httpx.delete(url, headers=self._headers(), timeout=30)
        if response.status_code != 204:
            response.raise_for_status()

    def put_variable(self, repo: str, name: str, value: str) -> None:
        """Create or update a GitHub Actions variable (unencrypted, visible in UI)."""
        url = f"{self.github_api}/repos/{repo}/actions/variables"
        payload = {"name": name, "value": value}
        response = httpx.post(url, headers=self._headers(), json=payload, timeout=30)
        if response.status_code == 409:
            # Variable already exists — update it
            update_url = f"{self.github_api}/repos/{repo}/actions/variables/{name}"
            response = httpx.patch(update_url, headers=self._headers(), json=payload, timeout=30)
        response.raise_for_status()

    def delete_variable(self, repo: str, name: str) -> None:
        url = f"{self.github_api}/repos/{repo}/actions/variables/{name}"
        response = httpx.delete(url, headers=self._headers(), timeout=30)
        if response.status_code != 204:
            response.raise_for_status()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }


# Backward compatibility alias
SecretsManager = GitHubActionsManager
