#!/usr/bin/env python3
"""STARK requirements-register tools. Every command takes the design folder <D> = <P>/design.

  register.py init   <D>             create _work/requirements.md and _work/STATE.md (leaves existing files alone)
  register.py prd    <D>             summarise the PRD's FR / BR rows: in scope, to confirm, skipped, not yet cited
  register.py seed   <D>             add one NEW row per in-scope FR and BR that no REQ cites yet, then number them
  register.py number <D>             give every row whose ID is NEW a final REQ-### (never renumbers)
  register.py assign <D> <file>      fill the Module column from a map file with lines like  M1: REQ-001-REQ-012, REQ-040
  register.py merge  <D>             append rows from _work/extract/*.md (parallel extraction) and number them
  register.py lint   <D> [--strict]  check the register (FR chain, sources, modules) and print statistics
  register.py ledger <D>             coverage of extra design sources: every chunk has REQs or a recorded reason
  register.py slice  <D> <module> [--out <dir>]
                                     write one module's requirements to _work/slices/<module>.md (or <dir>)
  register.py next-ac <D>            print the next free acceptance-criterion ID (AC-###)
  register.py number-ac <D>          replace `AC-NEW` in AC table rows with final sequential AC-### IDs
  register.py trace  <D> [--out <file>] [--no-summary]
                                     write the traceability table (FR → REQ → spec → AC → WP → audit);
                                     default _work/traceability.md + the summary inside TECHNICAL.md

Layout: <P>/discovery/PRD.md (Alice, read-only) · <D>/_work/requirements.md · <D>/TECHNICAL.md · <D>/technical/*.md
        · <D>/MODULES.md · <P>/plan/PLAN.md, AUDIT.md, audit/*.md (Jarvis, read-only here).
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.normpath(os.path.join(HERE, "..", "..", "..", "lib"))
sys.path.insert(0, LIB)
import mdtables as md  # noqa: E402  (shared table/ID parser — the same one atlasctl and the gates use)

CANON = ["ID", "Cat", "Type", "Requirement", "Source", "Priority", "Module", "Status"]
CATS = {"FUNC", "RULE", "DATA", "UI", "NOTIF", "INT", "SEC", "PERF", "OPS", "UX"}
FUNCTIONAL = {"FUNC", "RULE", "DATA", "UI", "NOTIF", "INT"}
REQ_RE = re.compile(r"REQ-\d{2,}")
FR_RE = re.compile(r"\b(?:FR|BR)-\d{2,}\b")
AC_RE = re.compile(r"\bAC-\d{2,}\b")
CHUNK_RE = re.compile(r"\[(d\d+-\d{3})\]")
PRD_SECTION_RE = re.compile(r"\bPRD\s*§\s*\d+")
UNNUMBERED = {"NEW", "REQ-NEW", "REQ-?", "REQ-???", "?", ""}
FR_SKIP = ("out of scope", "rejected", "deferred")
DEAD = ("out of scope", "rejected", "deferred", "removed")
SKELETON = """# Requirements Register — {{Project name}}

Primary source: `../discovery/PRD.md` (Alice) · Extra design sources: `_work/sources/INDEX.md` (if any)
Size class: (set in the sizing step)
System type: (greenfield / brownfield)

## Document roles & precedence

## Sizing breakdown

## Platforms

## Modules
Module list, rigour and code paths: `../MODULES.md`. Purpose, owned entities and dependencies: TECHNICAL.md §6.

## Requirements
| ID | Cat | Type | Requirement | Source | Priority | Module | Status |
|---|---|---|---|---|---|---|---|

## Actors & roles
## Entities
## States
## Workflows
## Dashboards & reports
## Notifications
## Integrations
## Non-functional expectations
## Constraints
## Existing data & migration
## Glossary
## Contradictions
| # | One place says | Another says | Resolution |
|---|---|---|---|

## Open questions
| ID | Question | Affects | Blocking | Recommended default | Owner | Status |
|---|---|---|---|---|---|---|

## Assumptions
| ID | Assumption | Affects | Confirm with |
|---|---|---|---|

## Out of scope
## Source ID map
"""

STATE_SKELETON = """# STARK run state

Update after every step: tick it, add the date, and note the facts later steps need.

| | |
|---|---|
| Mode | build |
| PRD version | |
| System type | |
| Code repo (read-only) | |
| Size class | |
| Layout | (single file / core + module files) |
| Modules | |

## Steps
- [ ] 0 Setup
- [ ] 1 Intake (PRD + extra design sources)
- [ ] 2 Extract
- [ ] 3 Size
- [ ] 4 Map the codebase (existing code only)
- [ ] 5 Model + modules + rigour proposal
- [ ] 6 Checkpoint with the user
- [ ] 7 Architecture & quality
- [ ] 8 Technical spec
- [ ] 9 Review
- [ ] 10 Overview
- [ ] 11 Verify
- [ ] 12 Hand off (rigour confirmation, events)

