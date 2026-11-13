"""Gate checks G1–G5 (see gates.md). Each check returns a dict: key, check, result (pass|fail|ask|n/a), detail.

Scaling: (S) checks apply when the project is not Small or any module is Standard/Critical; (C) checks apply only
where a Critical module is involved. 'ask' checks become pass/fail when the user answers (--answer key=yes|no).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import atlasctl as A
import mdtables as md

FR_DONE = ("out of scope", "rejected", "deferred")
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "GitHub token"),
    (re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b"), "Stripe live key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "Google API key"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{32,}\b"), "API secret key"),
    (re.compile(r"(?i)\b(password|passwd|secret|api_?key|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"), "hard-coded secret"),
]


def R(key: str, check: str, ok: Optional[bool], detail: str = "", ask: bool = False) -> Dict[str, Any]:
    if ask:
        res = "ask"
    elif ok is None:
        res = "n/a"
    else:
        res = "pass" if ok else "fail"
    return {"key": key, "check": check, "result": res, "detail": detail}


def short(ids: List[str], n: int = 12) -> str:
    ids = sorted(ids)
    return ", ".join(ids[:n]) + (" … (+%d)" % (len(ids) - n) if len(ids) > n else "")


# ───────── document readers ─────────

def frs(p: A.Project) -> Dict[str, Dict[str, str]]:
    out = {}
    for t in md.read_tables(p.path / "discovery" / "PRD.md"):
        ci, cs, cp = t.col("id"), t.col("status"), t.col("priority")
        if ci is None or cs is None:
            continue
        for r in t.rows:
            rid = r[ci].strip("* ") if ci < len(r) else ""
            if re.match(r"^FR-\d+$", rid):
                out[rid] = {"status": (r[cs] if cs < len(r) else "").strip().lower(),
                            "priority": (r[cp] if cp is not None and cp < len(r) else "").strip().lower()}
    return out


def reqs(p: A.Project) -> Dict[str, Dict[str, Any]]:
    """REQ rows from Stark's register and design documents: id → {links, status}."""
    out: Dict[str, Dict[str, Any]] = {}
    files = [p.path / "design" / "_work" / "requirements.md"] + sorted((p.path / "design").glob("*.md")) + \
        sorted((p.path / "design" / "technical").glob("*.md"))
    for f in files:
        for t in md.read_tables(f):
            cs = t.col("status")
            for r in t.rows:
                own = md.ids_in(r[0]) if r else []
                if len(own) != 1 or not own[0].startswith("REQ-"):
                    continue
                if r[0].strip().startswith("~~"):
                    out.setdefault(own[0], {"links": set(), "status": ""})["status"] = "removed"
                    continue
                e = out.setdefault(own[0], {"links": set(), "status": ""})
                e["links"] |= set(md.expand_ranges(" ".join(r[1:])))
                if cs is not None and cs < len(r) and r[cs].strip():
                    e["status"] = r[cs].strip().lower()
    return out


