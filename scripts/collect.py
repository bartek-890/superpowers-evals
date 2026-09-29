#!/usr/bin/env python3
"""Copy each run's trace next to aggregate-result.json and summarize both arms.

Usage: scripts/collect.py <results-dir>

Writes into <results-dir>:
  traces/<case>/<arm>-<n>.jsonl   raw transcript of every run
  summary.json / summary.md       per-case, per-arm statistics
  judge-audit.md                  every llm verdict with the evidence it saw,
                                  for human spot-checking

Statistics (per case, per arm):
  score      mean run score as claude plugin eval computes it (all scored graders)
  outcome    pass rate of outcome graders only (what was produced)
  process    pass rate of process graders only (how it was produced)
  solved     a run is solved when every scored grader passed
  pass@3     P(at least one of 3 runs is solved), unbiased estimator
  pass^3     P(all 3 of 3 runs are solved), unbiased estimator
  CIs        Wilson 95% for rates, bootstrap 95% for the with-minus-without delta
Behavior (from traces, both arms): which skills fired, whether tests were run,
tool calls, turns, cost, and sandbox errors (a broken environment check).
"""
import json, math, os, random, re, shutil, statistics, sys
from math import comb

TEST_CMD = re.compile(r"npm (run )?test|node --test")
# Graders that check the path rather than the result. Everything else is outcome.
PROCESS = {"saw-red", "tests-green", "tests-before-commit", "no-code-before-questions", "asks-a-question"}


