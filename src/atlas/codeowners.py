"""CODEOWNERS-based Surveyor-General routing (docs/architecture.md,
"Committed beyond today's build"). Reuses GitHub's existing
reviewer-assignment primitive instead of building a bespoke routing
system: a fact routes to whoever already owns the path it would be
written under.

Scope limit, stated plainly: this implements the common CODEOWNERS
patterns (exact paths, directory prefixes, simple globs) via fnmatch, not
the full gitignore-pattern grammar GitHub's own parser supports. Good
enough for routing a synthetic fact path; not a general-purpose
CODEOWNERS validator.
"""

from __future__ import annotations

import fnmatch

CodeownersRule = tuple[str, list[str]]


def parse_codeowners(text: str) -> list[CodeownersRule]:
    """Returns [(pattern, [owners]), ...] in file order."""
    rules: list[CodeownersRule] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        pattern, owners = parts[0], parts[1:]
        rules.append((pattern, owners))
    return rules


def owners_for_path(rules: list[CodeownersRule], path: str) -> list[str]:
    """CODEOWNERS semantics: the LAST matching rule wins, not the most
    specific one — this matches GitHub's own documented behavior."""
    matched: list[str] = []
    for pattern, owners in rules:
        normalized = pattern.lstrip("/")
        is_match = (
            fnmatch.fnmatch(path, normalized)
            or fnmatch.fnmatch(path, normalized.rstrip("/") + "/*")
            or path.startswith(normalized.rstrip("/") + "/")
        )
        if is_match:
            matched = owners
    return matched


def owners_for_fact(rules: list[CodeownersRule], fact_subject: str, facts_dir: str = "facts") -> list[str]:
    """A fact has no inherent file path — map it to the same synthetic
    path GitHubAdapter.propose_annexation writes it under, so routing
    matches what the PR will actually touch."""
    synthetic_path = f"{facts_dir}/{fact_subject.lower().replace(' ', '-')}.md"
    return owners_for_path(rules, synthetic_path)
