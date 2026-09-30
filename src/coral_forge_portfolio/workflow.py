"""Small deterministic plan/execute/evaluate loop for a synthetic task."""

from __future__ import annotations

import difflib
import hashlib
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .receipts import ReceiptStore

OBJECTIVE = "Apply the approved seasonal discount and prove the pricing behavior with tests."
BASELINE_IMPLEMENTATION = "def final_price(price):\n    return round(price, 2)\n"
FIRST_ATTEMPT_IMPLEMENTATION = "def final_price(price):\n    return round(price * 0.90, 2)\n"
EXPECTED_IMPLEMENTATION = "def final_price(price):\n    return round(price * 0.80, 2)\n"
SYNTHETIC_TEST = (
    "import unittest\n"
    "from discounts import final_price\n\n"
    "class PricingTests(unittest.TestCase):\n"
    "    def test_seasonal_discount(self):\n"
    "        self.assertEqual(final_price(100), 80.0)\n\n"
    "if __name__ == '__main__':\n"
    "    unittest.main()\n"
)
MAX_ATTEMPTS = 2
MAX_TEST_SECONDS = 5
MAX_OUTPUT_CHARS = 4000


@dataclass(frozen=True)
class WriteFile:
    path: str
    content: str


@dataclass(frozen=True)
class RunTests:
    purpose: str = "Check the synthetic acceptance test"


@dataclass(frozen=True)
class Plan:
    summary: str
    actions: tuple[WriteFile | RunTests, ...]


@dataclass(frozen=True)
class Evaluation:
    passed: bool
    return_code: int
    summary: str


@dataclass(frozen=True)
class RunResult:
    run_id: str
    passed: bool
    attempts: int
    receipt_count: int


class ActionPolicy:
    """Narrow allowlist for this built-in scenario."""

    def check(self, action: WriteFile | RunTests) -> None:
        if isinstance(action, WriteFile) and action.path != "discounts.py":
            raise PermissionError("only the synthetic discounts.py file may be written")
        if not isinstance(action, (WriteFile, RunTests)):
            raise PermissionError("action type is not allowlisted")


class Planner:
    """Deterministic scripted planner; intentionally does not call an LLM."""

    def plan(self, attempt: int, objective: str, manifest: tuple[str, ...]) -> Plan:
        if objective != OBJECTIVE or "discounts.py" not in manifest:
            raise ValueError("planner input is outside the synthetic scenario")
        content = FIRST_ATTEMPT_IMPLEMENTATION if attempt == 1 else EXPECTED_IMPLEMENTATION
        return Plan(
            summary="Implement the pricing rule, then verify its observable behavior.",
            actions=(WriteFile("discounts.py", content), RunTests()),
        )


class Evaluator:
    """Decides success from the test result, independently of planner claims."""

    def evaluate(self, process: subprocess.CompletedProcess[str]) -> Evaluation:
        passed = process.returncode == 0
        return Evaluation(
            passed=passed,
            return_code=process.returncode,
            summary="acceptance test passed" if passed else "acceptance test failed",
        )


class Workflow:
    def __init__(self, receipt_store: ReceiptStore) -> None:
        self.receipts = receipt_store
        self.policy = ActionPolicy()
        self.planner = Planner()
        self.evaluator = Evaluator()

    def run(self, run_id: str | None = None) -> tuple[RunResult, list[str]]:
        run_id = run_id or f"demo-{uuid4().hex[:8]}"
        output: list[str] = []
        events = 0

        def record(kind: str, data: dict[str, Any]) -> None:
            nonlocal events
            self.receipts.append(run_id, kind, data)
            events += 1

        with tempfile.TemporaryDirectory(prefix="coral-forge-demo-") as temporary:
            workspace = Path(temporary)
            target = workspace / "discounts.py"
            target.write_text(BASELINE_IMPLEMENTATION, encoding="utf-8")
            (workspace / "test_discount.py").write_text(SYNTHETIC_TEST, encoding="utf-8")
            manifest = ("discounts.py", "test_discount.py")
            record("run_started", {"objective": OBJECTIVE, "workspace_manifest": list(manifest)})
            record("disclosure_decision", {"decision": "synthetic task only", "allowed": True})
            record("route_selected", {"route": "local deterministic planner", "external_call": False})
            output.extend((
                "Disclosure: allow (synthetic task only).",
                "Route: local deterministic planner.",
            ))

            succeeded = False
            attempts = 0
            for attempt in range(1, MAX_ATTEMPTS + 1):
                attempts = attempt
                plan = self.planner.plan(attempt, OBJECTIVE, manifest)
                record("plan_created", {"attempt": attempt, "summary": plan.summary, "action_count": len(plan.actions)})
                for action in plan.actions:
                    self.policy.check(action)
                    if isinstance(action, WriteFile):
                        before = target.read_text(encoding="utf-8")
                        target.write_text(action.content, encoding="utf-8")
                        after = target.read_text(encoding="utf-8")
                        diff = "".join(difflib.unified_diff(
                            before.splitlines(keepends=True), after.splitlines(keepends=True),
                            fromfile="before/discounts.py", tofile="after/discounts.py",
                        ))
                        record("file_written", {
                            "attempt": attempt,
                            "path": action.path,
                            "before_sha256": _sha256(before),
                            "after_sha256": _sha256(after),
                            "diff_sha256": _sha256(diff),
                            "diff_lines": len(diff.splitlines()),
                        })
                        output.append(f"Attempt {attempt}: wrote {action.path}.")
                        output.append("Synthetic diff:\n" + diff[:MAX_OUTPUT_CHARS])
                    else:
                        process = _run_fixed_tests(workspace)
                        evaluation = self.evaluator.evaluate(process)
                        record("tests_executed", {
                            "attempt": attempt,
                            "command": "python -B -m unittest discover -s .",
                            "return_code": process.returncode,
                            "timed_out": process.returncode == 124,
                            "output_chars": min(len(process.stdout + process.stderr), MAX_OUTPUT_CHARS),
                            "output_sha256": _sha256((process.stdout + process.stderr)[-MAX_OUTPUT_CHARS:]),
                        })
                        record("evaluation", asdict(evaluation) | {"attempt": attempt})
                        if evaluation.passed:
                            succeeded = True
                            output.append(f"Attempt {attempt}: tests passed; evaluation passed.")
                            break
                        output.append(
                            f"Attempt {attempt}: tests failed; retry permitted ({attempt} of {MAX_ATTEMPTS})."
                            if attempt < MAX_ATTEMPTS
                            else f"Attempt {attempt}: tests failed; retry budget exhausted."
                        )
                if succeeded:
                    break
            record("run_completed", {"passed": succeeded, "attempts": attempts})
            output.append(f"Receipt created: run={run_id}, events={events}.")

        return RunResult(run_id, succeeded, attempts, events), output


def _run_fixed_tests(workspace: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "."],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=MAX_TEST_SECONDS,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return subprocess.CompletedProcess(args=exc.cmd, returncode=124, stdout=stdout, stderr=stderr)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
