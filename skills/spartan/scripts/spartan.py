#!/usr/bin/env python3
"""spartan.py: read-only helpers for Spartan. Standard library only, Python 3.9+.

    spartan.py changes [--phase P1] [--module M1] [--since YYYY-MM-DD] [--limit 1500] [--project PRJ-0001]
    spartan.py threats <signal> [<signal> …]

`changes`: for each Critical module (in the phase, or the one given) prints its Paths, the last recorded security
review, the commits touching those paths since then, the size of the diff and the `git diff` command to read. A diff
of more than --limit changed lines is split into parts by sub-folder, one command per part. Never writes anywhere.

`threats`: prints only the threat-note questions for the signals named (money, personal data, auth, integration,
states, regulation, migration) from references/threat-notes.md, so nobody has to read the whole file.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((SKILL / ".." / ".." / "lib").resolve()))

LIMIT = 1500                 # changed lines one review pass reads well
MAX_LOG = 40                 # log lines shown per repository
ALIASES = {
    "money": "money", "payment": "money", "payments": "money", "billing": "money", "finance": "money",
    "personal data": "personal data", "personal": "personal data", "pii": "personal data", "health": "personal data",
    "health data": "personal data", "privacy": "personal data",
    "auth": "auth", "login": "auth", "roles": "auth", "permissions": "auth", "authentication": "auth",
    "authorisation": "auth", "authorization": "auth",
    "integration": "integration", "integrations": "integration", "outside integration": "integration",
    "webhook": "integration", "api": "integration",
    "states": "states", "state": "states", "state machine": "states", "workflow": "states",
    "regulation": "regulation", "regulations": "regulation", "regulated": "regulation", "compliance": "regulation",
    "migration": "migration", "data migration": "migration",
}


def git(repo: Path, args: List[str]) -> str:
    r = subprocess.run(["git"] + args, cwd=str(repo), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


# ───────── changes ─────────

def split_parts(files: Dict[str, int], limit: int) -> List[Tuple[str, List[str], int]]:
    """Split changed files (path → changed lines) into review parts of about `limit` lines, by sub-folder.
    Returns (label, files, lines) per part."""
    def walk(prefix: str, group: Dict[str, int]) -> List[Tuple[str, List[str], int]]:
        total = sum(group.values())
        here = sorted(f for f in group if "/" not in f[len(prefix):])
        subs: Dict[str, Dict[str, int]] = {}
        for f in group:
            rest = f[len(prefix):]
            if "/" in rest:
                subs.setdefault(prefix + rest.split("/", 1)[0] + "/", {})[f] = group[f]
        if total <= limit or not subs:
            return [(prefix or "./", sorted(group), total)]
        out: List[Tuple[str, List[str], int]] = []
        if here:
            out.append(("files directly in " + (prefix or "the repository root"), here, sum(group[f] for f in here)))
        for sp in sorted(subs):
            out += walk(sp, subs[sp])
        return out

    parts = walk("", files)
    merged: List[Tuple[str, List[str], int]] = []       # put small neighbours together, up to the limit
    for label, fs, n in parts:
        if merged and merged[-1][2] + n <= limit:
            pl, pf, pn = merged[-1]
            merged[-1] = (pl + " + " + label, pf + fs, pn + n)
        else:
            merged.append((label, fs, n))
    return merged


def cmd_changes(a: argparse.Namespace) -> int:
    import atlasctl as A  # noqa: E402
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
        return 0
    repos = p.repo_paths()
    if not repos:
        print("No code repository linked on this device. Ask the user for it: `atlas link-repo <name> <path>`.")
    evs = [e for e in p.events() if e.get("type") == "review.security"]
    for mid in targets:
        m = mods[mid]
        last = [e for e in evs if mid in e.get("refs", [])]
        since = a.since or (last[-1]["ts"] if last else "")
        print("## %s %s (%s)" % (mid, m["name"], m["rigour"]))
        print("Paths: %s" % (", ".join(m["paths"]) or "? (unknown — ask the user, or leave a note for stark)"))
        print("Last security review: %s" % (("%s — %s" % (last[-1]["ts"][:10], last[-1]["summary"])) if last else "none"))
        print("Intended behaviour: atlas pack spartan --module %s" % mid)
        if not m["paths"]:
            print()
            continue
        spec = [":(glob)%s" % g for g in m["paths"]]
        for name, repo in repos.items():
            args = ["log", "--no-merges", "--format=%h %ad %an: %s", "--date=short"]
            if since:
                args.append("--since=%s" % since)
            log = git(repo, args + ["--"] + spec).strip().splitlines()
            print("\n[%s] %s%s" % (name, repo, (" since " + since[:19]) if since else " (full history)"))
            if not log:
                print("no commits touching these paths")
                continue
            oldest = log[-1].split()[0]
            base = oldest + "^" if git(repo, ["rev-parse", "-q", "--verify", oldest + "^"]).strip() else \
                git(repo, ["hash-object", "-t", "tree", "/dev/null"]).strip()
            files: Dict[str, int] = {}
            for ln in git(repo, ["diff", "--numstat", base, "HEAD", "--"] + spec).splitlines():
                parts = ln.split("\t")
                if len(parts) == 3:
                    files[parts[2]] = sum(int(x) for x in parts[:2] if x.isdigit())
            total = sum(files.values())
            print("%d commit(s), %d file(s), %d changed line(s):" % (len(log), len(files), total))
            print("\n".join("  " + ln for ln in log[:MAX_LOG]))
            if len(log) > MAX_LOG:
                print("  … %d older commit(s) not shown" % (len(log) - MAX_LOG))
            diff = "git -C '%s' diff %s HEAD -- " % (repo, base)
            if total <= a.limit:
                print("Diff to read: " + diff + " ".join("'%s'" % s for s in spec))
                continue
            parts_ = split_parts(files, a.limit)
            print("LARGE CHANGE: more than %d lines. Review it in %d part(s), one at a time, and say in the report "
                  "that the review was split by sub-folder:" % (a.limit, len(parts_)))
            for i, (label, fs, n) in enumerate(parts_, 1):
                print("  Part %d/%d — %s — %d line(s), %d file(s)%s" % (
                    i, len(parts_), label, n, len(fs), " (over the limit on its own: read it file by file)"
                    if n > a.limit else ""))
                print("    " + diff + " ".join("'%s'" % f for f in fs))
        print()
    return 0


# ───────── threats ─────────

def threat_sections() -> Dict[str, str]:
    text = (SKILL / "references" / "threat-notes.md").read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->\n?", "", text, flags=re.S)
    out: Dict[str, str] = {}
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        out[head.strip().lower()] = body.strip()
    return out


def cmd_threats(a: argparse.Namespace) -> int:
    sec = threat_sections()
    signals = sorted(k for k in sec if k not in ("how to write them", "always"))
    asked = [x.strip().lower() for s in a.signals for x in re.split(r"[,;·]", s) if x.strip()]
    want: List[str] = []
    unknown = []
    for s in asked:
        key = ALIASES.get(s) or next((k for k in signals if k in s), None) \
            or next((v for k, v in ALIASES.items() if re.search(r"\b%s\b" % re.escape(k), s)), None)
        if key in sec and key not in want:
            want.append(key)
        elif key not in sec and s not in ("none", "-", "—"):
            unknown.append(s)
    if unknown:
        print("spartan: no questions for %s. Signals: %s." % (", ".join(unknown), ", ".join(signals)), file=sys.stderr)
    if not want:
        return 2 if unknown else 0
    print("# Threat notes — questions for: %s\n" % ", ".join(want))
    print(sec.get("how to write them", "") + "\n")
    for k in want:
        print("## %s\n%s\n" % (k.capitalize(), sec[k]))
    print("## Always (failure, rollback, abuse)\n%s" % sec.get("always", ""))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(prog="spartan.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("changes")
    x.add_argument("--phase"); x.add_argument("--module"); x.add_argument("--since"); x.add_argument("--project")
    x.add_argument("--limit", type=int, default=LIMIT)
    x.set_defaults(fn=cmd_changes)
    x = sub.add_parser("threats"); x.add_argument("signals", nargs="+"); x.set_defaults(fn=cmd_threats)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
