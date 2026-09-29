# Results

superpowers v6.4.2 against no plugin, Claude Sonnet 5.5 as agent and judge,
Claude Code 2.1.284, 2026-09-29. Eight runs per arm per case.

Sources: `results/2026-09-29T14-57-41Z/` (v2, all 12 cases) and, for the three
`verification` cases, `results/2026-09-29T15-08-12Z/` (v2.1, after the scaffold fix
in the README change log). Spend: $14.40 + $3.48 for these two runs, about $26 in
total with v1 and all smoke passes.

## Headline

- **Superpowers changed behavior on 3 of 7 positive cases, and outcomes on 1.** The
  clear effects are brainstorming (ask before building: 8/8 vs 0/8) and TDD (watch
  the test fail first). Only `tdd-bugfix-regression` changed what was delivered:
  without the plugin, 4 of 8 runs fixed the bug without adding a regression test or
  running anything.
- **On debugging, verification, and code review, the no-plugin baseline already
  scored 1.00.** The skills fired every time and added nothing measurable on these
  tasks.
- **No negative case regressed.** Superpowers didn't invent problems in a correct
  fix, didn't argue with valid review, and didn't brainstorm when told not to ask.
- **It costs 1.33× per task and 1.52× the turns on average**, up to 1.63× cost on
  debugging. On the control question, 1 of 8 answers leaked skill-routing talk
  ("No other skill applies…").

## Per case

Score is the mean run score. Outcome and process are grader pass rates (see
METHODOLOGY). pass^3 is the probability that 3 of 3 runs are fully solved. Cost
ratio is with ÷ without.

| Case | Kind | Score with / w/out | Δ [95% CI] | Outcome with / w/out | Process with / w/out | pass^3 with / w/out | Cost × | Turns with / w/out | Skill fired |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| brainstorm-vague-build | positive | 1.00 / 0.00 | **+1.00** [+1.00, +1.00] | – | 1.00 / 0.00 | 1.00 / 0.00 | 1.08 | 3.0 / 3.2 | 8/8 |
| tdd-bugfix-regression | positive | 1.00 / 0.59 | **+0.41** [+0.16, +0.66] | 1.00 / 0.75 | 1.00 / 0.44 | 1.00 / 0.02 | 1.62 | 10.5 / 5.4 | 8/8 |
| tdd-add-function | positive | 1.00 / 0.78 | **+0.22** [+0.16, +0.25] | 1.00 / 1.00 | 1.00 / 0.56 | 1.00 / 0.00 | 1.41 | 8.0 / 5.8 | 8/8 |
| debug-root-cause | positive | 1.00 / 1.00 | 0.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.63 | 10.5 / 5.9 | 8/8 |
| verify-before-claim | positive | 1.00 / 1.00 | 0.00 | 1.00 / 1.00 | – | 1.00 / 1.00 | 1.32 | 4.9 / 2.9 | 8/8 |
| verify-before-commit | positive | 1.00 / 1.00 | 0.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.24 | 8.8 / 6.0 | 2/8 |
| review-pushback | positive | 0.96 / 1.00 | −0.04 [−0.12, 0.00] | 0.96 / 1.00 | – | 0.63 / 1.00 | 1.34 | 9.8 / 6.0 | 8/8 |
| verify-correct-fix | negative | 0.94 / 0.94 | 0.00 [−0.19, +0.19] | 0.94 / 0.94 | – | 0.63 / 0.63 | 1.41 | 5.0 / 2.8 | 8/8 |
| review-valid-feedback | negative | 1.00 / 1.00 | 0.00 | 1.00 / 1.00 | – | 1.00 / 1.00 | 1.45 | 10.0 / 4.5 | 8/8 |
| no-questions-build | negative | 1.00 / 1.00 | 0.00 | 1.00 / 1.00 | – | 1.00 / 1.00 | 1.16 | 5.0 / 5.1 | 0/8 |
| clear-small-change | negative | 1.00 / 1.00 | 0.00 | 1.00 / 1.00 | – | 1.00 / 1.00 | 1.14 | 5.0 / 5.2 | 0/8 |
| control-simple-question | control | 0.88 / 0.88 | 0.00 [−0.38, +0.38] | 0.88 / 0.88 | – | 0.63 / 0.63 | 1.17 | 1.2 / 1.0 | 1/8 (using-superpowers) |

