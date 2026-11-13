#!/usr/bin/env python3
"""ALICE helper (ATLAS plugin). <P> is the project storage folder (`atlasctl where`); Alice's files live in
<P>/discovery/ (PRD.md, PROPOSAL.md, QUESTIONS.md, _work/). <P> may be omitted: the script then asks atlasctl.

  alice.py init   [<P>]          create discovery/_work/ and STATE.md (does nothing to files that exist)
  alice.py next   [<P>] [KIND]   next free ID (all kinds, or one: FR PP WF P Q D RS ASM BR U M) — never reuse an ID
  alice.py check  [<P>]          verify PRD.md, PROPOSAL.md and QUESTIONS.md (exit 1 on any FAIL)
  alice.py status [<P>]          counts: meetings, requirements by status, proposals, open questions, unprocessed sources
  alice.py check-client <file>   verify a client-facing document (client update, handover pack, proposal):
                                 no internal IDs or source tags, no jargon, no template leftovers, prices flagged

ID formats: FR-001 (functional requirement), BR-01 (business rule), PP-01 (pain point), WF-01 (workflow),
P-01 (proposal), Q-001 (question for the client), D-01 (decision), RS-01 (research source), ASM-01 (assumption the
user approved), U-01 (clarification from our team), M01 (meeting).
Provenance tags: [M02@00:14:32] meeting + timestamp, [M02] meeting, [d3-002] document chunk, [U-03] our team,
[D-05] decision, [P-04] proposal, [RS-03] research, [ASM-02] assumption, [Q-007] waiting on the client.
Text between <!-- legend:start --> and <!-- legend:end --> is ignored (example tags in the template legend).
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import subprocess
import sys

KINDS = {  # prefix → (regex, width, home file)
    "FR": (r"FR-\d{3}", 3, "PRD.md"),
    "BR": (r"BR-\d{2,}", 2, "PRD.md"),
    "PP": (r"PP-\d{2,}", 2, "PRD.md"),
    "WF": (r"WF-\d{2,}", 2, "PRD.md"),
    "P": (r"(?<![A-Z])P-\d{2,}", 2, "PRD.md"),
    "D": (r"(?<![A-Z])D-\d{2,}", 2, "PRD.md"),
    "RS": (r"RS-\d{2,}", 2, "PRD.md"),
    "ASM": (r"ASM-\d{2,}", 2, "PRD.md"),
    "U": (r"(?<![A-Z])U-\d{2,}", 2, "PRD.md"),
    "Q": (r"(?<![A-Z])Q-\d{3}", 3, "QUESTIONS.md"),
    "M": (r"(?<![A-Za-z])M\d{2}(?![\d])", 2, "PRD.md"),
}
TAG_RE = re.compile(r"\[(?:M\d{2}(?:@[\d:]+)?|d\d+-\d{3}|P-\d+|RS-\d+|ASM-\d+|Q-\d+|D-\d+|U-\d+)(?:[^\]]*)\]")
CLIENT_EVIDENCE = re.compile(r"\[(?:M\d{2}(?:@[\d:]+)?|d\d+-\d{3}|D-\d+|U-\d+)")
LEGEND_RE = re.compile(r"<!--\s*legend:start\s*-->.*?<!--\s*legend:end\s*-->", re.S)
WORD_NUM = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|a couple of|several)"
FR_STATUSES = ("confirmed", "proposed", "to confirm", "deferred", "rejected", "out of scope")
P_STATUSES = ("proposed", "accepted", "partly accepted", "rejected", "deferred")
U_STATUSES = ("answered", "sent to client", "pending")
ASM_STATUSES = ("open", "confirmed", "rejected")
Q_STATUSES = ("open", "answered", "withdrawn")
JARGON = ("api", "endpoint", "database", "schema", "json", "webhook", "backend", "frontend", "sql", "microservice",
          "server-side", "repository", "deployment", "oauth", "jwt", "postgres", "react", "kubernetes", "docker")
STATE_SKELETON = """# ALICE state

Client, Project and Author come from atlas.json (`atlasctl status --json` → project). Fill the rows below only when
atlas.json lacks them (the user tells you); a value here overrides an empty atlas.json field.

| | |
|---|---|
| Client | %(client)s |
| Project | %(name)s |
| Author (name on the proposal) | %(author)s |
| Last run | |

## Sources

Every source document and what it is. `Processed`: `yes` once it is fully reflected in the documents; set it back to
`no` when the converter reports the file CHANGED.

