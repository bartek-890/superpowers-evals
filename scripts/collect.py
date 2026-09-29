#!/usr/bin/env python3
"""Copy each run's trace next to aggregate-result.json and summarize both arms.

Usage: scripts/collect.py <results-dir>

Writes <results-dir>/traces/<case>/<arm>-<n>.jsonl, summary.json, summary.md.
Behavior metrics come from the traces, not from graders, so they are
reported for both arms: which skills fired, and how often tests were run.
"""
import json, os, re, shutil, statistics, sys

TEST_CMD = re.compile(r"npm (run )?test|node --test")


def trace_stats(path):
    skills, test_runs, tool_calls = [], 0, 0
    if not path or not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8"):
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
            tool_calls += 1
            inp = b.get("input") or {}
            if b.get("name") == "Skill":
                skills.append(str(inp.get("skill", "")).split(":")[-1])
            if b.get("name") == "Bash" and TEST_CMD.search(str(inp.get("command", ""))):
                test_runs += 1
    return {"skills": skills, "testRuns": test_runs, "toolCalls": tool_calls}


def mean(xs):
    return round(statistics.mean(xs), 4) if xs else None


def sd(xs):
    return round(statistics.stdev(xs), 4) if len(xs) > 1 else 0.0


def main(results_dir):
    agg = json.load(open(os.path.join(results_dir, "aggregate-result.json")))
    summary = {"claudeVersion": agg.get("claudeVersion"), "costUsd": agg.get("costUsd"),
               "partial": agg.get("partial"), "cases": []}
    for case in agg["cases"]:
        row = {"case": case["name"], "delta": case["aggregates"].get("delta"), "arms": {}}
        for arm, runs in case["arms"].items():
            stats = []
            for i, r in enumerate(runs, 1):
                src = r.get("tracePath")
                dst = os.path.join(results_dir, "traces", case["name"], f"{arm}-{i}.jsonl")
                if src and os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(src, dst)
                stats.append(trace_stats(dst))
            scores = [r["score"] for r in runs]
            known = [s for s in stats if s]
            skill_counts = {}
            for s in known:
                for name in set(s["skills"]):
                    skill_counts[name] = skill_counts.get(name, 0) + 1
            row["arms"][arm] = {
                "runs": len(runs),
                "scoreMean": mean(scores), "scoreSd": sd(scores),
                "costMean": mean([r["costUsd"] for r in runs]),
                "turnsMean": mean([r["turns"] for r in runs]),
                "errors": [r["error"] for r in runs if r.get("error")],
                "runsWithSkill": skill_counts,
                "runsThatRanTests": sum(1 for s in known if s["testRuns"] > 0),
                "toolCallsMean": mean([s["toolCalls"] for s in known]),
            }
        summary["cases"].append(row)
    json.dump(summary, open(os.path.join(results_dir, "summary.json"), "w"), indent=2)

    lines = ["| Case | With (sd) | W/out (sd) | Δ | Cost with / w/out | Turns with / w/out | Skills fired (with) | Ran tests with / w/out |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in summary["cases"]:
        w, o = row["arms"].get("with", {}), row["arms"].get("without", {})
        fired = ", ".join(f"{k} {v}/{w['runs']}" for k, v in sorted(w.get("runsWithSkill", {}).items())) or "none"
        d = row["delta"]
        lines.append(
            f"| {row['case']} | {w.get('scoreMean')} ({w.get('scoreSd')}) | {o.get('scoreMean')} ({o.get('scoreSd')}) "
            f"| {'' if d is None else f'{d:+.2f}'} | ${w.get('costMean')} / ${o.get('costMean')} "
            f"| {w.get('turnsMean')} / {o.get('turnsMean')} | {fired} "
            f"| {w.get('runsThatRanTests')}/{w.get('runs')} / {o.get('runsThatRanTests')}/{o.get('runs')} |")
    open(os.path.join(results_dir, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
