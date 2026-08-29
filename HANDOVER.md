# Atlas — Handover

A complete account of what Atlas is, why it exists, what's built and verified, what's built but unverified, and what's still open — written so anyone (including a future session) can pick this up cold.

---

## 1. Where this came from

This project started as a submission idea for a micro1 hackathon. Partway through, two things happened:
1. The hackathon's actual rules (a separate document from the initial brief PDF) turned out to require assigning submission ownership to micro1 — incompatible with the open-source plan.
2. The user decided to drop the hackathon framing entirely: **"forget about the hackathon, let's build Atlas — the open source project the world will never forget and depend on for the next decade."**

Everything from that point on was built as a standalone open-source project, not a competition entry. All hackathon-era language has been swept out of the docs. `docs/hackathon-brief.pdf` remains in the repo only as a historical artifact of where the initial idea came from.

## 2. The core idea

**Atlas is what git is for code, but for the context and decisions behind it.**

The problem: coding-agent sessions lose things. Context gets compressed to fit a window and a constraint stated early quietly drops out (a documented phenomenon — Chroma's "context rot" research). A fresh session on a repo it's worked before starts cold except for a static, hand-written `CLAUDE.md`. An agent on one repo has no way to know what another repo's team already learned the hard way.

The mechanism: a team of agents takes **Field Notes** on a live session, a **Cartographer** checks each candidate fact for evidence and contradiction, and only ground-truthed, non-conflicting facts get **annexed** — promoted — into a **Chart** (one repo's durable memory) and from there into **the Atlas** (a workspace's memory across repos). Full vocabulary in `docs/lexicon.md`.

**Two claimed differentiators**, checked against six existing systems (Letta, Mem0, Zep/Graphiti, Claude Code's own auto memory, Cognee, LangMem) from official sources only — see `docs/competitive-landscape.md`:
1. **Ground-truthing**: a fact needs a linked test result, diff, or command output before it can be promoted. Five of six systems reviewed store what an LLM asserted, with no evidence requirement.
2. **A cross-repository tier**: none of the six maintain memory across repos.

## 3. The architectural spine: Engine vs. Application

This is the single organizing decision everything else follows from, arrived at after the user pushed back hard on an early design that assumed a paid hosted LLM by default:

> **git costs nothing and needs no service to function. GitHub is optional, hosted, and built on top.** Atlas draws the same line.

- **The Engine** — the data model, Chart/Atlas storage, the Cartographer, and every LLM-backed agent — runs completely offline, for $0, forever. It defaults to a free local model via Ollama. `pip install atlas-cartographer` pulls in only `pydantic`, `PyYAML`, `rapidfuzz` — no paid-service dependency at all.
- **The Application** — GitHub-hosted annexation, the MCP server, the (not yet built) visualization layer — is optional, built on top, adds convenience and collaboration, never capability the Engine lacks.

This shows up concretely in code: `src/atlas/adapters/github.py` and `src/atlas/llm/claude.py` both lazily import their third-party dependency with a clear error message if the optional extra isn't installed, so the base package never requires them.

**A real cost finding worth keeping**: the Claude Agent SDK's default configuration loads a full skill/command/system-prompt set on every call — about $0.09 and ~22k cache-creation tokens for a one-word reply. A lean config (`setting_sources=[]`, `skills=None`, a narrow system prompt) cuts that to ~$0.002. Documented in `docs/architecture.md` even though it's not the default path anymore.

## 4. Documentation map

| Doc | What's in it |
|---|---|
| `docs/project-definition.md` | Locked scope: who has this problem, the three tiers, differentiators, baseline. |
| `docs/competitive-landscape.md` | Six existing systems, researched from official sources only — the evidence behind the differentiator claims. |
| `docs/lexicon.md` | Full vocabulary (Field Notes, the Chart, the Atlas, the Cartographer, annexation, Surveyor-General, etc.) — deliberately not git's own terms. |
| `docs/vision.md` | The unscoped north star — visualization, cross-org sharing, the "git successor" framing taken to its logical end. Explicitly not the build spec. |
| `docs/requirements.md` | The functional spec, with live status markers (✅/⏳) against every component — the single most up-to-date "what's built" reference. |
| `docs/architecture.md` | Technology decisions and why, organized by Engine vs. Application. |
| `docs/open-source.md` | License (Apache-2.0), governance, distribution, dependency license check. |
| `docs/privacy.md` | What Atlas stores, where, what should never go in a Field Note. |
| `docs/naming-considerations.md` | Real collision risk for "Atlas" as a name (MongoDB Atlas, ChatGPT Atlas, a near-identical MCP server already live) — researched, not decided. |
| `docs/testing.md` | Measured coverage (88%, 100% on pure Engine logic), and an honest account of why some gaps exist. |
| `CHANGELOG.md` | Keep-a-Changelog format, built from the actual git log. |
| `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` | Standard OSS scaffolding, written in the project's own voice (a contribution is a Survey — claim plus evidence). |

## 5. What's built, module by module

All of this is real, working code with passing tests — not scaffolding or stubs, except where explicitly marked.

**The Engine** (100% test coverage on every module in this list):
- `models.py` — `Fact`, `FieldNote`, `AnnexationRequest`, `BorderDispute`, typed throughout with Pydantic.
- `storage.py` — Markdown+YAML Chart/Atlas storage, modeled on Claude Code's own verified auto-memory pattern. Includes `sanitize_path_component`, the shared sanitizer that closes a path-traversal gap found and fixed this session (see §7).
- `cartographer/deterministic.py` — the deterministic-first conflict check: structured-value comparison, honestly returns `AMBIGUOUS` for narrative claims rather than faking a semantic judgment.
- `cartographer/llm_escalation.py` — the LLM path, reached only for genuinely ambiguous cases.
- `cartographer/evaluate.py` — the full annexation check: ground-truthing → deterministic → LLM escalation, in that order, with `resolved_by` always populated so the eval harness can report how often the expensive path was actually needed.
- `llm/` — pluggable `LLMBackend`; `OllamaBackend` (stdlib `urllib` only, zero deps) is the default; `ClaudeBackend` is opt-in via the `claude` extra.
- `agents/field_agent.py`, `agents/briefing_agent.py` — real LLM-backed implementations (extraction, and two genuinely different briefing prompts for a human vs. a fresh agent).
- `local_annex.py` — adapter-free annexation: a file write on Cartographer approval, no GitHub required. This is what makes the Engine's own annexation path free and complete on its own.
- `weathering.py` — re-verification of already-annexed facts' evidence (git object existence, file existence), with a CLI entrypoint. Honest scope limit stated in the module: checks existence, not whether a test still passes.
- `ask.py` — Ask-the-Atlas; every answer must cite the fact ids it relies on.
- `codeowners.py` — CODEOWNERS parsing and fact-to-owner routing.
- `eval/` — the evaluation harness: hand-labeled fixtures (deliberately not LLM-generated — see the module's own docstring on why), per-tier recall, border-dispute catch rate, false-annexation rate, a Markdown+JSON report. Single entrypoint: `python -m atlas.eval.run`.

**The Application layer**:
- `adapters/github.py` — `GitHubAdapter`: annexation-as-pull-request, `propose_trade_route` (cross-org sharing, refuses non-shareable facts), and CODEOWNERS routing **wired into the live PR-open call**, not just built standalone. PR formatting and routing logic are unit-tested with mocked PyGithub objects; the actual live API calls (branch creation, PR open, fork) are real, ordinary PyGithub usage that has never been exercised against a real repository — deliberately, to avoid a test run silently opening real PRs.
- `mcp_server.py` — five MCP tools: `record_field_note`, `propose_annexation` (defaults to local annexation — works with zero GitHub config), `query_chart`, `get_briefing`, `ask_the_atlas`. Tested in-process via `server.call_tool` — no live transport or model needed.

**Packaging**: `pyproject.toml` splits dependencies so `pip install atlas-cartographer` gets only the free Engine; `[github]`, `[claude]`, `[mcp]` are additive extras. Verified: the package builds cleanly, passes `twine check`, and the built wheel installs and runs correctly in a genuinely fresh venv — not just the editable install used throughout development.

**Not built**: the visualization layer (TypeScript/React/deck.gl/D3/FastAPI/Docker — a real, separate stack, not attempted).

## 6. Test status

**93 tests, all passing**, verified repeatedly in throwaway clean venvs matching CI's exact install profile (most recently `pip install -e ".[dev,mcp,github]"` — no PyGithub/claude-agent-sdk live credentials needed for any of it).

**Measured coverage: 88% overall, 100% on every pure Engine-logic module.** The honest gaps, per `docs/testing.md`:
- `adapters/github.py` (63%) and `llm/claude.py` (34%) — the uncovered lines are the actual live API calls, deliberately untested for the reason above.
- `eval/run.py` (56%) and `weathering.py`'s CLI wrapper (72%) — both are genuinely exercised by real subprocess-based tests, but `coverage.py` doesn't track execution across a subprocess boundary, so they show as "missed" despite being tested. A tooling artifact, documented as such rather than left to look worse than it is.

## 7. Issues found and fixed this session

- **A real path-traversal gap.** While writing `SECURITY.md`, a claim about path safety was tested before being written down (per this project's own ground-truthing principle) rather than asserted. `storage.write_fact` already sanitized a Fact's `subject` before it touched a path; `GitHubAdapter`'s PR-path construction and `codeowners.owners_for_fact`'s synthetic-path construction did not — both only replaced spaces. A crafted subject like `../../etc/passwd` could influence the constructed GitHub path. Fixed by extracting one shared sanitizer (`storage.sanitize_path_component`) used everywhere a subject becomes part of a path. Regression test added: `test_malicious_subject_cannot_escape_the_chart_directory`.
- **PyPI name collision.** `atlas-map` was already taken — by an unrelated Rust tool that also maps codebases for LLM agents, confusingly in the same broad space. Renamed to `atlas-cartographer` (verified available on PyPI) across every reference.
- **A cosmetic commit-message defect.** One commit's message lost a few words (`` `twine check` ``) to shell backtick-substitution when passed as a plain string rather than a heredoc. Purely cosmetic — the actual committed code is unaffected. Not amended (repo history isn't rewritten without being asked).

## 8. Blocked by this session's environment — not something you need to act on, just honesty about what wasn't independently verified

- **The Docker build.** No Docker daemon is available in this sandboxed container (a `ulimit` permission restriction blocks `dockerd` from starting). The `Dockerfile` follows standard patterns and is labeled in its own header as unverified — someone with a working daemon needs to confirm `docker build .` actually succeeds.
- **Pushing the `v0.1.0` git tag.** Branch pushes work fine from this session; a tag push gets a consistent `403`, most likely a deliberate scope restriction on this session's git credentials (tags are often treated as more release-sensitive than branch commits). The tag exists locally in this session only. Run `git tag -a v0.1.0 -m "..."` (see `CHANGELOG.md` for the versioning policy) and `git push origin v0.1.0` from a machine with full push access.
- **Running the evaluation harness or the live smoke test for real.** Ollama can't be installed in this sandbox (`ollama.com` and direct GitHub release downloads are both blocked by the sandbox's own egress proxy). The harness and script are both ready and tested against fakes/mocks; the first real measurement against an actual model — local or hosted — hasn't happened yet.

## 9. Blocked on you — genuine decisions or access only you have

1. **GitHub Actions is disabled for this repo.** Every one of 7 pushes has failed CI in ~3-4 seconds with no log output — the unmistakable signature of Actions never actually running, not tests failing. Check Settings → Actions → General → "Actions permissions." Until this is flipped on, every "tests pass" claim rests on local verification only, never on independent confirmation from GitHub's own infrastructure.
2. **The "Atlas" naming decision.** Real collision risk documented in `docs/naming-considerations.md` (most concretely: an MCP server already live with near-identical positioning under the same name). Options laid out there; keeping, differentiating, or renaming is your call.
3. **Actually publishing to PyPI.** The package is publish-ready (builds clean, passes `twine check`, wheel verified to work) but publishing needs your PyPI account and credentials.
4. **Confirming repo visibility and the actual public announcement.** The repo is confirmed public (`linesman39/Atlas`), but "ready to build" and "announced" are different steps — that final call is yours.
5. **The visualization layer.** A genuinely separate stack (TypeScript, React, deck.gl, D3, a FastAPI serving layer, Docker Compose) — not started, and worth a deliberate go/no-go/when decision given its size relative to everything else here.
6. **Community setup** (Discussions, a Discord, etc.) if you want it — optional, not blocking.

## 10. Recommended order, if picking this up next

1. Flip on GitHub Actions and confirm the next push goes green — this is the cheapest, highest-value thing left, since it converts every "verified locally" claim in this document into something independently checkable.
2. Decide on the naming question before any public announcement — cheapest to change now, expensive once people depend on the name.
3. Install Ollama somewhere with real compute and run `python -m atlas.eval.run` and `python scripts/live_smoke_test.py` for the first real, non-mocked measurement of how well this actually works.
4. Push the `v0.1.0` tag and, if desired, cut a GitHub Release from it.
5. Decide whether/when to start the visualization layer — it's real, scoped (`docs/architecture.md`'s visualization table), and unstarted.
6. Publish to PyPI once 1–3 feel solid enough to stand behind publicly.

## 11. How to verify anything in this document yourself

```bash
git clone https://github.com/linesman39/Atlas && cd Atlas
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp,github]"
pytest tests/ -v                                                   # 93 tests, offline, ~2s
pytest tests/ --cov=atlas --cov-report=term-missing                # 88% coverage (pytest-cov is in [dev])
pip install build twine && python3 -m build && twine check dist/*  # package builds, metadata valid
```

Nothing in this document should be taken on faith — every claim above traces to a command you can run or a file you can read.
