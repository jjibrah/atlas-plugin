#!/usr/bin/env python3
"""Markdown → PDF for client documents, using a locally installed Chrome / Edge / Chromium / Brave in headless mode.

No Python packages needed. Mermaid diagrams are rendered by mermaid.js (loaded from a CDN while printing; if the
machine is offline the diagram source is shown instead). If no browser is found, an HTML file is written next to the
requested PDF and the caller is told to print it.

    python3 pdf_export.py <in.md> <out.pdf> [--title "Project name"] [--subtitle "…"]
"""
from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"

BROWSERS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
BROWSER_CMDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge",
                "brave-browser"]

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color: #1d232b;
       font-size: 10.5pt; line-height: 1.5; }
header.doc { border-bottom: 2px solid #2b5c8a; margin-bottom: 18px; padding-bottom: 8px; }
header.doc .project { font-size: 9pt; letter-spacing: .08em; text-transform: uppercase; color: #2b5c8a; }
header.doc .sub { font-size: 9pt; color: #5b6573; }
h1 { font-size: 20pt; margin: 6px 0 12px; color: #13202e; }
h2 { font-size: 14pt; margin: 22px 0 8px; color: #13202e; border-bottom: 1px solid #d9dee5; padding-bottom: 3px; }
h3 { font-size: 11.5pt; margin: 16px 0 6px; }
h4 { font-size: 10.5pt; margin: 12px 0 4px; }
p { margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #cfd6de; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #eef2f6; }
td:empty { min-width: 110px; height: 26px; }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 9pt; background: #f2f4f7; padding: 0 3px; }
pre { background: #f6f8fa; padding: 8px; font-size: 8.5pt; white-space: pre-wrap; }
pre.mermaid { background: none; text-align: center; }
blockquote { border-left: 3px solid #2b5c8a; margin: 8px 0; padding: 2px 10px; color: #3d4752; background: #f5f8fb; }
hr { border: none; border-top: 1px solid #d9dee5; margin: 16px 0; }
ul, ol { margin: 4px 0 8px 22px; padding: 0; }
li { margin: 2px 0; }
footer.doc { margin-top: 28px; font-size: 8.5pt; color: #7a8491; border-top: 1px solid #d9dee5; padding-top: 6px; }
"""


def inline(s: str) -> str:
    codes: List[str] = []

    def keep(m: "re.Match[str]") -> str:
        codes.append("<code>%s</code>" % html.escape(m.group(1)))
        return "\x00%d\x00" % (len(codes) - 1)
    s = re.sub(r"`([^`]+)`", keep, s)
    s = html.escape(s, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img alt="\1" src="\2" style="max-width:100%">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", s)
    s = s.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def cells(line: str) -> List[str]:
    t = line.strip()
    t = t[1:] if t.startswith("|") else t
    t = t[:-1] if t.endswith("|") else t
    return [c.strip() for c in re.split(r"(?<!\\)\|", t)]


def md_to_html(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines = text.split("\n")
    out: List[str] = []
    i = 0
    list_stack: List[tuple] = []  # (indent, tag)

    def close_lists(to_indent: int = -1) -> None:
        while list_stack and list_stack[-1][0] > to_indent:
            out.append("</li></%s>" % list_stack.pop()[1])

    para: List[str] = []

    def flush_para() -> None:
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        fence = re.match(r"^\s*```\s*(\w*)", ln)
        if fence:
            flush_para(); close_lists()
            lang = fence.group(1)
            j = i + 1
            body = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body.append(lines[j])
                j += 1
            code = "\n".join(body)
            if lang == "mermaid":
                out.append('<pre class="mermaid">%s</pre>' % html.escape(code))
            else:
                out.append("<pre><code>%s</code></pre>" % html.escape(code))
            i = j + 1
            continue
        if not s:
            flush_para()
            if not (i + 1 < len(lines) and re.match(r"^\s*([-*+]|\d+\.)\s", lines[i + 1])):
                close_lists()
            i += 1
            continue
        h = re.match(r"^(#{1,6})\s+(.*)", s)
        if h:
            flush_para(); close_lists()
            n = len(h.group(1))
            out.append("<h%d>%s</h%d>" % (n, inline(h.group(2).strip("# ")), n))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush_para(); close_lists()
            out.append("<hr>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush_para(); close_lists()
            head = cells(ln)
            out.append("<table><thead><tr>%s</tr></thead><tbody>" % "".join("<th>%s</th>" % inline(c) for c in head))
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                row = cells(lines[j])
                out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in row))
                j += 1
            out.append("</tbody></table>")
            i = j
            continue
        if s.startswith(">"):
            flush_para(); close_lists()
            body = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                body.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % md_to_html("\n".join(body)))
            continue
        li = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)", ln)
        if li:
            flush_para()
            ind = len(li.group(1).replace("\t", "    "))
            tag = "ol" if li.group(2)[0].isdigit() else "ul"
            item = li.group(3)
            item = re.sub(r"^\[ \]\s", "☐ ", item)
            item = re.sub(r"^\[[xX]\]\s", "☑ ", item)
            if list_stack and list_stack[-1][0] == ind:
                out.append("</li><li>%s" % inline(item))
            elif list_stack and list_stack[-1][0] > ind:
                close_lists(ind)
                if list_stack and list_stack[-1][0] == ind:
                    out.append("</li><li>%s" % inline(item))
                else:
                    list_stack.append((ind, tag))
                    out.append("<%s><li>%s" % (tag, inline(item)))
            else:
                list_stack.append((ind, tag))
                out.append("<%s><li>%s" % (tag, inline(item)))
            i += 1
            continue
        if list_stack and ln.startswith(" "):
            out.append(" " + inline(s))
            i += 1
            continue
        close_lists()
        para.append(s)
        i += 1
    flush_para(); close_lists()
    return "\n".join(out)


def build_html(md_text: str, title: str, subtitle: str) -> str:
    body = md_to_html(md_text)
    has_mermaid = 'class="mermaid"' in body
    script = ('<script src="%s"></script><script>mermaid.initialize({startOnLoad:true, theme:"neutral"});</script>'
              % MERMAID) if has_mermaid else ""
    return ("<!doctype html><html><head><meta charset='utf-8'><title>%s</title><style>%s</style></head><body>"
            "<header class='doc'><div class='project'>%s</div>%s</header>%s"
            "<footer class='doc'>%s</footer>%s</body></html>") % (
        html.escape(title), CSS, html.escape(title),
        ("<div class='sub'>%s</div>" % html.escape(subtitle)) if subtitle else "", body, html.escape(title), script)


def find_browser() -> Optional[str]:
    env = os.environ.get("ATLAS_BROWSER")
    if env and Path(env).exists():
        return env
    for b in BROWSERS:
        if Path(b).exists():
            return b
    for c in BROWSER_CMDS:
        w = shutil.which(c)
        if w:
            return w
    return None


def _print(cmd: List[str], out: Path, limit: float = 120.0) -> str:
    """Run headless Chrome; some versions write the PDF and then never exit, so stop it once the file is complete."""
    import time
    if out.exists():
        out.unlink()
    errf = tempfile.TemporaryFile()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=errf, stdin=subprocess.DEVNULL)
    start, last, stable = time.time(), -1, 0
    while time.time() - start < limit:
        if proc.poll() is not None:
            break
        size = out.stat().st_size if out.exists() else -1
        if size > 0 and size == last:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last = size
        time.sleep(0.5)
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    errf.seek(0)
    return errf.read().decode("utf-8", "replace")


def export(src: Path, out: Path, title: str = "", subtitle: str = "") -> Path:
    src, out = Path(src), Path(out)
    page = build_html(src.read_text(encoding="utf-8", errors="replace"), title or src.stem, subtitle)
    out.parent.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    if not browser:
        h = out.with_suffix(".html")
        h.write_text(page, encoding="utf-8")
        print("atlas: no Chrome/Edge/Chromium found — wrote %s; open it and Print → Save as PDF." % h, file=sys.stderr)
        return h
    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / "doc.html"
        hp.write_text(page, encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run",
               "--user-data-dir=%s" % (Path(td) / "profile"), "--virtual-time-budget=15000",
               "--print-to-pdf=%s" % out, hp.as_uri()]
        err = _print(cmd, out)
        if not out.exists():
            cmd[1] = "--headless"
            err = _print(cmd, out)
        if not out.exists():
            h = out.with_suffix(".html")
            h.write_text(page, encoding="utf-8")
            print("atlas: PDF export failed (%s) — wrote %s instead." % (err[-200:].strip(), h), file=sys.stderr)
            return h
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--title", default=""); ap.add_argument("--subtitle", default="")
    a = ap.parse_args()
    print(export(Path(a.src), Path(a.out), a.title, a.subtitle))
