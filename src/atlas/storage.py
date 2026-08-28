"""Chart/Atlas storage: one Fact per file, Markdown with YAML frontmatter,
plus an index file per tier. Modeled directly on Claude Code's own
auto-memory pattern (MEMORY.md index + topic files) — see
docs/competitive-landscape.md for the verified source and
docs/architecture.md for why this beats a vector/graph store here:
diffable, git-native, human-legible without any Atlas tooling running.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from atlas.models import Fact

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def sanitize_path_component(text: str) -> str:
    """Strip everything but alphanumerics before text becomes part of a
    filesystem or URL path. The one sanitizer every module that turns a
    Fact's subject into a path (this module, the GitHub adapter,
    CODEOWNERS routing) shares — so a subject like '../../etc/passwd'
    can never escape the directory it's written into, and the same
    subject always sanitizes to the same prefix everywhere it's used.
    See SECURITY.md.
    """
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def slug_for_fact(fact: Fact) -> str:
    return sanitize_path_component(f"{fact.subject}-{fact.id}")


def fact_to_markdown(fact: Fact) -> str:
    """Serialize a Fact to frontmatter + a human-readable body."""
    frontmatter = fact.model_dump(mode="json", exclude={"claim"})
    body_lines = [f"# {fact.subject}", "", fact.claim]
    if fact.evidence:
        body_lines += ["", "## Evidence"]
        for ev in fact.evidence:
            body_lines.append(f"- **{ev.kind.value}**: {ev.reference} — {ev.summary}".rstrip(" —"))
    body = "\n".join(body_lines) + "\n"
    return f"---\n{yaml.safe_dump(frontmatter, sort_keys=False)}---\n\n{body}"


def markdown_to_fact(text: str) -> Fact:
    """Parse a Fact back out of its stored file. Round-trips fact_to_markdown."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("Not a valid Atlas fact file: missing YAML frontmatter")
    frontmatter_raw, body = match.groups()
    data = yaml.safe_load(frontmatter_raw) or {}

    body_lines = body.strip("\n").split("\n")
    claim_lines: list[str] = []
    for line in body_lines[1:]:  # skip the "# subject" heading
        if line.startswith("## Evidence"):
            break
        claim_lines.append(line)
    data["claim"] = "\n".join(claim_lines).strip()
    return Fact.model_validate(data)


def write_fact(fact: Fact, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slug_for_fact(fact)}.md"
    path.write_text(fact_to_markdown(fact), encoding="utf-8")
    return path


def read_fact(path: Path) -> Fact:
    return markdown_to_fact(path.read_text(encoding="utf-8"))


def read_all_facts(directory: Path) -> list[Fact]:
    if not directory.exists():
        return []
    facts = []
    for path in sorted(directory.glob("*.md")):
        if path.name.upper() in {"CHART.md".upper(), "ATLAS.md".upper()}:
            continue
        facts.append(read_fact(path))
    return facts


def build_index(facts: list[Fact], title: str) -> str:
    """The CHART.md / ATLAS.md index: one line per fact, per the Claude
    Code MEMORY.md pattern this is modeled on."""
    lines = [f"# {title}", "", f"{len(facts)} fact(s) charted.", ""]
    for fact in sorted(facts, key=lambda f: f.subject):
        evidence_note = "ground-truthed" if fact.is_ground_truthed() else "NO EVIDENCE"
        lines.append(
            f"- **{fact.subject}** ({fact.scope}, {fact.status.value}, {evidence_note}): {fact.claim.splitlines()[0] if fact.claim else ''}"
        )
    return "\n".join(lines) + "\n"


def write_index(facts: list[Fact], directory: Path, title: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    filename = "ATLAS.md" if title.strip().lower() == "the atlas" else "CHART.md"
    path = directory / filename
    path.write_text(build_index(facts, title), encoding="utf-8")
    return path
