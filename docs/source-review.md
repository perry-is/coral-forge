# How the public version was made

## Source project reviewed

The source project reviewed was the private Coral Forge checkout. Its `pyproject.toml` declares a proprietary license. That license is why this portfolio edition was implemented from scratch: source code, tests, benchmark fixtures, configuration, and documentation were not copied into this repository.

## Component review

| Source component | Design observed | Public-edition treatment |
| --- | --- | --- |
| `models.py` | Typed plans, actions, statuses, criteria, and results | Replaced with small standard-library dataclasses and string enums; no source definitions copied |
| `planner.py` | Converts an objective and workspace snapshot into a structured plan | Replaced with a deterministic planner for one invented pricing task |
| `executor.py` | Dispatches typed actions, observes changed files, and records diffs | Replaced with a two-action allowlist, one path, and synthetic diff generation |
| `coding_loop.py` | Runs a bounded attempt loop and handles retry/recovery | Replaced with a two-attempt deterministic loop and one explicit correction |
| `evaluator.py` | Checks observable criteria independently of the coder | Replaced with an evaluator that consumes the fixed test process result |
| `sandbox/policy.py` | Validates action and command policy | Replaced with a small policy rejecting non-allowlisted files/actions |
| `sandbox/broker.py` | Brokers Docker-backed workspace execution | Not copied; temporary directory is used only to isolate the demo from this checkout |
| `task_manager.py` | Persists guarded task/run lifecycle in SQLite | Replaced with a minimal append-only SQLite receipt store; no production schema reused |
| `audit.py` | Appends typed audit events and handoff records | Replaced with metadata-only SQLite events; no production audit format reused |
| `providers/scripted.py` | Supplies deterministic provider responses for tests | Replaced with an in-process scripted decision; no provider adapter copied |
| `providers/ollama.py` | Performs live HTTP model calls, retries, and diagnostics | Excluded; the public demo makes no model or network calls |
| `config.py` / runtime wiring | Loads production runtime options and assembles services | Excluded; no production configuration or environment values were imported |

## Repository inspection

The source repository was reviewed for its package metadata, README and architecture notes, core control-flow components, sandbox policy/broker, provider implementations, tests and fixtures, ignore rules, and tracked file inventory. Its package metadata, runtime integrations, and full test suite are not included here.

The public implementation contains one synthetic scenario, its synthetic unit tests, focused workflow/receipt tests, and documentation written for this edition. No source repository history is present in this directory.
