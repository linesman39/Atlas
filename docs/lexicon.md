# The Atlas Lexicon

Atlas doesn't borrow version control's vocabulary (commit, branch, blame, merge, revert). It has its own, drawn from cartography and expedition — because the thing being versioned isn't code, it's decisions, and code is what a decision leaves behind. Each entry below names the mechanism, then notes the conventional concept it reimagines, for grounding only — the term on the left is what ships in docs, code, and UI.

| Term | What it is | Reimagines |
|---|---|---|
| **Field Notes** | The raw, unverified record of a single session — a surveyor's personal notebook. Ephemeral, not yet trusted. | Session-level context / working memory |
| **The Chart** | One repository's verified, durable knowledge. What Field Notes become once they survive scrutiny. | Codebase-level persistent memory |
| **The Atlas** | The bound collection of every Chart across a workspace. The top tier — and the product's namesake, because everything Atlas does exists to get a fact *into* it. | Cross-repo / workspace-level memory |
| **Survey** | The atomic unit of record: an act of exploring, verifying, and charting a piece of territory, with evidence attached. | A commit |
| **Ground-truthing** | The rule that nothing gets charted on a claim alone — a fact is only promotable if it's checked against something real (a passing test, a landed diff, a command's actual output). | Fact verification / provenance requirement |
| **Expedition** | A divergent line of exploration — trying one approach, then another. Abandoned expeditions are kept on record, not erased, because knowing what failed is worth as much as knowing what worked. | A branch |
| **Border dispute** | Two expeditions return with contradictory claims about the same territory. | A merge conflict |
| **The Cartographer** | The agent that adjudicates border disputes before anything is annexed — ground-truths whichever claim is more credible, or flags both as unresolved. | Verification / conflict-resolution agent |
| **Annexation** | A fact moving up a tier — Field Notes → Chart, or Chart → Atlas. Named as a bigger act than "promotion": territory changing hands permanently. | Memory promotion / write to persistent store |
| **The Surveyor-General** | The accountable human who signs off on an annexation that matters. Borrowed from the historical title for the head of a national land-survey authority. | Human-in-the-loop approver |
| **The Legend** | The provenance trail behind any charted fact — click it, see the Surveys and evidence that established it. A map's legend explains its symbols; Atlas's Legend explains why you're allowed to believe this. | Blame / audit trail |
| **Weathering** | A charted fact that hasn't been re-surveyed in a long time visibly loses trust — fades — until re-verified. | Staleness / freshness decay |
| **Retraction** | Rolling back a fact rolls back the *belief*, with a note on record for why — not just the diff it produced. | Revert |
| **Fault line** | An unresolved border dispute, rendered as a visible crack, severity by depth, until closed. | Flagged/unresolved conflict |
| **Trade route** | A channel of verified knowledge flowing between two Charts, or between two Atlases entirely (cross-org). | Remote / fork |
| **Expedition Briefing** | The handoff artifact — distilled from Field Notes, the Chart, and the Atlas — given to whoever (human or agent) sets out next. | Bootstrap brief / context handoff |

## Naming convention going forward

Code modules, agent names, and file paths should follow this lexicon directly (e.g. a `cartographer/` module, not a `verifier/` module) so the product's language is consistent from vision doc to source code to UI copy.
