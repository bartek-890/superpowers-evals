# Linux runner for claude plugin eval: the macOS host refuses Bash-granting
# runs (Docker Desktop symlinks in ~/.docker), and Linux uses bubblewrap instead.
FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      git bubblewrap socat python3 python3-yaml ca-certificates ripgrep \
    && rm -rf /var/lib/apt/lists/*
ARG CLAUDE_CODE_VERSION=2.1.284
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
USER node
WORKDIR /work
ENTRYPOINT ["claude", "plugin", "eval"]
