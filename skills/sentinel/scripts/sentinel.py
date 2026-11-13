#!/usr/bin/env python3
"""sentinel.py: helpers for SENTINEL (test plan, UAT, go-live). Standard library only, Python 3.9+.

    sentinel.py seed <P> --phase P1               add the phase section: one row per acceptance criterion not covered
    sentinel.py next <P>                          next free TC id (never one that was issued before)
    sentinel.py results <P> <junit.xml> [more …]  set TC status from JUnit-style XML (TC id in the test name)
    sentinel.py set <P> TC-001=pass TC-002=fail   set TC status by hand (todo|pass|fail)
    sentinel.py coverage <P> --phase P1           criteria with no TC; TCs not passed; depth hints
    sentinel.py check <P> [--phase P1]            TEST-PLAN table, IDs, Covers links, UAT wording, GO-LIVE

<P> is the project storage folder (`P` in the `atlas begin` brief). `atlas finish sentinel` runs `check`.
Exit code 1 when check/coverage find problems.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((SKILL / ".." / ".." / "lib").resolve()))
import atlasctl as A  # noqa: E402
import flow as F  # noqa: E402
import mdtables as md  # noqa: E402

HEADERS = ["TC", "Covers", "Module", "Level", "Type", "Steps / expectation", "Status"]
LEVELS = ["Light", "Standard", "Critical"]
TYPES = ["unit", "integration", "e2e", "manual", "security", "performance"]
STATUSES = ["todo", "pass", "fail"]
PASSED = ("pass", "passed", "✅")
INTERNAL_ID = re.compile(r"\b(?:REQ|AC|WP|TC|FR|BR|CR|OQ|AD|PP|WF)-\d+\b|\bM\d{1,2}\b|\bP\d\b|\bG[1-5]\b")
# The type `seed` gives the row of each criterion, by the module's rigour
SEED_TYPE = {"Light": "manual", "Standard": "integration", "Critical": "integration"}
# Extra rows `seed` adds per criterion of a Critical module: (label, type, what to think about)
CRITICAL_ROWS = [
    ("edge case", "integration", "boundary values, empty or missing input, the maximum, the same action twice or at once"),
    ("failure", "integration", "the step fails halfway or the outside service is down: what the user sees, what state is "
                               "left, how it is undone"),
    ("permission", "security", "not logged in, wrong role, someone else's data"),
]
# What each rigour level expects at least among the TC types of a module (warnings only)
DEPTH = {"Light": [("manual", "e2e")],
         "Standard": [("integration", "e2e", "unit")],
         "Critical": [("integration",), ("security",), ("e2e",)]}
SEEDED = re.compile(r"^(From AC:|From REQ\b|TODO steps)", re.I)     # a Steps cell nobody has written yet
RETIRED = re.compile(r"^Retired\b", re.I)
VERSION_ROW = re.compile(r"(\|\s*\**Version\**\s*\|\s*\**\s*)v(\d+)(?:\.(\d+))?[^|\n]*")
LAST_ROW = re.compile(r"(\|\s*Last TC issued\s*\|\s*)TC-(\d+)([^|\n]*)")
# TC-012 · TC_012 · tc012 · testTC012 (not "etc012")
TC_IN_NAME = re.compile(r"(?:(?<![A-Za-z])[Tt][Cc]|(?<=[a-z])TC)[-_ ]?(\d{1,6})(?!\d)")


def project(path: str) -> A.Project:
    p = Path(path).expanduser().resolve()
    if not (p / "atlas.json").exists():
        sys.exit("sentinel: %s is not an ATLAS project folder (no atlas.json). Use the `P` path from `atlas begin`." % p)
    return A.Project(p, {"mode": "folder"})


# ───────── readers ─────────

def plan_file(p: A.Project) -> Path:
    return p.path / "test" / "TEST-PLAN.md"


def tc_rows(p: A.Project) -> List[Tuple[int, md.Table, List[str]]]:
    """(table index, table, row) for every row of every TC table in TEST-PLAN.md."""
    out = []
    for i, t in enumerate(md.read_tables(plan_file(p))):
        if t.col("tc") is None or t.col("covers") is None:
            continue
        for r in t.rows:
            out.append((i, t, r))
    return out


def cell(t: md.Table, r: List[str], name: str) -> str:
    c = t.col(name)
    return r[c].strip() if c is not None and c < len(r) else ""


def tc_ids(p: A.Project) -> Dict[int, str]:
    """number → TC id as written in the plan (TC-012 → {12: 'TC-012'})."""
    out: Dict[int, str] = {}
    for _, t, r in tc_rows(p):
        m = re.match(r"^\**(TC-(\d+))", cell(t, r, "tc"))
        if m:
            out[int(m.group(2))] = m.group(1)
    return out


def last_issued(p: A.Project) -> int:
    """Highest TC number ever issued: the rows, and the 'Last TC issued' row that survives a deleted row."""
    nums = list(tc_ids(p))
    m = LAST_ROW.search(A.doc_text(p, "test/TEST-PLAN.md")[:3000])
    if m:
        nums.append(int(m.group(2)))
    return max(nums) if nums else 0


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


def sort_ids(ids: Iterable[str]) -> List[str]:
    return sorted(ids, key=lambda i: (re.sub(r"\d", "", i), int(re.sub(r"\D", "", i) or 0)))


def span(ids: List[str]) -> str:
    return ids[0] if len(ids) == 1 else "%s…%s" % (ids[0], ids[-1])


# ───────── next ─────────

def cmd_next(a: argparse.Namespace) -> int:
    print("TC-%03d" % (last_issued(project(a.project)) + 1))
    return 0


# ───────── seed ─────────

def new_plan_text(p: A.Project) -> str:
    text = (SKILL / "templates" / "TEST-PLAN.md").read_text(encoding="utf-8")
    for k, v in (("{{Project name}}", p.meta.get("name", "")), ("{{PRJ-id}}", p.meta.get("id", "")),
                 ("{{YYYY-MM-DD}}", A.today())):
        text = text.replace(k, v)
    return text


def stamp_header(text: str, last: int, bump: bool) -> Tuple[str, str]:
    """Keep the header table current: Version (bumped when rows were added to an existing plan) and
    'Last TC issued' (so a TC id is never reused, even if a row is deleted). Returns (text, version)."""
    head, tail = text[:3000], text[3000:]
    m = VERSION_ROW.search(head)
    if not m:                                   # an older plan without a header table: add one under the title
        table = "| Field | Value |\n|---|---|\n| Version | v1.0 — %s |\n| Last TC issued | TC-%03d |" % (A.today(), last)
        t = re.search(r"^# .*$", head, flags=re.M)
        head = (head[: t.end()] + "\n\n" + table + head[t.end():]) if t else (table + "\n\n" + head)
        return head + tail, "v1.0"
    major, minor = int(m.group(2)), int(m.group(3) or 0)
    if bump:
        minor += 1
        head = head[: m.start()] + "%sv%d.%d — %s " % (m.group(1), major, minor, A.today()) + head[m.end():]
    version = "v%d.%d" % (major, minor)
    if LAST_ROW.search(head):
        head = LAST_ROW.sub(lambda x: "%sTC-%03d%s" % (x.group(1), last, x.group(3)), head, count=1)
    else:
        m = VERSION_ROW.search(head)
        eol = head.find("\n", m.end())
        eol = len(head) if eol < 0 else eol
        head = head[:eol] + "\n| Last TC issued | TC-%03d |" % last + head[eol:]
    return head + tail, version


def insert_rows(text: str, phase: str, title: str, goal: str, rows: List[str]) -> str:
    """Append rows to the phase's TC table, creating the `## P# — <name>` section (and its table) when missing."""
    table = ["| " + " | ".join(HEADERS) + " |", "|" + "---|" * len(HEADERS)]
    lines = text.rstrip("\n").split("\n")
    start = next((i for i, ln in enumerate(lines) if re.match(r"^##+\s+%s\b" % re.escape(phase), ln)), None)
    if start is None:
        sec = ["", "## " + title, ""]
        if goal:
            sec += ["Phase goal: " + goal, ""]
        sec += table + rows + ["", "### Notes for " + phase, "- Test data and accounts needed: none recorded",
                               "- Waiting for an answer: none"]
        return "\n".join(lines + sec) + "\n"
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^#{1,%d}\s" % level, lines[i])), len(lines))
    hdr = next((i for i in range(start + 1, end - 1) if lines[i].lstrip().startswith("|")
                and md.split_row(lines[i])[0].strip("* ").upper() == "TC" and md.is_sep(lines[i + 1])), None)
    if hdr is None:                             # the section has no table yet: put it before its first sub-heading
        at = next((i for i in range(start + 1, end) if lines[i].startswith("#")), end)
        while at > start + 1 and not lines[at - 1].strip():
            at -= 1
        block = [""] + table + rows + ([""] if at < len(lines) and lines[at].strip() else [])
    else:
        at = hdr + 2
        while at < end and lines[at].lstrip().startswith("|"):
            at += 1
        block = rows
    return "\n".join(lines[:at] + block + lines[at:]) + "\n"