## Notes for later steps
"""


# ------------------------------------------------------------------ paths
def project_dir(d):
    return os.path.dirname(os.path.abspath(d))


def prd_path(d):
    return os.path.join(project_dir(d), "discovery", "PRD.md")


def plan_dir(d):
    return os.path.join(project_dir(d), "plan")


# ------------------------------------------------------------------ parsing
def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def is_sep(line):
    return bool(re.match(r"^\s*\|?\s*:?-{2,}", line))


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")


def req_tables(lines):
    """Yield (header_cells, [(line_index, cells)], header_line) for every requirements table."""
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and is_sep(lines[i + 1]):
            header = split_row(lines[i])
            rows, j = [], i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j, split_row(lines[j])))
                j += 1
            cols = {h.strip().lower() for h in header}
            if header and header[0].strip().lower() in ("id", "req", "req id") and cols & {"requirement", "statement", "description"}:
                first = [c[0] for _, c in rows if c]
                if not rows or any(REQ_RE.search(x) or x.upper() in UNNUMBERED for x in first):
                    if not any(re.match(r"(OQ|ASM|WP|AD|BR|FR|UC|AC)-", x) for x in first):
                        yield header, rows, i
            i = j
        else:
            i += 1


def generic_tables(lines):
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and is_sep(lines[i + 1]):
            header = split_row(lines[i])
            rows, j = [], i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j, split_row(lines[j])))
                j += 1
            yield header, rows, i
            i = j
        else:
            i += 1


def clean_id(cell):
    m = REQ_RE.search(cell)
    return m.group(0) if m else cell.strip()


def register_path(d):
    return os.path.join(d, "_work", "requirements.md")


def load(d):
    """Return (lines, rows). Each row: dict with canonical keys + _line, _removed."""
    path = register_path(d)
    if not os.path.exists(path):
        sys.exit("Register not found: %s — run: register.py init %s" % (path, d))
    lines = read_lines(path)
    rows = []
    for header, trows, _ in req_tables(lines):
        names = [h.strip().lower() for h in header]
        for li, cells in trows:
            row = {k: "" for k in CANON}
            for k in CANON:
                key = k.lower()
                alt = {"cat": ("cat", "category"), "requirement": ("requirement", "statement", "description")}.get(key, (key,))
                for a in alt:
                    if a in names and names.index(a) < len(cells):
                        row[k] = cells[names.index(a)]
                        break
            row["_raw_id"] = cells[0] if cells else ""
            row["_removed"] = "~~" in row["_raw_id"]
            row["ID"] = clean_id(row["_raw_id"].replace("~", ""))
            row["_line"] = li
            rows.append(row)
    return lines, rows


def active(rows):
    return [r for r in rows if not r["_removed"] and REQ_RE.fullmatch(r["ID"] or "")]


def live(rows):
    """Active requirements that still count (not out of scope / deferred / rejected)."""
    return [r for r in active(rows) if not any(w in r["Status"].lower() for w in DEAD)]


def req_num(rid):
    return int(rid.split("-")[1])


def expand_ranges(text):
    """REQ ids in text; 'REQ-010–REQ-014' covers the ids in between (only for ranges of ≤ 25)."""
    ids = set(REQ_RE.findall(text))
    for a, b in re.findall(r"REQ-(\d+)\s*(?:–|—|-|\.\.\.?|…|to)\s*(?:REQ-)?(\d+)", text):
        lo, hi = int(a), int(b)
        if 0 < hi - lo <= 25:
            for n in range(lo, hi + 1):
                ids.add("REQ-%0*d" % (len(a), n))
    return ids


def upstream(row):
    """FR-/BR- IDs a register row cites."""
    return sorted(set(FR_RE.findall(row["Source"] + " " + row["Requirement"])))


def is_derived(row):
    return row["Type"].strip().lower().startswith("derived")


def status_exempt(status):
    """Statuses that need no further build work."""
    s = status.lower()
    return any(w in s for w in ("built", "done", "parked", "out of scope", "removed", "deferred", "rejected"))


# ------------------------------------------------------------------ PRD (Alice) — read natively
def prd_items(d):
    """FR and BR rows of the PRD: id → {kind, text, role, priority, status}. Empty dict if there is no PRD."""
    out = collections.OrderedDict()
    path = prd_path(d)
    for t in md.read_tables(Path(path)):
        ci, cs = t.col("id"), t.col("status")
        if ci is None:
            continue
        ct = t.col("requirement", "rule", "statement", "description")
        cr, cp = t.col("role"), t.col("priority")
        for r in t.rows:
            rid = r[ci].strip("* ") if ci < len(r) else ""
            m = re.match(r"^(FR|BR)-\d+$", rid)
            if not m:
                continue
            g = lambda i: (r[i].strip() if i is not None and i < len(r) else "")  # noqa: E731
            out[rid] = {"kind": m.group(1), "text": g(ct), "role": g(cr), "priority": g(cp),
                        "status": g(cs).lower()}
    return out


def in_scope(item):
    return not any(w in item["status"] for w in FR_SKIP)


def cmd_prd(d):
    items = prd_items(d)
    if not items:
        sys.exit("No FR-### rows found in %s — Alice's PRD is the primary source; run /alice first." % prd_path(d))
    _, rows = load(d) if os.path.exists(register_path(d)) else ([], [])
    cited = collections.defaultdict(list)
    for r in active(rows):
        for u in upstream(r):
            cited[u].append(r["ID"])
    by = collections.Counter(v["status"] or "(blank)" for v in items.values())
    frs = [k for k, v in items.items() if v["kind"] == "FR"]
    print("PRD: %d FR, %d BR. FR status: %s" % (len(frs), len(items) - len(frs),
                                                ", ".join("%s %d" % kv for kv in sorted(by.items()))))
    skip = [k for k, v in items.items() if not in_scope(v)]
    tc = [k for k, v in items.items() if "to confirm" in v["status"]]
    todo = [k for k, v in items.items() if in_scope(v) and k not in cited]
    print("Skipped (out of scope / rejected / deferred): %s" % (", ".join(skip) or "none"))
    print("To confirm (become REQs flagged with the open question): %s" % (", ".join(tc) or "none"))
    print("In scope, not yet cited by any REQ: %s" % (", ".join(todo) or "none"))


def cmd_seed(d):
    items = prd_items(d)
    if not items:
        sys.exit("No FR-### rows found in %s." % prd_path(d))
    lines, rows = load(d)
    cited = {u for r in active(rows) for u in upstream(r)}
    tables = list(req_tables(lines))
    if not tables:
        sys.exit("The register has no requirements table (header starting with '| ID |').")
    header, trows, hline = tables[0]
    names = [h.strip().lower() for h in header]
    insert_at = (trows[-1][0] if trows else hline + 1) + 1
    new = []
    for k, v in items.items():
        if not in_scope(v) or k in cited:
            continue
        vals = {"id": "NEW", "cat": "FUNC" if v["kind"] == "FR" else "RULE", "type": "stated",
                "requirement": v["text"].replace("|", "/") or "(see PRD)", "source": k,
                "priority": v["priority"], "module": "",
                "status": "to confirm" if "to confirm" in v["status"] else ""}
        new.append("| " + " | ".join(vals.get(n, "") for n in names) + " |")
    lines[insert_at:insert_at] = new
    with open(register_path(d), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    n = cmd_number(d, quiet=True)
    print("Seeded %d row(s) from the PRD (one per in-scope FR/BR not yet cited) and numbered them." % n)
    print("Next: split compound rows into atomic REQs (new rows as NEW, cite the same FR), set Cat, then run lint.")


# ------------------------------------------------------------------ init / assign
def cmd_init(d):
    work = os.path.join(d, "_work")
    os.makedirs(work, exist_ok=True)
    for name, content in (("requirements.md", SKELETON), ("STATE.md", STATE_SKELETON)):
        path = os.path.join(work, name)
        if os.path.exists(path):
            print("exists, left alone: %s" % path)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print("created: %s" % path)


def cmd_assign(d, map_file):
    """Fill the Module column. Map file lines:  M1: REQ-001-REQ-012, REQ-040   (ranges of any width)."""
    wanted = {}
    for line in read_lines(map_file):
        m = re.match(r"\s*\**([A-Za-z]\w*)\**\s*[:=]\s*(.+)", line)
        if not m or not REQ_RE.search(m.group(2)):
            continue
        mod, spec = m.group(1), m.group(2)
        ids = set(REQ_RE.findall(spec))
        for x, y in re.findall(r"REQ-(\d+)\s*(?:–|—|-|\.\.\.?|…|to)\s*(?:REQ-)?(\d+)", spec):
            for n in range(int(x), int(y) + 1):
                ids.add("REQ-%0*d" % (len(x), n))
        for rid in ids:
            if rid in wanted and wanted[rid] != mod:
                sys.exit("%s is assigned to both %s and %s — every requirement belongs to exactly one module." % (rid, wanted[rid], mod))
            wanted[rid] = mod
    if not wanted:
        sys.exit("No assignments found in %s (expected lines like 'M1: REQ-001-REQ-012, REQ-040')." % map_file)
    lines, rows = load(d)
    done = 0
    for header, trows, _ in list(req_tables(lines)):
        names = [h.strip().lower() for h in header]
        if "module" not in names:
            sys.exit("A requirements table has no Module column.")
        mi = names.index("module")
        for li, cells in trows:
            rid = clean_id(cells[0].replace("~", "")) if cells else ""
            if rid in wanted:
                cells += [""] * (mi + 1 - len(cells))
                cells[mi] = wanted[rid]
                lines[li] = "| " + " | ".join(cells) + " |"
                done += 1
    with open(register_path(d), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    _, rows = load(d)
    left = [r["ID"] for r in active(rows) if not r["Module"]]
    unknown = sorted(set(wanted) - {r["ID"] for r in rows})
    print("Assigned %d requirement(s). %d still without a module%s" % (done, len(left), ": " + ", ".join(left[:20]) if left else "."))
    if unknown:
        print("Not in the register (ignored): %s" % ", ".join(unknown[:20]))


# ------------------------------------------------------------------ number / merge
def cmd_number(d, quiet=False):
    lines, rows = load(d)
    nxt = max([req_num(r["ID"]) for r in rows if REQ_RE.fullmatch(r["ID"] or "")] + [0]) + 1
    n = 0
    for r in rows:
        if r["ID"].upper() in UNNUMBERED:
            cells = split_row(lines[r["_line"]])
            cells[0] = "REQ-%03d" % nxt
            lines[r["_line"]] = "| " + " | ".join(cells) + " |"
            nxt += 1
            n += 1
    if n:
        with open(register_path(d), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    if not quiet:
        print("Numbered %d new requirement(s). Highest ID is now REQ-%03d." % (n, nxt - 1))
    return n


def cmd_merge(d):
    work = os.path.join(d, "_work")
    reg_path = register_path(d)
    os.makedirs(work, exist_ok=True)
    if not os.path.exists(reg_path):
        with open(reg_path, "w", encoding="utf-8") as f:
            f.write(SKELETON)
    done_path = os.path.join(work, "extract", ".merged")
    done = set(read_lines(done_path)) if os.path.exists(done_path) else set()
    files = [p for p in sorted(glob.glob(os.path.join(work, "extract", "*.md"))) if os.path.basename(p) not in done]
    if not files:
        print("Nothing to merge (no new files in _work/extract/).")
        return
    lines = read_lines(reg_path)
    tables = list(req_tables(lines))
    if not tables:
        sys.exit("The register has no requirements table (header starting with '| ID |').")
    header, trows, hline = tables[0]
    names = [h.strip().lower() for h in header]
    insert_at = (trows[-1][0] if trows else hline + 1) + 1
    new_rows, findings, per_file = [], [], []
    for path in files:
        src = read_lines(path)
        count = 0
        req_lines = set()
        for h2, rows2, start in req_tables(src):
            n2 = [h.strip().lower() for h in h2]
            req_lines.update(range(start, start + 2 + len(rows2)))
            for _, cells in rows2:
                out = []
                for name in names:
                    val = cells[n2.index(name)] if name in n2 and n2.index(name) < len(cells) else ""
                    out.append("NEW" if name == "id" else val)
                if any(out[1:]):
                    new_rows.append("| " + " | ".join(out) + " |")
                    count += 1
        section, buf = None, []
        for i, line in enumerate(src):
            if i in req_lines:
                continue
            if line.startswith("## "):
                if section and "".join(buf).strip():
                    findings.append((section, os.path.basename(path), "\n".join(buf).strip()))
                section, buf = line[3:].strip(), []
            elif section:
                buf.append(line)
        if section and "".join(buf).strip():
            findings.append((section, os.path.basename(path), "\n".join(buf).strip()))
        per_file.append((os.path.basename(path), count))
    lines[insert_at:insert_at] = new_rows
    with open(reg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    cmd_number(d, quiet=True)
    if findings:
        grouped = collections.OrderedDict()
        for section, fn, text in findings:
            if section.lower().startswith("requirement"):
                continue
            grouped.setdefault(section, []).append("<!-- from %s -->\n%s" % (fn, text))
        with open(os.path.join(work, "findings.md"), "a", encoding="utf-8") as f:
            for section, parts in grouped.items():
                f.write("\n## %s\n\n%s\n" % (section, "\n\n".join(parts)))
    with open(done_path, "a", encoding="utf-8") as f:
        f.write("\n".join(fn for fn, _ in per_file) + "\n")
    for fn, c in per_file:
        print("  %-28s %d requirement(s)" % (fn, c))
    print("Merged %d requirement(s) from %d file(s) into the register." % (len(new_rows), len(files)))
    if findings:
        print("Other sections gathered in _work/findings.md — consolidate them into the register, then delete that file.")
    print("Next: de-duplicate, normalise names, then run: register.py lint")


# ------------------------------------------------------------------ modules (MODULES.md + confirmed rigour)
def modules(d):
    """MODULES.md rows: id → {name, rigour (confirmed wins), proposed, confirmed, paths, signals, reason}."""
    out = collections.OrderedDict()
    for t in md.read_tables(Path(os.path.join(d, "MODULES.md"))):
        ci, cr = t.col("module"), t.col("rigour", "rigor")
        if ci is None or cr is None:
            continue
        cn, cp, cs, cw = t.col("name"), t.col("paths", "path"), t.col("signals"), t.col("reason")
        for r in t.rows:
            g = lambda i: (r[i].strip() if i is not None and i < len(r) else "")  # noqa: E731
            mid = g(ci).strip("* ")
            if re.match(r"^M\d+$", mid):
                out[mid] = {"name": g(cn), "proposed": g(cr).strip("* ").capitalize(), "paths": g(cp),
                            "signals": g(cs), "reason": g(cw), "confirmed": False, "header": t.headers}
    events = os.path.join(project_dir(d), "log", "events.jsonl")
    if os.path.exists(events):
        with open(events, encoding="utf-8") as f:
            for ln in f:
                try:
                    ev = json.loads(ln)
                except ValueError:
                    continue
                if ev.get("type") == "rigour.set" and ev.get("data", {}).get("module") in out:
                    m = out[ev["data"]["module"]]
                    m["rigour"], m["confirmed"] = ev["data"].get("level", m["proposed"]), True
    for m in out.values():
        m.setdefault("rigour", m["proposed"])
    return out


# ------------------------------------------------------------------ lint / stats
def counter_table(title, counter, limit=30):
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return "%s: %s" % (title, ", ".join("%s %d" % (k or "(blank)", v) for k, v in items))


def lint(d, strict=False):
    lines, rows = load(d)
    fails, warns = [], []
    act = active(rows)
    unnum = [r for r in rows if r["ID"].upper() in UNNUMBERED]
    if unnum:
        fails.append("%d row(s) have no final ID — run: register.py number" % len(unnum))
    dup = [k for k, v in collections.Counter(r["ID"] for r in rows if REQ_RE.fullmatch(r["ID"] or "")).items() if v > 1]
    if dup:
        fails.append("Duplicate IDs: %s" % ", ".join(sorted(dup)[:30]))
    no_src = [r["ID"] for r in act if not r["Source"]]
    if no_src:
        fails.append("%d requirement(s) have no Source: %s" % (len(no_src), ", ".join(no_src[:20])))
    empty = [r["ID"] for r in act if len(r["Requirement"]) < 8]
    if empty:
        fails.append("Empty requirement text: %s" % ", ".join(empty[:20]))

    # --- the FR → REQ chain (Alice's PRD is the primary source)
    items = prd_items(d)
    if not items:
        fails.append("No FR-### rows found in %s — the PRD is the primary source." % os.path.relpath(prd_path(d), project_dir(d)))
    chunks = live_chunks(d)
    no_up = []
    for r in act:
        if not r["Source"]:
            continue
        ups = upstream(r)
        if r["Cat"].upper() in FUNCTIONAL and not ups and not is_derived(r):
            no_up.append(r["ID"])
        elif not ups and not is_derived(r) and not PRD_SECTION_RE.search(r["Source"]) and not CHUNK_RE.search(r["Source"]):
            no_up.append(r["ID"])
        if is_derived(r) and not REQ_RE.search(r["Source"]):
            fails.append("%s is derived but its Source does not name the REQ it is derived from." % r["ID"])
    if no_up:
        fails.append("%d requirement(s) do not cite their upstream FR-/BR- ID (non-functional rows may cite `PRD §14` / "
                     "`PRD §15` or a design-source chunk instead): %s" % (len(no_up), ", ".join(no_up[:25])))
    if items:
        unknown_up = sorted({u for r in act for u in upstream(r) if u not in items})
        if unknown_up:
            fails.append("Register cites FR/BR IDs that are not in the PRD: %s" % ", ".join(unknown_up[:25]))
        dead_up = sorted({"%s→%s" % (r["ID"], u) for r in live(rows) for u in upstream(r)
                          if u in items and not in_scope(items[u])})
        if dead_up:
            warns.append("Live requirements cite FRs/BRs the PRD marks out of scope / rejected / deferred: %s" % ", ".join(dead_up[:20]))
        cited = {u for r in act for u in upstream(r)}
        miss = [k for k, v in items.items() if v["kind"] == "FR" and in_scope(v) and k not in cited]
        if miss:
            fails.append("%d in-scope FR(s) are cited by no REQ (run `register.py seed`, or record why): %s"
                         % (len(miss), ", ".join(miss[:40])))
        miss_br = [k for k, v in items.items() if v["kind"] == "BR" and in_scope(v) and k not in cited]
        if miss_br:
            warns.append("Business rules not cited by any REQ: %s" % ", ".join(miss_br[:30]))
        tc = {k for k, v in items.items() if "to confirm" in v["status"]}
        unflagged = [r["ID"] for r in act if set(upstream(r)) & tc and "confirm" not in r["Status"].lower()]
        if unflagged:
            warns.append("REQs built on a 'to confirm' FR should carry Status `to confirm` and the open question ID: %s"
                         % ", ".join(unflagged[:20]))

    if chunks is not None:
        bad = sorted({c for r in act for c in CHUNK_RE.findall(r["Source"]) if c not in chunks})
        if bad:
            fails.append("Source cells cite unknown design-source chunk IDs: %s" % ", ".join(bad[:20]))
    stated = [r for r in act if not is_derived(r)]
    derived = len(act) - len(stated)
    if stated and derived > max(5, 0.2 * len(stated)):
        warns.append("%d derived requirements against %d stated (over 20%%) — keep only what a stated requirement cannot work "
                     "without; the rest are open questions or not needed." % (derived, len(stated)))

    # --- modules
    no_mod = [r["ID"] for r in act if not r["Module"]]
    if no_mod:
        (fails if strict else warns).append("%d requirement(s) have no Module%s" % (len(no_mod), "" if strict else " (fill in the modelling step)"))
    mods = modules(d)
    if strict:
        if not mods:
            fails.append("MODULES.md is missing or has no `| Module | Name | Rigour | Paths | Signals | Reason |` rows.")
        else:
            odd = sorted({r["Module"] for r in act if r["Module"] and r["Module"] != "X" and r["Module"] not in mods})
            if odd:
                fails.append("Register Module values not in MODULES.md (use M1, M2 … or X): %s" % ", ".join(odd))
    bad_cat = sorted({r["Cat"] for r in act if r["Cat"] and r["Cat"].upper() not in CATS})
    if bad_cat:
        warns.append("Unknown categories: %s" % ", ".join(bad_cat[:12]))
    seen, twins = {}, []
    for r in act:
        key = re.sub(r"[^a-z0-9]+", " ", r["Requirement"].lower()).strip()
        if key in seen:
            twins.append("%s = %s" % (r["ID"], seen[key]))
        seen.setdefault(key, r["ID"])
    if twins:
        warns.append("Identical requirement text: %s" % ", ".join(twins[:12]))
    long_rows = [r["ID"] for r in act if len(r["Requirement"]) > 420]
    if long_rows:
        warns.append("%d requirement(s) are very long — probably not atomic: %s" % (len(long_rows), ", ".join(long_rows[:12])))
    text = "\n".join(lines)
    stats = [
        "Requirements: %d active (%d live), %d removed/duplicate." % (len(act), len(live(rows)), len([r for r in rows if r["_removed"]])),
        counter_table("By category", collections.Counter(r["Cat"].upper() for r in act)),
        counter_table("By module", collections.Counter(r["Module"] for r in act)),
    ]
    if any(r["Type"] for r in act):
        stats.append(counter_table("By type", collections.Counter(r["Type"].lower() for r in act)))
    if any(r["Status"] for r in act):
        stats.append(counter_table("By status", collections.Counter(r["Status"].lower() for r in act)))
    if any(r["Priority"] for r in act):
        stats.append(counter_table("By priority", collections.Counter(r["Priority"] for r in act)))
    contra = section_text(lines, "Contradictions")
    stats.append("Open questions in the register: %d · Contradictions: %d"
                 % (len(set(re.findall(r"^\|\s*(OQ-\d+)", text, flags=re.M))),
                    max(0, len(re.findall(r"^\|", contra, flags=re.M)) - 2)))
    return fails, warns, stats


def section_text(lines, name):
    out, on = [], False
    for line in lines:
        if line.startswith("## "):
            on = line[3:].strip().lower().startswith(name.lower())
            continue
        if on:
            out.append(line)
    return "\n".join(out)


def report(fails, warns):
    for w in warns:
        print("WARN  " + w)
    for f in fails:
        print("FAIL  " + f)
    if fails:
        print("\nResult: FAIL (%d issue(s))." % len(fails))
        sys.exit(1)
    print("\nResult: PASS" + (" with %d warning(s)." % len(warns) if warns else "."))


# ------------------------------------------------------------------ ledger (extra design sources only)
def manifest(d):
    path = os.path.join(d, "_work", "sources", "manifest.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def live_chunks(d):
    m = manifest(d)
    if not m:
        return None
    out = collections.OrderedDict()
    for code in sorted(m.get("docs", {}), key=lambda c: int(re.sub(r"\D", "", c) or 0)):
        doc = m["docs"][code]
        if doc.get("state") == "REMOVED":
            continue
        for c in doc.get("chunks", []):
            out[c["id"]] = dict(c, file=doc.get("file", ""))
    return out


def ledger(d, write=True):
    """Return (fails, warns). Every live chunk of an extra design source yields requirements or carries a reason."""
    chunks = live_chunks(d)
    if chunks is None:
        return [], []  # no extra design sources: the PRD's FR coverage (lint) is the ledger
    _, rows = load(d)
    counts = collections.Counter(c for r in active(rows) if not is_derived(r) for c in set(CHUNK_RE.findall(r["Source"])))
    path = os.path.join(d, "_work", "ledger.md")
    reasons = {}
    if os.path.exists(path):
        for line in read_lines(path):
            cells = split_row(line)
            if len(cells) >= 5 and re.fullmatch(r"d\d+-\d{3}", cells[0]) and cells[3].lower() == "none" and len(cells[4]) > 2:
                reasons[cells[0]] = cells[4]
    todo, thin, out = [], [], []
    for cid, c in chunks.items():
        n = counts.get(cid, 0)
        if n:
            status, reason = "ok", ""
            if c.get("words", 0) >= 1200 and n < c["words"] / 400.0:
                thin.append("%s (%d words, %d REQs)" % (cid, c["words"], n))
        elif cid in reasons:
            status, reason = "none", reasons[cid]
        else:
            status, reason = "TODO", ""
            todo.append(cid)
        out.append("| %s | %s | %d | %d | %s | %s |" % (cid, str(c.get("title", "")).replace("|", "/")[:60], c.get("words", 0), n, status, reason))
    if write:
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Design-source coverage ledger\n\nGenerated by `register.py ledger`. For a `TODO` chunk either extract its "
                    "requirements, or set Status to `none` and give the Reason (e.g. cover page, background only, already covered "
                    "by FR-###), then re-run.\n\n| Chunk | Section | Words | REQs | Status | Reason |\n|---|---|---|---|---|---|\n"
                    + "\n".join(out) + "\n")
    fails, warns = [], []
    if todo:
        fails.append("%d design-source chunk(s) produced no requirements and have no recorded reason: %s — see _work/ledger.md"
                     % (len(todo), ", ".join(todo[:25])))
    if thin:
        warns.append("Long chunks with very few requirements (re-read them): %s" % "; ".join(thin[:12]))
    return fails, warns


# ------------------------------------------------------------------ slice
def cmd_slice(d, module, out_dir=None):
    _, rows = load(d)
    key = module.lower()
    picked = [r for r in active(rows) if r["Module"].lower() == key or re.match(re.escape(key) + r"\b", r["Module"].lower())]
    if not picked:
        mods = sorted({r["Module"] for r in active(rows) if r["Module"]})
        sys.exit("No requirements for module '%s'. Modules in the register: %s" % (module, ", ".join(mods) or "(none assigned yet)"))
    out_dir = out_dir or os.path.join(d, "_work", "slices")
    os.makedirs(out_dir, exist_ok=True)
    name = re.sub(r"[^\w-]+", "-", module.lower()).strip("-")
    m = modules(d).get(picked[0]["Module"], {})
    chunks = sorted({c for r in picked for c in CHUNK_RE.findall(r["Source"])})
    body = ["# Requirements for %s %s (%d)" % (picked[0]["Module"], m.get("name", ""), len(picked)), "",
            "Rigour: %s%s" % (m.get("rigour", "?"), "" if m.get("confirmed") else " (proposed)"),
            "Upstream: PRD rows %s" % (", ".join(sorted({u for r in picked for u in upstream(r)})) or "—"),
            "Design-source chunks for detail look-ups: " + (", ".join(chunks) or "—"), "",
            "| ID | Cat | Type | Requirement | Source | Priority | Status |", "|---|---|---|---|---|---|---|"]
    body += ["| %s |" % " | ".join(r[k] for k in ("ID", "Cat", "Type", "Requirement", "Source", "Priority", "Status")) for r in picked]
    path = os.path.join(out_dir, name + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")
    print("%d requirement(s) → %s" % (len(picked), path))


# ------------------------------------------------------------------ acceptance criteria
def spec_files(d):
    return [p for p in [os.path.join(d, "TECHNICAL.md")] + sorted(glob.glob(os.path.join(d, "technical", "*.md"))) if os.path.exists(p)]


def ac_rows(d):
    """AC definitions: table rows whose first cell is one AC-### → list of (ac, reqs, file)."""
    out = []
    for p in spec_files(d):
        for t in md.read_tables(Path(p)):
            for r in t.rows:
                if not r:
                    continue
                own = AC_RE.findall(r[0])
                if len(own) == 1 and r[0].strip("* `") == own[0]:
                    out.append((own[0], sorted(expand_ranges(" ".join(r[1:]))), os.path.relpath(p, d)))
    return out


