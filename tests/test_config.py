from src.config import load_config


def test_load_config_defaults() -> None:
    config = load_config()
    assert config.app.name == "cookie-guardian"
    assert config.logging.json is True