def cmd_seed(a: argparse.Namespace) -> int:
    p = project(a.project)
    phases, wps = A.read_plan(p)
    ws = [w for w in wps if w["phase"] == a.phase]
    if not ws:
        print("No work packages for %s in plan/PLAN.md — nothing to seed." % a.phase)
        return 1
    ph = next((x for x in phases if x["id"] == a.phase), {"id": a.phase, "name": "", "goal": ""})
    reqs, _, by_req = phase_targets(p, a.phase)
    if not reqs:
        print("The work packages of %s cite no REQ in plan/PLAN.md — nothing to seed. Leave a note for jarvis." % a.phase)
        return 1
    register, criteria = F.req_rows(p), F.ac_rows(p)
    mods = {m["id"]: m for m in A.read_modules(p)}
    covered: Set[str] = set()
    for _, t, r in tc_rows(p):
        covered |= set(md.expand_ranges(cell(t, r, "covers")))

    def module_of(req: str) -> str:
        in_phase = [m for w in ws if req in w["reqs"] for m in w["modules"]]
        named = re.findall(r"\bM\d+\b", register.get(req, {}).get("module", ""))
        for m in [x for x in named if x in in_phase] + named + in_phase:
            if not mods or m in mods:
                return m
        return "?"

    n = last_issued(p)
    rows: List[str] = []
    made: Dict[str, List[str]] = {}             # module → TC ids
    seeded: Set[str] = set()
    no_ac, no_module = [], []

    def add(covers: str, mod: str, level: str, typ: str, steps: str) -> None:
        nonlocal n
        n += 1
        tc = "TC-%03d" % n
        rows.append("| %s | %s | %s | %s | %s | %s | todo |" % (tc, covers, mod, level, typ, steps.replace("\n", " ")))
        made.setdefault(mod, []).append(tc)

    placed = {req: module_of(req) for req in reqs}
    levels = {req: (mods[m]["rigour"] if m in mods else A.default_level(p)) for req, m in placed.items()}
    # strictest module first, so a criterion shared by two requirements gets the deeper treatment
    for req in sorted(sort_ids(reqs), key=lambda r: -LEVELS.index(levels[r])):
        mod, level = placed[req], levels[req]
        if mod == "?":
            no_module.append(req)
        acs = sort_ids(by_req.get(req, ()))
        if not acs:
            no_ac.append(req)
            if req not in covered:
                add(req, mod, level, SEED_TYPE[level], "From REQ (it has no acceptance criterion — confirm the expected "
                    "result with the user): " + register.get(req, {}).get("text", ""))
            continue
        new = [x for x in acs if x not in covered and x not in seeded]
        for ac in new:
            own = [r for r in criteria.get(ac, {}).get("reqs", []) if r in reqs] or [req]
            cov = ", ".join([ac] + sort_ids(set(own) | {req}))
            text = criteria.get(ac, {}).get("text") or "(criterion text not found in design/ — read its module section)"
            add(cov, mod, level, SEED_TYPE[level], "From AC: " + text)
            if level == "Critical":
                for label, typ, hint in CRITICAL_ROWS:
                    add(cov, mod, level, typ, "TODO steps — %s for %s: %s" % (label, ac, hint))
            seeded.add(ac)
        if level == "Critical" and new:
            add(", ".join(new + [req]), mod, level, "e2e",
                "TODO steps — end to end for %s: the whole path as its user walks it" % req)
    f = plan_file(p)
    existed = f.exists()
    if not rows and existed and re.search(r"^##+\s+%s\b" % re.escape(a.phase), f.read_text(encoding="utf-8"), flags=re.M):
        if not F.doc_version(p, "test/TEST-PLAN.md"):           # a plan from before the header table existed
            f.write_text(stamp_header(f.read_text(encoding="utf-8"), n, bump=False)[0], encoding="utf-8")
            print("Added the header table (Version, Last TC issued) to test/TEST-PLAN.md.")
        print("%s: every acceptance criterion already has a test row — nothing added." % a.phase)
        return 0
    text = f.read_text(encoding="utf-8") if existed else new_plan_text(p)
    title = "%s — %s" % (ph["id"], ph["name"]) if ph["name"] else ph["id"]
    text = insert_rows(text, a.phase, title, ph["goal"], rows)
    text, version = stamp_header(text, n, bump=existed and bool(rows))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    print("Seeded %s: %d row(s) for %d criteria in test/TEST-PLAN.md (%s)." % (title, len(rows), len(seeded), version))
    for mod in sorted(made):
        m = mods.get(mod)
        print("  %s%s: %s" % (mod, (" %s (%s)" % (m["name"], m["rigour"])) if m else "", span(made[mod])))
    if no_ac:
        print("REQs with no acceptance criterion (don't invent one — ask the user or leave a note for stark): "
              + ", ".join(no_ac))
    if no_module:
        print("No module found for %s — set the Module cell by hand." % ", ".join(no_module))
    if rows:
        print("Now write each Steps cell (setup → action → exact expected result). `check` fails while a cell still "
              "starts with \"From AC:\" or \"TODO steps\".")
    return 0


