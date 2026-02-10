from __future__ import annotations

import base64
from dataclasses import dataclass

import httpx
from nacl import public


@dataclass
class PublicKey:
    key_id: str
    key: str


class SecretsManager:
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

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }
