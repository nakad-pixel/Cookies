import json
from pathlib import Path

from src.config import load_config
from src.database import Database


def main() -> None:
    config = load_config()
    db = Database(config.storage.database_path)
    output = Path("audit_log.json")
    rows = []
    with db._connection() as conn:  # intentional internal usage for export
        for row in conn.execute("SELECT event_type, event_payload, created_at FROM audit_log"):
            rows.append({"event_type": row[0], "event_payload": row[1], "created_at": row[2]})
    output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Exported {len(rows)} audit log rows")


if __name__ == "__main__":
    main()
