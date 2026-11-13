"""Agent hand-offs for ATLAS: begin / finish / pack, notes between agents, stale-document detection, intake.

`begin` gives an agent everything it needs to start in about 30 lines, so it never reads CONTRACT.md or the
full status. `finish` runs the agent's own check, logs the events, runs the gate and saves once.
`pack` prints only the rows an agent needs from upstream documents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import atlasctl as A
import mdtables as md

WRITES = {"alice": "discovery/ and reports/", "stark": "design/", "jarvis": "plan/", "sentinel": "test/",
          "spartan": "reports/ (security reviews)", "atlas": "reports/"}
DOCS = {"alice": [("PRD", "discovery/PRD.md"), ("PROPOSAL", "discovery/PROPOSAL.md"),
                  ("QUESTIONS", "discovery/QUESTIONS.md")],
        "stark": [("TECHNICAL", "design/TECHNICAL.md"), ("DIAGRAMS", "design/DIAGRAMS.md")],
        "jarvis": [("PLAN", "plan/PLAN.md")],
        "sentinel": [("TEST-PLAN", "test/TEST-PLAN.md")]}
UPSTREAM = {"stark": ["prd"], "jarvis": ["design"], "sentinel": ["design", "plan"]}
OUTPUT = {"stark": "design/TECHNICAL.md", "jarvis": "plan/PLAN.md", "sentinel": "test/TEST-PLAN.md"}
LABEL = {"stark": "The design", "jarvis": "The plan", "sentinel": "The test plan"}
KIND_DOC = {"prd": ("PRD", "discovery/PRD.md", "requirement"), "design": ("design", "design/TECHNICAL.md",
                                                                             "requirement or criterion"),
            "plan": ("plan", "plan/PLAN.md", "work package")}
FIX = {"stark": "/stark update", "jarvis": "/jarvis plan", "sentinel": "/sentinel"}


# ───────────────────────── reading rows ─────────────────────────

def _h(cells: List[str]) -> str:
    return hashlib.sha1(" | ".join(c.strip() for c in cells).encode("utf-8")).hexdigest()[:10]


def fr_rows(p: A.Project) -> Dict[str, Dict[str, str]]:
    """FR / BR rows of the PRD: id → {text, priority, status, source, row}."""
    out: Dict[str, Dict[str, str]] = {}
    for t in md.read_tables(p.path / "discovery" / "PRD.md"):
        ci = t.col("id")
        if ci is None:
            continue
        cr, cp, cs, cso = t.col("requirement", "rule"), t.col("priority"), t.col("status"), t.col("source")
        for r in t.rows:
            rid = (r[ci] if ci < len(r) else "").strip("* ~")
            if not re.match(r"^(FR-\d+|BR-\d+)$", rid):
                continue
            g = lambda i: (r[i].strip() if i is not None and i < len(r) else "")  # noqa: E731
            out[rid] = {"text": g(cr), "priority": g(cp), "status": g(cs), "source": g(cso),
                        "h": _h([g(cr), g(cp), g(cs)])}
    return out


def req_rows(p: A.Project) -> Dict[str, Dict[str, str]]:
    """REQ rows of Stark's register: id → {text, module, priority, status, source}."""
    out: Dict[str, Dict[str, str]] = {}
    for t in md.read_tables(p.path / "design" / "_work" / "requirements.md"):
        ci, cr = t.col("id"), t.col("requirement")
        if ci is None or cr is None:
            continue
        cm, cp, cs, cso = t.col("module"), t.col("priority"), t.col("status"), t.col("source")
        for r in t.rows:
            rid = (r[ci] if ci < len(r) else "").strip("* ")
            if not re.match(r"^REQ-\d+$", rid):
                continue
            g = lambda i: (r[i].strip() if i is not None and i < len(r) else "")  # noqa: E731
            out[rid] = {"text": g(cr), "module": g(cm), "priority": g(cp), "status": g(cs), "source": g(cso),
                        "h": _h([g(cr), g(cm), g(cp), g(cs)])}
    return out


