#!/usr/bin/env python3
"""Initialize the Cookie Guardian database.

This script creates the SQLite database with metadata tables only.
NO cookie values are stored in the database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.database import Database


def main() -> None:
    config = load_config()
    Database(config.storage.database_path)
    print(f"Database initialized at: {config.storage.database_path}")
    print("Note: This database stores only metadata - NO cookie values")


if __name__ == "__main__":
    main()
