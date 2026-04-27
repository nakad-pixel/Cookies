import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config, get_env_value
from src.secrets_manager import SecretsManager


def main() -> None:
    config = load_config()
    token = get_env_value(config.github.token_env)
    repo = os.getenv("COOKIE_GUARDIAN_REPO")
    if not token or not repo:
        raise RuntimeError("Missing CG_GITHUB_TOKEN or COOKIE_GUARDIAN_REPO")
    secrets = SecretsManager(config.github.api_url, token)
    key = secrets.get_public_key(repo)
    print(f"Public key id: {key.key_id}")


if __name__ == "__main__":
    main()