def ac_rows(p: A.Project) -> Dict[str, Dict[str, Any]]:
    """Acceptance-criterion rows anywhere in design/: id → {reqs, text}."""
    out: Dict[str, Dict[str, Any]] = {}
    files = sorted((p.path / "design").glob("*.md")) + sorted((p.path / "design" / "technical").glob("*.md"))
    for f in files:
        for t in md.read_tables(f):
            for r in t.rows:
                if not r or not re.match(r"^\**AC-\d+\**$", r[0].strip()):
                    continue
                aid = r[0].strip("* ")
                rest = r[1:]
                reqs = [x for x in md.expand_ranges(" ".join(rest)) if x.startswith("REQ-")]
                text = max(rest, key=len).strip() if rest else ""
                out[aid] = {"reqs": reqs, "text": text, "h": _h(rest)}
    return out


def fingerprint(p: A.Project, kind: str) -> Dict[str, str]:
    if kind == "prd":
        fp = {k: v["h"] for k, v in fr_rows(p).items()}
        if not fp:                                   # adopted PRD: watch the source files Stark converted
            man = A.read_json(p.path / "design" / "_work" / "sources" / "manifest.json", {})
            fp = {d.get("file", code): str(d.get("sha256", ""))[:10] for code, d in (man.get("docs") or {}).items()}
        return fp
    if kind == "design":
        fp = {k: v["h"] for k, v in req_rows(p).items()}
        fp.update({k: v["h"] for k, v in ac_rows(p).items()})
        return fp
    _, wps = A.read_plan(p)
    return {w["id"]: _h([w["title"], w["phase"], ",".join(w["modules"]), ",".join(w["reqs"])]) for w in wps}


def doc_version(p: A.Project, rel: str) -> str:
    head = A.doc_text(p, rel)[:3000]
    m = re.search(r"\|\s*\**Version\**\s*\|\s*\**\s*(v\d+(?:\.\d+)*)", head, flags=re.I)
    return m.group(1) if m else ""


