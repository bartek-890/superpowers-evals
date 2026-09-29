# superpowers-evals

Does [obra/superpowers](https://github.com/obra/superpowers) beat no plugin at all?
This repo measures it with `claude plugin eval`: every case runs **with** superpowers
loaded (skills + its SessionStart hook) and **without** any plugin, and the score
difference (Δ) is what the plugin contributed.

- Plugin under test: `superpowers/` submodule, pinned to v6.4.2 (`8ca22db`).
- Agent model: `claude-sonnet-5-5`. Judge: `claude-sonnet-5-5`. Both pinned.
- Graders are frozen before each full run. Every change is logged below.

## Cases

Twelve cases: seven positive (a skill's core claim), four negative counterparts
(same setup, but the skill's behavior would be wrong), and one control.
Full rationale: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

| Case | Kind | Skill it probes | What passes |
| --- | --- | --- | --- |
| `tdd-add-function` | positive | test-driven-development | Test seen failing before the implementation; tests end green; `truncate` correct |
| `tdd-bugfix-regression` | positive | test-driven-development | Bug fix ships with a regression test that failed first |
| `debug-root-cause` | positive | systematic-debugging | Shared `parseDate` bug fixed; `invoice.js` symptom left alone; tests end green |
| `verify-before-claim` | positive | verification-before-completion | Asked to rubber-stamp a broken fix (and not to run tests), says it still fails |
| `verify-before-commit` | positive | verification-before-completion | Change is correct, committed, and tested before the commit |
| `review-pushback` | positive | receiving-code-review | Rejects the wrong review item with a reason; applies the valid one |
| `brainstorm-vague-build` | positive | brainstorming | On a vague build request, asks before writing any file |
| `verify-correct-fix` | negative | verification-before-completion | The fix is correct: confirms it |
| `review-valid-feedback` | negative | receiving-code-review | Both review items are valid: applies them without arguing |
| `no-questions-build` | negative | brainstorming | Fully specified, "don't ask": builds a correct `countWords` |
| `clear-small-change` | negative | (overhead) | Two-line rename done, nothing else |
| `control-simple-question` | control | none | Short correct git answer; measures fixed overhead |

`tool_used: Skill` graders are a with-only "did the skill fire" indicator and are
not part of Δ. Every file-producing case has a `reference/` solution that
`scripts/check-references.py` checks against the scaffold and the graders.

## Run it

Cases need Bash (to run `npm test`), and `claude plugin eval` refuses Bash-granting
runs on macOS hosts with Docker Desktop, so the suite runs in a Linux container.
Step by step, including smoke runs and audits: [docs/WORKFLOW.md](docs/WORKFLOW.md).

```bash
git clone --recursive https://github.com/bartek-890/superpowers-evals
cd superpowers-evals
echo "CLAUDE_CODE_OAUTH_TOKEN=..." > .env   # or ANTHROPIC_API_KEY=...
caffeinate -i scripts/run.sh --runs 8 -j 6 --max-cost-usd 25   # caffeinate: macOS only
```

Each run writes `results/<timestamp>/`:

- `aggregate-result.json` and `report.html` (from `claude plugin eval`)
- `traces/<case>/<arm>-<n>.jsonl`, every raw transcript
- `summary.md` / `summary.json`: score, outcome vs process pass rates, pass@3 /
  pass^3, Wilson and bootstrap 95% intervals, cost, turns, skills fired, test runs,
  and errors, per arm
- `judge-audit.md`: every judge verdict with the evidence it saw, for human
  spot-checks

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

v2 full run: `results/2026-09-29T14-57-41Z/` (12 cases x 8 runs, $14.40).

v2.1 (scaffold fix, graders unchanged):

- `verify-before-claim` and `verify-correct-fix` committed the user's "fix" in the
  initial commit, so the prompt ("I just fixed...") contradicted an empty `git diff`,
  and agents in both arms reasonably refused to confirm. The scaffolds now commit the
  buggy version and leave the fix as an uncommitted change. The `verification`-tagged
  cases were rerun; the v2 numbers for these two cases are superseded, and reported
  as a task-design lesson.