| Doc | File | Kind | Meeting | Processed |
|---|---|---|---|---|

Kinds: meeting transcript · meeting notes · SOP · client document · answers · other

## Unclear points for the user
Collected while reading; asked in one batch. Answered ones move to PRD §21.4 as U-## rows.

## Run log
| Date | What changed |
|---|---|
"""


LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "lib")
# Internal identifiers that must never reach the client (Q-numbers are allowed: the client answers by them).
INTERNAL_ID_RE = re.compile(r"\b(?:FR-\d{2,}|BR-\d+|PP-\d+|WF-\d+|RS-\d+|ASM-T?\d+|U-\d+|(?<![A-Z])P-\d+|(?<![A-Z])D-\d+"
                            r"|REQ-\d+|AC-\d+|WP-\d+|TC-\d+|CR-\d+|AD-\d+|OQ-\d+|PRJ-\d+|M\d{1,2}|G[1-5]|P\d{1,2})\b")
SOURCE_TAG_RE = re.compile(r"\[(?:M\d{2}(?:@[\d:]+)?|d\d+-\d{3}|U-\d+|D-\d+|P-\d+|RS-\d+|ASM-\d+)[^\]]*\]")
PROCESS_WORDS = (r"work packages?", r"acceptance criteri\w*", r"rigour", r"traceability", r"pull requests?",
                 r"commits?", r"repos?", r"repository", r"staging", r"sprints?", r"backlog", r"ci runs?", r"gates? g\d",
                 r"change requests? cr", r"confidence")
MONEY_RX = r"(?:\b(?:USD|KES|KSh|Ksh|MYR|RM|EUR|GBP|ZAR|NGN|UGX|TZS)\s?\d[\d,.]*|[$€£]\s?\d[\d,.]*)"


# ------------------------------------------------------------------ helpers
def resolve_project(folder):
    """<P> as given, or the current project from atlasctl."""
    if folder:
        return os.path.abspath(os.path.expanduser(folder))
    try:
        out = subprocess.run([sys.executable, os.path.join(LIB, "atlasctl.py"), "where"], capture_output=True,
                             text=True, timeout=60)
    except OSError as e:
        sys.exit("Could not run atlasctl where: %s" % e)
    if out.returncode != 0 or not out.stdout.strip():
        sys.exit("No project folder given and `atlasctl where` failed: %s" % (out.stderr or out.stdout).strip())
    return out.stdout.strip().splitlines()[-1]


def paths(folder):
    root = os.path.abspath(folder)
    a = os.path.join(root, "discovery")
    return {
        "root": root, "alice": a, "work": os.path.join(a, "_work"), "prd": os.path.join(a, "PRD.md"),
        "proposal": os.path.join(a, "PROPOSAL.md"), "questions": os.path.join(a, "QUESTIONS.md"),
        "state": os.path.join(a, "_work", "STATE.md"), "meetings": os.path.join(a, "_work", "meetings"),
        "manifest": os.path.join(a, "_work", "sources", "manifest.json"), "atlas": os.path.join(root, "atlas.json"),
        "reports": os.path.join(root, "reports"),
    }


def atlas_meta(p):
    try:
        with open(p["atlas"], encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def identity(p, state=None):
    """Client / Project / Author: atlas.json first, STATE.md as the fallback for empty fields."""
    meta = atlas_meta(p)
    state = state if state is not None else (read(p["state"]) or "")
    return {"client": meta.get("client") or state_field(state, "Client"),
            "name": meta.get("name") or state_field(state, "Project"),
            "author": meta.get("author") or state_field(state, "Author")}


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def tables(text):
    """Yield (header_lower, rows) for each markdown table."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            header = [h.strip().lower() for h in split_row(lines[i])]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            yield header, rows
            i = j
        else:
            i += 1


def col(header, *names):
    for n in names:
        for i, h in enumerate(header):
            if h.startswith(n):
                return i
    for n in names:
        for i, h in enumerate(header):
            if n in h:
                return i
    return None


def cell(row, i):
    return row[i] if i is not None and i < len(row) else ""


