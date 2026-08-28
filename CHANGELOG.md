# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Atlas hasn't tagged a `0.1.0` release yet — this tracks meaningful changes since the project's docs and code were first written, ahead of that first tag.

## [Unreleased]

### Added
- Core data model (`Fact`, `FieldNote`, `AnnexationRequest`, `BorderDispute`) and the Chart/Atlas markdown+YAML storage format, modeled on Claude Code's own verified auto-memory pattern.
- The Cartographer: a deterministic-first conflict check (`cartographer/deterministic.py`) escalating to an LLM only for genuinely ambiguous cases (`cartographer/llm_escalation.py`), unified in `cartographer/evaluate.py`.
- A pluggable `LLMBackend` interface (`src/atlas/llm/`) defaulting to a free local model via Ollama (`OllamaBackend`); `ClaudeBackend` as an explicit, opt-in hosted alternative.
- The Field Agent, Cartographer escalation, and Briefing Agent — all real, working implementations against the pluggable backend.
- `local_annex.py`: adapter-free annexation — a file write on Cartographer approval, no GitHub required.
- `GitHubAdapter`: annexation-as-pull-request, trade routes (`propose_trade_route`) for cross-org sharing of facts marked `shareable`, and CODEOWNERS-based reviewer routing wired into the live PR-open call.
- `weathering.py`: re-verification of already-annexed facts' evidence, with a CLI entrypoint and a template scheduled GitHub Actions workflow.
- `ask.py`: Ask-the-Atlas, answers cite the fact ids they rely on.
- `codeowners.py`: CODEOWNERS parsing and fact-to-owner routing.
- `mcp_server.py`: five MCP tools (`record_field_note`, `propose_annexation`, `query_chart`, `get_briefing`, `ask_the_atlas`).
- The evaluation harness (`src/atlas/eval/`): hand-labeled fixtures, per-tier recall, border-dispute catch rate, false-annexation rate, a Markdown+JSON report.
- Full documentation set: project definition, competitive landscape (six systems researched from official sources), lexicon, vision, requirements, architecture, open-source governance, privacy, naming considerations, testing.
- CODE_OF_CONDUCT.md, SECURITY.md, issue/PR templates, this changelog.

### Fixed
- **Security**: a fact's `subject` was used to build filesystem/URL paths in `GitHubAdapter` and `codeowners.py` without the same sanitization `storage.py` already applied, meaning a crafted subject like `../../etc/passwd` was not blocked from influencing the constructed path the way it already was for local Chart writes. Unified into one shared sanitizer (`storage.sanitize_path_component`) used everywhere a subject becomes part of a path. See `SECURITY.md`.

### Changed
- PyPI package renamed from `atlas-map` (already taken by an unrelated project) to `atlas-cartographer`.

## Versioning

Atlas follows [Semantic Versioning](https://semver.org/) once tagged: `MAJOR.MINOR.PATCH`. Pre-1.0, minor version bumps may include breaking changes to the fact schema or module layout — the project is still finding its shape. See `docs/open-source.md` for how schema changes themselves get proposed and reviewed (through Atlas's own annexation mechanism).
