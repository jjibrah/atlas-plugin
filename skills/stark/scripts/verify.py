#!/usr/bin/env python3
"""Verify a STARK design folder (<P>/design). Exit code 1 if anything FAILs (WARNs do not fail).

Usage: verify.py <design_dir> [--stage extract|spec|all]

  extract  register well-formed; every in-scope PRD FR cited by a REQ; extra design sources accounted for
  spec     + modules assigned; MODULES.md valid; every REQ specified and given an acceptance criterion (AC-###);
           Critical modules carry threat notes and failure/rollback behaviour; open-question table readable by gate G2;
           documents complete, consistent and within size budgets
  all      (default) spec + OVERVIEW.md present and plain-language

These checks mirror what `atlasctl gate G2` reads, so a PASS here means G2 can parse the design.
"""
from __future__ import annotations

import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import register as reg  # noqa: E402

BUDGETS_KB = {"TECHNICAL.md": 40, "OVERVIEW.md": 30, "DECISIONS.md": 40, "MODULES.md": 15}
SINGLE_FILE_BUDGET_KB = 60   # TECHNICAL.md when there are no module files
MODULE_BUDGET_KB = 35
MAX_CELL = 600
MAX_LINE = 1500
LATER_OUTPUTS = ("PLAN.md", "AUDIT.md")  # Jarvis writes these after the design
MODULES_HEADER = ["module", "name", "rigour", "paths", "signals", "reason"]
LEVELS = ("Light", "Standard", "Critical")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def rel(path, root):
    return os.path.relpath(path, root)


def mermaid_blocks(text):
    return re.findall(r"```mermaid\s*\n(.*?)```", text, flags=re.S)


# ------------------------------------------------------------------ generic document checks
def check_docs(root, docs, fails, warns):
    has_modules = bool(glob.glob(os.path.join(root, "technical", "*.md")))
    for path, text in docs.items():
        name = rel(path, root)
        ph = re.findall(r"\{\{[^}]*\}\}", text)
        if ph:
            fails.append("%s: %d unfilled placeholder(s), e.g. %s" % (name, len(ph), ph[0][:60]))
        if "TEMPLATE NOTE" in text:
            fails.append("%s: template notes still present — delete them." % name)
        if len(re.findall(r"^\s*```", text, flags=re.M)) % 2:
            fails.append("%s: unbalanced ``` code fences." % name)
        for i, blk in enumerate(mermaid_blocks(text), 1):
            body = [ln for ln in blk.splitlines() if ln.strip() and not ln.strip().startswith("%%")]
            if len(body) <= 1:
                fails.append("%s: Mermaid diagram #%d is empty." % (name, i))
                continue
            kind = body[0].split()[0]
            if kind in ("flowchart", "graph"):
                if re.search(r"(?:^|\s)[A-Za-z]\w*-\w+\s*(?:\[|\(|\{|-->)", blk):
                    warns.append("%s: diagram #%d may use hyphens in node IDs (use underscores)." % (name, i))
                if re.search(r"(?:^|\s)end\s*(?:\[|-->)", blk):
                    warns.append("%s: diagram #%d uses `end` as a node ID (reserved word)." % (name, i))
                if re.search(r"\[[^\]\"]*[()][^\]\"]*\]", blk):
                    warns.append("%s: diagram #%d has parentheses in an unquoted label — wrap the label in quotes." % (name, i))
        for target in re.findall(r"\]\(([^)\s]+)\)", re.sub(r"```.*?```", "", text, flags=re.S)):
            if re.match(r"[a-z]+:|#", target):
                continue
            file_part = target.split("#")[0]
            if file_part and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), file_part))):
                if os.path.basename(file_part) in LATER_OUTPUTS or "/plan/" in "/" + file_part:
                    continue
                fails.append("%s: broken link → %s" % (name, target))
        size_kb = len(text.encode("utf-8")) / 1024.0
        base = os.path.basename(path)
        folder = os.path.basename(os.path.dirname(path))
        budget = BUDGETS_KB.get(base) if os.path.dirname(path) == root else (MODULE_BUDGET_KB if folder == "technical" else None)
        if base == "TECHNICAL.md" and os.path.dirname(path) == root and not has_modules:
            budget = SINGLE_FILE_BUDGET_KB
        if budget and size_kb > budget:
            warns.append("%s is %d KB (budget %d KB) — split it; see sizing-rubric.md → File size budgets." % (name, size_kb, budget))
        longest = max([len(ln) for ln in text.split("\n")] + [0])
        fat = sum(1 for ln in text.split("\n") if ln.lstrip().startswith("|") for c in reg.split_row(ln) if len(c) > MAX_CELL)
        if longest > MAX_LINE or fat:
            warns.append("%s has %d table cell(s) over %d characters (longest line %d) — move detail into a note below the table."
                         % (name, fat, MAX_CELL, longest))


