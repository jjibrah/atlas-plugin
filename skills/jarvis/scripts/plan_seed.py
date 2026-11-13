#!/usr/bin/env python3
"""Propose work-package rows for PLAN.md from Stark's requirements register and MODULES.md.

Usage: plan_seed.py <P> [--out <file>]

  <P>     the project storage folder (the `P =` line of `atlas begin`)
  --out   write the proposal to a file (normally <P>/plan/_work/seed.md) instead of printing it

What it does — the mechanical half of planning:
  - takes every live REQ (not out of scope / deferred / rejected / removed) that no work package in an existing
    PLAN.md covers and that is not in its `| REQ | Evidence |` table of requirements already built;
  - groups them by module and splits each group to the size the module's rigour allows (the confirmed level wins):
      Light     1 package per module, 2 when it has more than 8 REQs
      Standard  at most ~6 REQs per package
      Critical  at most ~3 REQs per package, size S, title ends "+ review"
  - orders modules by dependency when the design gives one (a `Depends on` column in a module table of TECHNICAL.md
    or MODULES.md, the `Depends on` row of technical/mNN-*.md, or the flowchart under a "Build order" heading);
  - chains the packages (within a module, and from a module to the ones it depends on);
  - prints the work-package table in the exact format Atlas reads, with `{{…}}` placeholders for titles and phases.

What is left to the planner — the judgement half: merge packages into vertical slices, order them by risk, give
each a real title, assign phases, cut dependencies that are not real. verify.py fails while a placeholder remains.
Read-only on the design. Python 3.9+, standard library only.
"""
from __future__ import annotations

import math
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "..", "lib")))
import atlasctl as A  # noqa: E402
import flow  # noqa: E402  (the same readers `atlas pack` and the staleness stamps use)
import mdtables as md  # noqa: E402

DEAD = ("out of scope", "deferred", "rejected", "removed")
PER_PACKAGE = {"Standard": 6, "Critical": 3}
LIGHT_SPLIT_ABOVE = 8


def num(i: str) -> int:
    return int(re.sub(r"\D", "", i) or 0)


def first_module(cell: str) -> str:
    m = re.findall(r"\bM\d+\b", cell)
    if m:
        return m[0]
    return "X" if cell.strip("* ").upper() == "X" else "?"


def compact(ids: List[str]) -> str:
    """REQ-001, REQ-002, REQ-003, REQ-007 → 'REQ-001–REQ-003, REQ-007' (runs of 3 or more become a range)."""
    ids = sorted(ids, key=num)
    out, i = [], 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and num(ids[j + 1]) == num(ids[j]) + 1:
            j += 1
        if j - i >= 2:
            out.append("%s–%s" % (ids[i], ids[j]))
        else:
            out += ids[i:j + 1]
        i = j + 1
    return ", ".join(out)


def built_reqs(p: A.Project) -> Set[str]:
    """REQs in PLAN.md's `| REQ | Evidence |` table — read the way gate G3 reads it."""
    out: Set[str] = set()
    for t in md.read_tables(p.path / "plan" / "PLAN.md"):
        if t.col("req") == 0 and t.col("evidence") is not None:
            for r in t.rows:
                out |= {x for x in md.expand_ranges(r[0] if r else "") if x.startswith("REQ-")}
    return out