def design_text(p: A.Project) -> str:
    parts = []
    for f in sorted((p.path / "design").rglob("*.md")):
        if "_work" not in f.parts:
            parts.append(f.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def module_text(p: A.Project, mid: str) -> str:
    """Spec text for one module: its technical/mNN-*.md file, or its '### … Mx …' section in TECHNICAL.md."""
    num = int(mid[1:])
    for f in sorted((p.path / "design" / "technical").glob("m%02d-*.md" % num)) + \
            sorted((p.path / "design" / "technical").glob("m%d-*.md" % num)):
        return f.read_text(encoding="utf-8", errors="replace")
    text = A.doc_text(p, "design/TECHNICAL.md")
    m = re.search(r"^#{2,4} .*\b%s\b.*$" % mid, text, flags=re.M)
    if not m:
        return ""
    level = len(m.group(0)) - len(m.group(0).lstrip("#"))
    rest = text[m.end():]
    end = re.search(r"^#{2,%d} " % level, rest, flags=re.M)
    return rest[: end.start()] if end else rest


def section(text: str, number: str) -> str:
    m = re.search(r"^## %s\.?\s.*$" % re.escape(number), text, flags=re.M)
    if not m:
        return ""
    rest = text[m.end():]
    end = re.search(r"^## ", rest, flags=re.M)
    return rest[: end.start()] if end else rest


def ac_index(p: A.Project) -> Dict[str, Set[str]]:
    """AC id → ids it links to; plus REQ → ACs (reverse) via the shared id graph."""
    links, _ = A.id_graph(p)
    return links


def scope_flags(p: A.Project) -> Dict[str, bool]:
    mods = A.read_modules(p)
    std = p.meta.get("size", "Medium") != "Small" or any(m["rigour"] in ("Standard", "Critical") for m in mods)
    return {"S": std, "C": any(m["rigour"] == "Critical" for m in mods)}


def answered(answers: Dict[str, str], key: str) -> Optional[bool]:
    v = answers.get(key)
    if v is None:
        return None
    return v.strip().lower() in ("yes", "y", "true", "pass", "done", "ok")


# ───────── gates ─────────

def g1(p: A.Project, answers: Dict[str, str]) -> List[Dict[str, Any]]:
    out = []
    evs = p.events()
    so = [e for e in evs if e.get("type") == "signoff.recorded"]
    out.append(R("signoff", "Client sign-off recorded", bool(so),
                 so[-1]["summary"] if so else "record it with `atlasctl signoff --what \"PRD v1.0\" --by …`"))
    total, blocking = A.open_questions(p)
    out.append(R("questions", "No open 'needed before we start' client questions", blocking == 0,
                 "%d open" % blocking if blocking else ""))
    f = frs(p)
    if not f:
        out.append(R("frs", "Functional requirements have a status", False, "no FR rows found in discovery/PRD.md"))
    else:
        valid = ("confirmed", "proposed", "to confirm", "deferred", "rejected", "out of scope")
        bad = [k for k, v in f.items() if v["status"] not in valid]
        out.append(R("frs", "Every functional requirement has a valid status", not bad, short(bad)))
        must_tc = [k for k, v in f.items() if v["status"] == "to confirm" and v["priority"].startswith("must")]
        out.append(R("must", "No Must requirement is still 'to confirm'", not must_tc, short(must_tc)))
    sc = scope_flags(p)
    prd = md.strip_noise(A.doc_text(p, "discovery/PRD.md"))
    s15 = section(prd, "15")
    if sc["S"]:
        rows = [ln for ln in s15.splitlines() if ln.strip().startswith("|") and not md.is_sep(ln)]
        filled = len(rows) > 1 or "none identified" in s15.lower()
        out.append(R("regulations", "(S) Regulations section (PRD §15) filled in or 'None identified'", filled,
                     "" if filled else "PRD §15 is empty"))
    if re.search(r"(?i)\b(lawyer|legal advice|legal review|counsel)\b", s15):
        v = answered(answers, "legal_ack")
        out.append(R("legal_ack", "Legal flags in PRD §15 acknowledged by our team", v,
                     "PRD §15 flags items needing legal advice", ask=v is None))
    return out


def g2(p: A.Project, answers: Dict[str, str]) -> List[Dict[str, Any]]:
    out = []
    f = {k: v for k, v in frs(p).items() if v["status"] not in FR_DONE}
    rq = reqs(p)
    cited = set()
    for v in rq.values():
        cited |= {x for x in v["links"] if x.startswith("FR-")}
    if not rq:
        out.append(R("fr_req", "Every in-scope FR is cited by a REQ", False, "no REQ rows found in design/"))
    else:
        miss = [x for x in f if x not in cited]
        out.append(R("fr_req", "Every in-scope FR is cited by at least one REQ", not miss, short(miss)))
    links = ac_index(p)
    has_ac = set()
    for i, ls in links.items():
        if i.startswith("AC-"):
            has_ac |= {x for x in ls if x.startswith("REQ-")}
    for r, v in rq.items():
        if any(x.startswith("AC-") for x in v["links"]):
            has_ac.add(r)
    live = [r for r, v in rq.items() if not any(s in v["status"] for s in ("out of scope", "deferred", "rejected", "removed"))]
    no_ac = [r for r in live if r not in has_ac]
    if rq:
        out.append(R("acs", "Every REQ has at least one acceptance criterion (AC-…)", not no_ac, short(no_ac)))
    mods = A.read_modules(p)
    out.append(R("modules", "design/MODULES.md lists the modules", bool(mods), "" if mods else "missing or empty"))
    unconf = [m["id"] for m in mods if not m["confirmed"]]
    out.append(R("rigour", "Every module's rigour level is confirmed by the user", bool(mods) and not unconf,
                 ("unconfirmed: " + ", ".join(unconf)) if unconf else ""))
    sc = scope_flags(p)
    if sc["S"]:
        blocking = []
        for fpath in [p.path / "design" / "TECHNICAL.md", p.path / "design" / "DECISIONS.md"]:
            for t in md.read_tables(fpath):
                cb, cs = t.col("blocking"), t.col("status")
                for r in t.rows:
                    if not r or not re.match(r"^OQ-\d+", r[0].strip("* ")):
                        continue
                    blk = cb is not None and cb < len(r) and r[cb].strip().lower() in ("yes", "y", "✅", "blocking")
                    st = (r[cs] if cs is not None and cs < len(r) else "").lower()
                    if blk and not any(w in st for w in ("resolved", "closed", "answered", "done")):
                        blocking.append(r[0].strip("* "))
        out.append(R("oq", "(S) No blocking open questions in the design", not blocking, short(blocking)))
    for m in mods:
        if m["rigour"] != "Critical":
            continue
        t = module_text(p, m["id"]).lower()
        threat = "threat" in t or "abuse" in t
        fail = "rollback" in t or "failure" in t or "error" in t
        out.append(R("crit_%s" % m["id"], "(C) %s %s has threat notes and failure/rollback behaviour" % (m["id"], m["name"]),
                     threat and fail, ", ".join(x for x, ok in (("threat notes", threat), ("failure/rollback", fail))
                                                if not ok) and "missing: " + ", ".join(
                         x for x, ok in (("threat notes", threat), ("failure/rollback", fail)) if not ok)))
    return out


def g3(p: A.Project, answers: Dict[str, str]) -> List[Dict[str, Any]]:
    out = []
    phases, wps = A.read_plan(p)
    if not wps:
        return [R("plan", "plan/PLAN.md has work packages", False, "no work-package table found")]
    rq = reqs(p)
    covered = set()
    for w in wps:
        covered |= set(w["reqs"])
    live = [r for r, v in rq.items() if not any(s in v["status"] for s in ("out of scope", "deferred", "rejected", "removed"))]
    miss = [r for r in live if r not in covered]
    out.append(R("coverage", "Every REQ is covered by a work package", not miss, short(miss)))
    graph = {w["id"]: w["depends"] for w in wps}
    cycle = find_cycle(graph)
    out.append(R("cycles", "No dependency cycles between work packages", not cycle, " → ".join(cycle)))
    unknown = sorted({d for w in wps for d in w["depends"] if d not in graph})
    if unknown:
        out.append(R("deps", "Every dependency names a real work package", False, short(unknown)))
    nogoal = [ph["id"] for ph in phases if not ph["goal"].strip() or "{{" in ph["goal"]]
    out.append(R("goals", "Every phase has a goal (exit criterion)", bool(phases) and not nogoal,
                 "no phase table" if not phases else short(nogoal)))
    orphan = sorted({w["phase"] for w in wps} - {ph["id"] for ph in phases})
    if orphan and phases:
        out.append(R("phases", "Every work package's phase is in the phase table", False, short(orphan)))
    crit = {m["id"] for m in A.read_modules(p) if m["rigour"] == "Critical"}
    if crit:
        plan_text = A.doc_text(p, "plan/PLAN.md")
        bad = []
        for w in wps:
            if set(w["modules"]) & crit:
                row = next((ln for ln in plan_text.splitlines() if re.match(r"^\|\s*\**%s\b" % w["id"], ln)), "")
                small = w["size"].upper().strip() in ("XS", "S", "M")
                review = "review" in row.lower() or "review" in w["title"].lower()
                if not (small and review):
                    bad.append("%s (%s)" % (w["id"], ", ".join(x for x, ok in (("size %s" % (w["size"] or "?"), small),
                                                                               ("no review checkpoint", review)) if not ok)))
        out.append(R("crit_wps", "(C) Critical-module work packages are small and end in a review checkpoint", not bad,
                     "; ".join(bad[:8])))
    return out


def find_cycle(graph: Dict[str, List[str]]) -> List[str]:
    color: Dict[str, int] = {}
    stack: List[str] = []

    def visit(n: str) -> List[str]:
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
    for n in graph:
        if color.get(n, 0) == 0:
            c = visit(n)
            if c:
                return c
    return []


def scan_secrets(repo: Path) -> List[str]:
    hits = []
    r = subprocess.run(["git", "ls-files"], cwd=str(repo), capture_output=True, text=True)
    for f in r.stdout.splitlines():
        name = f.split("/")[-1]
        if name in (".env", ".env.local", ".env.production", "id_rsa", "id_ed25519") or name.endswith((".pem", ".p12",
                                                                                                         ".pfx", ".key")):
            hits.append("%s (tracked secret file)" % f)
            continue
        fp = repo / f
        try:
            if fp.stat().st_size > 1_000_000:
                continue
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for rx, what in SECRET_PATTERNS:
            m = rx.search(text)
            if m and "example" not in text[max(0, m.start() - 80):m.end() + 20].lower():
                hits.append("%s (%s, line %d)" % (f, what, text[: m.start()].count("\n") + 1))
                break
        if len(hits) > 30:
            break
    return hits


def g4(p: A.Project, phase: str, answers: Dict[str, str]) -> List[Dict[str, Any]]:
    out = []
    s = A.build_status(p)
    ws = [w for w in s["wps"] if w["phase"] == phase]
    if not ws:
        return [R("wps", "Phase %s has work packages" % phase, False, "none found in PLAN.md")]
    open_ = [w["id"] for w in ws if w["state"] not in ("done", "deferred")]
    out.append(R("done", "Every work package in %s is done or deferred" % phase, not open_, short(open_)))
    noev = [w["id"] for w in ws if w["state"] == "done" and w["confidence"] == "claimed"]
    if noev:
        out.append(R("evidence", "Done work packages have code evidence", False, short(noev)))
    ci = s["rec"].get("ci") or {}
    if any(ci.values()):
        bad = ["%s: %s" % (k, v.get("conclusion") or v.get("status")) for k, v in ci.items()
               if v and v.get("conclusion") not in ("success",)]
        out.append(R("ci", "CI is green on the default branch", not bad, "; ".join(bad)))
    else:
        out.append(R("ci", "CI is green on the default branch", None, "no CI runs found"))
    sc = scope_flags(p)
    if sc["S"]:
        drift = [a for a in s["attention"] if a.startswith("Drift:") or "match no work package" in a]
        out.append(R("drift", "(S) No unresolved drift from the last reconcile", not drift, "; ".join(drift)[:300]))
    crit = {m["id"]: m for m in s["modules"] if m["rigour"] == "Critical"}
    touched = sorted({m for w in ws for m in w["modules"] if m in crit})
    if touched:
        reviewed = {r for e in p.events() if e.get("type") == "review.security"
                    and e.get("data", {}).get("phase") in (phase, "", None) for r in e.get("refs", [])}
        miss = [m for m in touched if m not in reviewed]
        out.append(R("security_review", "(C) Security review recorded for Critical modules in %s" % phase, not miss,
                     ("missing: " + ", ".join(miss)) if miss else ""))
    hits = []
    for name, path in p.repo_paths().items():
        hits += ["%s: %s" % (name, h) for h in scan_secrets(path)]
    out.append(R("secrets", "No secrets in the code repositories' tracked files", not hits, "; ".join(hits[:6])))
    return out


def g5(p: A.Project, phase: str, answers: Dict[str, str]) -> List[Dict[str, Any]]:
    out = []
    _, wps = A.read_plan(p)
    ws = [w for w in wps if w["phase"] == phase]
    phase_reqs = {r for w in ws for r in w["reqs"]}
    links, _ = A.id_graph(p)
    acs = {a for a, ls in links.items() if a.startswith("AC-") and ls & phase_reqs}
    for r in phase_reqs:
        acs |= {x for x in links.get(r, set()) if x.startswith("AC-")}
    targets = acs or phase_reqs
    tc = A.test_status(p)
    if not (p.path / "test" / "TEST-PLAN.md").exists():
        out.append(R("tests", "TEST-PLAN.md covers every acceptance criterion in %s" % phase, False,
                     "test/TEST-PLAN.md missing — run /sentinel"))
    else:
        miss = [x for x in targets if x not in tc]
        out.append(R("tests", "TEST-PLAN.md covers every acceptance criterion in %s" % phase, not miss, short(miss)))
        failing = [x for x in targets if tc.get(x) == "fail"]
        notrun = [x for x in targets if tc.get(x) == "todo"]
        out.append(R("results", "All tests for %s have passed" % phase, not failing and not notrun,
                     ("failing: %s " % short(failing) if failing else "") + ("not run: %s" % short(notrun)
                                                                              if notrun else "")))
    uat = [e for e in p.events() if e.get("type") == "signoff.recorded" and
           (e["data"].get("phase") == phase or (not e["data"].get("phase") and "uat" in e["data"].get("what", "").lower()
                                                 and phase.lower() in e["data"].get("what", "").lower()))]
    out.append(R("uat", "UAT passed and signed off by the client", bool(uat),
                 uat[-1]["summary"] if uat else "record with `atlasctl signoff --what \"UAT %s\" --by … --phase %s`"
                 % (phase, phase)))
    sc = scope_flags(p)
    golive = A.doc_text(p, "test/GO-LIVE.md")
    if sc["S"]:
        if not golive:
            out.append(R("golive", "(S) GO-LIVE.md checklist complete", False, "test/GO-LIVE.md missing"))
        else:
            unchecked = len(re.findall(r"^\s*[-*] \[ \]", golive, flags=re.M))
            out.append(R("golive", "(S) GO-LIVE.md checklist complete", unchecked == 0,
                         "%d item(s) unchecked" % unchecked if unchecked else ""))
    crit = {m["id"] for m in A.read_modules(p) if m["rigour"] == "Critical"}
    if crit & {m for w in ws for m in w["modules"]}:
        has_rb = bool(re.search(r"(?i)rollback", golive))
        v = answered(answers, "rollback_rehearsed")
        out.append(R("rollback_rehearsed", "(C) Rollback plan written and rehearsed", (has_rb and v) if v is not None
                     else None, "" if has_rb else "no rollback section in GO-LIVE.md", ask=v is None and has_rb))
        if not has_rb:
            out[-1]["result"] = "fail"
        if re.search(r"(?i)migrat", A.doc_text(p, "plan/PLAN.md") + golive):
            v2 = answered(answers, "migration_rehearsed")
            out.append(R("migration_rehearsed", "(C) Data migration rehearsed", v2, "", ask=v2 is None))
    return out


def run_gate(p: A.Project, gate: str, phase: Optional[str], answers: Dict[str, str]) -> List[Dict[str, Any]]:
    if gate == "G1":
        return g1(p, answers)
    if gate == "G2":
        return g2(p, answers)
    if gate == "G3":
        return g3(p, answers)
    if gate == "G4":
        return g4(p, phase or "", answers)
    return g5(p, phase or "", answers)