# ------------------------------------------------------------------ spec checks
def check_spec(root, rows, tech, fails, warns):
    tech_all = "\n".join(tech.values())
    act = reg.active(rows)
    defined = {r["ID"] for r in act}
    removed = {r["ID"] for r in rows if r["_removed"]}
    referenced = reg.expand_ranges(tech_all)
    missing = sorted({r["ID"] for r in reg.live(rows)} - referenced, key=reg.req_num)
    if missing:
        fails.append("%d requirement(s) not referenced in the technical docs: %s%s"
                     % (len(missing), ", ".join(missing[:50]), " …" if len(missing) > 50 else ""))
    unknown = sorted(set(reg.REQ_RE.findall(tech_all)) - defined - removed, key=reg.req_num)
    if unknown:
        warns.append("Technical docs cite REQ IDs that are not in the register: %s" % ", ".join(unknown[:30]))
    stale = sorted(set(reg.REQ_RE.findall(tech_all)) & removed, key=reg.req_num)
    if stale:
        warns.append("Technical docs still cite removed requirements: %s" % ", ".join(stale[:30]))
    kinds = " ".join(b.split(None, 1)[0] if b.strip() else "" for b in mermaid_blocks(tech_all))
    for needed in ("flowchart", "erDiagram", "stateDiagram-v2"):
        if needed not in kinds and not (needed == "flowchart" and "graph" in kinds):
            warns.append("Technical docs have no %s diagram." % needed)
    core = tech.get(os.path.join(root, "TECHNICAL.md"), "")
    for path in tech:
        if os.path.basename(os.path.dirname(path)) == "technical" and os.path.basename(path) not in core:
            warns.append("TECHNICAL.md does not link to technical/%s." % os.path.basename(path))
    if re.search(r"^\|\s*WP\s*\|", tech_all, flags=re.M | re.I):
        warns.append("A work-package table is in the design — the plan belongs to Jarvis in plan/PLAN.md (atlasctl reads only that).")


def check_acs(root, rows, fails, warns):
    acs = reg.ac_rows(root)
    seen = {}
    for ac, reqs, f in acs:
        if ac in seen:
            fails.append("%s is defined twice (%s and %s) — AC IDs are permanent and unique." % (ac, seen[ac], f))
        seen.setdefault(ac, f)
        if not reqs:
            fails.append("%s (%s) cites no REQ in its row — the chain FR → REQ → AC needs it." % (ac, f))
    covered = {r for _, reqs, _ in acs for r in reqs}
    no_ac = sorted({r["ID"] for r in reg.live(rows)} - covered, key=reg.req_num)
    if no_ac:
        fails.append("%d requirement(s) have no acceptance criterion row (`| AC-### | REQ-### | Given … |`): %s%s"
                     % (len(no_ac), ", ".join(no_ac[:40]), " …" if len(no_ac) > 40 else ""))
    texts = "\n".join(read(p) for p in reg.spec_files(root))
    stray = sorted(set(reg.AC_RE.findall(texts)) - set(seen))
    if stray:
        warns.append("AC IDs mentioned but never defined in an AC table row: %s" % ", ".join(stray[:20]))
    if "AC-NEW" in texts:
        fails.append("Acceptance criteria still marked AC-NEW — run: register.py number-ac <D>")
    odd = sorted(set(re.findall(r"\bAC-[A-Z0-9]+\.\d+\b", texts)))
    if odd:
        fails.append("Old-style AC IDs (use AC-001, AC-002 … — atlasctl and the gates only read that form): %s" % ", ".join(odd[:10]))
    if acs:
        print("Acceptance criteria: %d, covering %d requirement(s)." % (len(seen), len(covered)))


