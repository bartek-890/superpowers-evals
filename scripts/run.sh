#!/usr/bin/env bash
# Usage: scripts/run.sh [extra claude plugin eval args...]
#
# Runs the suite inside a Linux container. On macOS hosts with Docker Desktop,
# claude plugin eval refuses Bash-granting runs (symlinks in ~/.docker), and
# these cases need Bash to run npm test. Credentials come from .env
# (CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY) and never enter the image.
set -euo pipefail
cd "$(dirname "$0")/.."
out="results/$(date -u +%Y-%m-%dT%H-%M-%SZ)"
mkdir -p "$out" .tmp
docker build -q -t superpowers-evals-runner . >/dev/null
run() { docker run --rm --env-file .env -e TMPDIR=/work/.tmp \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined --security-opt systempaths=unconfined \
  -v "$PWD":/work "$@"; }
set +e
run superpowers-evals-runner . \
  --trust-plugin --no-publish --keep-temp --scaffold --threshold 0 \
  --model claude-sonnet-5-5 --judge-model claude-sonnet-5-5 \
  --allow-tools Bash Write Edit \
  --output-dir "$out" "$@"
status=$?
set -e
run --entrypoint python3 superpowers-evals-runner scripts/collect.py "$out"
# Kept run dirs are sealed read-only by the runner; open them so they can be removed.
run --entrypoint sh superpowers-evals-runner -c 'chmod -R u+rwx .tmp 2>/dev/null; rm -rf .tmp'
echo "results: $out (eval exit $status)"
