#!/usr/bin/env python3
"""Test WARP connection.

This script tests the Cloudflare WARP connection and displays status.
"""

from src.config import load_config
from src.warp_manager import WarpManager


def main() -> None:
    config = load_config()

    print("Testing WARP connection...")
    print(f"Connect timeout: {config.warp.connect_timeout_sec}s")

    try:
        manager = WarpManager(connect_timeout_sec=config.warp.connect_timeout_sec)

        # Check current status
        status = manager.status()
        print(f"Initial status: connected={status.connected}, ip={status.ip}")

        # Try to connect
        print("Connecting to WARP...")
        manager.connect()

        # Check status after connect
        status = manager.status()
        print(f"Connected status: connected={status.connected}, ip={status.ip}")

        # Rotate IP
        print("Rotating IP...")
        manager.rotate_ip()

        # Check status after rotation
        status = manager.status()
        print(f"After rotation: connected={status.connected}, ip={status.ip}")

        # Disconnect
        print("Disconnecting...")
        manager.disconnect()

        status = manager.status()
        print(f"Final status: connected={status.connected}, ip={status.ip}")

        print("\nWARP test completed successfully!")

    except Exception as e:
        print(f"WARP test failed: {e}")
        raise


if __name__ == "__main__":
    main()
