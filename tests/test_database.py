from src.database import Repository


def test_database_crud(temp_db) -> None:
    repo_id = temp_db.add_repository(Repository(name="example", url="https://example.com"))
    assert repo_id > 0
    repos = temp_db.list_repositories()
    assert repos[0].name == "example"
    assert temp_db.get_state() == "IDLE"
