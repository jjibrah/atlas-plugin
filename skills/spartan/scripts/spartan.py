#!/usr/bin/env python3
"""spartan.py: read-only helper for Spartan's security review. Standard library only, Python 3.9+.

    spartan.py changes [--phase P1] [--module M1] [--since YYYY-MM-DD] [--project PRJ-0001]

For each Critical module (in the phase, or the one given) prints its Paths, the linked code repositories on this
device, the last recorded security review, and the commits + files touching those paths since then. Never writes
to a code repository.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((SKILL / ".." / ".." / "lib").resolve()))
import atlasctl as A  # noqa: E402


def git(repo: Path, args: List[str]) -> str:
    r = subprocess.run(["git"] + args, cwd=str(repo), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def main() -> None:
    ap = argparse.ArgumentParser(prog="spartan.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("changes")
    x.add_argument("--phase"); x.add_argument("--module"); x.add_argument("--since"); x.add_argument("--project")
    a = ap.parse_args()
    p = A.find_project(A.load_config(), a.project)
    mods = {m["id"]: m for m in A.read_modules(p)}
    if a.module:
        if a.module not in mods:
            sys.exit("unknown module %s (MODULES.md has: %s)" % (a.module, ", ".join(mods) or "none"))
        targets = [a.module]
    else:
        _, wps = A.read_plan(p)
        phase_mods = {m for w in wps if not a.phase or w["phase"] == a.phase for m in w["modules"]}
        targets = sorted(m for m in phase_mods if m in mods and mods[m]["rigour"] == "Critical")
    if not targets:
        print("No Critical modules%s — no security review needed." % ((" in " + a.phase) if a.phase else ""))
        return
    repos = p.repo_paths()
    if not repos:
        print("No code repository linked on this device. Ask the user for it: `atlasctl link-repo <name> <path>`.")
    evs = [e for e in p.events() if e.get("type") == "review.security"]
    for mid in targets:
        m = mods[mid]
        last = [e for e in evs if mid in e.get("refs", [])]
        since = a.since or (last[-1]["ts"] if last else "")
        print("## %s %s (%s)" % (mid, m["name"], m["rigour"]))
        print("Paths: %s" % (", ".join(m["paths"]) or "? (unknown — ask the user or /stark)"))
        print("Last security review: %s" % (("%s — %s" % (last[-1]["ts"][:10], last[-1]["summary"])) if last else "none"))
        if not m["paths"]:
            print()
            continue
        spec = [":(glob)%s" % g for g in m["paths"]]
        for name, repo in repos.items():
            args = ["log", "--no-merges", "--format=--- %h %ad %an: %s", "--date=short", "--name-only"]
            if since:
                args.append("--since=%s" % since)
            out = git(repo, args + ["--"] + spec).strip()
            print("\n[%s] %s%s" % (name, repo, (" since " + since[:19]) if since else " (full history)"))
            print(out if out else "no commits touching these paths")
            if out:
                oldest = [ln.split()[1] for ln in out.splitlines() if ln.startswith("--- ")][-1]
                base = oldest + "^" if git(repo, ["rev-parse", "-q", "--verify", oldest + "^"]).strip() else \
                    git(repo, ["hash-object", "-t", "tree", "/dev/null"]).strip()
                print("Diff to read: git -C '%s' diff %s HEAD -- %s" % (repo, base, " ".join("'%s'" % s for s in spec)))
        print()


if __name__ == "__main__":
    main()