def cmd_number_ac(d):
    """Replace `AC-NEW` in the first cell of AC table rows with the next free AC-### (spec files in order)."""
    nums = [int(x.split("-")[1]) for p in spec_files(d) for x in AC_RE.findall("\n".join(read_lines(p)))]
    nxt, n = max(nums + [0]) + 1, 0
    for p in spec_files(d):
        lines = read_lines(p)
        changed = False
        for i, line in enumerate(lines):
            if re.match(r"^\s*\|\s*\**AC-NEW\**\s*\|", line):
                lines[i] = re.sub(r"AC-NEW", "AC-%03d" % nxt, line, count=1)
                nxt, n, changed = nxt + 1, n + 1, True
        if changed:
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
    print("Numbered %d new acceptance criteria. Next free: AC-%03d." % (n, nxt))


def cmd_next_ac(d):
    nums = [int(a.split("-")[1]) for a, _, _ in ac_rows(d)]
    for p in spec_files(d):
        nums += [int(x.split("-")[1]) for x in AC_RE.findall("\n".join(read_lines(p)))]
    print("AC-%03d" % (max(nums + [0]) + 1))


# ------------------------------------------------------------------ trace
def citations(path, d):
    """REQ → ordered list of 'file §heading' places where it is cited."""
    out = collections.defaultdict(list)
    heading, fence = "", False
    rel = os.path.relpath(path, d)
    for line in read_lines(path):
        if line.startswith("```"):
            fence = not fence
        if not fence and re.match(r"#{2,4} ", line):
            heading = re.sub(r"[#*`]", "", line).strip()
            heading = heading if len(heading) <= 60 else heading[:60].rsplit(" ", 1)[0] + "…"
            continue
        for rid in expand_ranges(line):
            place = "%s §%s" % (rel, heading) if heading else rel
            if place not in out[rid]:
                out[rid].append(place)
    return out