def defined_ids(text, kind):
    """IDs defined in text: first cell of a table row, or a heading starting with the ID."""
    rx = KINDS[kind][0]
    out = collections.Counter()
    for header, rows in tables(text):
        if not header or header[0].strip("* ") not in ("id", "#", "fr", "q", "m", "meeting"):
            continue  # e.g. "| Pain point | …" rows that merely refer to PP-01
        for r in rows:
            m = re.match(r"\**\s*(%s)\b" % rx, r[0]) if r else None
            if m:
                out[m.group(1)] += 1
    for m in re.finditer(r"^#{2,5}\s+\**(%s)\b" % rx, text, flags=re.M):
        out[m.group(1)] += 1
    return out


def cited_ids(text, kind):
    return set(re.findall(KINDS[kind][0], text))


def strip_code(text):
    return re.sub(r"```.*?```", "", text, flags=re.S)


def num(id_):
    return int(re.search(r"(\d+)$", id_).group(1))


def section(text, pattern):
    m = re.search(r"^##\s[^\n]*(?:%s)[^\n]*\n(.*?)(?=^##\s|\Z)" % pattern, text, flags=re.S | re.M | re.I)
    return m.group(1) if m else ""


def state_field(state, name):
    m = re.search(r"^\|\s*%s[^|]*\|\s*([^|]*)\|" % re.escape(name), state or "", flags=re.M)
    return m.group(1).strip() if m else ""


