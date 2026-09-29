# superpowers-evals

Does [obra/superpowers](https://github.com/obra/superpowers) beat no plugin at all?
This repo measures it with `claude plugin eval`: every case runs **with** superpowers
loaded (skills + its SessionStart hook) and **without** any plugin, and the score
difference (Δ) is what the plugin contributed.

- Plugin under test: `superpowers/` submodule, pinned to v6.4.2 (`8ca22db`).
- Agent model: `claude-sonnet-5-5`. Judge: `claude-haiku-4-5`. Both pinned.
- Graders are frozen before the full run. Any change after it is logged below.

## Cases

Each case targets one skill's core claim. Deterministic graders (regex, tool calls)
carry most of the score; `llm` graders are kept to short outputs.

| Case | Skill it probes | What passes |
| --- | --- | --- |
| `tdd-add-function` | test-driven-development | A failing test run appears before the passing one ("saw red"); tests end green; `truncate` correct |
| `debug-root-cause` | systematic-debugging | Shared `parseDate` bug fixed; `invoice.js` symptom left alone; tests end green |
| `verify-before-claim` | verification-before-completion | Asked to rubber-stamp a fix (and not to run tests), says it still fails |
| `review-pushback` | receiving-code-review | Rejects the wrong review item with a reason; applies the valid one |
| `brainstorm-vague-build` | brainstorming | On a vague build request, asks before writing any file (behavior shift, not quality) |
| `control-simple-question` | none | Short correct git answer; measures the plugin's overhead |

`tool_used: Skill` graders are a with-only "did the skill fire" indicator and are
not part of Δ.

## Run it

Cases need Bash (to run `npm test`), and `claude plugin eval` refuses Bash-granting
runs on macOS hosts with Docker Desktop, so the suite runs in a Linux container:

```bash
git clone --recursive https://github.com/bartek-890/superpowers-evals
cd superpowers-evals
echo "CLAUDE_CODE_OAUTH_TOKEN=..." > .env   # or ANTHROPIC_API_KEY=...
scripts/run.sh --runs 5 -j 4 --max-cost-usd 25
```

Each run writes `results/<timestamp>/` with `aggregate-result.json`, `report.html`,
every raw trace under `traces/<case>/<arm>-<n>.jsonl`, and `summary.md` /
`summary.json` (per-arm score mean and sd, cost, turns, which skills fired, how
often tests were run, computed from the traces by `scripts/collect.py`).

Test outcomes are graded from node's own summary in the trace (`# fail 0`,
`# fail N`), not from "a Bash call happened": an early smoke pass showed Bash
calls can fail inside a misconfigured sandbox while a tool-call grader still passes.
`scripts/collect.py` also counts sandbox errors per run so a broken environment
is visible in `summary.md`.

## Change log

Smoke passes (1 run per arm, not published) before the freeze:

- Grader `description` keys removed (not in the schema); kept as YAML comments.
- Container needs `--security-opt systempaths=unconfined` for bubblewrap to mount
  `/proc`; without it every Bash call failed and `tool_used: Bash` graders still passed.
- `tests-run` (tool call) replaced by `tests-green` (`# fail 0` in the trace).
- TDD order grader: `tool_order` on Edit missed implementations written by a Bash
  heredoc and matched test edits that import `src/text.js`; replaced by `saw-red`.
- Judge moved from Haiku 4.5 to Sonnet 5.5 after Haiku failed a correct control
  answer 3/3; control rubric simplified.

v1 graders frozen at `1e5b4c3`; the v1 full run (6 cases x 5 runs) is kept in
`results/2026-09-29T14-42-45Z/` for comparison.

v2 (after reviewing current eval practice, see `docs/METHODOLOGY.md`):

- Six new cases: `tdd-bugfix-regression`, `verify-before-commit` (headroom), and
  the negative counterparts `verify-correct-fix`, `review-valid-feedback`,
  `clear-small-change`, `no-questions-build`.
- Every file-producing case has a `reference/` solution checked by
  `scripts/check-references.py`.
- `llm` rubrics got an escape clause (missing or unclear evidence is FAIL).
- Scaffolds set a repo-local git identity so agents can commit.
- `saw-red` widened from `# fail [1-9]` to any node failure marker, after a smoke
  run showed an agent that did see a failing test but piped the output through `head`.
- `collect.py` reports outcome vs process graders separately, pass@3 / pass^3,
  Wilson and bootstrap 95% intervals, and writes `judge-audit.md`.

v2 graders frozen at the commit that adds this line. Any later change is listed below.
