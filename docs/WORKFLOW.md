# Workflow

The loop used to build and run this suite. It works for any Claude Code plugin or
skill: swap the submodule. Why each step exists is in [METHODOLOGY.md](METHODOLOGY.md).

```text
 pick a claim ─► write case + scaffold ─► write reference ─► check-references
       ▲                                                          │
       │                                                          ▼
 write up ◄─ audit judges + read traces ◄─ full run ◄─ freeze ◄─ smoke (1 run/arm)
```

## 0. One-time setup

```bash
git clone --recursive https://github.com/bartek-890/superpowers-evals
cd superpowers-evals
claude setup-token                     # or use an API key
echo "CLAUDE_CODE_OAUTH_TOKEN=..." > .env   # gitignored; never baked into the image
docker build -t superpowers-evals-runner .
```

Docker Desktop must be running. Everything runs in the container. On a macOS host,
`claude plugin eval` refuses any run that grants Bash (see METHODOLOGY:
Environment).

To pin a different plugin version:

```bash
git -C superpowers fetch && git -C superpowers checkout <sha>
```

## 1. Pick a claim

Read the skill's `SKILL.md` and write down, in one sentence, the behavior it
promises: "debugging finds the root cause instead of patching the symptom". If you
can't state a pass/fail check for it, it isn't a case yet.

For every positive case, write its **negative counterpart**: the same setup where
that behavior would be wrong. A suite of only "should" cases rewards a plugin that
does the thing everywhere.

## 2. Write the case

```text
evals/<case>/
├── case.yaml       prompt, limits, graders
├── scaffold.sh     builds the workspace (runs only with --scaffold)
└── reference/      known-good answer + EXPECT (initial=pass|fail)
```

Rules that saved time here:

- **Phrase the prompt like a user**, never naming the skill. The eval also measures
  whether the skill triggers.
- **Put everything the task needs in the scaffold or the prompt.** `context.add_dirs`
  fixtures exist, but the agent isn't told where they are mounted.
- **Set `plugins: ["../../superpowers"]`** and always run from the repo root
  (`claude plugin eval .`). A single case file as the target fails containment.
- **Grade files with `{ source: file, path: ... }`**, and test results with a regex
  over `trace` (`# fail 0`), not with `tool_used: Bash`.
- **Anchor `input_match` on `file_path`** when matching an Edit. A test file that
  imports `src/x.js` would otherwise match `src/x\.js`.
- **Don't use `tool_order` on Edit** to check implementation order. Agents often
  write code with a Bash heredoc.
- **Every `llm` rubric** gets concrete PASS and FAIL values plus "missing or unclear
  is FAIL".
- **Graders take only** `name`, `type`, `weight`, `arm`, and their type's options.
  Put notes in YAML comments.
- **Scaffolds set a repo-local git identity** (`git config user.email ...`), or the
  agent can't commit in the sandbox.

## 3. Prove the case is solvable

```bash
docker run --rm -v "$PWD":/work --entrypoint python3 superpowers-evals-runner \
  scripts/check-references.py
```

Every case must print `ok`: the starting state matches `EXPECT`, the reference
passes the tests, and every file regex grader accepts the reference.

## 4. Smoke (1 run per arm)

```bash
scripts/run.sh --runs 1 -j 4 --max-cost-usd 4 --tag <tag>
```

`--case` takes a single glob (no braces). Use tags to select several cases.

Then **read the traces**, not just the scores:

```bash
d=results/$(ls results | tail -1)
cat $d/summary.md          # the Errors column must be 0
less $d/traces/<case>/with-1.jsonl
```

For each failed grader, ask whether the failure is fair. In this suite, smoke
passes caught:

- a broken sandbox that tool-call graders didn't notice
- an order grader fooled by an import line
- a judge that failed a correct answer
- an agent that saw red but piped the test output through `head`

Fix the grader, log the change in the README change log, and smoke again.

## 5. Freeze

Commit with a message that says the graders are frozen, and add the commit to the
README change log. From here on, results are reported as scored.

## 6. Full run

```bash
caffeinate -i scripts/run.sh --runs 8 -j 6 --max-cost-usd 25
```

- `caffeinate -i` stops macOS from idle-sleeping. A sleeping host stalls runs past
  their timeout.
- `-j` shares one rate limit. It shortens wall time, not total cost.
- Exit code 2 means the cost ceiling was hit: the results are partial, so don't
  publish them.

`scripts/run.sh` does the rest: it runs `claude plugin eval` in the container with
`--scaffold --keep-temp`, then `collect.py` copies every trace into
`results/<timestamp>/traces/` and writes `summary.md`, `summary.json`, and
`judge-audit.md`. It then deletes the sandbox directories.

## 7. Audit

- **Errors column is 0.** Otherwise a score may reflect the environment, not the
  plugin.
- **Judge audit:** read `judge-audit.md` and mark every verdict you disagree with.
  More than ~10% disagreement on a grader means its rubric is broken. Report that,
  and fix it in the next version, not this one.
- **Saturation:** a positive case where both arms score 1.00 can't show a
  difference. Note it; it needs a harder variant.
- **Before any push**, scan the results for secrets and personal data:

  ```bash
  grep -rlE "sk-ant-|OAUTH_TOKEN|API_KEY" results
  ```

## 8. Write up

Report per case: score with/without, Δ with its CI, outcome vs process separately,
pass^3, the cost ratio, and how often the skill fired. Say which cases were
saturated, which rubric changes happened before the freeze, and every limitation
in METHODOLOGY's Threats to validity. Link the exact results directory and commit.
