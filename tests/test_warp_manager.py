from src.warp_manager import WarpManager, WarpStatus


def test_warp_status_parsing(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        class Result:
            stdout = "Status: Connected\nIP: 203.0.113.1\n"
        return Result()

    monkeypatch.setattr("src.warp_manager.subprocess.run", fake_run)
    manager = WarpManager()
    status = manager.status()
    assert status == WarpStatus(connected=True, ip="203.0.113.1")
