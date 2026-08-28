"""The substrate adapter boundary (docs/architecture.md).

This is the single most load-bearing interface in the project: Chart
Keeper and Atlas Keeper are only ever allowed to talk to a
SubstrateAdapter, never to a hosting system directly. GitHubAdapter is
the only implementation that ships today. Replacing or adding a hosting
backend later — a native Atlas store, GitLab, whatever comes next — means
writing a second adapter, not touching the Cartographer, Chart Keeper, or
Atlas Keeper.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from atlas.models import AnnexationRequest, Fact


class AnnexationHandle(BaseModel):
    """A reference to an annexation opened on some substrate — a GitHub PR
    today, something else tomorrow. Nothing outside the adapter that
    created it should need to know which."""

    url: str
    is_open: bool = True


class SubstrateAdapter(ABC):
    """Where Charts and the Atlas actually live, and how an annexation
    actually gets reviewed. See docs/requirements.md #3."""

    @abstractmethod
    def propose_annexation(self, request: AnnexationRequest) -> AnnexationHandle:
        """Open a reviewable annexation (a PR, or equivalent) containing
        the candidate fact, its evidence, and the Cartographer's verdict.
        Must never auto-merge — a Surveyor-General approves it."""

    @abstractmethod
    def is_approved(self, handle: AnnexationHandle) -> bool:
        """Has a Surveyor-General approved this annexation?"""

    @abstractmethod
    def get_facts(self, scope: str) -> list[Fact]:
        """Read the currently-annexed facts for a scope (a repo's Chart,
        or the whole Atlas)."""
