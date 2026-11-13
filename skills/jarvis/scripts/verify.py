#!/usr/bin/env python3
"""Verify a JARVIS plan folder (<P>/plan). Exit code 1 if anything FAILs (WARNs do not fail).

Usage: verify.py <plan_dir> [--stage plan|audit|all] [--repo <code_repository_root>]

  plan   PLAN.md has its `| Version | v1.0 — YYYY-MM-DD |` header row and tables in the format Atlas reads; every
         live REQ is in a work package's REQs column or in the `| REQ | Evidence |` table of requirements already
         built; dependencies exist and have no cycles; every phase has a goal; Critical-module work packages are
         XS/S/M and end in a review checkpoint; briefs name WP branches; links and placeholders are clean
  audit  every REQ has an audit row in AUDIT.md / audit/*.md with a valid status and real `path:line` evidence
  all    (default) plan + audit when an audit exists

The requirements register and modules come from the design folder (<plan_dir>/../design), via Stark's register.py.
`atlas finish jarvis` (and `atlas finish stark` on the small track) runs exactly `verify.py <P>/plan`. These checks
mirror what gate G3 reads, so a PASS here means G3 can parse the plan.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "stark", "scripts")))
import register as reg  # noqa: E402  (Stark's register tools; also puts <plugin>/lib on sys.path)

md = reg.md
BUDGETS_KB = {"PLAN.md": 40, "AUDIT.md": 30}
MODULE_BUDGET_KB = 35
MAX_CELL = 600
MAX_LINE = 1500
WP_COLUMNS = ["wp", "title", "phase", "module", "reqs", "depends on", "size", "status"]
PLANNED_STATUS = ("todo", "blocked", "deferred")   # the planned state; real progress is inferred by Atlas
VERSION_RE = re.compile(r"\|\s*\**Version\**\s*\|\s*\**\s*(v\d+(?:\.\d+)*)", flags=re.I)  # what `atlas finish` reads
SIZES = ("XS", "S", "M", "L")
AUDIT_STATUSES = (("done", ("done", "built", "✅")), ("partial", ("partial", "🟡")),
                  ("missing", ("missing", "not started", "not built", "❌")),
                  ("deviates", ("deviat", "⚠")), ("unclear", ("unclear", "❔", "unknown")))
EVIDENCE_RE = re.compile(r"([\w@./+\-\[\]()]+\.[A-Za-z0-9]{1,8}):(\d+)(?:\s*[-–]\s*(\d+))?")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def rel(path, root):
    return os.path.relpath(path, root)


def mermaid_blocks(text):
    return re.findall(r"```mermaid\s*\n(.*?)```", text, flags=re.S)


def norm(h):
    return h.strip("* ").lower()


# ------------------------------------------------------------------ documents
def check_docs(root, docs, fails, warns):
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
            elif body[0].split()[0] in ("flowchart", "graph") and re.search(r"(?:^|\s)[A-Za-z]\w*-\w+\s*(?:\[|\(|\{|-->)", blk):
                warns.append("%s: diagram #%d may use hyphens in node IDs (use WP_01, not WP-01)." % (name, i))
        for target in re.findall(r"\]\(([^)\s]+)\)", re.sub(r"```.*?```", "", text, flags=re.S)):
            if re.match(r"[a-z]+:|#", target):
                continue
            file_part = target.split("#")[0]
            if file_part and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), file_part))):
                fails.append("%s: broken link → %s" % (name, target))
        size_kb = len(text.encode("utf-8")) / 1024.0
        base = os.path.basename(path)
        folder = os.path.basename(os.path.dirname(path))
        budget = BUDGETS_KB.get(base) if os.path.dirname(path) == root else (MODULE_BUDGET_KB if folder in ("audit", "briefs") else None)
        if budget and size_kb > budget:
            warns.append("%s is %d KB (budget %d KB) — full detail only for the current and next phase." % (name, size_kb, budget))
        longest = max([len(ln) for ln in text.split("\n")] + [0])
        fat = sum(1 for ln in text.split("\n") if ln.lstrip().startswith("|") for c in reg.split_row(ln) if len(c) > MAX_CELL)
        if longest > MAX_LINE or fat:
            warns.append("%s has %d table cell(s) over %d characters — move detail below the table." % (name, fat, MAX_CELL))


# ------------------------------------------------------------------ plan
def parse_plan(text, fails, warns):
    """Phase rows and WP rows, read the way atlasctl.read_plan reads them (plus format checks)."""
    phases, wps = [], []
    for t in md.tables(text):
        names = [norm(h) for h in t.headers]
        if t.col("wp") is not None and t.col("phase") is not None and t.col("title") is not None:
            idx = [next((i for i, n in enumerate(names) if n == c or n.startswith(c)), None) for c in WP_COLUMNS]
            if None in idx or idx != sorted(idx):
                fails.append("Work-package table (line %d) must have the columns `| WP | Title | Phase | Module | REQs | "
                             "Depends on | Size | Status |` in this order (found: %s)." % (t.line, " | ".join(t.headers)))
                continue
            cw, ct, cph, cm, cr, cd, cz, cs = idx
            for r in t.rows:
                g = lambda i: (r[i].strip() if i < len(r) else "")  # noqa: E731
                wid = g(cw).strip("* ")
                if not re.match(r"^WP-\d+$", wid):
                    if wid:
                        fails.append("Work-package row '%s' — the first cell must be the ID alone, e.g. WP-07." % wid[:40])
                    continue
                wps.append({"id": wid, "title": g(ct), "phase": (re.findall(r"P\d+", g(cph)) or [g(cph)])[0],
                            "modules": re.findall(r"\bM\d+\b", g(cm)), "module_cell": g(cm),
                            "reqs": sorted(reg.expand_ranges(g(cr))),
                            "depends": [x for x in md.expand_ranges(g(cd)) if x.startswith("WP-")],
                            "size": g(cz).strip("*` ").upper(), "status": g(cs).strip("*` ").lower(),
                            "row": "|".join(r)})
        elif t.col("phase") is not None and t.col("goal") is not None:
            cp, cg, cw, cgate, ctg = t.col("phase"), t.col("goal"), t.col("work packages", "wps"), t.col("gate"), t.col("target")
            if cw is None or cgate is None:
                warns.append("Phase table (line %d) should have `Work packages` and `Gate to start` columns." % t.line)
            if ctg is None:
                warns.append("Phase table (line %d) has no `Target` column (YYYY-MM-DD or blank) — Atlas uses it to spot slippage." % t.line)
            for r in t.rows:
                g = lambda i: (r[i].strip() if i is not None and i < len(r) else "")  # noqa: E731
                m = re.match(r"^\s*\**(P\d+)\b", g(cp))
                if not m:
                    if g(cp) and not g(cp).lower().startswith("gated"):
                        warns.append("Phase row '%s' does not start with a phase ID (P0, P1 …) — atlasctl ignores it." % g(cp)[:40])
                    continue
                phases.append({"id": m.group(1), "goal": g(cg), "wps": md.expand_ranges(g(cw)), "target": g(ctg)})
    return phases, wps


def find_cycle(graph):
    color, stack = {}, []

    def visit(n):
        color[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if color.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if color.get(m, 0) == 0 and m in graph:
                c = visit(m)
                if c:
                    return c
        stack.pop()
        color[n] = 2
        return []
    for n in sorted(graph):
        if color.get(n, 0) == 0:
            c = visit(n)
            if c:
                return c
    return []


def built_rows(text):
    """Rows of PLAN.md's optional `| REQ | Evidence |` table (requirements the audit found already built):
    list of (REQ ids in the first cell, evidence cell). Read the way gate G3 reads it."""
    out = []
    for t in md.tables(text):
        if t.col("req") != 0 or t.col("evidence") is None:
            continue
        ce = t.col("evidence")
        for r in t.rows:
            ids = sorted(reg.expand_ranges(r[0] if r else ""), key=reg.req_num)
            if ids:
                out.append((ids, r[ce].strip() if ce < len(r) else ""))
    return out


def check_built(root, built, allreq, wp_reqs, repo, fails, warns):
    """Already-built requirements count as covered only with evidence: `path:line`, or the audit file that holds it."""
    audit = audit_rows(root)[0]
    no_ev, soft, not_done, bad = [], [], [], []
    cache = {}
    for ids, cell in built:
        label = ids[0] if len(ids) == 1 else "%s–%s" % (ids[0], ids[-1])
        ev = EVIDENCE_RE.findall(cell.replace("`", " "))
        cites_audit = bool(re.search(r"(?i)\baudit(/|\.md)", cell))
        if not cell.strip("—-–? "):
            no_ev.append(label)
        elif not ev and not cites_audit:
            soft.append(label)
        for rid in ids:
            if rid in audit and audit[rid] != "done":
                not_done.append("%s (audit: %s)" % (rid, audit[rid] or "?"))
            elif cites_audit and not ev and rid not in audit:
                not_done.append("%s (no audit row)" % rid)
        if repo:
            for fpath, a, b in ev:
                problem = evidence_problem(repo, fpath, a, b, cache)
                if problem:
                    bad.append("%s: %s" % (label, problem))
    if no_ev:
        fails.append("`| REQ | Evidence |` rows with no evidence — only code read and cited makes a requirement built: %s"
                     % ", ".join(no_ev[:20]))
    if not_done:
        fails.append("Listed as already built, but the audit does not say `done`: %s — give them a work package."
                     % ", ".join(not_done[:20]))
    if bad:
        fails.append("%d evidence reference(s) in the already-built table do not exist in the repository: %s"
                     % (len(bad), "; ".join(bad[:10])))
    if soft:
        warns.append("Already-built rows whose evidence is neither `path:line` nor an audit file: %s" % ", ".join(soft[:20]))
    if built and not repo and any(EVIDENCE_RE.search(cell.replace("`", " ")) for _, cell in built):
        warns.append("Evidence paths in the already-built table were not checked against the code — link the repository "
                     "(`atlas link-repo`) or pass --repo <code repository root>.")
    listed = {r for ids, _ in built for r in ids}
    ghost = sorted(listed - allreq, key=reg.req_num)
    if ghost:
        fails.append("The already-built table cites REQ IDs that are not in the register: %s" % ", ".join(ghost[:30]))
    both = sorted(listed & wp_reqs, key=reg.req_num)
    if both:
        warns.append("Requirements both listed as already built and scheduled in a work package (a partial one "
                     "belongs only in its work package): %s" % ", ".join(both[:30]))
    return listed


def check_plan(root, design, rows, text, fails, warns, repo=None):
    phases, wps = parse_plan(text, fails, warns)
    if not VERSION_RE.search(text[:3000]):
        fails.append("PLAN.md has no `| Version | v1.0 — YYYY-MM-DD |` row in its header table — `atlas finish` reads "
                     "the version from it.")
    if not wps:
        fails.append("No work-package table found in PLAN.md (header `| WP | Title | Phase | Module | REQs | Depends on | Size | Status |`).")
        return
    if not phases:
        fails.append("No phase table found in PLAN.md (header `| Phase | Goal … | Work packages | Gate to start | Target | Status |`, rows P0, P1 …).")
    ids = [w["id"] for w in wps]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        fails.append("Duplicate work-package IDs: %s" % ", ".join(dup))
    pids = [p["id"] for p in phases]
    if len(set(pids)) != len(pids):
        fails.append("Duplicate phase IDs in the phase table.")
    nogoal = [p["id"] for p in phases if not p["goal"].strip() or p["goal"].strip() in ("—", "-")]
    if nogoal:
        fails.append("Phases without a goal (exit criterion): %s" % ", ".join(nogoal))
    badt = [p["id"] for p in phases if p["target"].strip("—- ") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p["target"].strip())]
    if badt:
        fails.append("Phase Target must be YYYY-MM-DD or blank: %s" % ", ".join(badt))
    orphan = sorted({w["phase"] for w in wps} - set(pids))
    if orphan and phases:
        fails.append("Work packages name phases that are not in the phase table: %s" % ", ".join(orphan))
    for p in phases:
        listed = set(p["wps"])
        actual = {w["id"] for w in wps if w["phase"] == p["id"]}
        if listed and listed != actual:
            warns.append("Phase %s lists %s but the work-package table puts %s in it."
                         % (p["id"], ", ".join(sorted(listed)) or "—", ", ".join(sorted(actual)) or "—"))

    # requirements coverage — the REQs column only (what gate G3 reads)
    live = {r["ID"] for r in reg.live(rows)}
    allreq = {r["ID"] for r in reg.active(rows)}
    removed = {r["ID"] for r in rows if r["_removed"]}
    covered = {r for w in wps for r in w["reqs"]}
    built = check_built(root, built_rows(text), allreq | removed, covered, repo, fails, warns)
    miss = sorted(live - covered - built, key=reg.req_num)
    if miss:
        fails.append("%d live requirement(s) are in no work package's REQs column (and not in the `| REQ | Evidence |` "
                     "table of requirements already built): %s%s"
                     % (len(miss), ", ".join(miss[:50]), " …" if len(miss) > 50 else ""))
    ghost = sorted(covered - allreq - removed, key=reg.req_num)
    if ghost:
        fails.append("Work packages cite REQ IDs that are not in the register: %s" % ", ".join(ghost[:30]))
    if covered & removed:
        warns.append("The plan still schedules removed requirements: %s" % ", ".join(sorted(covered & removed, key=reg.req_num)[:30]))
    dead = sorted((covered & allreq) - live, key=reg.req_num)
    if dead:
        warns.append("The plan schedules requirements marked out of scope / deferred / rejected: %s" % ", ".join(dead[:30]))

    # dependencies
    graph = {w["id"]: w["depends"] for w in wps}
    unknown = sorted({d for w in wps for d in w["depends"] if d not in graph})
    if unknown:
        fails.append("Work packages depend on IDs that do not exist: %s" % ", ".join(unknown[:20]))
    cyc = find_cycle(graph)
    if cyc:
        fails.append("Dependency cycle in the plan: %s" % " → ".join(cyc))
    order = {p: i for i, p in enumerate(pids)}
    later = ["%s (%s) needs %s (%s)" % (w["id"], w["phase"], d, graph_phase) for w in wps for d in w["depends"]
             for graph_phase in [next((x["phase"] for x in wps if x["id"] == d), None)]
             if graph_phase in order and w["phase"] in order and order[graph_phase] > order[w["phase"]]]
    if later:
        warns.append("Work packages depend on work in a later phase: %s" % "; ".join(later[:8]))

    # modules, sizes, statuses, rigour
    mods = reg.modules(design)
    for w in wps:
        badm = [m for m in w["modules"] if m not in mods]
        if mods and badm:
            fails.append("%s names modules that are not in MODULES.md: %s" % (w["id"], ", ".join(badm)))
        if not w["modules"] and "X" not in w["module_cell"]:
            warns.append("%s names no module (M# or X)." % w["id"])
        legacy = w["id"] == "WP-00" and w["status"] == "done"
        if legacy:
            warns.append("WP-00 is an old-style baseline row — list requirements that are already built in a "
                         "`| REQ | Evidence |` table instead (gate G3 counts them as covered) and delete the row.")
        if w["size"] not in SIZES and not legacy:
            fails.append("%s: Size must be XS, S, M or L (found '%s')." % (w["id"], w["size"]))
        elif w["size"] == "L":
            warns.append("%s is size L — split it if you can (one agent session each)." % w["id"])
        if w["status"] not in PLANNED_STATUS and not legacy:
            fails.append("%s: Status '%s' — PLAN.md holds the planned state only: todo, blocked or deferred. Atlas infers "
                         "real progress from branches, pull requests and commits (`atlas wp` to correct it)."
                         % (w["id"], w["status"]))
        if not w["reqs"]:
            warns.append("%s lists no REQs (fine for a spike; otherwise cite what it delivers)." % w["id"])
    crit = {m for m, v in mods.items() if v["rigour"] == "Critical"}
    bad = []
    for w in wps:
        if set(w["modules"]) & crit and not (w["id"] == "WP-00" and w["status"] == "done"):
            small = w["size"] in ("XS", "S", "M")
            review = "review" in w["row"].lower()
            if not (small and review):
                bad.append("%s (%s)" % (w["id"], ", ".join(x for x, ok in (("size %s" % (w["size"] or "?"), small),
                                                                           ("no review checkpoint", review)) if not ok)))
    if bad:
        fails.append("Critical-module work packages must be XS/S/M and end in a review checkpoint (put 'review' in the "
                     "title, e.g. '… + review'): %s" % "; ".join(bad[:10]))
    for m, v in mods.items():
        n = sum(1 for w in wps if m in w["modules"])
        if v["rigour"] == "Light" and n > 2:
            warns.append("%s is Light but has %d work packages — a Light module needs 1–2." % (m, n))
    unconf = [m for m, v in mods.items() if not v["confirmed"]]
    if unconf:
        warns.append("Rigour not confirmed for %s — granularity used the proposed level; the user confirms with "
                     "`atlas rigour --accept [M2=Critical …]` (gate G2 needs it)." % ", ".join(unconf))

    # acceptance criteria referenced by the plan
    defined = {a for a, _, _ in reg.ac_rows(design)}
    stray = sorted(set(reg.AC_RE.findall(text)) - defined)
    if stray:
        warns.append("The plan cites AC IDs not defined in the design: %s" % ", ".join(stray[:20]))

    by_size = {}
    for w in wps:
        by_size[w["size"] or "?"] = by_size.get(w["size"] or "?", 0) + 1
    print("Plan: %d phase(s), %d work package(s) (%s), %d of %d live REQs covered%s."
          % (len(phases), len(wps), ", ".join("%s %d" % kv for kv in sorted(by_size.items())),
             len(live & (covered | built)), len(live),
             (" (%d already built)" % len(live & built - covered)) if built else ""))
    return wps


def check_briefs(root, wps, warns):
    for p in sorted(glob.glob(os.path.join(root, "briefs", "*.md"))):
        text = read(p)
        named = sorted(set(re.findall(r"\bWP-\d+\b", text)) & {w["id"] for w in wps})
        branched = {b.upper() for b in re.findall(r"\b(WP-\d+)-[a-z0-9][a-z0-9-]*\b", text)}
        nob = [w for w in named if w not in branched]
        if nob:
            warns.append("%s: no branch name like `%s-short-title` for %s — Atlas matches commits by branch." % (rel(p, root), nob[0], ", ".join(nob)))
        if re.search(r"(?i)update .*PLAN\.md.*(status|done)", text):
            warns.append("%s tells agents to edit PLAN.md statuses — Atlas infers progress from branches, pull requests "
                         "and commits; PLAN.md is not edited as work happens." % rel(p, root))


# ------------------------------------------------------------------ audit
def norm_status(cell):
    c = cell.lower()
    for name, keys in AUDIT_STATUSES:
        if any(k in c for k in keys):
            return name
    return None


_REPO_FILES = {}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target", "vendor", ".cache"}


def line_count(path):
    try:
        with open(path, "rb") as f:
            return f.read().count(b"\n") + 1
    except OSError:
        return None


def suffix_matches(repo, fpath):
    if repo not in _REPO_FILES:
        index = {}
        for dirpath, dirnames, filenames in os.walk(repo):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                index.setdefault(fn, []).append(os.path.join(dirpath, fn))
        _REPO_FILES[repo] = index
    want = "/" + fpath.lstrip("./")
    return [p for p in _REPO_FILES[repo].get(os.path.basename(fpath), []) if ("/" + os.path.relpath(p, repo)).endswith(want)]


def linked_repo(root):
    """A local code repository path from <P>/atlas.json (first repo with a path), else None."""
    try:
        meta = json.loads(read(os.path.join(os.path.dirname(root), "atlas.json")))
    except (OSError, ValueError):
        return None
    for r in meta.get("repos", []):
        if r.get("path") and os.path.isdir(r["path"]):
            return r["path"]
    return None


def evidence_problem(repo, fpath, a, b, cache, shortened=None):
    """'' when `fpath:a[-b]` exists in the repository, else a short description of what is wrong."""
    if fpath.count("(") != fpath.count(")"):
        fpath = fpath.lstrip("(").rstrip(")")
    full = os.path.join(repo, fpath)
    if full not in cache:
        cache[full] = line_count(full)
    n = cache[full]
    if n is None:
        hits = suffix_matches(repo, fpath)
        if len(hits) != 1:
            return "%s (%s)" % (fpath, "no such file" if not hits else "ambiguous: %d files match" % len(hits))
        if shortened is not None:
            shortened.add(fpath)
        n = cache.setdefault(hits[0], line_count(hits[0]))
    if n is None:
        return "%s (unreadable)" % fpath
    if int(b or a) > n:
        return "%s:%s (file has %d lines)" % (fpath, b or a, n)
    return ""


def audit_rows(root):
    """(REQ → normalised status or None, REQ → evidence cell) from AUDIT.md / audit/*.md."""
    files = sorted(glob.glob(os.path.join(root, "audit", "*.md")))
    main = os.path.join(root, "AUDIT.md")
    if not files and os.path.exists(main):
        files = [main]
    found, cells_by = {}, {}
    for path in files:
        for header, trows, _ in reg.generic_tables(read(path).split("\n")):
            names = [h.strip().lower() for h in header]
            if "status" not in names or not names[0].startswith(("req", "id")):
                continue
            s_i = names.index("status")
            e_i = next((i for i, n in enumerate(names) if n.startswith("evidence")), None)
            for _, cells in trows:
                m = reg.REQ_RE.search(cells[0]) if cells else None
                if not m or s_i >= len(cells):
                    continue
                found[m.group(0)] = norm_status(cells[s_i])
                cells_by[m.group(0)] = cells[e_i] if e_i is not None and e_i < len(cells) else " ".join(cells[s_i + 1:])
    return found, cells_by


def check_audit(root, rows, repo, fails, warns):
    if not glob.glob(os.path.join(root, "audit", "*.md")) and not os.path.exists(os.path.join(root, "AUDIT.md")):
        fails.append("No audit files found (expected AUDIT.md and audit/<module>.md).")
        return
    found, cells_by = audit_rows(root)
    no_status, no_evidence, bad_evidence, shortened = [], [], [], set()
    cache = {}
    for rid, status in found.items():
        if status is None:
            no_status.append(rid)
            continue
        if status == "missing":
            continue
        ev = EVIDENCE_RE.findall(cells_by[rid].replace("`", " "))
        if not ev and status != "unclear":
            no_evidence.append(rid)
        if repo is None:
            continue
        for fpath, a, b in ev:
            problem = evidence_problem(repo, fpath, a, b, cache, shortened)
            if problem:
                bad_evidence.append("%s: %s" % (rid, problem))
    act = [r["ID"] for r in reg.live(rows)]
    missing = [r for r in act if r not in found]
    if missing:
        fails.append("%d requirement(s) have no audit row: %s%s" % (len(missing), ", ".join(missing[:40]), " …" if len(missing) > 40 else ""))
    if no_status:
        fails.append("Audit rows with an unrecognised status (use done/partial/missing/deviates/unclear): %s" % ", ".join(no_status[:25]))
    if no_evidence:
        fails.append("%d audit row(s) claim an implementation but cite no `path:line` evidence: %s" % (len(no_evidence), ", ".join(no_evidence[:30])))
    if bad_evidence:
        fails.append("%d evidence reference(s) do not exist in the repository: %s" % (len(bad_evidence), "; ".join(bad_evidence[:15])))
    if shortened:
        warns.append("Abbreviated evidence paths (resolved by filename) — write full paths from the repository root, e.g. %s"
                     % ", ".join(sorted(shortened)[:5]))
    if repo is None:
        warns.append("Evidence paths were not checked against the code — pass --repo <code repository root>.")
    tally = {}
    for rid in act:
        s = found.get(rid)
        if s:
            tally[s] = tally.get(s, 0) + 1
    if act and tally:
        score = 100.0 * (tally.get("done", 0) + 0.5 * tally.get("partial", 0)) / len(act)
        print("Audit: %s — %.0f%% complete (done = 1, partial = ½)."
              % (", ".join("%d %s" % (tally[k], k) for k, _ in AUDIT_STATUSES if k in tally), score))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args else 2)
    root = os.path.abspath(args[0])
    stage = args[args.index("--stage") + 1] if "--stage" in args else "all"
    repo = os.path.abspath(args[args.index("--repo") + 1]) if "--repo" in args else None
    if stage not in ("plan", "audit", "all"):
        sys.exit("Unknown stage: %s (plan | audit | all)" % stage)
    design = os.path.join(os.path.dirname(root), "design")
    if os.path.basename(root) != "plan":
        print("note: expected the project's plan folder (<P>/plan); got %s" % root)
    fails, warns = [], []
    _, rows = reg.load(design)
    plan_path = os.path.join(root, "PLAN.md")
    has_audit = os.path.exists(os.path.join(root, "AUDIT.md")) or bool(glob.glob(os.path.join(root, "audit", "*.md")))

    docs = {}
    for p in [plan_path, os.path.join(root, "AUDIT.md")] + sorted(glob.glob(os.path.join(root, "audit", "*.md"))) + \
            sorted(glob.glob(os.path.join(root, "briefs", "*.md"))):
        if os.path.exists(p):
            docs[p] = read(p)
    if stage in ("plan", "all"):
        if plan_path not in docs:
            fails.append("Missing PLAN.md")
        else:
            wps = check_plan(root, design, rows, docs[plan_path], fails, warns, repo or linked_repo(root))
            if wps:
                check_briefs(root, wps, warns)
    if stage == "audit" or (stage == "all" and has_audit):
        check_audit(root, rows, repo or linked_repo(root), fails, warns)
    if stage == "audit":
        docs = {p: t for p, t in docs.items() if "audit" in rel(p, root).lower()}
    check_docs(root, docs, fails, warns)
    reg.report(fails, warns)


if __name__ == "__main__":
    main()
