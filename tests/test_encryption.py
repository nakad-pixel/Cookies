from src.encryption import decrypt_from_string, encrypt_to_string, generate_key


def test_encrypt_roundtrip() -> None:
    key = generate_key()
    payload = encrypt_to_string(b"secret", key)
    assert decrypt_from_string(payload, key) == b"secret"
