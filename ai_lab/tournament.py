#!/usr/bin/env python3
"""Local, owner-operated research tournament. Python 3.10+, Git. No API keys needed."""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

AGENTS = ("claude", "codex", "gemini")

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def clean_sha(path):
    if git(path, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError(f"Commit or remove pending changes in {path}")
    return git(path, "rev-parse", "HEAD")

def start(root, workspace, name, base, task):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name):
        raise ValueError("Round name must contain lowercase letters, digits or hyphens.")
    sha = git(root, "rev-parse", "--verify", base + "^{commit}")
    if workspace == root or root in workspace.parents:
        raise ValueError("Round workspace must be outside the repository.")
    workspace.mkdir(parents=True, exist_ok=False)
    state = {"round": name, "base": sha, "repository": str(root),
             "task": task, "agents": {}}
    for agent in AGENTS:
        folder = workspace / agent
        ref = f"lab/{name}/{agent}"
        git(root, "worktree", "add", "-b", ref, str(folder), sha)
        state["agents"][agent] = {"path": str(folder), "branch": ref}
        write(workspace / "round.json", state)
        (workspace / f"{agent}-task.md").write_text(
            f"# {name}: {agent}\n\nBaseline: {sha}\nWorkspace: {folder}\n\n"
            f"{task}\n\nRead AGENTS.md, FIGURINE-AGENT-PROMPT.md and improvements/INDEX.md. "
            "Work only in this worktree and your own agent folder; proposed shared-tool changes "
            "may be made in this isolated branch for research. Do not modify judge inputs, "
            "thresholds, reference cases or evaluator. Preserve previous jobs. Commit your "
            "candidate and record assumptions, failures, commands and evidence. Do not merge "
            "or push to main. Do not copy a rival before independent submissions are frozen.\n",
            encoding="utf-8")
    git(root, "worktree", "add", "--detach", str(workspace / "baseline"), sha)
    print(f"Round created at {workspace}; open each worktree in its agent.")