def plan_table_map(plan_text):
    """REQ → work packages, from the REQs column of PLAN.md's work-package table (what atlasctl and gate G3 read)."""
    out = collections.defaultdict(list)
    for t in md.tables(plan_text):
        cw, cr = t.col("wp"), t.col("reqs", "req")
        if cw is None or cr is None or t.col("title") is None:
            continue
        for r in t.rows:
            wid = r[cw].strip("* ") if cw < len(r) else ""
            if not re.match(r"^WP-\d+$", wid) or cr >= len(r):
                continue
            for rid in expand_ranges(r[cr]):
                if wid not in out[rid]:
                    out[rid].append(wid)
    return out


def plan_text(d):
    path = os.path.join(plan_dir(d), "PLAN.md")
    return "\n".join(read_lines(path)) if os.path.exists(path) else ""


def audit_map(d):
    out = {}
    pd = plan_dir(d)
    for path in [os.path.join(pd, "AUDIT.md")] + sorted(glob.glob(os.path.join(pd, "audit", "*.md"))):
        if not os.path.exists(path):
            continue
        for header, trows, _ in generic_tables(read_lines(path)):
            names = [h.lower() for h in header]
            if "status" not in names or not names or not names[0].startswith(("req", "id")):
                continue
            for _, cells in trows:
                m = REQ_RE.search(cells[0]) if cells else None
                if m and names.index("status") < len(cells):
                    out[m.group(0)] = cells[names.index("status")]
    return out