def manifest(p):
    try:
        with open(p["manifest"], encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def all_texts(p):
    texts = {}
    for key in ("prd", "proposal", "questions"):
        t = read(p[key])
        if t is not None:
            texts[p[key]] = LEGEND_RE.sub("", t)
    for f in sorted(glob.glob(os.path.join(p["meetings"], "*.md"))):
        texts[f] = read(f)
    for f in (os.path.join(p["work"], "research.md"),):
        t = read(f)
        if t is not None:
            texts[f] = t
    return texts


# ------------------------------------------------------------------ commands
def cmd_init(folder):
    p = paths(folder)
    if not os.path.exists(p["atlas"]):
        print("WARN  %s has no atlas.json — is this the project folder (`atlasctl where`)?" % p["root"])
    os.makedirs(p["meetings"], exist_ok=True)
    os.makedirs(os.path.join(p["alice"], "sources"), exist_ok=True)
    os.makedirs(p["reports"], exist_ok=True)
    if os.path.exists(p["state"]):
        print("exists, left alone: %s" % p["state"])
    else:
        meta = atlas_meta(p)
        with open(p["state"], "w", encoding="utf-8") as f:
            f.write(STATE_SKELETON % {k: meta.get(k, "") for k in ("client", "name", "author")})
        print("created: %s" % p["state"])
    who = identity(p)
    missing = [k for k in ("client", "name", "author") if not who[k]]
    print("Client: %s · Project: %s · Author: %s" % (who["client"] or "?", who["name"] or "?", who["author"] or "?"))
    if missing:
        print("MISSING %s — ask the user, then record it in %s" % (", ".join(missing), p["state"]))
    print("Client files: %s" % os.path.join(p["alice"], "sources"))
    print("Output folder: %s" % p["alice"])


def cmd_next(folder, only=None):
    p = paths(folder)
    texts = all_texts(p)
    state = read(p["state"])
    if state:
        texts["state"] = state
    everything = "\n".join(texts.values())
    if only and only.upper() not in KINDS:
        sys.exit("Unknown kind %s. Kinds: %s" % (only, " ".join(KINDS)))
    if not only:
        print("Next free IDs (never reuse or renumber an ID, even after deleting the item):")
    for kind, (rx, width, _) in KINDS.items():
        if only and kind != only.upper():
            continue
        used = [num(x) for x in re.findall(rx, everything)]
        n = max(used + [0]) + 1
        print("  %-4s %s" % (kind, ("M%0*d" % (width, n)) if kind == "M" else "%s-%0*d" % (kind, width, n)))


def cmd_status(folder):
    p = paths(folder)
    prd, questions = read(p["prd"]) or "", read(p["questions"]) or ""
    fr = collections.Counter()
    for header, rows in tables(prd):
        si = col(header, "status")
        if header and header[0] in ("id", "fr") and si is not None:
            for r in rows:
                if re.match(r"\**FR-\d{3}", r[0]):
                    fr[cell(r, si).lower().strip("*` ") or "(blank)"] += 1
    qs = collections.Counter()
    for header, rows in tables(questions):
        si = col(header, "status")
        for r in rows:
            if re.match(r"\**Q-\d{3}", r[0]) and si is not None:
                qs[cell(r, si).lower().strip("*` ") or "(blank)"] += 1
    meetings = sorted(defined_ids(prd, "M"))
    who = identity(p)
    vm = re.search(r"^\|\s*Version\s*\|\s*(v[\d.]+)", prd, flags=re.M)
    print("Project: %s · Client: %s · Author: %s · PRD %s" % (who["name"] or "?", who["client"] or "?",
                                                         who["author"] or "?", vm.group(1) if vm else "not written yet"))
    print("Meetings: %d (%s)" % (len(meetings), ", ".join(meetings) or "none yet"))
    print("Functional requirements: %d — %s" % (sum(fr.values()), ", ".join("%d %s" % (v, k) for k, v in fr.most_common()) or "none"))
    print("Pain points: %d · Proposals: %d · Decisions: %d" % (len(defined_ids(prd, "PP")), len(defined_ids(prd, "P")), len(defined_ids(prd, "D"))))
    print("Questions: %s" % (", ".join("%d %s" % (v, k) for k, v in qs.most_common()) or "none"))
    m = manifest(p)
    state = read(p["state"]) or ""
    if m:
        pending = []
        for code, d in sorted(m["docs"].items(), key=lambda kv: int(kv[0][1:])):
            if d.get("state") == "REMOVED":
                continue
            if not processed(state, code):
                pending.append("%s (%s)" % (code, d["file"]))
        print("Sources not yet processed: %s" % ("; ".join(pending) if pending else "none"))
    waiting = answers_waiting(questions)
    if waiting:
        print("Client answers waiting to be applied: %s" % ", ".join(waiting))
    pend_u = [r[0].strip("* ") for h, rows in tables(prd) for r in rows
              if r and re.match(r"\**U-\d+", r[0]) and col(h, "status") is not None and cell(r, col(h, "status")).lower().startswith("pending")]
    if pend_u:
        print("Waiting on you (our team): %s" % ", ".join(pend_u))


def processed(state, code):
    row = re.search(r"^\|\s*%s\s*\|(.*)$" % re.escape(code), state or "", flags=re.M)
    if not row:
        return False
    cells = split_row("|" + row.group(1))
    return bool(cells) and bool(re.match(r"\s*(yes|n/a)", cells[-1] if cells[-1] else (cells[-2] if len(cells) > 1 else ""), flags=re.I))


def answers_waiting(questions):
    out = []
    for header, rows in tables(questions or ""):
        si, ai = col(header, "status"), col(header, "answer")
        if si is None or ai is None:
            continue
        for r in rows:
            if r and re.match(r"\**Q-\d{3}", r[0]) and cell(r, si).lower().strip("*` ").startswith("open") and len(cell(r, ai).strip()) >= 2:
                out.append(r[0].strip("* "))
    return out


def cmd_check(folder):
    p = paths(folder)
    fails, warns = [], []
    prd, proposal, questions = read(p["prd"]), read(p["proposal"]), read(p["questions"])
    state = read(p["state"])
    for key, text in (("prd", prd), ("proposal", proposal), ("questions", questions)):
        if text is None:
            fails.append("Missing %s" % os.path.relpath(p[key], p["alice"]))
    if fails:
        return report(fails, warns)
    texts = all_texts(p)
    rel = lambda f: os.path.relpath(f, p["alice"])

    # 1. template leftovers, fences, diagrams
    for f, t in texts.items():
        ph = re.findall(r"\{\{[^}]*\}\}", t)
        if ph:
            fails.append("%s: %d unfilled placeholder(s), e.g. %s" % (rel(f), len(ph), ph[0][:60]))
        if "TEMPLATE NOTE" in t:
            fails.append("%s: template notes still present — delete them." % rel(f))
        if len(re.findall(r"^\s*```", t, flags=re.M)) % 2:
            fails.append("%s: unbalanced ``` code fences." % rel(f))
        for i, blk in enumerate(re.findall(r"```mermaid\s*\n(.*?)```", t, flags=re.S), 1):
            if len([l for l in blk.splitlines() if l.strip() and not l.strip().startswith("%%")]) <= 1:
                fails.append("%s: Mermaid diagram #%d is empty." % (rel(f), i))

    # 2. definitions: unique, and everything cited is defined
    homes = {"QUESTIONS.md": questions, "PRD.md": prd}
    defined = {}
    for kind, (_, _, home) in KINDS.items():
        d = defined_ids(homes[home], kind)
        dup = sorted(k for k, v in d.items() if v > 1)
        if dup and kind != "M":
            fails.append("%s defined more than once in %s: %s" % (kind, home, ", ".join(dup[:15])))
        defined[kind] = set(d)
    everything = "\n".join(strip_code(t) for t in texts.values())
    for kind in KINDS:
        stray = sorted(cited_ids(everything, kind) - defined[kind], key=num)
        if stray:
            home = KINDS[kind][2]
            fails.append("Cited but never defined in %s (needs a table row or heading starting with the ID): %s"
                         % (home, ", ".join(stray[:20])))

    # 3. sources: chunk IDs exist; every source document is used; meetings have digests
    m = manifest(p)
    if m:
        live = {code: d for code, d in m["docs"].items() if d.get("state") != "REMOVED"}
        chunks = {c["id"] for d in live.values() for c in d["chunks"]}
        bad = sorted(set(re.findall(r"\b(d\d+-\d{3})\b", everything)) - chunks - {c["id"] for d in m["docs"].values() for c in d["chunks"]})
        if bad:
            fails.append("Citations of chunks that do not exist: %s" % ", ".join(bad[:15]))
        unused = []
        for code, d in sorted(live.items(), key=lambda kv: int(kv[0][1:])):
            if not re.search(r"\b%s(?:-\d{3})?\b" % code, everything):
                unused.append("%s (%s)" % (code, d["file"]))
        if unused:
            fails.append("Source documents never cited in the PRD or a meeting digest: %s — process them, or cite them in "
                         "STATE.md Sources and the PRD's source list with the reason they add nothing." % "; ".join(unused[:10]))
        unrec = ["%s (%s)" % (c, d["file"]) for c, d in sorted(live.items(), key=lambda kv: int(kv[0][1:])) if not processed(state, c)]
        if unrec:
            fails.append("Sources not marked processed (Processed = yes) in STATE.md → Sources: %s" % "; ".join(unrec[:10]))
    else:
        warns.append("No source manifest — run convert_docs.py first.")
    digests = " ".join(os.path.basename(f) for f in glob.glob(os.path.join(p["meetings"], "*.md")))
    no_digest = sorted(mid for mid in defined["M"] if mid not in digests)
    if no_digest:
        fails.append("Meetings without a digest in _work/meetings/: %s" % ", ".join(no_digest))

    # 4. PRD requirement tables: provenance and status
    fr_seen = 0
    pending_u = set()
    answered_q = set()
    for header, rows in tables(questions):
        si, ai = col(header, "status"), col(header, "answer")
        for r in rows:
            if r and re.match(r"\**Q-\d{3}", r[0]):
                st = cell(r, si).lower() if si is not None else ""
                if st.startswith("answered") or (si is None and len(cell(r, ai).strip()) >= 2):
                    answered_q.add(re.match(r"\**(Q-\d{3})", r[0]).group(1))
    for header, rows in tables(prd):
        if not header or header[0] not in ("id", "fr", "pp", "p", "br"):
            continue
        si, srci = col(header, "status"), col(header, "source", "evidence", "basis")
        for r in rows:
            u = re.match(r"\**(U-\d+)", r[0]) if r else None
            if u:
                st = cell(r, si).lower().strip("*` ")
                if si is None or not st.startswith(U_STATUSES):
                    fails.append("%s status '%s' — use: answered, sent to client (Q-…), or pending." % (u.group(1), st))
                elif st.startswith("pending"):
                    pending_u.add(u.group(1))
                continue
            a = re.match(r"\**(ASM-\d+)", r[0]) if r else None
            if a:
                src = cell(r, srci) if srci is not None else " ".join(r[1:])
                if not re.search(r"\[(?:U|D)-\d+", src):
                    fails.append("%s is an assumption nobody approved — ask the user; an assumption needs [U-..] or [D-..]." % a.group(1))
                continue
            rid = re.match(r"\**((?:FR|PP|BR|P)-\d+)", r[0]) if r else None
            if not rid:
                continue
            rid = rid.group(1)
            src = cell(r, srci) if srci is not None else " ".join(r[1:])
            if not TAG_RE.search(src):
                fails.append("%s has no provenance tag such as [M02@00:14:32], [d1-003], [P-02], [RS-01], [ASM-01]." % rid)
                continue
            status = cell(r, si).lower().strip("*` ")
            if rid.startswith("FR"):
                fr_seen += 1
                if si is None or not status.startswith(FR_STATUSES):
                    fails.append("%s status '%s' — use: %s." % (rid, status, ", ".join(FR_STATUSES)))
                elif status.startswith("confirmed") and any(t in pending_u for t in re.findall(r"U-\d+", src)) and not \
                        re.search(r"\[(?:M\d{2}|d\d+-|D-)", src):
                    fails.append("%s is 'confirmed' only by a clarification still pending with the user." % rid)
                elif status.startswith("confirmed") and not CLIENT_EVIDENCE.search(src):
                    fails.append("%s is 'confirmed' but cites no meeting, client document or decision — the client never said it. "
                                 "Mark it 'proposed' or 'to confirm'." % rid)
                elif status.startswith("proposed") and not re.search(r"\[(?:P|RS)-", src):
                    warns.append("%s is 'proposed' but cites no proposal (P-) or research (RS-)." % rid)
                elif status.startswith("to confirm") and not re.search(r"\[(?:Q|ASM|U)-", src):
                    warns.append("%s is 'to confirm' but cites no question (Q-, U-) or assumption (ASM-)." % rid)
                elif status.startswith("to confirm"):
                    qs_here = re.findall(r"Q-\d{3}", src)
                    if qs_here and all(q in answered_q for q in qs_here):
                        fails.append("%s is still 'to confirm' but its question(s) %s are answered — apply the answer." % (rid, ", ".join(qs_here)))
            elif rid.startswith("P-") and si is not None and not status.startswith(P_STATUSES):
                fails.append("%s status '%s' — use: %s." % (rid, status, ", ".join(P_STATUSES)))
    if fr_seen == 0:
        fails.append("PRD.md has no functional-requirement table (rows starting '| FR-001 |' under a header starting '| ID |').")
    m_count = re.search(r"\|\s*Requirements\s*\|\s*(\d+)\s*functional", prd)
    if m_count and int(m_count.group(1)) != fr_seen:
        fails.append("PRD header says %s functional requirements; the tables have %d." % (m_count.group(1), fr_seen))

    # 5. questions
    q_seen = 0
    for header, rows in tables(questions):
        si, ai, wi = col(header, "status"), col(header, "answer"), col(header, "why")
        for r in rows:
            if not (r and re.match(r"\**Q-\d{3}", r[0])):
                continue
            q_seen += 1
            st = cell(r, si).lower().strip("*` ")
            if si is None and ai is not None and len(cell(r, ai).strip()) >= 2:
                continue  # the "Already answered" table
            if si is None or not st.startswith(Q_STATUSES):
                fails.append("%s status '%s' — use open, answered or withdrawn." % (r[0].strip("* "), st))
            elif st.startswith("answered") and len(cell(r, ai).strip()) < 2:
                fails.append("%s is 'answered' but the Answer is empty." % r[0].strip("* "))
            if wi is not None and len(cell(r, wi)) < 5:
                warns.append("%s has no 'why we ask'." % r[0].strip("* "))
    if q_seen == 0:
        warns.append("QUESTIONS.md has no questions (rows starting '| Q-001 |'). Fine only if nothing is unclear.")
    waiting = answers_waiting(questions)
    if waiting:
        fails.append("The client has answered %s but the answers are not applied yet (status still open)." % ", ".join(waiting))
    qtext = LEGEND_RE.sub("", questions)
    if re.search(r"\[(?:M\d{2}|d\d+-\d{3}|U-\d+)[^\]]*\]", qtext):
        fails.append("QUESTIONS.md contains internal source tags — it goes to the client.")
    q_internal = sorted(set(re.findall(r"\b(?:FR-\d{3}|BR-\d+|PP-\d+|RS-\d+|ASM-\d+|U-\d+|(?<![A-Z])P-\d+|(?<![A-Z])D-\d+)\b", qtext)))
    if q_internal:
        warns.append("QUESTIONS.md shows internal IDs (%s) — the client only needs Q-numbers." % ", ".join(q_internal[:6]))

    # 6. proposal is client-facing and plain
    prop = strip_code(proposal)
    leaks = sorted(set(re.findall(r"\[(?:M\d{2}(?:@[\d:]+)?|d\d+-\d{3})[^\]]*\]", prop)))
    if leaks:
        fails.append("PROPOSAL.md contains internal source tags (e.g. %s) — the client document must be clean." % leaks[0])
    internal = sorted(set(re.findall(r"\b(?:FR-\d{3}|BR-\d+|PP-\d+|RS-\d+|ASM-\d+|U-\d+|(?<![A-Z])P-\d+|(?<![A-Z])D-\d+)\b", prop)))
    if internal:
        warns.append("PROPOSAL.md shows internal IDs (%s) — clients do not need them." % ", ".join(internal[:6]))
    if re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/\w|\bSELECT\b.+\bFROM\b", proposal):
        fails.append("PROPOSAL.md contains technical content (endpoints or SQL).")
    words = re.findall(r"[a-z][a-z-]+", prop.lower())
    jargon = collections.Counter(w for w in words if w in JARGON)
    if sum(jargon.values()) > 3:
        warns.append("PROPOSAL.md uses technical words: %s — say it in plain language." % ", ".join(k for k, _ in jargon.most_common(6)))
    money_rx = r"(?:\b(?:USD|KES|KSh|Ksh|MYR|RM|EUR|GBP|ZAR|NGN|UGX|TZS)\s?\d|[$€£]\s?\d)"
    dur_rx = r"\b%s\s*(?:-\s*%s\s*)?(?:days?|weeks?|months?|sprints?)\b" % (WORD_NUM, WORD_NUM)
    plan_like = "".join(section(proposal, pat) for pat in (r"phase", r"deliver", r"how we will", r"roll.?out", r"plan",
                                                           r"timeline", r"schedule", r"cost", r"price", r"invest", r"fee"))
    money = re.findall(money_rx, plan_like)
    durations = re.findall(dur_rx, plan_like, flags=re.I)
    if money or durations:
        fails.append("PROPOSAL.md delivery/plan section shows %s (e.g. '%s') — the proposal lists phases only, with no timeline "
                     "and no price. If it describes a condition rather than a delivery time, reword it without a duration "
                     "(e.g. 'once there is enough sales history')."
                     % (", ".join((["prices"] if money else []) + (["durations"] if durations else [])),
                        (money or durations)[0] if isinstance((money or durations)[0], str) else ""))
    elsewhere = re.findall(money_rx, prop)
    if elsewhere and not money:
        warns.append("PROPOSAL.md mentions amounts (%s) — fine for the client's own figures, never for our price." % elsewhere[0])
    if re.search(r"^##.*(regulat|compliance|legal)", proposal, flags=re.M | re.I):
        warns.append("PROPOSAL.md has a regulations/compliance section — regulations belong in the internal PRD.")
    author = identity(p, state or "")["author"]
    if not author:
        fails.append("No author in atlas.json or _work/STATE.md — ask the user whose name goes on the proposal and "
                     "record it in STATE.md.")
    elif author.lower() not in ("none", "no branding", "-", "—") and author.lower() not in proposal.lower():
        fails.append("PROPOSAL.md does not show the author '%s'." % author)

    # 7. structure that atlasctl and the gates read
    for heading in ("## Needed before we start", "## Can be answered later", "## Already answered"):
        if not re.search(r"^%s\s*$" % re.escape(heading), questions, flags=re.M | re.I):
            fails.append("QUESTIONS.md lacks the section '%s' (atlasctl counts open questions by section)." % heading)
    q_valid = Q_STATUSES + ("sent", "waiting")
    for header, rows in tables(questions):
        if not any(r and re.match(r"\**Q-\d{3}", r[0]) for r in rows):
            continue
        if not header or not header[-1].startswith("status"):
            fails.append("QUESTIONS.md: a question table's last column is '%s' — it must be Status." % (header[-1] if header else ""))
        if any(r and re.match(r"\**Q-\d{3}", r[0]) and r[-1].lower().strip("*` ").startswith("open") for r in rows) \
                and col(header, "your answer", "answer") is None:
            fails.append("QUESTIONS.md: a table with open questions has no 'Your answer' column — the client fills it in.")
        for r in rows:
            if r and re.match(r"\**Q-\d{3}", r[0]):
                last = r[-1].lower().strip("*` ")
                if not last.startswith(q_valid):
                    fails.append("%s: last cell '%s' is not a status (open, answered, withdrawn) — atlasctl reads it."
                                 % (r[0].strip("* "), r[-1][:30]))
    fr_tables = [h for h, rows in tables(prd) if any(r and re.match(r"\**FR-\d{3}", r[0]) for r in rows)]
    for h in fr_tables:
        if not h or h[0].strip("* ") != "id" or col(h, "priority") is None or col(h, "status") is None:
            fails.append("PRD.md: every FR table needs the columns ID … Priority … Status (header now: %s)." % " | ".join(h))
            break
    if not re.search(r"^## 15\.\s", prd, flags=re.M):
        fails.append("PRD.md: the regulations section must be numbered '## 15. Regulations and compliance' (G1 reads it).")
    if not re.search(r"^\|\s*Version\s*\|\s*v\d+\.\d+", prd, flags=re.M):
        fails.append("PRD.md header has no '| Version | v0.1 — YYYY-MM-DD |' row (needed for doc.version events).")

    # 8. size sanity
    kb = lambda t: len(t.encode("utf-8")) / 1024.0
    if kb(proposal) > 45:
        warns.append("PROPOSAL.md is %d KB — a client will not read that much. Aim for under ~25 KB." % kb(proposal))
    if kb(prd) > 250:
        warns.append("PRD.md is %d KB — consider whether detail is repeated." % kb(prd))

    print("PRD: %d functional requirements · %d meetings · %d questions" % (fr_seen, len(defined["M"]), q_seen))
    report(fails, warns)


def cmd_check_client(path):
    """A client-facing document: client update, handover pack, proposal or questions."""
    text = read(path)
    if text is None:
        sys.exit("Not found: %s" % path)
    fails, warns = [], []
    body = strip_code(LEGEND_RE.sub("", text))
    body_nc = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    if re.findall(r"\{\{[^}]*\}\}", text):
        fails.append("Unfilled placeholders, e.g. %s" % re.findall(r"\{\{[^}]*\}\}", text)[0][:60])
    if "TEMPLATE NOTE" in text:
        fails.append("Template notes still present — delete them.")
    tags = sorted(set(SOURCE_TAG_RE.findall(body_nc)))
    if tags:
        fails.append("Internal source tags (e.g. %s) — the client never sees these." % tags[0])
    ids = sorted(set(INTERNAL_ID_RE.findall(body_nc)))
    if ids:
        fails.append("Internal IDs (%s) — describe the thing in plain words ('the online ordering', 'Phase 1')."
                     % ", ".join(ids[:8]))
    low = body_nc.lower()
    proc = sorted({m.group(0) for w in PROCESS_WORDS for m in [re.search(r"\b%s\b" % w, low)] if m})
    if proc:
        fails.append("Internal process words (%s) — the client does not know our process; say what it means for them."
                     % ", ".join(proc[:6]))
    words = re.findall(r"[a-z][a-z-]+", low)
    jargon = collections.Counter(w for w in words if w in JARGON)
    if jargon:
        (fails if sum(jargon.values()) > 3 else warns).append(
            "Technical words: %s — say it in plain language." % ", ".join(k for k, _ in jargon.most_common(6)))
    money = re.findall(MONEY_RX, body_nc)
    if money:
        warns.append("Mentions amounts (%s) — only the client's own figures or a price the user agreed to send." % money[0])
    if re.search(r"^##.*(regulat|compliance|legal)", text, flags=re.M | re.I):
        warns.append("Has a regulations/compliance section — those stay internal unless the user asks.")
    print("Checked %s (%d KB)" % (path, len(text.encode("utf-8")) // 1024))
    report(fails, warns)


def report(fails, warns):
    for w in warns:
        print("WARN  " + w)
    for f in fails:
        print("FAIL  " + f)
    if fails:
        print("\nResult: FAIL (%d issue(s))." % len(fails))
        sys.exit(1)
    print("\nResult: PASS" + (" with %d warning(s)." % len(warns) if warns else "."))


def main():
    a = sys.argv[1:]
    if a and a[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if not a or a[0] not in ("init", "next", "check", "status", "check-client"):
        print(__doc__)
        sys.exit(2)
    if a[0] == "check-client":
        if len(a) != 2:
            sys.exit("usage: alice.py check-client <file.md>")
        return cmd_check_client(a[1])
    rest = a[1:]
    if a[0] == "next":
        kind = None
        if rest and rest[-1].upper() in KINDS and not os.path.isdir(rest[-1]):
            kind = rest.pop()
        if len(rest) > 1:
            print(__doc__)
            sys.exit(2)
        return cmd_next(resolve_project(rest[0] if rest else None), kind)
    if len(rest) > 1:
        print(__doc__)
        sys.exit(2)
    {"init": cmd_init, "check": cmd_check, "status": cmd_status}[a[0]](resolve_project(rest[0] if rest else None))


if __name__ == "__main__":
    main()
