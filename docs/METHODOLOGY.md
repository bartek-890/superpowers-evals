# Methodology

How this suite measures what [obra/superpowers](https://github.com/obra/superpowers)
adds to Claude Code, and why it is built the way it is. The step-by-step procedure
is in [WORKFLOW.md](WORKFLOW.md).

## The question

Not "is superpowers good?" but a narrower, measurable one: **on tasks its skills
claim to handle, does loading the plugin change what the agent produces or how it
works, compared with the same model and prompt with no plugin at all?**

"No plugin" is a strong baseline. The agent (Claude Sonnet 5.5) already knows TDD,
debugging, and code review. A skill only earns a positive delta if it changes
behavior beyond what the model does by default.

## Ablation design

`claude plugin eval` runs every case in two arms:

| Arm | What loads |
| --- | --- |
| **with** | superpowers v6.4.2: its 14 skills and its `SessionStart` hook, which injects the full `using-superpowers` skill into every session |
| **without** | nothing: no plugin, no `CLAUDE.md`, no user settings, no memory |

Both arms get the same prompt, tools, model, turn limit, and scaffolded workspace.
Each run starts in a fresh temporary home and working directory, so runs share no
state (Anthropic: "Each trial should be 'isolated' by starting from a clean
environment").

**Δ = with-arm score − without-arm score.** A `tool_used: Skill` grader in each
case reports whether the skill fired, but it is excluded from both arms' scores:
it can never pass without the plugin, and counting it would inflate Δ.

## Case design

Twelve cases in three groups. Each targets one skill's advertised behavior.

**Positive (the skill's core claim):**

| Case | Skill | The trap or claim |
| --- | --- | --- |
| `tdd-add-function` | test-driven-development | Write and watch a test fail before implementing |
| `tdd-bugfix-regression` | test-driven-development | A bug fix should come with a regression test that failed first |
| `debug-root-cause` | systematic-debugging | The failing test is in `invoice.js`; the bug is in the shared `parseDate` |
| `verify-before-claim` | verification-before-completion | User asks to rubber-stamp a "fix" that still fails, and says not to run tests |
| `verify-before-commit` | verification-before-completion | Change, then commit: is the change verified before the commit? |
| `review-pushback` | receiving-code-review | One review item is wrong (null authors exist); comply or push back? |
| `brainstorm-vague-build` | brainstorming | "Build me a reading-list CLI": ask first, or start writing? |

**Negative counterparts** ("one-sided evals create one-sided optimization"): same
setup, but the skill's behavior would be wrong here.

| Case | Counterpart of | Correct behavior |
| --- | --- | --- |
| `verify-correct-fix` | verify-before-claim | The fix is correct: confirm it, don't invent problems |
| `review-valid-feedback` | review-pushback | Both review items are valid: apply them, don't argue |
| `no-questions-build` | brainstorm-vague-build | Fully specified, "don't ask me anything": build it |
| `clear-small-change` | brainstorming / overhead | A two-line rename: just do it |

**Control:** `control-simple-question`, a factual git question no skill targets.
It measures the plugin's fixed overhead in cost and turns.

Workspaces are tiny Node projects created by each case's `scaffold.sh`, with tests
run by `node --test`. Small fixtures keep every task unambiguous ("two domain
experts would independently reach the same pass/fail verdict") and cheap enough to
run many trials. The cost is realism: see Threats to validity.

## Graders

Deterministic graders come first. `llm` graders are kept to short outputs (one
file, or the final reply), because judge verdicts drift more on long text.

| Type | Used for | Cost |
| --- | --- | --- |
| `regex` on a produced file | Code shape: null guard kept, JSDoc added, symptom not patched | free |
| `regex` on the trace | Test outcomes from node's own output: `# fail 0` (green), any failure marker (red) | free |
| `file_exists`, `tool_used`, `tool_order` | Deliverable created, commit made, tests before commit | free |
| `llm` (judge: Sonnet 5.5, 3 votes, majority) | Behavioral correctness of a function; whether a reply confirms, refuses, or pushes back | paid |

**Outcome vs process.** Anthropic's guidance is to "grade what the agent produced,
not the path it took". Some superpowers skills are *about* the path (TDD's "watch
it fail", brainstorming's "ask first"), so the suite keeps both kinds of grader but
reports them separately:

- **Outcome graders:** the code, the commit, the reply.
- **Process graders:** `saw-red`, `tests-green`, `tests-before-commit`,
  `no-code-before-questions`, `asks-a-question`.

A skill that changes process without changing outcome is a legitimate finding, not
a win.

**Test outcomes come from the trace, not from tool calls.** An early smoke run had a
broken sandbox: every Bash call failed, yet a `tool_used: Bash` grader passed
because the call was *made*. Graders now match node's own summary (`# fail 0`), and
`collect.py` counts sandbox errors per run.

**Judge rubrics** state concrete PASS and FAIL conditions with worked values (e.g.
`truncate("hello world", 8) === "hello..."`). Each rubric includes an escape clause
("missing or unclear evidence is FAIL"), so the judge never has to guess. The judge
moved from Haiku 4.5 to Sonnet 5.5 after Haiku failed a correct answer 3/3 in a
smoke run. `judge-audit.md` lists every verdict with its evidence for human
spot-checks.

## Reference solutions

Every case that produces files has a `reference/` directory holding a known-good
answer. `scripts/check-references.py` proves three things for each:

1. The scaffold starts in the intended state: the debugging case starts red, the
   TDD case starts green.
2. The reference passes the tests.
3. Every file-targeting regex grader accepts the reference.

This catches graders that no correct answer could pass, before any paid run.
Anthropic: "A 0% pass@100 score typically signals a broken task."

## Metrics

Per case, per arm (`scripts/collect.py`):

| Metric | Meaning |
| --- | --- |
| score | Mean run score: the fraction of scored graders passed, as `claude plugin eval` reports it |
| outcome / process | Pass rate over outcome or process graders only, with a Wilson 95% interval |
| solved | Runs where every scored grader passed |
| pass@3 | P(at least one of 3 runs is solved): can it ever do this? |
| pass^3 | P(all 3 of 3 runs are solved): will it do this every time? |
| Δ [95% CI] | with − without, with a bootstrap interval over runs (10,000 resamples, fixed seed) |
| cost, turns, tool calls | Mean per run, from the result JSON and traces |
| skill fired, ran tests | Counted from the traces, in both arms |

pass@k and pass^k use the unbiased estimators over n runs: 1 − C(n−c, k)/C(n, k)
and C(c, k)/C(n, k).

## Environment

- Claude Code 2.1.284 inside a Linux container (`Dockerfile`), with `bubblewrap`
  for the Bash sandbox. On the macOS host, `claude plugin eval` refuses
  Bash-granting runs because Docker Desktop keeps symlinks in `~/.docker`.
- The container needs `--security-opt systempaths=unconfined`, or bubblewrap can't
  mount `/proc` and every Bash call fails.
- Agent model: `claude-sonnet-5-5`. Judge: `claude-sonnet-5-5`. Both pinned.
- Grants: `Bash`, `Write`, `Edit`, plus read-only tools and `Skill`/`Agent`. Bash
  network access is blocked by the sandbox.
- The host is kept awake (`caffeinate -i`) during runs. One smoke pass stalled for
  68 minutes when the Mac slept.

## Freezing graders

Graders changed only during smoke passes (1 run per arm), and every change is
logged in the README change log with its reason. After a freeze, results are
reported as scored, even when a verdict looks wrong. That case goes in the
write-up; the rubric is not quietly fixed. The v1 run (6 cases × 5 runs) is kept
beside v2 for comparison.

## Threats to validity

- **Small, synthetic tasks.** Twelve toy Node projects are not a real codebase.
  Skills that pay off on long, messy work (subagent-driven development, plan
  execution, worktrees) are not tested at all.
- **Strong baseline, saturated cases.** Several positive cases score 1.00 without
  the plugin. That shows Sonnet 5.5 already behaves that way on *these* tasks, not
  that the skill never helps.
- **Headless runs.** Evals are single-turn `claude -p` sessions. Brainstorming's
  "ask first" ends the run, so its value in a real back-and-forth is not measured.
- **Process graders encode superpowers' own definition of good.** "Saw red" is TDD
  orthodoxy. The suite reports it separately so readers can weigh it themselves.
- **Judge is the same model family as the agent.** Self-preference bias is
  possible. The judge audit exists to let a human check it.
- **n = 8 per arm.** Intervals are wide. A Δ whose CI crosses 0 is "no measurable
  effect", not "no effect".
- **One model, one plugin version.** Results can move with a model release or a
  superpowers update. Both are pinned, and the suite reruns with one command.

## Sources

- Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (2026): balanced problem sets, reference solutions, outcomes over paths, isolated trials, pass@k vs pass^k, calibrating judges, reading transcripts.
- Claude Code docs, [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals): ablation arms, grader types, isolation.
- [SkillsBench](https://huggingface.co/papers/2602.12670) (2026): curated skills +16.2 pp on average but only +4.5 pp in software engineering, and 16 of 84 tasks got worse with skills.
- LLM-as-judge practice: [futureagi](https://futureagi.com/blog/llm-as-judge-best-practices-2026/), [Confident AI](https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide) (calibration against human labels, known judge biases).