def diff_rows(old: Dict[str, str], new: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
    added = sorted(k for k in new if k not in old)
    changed = sorted(k for k in new if k in old and old[k] != new[k])
    removed = sorted(k for k in old if k not in new)
    return added, changed, removed


# ───────────────────────── stamps and staleness ─────────────────────────

def load_stamps(p: A.Project) -> Dict[str, Any]:
    return A.read_json(p.path / "state" / "stamps.json", {})


def stamp(p: A.Project, agent: str) -> None:
    st = load_stamps(p)
    entry: Dict[str, Any] = {"at": A.now()}
    for kind in UPSTREAM.get(agent, []):
        entry[kind] = {"version": doc_version(p, KIND_DOC[kind][1]), "rows": fingerprint(p, kind)}
    st[agent] = entry
    A.write_json(p.path / "state" / "stamps.json", st)


def staleness(p: A.Project, agent: str) -> List[Dict[str, Any]]:
    """For each upstream document this agent built on: what changed since."""
    out = []
    entry = load_stamps(p).get(agent)
    if not entry or not (p.path / OUTPUT.get(agent, "x")).exists():
        return out
    for kind in UPSTREAM.get(agent, []):
        if kind not in entry:
            continue
        added, changed, removed = diff_rows(entry[kind]["rows"], fingerprint(p, kind))
        if added or changed or removed:
            out.append({"kind": kind, "was": entry[kind].get("version", ""),
                        "now": doc_version(p, KIND_DOC[kind][1]), "added": added, "changed": changed,
                        "removed": removed})
    return out


def stale_lines(p: A.Project) -> List[str]:
    lines = []
    for agent in ("stark", "jarvis", "sentinel"):
        for s in staleness(p, agent):
            name, _, noun = KIND_DOC[s["kind"]]
            n = len(s["added"]) + len(s["changed"]) + len(s["removed"])
            ver = (" %s" % s["was"]) if s["was"] else ""
            nowv = (" (now %s)" % s["now"]) if s["now"] and s["now"] != s["was"] else ""
            lines.append("%s was built on the %s%s; %d %s(s) changed since%s — run %s." % (
                LABEL[agent], name, ver, n, noun, nowv, FIX[agent]))
    return lines


# ───────────────────────── notes between agents ─────────────────────────

def open_notes(evs: List[Dict[str, Any]], to: Optional[str] = None, include_closed: bool = False) -> List[Dict[str, Any]]:
    notes: Dict[str, Dict[str, Any]] = {}
    for ev in evs:
        d = ev.get("data", {})
        if ev.get("type") == "note.added":
            notes[d["id"]] = {"id": d["id"], "to": d.get("to", ""), "from": d.get("from", ""), "text": ev["summary"],
                              "refs": ev.get("refs", []), "date": ev["ts"][:10], "open": True, "reply": ""}
        elif ev.get("type") == "note.closed" and d.get("id") in notes:
            notes[d["id"]]["open"] = False
            notes[d["id"]]["reply"] = d.get("reply", "")
    out = [n for n in notes.values() if (include_closed or n["open"]) and (to is None or n["to"] == to)]
    return out


def cmd_note(a: argparse.Namespace) -> None:
    p = A.find_project(A.load_config(), a.project)
    n = 1 + max([int(e["data"]["id"][2:]) for e in p.events() if e.get("type") == "note.added"] or [0])
    nid = "N-%02d" % n
    refs = [r.strip() for r in (a.refs or "").split(",") if r.strip()] or md.ids_in(a.text)
    A.append_event(p, "note.added", a.sender or "user", a.text, refs=refs,
                   data={"id": nid, "to": a.to, "from": a.sender or "user"})
    A.git_commit_push(p.path, "Note %s for %s" % (nid, a.to), push=False)
    print("%s left for %s." % (nid, a.to))


def cmd_notes(a: argparse.Namespace) -> None:
    p = A.find_project(A.load_config(), a.project)
    notes = open_notes(p.events(), a.to, include_closed=a.all)
    if not notes:
        print("No open notes%s." % ((" for " + a.to) if a.to else ""))
        return
    for n in notes:
        print("%s %s → %s (%s)%s: %s%s" % (n["id"], n["from"], n["to"], n["date"],
                                          (" [" + ", ".join(n["refs"]) + "]") if n["refs"] else "", n["text"],
                                          "" if n["open"] else "  — closed: " + n["reply"]))


def cmd_note_done(a: argparse.Namespace) -> None:
    p = A.find_project(A.load_config(), a.project)
    known = {n["id"] for n in open_notes(p.events())}
    for nid in a.ids:
        nid = nid.upper()
        if nid not in known:
            print("%s is not an open note." % nid)
            continue
        A.append_event(p, "note.closed", a.sender or "user", "%s handled%s" % (nid, (": " + a.reply) if a.reply else ""),
                       refs=[nid], data={"id": nid, "reply": a.reply or ""})
        print("%s closed." % nid)
    A.git_commit_push(p.path, "Notes closed", push=False)


# ───────────────────────── begin ─────────────────────────

def _stage_for(agent: str, arg: Optional[str]) -> str:
    if arg:
        return "" if arg == "none" else arg
    return A.AGENT_STAGE.get(agent, "")


def cmd_begin(a: argparse.Namespace) -> None:
    cfg = A.load_config()
    p = A.find_project(cfg, a.project)
    p.sync_pull()
    agent = a.agent
    s = A.build_status(p)
    stage = _stage_for(agent, a.stage)
    phase = a.phase or (s["current_phase"] if agent == "sentinel" else "")
    if stage and A.stage_state(p.events()).get(stage) != "in progress":
        data = {"stage": stage}
        if phase:
            data["phase"] = phase
        A.append_event(p, "stage.started", agent, "%s started%s" % (stage.capitalize(), (" for " + phase) if phase else ""),
                       refs=[phase] if phase else [], data=data)
        s = A.build_status(p)
    m = p.meta
    L = ["ATLAS brief for %s — %s %s (client: %s · size: %s · track: %s · author: %s)" % (
        agent, m["id"], m["name"], m.get("client") or "?", m.get("size") or "?", s["track"], m.get("author") or "?"),
        "P     = %s" % p.path,
        "atlas = python3 %s   (every `atlas …` below means this)" % (A.LIB / "atlasctl.py"),
        "Write only in P/%s. Everything else goes through `atlas`." % WRITES.get(agent, "your own folder"),
        "Stages: " + " · ".join("%s=%s" % (k, v) for k, v in s["stages"].items() if v != "not started")
        + ((" · current phase: " + s["current_phase"]) if s["current_phase"] and s["phases"] else "")]
    # upstream documents
    ups = []
    for name, rel in (("PRD", "discovery/PRD.md"), ("TECHNICAL", "design/TECHNICAL.md"), ("PLAN", "plan/PLAN.md"),
                      ("TEST-PLAN", "test/TEST-PLAN.md")):
        if (p.path / rel).exists():
            ups.append("%s %s" % (name, doc_version(p, rel) or "(no version)"))
    if ups:
        L.append("Documents: " + " · ".join(ups))
    for st in staleness(p, agent):
        name = KIND_DOC[st["kind"]][0]
        bits = []
        for label in ("added", "changed", "removed"):
            if st[label]:
                bits.append("%s: %s" % (label, ", ".join(st[label][:12]) + (" …" if len(st[label]) > 12 else "")))
        L.append("CHANGED UPSTREAM since your last run (%s %s → %s): %s" % (name, st["was"] or "?", st["now"] or "?",
                                                                          "; ".join(bits)))
        if agent == "stark":
            L.append("  Read only those rows: atlas pack stark --changed")
    if s["modules"]:
        L.append("Modules: " + " · ".join("%s %s %s%s" % (mo["id"], mo["name"], mo["rigour"],
                                                         "" if mo["confirmed"] else " (unconfirmed)")
                                           for mo in s["modules"]))
    if phase and s["phases"]:
        ws = [w for w in s["wps"] if w["phase"] == phase]
        L.append("Phase %s: %d work package(s), %d done. Slice of the design for it: atlas pack %s --phase %s" % (
            phase, len(ws), sum(1 for w in ws if w["state"] in ("done", "deferred")), agent, phase))
    notes = open_notes(p.events(), agent)
    if notes:
        L.append("Notes for you (%d) — handle each, then `atlas note-done <id> --reply \"…\"`:" % len(notes))
        for n in notes:
            L.append("  %s from %s%s: %s" % (n["id"], n["from"], (" [" + ", ".join(n["refs"]) + "]") if n["refs"] else "",
                                            n["text"]))
    crs = ["%s (%s): %s" % (cid, c["state"], c["title"]) for cid, c in sorted(s["crs"].items())
           if c["state"] in ("opened", "approved")]
    if crs:
        L.append("Change requests: " + " | ".join(crs))
        L.append("  What a change touches: atlas impact <FR-… or REQ-…>")
    # open items of this agent's gate
    g = A.STAGE_GATE.get(stage, "G5" if stage == "test" else "")
    if g and (p.path / (OUTPUT.get(agent) or "discovery/PRD.md")).exists():
        import gates as G  # noqa: E402
        res = [r for r in G.run_gate(p, g, phase or None, A.saved_answers(p, g, phase or None))
               if r["result"] in ("fail", "ask")]
        if res:
            L.append("Open items for %s (the check that runs when you finish):" % g)
            L += ["  - %s%s" % (r["check"], (" — " + r["detail"]) if r["detail"] else "") for r in res]
    repos = p.repo_paths()
    if repos:
        L.append("Code (read-only): " + " · ".join("%s=%s" % (k, v) for k, v in repos.items()))
    if agent == "stark" and s["track"] == "small" and stage:
        L.append("Small track: write the plan (P/plan/PLAN.md) in this same run — see references/small-track.md.")
    adopted = [f.name for f in (p.path / "design" / "sources").glob("*") if f.is_file() and f.name != ".gitkeep"] \
        if (p.path / "design" / "sources").exists() else []
    if agent == "stark" and adopted and not fr_rows(p):
        L.append("No PRD from Alice: the requirements source is P/design/sources/ (%s)." % ", ".join(adopted[:4]))
    client_q = "a question only the client can answer goes into QUESTIONS.md" if agent == "alice" else \
        "a question only the client can answer goes to Alice (`atlas note --to alice \"…\" --from %s`)" % agent
    L += ["Rules: never guess — ask the user in one batch; %s; IDs are permanent; no secrets in files; never put "
          "client details in a web search." % client_q,
          "When done: atlas finish %s%s%s   (runs your check, logs the run, runs the gate, saves)" % (
              agent, (" --stage " + a.stage) if a.stage else "", (" --phase " + phase) if phase else "")]
    A.git_commit_push(p.path, "%s begins" % agent, push=False)
    print("\n".join(L))


# ───────────────────────── finish ─────────────────────────

def _checks(p: A.Project, agent: str, stage: str, phase: str, small_plan: bool) -> List[List[str]]:
    py, sk = sys.executable, A.PLUGIN / "skills"
    if agent == "alice":
        if stage == "define":
            return [[py, str(sk / "alice/scripts/alice.py"), "check", str(p.path)]]
        if stage == "handover" and (p.path / "reports/HANDOVER-CLIENT.md").exists():
            return [[py, str(sk / "alice/scripts/alice.py"), "check-client", str(p.path / "reports/HANDOVER-CLIENT.md")]]
        if (p.path / "discovery/PRD.md").exists():           # sign-off, change request: the PRD may have changed
            return [[py, str(sk / "alice/scripts/alice.py"), "check", str(p.path)]]
        return []
    if agent == "stark":
        if not stage and not (p.path / "design" / "TECHNICAL.md").exists():
            return []                                   # diagram pack before the design exists
        c = [[py, str(sk / "stark/scripts/verify.py"), str(p.path / "design")]]
        if small_plan:
            c.append([py, str(sk / "jarvis/scripts/verify.py"), str(p.path / "plan")])
        return c
    if agent == "jarvis":
        return [[py, str(sk / "jarvis/scripts/verify.py"), str(p.path / "plan")]]
    if agent == "sentinel":
        return [[py, str(sk / "sentinel/scripts/sentinel.py"), "check", str(p.path)] + (["--phase", phase] if phase else [])]
    return []


def _summary(p: A.Project, agent: str, phase: str) -> str:
    if agent == "alice":
        fr = [v for k, v in fr_rows(p).items() if k.startswith("FR-")]
        by: Dict[str, int] = {}
        for v in fr:
            by[v["status"].lower() or "?"] = by.get(v["status"].lower() or "?", 0) + 1
        q, qb = A.open_questions(p)
        return "PRD %s: %d requirements (%s); %d client question(s) open, %d needed before we start" % (
            doc_version(p, "discovery/PRD.md"), len(fr), ", ".join("%d %s" % (n, k) for k, n in sorted(by.items())),
            q, qb)
    if agent == "stark":
        mods = A.read_modules(p)
        return "Design %s: %d REQs, %d acceptance criteria, %d modules (%d Critical)" % (
            doc_version(p, "design/TECHNICAL.md"), len(req_rows(p)), len(ac_rows(p)), len(mods),
            sum(1 for m in mods if m["rigour"] == "Critical"))
    if agent == "jarvis":
        phases, wps = A.read_plan(p)
        return "Plan %s: %d phase(s), %d work package(s)" % (doc_version(p, "plan/PLAN.md"), len(phases), len(wps))
    if agent == "sentinel":
        ts = A.test_status(p)
        return "Test plan written%s; across all phases %d item(s) are covered by tests, %d passed" % (
            (" for " + phase) if phase else "", len(ts), sum(1 for v in ts.values() if v == "pass"))
    return "%s finished" % agent


def cmd_finish(a: argparse.Namespace) -> None:
    cfg = A.load_config()
    p = A.find_project(cfg, a.project)
    agent = a.agent
    stage = _stage_for(agent, a.stage)
    s0 = A.build_status(p)
    phase = a.phase or (s0["current_phase"] if agent == "sentinel" else "") or ""
    _, wps = A.read_plan(p)
    small_plan = agent == "stark" and s0["track"] == "small" and bool(wps)
    # 1. the agent's own check
    if not a.skip_check:
        for cmd in _checks(p, agent, stage, phase, small_plan):
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                out = (r.stdout + r.stderr).strip().splitlines()
                keep = [ln for ln in out if re.search(r"FAIL|ERROR|Traceback|✗", ln)] or out[-25:]
                again = "atlas finish %s%s%s" % (agent, (" --stage " + a.stage) if a.stage else "",
                                                 (" --phase " + phase) if phase and agent == "sentinel" else "")
                print("Not finished: %s reported problems. Fix them and run `%s` again.\n" % (Path(cmd[1]).name, again))
                print("\n".join(keep[:40]))
                sys.exit(2)
    # 2. document versions
    last: Dict[str, str] = {}
    for ev in p.events():
        if ev.get("type") == "doc.version":
            for ref in ev.get("refs", []):
                if "@" in ref:
                    last[ref.split("@")[0]] = ref.split("@")[1]
    docs = list(DOCS.get(agent, [])) + (DOCS["jarvis"] if small_plan else [])
    for name, rel in docs:
        v = doc_version(p, rel)
        if v and last.get(name) != v:
            A.append_event(p, "doc.version", agent, "%s %s" % (name, v), refs=["%s@%s" % (name, v)])
    # 3. what this run was built on
    if agent in UPSTREAM and (stage or not (p.path / OUTPUT[agent]).exists()):
        stamp(p, agent)          # a side run (diagram pack, a note) must not hide that the design is behind
    if small_plan:
        stamp(p, "jarvis")
    # 4. stage finished
    summary = a.summary or _summary(p, agent, phase)
    if stage:
        data: Dict[str, Any] = {"stage": stage}
        if phase:
            data["phase"] = phase
        A.append_event(p, "stage.finished", agent, summary, refs=[phase] if phase else [], data=data)
        if small_plan:
            A.append_event(p, "stage.finished", agent, _summary(p, "jarvis", ""), data={"stage": "plan"})
    # 5. gates, 6. auto-publish, 7. views + one save
    s = A.auto_gates(p, A.build_status(p))
    if p.meta.get("auto_publish") and s["gates"].get("G3", {}).get("result") in ("passed", "waived") \
            and agent in ("jarvis", "stark"):
        n = A.do_publish(p, p.meta["auto_publish"])
        if n:
            print("Blueprint re-published to %s (%d files)." % (p.meta["auto_publish"], n))
        s = A.auto_gates(p, A.build_status(p))
    A.write_views(p, s)
    p.sync_push("%s: %s" % (agent, summary))
    print("Finished %s. %s" % (agent, summary))
    A.print_gate_todo(s)
    print("Next: " + s["next"])


# ───────────────────────── pack ─────────────────────────

def _req_line(rid: str, r: Dict[str, str]) -> str:
    tags = ", ".join(x for x in (r.get("module"), r.get("priority"), r.get("status")) if x)
    return "%s [%s] %s" % (rid, tags, r.get("text", ""))


def _pack_reqs(p: A.Project, ids: List[str], with_tests: bool = True) -> List[str]:
    reqs, acs = req_rows(p), ac_rows(p)
    by_req: Dict[str, List[str]] = {}
    for aid, ac in acs.items():
        for r in ac["reqs"]:
            by_req.setdefault(r, []).append(aid)
    L = []
    for rid in ids:
        L.append(_req_line(rid, reqs.get(rid, {"text": "(not in the register)"})))
        for aid in sorted(by_req.get(rid, [])):
            L.append("  %s: %s" % (aid, acs[aid]["text"]))
        if not by_req.get(rid):
            L.append("  (no acceptance criterion)")
    return L


def cmd_pack(a: argparse.Namespace) -> None:
    p = A.find_project(A.load_config(), a.project)
    agent = a.agent
    s = A.build_status(p)
    L: List[str] = []
    if agent == "stark" and a.changed:
        entry = load_stamps(p).get("stark", {}).get("prd")
        cur = fr_rows(p)
        if not entry:
            print("No earlier design run recorded — read the PRD's requirement tables in full.")
            return
        added, changed, removed = diff_rows(entry["rows"], {k: v["h"] for k, v in cur.items()})
        L.append("PRD changes since the design was built (PRD %s → %s)" % (entry.get("version") or "?",
                                                                         doc_version(p, "discovery/PRD.md") or "?"))
        for label, ids in (("NEW", added), ("CHANGED", changed)):
            for i in ids:
                L.append("%s %s [%s, %s] %s  (source %s)" % (label, i, cur[i]["priority"], cur[i]["status"],
                                                           cur[i]["text"], cur[i]["source"]))
        for i in removed:
            L.append("REMOVED %s" % i)
        if not (added or changed or removed):
            L.append("Nothing changed in the requirement tables.")
        links, _ = A.id_graph(p)
        hit = sorted(k for k, v in links.items() if k.startswith("REQ-") and v & set(changed + removed))
        if hit:
            L.append("REQs that cite a changed or removed requirement: " + ", ".join(hit))
    elif a.module:
        mo = next((m for m in s["modules"] if m["id"] == a.module), None)
        if not mo:
            A.die("%s is not in design/MODULES.md" % a.module)
        reqs = req_rows(p)
        ids = sorted(k for k, v in reqs.items() if a.module in re.findall(r"\bM\d+\b", v["module"]))
        L.append("Module %s %s — rigour %s%s · code paths: %s" % (mo["id"], mo["name"], mo["rigour"],
                                                                "" if mo["confirmed"] else " (unconfirmed)",
                                                                ", ".join(mo["paths"]) or "?"))
        L.append("Work packages: " + (", ".join("%s (%s)" % (w["id"], w["state"]) for w in s["wps"]
                                                if a.module in w["modules"]) or "none"))
        L += _pack_reqs(p, ids)
    elif agent == "alice" or a.report:
        L.append("Progress for a client update — %s (only 'verified' or 'likely' work may be called done)" % p.meta["name"])
        for ph in s["phases"]:
            ws = [w for w in s["wps"] if w["phase"] == ph["id"]]
            solid = sum(1 for w in ws if w["state"] == "done" and w["confidence"] in ("verified", "likely"))
            L.append("Phase %s %s — %s · %d of %d pieces of work done%s" % (
                ph["id"], ph["name"], ph["goal"], solid, len(ws),
                " · RELEASED" if ph["id"] in s["released"] else (" · current" if ph["id"] == s["current_phase"] else "")))
            for w in ws:
                if ph["id"] == s["current_phase"]:
                    L.append("  - %s: %s" % (w["title"], "done" if w["state"] == "done" and w["confidence"] != "claimed"
                                            else ("in progress" if w["state"] in ("in-progress", "done") else w["state"])))
        evs = p.events()
        last_report = max([e["seq"] for e in evs if e.get("type") == "report.sent"] or [0])
        since = [e for e in evs if e["seq"] > last_report and e.get("type") in (
            "phase.released", "signoff.recorded", "decision.recorded", "cr.opened", "cr.approved", "cr.done",
            "cr.rejected")]
        L.append("Since the last update sent (%s):" % (next((e["ts"][:10] for e in evs if e["seq"] == last_report),
                                                          "none sent yet")))
        L += ["  - %s %s: %s" % (e["ts"][:10], e["type"], e["summary"]) for e in since] or ["  - nothing recorded"]
        q, qb = s["questions"]
        L.append("Open questions for the client: %d (%d needed before we start)" % (q, qb))
        L.append("Next for us: " + s["next"])
    elif agent == "jarvis":
        reqs = req_rows(p)
        acs = ac_rows(p)
        n_ac: Dict[str, int] = {}
        for ac in acs.values():
            for r in ac["reqs"]:
                n_ac[r] = n_ac.get(r, 0) + 1
        L.append("Design for planning — %d REQs, %d criteria" % (len(reqs), len(acs)))
        for mo in s["modules"]:
            L.append("%s %s — %s%s · paths: %s" % (mo["id"], mo["name"], mo["rigour"],
                                                   "" if mo["confirmed"] else " (unconfirmed)",
                                                   ", ".join(mo["paths"]) or "?"))
        planned = {r for w in s["wps"] for r in w["reqs"]}
        for t in md.read_tables(p.path / "plan" / "PLAN.md"):
            if t.col("req") == 0 and t.col("evidence") is not None:
                for r in t.rows:
                    planned |= set(md.expand_ranges(r[0]))
        for rid, r in sorted(reqs.items()):
            if any(x in r["status"].lower() for x in ("out of scope", "deferred", "rejected", "removed")):
                continue
            text = r["text"] if len(r["text"]) <= 110 else r["text"][:107] + "…"
            L.append("%s [%s, %s, %d AC]%s %s" % (rid, r["module"], r["priority"], n_ac.get(rid, 0),
                                                 "" if rid in planned or not s["wps"] else " UNPLANNED", text))
        if s["wps"]:
            L.append("Real progress: " + " · ".join("%s=%s" % (w["id"], w["state"]) for w in s["wps"]))
    else:  # sentinel, spartan and anyone else: a phase slice
        phase = a.phase or s["current_phase"]
        ph = next((x for x in s["phases"] if x["id"] == phase), None)
        if not ph:
            A.die("no phase %s in plan/PLAN.md" % phase)
        ws = [w for w in s["wps"] if w["phase"] == phase]
        L.append("Phase %s %s — goal: %s" % (ph["id"], ph["name"], ph["goal"]))
        L.append("Work packages:")
        for w in ws:
            L.append("  %s %s · %s · %s · %s%s" % (w["id"], w["title"], ", ".join(w["modules"]), w["level"], w["state"],
                                                 (" (" + w["confidence"] + ")") if w["confidence"] else ""))
        mods = sorted({m for w in ws for m in w["modules"]})
        L.append("Modules: " + " · ".join("%s %s %s" % (m["id"], m["name"], m["rigour"]) for m in s["modules"]
                                          if m["id"] in mods))
        ids = sorted({r for w in ws for r in w["reqs"]})
        L.append("Requirements and acceptance criteria (%d REQs):" % len(ids))
        L += _pack_reqs(p, ids)
        tcs = []
        for t in md.read_tables(p.path / "test" / "TEST-PLAN.md"):
            ct, cc, cs = t.col("tc"), t.col("covers"), t.col("status")
            if ct is None or cc is None:
                continue
            for r in t.rows:
                cov = set(md.expand_ranges(r[cc] if cc < len(r) else ""))
                if cov & set(ids) or any(set(ac_rows(p).get(x, {}).get("reqs", [])) & set(ids) for x in cov):
                    tcs.append("  %s covers %s — %s" % (r[ct].strip(), r[cc].strip(),
                                                       (r[cs].strip() if cs is not None and cs < len(r) else "")))
        if tcs:
            L.append("Tests already written for this phase:")
            L += tcs
    print("\n".join(L))


# ───────────────────────── intake, stage ─────────────────────────

def cmd_intake(a: argparse.Namespace) -> None:
    p = A.find_project(A.load_config(), a.project)
    dest = p.path / ("design" if a.to == "design" else "discovery") / "sources"
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in a.paths:
        sp = Path(src).expanduser()
        if not sp.exists():
            print("not found: %s" % sp)
            continue
        files = [sp] if sp.is_file() else [f for f in sorted(sp.rglob("*")) if f.is_file()
                                           and not any(part.startswith(".") for part in f.relative_to(sp).parts)]
        for f in files:
            rel = Path(f.name) if sp.is_file() else f.relative_to(sp)
            if set(rel.parts) & {"alice", "_work", "node_modules"}:
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() == f.read_bytes():
                continue
            shutil.copy2(f, target)
            n += 1
    if n:
        A.append_event(p, "sources.added", "atlas", "%d file(s) added to %s/sources" % (n, dest.parent.name),
                       by="user", data={"count": n, "to": dest.parent.name})
        p.sync_push("Intake: %d file(s)" % n)
    print("%d new or changed file(s) copied to %s. Next: %s" % (n, dest, "/stark" if a.to == "design" else "/alice"))


def cmd_stage(a: argparse.Namespace) -> None:
    p = A.find_project(A.load_config(), a.project)
    if a.name not in A.STAGES:
        A.die("stage must be one of %s" % ", ".join(A.STAGES))
    state = {"reset": "not started"}.get(a.state, a.state)
    A.append_event(p, "stage.set", "atlas", "Stage %s set to %s: %s" % (a.name, state, a.reason), by="user",
                   data={"stage": a.name, "state": state, "reason": a.reason})
    p.sync_push("Stage %s %s" % (a.name, state))
    print("Stage %s is now %s." % (a.name, state))
