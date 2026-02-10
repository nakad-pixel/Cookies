from pathlib import Path

import pytest

from src.database import Database


@pytest.fixture()
def temp_db(tmp_path: Path) -> Database:
    return Database(str(tmp_path / "test.sqlite"))
