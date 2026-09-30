from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coral_forge_portfolio.receipts import ReceiptStore


class ReceiptStoreTests(unittest.TestCase):
    def test_metadata_receipts_persist_across_store_instances(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipts.sqlite3"
            ReceiptStore(path).append("run-a", "decision", {"route": "local synthetic"})
            rows = ReceiptStore(path).list_for_run("run-a")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["payload"], {"route": "local synthetic"})
            self.assertTrue(path.is_file())

    def test_run_filter_keeps_receipts_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ReceiptStore(Path(temporary) / "receipts.sqlite3")
            store.append("run-a", "done", {"ok": True})
            store.append("run-b", "done", {"ok": False})
            self.assertEqual(len(store.list_for_run("run-a")), 1)
            self.assertEqual(store.list_for_run("run-b")[0]["payload"], {"ok": False})


if __name__ == "__main__":
    unittest.main()
