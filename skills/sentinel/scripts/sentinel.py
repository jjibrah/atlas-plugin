#!/usr/bin/env python3
"""sentinel.py: helpers for SENTINEL (test plan, UAT, go-live). Standard library only, Python 3.9+.

    sentinel.py next <P>                          next free TC id
    sentinel.py coverage <P> --phase P1           phase ACs/REQs with no TC; TCs not passed; depth hints
    sentinel.py check <P> [--phase P1]            TEST-PLAN table, IDs, Covers links, UAT wording, GO-LIVE
    sentinel.py set <P> TC-001=pass TC-002=fail   update Status cells in TEST-PLAN.md (todo|pass|fail)

<P> is the project storage folder (`atlasctl where`). Exit code 1 when check/coverage find problems.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((SKILL / ".." / ".." / "lib").resolve()))
import atlasctl as A  # noqa: E402
import mdtables as md  # noqa: E402

HEADERS = ["TC", "Covers", "Module", "Level", "Type", "Steps / expectation", "Status"]
LEVELS = ["Light", "Standard", "Critical"]
TYPES = ["unit", "integration", "e2e", "manual", "security", "performance"]
STATUSES = ["todo", "pass", "fail"]
INTERNAL_ID = re.compile(r"\b(?:REQ|AC|WP|TC|FR|BR|CR|OQ|AD|PP|WF)-\d+\b|\bM\d{1,2}\b|\bP\d\b|\bG[1-5]\b")
# What each rigour level expects at minimum among the TC types of a module (rigour.md)
DEPTH = {"Light": [("manual", "e2e")],
         "Standard": [("unit",), ("integration", "e2e")],
         "Critical": [("unit",), ("integration",), ("e2e",), ("security",)]}


def project(path: str) -> A.Project:
    p = Path(path).expanduser().resolve()
    if not (p / "atlas.json").exists():
        sys.exit("sentinel: %s is not an ATLAS project folder (no atlas.json). Use `atlasctl where`." % p)
    return A.Project(p, {"mode": "folder"})


# ───────── readers ─────────

def tc_rows(p: A.Project) -> List[Tuple[int, md.Table, List[str]]]:
    """(table index, table, row) for every row of every TC table in TEST-PLAN.md."""
    out = []
    for i, t in enumerate(md.read_tables(p.path / "test" / "TEST-PLAN.md")):
        if t.col("tc") is None or t.col("covers") is None:
            continue
        for r in t.rows:
            out.append((i, t, r))
    return out


def cell(t: md.Table, r: List[str], name: str) -> str:
    c = t.col(name)
    return r[c].strip() if c is not None and c < len(r) else ""


def design_ids(p: A.Project) -> Set[str]:
    """Every ID written anywhere in design/ (incl. _work/requirements.md) — what Covers may cite."""
    out: Set[str] = set()
    for f in sorted((p.path / "design").rglob("*.md")):
        if "sources" in f.parts:
            continue
        out |= set(md.expand_ranges(md.strip_noise(f.read_text(encoding="utf-8", errors="replace"))))
    return {x for x in out if x.startswith(("REQ-", "AC-"))}


def phase_targets(p: A.Project, phase: str) -> Tuple[Set[str], Set[str], Dict[str, Set[str]]]:
    """(phase REQs, phase ACs, REQ → its ACs) — same rule as gates.py G5."""
    _, wps = A.read_plan(p)
    reqs = {r for w in wps if w["phase"] == phase for r in w["reqs"] if r.startswith("REQ-")}
    links, _ = A.id_graph(p)
    by_req: Dict[str, Set[str]] = {r: set() for r in reqs}
    for a, ls in links.items():
        if a.startswith("AC-"):
            for r in ls & reqs:
                by_req[r].add(a)
    for r in reqs:
        by_req[r] |= {x for x in links.get(r, set()) if x.startswith("AC-")}
    acs = set().union(*by_req.values()) if by_req else set()
    return reqs, acs, by_req


def sort_ids(ids) -> List[str]:
    return sorted(ids, key=lambda i: (re.sub(r"\d", "", i), int(re.sub(r"\D", "", i) or 0)))


# ───────── commands ─────────

def cmd_next(a: argparse.Namespace) -> int:
    p = project(a.project)
    nums = [int(m) for _, t, r in tc_rows(p) for m in re.findall(r"^\**TC-(\d+)", cell(t, r, "tc"))]
    print("TC-%03d" % (max(nums) + 1 if nums else 1))
    return 0


def cmd_coverage(a: argparse.Namespace) -> int:
    p = project(a.project)
    reqs, acs, by_req = phase_targets(p, a.phase)
    if not reqs:
        print("No work packages / REQs found for %s in plan/PLAN.md." % a.phase)
        return 1
    rows = tc_rows(p)
    covered: Dict[str, List[str]] = {}
    tc_info = {}
    for _, t, r in rows:
        tc = cell(t, r, "tc").strip("* ")
        cov = set(md.expand_ranges(cell(t, r, "covers")))
        tc_info[tc] = (cov, cell(t, r, "status").lower(), cell(t, r, "module"), cell(t, r, "type").lower())
        for x in cov:
            covered.setdefault(x, []).append(tc)
    problems = 0
    no_ac = sort_ids(r for r in reqs if not by_req.get(r))
    targets = acs | set(no_ac)
    missing = sort_ids(x for x in targets if x not in covered)
    print("Phase %s: %d REQ(s), %d AC(s); %d TC(s) in TEST-PLAN.md" % (a.phase, len(reqs), len(acs), len(rows)))
    if no_ac:
        print("\nREQs with no acceptance criterion (ask the user / run /stark; covered directly meanwhile):")
        print("  " + ", ".join(no_ac))
    if missing:
        problems += len(missing)
        print("\nNot covered by any TC (%d):" % len(missing))
        for x in missing:
            parent = next((r for r, s in by_req.items() if x in s), "")
            print("  %s%s" % (x, (" (" + parent + ")") if parent else ""))
    phase_tcs = sort_ids(tc for tc, (cov, *_rest) in tc_info.items() if cov & (targets | reqs))
    open_ = [(tc, tc_info[tc][1] or "todo") for tc in phase_tcs if tc_info[tc][1] not in ("pass", "passed", "✅")]
    if open_:
        problems += len(open_)
        print("\nTCs not passed (%d):" % len(open_))
        for tc, st in open_:
            print("  %s  %s" % (tc, st))
    # depth hints by rigour (warnings only)
    mods = {m["id"]: m["rigour"] for m in A.read_modules(p)}
    _, wps = A.read_plan(p)
    phase_mods = sorted({m for w in wps if w["phase"] == a.phase for m in w["modules"]})
    hints = []
    for m in phase_mods:
        types = {tc_info[tc][3] for tc in phase_tcs if tc_info[tc][2].strip("* ") == m}
        lvl = mods.get(m, A.default_level(p))
        need = [" or ".join(alts) for alts in DEPTH.get(lvl, []) if not types & set(alts)]
        if need:
            hints.append("%s (%s) has no %s test" % (m, lvl, ", no ".join(need)))
    if hints:
        print("\nDepth hints (rigour.md):")
        for h in hints:
            print("  - " + h)
    if not problems:
        print("\nEvery acceptance criterion in %s is covered and every test has passed." % a.phase)
    return 1 if problems else 0


def check_test_plan(p: A.Project, errors: List[str], warns: List[str]) -> None:
    f = p.path / "test" / "TEST-PLAN.md"
    if not f.exists():
        errors.append("test/TEST-PLAN.md missing")
        return
    tables = [t for t in md.read_tables(f) if t.col("tc") is not None]
    if not tables:
        errors.append("TEST-PLAN.md: no TC table found")
        return
    known = design_ids(p)
    mods = {m["id"]: m["rigour"] for m in A.read_modules(p)}
    seen: Dict[str, int] = {}
    for t in tables:
        hdr = [h.strip("* ") for h in t.headers]
        if hdr != HEADERS:
            errors.append("TEST-PLAN.md line %d: header must be | %s | (found | %s |)"
                          % (t.line, " | ".join(HEADERS), " | ".join(hdr)))
            continue
        for k, r in enumerate(t.rows):
            ln = t.line + 2 + k
            if len(r) != len(HEADERS):
                errors.append("line %d: %d cells, expected %d" % (ln, len(r), len(HEADERS)))
                continue
            tc, cov, mod, lvl, typ, steps, st = [c.strip() for c in r]
            tc = tc.strip("* ")
            if not re.match(r"^TC-\d{3,}$", tc):
                errors.append("line %d: bad TC id %r (use `sentinel.py next`)" % (ln, tc))
            elif tc in seen:
                errors.append("line %d: %s duplicates line %d" % (ln, tc, seen[tc]))
            else:
                seen[tc] = ln
            ids = md.expand_ranges(cov)
            if not any(i.startswith(("AC-", "REQ-")) for i in ids):
                errors.append("line %d: %s Covers has no AC/REQ id" % (ln, tc))
            unknown = [i for i in ids if i.startswith(("AC-", "REQ-")) and i not in known]
            if unknown:
                errors.append("line %d: %s covers id(s) not found in design/: %s" % (ln, tc, ", ".join(unknown)))
            m = mod.strip("* ")
            if mods and m not in mods:
                errors.append("line %d: %s module %r is not in design/MODULES.md" % (ln, tc, m))
            if lvl not in LEVELS:
                errors.append("line %d: %s Level %r must be one of %s" % (ln, tc, lvl, "/".join(LEVELS)))
            elif m in mods and lvl != mods[m]:
                warns.append("line %d: %s Level %s differs from %s rigour %s" % (ln, tc, lvl, m, mods[m]))
            if typ.lower() not in TYPES:
                errors.append("line %d: %s Type %r must be one of %s" % (ln, tc, typ, "/".join(TYPES)))
            if st.lower() not in STATUSES:
                errors.append("line %d: %s Status %r must be todo/pass/fail" % (ln, tc, st))
            if not steps or "{{" in steps:
                errors.append("line %d: %s has no steps / expectation" % (ln, tc))
    if "{{" in md.strip_noise(f.read_text(encoding="utf-8")):
        errors.append("TEST-PLAN.md still has {{placeholders}}")


def check_uat(p: A.Project, errors: List[str]) -> None:
    f = p.path / "test" / "UAT.md"
    if not f.exists():
        errors.append("test/UAT.md missing")
        return
    text = re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8"), flags=re.S)
    for n, ln in enumerate(text.splitlines(), 1):
        hits = sorted(set(INTERNAL_ID.findall(ln)))
        if hits:
            errors.append("UAT.md line %d: internal id(s) %s — the client must not see these" % (n, ", ".join(hits)))
        if "{{" in ln:
            errors.append("UAT.md line %d: unfilled {{placeholder}}" % n)
    if not re.search(r"(?i)sign[- ]?off", text) or not re.search(r"(?i)signature", text):
        errors.append("UAT.md: sign-off block (name, role, date, signature) missing")


def phase_has_critical(p: A.Project, phase: Optional[str]) -> bool:
    crit = {m["id"] for m in A.read_modules(p) if m["rigour"] == "Critical"}
    if not phase:
        return bool(crit)
    _, wps = A.read_plan(p)
    return bool(crit & {m for w in wps if w["phase"] == phase for m in w["modules"]})


def check_golive(p: A.Project, phase: Optional[str], errors: List[str], warns: List[str]) -> None:
    f = p.path / "test" / "GO-LIVE.md"
    if not f.exists():
        errors.append("test/GO-LIVE.md missing")
        return
    raw = f.read_text(encoding="utf-8")
    text = md.strip_noise(raw)
    if "{{" in text:
        errors.append("GO-LIVE.md still has {{placeholders}}")
    if not re.search(r"^\s*[-*] \[[ xX]\]", text, flags=re.M):
        errors.append("GO-LIVE.md has no checklist items (- [ ] …)")
    if phase_has_critical(p, phase) and not re.search(r"(?im)^#{1,4} .*rollback", text):
        errors.append("GO-LIVE.md needs a 'Rollback' section (a Critical module is in %s)" % (phase or "the project"))
    try:
        import gates as G  # noqa: E402
        for rx, what in G.SECRET_PATTERNS:
            if rx.search(raw):
                errors.append("GO-LIVE.md seems to contain a %s — secrets live in the hosting provider, never in files"
                              % what)
    except ImportError:
        pass
    left = len(re.findall(r"^\s*[-*] \[ \]", text, flags=re.M))
    if left:
        warns.append("GO-LIVE.md: %d item(s) still unchecked (G5 needs all ticked)" % left)


def cmd_check(a: argparse.Namespace) -> int:
    p = project(a.project)
    errors: List[str] = []
    warns: List[str] = []
    check_test_plan(p, errors, warns)
    check_uat(p, errors)
    check_golive(p, a.phase, errors, warns)
    for w in warns:
        print("warn: " + w)
    for e in errors:
        print("FAIL: " + e)
    print("check: %s (%d error(s), %d warning(s))" % ("OK" if not errors else "FAILED", len(errors), len(warns)))
    return 1 if errors else 0


def cmd_set(a: argparse.Namespace) -> int:
    p = project(a.project)
    f = p.path / "test" / "TEST-PLAN.md"
    want: Dict[str, str] = {}
    for x in a.results:
        if "=" not in x:
            sys.exit("use TC-001=pass|fail|todo")
        k, v = x.split("=", 1)
        v = v.strip().lower()
        if v not in STATUSES:
            sys.exit("status must be todo/pass/fail: %s" % x)
        want[k.strip().upper()] = v
    lines = f.read_text(encoding="utf-8").split("\n")
    done = set()
    for i, ln in enumerate(lines):
        m = re.match(r"^\|\s*\**(TC-\d+)\**\s*\|", ln)
        if m and m.group(1) in want:
            cells = md.split_row(ln)
            if len(cells) != len(HEADERS):
                continue
            cells[-1] = want[m.group(1)]
            lines[i] = "| " + " | ".join(cells) + " |"
            done.add(m.group(1))
    f.write_text("\n".join(lines), encoding="utf-8")
    for k in sorted(want):
        print("%s → %s" % (k, want[k]) if k in done else "%s not found" % k)
    return 0 if done == set(want) else 1


def main() -> None:
    ap = argparse.ArgumentParser(prog="sentinel.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("next"); x.add_argument("project"); x.set_defaults(fn=cmd_next)
    x = sub.add_parser("coverage"); x.add_argument("project"); x.add_argument("--phase", required=True)
    x.set_defaults(fn=cmd_coverage)
    x = sub.add_parser("check"); x.add_argument("project"); x.add_argument("--phase"); x.set_defaults(fn=cmd_check)
    x = sub.add_parser("set"); x.add_argument("project"); x.add_argument("results", nargs="+")
    x.set_defaults(fn=cmd_set)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