# ───────── coverage ─────────

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
        print("\nREQs with no acceptance criterion (ask the user or leave a note for stark; covered directly meanwhile):")
        print("  " + ", ".join(no_ac))
    if missing:
        problems += len(missing)
        print("\nNot covered by any TC (%d) — `sentinel.py seed` adds the rows:" % len(missing))
        for x in missing:
            parent = next((r for r, s in by_req.items() if x in s), "")
            print("  %s%s" % (x, (" (" + parent + ")") if parent else ""))
    phase_tcs = sort_ids(tc for tc, (cov, *_rest) in tc_info.items() if cov & (targets | reqs))
    open_ = [(tc, tc_info[tc][1] or "todo") for tc in phase_tcs if tc_info[tc][1] not in PASSED]
    if open_:
        problems += len(open_)
        print("\nTCs not passed (%d):" % len(open_))
        for tc, st in open_:
            print("  %s  %s  (%s)" % (tc, st, tc_info[tc][3]))
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
        print("\nDepth hints:")
        for h in hints:
            print("  - " + h)
    if not problems:
        print("\nEvery acceptance criterion in %s is covered and every test has passed." % a.phase)
    return 1 if problems else 0


# ───────── check ─────────

def check_test_plan(p: A.Project, phase: Optional[str], errors: List[str], warns: List[str]) -> None:
    f = plan_file(p)
    if not f.exists():
        errors.append("test/TEST-PLAN.md missing — run `sentinel.py seed <P> --phase %s`" % (phase or "P#"))
        return
    raw = f.read_text(encoding="utf-8")
    if not F.doc_version(p, "test/TEST-PLAN.md"):
        errors.append("TEST-PLAN.md: header table needs a `| Version | v1.0 — YYYY-MM-DD |` row")
    if phase and not re.search(r"^##+\s+%s\b" % re.escape(phase), raw, flags=re.M):
        errors.append("TEST-PLAN.md has no `## %s — <phase name>` section — run `sentinel.py seed <P> --phase %s`"
                      % (phase, phase))
    tables = [t for t in md.read_tables(f) if t.col("tc") is not None]
    if not tables:
        errors.append("TEST-PLAN.md: no TC table found")
        return
    known = design_ids(p)
    mods = {m["id"]: m["rigour"] for m in A.read_modules(p)}
    seen: Dict[str, int] = {}
    unwritten: List[str] = []
    for t in tables:
        hdr = [h.strip("* ") for h in t.headers]
        if hdr != HEADERS:
            errors.append("TEST-PLAN.md line %d: header must be | %s | (found | %s |)"
                          % (t.line, " | ".join(HEADERS), " | ".join(hdr)))
            continue
        for k, r in enumerate(t.rows):
            ln = t.line + 2 + k
            if len(r) != len(HEADERS):
                errors.append("line %d: %d cells, expected %d (escape a | inside a cell as \\|)" % (ln, len(r), len(HEADERS)))
                continue
            tc, cov, mod, lvl, typ, steps, st = [c.strip() for c in r]
            tc = tc.strip("* ")
            if not re.match(r"^TC-\d{3,}$", tc):
                errors.append("line %d: bad TC id %r (use `sentinel.py next`)" % (ln, tc))
            elif tc in seen:
                errors.append("line %d: %s duplicates line %d" % (ln, tc, seen[tc]))
            else:
                seen[tc] = ln
            retired = bool(RETIRED.match(steps))
            ids = md.expand_ranges(cov)
            if not retired and not any(i.startswith(("AC-", "REQ-")) for i in ids):
                errors.append("line %d: %s Covers has no AC/REQ id" % (ln, tc))
            unknown = [i for i in ids if i.startswith(("AC-", "REQ-")) and i not in known]
            if unknown:
                errors.append("line %d: %s covers id(s) not found in design/: %s" % (ln, tc, ", ".join(unknown)))
            if retired and ids:
                warns.append("line %d: %s is retired but still counts for %s — set its Covers to —" % (ln, tc, cov))
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
            elif SEEDED.match(steps):
                unwritten.append(tc)
            elif re.match(r"(?i)^blocked\b", steps):
                warns.append("line %d: %s is blocked on a question" % (ln, tc))
    if unwritten:
        errors.append("TEST-PLAN.md: Steps not written yet (still the seeded text) for %d row(s): %s — write setup → "
                      "action → expected result, or `Blocked: <question>`" % (len(unwritten), ", ".join(unwritten)))
    if "{{" in md.strip_noise(raw):
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
    check_test_plan(p, a.phase, errors, warns)
    check_uat(p, errors)
    check_golive(p, a.phase, errors, warns)
    for w in warns:
        print("warn: " + w)
    for e in errors:
        print("FAIL: " + e)
    print("check: %s (%d error(s), %d warning(s))" % ("OK" if not errors else "FAILED", len(errors), len(warns)))
    return 1 if errors else 0


