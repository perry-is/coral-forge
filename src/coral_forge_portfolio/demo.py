"""Command-line entry point for the synthetic Coral Forge demo."""

from __future__ import annotations

import argparse
from pathlib import Path

from .receipts import ReceiptStore
from .workflow import Workflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic Coral Forge workflow demo.")
    parser.add_argument("--db-path", type=Path, default=Path(".local/forge.sqlite3"))
    args = parser.parse_args()
    store = ReceiptStore(args.db_path)
    result, lines = Workflow(store).run()
    for line in lines:
        print(line)
    print(
        f"Receipt: run={result.run_id} events={result.receipt_count} "
        f"database={args.db_path.as_posix()}"
    )
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