def module_deps(p: A.Project, ids: List[str]) -> Dict[str, Set[str]]:
    """module → modules it depends on (must exist first), from whatever the design states."""
    deps: Dict[str, Set[str]] = {m: set() for m in ids}

    def add(mid: str, cell: str) -> None:
        if mid in deps:
            deps[mid] |= {x for x in re.findall(r"\bM\d+\b", cell) if x in deps and x != mid}

    design = p.path / "design"
    for f in (design / "MODULES.md", design / "TECHNICAL.md"):
        for t in md.read_tables(f):
            cm, cd = t.col("module"), t.col("depends")
            if cm is None or cd is None:
                continue
            for r in t.rows:
                own = re.findall(r"\bM\d+\b", r[cm] if cm < len(r) else "")
                if own and cd < len(r):
                    add(own[0], r[cd])
    for f in sorted((design / "technical").glob("m*.md")):
        m = re.match(r"m0*(\d+)-", f.name)
        if not m:
            continue
        for t in md.read_tables(f):
            for r in t.rows:
                if len(r) > 1 and r[0].strip("* ").lower().startswith("depends on"):
                    add("M" + m.group(1), r[1])
    # flowchart under a "Build order" heading: an arrow A --> B means A must exist before B
    text = A.doc_text(p, "design/TECHNICAL.md")
    for sec in re.split(r"^#{2,4} ", text, flags=re.M):
        if not re.match(r"[\d. ]*build order", sec, flags=re.I):
            continue
        for blk in re.findall(r"```mermaid\s*\n(.*?)```", sec, flags=re.S):
            node: Dict[str, str] = {}
            for nid, label in re.findall(r"\b(\w+)\s*[\[({]+\"?([^\"\])}\n]*)", blk):
                mm = re.findall(r"\bM\d+\b", label)
                if mm:
                    node[nid] = mm[0]
            bare = re.sub(r"[\[({]+\"?[^\"\])}\n]*\"?[\])}]+", "", blk)
            bare = re.sub(r"\|[^|\n]*\|", "", bare)
            for line in bare.splitlines():
                chain = [x.strip() for x in re.split(r"\s*[-=.]{2,}>\s*", line.strip()) if x.strip()]
                for a, b in zip(chain, chain[1:]):
                    ma = node.get(a) or (a.upper() if re.fullmatch(r"[Mm]\d+", a) else "")
                    mb = node.get(b) or (b.upper() if re.fullmatch(r"[Mm]\d+", b) else "")
                    if ma and mb:
                        add(mb, ma)
    return deps


def topo(ids: List[str], deps: Dict[str, Set[str]]) -> Tuple[List[str], List[str]]:
    """Dependencies first, ties by module number. Returns (order, modules caught in a cycle)."""
    left, order = sorted(ids, key=num), []
    while left:
        ready = [m for m in left if not (deps.get(m, set()) & set(left))]
        if not ready:
            return order + left, left
        order.append(ready[0])
        left.remove(ready[0])
    return order, []


