Run the SQL guardrail test suite and report any failures.

Steps:
1. Run `pytest tests/unit/test_guardrail.py -v`.
2. If all pass: confirm coverage of blocked statement types (DELETE, UPDATE, INSERT, DROP, EXEC, stacked queries).
3. If any fail: show the failing assertion, identify whether it's a false positive (safe SQL blocked) or false negative (dangerous SQL passed), and suggest the fix.
4. Never suggest disabling or weakening the guardrail to make tests pass.
