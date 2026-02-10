import os
from pathlib import Path

from src.config import load_config, get_env_value
from src.encryption import encrypt_to_string


def main() -> None:
    config = load_config()
    key = get_env_value(config.storage.encryption_key_env)
    if not key:
        raise RuntimeError("Missing encryption key")
    db_path = Path(config.storage.database_path)
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    encrypted = encrypt_to_string(db_path.read_bytes(), key)
    output_path = db_path.with_suffix(".enc")
    output_path.write_text(encrypted, encoding="utf-8")
    os.chmod(output_path, 0o600)
    print(f"Encrypted database written to {output_path}")


if __name__ == "__main__":
    main()
