from src.discovery import score_cookie_names


def test_score_cookie_names() -> None:
    score = score_cookie_names(["session_id", "foo", "auth_token"])
    assert score > 0.3