def cmd_trace(d, out_path=None, summary=True):
    _, rows = load(d)
    cites = collections.defaultdict(list)
    for p in spec_files(d):
        for rid, places in citations(p, d).items():
            cites[rid] += [x for x in places if "raceability" not in x and " §" in x]
    for rid in cites:  # module spec files first, the core file last
        cites[rid].sort(key=lambda x: x.startswith("TECHNICAL.md"))
    acs = collections.defaultdict(list)
    for ac, reqs, _ in ac_rows(d):
        for r in reqs:
            acs[r].append(ac)
    plan, audit = plan_table_map(plan_text(d)), audit_map(d)
    act = active(rows)
    # First column is a plain counter so `atlasctl impact` does not treat these generated rows as definitions.
    head = ["#", "REQ", "Upstream", "Requirement", "Specified in", "ACs", "Planned in"] + (["Audit"] if audit else [])
    out = ["# Traceability", "", "Generated by `register.py trace` — do not edit by hand; re-run after changing the blueprint.", "",
           "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for i, r in enumerate(act, 1):
        text = r["Requirement"] if len(r["Requirement"]) <= 100 else r["Requirement"][:97] + "…"
        ups = ", ".join(upstream(r)) or r["Source"]
        cells = [str(i), r["ID"], ups, text, "; ".join(cites.get(r["ID"], [])[:3]) or "—",
                 ", ".join(acs.get(r["ID"], [])) or "—", ", ".join(plan.get(r["ID"], [])) or "—"]
        if audit:
            cells.append(audit.get(r["ID"], "—"))
        out.append("| " + " | ".join(cells) + " |")
    path = out_path or os.path.join(d, "_work", "traceability.md")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("Traceability written: %s (%d requirements)" % (path, len(act)))
    if not summary:
        return
    by_mod = collections.OrderedDict()
    for r in act:
        m = by_mod.setdefault(r["Module"] or "(unassigned)", {"n": 0, "spec": 0, "ac": 0, "plan": 0, "files": collections.Counter()})
        m["n"] += 1
        m["spec"] += 1 if cites.get(r["ID"]) else 0
        m["ac"] += 1 if acs.get(r["ID"]) else 0
        m["plan"] += 1 if plan.get(r["ID"]) or status_exempt(r["Status"]) else 0
        for place in cites.get(r["ID"], [])[:1]:
            m["files"][place.split(" §")[0]] += 1

    def mod_key(name):
        mm = re.match(r"M(\d+)", name)
        return (0, int(mm.group(1))) if mm else (1, 0)

    table = ["| Module | Requirements | Specified | With ACs | Planned | Main spec file |", "|---|---|---|---|---|---|"]
    for mod in sorted(by_mod, key=mod_key):
        m = by_mod[mod]
        main = m["files"].most_common(1)[0][0] if m["files"] else "—"
        table.append("| %s | %d | %d | %d | %d | %s |" % (mod, m["n"], m["spec"], m["ac"], m["plan"], main))
    core = os.path.join(d, "TECHNICAL.md")
    start, end = "<!-- trace-summary:start -->", "<!-- trace-summary:end -->"
    if os.path.exists(core):
        text = "\n".join(read_lines(core))
        if start in text and end in text:
            text = text[:text.index(start) + len(start)] + "\n" + "\n".join(table) + "\n" + text[text.index(end):]
            with open(core, "w", encoding="utf-8") as f:
                f.write(text)
            print("Module summary updated inside TECHNICAL.md (between the trace-summary markers).")
            return
    print("Module summary (no trace-summary markers found in TECHNICAL.md — paste it under Traceability):\n")
    print("\n".join(table))


def main():
    a = sys.argv[1:]
    if a and a[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if len(a) < 2:
        print(__doc__)
        sys.exit(2)
    cmd, d = a[0], os.path.abspath(a[1])
    if cmd == "init":
        cmd_init(d)
    elif cmd == "prd":
        cmd_prd(d)
    elif cmd == "seed":
        cmd_seed(d)
    elif cmd == "assign" and len(a) >= 3:
        cmd_assign(d, a[2])
    elif cmd == "number":
        cmd_number(d)
    elif cmd == "merge":
        cmd_merge(d)
    elif cmd == "lint":
        fails, warns, stats = lint(d, strict="--strict" in a)
        print("\n".join(stats) + "\n")
        report(fails, warns)
    elif cmd == "ledger":
        fails, warns = ledger(d)
        if live_chunks(d) is not None:
            print("Ledger written: %s" % os.path.join(d, "_work", "ledger.md"))
        else:
            print("No extra design sources (no _work/sources/manifest.json) — PRD coverage is checked by lint.")
        report(fails, warns)
    elif cmd == "slice" and len(a) >= 3:
        cmd_slice(d, a[2], os.path.abspath(a[a.index("--out") + 1]) if "--out" in a else None)
    elif cmd == "next-ac":
        cmd_next_ac(d)
    elif cmd == "number-ac":
        cmd_number_ac(d)
    elif cmd == "trace":
        out = a[a.index("--out") + 1] if "--out" in a else None
        cmd_trace(d, out_path=os.path.abspath(out) if out else None, summary="--no-summary" not in a)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
