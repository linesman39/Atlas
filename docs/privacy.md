# Atlas — Data Handling & Privacy

Atlas's entire purpose is capturing what happens in a coding-agent session and making it durable. That makes data handling a first-class design question, not an afterthought — this document says plainly what Atlas stores, where, and what a user should keep out of it.

## What gets stored, and where

- **Field Notes**: extracted by the Field Agent from a session transcript segment you provide. Stored wherever your code calls `write_fact`/`annex_locally` writes to — by default, a local directory you choose (`chart_dir`), as plain markdown files. Atlas does not choose a location for you and does not write anywhere you didn't point it at.
- **Charts and the Atlas**: the same markdown+YAML files, plain text, readable without any Atlas tooling. If that directory is inside a git repository you push, its contents go wherever that repository goes — the same as any other file you commit.
- **Nothing is sent anywhere by the Engine by default.** The default `OllamaBackend` talks only to `localhost:11434` — a model running on your own machine. No Field Note, Chart content, or query ever leaves your machine unless you explicitly configure `ATLAS_LLM_BACKEND=claude` (sends prompts to Anthropic's API) or use `GitHubAdapter` (sends fact content to GitHub as part of opening a PR, exactly as visibly as pushing a normal commit).

## What Atlas does not do

- It does not phone home. There is no telemetry, no usage reporting, no analytics call anywhere in the Engine or the Application layer as built.
- It does not read anything you don't hand it. The Field Agent only ever processes the `transcript_segment` string it's explicitly called with — it does not scan a filesystem, a shell history, or anything else on its own initiative.
- It does not decide what's sensitive for you. Atlas has no content filter that tries to detect secrets or PII in a Field Note before storing it — that's a human judgment call, not something to silently automate.

## What you should keep out of a Field Note

Because a Chart is plain text meant to be durable, diffable, and eventually shared (via annexation, or a trade route to another org), treat it the way you'd treat a commit message or code comment, not a private scratchpad:

- **No credentials, API keys, or tokens.** If a session transcript segment contains one (e.g., pasted into a debugging conversation), don't hand that raw segment to the Field Agent — the extraction has no way to know a string is a secret rather than an ordinary fact. This mirrors the same discipline every `.gitignore`/secrets-scanning practice already assumes for code.
- **No personal data about real people** beyond what's necessary and already appropriate to have in your codebase's own history (e.g., a commit author's name is normal; a customer's private data pasted into a debugging session is not).
- **Be deliberate about `shareable=True`.** A fact marked shareable is explicitly eligible for export to another organization's Atlas via a trade route (`GitHubAdapter.propose_trade_route`). Nothing is exported automatically — a Surveyor-General still has to open and approve that PR — but the flag itself should be set thoughtfully, not by default.

## Evidence and weathering

Ground-truthing evidence (`EvidenceRef`) typically points at things already in your repository — a test file path, a commit SHA, a command. Weathering (`src/atlas/weathering.py`) re-checks these using standard git and filesystem operations against a repo checkout you provide — it does not fetch anything remotely and does not execute the referenced commands themselves (see the module's own stated scope limit).

## If you're building the Application layer on top

If you deploy the MCP server or `GitHubAdapter` for a team, you inherit the normal responsibilities of any tool that touches a shared GitHub repository or exposes an MCP surface to multiple users — access control, who can approve an annexation (the Surveyor-General role), and standard git-hosting security practice apply exactly as they would for any other repository. Atlas doesn't add new risk here beyond what committing files to that repository already means.