def trace_stats(path):
    s = {"skills": [], "testRuns": 0, "toolCalls": 0, "sandboxErrors": 0}
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8"):
        if "bwrap:" in line or ("sandbox" in line and "Operation not permitted" in line):
            s["sandboxErrors"] += 1
        try:
            m = json.loads(line)
        except ValueError:
            continue
        msg = m.get("message") if isinstance(m, dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            s["toolCalls"] += 1
            inp = b.get("input") or {}
            if b.get("name") == "Skill":
                s["skills"].append(str(inp.get("skill", "")).split(":")[-1])
            if b.get("name") == "Bash" and TEST_CMD.search(str(inp.get("command", ""))):
                s["testRuns"] += 1
    return s


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def pass_at(n, c, k):
    if n < k:
        return None
    return round(1 - comb(n - c, k) / comb(n, k), 3)


def pass_hat(n, c, k):
    if n < k:
        return None
    return round(comb(c, k) / comb(n, k), 3)


def boot_delta(a, b, iters=10000, seed=7):
    if not a or not b:
        return None
    rng = random.Random(seed)
    ds = sorted(statistics.mean(rng.choices(a, k=len(a))) - statistics.mean(rng.choices(b, k=len(b)))
                for _ in range(iters))
    return [round(ds[int(0.025 * iters)], 3), round(ds[int(0.975 * iters)], 3)]


def rate(runs, names):
    k = n = 0
    for r in runs:
        for g in r["graders"]:
            if g.get("scored", True) and g["name"] in names:
                n += 1
                k += bool(g["passed"])
    return {"pass": k, "of": n, "rate": round(k / n, 3) if n else None, "ci95": wilson(k, n)}


def main(results_dir):
    agg = json.load(open(os.path.join(results_dir, "aggregate-result.json")))
    summary = {"claudeVersion": agg.get("claudeVersion"), "costUsd": round(agg.get("costUsd", 0), 2),
               "partial": agg.get("partial"), "cases": []}
    audit = ["# Judge audit", "",
             "Every `llm` grader verdict, with the evidence the judge saw. Spot-check these by hand:",
             "mark a row where you disagree, and treat a disagreement rate above ~10% as a broken rubric.", ""]
    for case in agg["cases"]:
        scored = {g["name"] for r in case["arms"]["with"] for g in r["graders"] if g.get("scored", True)}
        row = {"case": case["name"], "delta": case["aggregates"].get("delta"), "arms": {}}
        scores = {}
        for arm, runs in case["arms"].items():
            stats = []
            for i, r in enumerate(runs, 1):
                src, dst = r.get("tracePath"), os.path.join(results_dir, "traces", case["name"], f"{arm}-{i}.jsonl")
                if src and os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(src, dst)
                stats.append(trace_stats(dst))
                for g in r["graders"]:
                    if "judgeVotes" in g:
                        ev = (g.get("evidence") or "").strip().replace("\n", " ")
                        audit.append(f"- **{case['name']}** · {arm} run {i} · `{g['name']}` · "
                                     f"{'PASS' if g['passed'] else 'FAIL'} ({g['explanation'].replace('judge votes: ', '')})"
                                     f"  \n  > {ev[:600]}{'…' if len(ev) > 600 else ''}")
            scores[arm] = [r["score"] for r in runs]
            n = len(runs)
            solved = sum(1 for r in runs if all(g["passed"] for g in r["graders"] if g.get("scored", True)))
            known = [s for s in stats if s]
            fired = {}
            for s in known:
                for name in set(s["skills"]):
                    fired[name] = fired.get(name, 0) + 1
            row["arms"][arm] = {
                "runs": n,
                "scoreMean": round(statistics.mean(scores[arm]), 3),
                "scoreSd": round(statistics.stdev(scores[arm]), 3) if n > 1 else 0.0,
                "outcome": rate(runs, scored - PROCESS),
                "process": rate(runs, scored & PROCESS),
                "solved": solved, "solvedCi95": wilson(solved, n),
                "passAt3": pass_at(n, solved, 3), "passHat3": pass_hat(n, solved, 3),
                "costMean": round(statistics.mean(r["costUsd"] for r in runs), 4),
                "turnsMean": round(statistics.mean(r["turns"] for r in runs), 1),
                "errors": [r["error"] for r in runs if r.get("error")],
                "runsWithSkill": fired,
                "runsThatRanTests": sum(1 for s in known if s["testRuns"]),
                "toolCallsMean": round(statistics.mean(s["toolCalls"] for s in known), 1) if known else None,
                "runsWithSandboxErrors": sum(1 for s in known if s["sandboxErrors"]),
            }
        row["deltaCi95"] = boot_delta(scores.get("with"), scores.get("without"))
        summary["cases"].append(row)
    json.dump(summary, open(os.path.join(results_dir, "summary.json"), "w"), indent=2)
    open(os.path.join(results_dir, "judge-audit.md"), "w").write("\n".join(audit) + "\n")

    def r(x):
        return "–" if not x or x["rate"] is None else f"{x['rate']:.2f}"

    lines = ["| Case | Score with / w/out | Δ [95% CI] | Outcome with / w/out | Process with / w/out "
             "| pass^3 with / w/out | Cost with / w/out | Turns | Skill fired | Ran tests | Errors |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in summary["cases"]:
        w, o = row["arms"]["with"], row["arms"].get("without", {})
        d, ci = row["delta"], row["deltaCi95"]
        fired = ", ".join(f"{k} {v}/{w['runs']}" for k, v in sorted(w["runsWithSkill"].items())) or "none"
        errs = len(w["errors"]) + len(o.get("errors", [])) + w["runsWithSandboxErrors"] + o.get("runsWithSandboxErrors", 0)
        lines.append(
            f"| {row['case']} | {w['scoreMean']:.2f} / {o.get('scoreMean', 0):.2f} "
            f"| {'' if d is None else f'{d:+.2f}'} {'' if not ci else f'[{ci[0]:+.2f}, {ci[1]:+.2f}]'} "
            f"| {r(w['outcome'])} / {r(o.get('outcome'))} | {r(w['process'])} / {r(o.get('process'))} "
            f"| {w['passHat3']} / {o.get('passHat3')} | ${w['costMean']:.3f} / ${o.get('costMean', 0):.3f} "
            f"| {w['turnsMean']} / {o.get('turnsMean')} | {fired} "
            f"| {w['runsThatRanTests']}/{w['runs']} / {o.get('runsThatRanTests')}/{o.get('runs')} | {errs} |")
    open(os.path.join(results_dir, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
