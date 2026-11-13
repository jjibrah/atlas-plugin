"""Small helpers for reading Markdown tables and IDs. Standard library only, Python 3.9+."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

ID_RE = re.compile(
    r"\b(PRJ-\d{4}|FR-\d{2,}|BR-\d{2,}|PP-\d{2,}|WF-\d{2,}|P-\d{2,}|D-\d{2,}|RS-\d{2,}|ASM-T?\d+|U-\d{2,}|Q-\d{3,}"
    r"|REQ-\d{2,}|AC-\d{2,}|AD-\d+|OQ-\d+|WP-\d{2,}|TC-\d{2,}|CR-\d{2,}|M\d{1,2}|G[1-5])\b"
)
# IDs that only make sense as a row's own ID (too short to be reliable as links inside prose)
WEAK_LINK = re.compile(r"^(M\d{1,2}|G[1-5])$")


def strip_noise(text: str) -> str:
    """Remove HTML comments and fenced code blocks (keeps line count stable)."""
    def blank(m: "re.Match[str]") -> str:
        return "\n" * m.group(0).count("\n")
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"^```.*?^```", blank, text, flags=re.S | re.M)
    return text


def split_row(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells, cur, esc = [], "", False
    for ch in s:
        if esc:
            cur += ch
            esc = False
        elif ch == "\\":
            cur += ch
            esc = True
        elif ch == "|":
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def is_sep(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", line))


class Table:
    def __init__(self, headers: List[str], rows: List[List[str]], line: int, heading: str):
        self.headers = headers
        self.rows = rows
        self.line = line
        self.heading = heading

    def col(self, *names: str) -> Optional[int]:
        """Index of the first header that starts with (case-insensitive) any of names."""
        low = [h.lower().strip("* ") for h in self.headers]
        for n in names:
            n = n.lower()
            for i, h in enumerate(low):
                if h == n or h.startswith(n):
                    return i
        return None

    def dicts(self) -> Iterator[Dict[str, str]]:
        for r in self.rows:
            yield {self.headers[i]: (r[i] if i < len(r) else "") for i in range(len(self.headers))}


def tables(text: str) -> List[Table]:
    lines = strip_noise(text).split("\n")
    out: List[Table] = []
    heading = ""
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            heading = ln.lstrip("#").strip()
        if ln.strip().startswith("|") and i + 1 < len(lines) and is_sep(lines[i + 1]):
            headers = split_row(ln)
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            out.append(Table(headers, rows, i + 1, heading))
            i = j
            continue
        i += 1
    return out


def read_tables(path: Path) -> List[Table]:
    try:
        return tables(path.read_text(encoding="utf-8", errors="replace"))
    except FileNotFoundError:
        return []


def ids_in(text: str) -> List[str]:
    return ID_RE.findall(text or "")


def expand_ranges(text: str) -> List[str]:
    """IDs in text, expanding ranges like 'WP-01–WP-03' or 'REQ-010-014' (≤ 50 items)."""
    found = set(ids_in(text))
    for kind, a, b in re.findall(r"\b([A-Z]{1,3})-(\d+)\s*(?:–|—|-|\.\.|to)\s*(?:[A-Z]{1,3}-)?(\d+)\b", text or ""):
        x, y = int(a), int(b)
        if 0 < y - x <= 50:
            for n in range(x, y + 1):
                found.add("%s-%0*d" % (kind, len(a), n))
    return sorted(found)