"–" means the case has no grader of that kind.

## Findings

**TDD is the one skill that changes a deliverable.** On `tdd-bugfix-regression` the
with-arm added a regression test and watched it fail in 8/8 runs. Without the
plugin, 4 of 8 runs edited `src/money.js`, didn't touch the test file, ran nothing,
and reported "I haven't run the code or any tests". Every run's code was correct.
The difference is whether a test protects it next time: pass^3 is 1.00 against 0.02.

**On `tdd-add-function` only the process moved.** Both arms shipped a correct,
tested `truncate` 8/8. Only the with-arm reliably saw the test fail first (1.00 vs
0.56). Whether that is worth 1.41× the cost depends on whether you value the ritual
or the result.

**Brainstorming is a pure behavior switch.** With the plugin, 8/8 runs asked
questions and wrote nothing. Without it, 0/8 asked and every run built something.
In this headless setup the with-arm delivers no code at all. That is correct by the
skill's definition, and a cost if you wanted a first draft. Its counterparts held:
told "don't ask me anything, just build it", both arms built a correct `countWords`
8/8, and on a two-line rename brainstorming didn't fire at all (0/8).

**Debugging, verification, and review pushback are saturated.** The baseline found
the shared `parseDate` bug, refused to rubber-stamp the broken rounding fix, and
pushed back on the wrong review item in 8/8 runs each. The skills fired every time,
cost 1.3-1.6× more, and changed only habits:

- the with-arm ran the test suite in 7/8 review-pushback runs vs 0/8
- in 8/8 review-valid-feedback runs vs 1/8

`verify-before-commit` fired its skill in only 2/8 runs. The baseline already ran
tests before committing in 8/8.

**One regression-shaped result is judge noise.** `review-pushback` with-arm run 5
kept the null check and named deleted authors in its reply, but said "for the
reason above", and the judge failed it 3/3. On review, that verdict is wrong (see
the audit below).

**Task design mattered more than the plugin once.** In v2, `verify-correct-fix`
scored 0.81 / 0.75. The scaffold had committed the user's "fix" into the initial
commit, so `git diff` was empty, and agents in both arms reasonably refused to
confirm a fix they couldn't see. With the fix left uncommitted (v2.1), both arms
score 0.94. The remaining failure in each arm is a genuine hedge ("I can't call it
fully verified").

## Judge audit

All 12 FAIL verdicts from the reported runs were reviewed against the evidence the
judge saw (v2: 10, of which 7 were in the superseded `verify-correct-fix`; v2.1: 2).
The 212 PASS verdicts were not reviewed. `judge-audit.md` in each results directory
lists them for a human pass.

| Verdict | Review |
| --- | --- |
| verify-correct-fix v2, 7 FAILs | Fair given the flawed task (fix not visible in git). Superseded by v2.1 |
| verify-correct-fix v2.1, with-4 and without-2 | Agree: the reply declines to confirm a correct fix |
| control with-2 | Agree, borderline: six sentences, including a leaked skill-routing preamble |
| control without-4 | **Disagree**: correct and about five sentences |
| review-pushback with-5 | **Disagree**: kept the guard and gave the deleted-author reason |

That is 2 disagreements among the 5 reviewed FAILs that weren't superseded. Both
flip a score by 1/8 in one arm and change no conclusion. Graders stay frozen, so
the table reports verdicts as scored. The fix belongs in the next version's rubrics
(let the review-pushback judge read the trace, not just the last message).

This review was done by Claude, the same model family as the judge, not by an
independent human expert. Treat it as a first pass.

## What this does and doesn't show

It shows that on small, unambiguous tasks, Sonnet 5.5 without any plugin already
does most of what superpowers asks of it. The plugin reliably adds TDD discipline
and question-first brainstorming, at about a third more cost per task.

It doesn't show how superpowers does on long, messy, multi-session work. Its
planning, subagent, and worktree skills weren't tested, and those are what it's
built around. See METHODOLOGY, Threats to validity.
