import base64

from nacl import public

from src.secrets_manager import PublicKey, SecretsManager


def test_encrypt_secret_roundtrip() -> None:
    private_key = public.PrivateKey.generate()
    public_key = private_key.public_key
    encoded = base64.b64encode(bytes(public_key)).decode("utf-8")
    secrets = SecretsManager("https://api.github.com", "token")
    payload = secrets.encrypt_secret(PublicKey(key_id="1", key=encoded), "value")
    sealed_box = public.SealedBox(private_key)
    decrypted = sealed_box.decrypt(base64.b64decode(payload))
    assert decrypted.decode("utf-8") == "value"