# ───────── results ─────────

def write_status(p: A.Project, want: Dict[str, str]) -> Set[str]:
    """Set the Status cell of the TCs named in `want` (TC id → todo|pass|fail). Returns the ids that were found."""
    f = plan_file(p)
    if not f.exists():
        sys.exit("sentinel: test/TEST-PLAN.md does not exist yet")
    lines = f.read_text(encoding="utf-8").split("\n")
    done: Set[str] = set()
    for i, ln in enumerate(lines):
        m = re.match(r"^\|\s*\**(TC-\d+)\**\s*\|", ln)
        if m and m.group(1) in want:
            cells = md.split_row(ln)
            if len(cells) != len(HEADERS):
                continue
            cells[-1] = want[m.group(1)]
            lines[i] = "| " + " | ".join(cells) + " |"
            done.add(m.group(1))
    if done:
        f.write_text("\n".join(lines), encoding="utf-8")
    return done


def cmd_set(a: argparse.Namespace) -> int:
    p = project(a.project)
    want: Dict[str, str] = {}
    for x in a.results:
        if "=" not in x:
            sys.exit("use TC-001=pass|fail|todo")
        k, v = x.split("=", 1)
        v = v.strip().lower()
        if v not in STATUSES:
            sys.exit("status must be todo/pass/fail: %s" % x)
        want[k.strip().upper()] = v
    done = write_status(p, want)
    for k in sort_ids(want):
        print("%s → %s" % (k, want[k]) if k in done else "%s not found" % k)
    return 0 if done == set(want) else 1


