from __future__ import annotations

import argparse
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/facesignup.db"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("backups"),
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Database not found: {args.source}")
    args.output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = args.output / f"facesignup-{timestamp}.db"

    with sqlite3.connect(args.source) as source, sqlite3.connect(destination) as target:
        source.backup(target)
    print(destination)


if __name__ == "__main__":
    main()
