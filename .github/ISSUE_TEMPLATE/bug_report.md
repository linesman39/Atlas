---
name: Bug report
about: Something in the Engine or Application layer doesn't behave as documented
title: ""
labels: bug
---

**What happened**
A clear description of the actual behavior.

**What you expected**
What the docs (or common sense) led you to expect instead — link the relevant doc if there is one (`docs/requirements.md`, `docs/architecture.md`, a module docstring).

**Minimal reproduction**
```python
# The smallest snippet that reproduces it. If it needs a Chart directory
# or specific facts, include how to set those up.
```

**Environment**
- Atlas version / commit:
- Python version:
- Which backend: `local` (Ollama) or `claude`
- Extras installed: (`github`, `claude`, `mcp`, none)

**Evidence**
Per the project's own principle — attach whatever backs up the report: a traceback, the actual vs. expected output, a failing test if you wrote one.