def junit_cases(path: Path) -> List[Dict[str, Any]]:
    """Every <testcase> in a JUnit-style file: name, outcome (pass|fail|skip) and the first line of a failure."""
    out = []
    for el in ET.parse(str(path)).getroot().iter():
        if el.tag.rsplit("}", 1)[-1] != "testcase":
            continue
        kids = {c.tag.rsplit("}", 1)[-1]: c for c in el}
        bad = kids.get("failure") if "failure" in kids else kids.get("error")
        if bad is not None:
            why = (bad.get("message") or (bad.text or "")).strip().splitlines()
            outcome, note = "fail", (why[0][:140] if why else "")
        elif "skipped" in kids or (el.get("status") or "").lower() in ("skipped", "notrun", "disabled"):
            outcome, note = "skip", ""
        else:
            outcome, note = "pass", ""
        out.append({"name": el.get("name") or "", "where": " ".join(x for x in (el.get("classname"), el.get("file")) if x),
                    "outcome": outcome, "note": note})
    return out


def cmd_results(a: argparse.Namespace) -> int:
    p = project(a.project)
    known = tc_ids(p)
    if not known:
        sys.exit("sentinel: no TC rows in test/TEST-PLAN.md yet — run `sentinel.py seed` first")
    cases: List[Dict[str, Any]] = []
    for f in a.files:
        try:
            cases += junit_cases(Path(f).expanduser())
        except (OSError, ET.ParseError) as e:
            sys.exit("sentinel: cannot read %s as JUnit XML: %s" % (f, e))
    seen: Dict[str, List[Dict[str, Any]]] = {}
    unknown: Dict[str, str] = {}
    named = 0
    for c in cases:
        nums = {int(n) for n in TC_IN_NAME.findall(c["name"] + " " + c["where"])}
        named += 1 if nums else 0
        for n in nums:
            if n in known:
                seen.setdefault(known[n], []).append(c)
            else:
                unknown.setdefault("TC-%03d" % n, c["name"])
    want: Dict[str, str] = {}
    untouched = []
    for tc, cs in seen.items():
        if any(c["outcome"] == "fail" for c in cs):
            want[tc] = "fail"
        elif any(c["outcome"] == "pass" for c in cs):
            want[tc] = "pass"
        else:
            untouched.append(tc)
    done = write_status(p, want) if want else set()
    print("Read %d test case(s) from %d file(s); %d carry a TC id." % (len(cases), len(a.files), named))
    passed = sort_ids(t for t in done if want[t] == "pass")
    failed = sort_ids(t for t in done if want[t] == "fail")
    if passed:
        print("pass (%d): %s" % (len(passed), ", ".join(passed)))
    for tc in failed:
        c = next(c for c in seen[tc] if c["outcome"] == "fail")
        print("FAIL: %s — %s%s" % (tc, c["name"], (": " + c["note"]) if c["note"] else ""))
    if untouched:
        print("skipped, left unchanged: " + ", ".join(sort_ids(untouched)))
    for tc in sort_ids(unknown):
        print("not in TEST-PLAN.md: %s (test \"%s\")" % (tc, unknown[tc]))
    left = [(tc, cell(t, r, "type").lower()) for _, t, r in tc_rows(p) for tc in [cell(t, r, "tc").strip("* ")]
            if cell(t, r, "status").lower() not in PASSED and tc not in want and not RETIRED.match(cell(t, r, "steps"))]
    if left:
        hand = [tc for tc, typ in left if typ == "manual"]
        auto = [tc for tc, typ in left if typ != "manual"]
        print("Still not passed and not in these results: %s" % "; ".join(
            x for x in ("%d automated (%s)" % (len(auto), ", ".join(auto[:15]) + (" …" if len(auto) > 15 else ""))
                        if auto else "", "%d manual (%s)" % (len(hand), ", ".join(hand[:15])
                                                             + (" …" if len(hand) > 15 else "")) if hand else "") if x))
    if not named:
        print("No test name carries a TC id. Convention: put the id in the test name, e.g. `test_TC_012_refund_capped` "
              "or `it(\"TC-012 refund is capped\")`.")
        return 1
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(prog="sentinel.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("seed"); x.add_argument("project"); x.add_argument("--phase", required=True)
    x.set_defaults(fn=cmd_seed)
    x = sub.add_parser("next"); x.add_argument("project"); x.set_defaults(fn=cmd_next)
    x = sub.add_parser("coverage"); x.add_argument("project"); x.add_argument("--phase", required=True)
    x.set_defaults(fn=cmd_coverage)
    x = sub.add_parser("check"); x.add_argument("project"); x.add_argument("--phase"); x.set_defaults(fn=cmd_check)
    x = sub.add_parser("set"); x.add_argument("project"); x.add_argument("results", nargs="+")
    x.set_defaults(fn=cmd_set)
    x = sub.add_parser("results"); x.add_argument("project"); x.add_argument("files", nargs="+")
    x.set_defaults(fn=cmd_results)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
