from src.config import load_config
from src.warp_manager import WarpManager


def main() -> None:
    config = load_config()
    manager = WarpManager(connect_timeout_sec=config.warp.connect_timeout_sec)
    manager.connect()
    status = manager.status()
    print(f"Connected: {status.connected}, IP: {status.ip}")
    manager.disconnect()


if __name__ == "__main__":
    main()