def split(ids: List[str], level: str) -> List[List[str]]:
    n = len(ids)
    if level == "Light":
        k = 1 if n <= LIGHT_SPLIT_ABOVE else 2
    else:
        k = int(math.ceil(n / float(PER_PACKAGE.get(level, PER_PACKAGE["Standard"]))))
    base, extra = divmod(n, k)          # balanced: 7 REQs in 3 packages → 3, 2, 2
    out, i = [], 0
    for j in range(k):
        step = base + (1 if j < extra else 0)
        out.append(ids[i:i + step])
        i += step
    return [x for x in out if x]


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args else 2)
    root = Path(args[0]).expanduser().resolve()
    out_path = args[args.index("--out") + 1] if "--out" in args and args.index("--out") + 1 < len(args) else None
    if root.name in ("plan", "design") and not (root / "atlas.json").exists():
        root = root.parent
    p = A.Project(root, {"mode": "folder"})

    reqs = flow.req_rows(p)
    if not reqs:
        A.die("no REQ rows in %s — the design comes first (/stark)." % (root / "design" / "_work" / "requirements.md"))
    mods = A.read_modules(p)
    if not mods:
        A.die("design/MODULES.md has no modules — the design comes first (/stark).")
    mod_by = {m["id"]: m for m in mods}
    n_ac: Dict[str, int] = {}
    for ac in flow.ac_rows(p).values():
        for r in ac["reqs"]:
            n_ac[r] = n_ac.get(r, 0) + 1
    _, wps = A.read_plan(p)
    planned = {r for w in wps for r in w["reqs"]}
    built = built_reqs(p)

    live = {k: v for k, v in reqs.items() if not any(x in v["status"].lower() for x in DEAD)}
    todo = {k: v for k, v in live.items() if k not in planned and k not in built}
    groups: Dict[str, List[str]] = {}
    for rid in sorted(todo, key=num):
        groups.setdefault(first_module(todo[rid]["module"]), []).append(rid)

    deps = module_deps(p, [m["id"] for m in mods])
    order, cyc = topo([m["id"] for m in mods], deps)
    seq = [m for m in order if m in groups] + [g for g in ("X", "?") if g in groups] + \
        sorted(g for g in groups if g not in mod_by and g not in ("X", "?"))

    last_wp: Dict[str, str] = {}         # module → last work package that touches it (existing plan, then this seed)
    for w in sorted(wps, key=lambda x: num(x["id"])):
        for m in w["modules"]:
            last_wp[m] = w["id"]
    nxt = max([num(w["id"]) for w in wps] + [0]) + 1
    rows, n_pk = [], 0
    for g in seq:
        mo = mod_by.get(g)
        level = mo["rigour"] if mo else "Standard"
        name = ("%s %s" % (g, mo["name"])) if mo else ("cross-cutting" if g == "X" else "module not assigned")
        parts = split(groups[g], level)
        first_dep = sorted({last_wp[d] for d in deps.get(g, set()) if d in last_wp}, key=num)
        for i, ids in enumerate(parts, 1):
            wid = "WP-%02d" % nxt
            nxt += 1
            n_pk += 1
            part = (", part %d of %d" % (i, len(parts))) if len(parts) > 1 else ""
            title = "{{name it: %s%s}}" % (name.replace("|", "/"), part)
            if level == "Critical":
                title += " + review"
                size = "S"
            else:
                size = "M" if len(ids) > 2 else "S"
            dep = [last_wp[g]] if g in last_wp else first_dep
            rows.append("| %s | %s | {{P#}} | %s | %s | %s | %s | todo |" % (
                wid, title, g if g != "?" else "{{M#}}", compact(ids), ", ".join(dep) or "—", size))
            last_wp[g] = wid

    L = ["<!-- plan_seed %s: %d live REQ(s) to plan → %d proposed work package(s). A proposal: merge, order, name "
         "and phase the rows; verify.py fails while a {{placeholder}} remains. -->" % (A.today(), len(todo), n_pk),
         "Module order (dependencies first): " + " → ".join(
             "%s %s (%s%s)" % (m, mod_by[m]["name"], mod_by[m]["rigour"], "" if mod_by[m]["confirmed"] else ", unconfirmed")
             for m in order) + ("" if any(deps.values()) else "   — the design states no dependencies; order is by module number"),
         ""]
    if rows:
        L += ["| WP | Title | Phase | Module | REQs | Depends on | Size | Status |",
              "|---|---|---|---|---|---|---|---|"] + rows + [""]
    notes = []
    if planned or built:
        notes.append("Left out: %d REQ(s) already in a work package, %d listed as already built." % (
            len(set(live) & planned), len(set(live) & built - planned)))
    no_ac = sorted((r for r in todo if not n_ac.get(r)), key=num)
    if no_ac:
        notes.append("No acceptance criterion (a design gap — send back with `atlas note --to stark`): " + compact(no_ac))
    tc = sorted((r for r, v in todo.items() if "confirm" in v["status"].lower()), key=num)
    if tc:
        notes.append("Still `to confirm` (Status `blocked` for the package if the open question is blocking): " + compact(tc))
    if "X" in groups:
        notes.append("Module X is cross-cutting: fold its REQs into the walking skeleton and the packages they protect.")
    if "?" in groups:
        notes.append("REQs with no module in the register (Stark must assign them): " + compact(groups["?"]))
    if cyc:
        notes.append("Module dependencies form a cycle (%s) — ordered by number from there; check the design." % ", ".join(cyc))
    unconf = [m["id"] for m in mods if not m["confirmed"]]
    if unconf:
        notes.append("Rigour not confirmed for %s — the proposed level was used." % ", ".join(unconf))
    if not rows:
        notes.append("Nothing to plan: every live REQ is in a work package or listed as already built.")
    L += ["- " + n for n in notes]
    text = "\n".join(L).rstrip() + "\n"
    if out_path:
        out = Path(out_path).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print("%d work package(s) proposed for %d REQ(s) → %s" % (n_pk, len(todo), out))
        for n in notes:
            print("- " + n)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
