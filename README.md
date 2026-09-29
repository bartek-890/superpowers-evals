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
| `tdd-add-function` | test-driven-development | Test file edited before the implementation; tests run; `truncate` correct |
| `debug-root-cause` | systematic-debugging | Shared `parseDate` bug fixed; `invoice.js` symptom left alone; tests run |
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

## Change log

- (none yet)
