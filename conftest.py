"""Ensures the repo root is on sys.path regardless of how pytest is
invoked, so `from tests.fakes import ...` resolves under both `pytest`
(the console script) and `python -m pytest` (which adds the cwd itself
and would otherwise mask this).

Found by testing a genuinely fresh `git clone` rather than trusting a
working directory that had already accumulated enough incidental state
(a `python -m pytest` habit, stale __pycache__) to paper over the gap.
The `pythonpath` pytest.ini_options setting was tried first and did not
resolve it under the plain `pytest` invocation on this project's pytest
version; this explicit, dependency-free approach does.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
