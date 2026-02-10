from pathlib import Path

from src.config import load_config, get_env_value
from src.encryption import decrypt_from_string


def main() -> None:
    config = load_config()
    key = get_env_value(config.storage.encryption_key_env)
    if not key:
        raise RuntimeError("Missing encryption key")
    encrypted_path = Path(config.storage.database_path).with_suffix(".enc")
    if not encrypted_path.exists():
        raise FileNotFoundError(encrypted_path)
    plaintext = decrypt_from_string(encrypted_path.read_text(encoding="utf-8"), key)
    output_path = Path(config.storage.database_path)
    output_path.write_bytes(plaintext)
    print(f"Decrypted database written to {output_path}")


if __name__ == "__main__":
    main()
