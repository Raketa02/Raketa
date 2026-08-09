# Sandbox image for the AFK agent loop, driven by sandbuket.
#
# The image contains the tools the agent needs to verify backend work inside the
# sandbox: git, gh, Python 3.11, Poetry, make, Docker-friendly build tools, and
# Claude Code.
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

ARG AGENT_UID=1000
ARG AGENT_GID=1000

RUN groupmod -o -g $AGENT_GID node \
    && usermod -o -u $AGENT_UID -g $AGENT_GID -d /home/agent -m -l agent node

USER ${AGENT_UID}:${AGENT_GID}

RUN pipx install poetry==1.8.3 && pipx ensurepath
RUN curl -fsSL https://claude.ai/install.sh | bash

ENV PATH="/home/agent/.local/bin:$PATH"
WORKDIR /home/agent

ENTRYPOINT ["sleep", "infinity"]
