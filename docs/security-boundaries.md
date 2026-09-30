# Security boundaries

## Controls in this demonstration

- The task, initial workspace files, and expected results are synthetic and bundled in the demo.
- The demo creates a fresh temporary workspace; it does not use or modify the current repository as its execution target.
- The policy allows writes only to `discounts.py` and permits only the built-in test action.
- The test process uses a fixed argument vector, `shell=False`, a working directory inside the temporary workspace, a short timeout, and bounded captured output.
- The retry count is fixed at two total attempts.
- SQLite receipts store event metadata and hashes, not file contents or model prompts.
- There are no remote services, API keys, user-selected model endpoints, or live model calls.

## Limits

`tempfile.TemporaryDirectory` is not a security sandbox. Python subprocesses still run with the current user's operating-system permissions and may access the host. The only code run here is the repository's own small synthetic test fixture, and the demo does not ingest arbitrary repositories or model-generated code from outside the package. Do not describe this as safe execution of hostile code.

A production system needs an independently reviewed isolation mechanism with explicit filesystem, network, identity, resource, and lifecycle controls. That is outside this portfolio edition.
