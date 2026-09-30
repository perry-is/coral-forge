from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coral_forge_portfolio.receipts import ReceiptStore
from coral_forge_portfolio.workflow import (
    ActionPolicy,
    Planner,
    RunTests,
    WriteFile,
    Workflow,
)


class WorkflowTests(unittest.TestCase):
    def test_demo_retries_once_then_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ReceiptStore(Path(temporary) / "receipts.sqlite3")
            result, output = Workflow(store).run("synthetic-test-run")
            self.assertTrue(result.passed)
            self.assertEqual(result.attempts, 2)
            self.assertIn("Attempt 1: tests failed; retry permitted (1 of 2).", output)
            self.assertIn("Attempt 2: tests passed; evaluation passed.", output)
            events = store.list_for_run(result.run_id)
            kinds = [event["event_type"] for event in events]
            self.assertEqual(kinds[0], "run_started")
            self.assertEqual(kinds[-1], "run_completed")
            self.assertEqual(kinds.count("evaluation"), 2)

    def test_policy_rejects_unlisted_path(self) -> None:
        with self.assertRaises(PermissionError):
            ActionPolicy().check(WriteFile("../outside.txt", "synthetic"))

    def test_policy_accepts_only_known_action_types(self) -> None:
        ActionPolicy().check(RunTests())
        with self.assertRaises(PermissionError):
            ActionPolicy().check(object())  # type: ignore[arg-type]

    def test_planner_rejects_non_synthetic_context(self) -> None:
        planner = Planner()
        with self.assertRaises(ValueError):
            planner.plan(1, "inspect a private customer repository", ("discounts.py",))


if __name__ == "__main__":
    unittest.main()