def check_modules(root, rows, fails, warns):
    path = os.path.join(root, "MODULES.md")
    if not os.path.exists(path):
        fails.append("MODULES.md is missing (template: <skill>/templates/MODULES.md).")
        return {}
    mods = reg.modules(root)
    if not mods:
        fails.append("MODULES.md has no rows in a `| Module | Name | Rigour | Paths | Signals | Reason |` table.")
        return {}
    header = [h.strip("* ").lower() for h in next(iter(mods.values()))["header"]]
    if header[:6] != MODULES_HEADER:
        fails.append("MODULES.md columns must be exactly `| Module | Name | Rigour | Paths | Signals | Reason |` (found: %s)."
                     % " | ".join(header))
    for mid, m in mods.items():
        if m["proposed"] not in LEVELS:
            fails.append("MODULES.md %s: Rigour must be Light, Standard or Critical (found '%s')." % (mid, m["proposed"]))
        if not m["paths"]:
            fails.append("MODULES.md %s: Paths is empty — write code globs, or `?` if not known yet." % mid)
        if not m["reason"]:
            fails.append("MODULES.md %s: Reason is empty — say why this rigour level." % mid)
        if m["proposed"] == "Critical" and not m["signals"].strip("-— "):
            warns.append("MODULES.md %s is Critical but lists no signals (rigour.md)." % mid)
        cells = " ".join([m["name"], m["paths"], m["signals"], m["reason"]])
        if re.search(r"\b(REQ|FR|AC|WP)-\d+", cells):
            warns.append("MODULES.md %s cites REQ/FR/AC/WP IDs — remove them; `atlasctl impact` would treat the whole module as affected." % mid)
    act = reg.active(rows)
    used = {r["Module"] for r in act if r["Module"]}
    empty = [m for m in mods if m not in used]
    if empty:
        warns.append("Modules with no requirements: %s" % ", ".join(empty))
    unconf = [m for m, v in mods.items() if not v["confirmed"]]
    print("Modules: %s" % ", ".join("%s %s (%s%s)" % (k, v["name"], v["rigour"], "" if v["confirmed"] else ", proposed")
                                    for k, v in mods.items()))
    if unconf:
        warns.append("Rigour not yet confirmed by the user for %s — ask, then `atlasctl rigour <M#> <Level> --reason \"…\"` (gate G2 needs it)."
                     % ", ".join(unconf))
    return mods


def module_text(root, mid, core):
    """Same lookup as gate G2: technical/mNN-*.md, else the '#…' section of TECHNICAL.md whose heading names the module."""
    num = int(mid[1:])
    for f in sorted(glob.glob(os.path.join(root, "technical", "m%02d-*.md" % num))) + \
            sorted(glob.glob(os.path.join(root, "technical", "m%d-*.md" % num))):
        return read(f)
    m = re.search(r"^#{2,4} .*\b%s\b.*$" % mid, core, flags=re.M)
    if not m:
        return ""
    level = len(m.group(0)) - len(m.group(0).lstrip("#"))
    rest = core[m.end():]
    end = re.search(r"^#{2,%d} " % level, rest, flags=re.M)
    return m.group(0) + "\n" + (rest[: end.start()] if end else rest)


def check_depth(root, mods, core, fails, warns):
    for mid, m in mods.items():
        text = module_text(root, mid, core)
        if not text:
            fails.append("%s %s has no spec: expected technical/m%02d-*.md or a TECHNICAL.md heading naming %s (e.g. `### 6.1 %s %s`)."
                         % (mid, m["name"], int(mid[1:]), mid, mid, m["name"]))
            continue
        first = text.strip().split("\n", 1)[0]
        if not text.startswith("#") and re.search(r"\bM\d+\b", first) and mid not in first:
            warns.append("%s: the spec found for it starts with '%s' — check the heading." % (mid, first[:60]))
        low = text.lower()
        if m["rigour"] == "Critical":
            miss = [w for w, ok in (("threat notes", "threat" in low or "abuse" in low),
                                    ("failure/rollback behaviour", "rollback" in low or "failure" in low)) if not ok]
            if miss:
                fails.append("%s %s is Critical but its spec lacks %s (rigour.md; gate G2)." % (mid, m["name"], " and ".join(miss)))
            if "audit" not in low:
                warns.append("%s %s is Critical — rigour.md also asks for an audit trail." % (mid, m["name"]))
            if "edge" not in low and "error" not in low:
                warns.append("%s %s is Critical — list every error and edge case." % (mid, m["name"]))
        elif m["rigour"] == "Standard" and "|" not in text:
            warns.append("%s %s is Standard — add the data model / flows / API contracts (rigour.md)." % (mid, m["name"]))


def check_questions(root, docs, fails, warns):
    """Open-question tables must carry Blocking (yes/no) and Status — gate G2 reads them."""
    n_open = n_block = 0
    for path in (os.path.join(root, "TECHNICAL.md"), os.path.join(root, "DECISIONS.md")):
        if path not in docs:
            continue
        for t in reg.md.tables(docs[path]):
            oq_rows = [r for r in t.rows if r and re.match(r"^OQ-\d+", r[0].strip("* "))]
            if not oq_rows:
                continue
            cb, cs = t.col("blocking"), t.col("status")
            if cb is None or cs is None:
                fails.append("%s: open-question table (line %d) needs `Blocking` and `Status` columns."
                             % (rel(path, root), t.line))
                continue
            for r in oq_rows:
                b = r[cb].strip().lower() if cb < len(r) else ""
                s = r[cs].strip().lower() if cs < len(r) else ""
                if b not in ("yes", "no"):
                    warns.append("%s %s: Blocking should be `yes` or `no` (found '%s')." % (rel(path, root), r[0], b))
                if not any(w in s for w in ("resolved", "closed", "answered", "done")):
                    n_open += 1
                    n_block += b == "yes"
    print("Open questions: %d open, %d blocking." % (n_open, n_block))
    if n_block:
        warns.append("%d blocking open question(s) — gate G2 fails on them for Standard/Critical projects. Ask the user "
                     "(client-only questions go to Alice's QUESTIONS.md)." % n_block)


