# Atlas — Engine + MCP server image.
#
# This packages what's actually built and working: the free local Engine
# and the MCP server (5 tools). It does not include the visualization
# layer (not yet built — see docs/requirements.md) or a bundled Ollama
# instance (run Ollama separately; ATLAS_LLM_BACKEND defaults to "local"
# and expects it reachable at OLLAMA_HOST, default http://localhost:11434
# — point this container at a host or sibling-container Ollama via
# `docker run -e ATLAS_LLM_MODEL=... --network host` or Compose).
#
# Verification status, stated plainly: the Docker daemon is not available
# in the environment this was written in (a sandboxed container that
# cannot itself start dockerd), so unlike the rest of this codebase this
# file has NOT been through `docker build` and run. It follows standard,
# well-established patterns, but treat it as unverified until someone
# with a working Docker daemon confirms `docker build .` succeeds.

FROM python:3.11-slim AS base

WORKDIR /app

# System deps: git is required by weathering.py (git cat-file) and by
# any workflow that annexes into a real git-tracked Chart.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# mcp: the server this image's default command runs.
# github: optional at runtime (GITHUB_TOKEN unset = GitHubAdapter simply
# isn't constructed by anything that needs it), included so the same
# image can serve either the local-only or GitHub-integrated path
# without a rebuild.
RUN pip install --no-cache-dir -e ".[mcp,github]"

ENV ATLAS_LLM_BACKEND=local
ENV ATLAS_LLM_MODEL=llama3.1

EXPOSE 8765

# stdio transport by default -- an MCP client (Claude Code, etc.) attaches
# to this process's stdin/stdout. For a network transport, adjust
# src/atlas/mcp_server.py's server.run() call and this CMD together.
CMD ["python3", "-m", "atlas.mcp_server"]
