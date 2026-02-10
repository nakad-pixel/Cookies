from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class EncryptedPayload:
    nonce: bytes
    ciphertext: bytes

    def serialize(self) -> str:
        return ":".join(
            [
                base64.urlsafe_b64encode(self.nonce).decode("utf-8"),
                base64.urlsafe_b64encode(self.ciphertext).decode("utf-8"),
            ]
        )

    @classmethod
    def deserialize(cls, value: str) -> "EncryptedPayload":
        nonce_b64, cipher_b64 = value.split(":", 1)
        return cls(
            nonce=base64.urlsafe_b64decode(nonce_b64.encode("utf-8")),
            ciphertext=base64.urlsafe_b64decode(cipher_b64.encode("utf-8")),
        )


def generate_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")


def _normalize_key(key: str) -> bytes:
    raw = base64.urlsafe_b64decode(key.encode("utf-8"))
    if len(raw) != 32:
        raise ValueError("Encryption key must be 32 bytes (base64-encoded)")
    return raw


def encrypt(plaintext: bytes, key: str) -> EncryptedPayload:
    aesgcm = AESGCM(_normalize_key(key))
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return EncryptedPayload(nonce=nonce, ciphertext=ciphertext)


def decrypt(payload: EncryptedPayload, key: str) -> bytes:
    aesgcm = AESGCM(_normalize_key(key))
    return aesgcm.decrypt(payload.nonce, payload.ciphertext, None)


def encrypt_to_string(plaintext: bytes, key: str) -> str:
    return encrypt(plaintext, key).serialize()


def decrypt_from_string(value: str, key: str) -> bytes:
    return decrypt(EncryptedPayload.deserialize(value), key)
