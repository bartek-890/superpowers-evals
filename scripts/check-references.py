#!/usr/bin/env python3
"""Prove every case is solvable and its file graders accept a known-good answer.

For each case with a reference/ directory:
  1. run scaffold.sh in a fresh temp dir and check the starting test state
     matches reference/EXPECT (initial=pass|fail)
  2. copy reference/ files over the workspace, run npm test, require # fail 0
  3. evaluate every regex grader that targets { source: file } against the
     reference workspace; it must pass (not_contains must be absent)

llm, tool_used, tool_order and trace graders need a real run and are not
checked here. Run inside the runner image (needs node, git, python3-yaml).
"""
import os, re, shutil, subprocess, sys, tempfile
import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..", "evals")


def npm_test(cwd):
    r = subprocess.run(["npm", "test"], cwd=cwd, capture_output=True, text=True)
    out = r.stdout + r.stderr
    m = re.search(r"# fail (\d+)", out)
    return int(m.group(1)) if m else None


def js_regex(pattern, flags):
    # graders use JavaScript regexes; the ones in this suite are Python-compatible
    return re.compile(pattern, re.I if "i" in (flags or "") else 0)


def check(case_dir):
    name = os.path.basename(case_dir)
    ref = os.path.join(case_dir, "reference")
    spec = yaml.safe_load(open(os.path.join(case_dir, "case.yaml")))
    expect = dict(l.strip().split("=") for l in open(os.path.join(ref, "EXPECT")) if "=" in l)
    problems = []
    with tempfile.TemporaryDirectory() as ws:
        subprocess.run(["bash", os.path.join(case_dir, "scaffold.sh")], cwd=ws, check=True,
                       capture_output=True)
        fails = npm_test(ws)
        state = "pass" if fails == 0 else "fail"
        if state != expect.get("initial"):
            problems.append(f"initial tests {state} (# fail {fails}), expected {expect.get('initial')}")
        for dirpath, _, files in os.walk(ref):
            for f in files:
                if f == "EXPECT":
                    continue
                src = os.path.join(dirpath, f)
                dst = os.path.join(ws, os.path.relpath(src, ref))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
        fails = npm_test(ws)
        if fails != 0:
            problems.append(f"reference does not pass tests (# fail {fails})")
        checked = 0
        for g in spec.get("graders", []):
            t = g.get("target")
            if g.get("type") != "regex" or not isinstance(t, dict) or t.get("source") != "file":
                continue
            checked += 1
            text = open(os.path.join(ws, t["path"])).read()
            found = bool(js_regex(g["pattern"], g.get("flags")).search(text))
            want = g.get("match", "contains") != "not_contains"
            if found != want:
                problems.append(f"grader {g['name']} fails on reference")
    status = "ok" if not problems else "FAIL"
    print(f"{status:4} {name}: {checked} file graders checked" + "".join(f"\n     - {p}" for p in problems))
    return not problems


if __name__ == "__main__":
    cases = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d, "reference")))
    results = [check(os.path.join(ROOT, c)) for c in cases]
    skipped = sorted(d for d in os.listdir(ROOT) if os.path.isfile(os.path.join(ROOT, d, "case.yaml")) and d not in cases)
    print(f"{sum(results)}/{len(results)} cases ok; no reference (text-only answers): {', '.join(skipped)}")
    sys.exit(0 if all(results) else 1)
