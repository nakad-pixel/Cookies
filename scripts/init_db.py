from src.config import load_config
from src.database import Database


def main() -> None:
    config = load_config()
    Database(config.storage.database_path)
    print("Database initialized")


if __name__ == "__main__":
    main()