def check_refs(root, docs, fails):
    """Every OQ-/ASM-T/AD- cited must be defined (a table row or heading) in DECISIONS.md or TECHNICAL.md."""
    home = docs.get(os.path.join(root, "DECISIONS.md"), "") + "\n" + docs.get(os.path.join(root, "TECHNICAL.md"), "")
    defined = set(re.findall(r"^\s*(?:\|\s*\**|#{2,5}\s+)((?:OQ|ASM-T|AD)-?\d+)", home, flags=re.M))
    allt = "\n".join(docs.values())
    cited = set(re.findall(r"\b((?:OQ-|AD-|ASM-T)\d+)\b", allt))
    stray = sorted(cited - defined)
    if stray:
        fails.append("Cited but never defined (need a table row or heading in DECISIONS.md, or TECHNICAL.md for a small system): %s"
                     % ", ".join(stray[:30]))
    home_alice = sorted(set(re.findall(r"^\s*\|\s*\**(ASM-\d+)", home, flags=re.M)))
    if home_alice:
        fails.append("ASM-## is Alice's ID kind (cite hers, never define one); technical assumptions are ASM-T1, ASM-T2 … "
                     "(defined here: %s)." % ", ".join(home_alice[:10]))


def check_overview(text, fails, warns):
    if not mermaid_blocks(text):
        warns.append("OVERVIEW.md has no diagrams — add at least the system and build-order diagrams.")
    leaks = []
    if re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/\w", text):
        leaks.append("HTTP endpoints")
    if re.search(r"\bSELECT\b.+\bFROM\b|\bCREATE TABLE\b", text, flags=re.I):
        leaks.append("SQL")
    other_code = sorted({m for m in re.findall(r"^```(\w*)", text, flags=re.M) if m and m != "mermaid"})
    if other_code:
        leaks.append("code blocks (%s)" % ", ".join(other_code))
    if leaks:
        fails.append("OVERVIEW.md contains technical content: %s." % ", ".join(leaks))
    inline = [c for c in re.findall(r"`([^`\n]+)`", text) if re.search(r"[_./(){}]|^[a-z]+[A-Z]", c)]
    if len(inline) > 3:
        warns.append("OVERVIEW.md has %d technical-looking code spans (e.g. `%s`) — use plain words." % (len(inline), inline[0]))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args else 2)
    root = os.path.abspath(args[0])
    stage = args[args.index("--stage") + 1] if "--stage" in args else "all"
    if stage not in ("extract", "spec", "all"):
        sys.exit("Unknown stage: %s (extract | spec | all)" % stage)
    if os.path.basename(root) != "design":
        print("note: expected the project's design folder (<P>/design); got %s" % root)
    fails, warns = [], []

    _, rows = reg.load(root)
    f, w, stats = reg.lint(root, strict=stage != "extract")
    print(stats[0])
    fails += f
    warns += w
    f, w = reg.ledger(root)
    fails += f
    warns += w

    if stage != "extract":
        tech = {}
        core_path = os.path.join(root, "TECHNICAL.md")
        if os.path.exists(core_path):
            tech[core_path] = read(core_path)
        for p in sorted(glob.glob(os.path.join(root, "technical", "*.md"))):
            tech[p] = read(p)
        docs = dict(tech)
        for n in ("DECISIONS.md", "OVERVIEW.md", "MODULES.md"):
            p = os.path.join(root, n)
            if os.path.exists(p):
                docs[p] = read(p)
        core = tech.get(core_path)
        if core is None:
            fails.append("Missing TECHNICAL.md")
        else:
            check_spec(root, rows, tech, fails, warns)
            check_acs(root, rows, fails, warns)
        mods = check_modules(root, rows, fails, warns)
        if core is not None and mods:
            check_depth(root, mods, core, fails, warns)
            absent = [m for m in mods if not re.search(r"\b%s\b" % m, core)]
            if absent:
                warns.append("Modules in MODULES.md but not mentioned in TECHNICAL.md: %s" % ", ".join(absent))
        check_questions(root, docs, fails, warns)
        check_refs(root, docs, fails)
        overview = docs.get(os.path.join(root, "OVERVIEW.md"))
        if stage == "all":
            if overview is None:
                fails.append("Missing OVERVIEW.md")
            if not os.path.exists(os.path.join(root, "_work", "traceability.md")):
                warns.append("No _work/traceability.md — run register.py trace.")
        if overview is not None:
            check_overview(overview, fails, warns)
        check_docs(root, docs, fails, warns)

    reg.report(fails, warns)


if __name__ == "__main__":
    main()
