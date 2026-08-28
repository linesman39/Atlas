# Security Policy

## Reporting a vulnerability

If you find a security issue in Atlas, please report it privately rather than opening a public issue — this gives us a chance to fix it before it's disclosed.

**Preferred**: use [GitHub's private vulnerability reporting](https://github.com/linesman39/Atlas/security/advisories/new) for this repository (Security tab → "Report a vulnerability"). This creates a private advisory only maintainers can see.

Please include:
- What the vulnerability is and where it lives (which module/function).
- Steps to reproduce it, or a minimal proof of concept.
- What you think the impact is (what could an attacker actually do with it).

## What's in scope

- The Engine (`src/atlas/models.py`, `storage.py`, `cartographer/`, `llm/`, `local_annex.py`, `weathering.py`, `ask.py`, `codeowners.py`).
- The Application layer (`adapters/github.py`, `mcp_server.py`) — particularly anything that could let a malicious fact, transcript, or CODEOWNERS entry cause unintended code execution, path traversal, or unauthorized GitHub API actions.

Given Atlas's own principles (`docs/privacy.md`), pay particular attention to:
- Anything that could cause a Field Note or Chart file to be written outside its intended directory (path traversal via a crafted `subject`/`scope` value).
- Anything that could cause `weathering.py`'s `git cat-file` subprocess call to execute unintended commands (it uses list-form subprocess arguments, never a shell, specifically to avoid this class of bug — a finding that this protection has a gap is high-priority).
- Anything that could cause the MCP server or `GitHubAdapter` to take a consequential action (an annexation, a PR, a trade route) without the ground-truthing or human-approval checks actually being enforced.

## What's out of scope

- The optional `ClaudeBackend`/`GitHubAdapter` live API paths' behavior is bounded by Anthropic's and GitHub's own security postures, not Atlas's — report issues with those services to them directly.
- Findings that require an attacker to already have write access to a Chart directory or the ability to run arbitrary code where Atlas runs (at that point, the whole local environment is already compromised).

## Response

This is a young, actively-developed project without a formal SLA yet. We'll do our best to acknowledge a report within a few days and keep you updated as it's investigated and fixed.