def freeze(workspace):
    state = read(workspace / "round.json")
    if set(state["agents"]) != set(AGENTS):
        raise ValueError("Incomplete round")
    root = Path(state["repository"])
    candidates = {}
    for name, item in state["agents"].items():
        path = Path(item["path"])
        sha = clean_sha(path)
        if git(root, "merge-base", state["base"], sha) != state["base"]:
            raise ValueError(f"{name}: candidate does not descend from baseline")
        candidates[name] = sha
    if clean_sha(workspace / "baseline") != state["base"]:
        raise ValueError("Baseline changed")
    frozen = workspace / "frozen.json"
    if frozen.exists():
        raise ValueError("Round already frozen; start a new round for revisions")
    write(frozen, candidates)
    for reviewer in AGENTS:
        rivals = [a for a in AGENTS if a != reviewer]
        lines = [f"# Independent review by {reviewer}", f"Base: {state['base']}",
                 "Review both frozen rivals. Do not edit their branches. Identify bugs, "
                 "regressions, hidden assumptions and reusable ideas. Cite files and evidence. "
                 "Separate measured results from guesses; do not vote by brand. "
                 "Write findings in the owner-controlled round directory."]
        for rival in rivals:
            lines.append(f"\n## {rival}\nRun: git diff {state['base']} {candidates[rival]}")
        (workspace / f"{reviewer}-review.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("Frozen commits and cross-review prompts created.")

def numbers(data, rules):
    if not isinstance(data, dict) or data.get("pass") is not True:
        raise ValueError("Independent judge did not return pass: true")
    values = data.get("metrics", {})
    if not isinstance(values, dict):
        raise ValueError("Missing metrics object")
    result = {}
    for key in rules:
        v = values.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError(f"Missing/non-finite metric: {key}")
        result[key] = v
    return result

def compare(baseline, candidate, rules):
    gains = []
    regressions = []
    for key, direction in rules.items():
        delta = candidate[key] - baseline[key]
        if direction == "min":
            delta = -delta
        if delta < 0:
            regressions.append(key)
        elif delta > 0:
            gains.append(key)
    return gains, regressions

def allowed_paths(root, base, sha, prefixes):
    # Disable rename detection so both the old and new path are checked.
    raw = subprocess.check_output(["git", "-C", str(root), "diff", "--no-renames",
                                   "--name-only", "-z", base, sha])
    paths = [p.decode("utf-8") for p in raw.split(b"\0") if p]
    return [p for p in paths if not any(p == a or (a.endswith("/") and p.startswith(a))
                                       for a in prefixes)]

def evaluate(workspace, config_path):
    state = read(workspace / "round.json")
    frozen = read(workspace / "frozen.json")
    root = Path(state["repository"])
    config = read(config_path)
    rules = config["metrics"]
    argv = config["judge_command"]
    prefixes = config["allowed_paths"]
    if not rules or any(d not in ("min", "max") for d in rules.values()):
        raise ValueError("Specify nonempty metrics with min/max directions")
    priority = config.get("priority", list(rules))
    if len(priority) != len(rules) or set(priority) != set(rules):
        raise ValueError("Priority must list each metric exactly once")
    if not argv or not all(isinstance(a, str) for a in argv):
        raise ValueError("Judge command must be an argv list")
    if not Path(argv[0]).is_absolute():
        raise ValueError("Use an absolute executable path")
    if not prefixes or any(not isinstance(p, str) or not p or p.startswith("/") or ".." in p.split("/") for p in prefixes):
        raise ValueError("Specify explicit repo-relative allowed paths")
    if any(p.split("/")[0] in ("jobs", "scoreboard", "ai_lab", ".github") for p in prefixes):
        raise ValueError("Judge, orchestrator and CI files cannot be candidate edits")
    timeout = config.get("timeout_seconds", 3600)
    run_dir = workspace / "judgments"
    run_dir.mkdir(exist_ok=False)
    report = {"base": state["base"], "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
              "candidates": {}, "recommended": None}
    def judge(name, path, sha):
        if clean_sha(path) != sha:
            raise ValueError(f"{name}: frozen commit changed")
        output = run_dir / f"{name}.json"
        command = [a.replace("{candidate}", str(path)).replace("{output}", str(output))
                   .replace("{commit}", sha) for a in argv]
        with (run_dir / f"{name}.log").open("w", encoding="utf-8") as log:
            subprocess.run(command, cwd=config_path.parent, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=timeout)
        if clean_sha(path) != sha:
            raise ValueError(f"{name}: judge modified candidate worktree")
        return numbers(read(output), rules)
    baseline = judge("baseline", workspace / "baseline", state["base"])
    report["baseline_metrics"] = baseline
    for name in AGENTS:
        sha = frozen[name]
        entry = {"commit": sha, "eligible": False}
        try:
            outside = allowed_paths(root, state["base"], sha, prefixes)
            if outside:
                raise ValueError(f"Disallowed changes: {outside}")
            values = judge(name, Path(state["agents"][name]["path"]), sha)
            gains, losses = compare(baseline, values, rules)
            entry.update(metrics=values, gains=gains, regressions=losses,
                         eligible=bool(gains) and not losses)
        except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
            entry["error"] = str(exc)
        report["candidates"][name] = entry
        write(run_dir / "report.json", report)
    def rank(name):
        return tuple(report["candidates"][name]["metrics"][m] * (1 if rules[m]=="min" else -1)
                     for m in priority)
    eligible = sorted((a for a in AGENTS if report["candidates"][a]["eligible"]), key=rank)
    if eligible and (len(eligible) == 1 or rank(eligible[0]) != rank(eligible[1])):
        report["recommended"] = eligible[0]
    elif eligible:
        report["tie"] = [a for a in eligible if rank(a) == rank(eligible[0])]
    write(run_dir / "report.json", report)
    print(json.dumps(report, indent=2))
    print("Recommendation only: owner reviews evidence, then integrates and retests.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("start")
    p.add_argument("workspace", type=Path)
    p.add_argument("--round", required=True)
    p.add_argument("--base", default="HEAD")
    p.add_argument("--task-file", required=True, type=Path)
    p = sub.add_parser("freeze")
    p.add_argument("workspace", type=Path)
    p = sub.add_parser("evaluate")
    p.add_argument("workspace", type=Path)
    p.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if args.command == "start":
        root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
        start(root, workspace, args.round, args.base, args.task_file.read_text(encoding="utf-8"))
    elif args.command == "freeze":
        freeze(workspace)
    else:
        config = args.config.resolve()
        state = read(workspace / "round.json")
        root = Path(state["repository"]).resolve()
        if config == root or root in config.parents or workspace in config.parents:
            raise ValueError("Keep judge config in a separate owner-controlled directory")
        evaluate(workspace, config)

if __name__ == "__main__":
    main()
