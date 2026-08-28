# Atlas — Test Coverage

Measured, not estimated: `pytest --cov=atlas --cov-report=term-missing`, 92 tests, 87% overall statement coverage. Reproduce it yourself:

```bash
pip install -e ".[dev,mcp,github]" pytest-cov
pytest tests/ --cov=atlas --cov-report=term-missing
```

## 100% covered

Every module that is pure Engine logic — the data model, storage, the deterministic and LLM-escalation Cartographer paths, the full annexation orchestration, local (adapter-free) annexation, weathering's evidence-checking logic, Ask-the-Atlas, CODEOWNERS parsing/routing, the LLM backend-selection logic, the local (Ollama) backend, and the evaluation harness's scoring and reporting — is at 100%.

## Honest gaps, and why they're there on purpose

- **`src/atlas/adapters/github.py` (63%)** and **`src/atlas/llm/claude.py` (34%)**: the uncovered lines are the actual live API calls — opening a branch, creating a PR, requesting a fork, calling the Claude Agent SDK. This is deliberate, stated in both modules' own docstrings and in `docs/requirements.md`: these need a real GitHub token/repo or a real model connection to exercise meaningfully, and doing that inside an automated test suite risks silently opening real PRs or spending real money against whatever credentials happen to be in the environment running the tests. Everything *around* those calls — PR body/title formatting, the CODEOWNERS routing that runs after a PR opens, the shareable-fact guard, the extra-not-installed error message — is tested.
- **`src/atlas/eval/run.py` (56%)** and **`src/atlas/weathering.py` (72%)**: the uncovered lines are each module's CLI `main()` wrapper (argument parsing, file writing, exit codes). Both are actually exercised by real subprocess-based tests (`tests/test_weathering_cli.py`, and `run_evaluation()` — the function `main()` calls — is separately 100% covered in `tests/eval/`) but `coverage.py` doesn't track execution across a subprocess boundary by default, so these show as "missed" despite being tested. A tooling artifact, not an untested code path — noted here rather than silently left to look worse than it is.

## What this doesn't cover

Coverage measures whether a line executed during a test, not whether the test's assertions are any good, and not whether the *real* backends (a live Ollama server, a live GitHub repo, a live Claude API call) actually behave the way their mocks assume. See `docs/requirements.md`'s open questions — the first real run of the evaluation harness against an actual model, and the first live exercise of `GitHubAdapter`, are both still open and not something a coverage percentage can stand in for.
