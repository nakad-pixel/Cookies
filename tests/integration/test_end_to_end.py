from src.database import Database


def test_end_to_end_smoke(tmp_path) -> None:
    db = Database(str(tmp_path / "e2e.sqlite"))
    assert db.get_state() == "IDLE"
