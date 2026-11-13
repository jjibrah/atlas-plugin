"""Project intelligence for ATLAS: the front door (start, set), leads and the pipeline, and the scope watch.

Scope watch is the heart of it: when the client signs (or a proposal is sent) the agreed requirements become the
baseline. Any later difference between the PRD and that baseline is reported, with what changed and what it touches,
until someone decides: approve it as a change request, or put the PRD back.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import atlasctl as A
import flow
import mdtables as md

LEAD_STATES = ["lead", "sent", "won", "lost"]
DEFAULT_ROOT = Path.home() / "AtlasProjects"


# ───────────────────────── front door ─────────────────────────

def ensure_setup() -> Dict[str, Any]:
    """First use on a device with no choice made yet: a local projects folder. `atlas setup` changes it later."""
    cfg = A.read_json(A.CONFIG, None)
    if cfg:
        return cfg
    import os
    import socket
    import uuid
    root = Path(os.environ.get("ATLAS_PROJECTS", DEFAULT_ROOT)).expanduser()
    if os.environ.get("ATLAS_HOME") and not os.environ.get("ATLAS_PROJECTS"):
        root = A.HOME / "projects"
    A.HOME.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    cfg = {"device": "%s-%s" % (socket.gethostname().split(".")[0][:20], uuid.uuid4().hex[:6]),
           "mode": "folder", "projects_root": str(root.resolve())}
    if not (root / "registry.json").exists():
        A.write_json(root / "registry.json", {"next": 1, "projects": []})
    A.save_config(cfg)
    A.install_shim()
    print("First use on this device: projects will be kept in %s (change with `atlas setup`)." % root)
    return cfg


def cmd_start(a: argparse.Namespace) -> None:
    """One command from nothing to a project: sets up the device if needed, creates the project, takes in files."""
    ensure_setup()
    ns = argparse.Namespace(name=a.name, client=a.client or a.name, size=a.size or "Small", author=a.author or "",
                            repo=a.repo, start=None, prd=None, track=None, project=None)
    A.cmd_new(ns)
    p = A.find_project(A.load_config(), None)
    if a.lead:
        A.append_event(p, "lead.created", "atlas", "Lead: %s%s" % (a.client or a.name, (" — " + a.note) if a.note else ""),
                       by="user", data={"contact": a.contact or "", "source": a.source or "", "note": a.note or ""})
    if a.files:
        flow.cmd_intake(argparse.Namespace(project=None, paths=a.files, to="discovery"))
    A.git_commit_push(p.path, "Start %s" % p.id, push=A.load_config()["mode"] == "github")
    print("Size is set to %s for now; change it with `atlas set size Medium` once the work is understood."
          % (a.size or "Small"))


def cmd_set(a: argparse.Namespace) -> None:
    cfg = A.load_config()
    p = A.find_project(cfg, a.project)
    key, val = a.key.lower(), a.value.strip()
    if key not in ("size", "client", "author", "name"):
        A.die("you can set: size, client, author, name")
    if key == "size":
        val = val.capitalize()
        if val not in A.SIZES:
            A.die("size must be Small, Medium or Large")
    old = p.meta.get(key, "")
    p.meta[key] = val
    A.write_json(p.path / "atlas.json", p.meta)
    if key in ("name", "client"):
        reg = A.load_registry(cfg)
        for e in reg["projects"]:
            if e["id"] == p.id:
                e[key] = val
        A.save_registry(cfg, reg, "Update %s" % p.id)
    A.append_event(p, "project.updated", "atlas", "%s: %s → %s" % (key, old or "(empty)", val), by="user",
                   data={"key": key, "old": old, "new": val})
    A.write_views(p, A.build_status(p))
    p.sync_push("Set %s" % key)
    print("%s is now %s." % (key.capitalize(), val))


# ───────────────────────── leads and the pipeline ─────────────────────────

def lead_state(evs: List[Dict[str, Any]]) -> Dict[str, Any]:
    st: Dict[str, Any] = {"status": "", "since": "", "followup": "", "notes": 0, "reason": ""}
    for ev in evs:
        t, d, day = ev.get("type", ""), ev.get("data", {}), ev.get("ts", "")[:10]
        if t == "lead.created":
            st.update(status="lead", since=day)
        elif t == "lead.note":
            st["notes"] += 1
        elif t == "proposal.sent":
            st.update(status="sent", since=day, followup=d.get("followup", ""))
        elif t == "lead.followup":
            st["followup"] = d.get("on", "")
        elif t in ("lead.won", "signoff.recorded") and st["status"] in ("lead", "sent"):
            st.update(status="won", since=day, followup="")
        elif t == "lead.lost":
            st.update(status="lost", since=day, followup="", reason=d.get("reason", ""))
    return st


def _when(text: str) -> str:
    m = re.match(r"^\+?(\d+)d?$", text.strip())
    if m:
        return (dt.date.today() + dt.timedelta(days=int(m.group(1)))).isoformat()
    try:
        return dt.date.fromisoformat(text.strip()).isoformat()
    except ValueError:
        A.die("give a date as YYYY-MM-DD or as a number of days, e.g. +5d")
        return ""


def cmd_lead(a: argparse.Namespace) -> None:
    act = a.action
    if act == "new":
        if not a.text:
            A.die('usage: atlas lead new "<client>" [--contact …] [--source …] [--note …]')
        cmd_start(argparse.Namespace(name=a.text, client=a.text, size=None, author=None, repo=None, files=a.files,
                                     lead=True, contact=a.contact, source=a.source, note=a.note))
        return
    p = A.find_project(A.load_config(), a.project)
    st = lead_state(p.events())
    if act == "note":
        A.append_event(p, "lead.note", "atlas", a.text or a.note or "", by="user")
        print("Noted.")
    elif act == "sent":
        on = _when(a.followup or "+5d")
        if not st["status"]:
            A.append_event(p, "lead.created", "atlas", "Lead: %s" % (p.meta.get("client") or p.meta["name"]), by="user")
        A.append_event(p, "proposal.sent", "atlas", "%s sent to the client; follow up on %s" % (
            a.text or "Proposal", on), by="user", data={"what": a.text or "Proposal", "followup": on})
        set_baseline(p, "sent")
        print("Recorded. Atlas will remind you on %s if there is no reply. The requirements in the PRD are now the "
              "baseline: later changes are reported by `atlas scope`." % on)
    elif act == "followup":
        on = _when(a.text or "+5d")
        A.append_event(p, "lead.followup", "atlas", "Follow up on %s%s" % (on, (": " + a.note) if a.note else ""),
                       by="user", data={"on": on, "note": a.note or ""})
        print("Next follow-up: %s." % on)
    elif act == "won":
        A.append_event(p, "lead.won", "atlas", "Client said yes%s" % ((": " + (a.text or a.note)) if (a.text or a.note) else ""),
                       by="user")
        print("Marked as won. Record the approval of the proposal itself with `atlas signoff …` when you have it.")
    elif act == "lost":
        reason = a.reason or a.text or ""
        if not reason:
            A.die('say why: atlas lead lost --reason "…"')
        A.append_event(p, "lead.lost", "atlas", "Lead lost: %s" % reason, by="user", data={"reason": reason})
        print("Marked as lost.")
    A.write_views(p, A.build_status(p))
    p.sync_push("Lead %s" % act)


def lead_attention(p: A.Project, evs: List[Dict[str, Any]]) -> List[Tuple[int, str]]:
    st = lead_state(evs)
    out: List[Tuple[int, str]] = []
    if st["status"] == "sent" and st["followup"] and st["followup"] <= A.today():
        days = (dt.date.today() - dt.date.fromisoformat(st["since"])).days
        out.append((0, "Proposal sent %d day(s) ago with no recorded reply — follow up, then `atlas lead followup +5d` "
                       "(or `atlas lead won` / `atlas lead lost --reason …`)." % days))
    return out


def cmd_pipeline(a: argparse.Namespace) -> None:
    cfg = A.load_config()
    if cfg["mode"] == "github":
        A.git_pull(A.registry_dir(cfg))
    rows = []
    for e in A.load_registry(cfg)["projects"]:
        d = A.project_dir_for(cfg, e)
        if not (d / "atlas.json").exists():
            continue
        p = A.Project(d, cfg)
        evs = p.events()
        ls = lead_state(evs)
        s = A.build_status(p)
        if ls["status"] in ("lead", "sent"):
            stage = {"lead": "talking", "sent": "proposal sent"}[ls["status"]]
            days = (dt.date.today() - dt.date.fromisoformat(ls["since"])).days
            due = ls["followup"] and ls["followup"] <= A.today()
            rank = 0 if due else 1
            what = ("FOLLOW UP (due %s)" % ls["followup"]) if due else (
                ("Waiting for the client's reply; follow up on %s" % ls["followup"]) if ls["status"] == "sent"
                else s["next"])
        elif ls["status"] == "lost":
            stage, days, rank, what = "lost", 0, 9, ls["reason"]
        else:
            stage = next((st for st in A.STAGES if s["stages"][st] not in ("done", "skipped")), "complete")
            days, rank, what = 0, (2 if s["attention"] else 3), s["next"]
        rows.append((rank, e["id"], e.get("client") or e["name"], stage, days, len(s["attention"]), what))
    if not rows:
        print('Nothing yet. Start with: atlas lead new "<client>"   or   atlas start "<project>"')
        return
    print("| Project | Client | Where it is | Days waiting | Needs you | Next |\n|---|---|---|---|---|---|")
    for rank, pid, client, stage, days, att, what in sorted(rows):
        print("| %s | %s | %s | %s | %s | %s |" % (pid, client, stage, days or "", att or "", what))


# ───────────────────────── scope watch ─────────────────────────

def _rows(p: A.Project) -> Dict[str, Dict[str, str]]:
    return {k: {x: v[x] for x in ("h", "text", "priority", "status", "source")} for k, v in flow.fr_rows(p).items()}


def set_baseline(p: A.Project, kind: str, only: Optional[List[str]] = None) -> None:
    """Freeze the agreed requirements. `only` moves just those IDs forward (after an approved change request)."""
    path = p.path / "state" / "baseline.json"
    cur = _rows(p)
    if only is not None:
        base = A.read_json(path, None)
        if not base:
            return
        for rid in only:
            if rid in cur:
                base["rows"][rid] = cur[rid]
            else:
                base["rows"].pop(rid, None)
        base["date"] = A.today()
        base["version"] = flow.doc_version(p, "discovery/PRD.md") or base.get("version", "")
        A.write_json(path, base)
        return
    if not cur:
        return
    A.write_json(path, {"kind": kind, "date": A.today(), "version": flow.doc_version(p, "discovery/PRD.md"),
                        "rows": cur})


def scope_diff(p: A.Project) -> Optional[Dict[str, Any]]:
    base = A.read_json(p.path / "state" / "baseline.json", None)
    if not base:
        return None
    cur = _rows(p)
    added, changed, removed = flow.diff_rows({k: v["h"] for k, v in base["rows"].items()},
                                             {k: v["h"] for k, v in cur.items()})
    # a requirement struck out in place counts as removed, not changed
    dead = ("out of scope", "rejected", "removed")
    gone = [k for k in changed if any(w in cur[k]["status"].lower() for w in dead)
            and not any(w in base["rows"][k]["status"].lower() for w in dead)]
    changed = [k for k in changed if k not in gone]
    removed = sorted(removed + gone)
    # a new requirement that was declined and kept as a rejected row is not part of the scope
    added = [k for k in added if not any(w in cur[k]["status"].lower() for w in dead)]
    return {"base": base, "cur": cur, "added": added, "changed": changed, "removed": removed,
            "n": len(added) + len(changed) + len(removed)}


def _key(d: Dict[str, Any]) -> str:
    sig = [(k, d["cur"].get(k, {}).get("h", "")) for k in sorted(d["added"] + d["changed"] + d["removed"])]
    return hashlib.sha1(json.dumps(sig).encode()).hexdigest()[:12]


def scope_crs(evs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for ev in evs:
        d = ev.get("data", {})
        if ev.get("type") == "cr.opened" and d.get("scope"):
            out[d["cr"]] = {"ids": d["scope"], "state": "opened", "key": d.get("key", "")}
        elif ev.get("type", "").startswith("cr.") and d.get("cr") in out:
            out[d["cr"]]["state"] = ev["type"].split(".")[1]
    return out


def scope_attention(p: A.Project, evs: List[Dict[str, Any]], record: bool = True) -> List[Tuple[int, str]]:
    d = scope_diff(p)
    if not d or not d["n"]:
        return []
    key = _key(d)
    ids = d["added"] + d["changed"] + d["removed"]
    if record and not any(e.get("type") == "scope.changed" and e["data"].get("key") == key for e in evs):
        A.append_event(p, "scope.changed", "atlas", "Scope differs from the baseline: %d added, %d changed, %d removed" % (
            len(d["added"]), len(d["changed"]), len(d["removed"])), refs=ids[:20],
            data={"key": key, "added": d["added"], "changed": d["changed"], "removed": d["removed"]})
    what = "what the client signed" if d["base"]["kind"] == "signoff" else "the proposal you sent"
    counts = ", ".join("%d %s" % (len(d[k]), k) for k in ("added", "changed", "removed") if d[k])
    crs = scope_crs(evs)
    cover = [c for c, v in crs.items() if v["state"] == "opened" and set(ids) <= set(v["ids"])]
    rejected = [c for c, v in crs.items() if v["state"] == "rejected" and set(ids) & set(v["ids"])]
    if cover:
        return [(0, "Scope change waiting for a decision (%s: %s) — `atlas cr approved %s` or `atlas cr rejected %s`."
                 % (cover[0], counts, cover[0], cover[0]))]
    if rejected:
        return [(0, "%s was rejected but the PRD still contains its change (%s) — Alice must put the PRD back "
                    "(`atlas scope` shows the signed wording)." % (rejected[0], counts))]
    return [(0, "The PRD no longer matches %s (%s, %s): %s — review with `atlas scope`." % (
        what, d["base"].get("version") or "PRD", d["base"]["date"], counts))]


def churn(evs: List[Dict[str, Any]]) -> Dict[str, int]:
    n: Dict[str, int] = {}
    for ev in evs:
        if ev.get("type") == "scope.changed":
            for rid in ev["data"].get("added", []) + ev["data"].get("changed", []) + ev["data"].get("removed", []):
                n[rid] = n.get(rid, 0) + 1
    return n


def cmd_scope(a: argparse.Namespace) -> None:
    p = A.find_project(A.load_config(), a.project)
    evs = p.events()
    if a.baseline:
        set_baseline(p, "signoff" if any(e.get("type") == "signoff.recorded" for e in evs) else "sent")
        A.append_event(p, "scope.baseline", "atlas", "Baseline reset to the current PRD: %s" % a.baseline, by="user",
                       data={"reason": a.baseline})
        p.sync_push("Scope baseline")
        print("The current PRD is now the baseline.")
        return
    d = scope_diff(p)
    if d is None:
        print("No baseline yet. It is set when you record `atlas lead sent` or `atlas signoff`.")
        return
    base = d["base"]
    what = "client sign-off" if base["kind"] == "signoff" else "proposal sent"
    if not d["n"]:
        print("In sync: the PRD matches the baseline (%s, %s %s, %d requirements)." % (
            what, base.get("version") or "PRD", base["date"], len(base["rows"])))
        return
    links, _ = A.id_graph(p)
    rev: Dict[str, set] = {}
    for src, dsts in links.items():
        for x in dsts:
            rev.setdefault(x, set()).add(src)

    def downstream(rid: str) -> str:
        seen, todo = set(), [rid]
        while todo:
            x = todo.pop()
            for y in rev.get(x, ()):
                if y not in seen and not y.startswith(("FR-", "BR-")):
                    seen.add(y)
                    todo.append(y)
        return ", ".join(sorted(seen)[:10]) + (" …" if len(seen) > 10 else "") if seen else "nothing built on it yet"

    times = churn(evs)
    print("Scope against the baseline (%s, %s %s):\n" % (what, base.get("version") or "PRD", base["date"]))
    for rid in d["added"]:
        r = d["cur"][rid]
        print("ADDED    %s [%s, %s] %s\n         from: %s\n" % (rid, r["priority"], r["status"], r["text"], r["source"] or "?"))
    for rid in d["changed"]:
        b, r = base["rows"][rid], d["cur"][rid]
        print("CHANGED  %s%s\n         was: [%s, %s] %s\n         now: [%s, %s] %s\n         from: %s\n         touches: %s\n" % (
            rid, (" (changed %d times)" % times[rid]) if times.get(rid, 0) > 1 else "", b["priority"], b["status"],
            b["text"], r["priority"], r["status"], r["text"], r["source"] or "?", downstream(rid)))
    for rid in d["removed"]:
        b = base["rows"][rid]
        print("REMOVED  %s was: [%s, %s] %s\n         touches: %s\n" % (rid, b["priority"], b["status"], b["text"],
                                                                      downstream(rid)))
    ids = d["added"] + d["changed"] + d["removed"]
    if a.cr:
        n = 1 + max([int(e["data"]["cr"][3:]) for e in evs if e.get("type") == "cr.opened"] or [0])
        cid = "CR-%02d" % n
        title = a.cr if isinstance(a.cr, str) and a.cr != "auto" else "Scope change: " + ", ".join(
            ["+" + x for x in d["added"]] + ["~" + x for x in d["changed"]] + ["-" + x for x in d["removed"]])[:160]
        A.append_event(p, "cr.opened", "atlas", title, refs=[cid] + ids[:20], by="user",
                       data={"cr": cid, "scope": ids, "key": _key(d), "touches": ids})
        A.write_views(p, A.build_status(p))
        p.sync_push("Open %s" % cid)
        print("Opened %s for these changes. Decide: `atlas cr approved %s` (the baseline moves forward) or "
              "`atlas cr rejected %s --note \"…\"` (Alice puts the PRD back)." % (cid, cid, cid))
    else:
        crs = scope_crs(evs)
        rej = [c for c, v in crs.items() if v["state"] == "rejected" and set(ids) & set(v["ids"])]
        opened = [c for c, v in crs.items() if v["state"] == "opened" and set(ids) <= set(v["ids"])]
        if opened:
            print("%s is waiting for a decision: `atlas cr approved %s` or `atlas cr rejected %s --note \"…\"`."
                  % (opened[0], opened[0], opened[0]))
        elif rej:
            print("%s was rejected: the PRD must go back to the wording shown under \"was\" above (Alice does this)."
                  % rej[0])
        else:
            print("Decide together, then: `atlas scope --cr` opens a change request for all of this "
                  "(approve or reject it), or `atlas scope --baseline \"<why>\"` accepts the PRD as it is now.")


def on_cr_decided(p: A.Project, cid: str, action: str, note: str) -> None:
    """Called by `atlas cr approved|rejected`: move the baseline, or tell Alice to put the PRD back."""
    info = scope_crs(p.events()).get(cid)
    if not info:
        return
    if action == "approved":
        set_baseline(p, "", only=info["ids"])
        print("Baseline moved forward for %s." % ", ".join(info["ids"]))
    elif action == "rejected":
        n = 1 + max([int(e["data"]["id"][2:]) for e in p.events() if e.get("type") == "note.added"] or [0])
        A.append_event(p, "note.added", "atlas", "%s was rejected%s. Put these requirements back to the agreed wording "
                       "(`atlas scope` shows it): %s" % (cid, (": " + note) if note else "", ", ".join(info["ids"])),
                       refs=[cid] + info["ids"][:20], data={"id": "N-%02d" % n, "to": "alice", "from": "atlas"})
        print("A note asks Alice to put the PRD back. Status keeps reporting it until the PRD matches.")
