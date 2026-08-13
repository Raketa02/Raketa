# Sandbox image for the AFK agent loop, driven by sandbuket.
#
# The image contains the tools the agent needs to verify work in ANY of the three
# apps inside the sandbox: git, gh, jq, Python 3.11, Poetry, Node 22, pnpm, make,
# build tools, and Claude Code.
#
# Two versions here are load-bearing and must not drift:
#   - Poetry matches the version that generated backend/poetry.lock (lock-version
#     2.1). An older Poetry reads that lock differently and can resolve groups
#     wrongly.
#   - jq is required by .claude/hooks/*; without it both hooks fail safe and
#     block every tool call.
#
# Build:
#   docker build -t sandbuket:rakieta \
#     --build-arg AGENT_UID=$(id -u) --build-arg AGENT_GID=$(id -g) \
#     -f .sandbuket/Dockerfile .sandbuket
# The root Makefile `afk-build` target does this for you.

FROM node:22-bookworm

RUN apt-get update && apt-get install -y \
      git curl jq make build-essential \
      python3 python3-pip python3-venv pipx \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# pnpm, for frontend_player and frontend_club. Must run as root: corepack writes
# its shims into the Node prefix, which the agent user cannot write to.
RUN corepack enable pnpm

# Python 3.11.x — Debian bookworm ships 3.11.2, which is BELOW the backend's
# `python = "^3.11.6"` floor, so Poetry refuses it outright and every backend
# verification fails before it starts. The backend's own images are
# `python:3.11-slim-bookworm`, so a current 3.11 is also what CI and production
# actually run. Installed to a shared prefix and symlinked into /usr/local/bin,
# which precedes /usr/bin on PATH, so Poetry finds it ahead of Debian's.
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh \
    && uv python install 3.11 \
    && ln -sf "$(uv python find 3.11)" /usr/local/bin/python3.11 \
    && chmod -R a+rX /opt/python

ARG AGENT_UID=1000
ARG AGENT_GID=1000

RUN groupmod -o -g $AGENT_GID node \
    && usermod -o -u $AGENT_UID -g $AGENT_GID -d /home/agent -m -l agent node

USER ${AGENT_UID}:${AGENT_GID}

# Poetry must run ON the 3.11 installed above, not on Debian's 3.11.2. Poetry
# creates project venvs from its own interpreter by default, so a Poetry running
# on 3.11.2 produces a venv the project rejects — and `poetry env use python3.11`
# does NOT rescue it, because Poetry matches on the minor version and reuses its
# own. Getting this wrong fails every backend verification before it starts.
RUN pipx install --python /usr/local/bin/python3.11 poetry==2.1.3 && pipx ensurepath
RUN curl -fsSL https://claude.ai/install.sh | bash

ENV PATH="/home/agent/.local/bin:$PATH"
WORKDIR /home/agent

ENTRYPOINT ["sleep", "infinity"]
