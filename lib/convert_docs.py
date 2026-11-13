#!/usr/bin/env python3
"""ATLAS intake (shared by every agent): convert source material (transcripts, notes, SOPs, documents) into small,
addressable markdown chunks.

Usage:
  convert_docs.py <source_dir> <out_dir> [--force] [--exclude NAME ...]
                                                     convert / refresh (unchanged files are reused); folders named
                                                     _work .git node_modules views log state snapshots are always
                                                     skipped, and so is the ATLAS placeholder README.txt
  convert_docs.py --install-deps                     create the ATLAS venv ($ATLAS_HOME/venv, default ~/.atlas/venv)
                                                     with the PDF engine (same as `atlasctl setup`)
  convert_docs.py diff <out_dir> <docA> <docB>       unified diff of two converted docs (e.g. d1.prev d1)
  convert_docs.py reindex <out_dir>                  rebuild INDEX.md after editing chunk files by hand

Output layout (<out_dir> is normally <folder>/_work/sources):
  INDEX.md, manifest.json, d1/d1-001.md ..., d1/media/*

Formats: PDF (PyMuPDF: text, headings, tables, figure detection; falls back to pdfplumber,
pypdf, pdftotext), DOCX / XLSX / PPTX (standard library, incl. embedded images, Word comments
and footnotes), VTT / SRT caption transcripts (one timestamp per cue), HTML, MD, TXT, CSV, JSON,
and standalone images.

PDF engine: when PyMuPDF is not importable and a PDF needs converting, the script re-executes itself with the ATLAS
venv's python if that venv exists; otherwise it falls back to a text-only engine and says to run `atlasctl setup`.
Python 3.9+, standard library only outside the venv.
"""
from __future__ import annotations

import collections
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

LIB_DIR = os.path.dirname(os.path.abspath(__file__))
ATLAS_HOME = os.path.expanduser(os.environ.get("ATLAS_HOME") or os.path.join("~", ".atlas"))
VENV_DIR = os.path.join(ATLAS_HOME, "venv")


def _venv_python(venv):
    return os.path.join(venv, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv, "bin", "python")


VENV_PY = _venv_python(VENV_DIR)
ALWAYS_SKIP = {"_work", ".git", "node_modules", "views", "log", "state", "snapshots", ".venv", "__pycache__"}
SETUP_HINT = "python3 %s setup   (or: python3 %s --install-deps)" % (os.path.join(LIB_DIR, "atlasctl.py"),
                                                                    os.path.abspath(__file__))


def _has_fitz():
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        return False


def _needs_pdf_engine(src):
    """True when the source folder holds a PDF (only then is the venv worth re-executing into)."""
    if not src or not os.path.isdir(src):
        return False
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ALWAYS_SKIP]
        if any(f.lower().endswith(".pdf") for f in filenames):
            return True
    return False


def _maybe_reexec_in_venv(src=None):
    """Re-run with the ATLAS venv's python when PyMuPDF is needed, missing here, and the venv exists."""
    if os.environ.get("ATLAS_NO_VENV") or _has_fitz() or not _needs_pdf_engine(src):
        return
    if not os.path.exists(VENV_PY):
        print("Note: PDFs found but the PDF engine (PyMuPDF) is not installed — run:\n  %s\n"
              "Continuing with a text-only engine." % SETUP_HINT, file=sys.stderr)
        return
    if os.path.realpath(sys.prefix) == os.path.realpath(VENV_DIR):
        return
    os.environ["ATLAS_NO_VENV"] = "1"  # never loop
    os.execv(VENV_PY, [VENV_PY, os.path.abspath(__file__)] + sys.argv[1:])


def _is_atlas_placeholder(path):
    """The README.txt that `atlasctl new` puts in discovery/sources/ is not client material."""
    if os.path.basename(path).lower() != "readme.txt":
        return False
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(400)
    except OSError:
        return False
    return head.startswith("Drop the client") or "then run /alice" in head


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"
MC_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}
TARGET_WORDS = 1800      # start looking for a heading boundary after this many words
HARD_CAP_WORDS = 3000    # split at any block boundary beyond this
SHEET_ROWS_PER_BLOCK = 120
MAX_SHEET_ROWS = 5000
MAX_RENDERED_PAGES = 60
RULING_PATH_LIMIT = 1500  # more "ruling" paths than this on a page = diagram, not a table


# ------------------------------------------------------------------ helpers
def words_in(text):
    return len(text.split())


def md_cell(text):
    return re.sub(r"\s*\n\s*", " ", str(text or "")).replace("|", "\\|").strip()


def md_table(rows):
    rows = [[md_cell(c) for c in r] for r in rows]
    rows = [r for r in rows if any(r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def block(text, level=0, page=None, flags=()):
    return {"text": text.strip(), "level": level, "page": page, "flags": set(flags)}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def iter_skip_fallback(node):
    """Like node.iter() but ignores mc:Fallback copies (duplicated text boxes / drawings)."""
    stack = [node]
    while stack:
        n = stack.pop()
        if n.tag == MC_FALLBACK:
            continue
        yield n
        stack.extend(reversed(list(n)))


def read_rels(z, rels_path):
    out = {}
    if rels_path in z.namelist():
        for rel in ET.fromstring(z.read(rels_path)).findall(PR + "Relationship"):
            out[rel.get("Id")] = rel.get("Target")
    return out


def save_media(z, member, media_dir):
    if member not in z.namelist():
        return None
    os.makedirs(media_dir, exist_ok=True)
    name = os.path.basename(member)
    with open(os.path.join(media_dir, name), "wb") as f:
        f.write(z.read(member))
    return "media/" + name


# ------------------------------------------------------------------ PDF
def _ruling_paths(drawings):
    """Keep only table rulings / boxes. Drops glyph outlines (Type-3 fonts draw text as paths),
    which otherwise make table detection take minutes and find nothing."""
    keep = []
    for d in drawings:
        kinds = {i[0] for i in d["items"]}
        if "c" in kinds or "qu" in kinds:
            continue
        r = d["rect"]
        if kinds == {"l"} and d.get("type") == "f" and r.width < 25 and r.height < 25:
            continue
        if r.width < 3 and r.height < 3:  # dotted leaders, bullets
            continue
        keep.append(d)
    return keep


def convert_pdf_fitz(path, media_dir):
    import fitz  # type: ignore
    doc = fitz.open(path)
    n = len(doc)
    size_chars = collections.Counter()
    page_dicts = []
    edge_lines = collections.Counter()
    for page in doc:
        d = page.get_text("dict")
        page_dicts.append(d)
        h = page.rect.height
        for b in d["blocks"]:
            for l in b.get("lines", []):
                text = "".join(s["text"] for s in l["spans"]).strip()
                for s in l["spans"]:
                    size_chars[round(s["size"], 1)] += len(s["text"].strip())
                if text and (l["bbox"][1] < h * 0.08 or l["bbox"][3] > h * 0.92):
                    edge_lines[re.sub(r"\d+", "#", text)] += 1
    body = size_chars.most_common(1)[0][0] if size_chars else 10.0
    repeated = {k for k, v in edge_lines.items() if n >= 4 and v >= n * 0.5}
    image_use = collections.Counter()
    for page in doc:
        for im in page.get_images(full=True):
            image_use[im[0]] += 1
    logos = {x for x, c in image_use.items() if n >= 4 and c >= n * 0.5}

    blocks, rendered, tables_total, visual_pages = [], 0, 0, []
    for pno, page in enumerate(doc, 1):
        d = page_dicts[pno - 1]
        items = []  # (y, x, block)
        flags = set()
        table_rects = []
        try:
            rulings = _ruling_paths(page.get_drawings())
        except Exception:
            rulings = []
        dense_vector = len(rulings) > RULING_PATH_LIMIT
        if rulings and not dense_vector:
            try:
                for tb in page.find_tables(paths=rulings).tables:
                    rows = tb.extract()
                    if tb.row_count >= 2 and tb.col_count >= 2:
                        md = md_table(rows)
                        if md:
                            rect = fitz.Rect(tb.bbox)
                            table_rects.append(rect)
                            items.append((rect.y0, rect.x0, block(md, page=pno, flags=["tables"])))
                            tables_total += 1
            except Exception:
                pass
        chars = len(page.get_text().strip())
        # vector figures: many line/box paths that do not belong to any detected table
        loose = sum(1 for r in rulings if not any(fitz.Rect(r["rect"]).intersects(tr + (-3, -3, 3, 3)) for tr in table_rects))
        dense_vector = dense_vector or loose >= 40
        for b in d["blocks"]:
            if b.get("type") != 0:
                continue
            rect = fitz.Rect(b["bbox"])
            centre = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
            if any(centre in tr for tr in table_rects):
                continue
            lines, max_size = [], 0.0
            for l in b.get("lines", []):
                text = "".join(s["text"] for s in l["spans"]).strip()
                if not text or re.sub(r"\d+", "#", text) in repeated:
                    continue
                lines.append(text)
                max_size = max([max_size] + [s["size"] for s in l["spans"] if s["text"].strip()])
            if not lines:
                continue
            text = " ".join(lines)
            level = 0
            if len(text) <= 140 and max_size >= body * 1.25:
                level = 2 if max_size >= body * 1.6 else 3
            blk = block(("#" * level + " " + re.sub(r" {2,}", " ", text)) if level else re.sub(r" {2,}", " ", text), level=level, page=pno)
            blk["y1"] = rect.y1
            items.append((rect.y0, rect.x0, blk))
        has_image = False
        try:
            for info in page.get_image_info(xrefs=True):
                x0, y0, x1, y1 = info["bbox"]
                if info.get("xref") not in logos and (x1 - x0) > 60 and (y1 - y0) > 60:
                    has_image = True  # icons and bullets are smaller than this
        except Exception:
            has_image = any(im[0] not in logos for im in page.get_images(full=True))
        scanned = chars < 40
        if has_image or scanned or dense_vector:
            flags.add("visual")
            visual_pages.append(pno)
            note = "> **Visual on page %d**" % pno
            if rendered < MAX_RENDERED_PAGES:
                try:
                    os.makedirs(media_dir, exist_ok=True)
                    name = "page-%03d.png" % pno
                    page.get_pixmap(dpi=110).save(os.path.join(media_dir, name))
                    rendered += 1
                    note += " — view `media/%s`" % name
                except Exception:
                    note += " — view this page of the original PDF"
            else:
                note += " — view this page of the original PDF"
            note += (" (scanned page: transcribe it)." if scanned else
                     " and add what the figure shows under `### Visual notes`.")
            items.append((1e9, 0, block(note, page=pno, flags=["visual"])))
        items.sort(key=lambda t: (round(t[0] / 4), t[1]))
        prev = None
        for y0, _, blk in items:
            # a paragraph whose first line has different styling arrives as two blocks: re-join them
            if (prev is not None and "y1" in prev and "y1" in blk and not prev["level"] and not blk["level"]
                    and 0 <= y0 - prev["y1"] < body * 0.6 and not re.match(r"[\u2022\u25aa\u25cf\-\*\u2013]|\d+[.)]\s", blk["text"])):
                prev["text"] += " " + blk["text"]
                prev["y1"] = blk["y1"]
                continue
            blocks.append(blk)
            prev = blk
    note = "%d pages, %d tables" % (n, tables_total)
    if visual_pages:
        note += ", visual pages: %s" % compact_ranges(visual_pages)
    return blocks, {"engine": "pymupdf", "pages": n, "note": note}


def compact_ranges(nums):
    nums = sorted(set(nums))
    out, start, prev = [], None, None
    for x in nums:
        if start is None:
            start = prev = x
        elif x == prev + 1:
            prev = x
        else:
            out.append("%d" % start if start == prev else "%d-%d" % (start, prev))
            start = prev = x
    if start is not None:
        out.append("%d" % start if start == prev else "%d-%d" % (start, prev))
    return ", ".join(out)


def convert_pdf(path, media_dir):
    try:
        import fitz  # noqa: F401
        return convert_pdf_fitz(path, media_dir)
    except ImportError:
        pass
    pages, engine, tables = [], None, 0
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                text = p.extract_text() or ""
                for t in p.extract_tables() or []:
                    md = md_table(t)
                    if md:
                        text += "\n\n" + md
                        tables += 1
                pages.append(text)
        engine = "pdfplumber"
    except Exception:
        pages = []
    if not pages:
        try:
            import pypdf  # type: ignore
            pages = [(p.extract_text() or "") for p in pypdf.PdfReader(path).pages]
            engine = "pypdf (text-only)"
        except Exception:
            pages = []
    if not pages and shutil.which("pdftotext"):
        try:
            txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, timeout=300).stdout
            pages = txt.split("\f")
            engine = "pdftotext (text-only)"
        except Exception:
            pages = []
    if not pages:
        return None, {"engine": None, "note": "no PDF engine — run `atlasctl setup` (or read the PDF directly)"}
    if sum(len(p.strip()) for p in pages) < 40 * max(1, len(pages)):
        return None, {"engine": engine, "note": "little or no text (scanned?) — read the PDF directly (page images may help)"}
    blocks = []
    for i, text in enumerate(pages, 1):
        for para in re.split(r"\n\s*\n", text):
            if para.strip():
                blocks.append(block(para, page=i, flags=["tables"] if para.lstrip().startswith("|") else []))
    note = "%d pages" % len(pages)
    if "text-only" in engine:
        note += " — TEXT-ONLY: tables are flattened and figures undetected; run `atlasctl setup` for full quality"
    else:
        note += ", %d tables" % tables
    return blocks, {"engine": engine, "pages": len(pages), "note": note}


# ------------------------------------------------------------------ DOCX
def docx_para(p, rels, z, media_dir):
    parts, images = [], []
    for node in iter_skip_fallback(p):
        if node.tag == W + "t" and node.text:
            parts.append(node.text)
        elif node.tag == W + "tab":
            parts.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            parts.append("\n")
        elif node.tag == A + "blip":
            target = rels.get(node.get(R + "embed") or "")
            if target:
                saved = save_media(z, "word/" + target.lstrip("/").replace("word/", ""), media_dir)
                if saved:
                    images.append(saved)
    return "".join(parts).strip(), images


def docx_para_block(p, rels, z, media_dir):
    text, images = docx_para(p, rels, z, media_dir)
    out = []
    ppr = p.find(W + "pPr")
    style, is_list, outline = "", False, None
    if ppr is not None:
        ps = ppr.find(W + "pStyle")
        if ps is not None:
            style = (ps.get(W + "val") or "").lower()
        is_list = ppr.find(W + "numPr") is not None
        ol = ppr.find(W + "outlineLvl")
        if ol is not None and (ol.get(W + "val") or "").isdigit():
            outline = int(ol.get(W + "val"))
    if text:
        m = re.search(r"heading\s*(\d)", style) or re.search(r"(?:berschrift|titre|titolo|ttulo)\s*(\d)", style)
        level = 0
        if m:
            level = min(int(m.group(1)) + 1, 6)
        elif outline is not None and outline < 6:
            level = outline + 2
        elif style == "title":
            level = 1
        if level and len(text) < 200:
            out.append(block("#" * level + " " + text, level=level))
        elif is_list or "list" in style:
            out.append(block("- " + text))
        else:
            out.append(block(text))
    for img in images:
        out.append(block("> **Image** — view `%s` and add what it shows under `### Visual notes`." % img, flags=["visual"]))
    return out


def docx_table(tbl, rels, z, media_dir):
    rows, images = [], []
    for tr in tbl.findall(W + "tr"):
        row = []
        for tc in tr.findall(W + "tc"):
            texts = []
            for p in tc.iter(W + "p"):
                t, imgs = docx_para(p, rels, z, media_dir)
                images += imgs
                if t:
                    texts.append(t)
            span = 1
            tcpr = tc.find(W + "tcPr")
            if tcpr is not None and tcpr.find(W + "gridSpan") is not None:
                try:
                    span = int(tcpr.find(W + "gridSpan").get(W + "val") or 1)
                except ValueError:
                    span = 1
            row.append(" / ".join(texts))
            row += [""] * (span - 1)
        rows.append(row)
    out = []
    md = md_table(rows)
    if md:
        out.append(block(md, flags=["tables"]))
    for img in images:
        out.append(block("> **Image (in table)** — view `%s` and add what it shows under `### Visual notes`." % img, flags=["visual"]))
    return out


def convert_docx(path, media_dir):
    blocks = []
    with zipfile.ZipFile(path) as z:
        rels = read_rels(z, "word/_rels/document.xml.rels")
        body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
        for child in body:
            if child.tag == W + "p":
                blocks += docx_para_block(child, rels, z, media_dir)
            elif child.tag == W + "tbl":
                blocks += docx_table(child, rels, z, media_dir)
            elif child.tag == W + "sdt":  # content controls (e.g. table of contents, form fields)
                for p in child.iter(W + "p"):
                    blocks += docx_para_block(p, rels, z, media_dir)
        extras = []
        for member, title, tag in (("word/footnotes.xml", "Footnotes", W + "footnote"),
                                   ("word/comments.xml", "Reviewer comments", W + "comment")):
            if member not in z.namelist():
                continue
            lines = []
            for item in ET.fromstring(z.read(member)).findall(tag):
                text = " ".join(t for t in ("".join(x.text or "" for x in p.iter(W + "t")).strip() for p in item.iter(W + "p")) if t)
                if text:
                    author = item.get(W + "author")
                    lines.append("- " + ("**%s:** " % author if author else "") + text)
            if lines:
                extras.append(block("## " + title, level=2))
                extras.append(block("\n".join(lines), flags=["comments"] if "comment" in member else []))
        blocks += extras
    return blocks, {"engine": "docx", "note": ""}


# ------------------------------------------------------------------ XLSX
def col_index(ref):
    n = 0
    for ch in re.match(r"([A-Z]+)", ref).group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def convert_xlsx(path, media_dir):
    blocks, note = [], ""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(S + "si"):
                shared.append("".join(t.text or "" for t in si.iter(S + "t")))
        rels = {}
        for rid, target in read_rels(z, "xl/_rels/workbook.xml.rels").items():
            target = target.lstrip("/")
            rels[rid] = target if target.startswith("xl/") else "xl/" + target
        for sheet in ET.fromstring(z.read("xl/workbook.xml")).iter(S + "sheet"):
            target = rels.get(sheet.get(R + "id"))
            if not target or target not in names:
                continue
            hidden = " (hidden sheet)" if sheet.get("state") in ("hidden", "veryHidden") else ""
            rows = []
            for row in ET.fromstring(z.read(target)).iter(S + "row"):
                cells = {}
                for c in row.findall(S + "c"):
                    t, v = c.get("t"), c.find(S + "v")
                    if t == "s" and v is not None:
                        val = shared[int(v.text)]
                    elif t == "inlineStr":
                        val = "".join(x.text or "" for x in c.iter(S + "t"))
                    else:
                        val = v.text if v is not None and v.text else ""
                    cells[col_index(c.get("r"))] = val
                if cells:
                    rows.append((int(row.get("r") or len(rows) + 1), [cells.get(i, "") for i in range(max(cells) + 1)]))
                if len(rows) >= MAX_SHEET_ROWS:
                    note = "sheets truncated at %d rows" % MAX_SHEET_ROWS
                    break
            blocks.append(block("## Sheet: %s%s" % (sheet.get("name"), hidden), level=2))
            if not rows:
                blocks.append(block("_(empty)_"))
                continue
            header = rows[0][1]
            for i in range(1, max(2, len(rows)), SHEET_ROWS_PER_BLOCK):
                part = rows[i:i + SHEET_ROWS_PER_BLOCK]
                label = "Rows %d–%d" % (part[0][0], part[-1][0]) if part else "Header only"
                blocks.append(block("**%s**\n\n%s" % (label, md_table([header] + [r for _, r in part])), flags=["tables"]))
    return blocks, {"engine": "xlsx", "note": note}


# ------------------------------------------------------------------ PPTX
def convert_pptx(path, media_dir):
    blocks = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        slides = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                        key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
        for i, name in enumerate(slides, 1):
            root = ET.fromstring(z.read(name))
            paras = ["".join(t.text or "" for t in p.iter(A + "t")).strip() for p in root.iter(A + "p")]
            paras = [p for p in paras if p]
            blocks.append(block("## Slide %d%s" % (i, ": " + paras[0][:80] if paras else ""), level=2, page=i))
            if paras:
                blocks.append(block("\n".join("- " + p for p in paras), page=i))
            rels = read_rels(z, "ppt/slides/_rels/%s.rels" % os.path.basename(name))
            for blip in root.iter(A + "blip"):
                target = rels.get(blip.get(R + "embed") or "")
                if target:
                    saved = save_media(z, os.path.normpath(os.path.join("ppt/slides", target)).replace("\\", "/"), media_dir)
                    if saved:
                        blocks.append(block("> **Image on slide %d** — view `%s` and add what it shows under `### Visual notes`." % (i, saved),
                                            page=i, flags=["visual"]))
            notes = "ppt/notesSlides/notesSlide%d.xml" % i
            if notes in names:
                texts = ["".join(t.text or "" for t in p.iter(A + "t")).strip() for p in ET.fromstring(z.read(notes)).iter(A + "p")]
                texts = [t for t in texts if t and not t.isdigit()]
                if texts:
                    blocks.append(block("**Speaker notes:** " + " ".join(texts), page=i))
    return blocks, {"engine": "pptx", "note": "%d slides" % len(slides)}


# ------------------------------------------------------------------ HTML / text
class _Stripper(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table"}

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n\n" if tag != "br" else "\n")
            if re.match(r"h[1-6]$", tag):
                self.parts.append("#" * int(tag[1]) + " ")
            elif tag == "li":
                self.parts.append("- ")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        elif tag in ("td", "th"):
            self.parts.append(" | ")
        elif re.match(r"h[1-6]$", tag):
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def text_to_blocks(text):
    blocks, fence = [], False
    for para in re.split(r"\n\s*\n", text):
        if not para.strip():
            continue
        if para.count("```") % 2:
            fence = not fence
        m = re.match(r"\s*(#{1,6})\s+\S", para) if not fence else None
        first = para.strip().splitlines()[0]
        if m and "\n" in para.strip():
            rest = para.strip()[len(first):]
            blocks.append(block(first, level=len(m.group(1))))
            blocks.append(block(rest))
        else:
            blocks.append(block(para, level=len(m.group(1)) if m else 0,
                                flags=["tables"] if para.lstrip().startswith("|") else []))
    return blocks


def convert_html(path, media_dir):
    s = _Stripper()
    with open(path, encoding="utf-8", errors="replace") as f:
        s.feed(f.read())
    return text_to_blocks("".join(s.parts)), {"engine": "html", "note": ""}


def convert_captions(path, media_dir):
    """WebVTT / SRT → '[hh:mm:ss] Speaker: text' lines, merging consecutive cues of one speaker."""
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        raw = f.read().replace("\r\n", "\n")
    cues = re.split(r"\n\s*\n", raw)
    lines, last_speaker = [], None
    for cue in cues:
        rows = [r.strip() for r in cue.strip().split("\n") if r.strip()]
        stamp = None
        text_rows = []
        for r in rows:
            m = re.match(r"(\d{1,2}:)?(\d{1,2}):(\d{2})[.,]\d{1,3}\s*-->", r)
            if m:
                h = int((m.group(1) or "0:")[:-1])
                stamp = "%02d:%02d:%02d" % (h, int(m.group(2)), int(m.group(3)))
            elif r.upper().startswith("WEBVTT") or r.isdigit() or r.startswith(("NOTE", "STYLE")):
                continue
            elif stamp is not None:
                text_rows.append(r)
        if not stamp or not text_rows:
            continue
        text = " ".join(text_rows)
        speaker = None
        m = re.match(r"<v\s+([^>]+)>(.*)", text)
        if m:
            speaker, text = m.group(1).strip(), m.group(2)
        else:
            m = re.match(r"([A-Z][\w .'-]{0,40}):\s+(.*)", text)
            if m:
                speaker, text = m.group(1).strip(), m.group(2)
        text = re.sub(r"</?[^>]+>", "", text).strip()
        # every cue keeps its own timestamp, so citations point at the exact moment
        label = speaker + ": " if speaker and speaker != last_speaker else ""
        lines.append("[%s] %s%s" % (stamp, label, text))
        last_speaker = speaker or last_speaker
    blocks, buf = [block("## Transcript (%s)" % os.path.basename(path), level=2)], []
    for line in lines:
        buf.append(line)
        if sum(len(x.split()) for x in buf) > 250:
            blocks.append(block("\n\n".join(buf)))
            buf = []
    if buf:
        blocks.append(block("\n\n".join(buf)))
    return blocks, {"engine": "captions", "note": "transcript, %d turns" % len(lines)}


def convert_plain(path, media_dir):
    with open(path, encoding="utf-8", errors="replace") as f:
        return text_to_blocks(f.read()), {"engine": "text", "note": ""}


CONVERTERS = {
    ".pdf": convert_pdf, ".docx": convert_docx, ".docm": convert_docx, ".xlsx": convert_xlsx, ".xlsm": convert_xlsx,
    ".pptx": convert_pptx, ".html": convert_html, ".htm": convert_html, ".txt": convert_plain,
    ".md": convert_plain, ".markdown": convert_plain, ".csv": convert_plain, ".json": convert_plain,
    ".vtt": convert_captions, ".srt": convert_captions,
}


# ------------------------------------------------------------------ chunking
def chunk_blocks(blocks):
    chunks, cur, cur_words = [], [], 0
    for b in blocks:
        if not b["text"]:
            continue
        w = words_in(b["text"])
        at_heading = b["level"] and b["level"] <= 3
        if cur and ((cur_words >= TARGET_WORDS and at_heading) or cur_words + w > HARD_CAP_WORDS):
            chunks.append(cur)
            cur, cur_words = [], 0
        cur.append(b)
        cur_words += w
    if cur:
        chunks.append(cur)
    # a trailing sliver is merged back
    if len(chunks) > 1 and sum(words_in(b["text"]) for b in chunks[-1]) < 150:
        chunks[-2] += chunks.pop()
    return chunks


def write_doc(code, rel, blocks, doc_dir):
    """Write chunk files; return chunk metadata list."""
    metas, section = [], ""
    for i, chunk in enumerate(chunk_blocks(blocks), 1):
        cid = "%s-%03d" % (code, i)
        heads = [b["text"].lstrip("# ").strip() for b in chunk if b["level"]]
        title = heads[0] if heads else (section + " (cont.)" if section else " ".join(chunk[0]["text"].split()[:8]))
        if heads:
            section = heads[-1]
        pages = sorted({b["page"] for b in chunk if b["page"]})
        flags = sorted(set().union(*[b["flags"] for b in chunk]))
        body, last_page = [], None
        for b in chunk:
            if b["page"] and b["page"] != last_page:
                body.append("<!-- page %d -->" % b["page"])
                last_page = b["page"]
            body.append(b["text"])
        page_txt = compact_ranges(pages) if pages else ""
        header = "<!-- chunk: %s | source: %s%s | section: %s -->" % (
            cid, rel, " | pages: " + page_txt if page_txt else "", title[:90])
        text = header + "\n\n" + "\n\n".join(body) + "\n"
        with open(os.path.join(doc_dir, cid + ".md"), "w", encoding="utf-8") as f:
            f.write(text)
        metas.append({"id": cid, "title": title[:90], "pages": page_txt, "words": words_in(text), "flags": flags})
    return metas


def write_placeholder(code, rel, doc_dir, reason, src_path):
    cid = code + "-001"
    text = ("<!-- chunk: %s | source: %s | section: NEEDS DIRECT READ -->\n\n"
            "> **Not converted automatically:** %s\n> Original: `%s`\n>\n"
            "> Read the original and replace this note with its content (tables as markdown tables, figures described).\n"
            "> For a long document write several files (`%s-001.md`, `%s-002.md`, … about 2,000 words each, each starting\n"
            "> with a `<!-- chunk: ID | source: … | section: … -->` line), then run `convert_docs.py reindex <out_dir>`.\n"
            % (cid, rel, reason, src_path, code, code))
    with open(os.path.join(doc_dir, cid + ".md"), "w", encoding="utf-8") as f:
        f.write(text)
    return [{"id": cid, "title": "NEEDS DIRECT READ", "pages": "", "words": 0, "flags": ["needs-read"]}]


# ------------------------------------------------------------------ index
def write_index(out_dir, manifest):
    docs = manifest["docs"]
    order = sorted(docs, key=lambda c: int(c[1:]))
    lines = ["# Source index", "",
             "Read this instead of the documents. Each chunk is a file `<doc>/<chunk>.md`. "
             "Cite document chunks as `[d1-007]`; cite meetings by their meeting ID and timestamp, e.g. `[M02@00:14:32]`.", "",
             "| Doc | File | State | Engine | Words | Chunks | Notes |", "|---|---|---|---|---|---|---|"]
    total = 0
    for code in order:
        d = docs[code]
        w = sum(c["words"] for c in d["chunks"])
        if d.get("state") != "REMOVED":
            total += w
        lines.append("| %s | %s | %s | %s | %d | %d | %s |" % (code, md_cell(d["file"]), d.get("state", ""), d.get("engine") or "-",
                                                             w, len(d["chunks"]), md_cell(d.get("note", ""))))
    lines += ["", "**Total: ~%d words (~%d pages).** %s" % (total, total // 450 + 1, strategy(total, len([c for c in order if docs[c].get('state') != 'REMOVED']))), ""]
    for code in order:
        d = docs[code]
        if d.get("state") == "REMOVED":
            continue
        lines += ["## %s — %s" % (code, d["file"]), "", "| Chunk | Pages | Section | Words | Flags |", "|---|---|---|---|---|"]
        for c in d["chunks"]:
            lines.append("| %s | %s | %s | %d | %s |" % (c["id"], c["pages"], md_cell(c["title"]), c["words"], ", ".join(c["flags"])))
        lines.append("")
    with open(os.path.join(out_dir, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    return total


def strategy(total, ndocs):
    if total > 30000 or (ndocs > 3 and total > 12000):
        return "Strategy: digest NEW/CHANGED documents **in parallel with subagents**, one per meeting or document."
    if total > 8000:
        return "Strategy: digest **one document at a time**, writing each digest before reading the next."
    return "Strategy: small enough to read directly."


def load_manifest(out_dir):
    path = os.path.join(out_dir, "manifest.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
            if isinstance(m.get("docs"), dict):
                return m
        except Exception:
            pass
    return {"version": 2, "docs": {}}


# ------------------------------------------------------------------ commands
def best_pdf_engine():
    for mod, name in (("fitz", "pymupdf"), ("pdfplumber", "pdfplumber"), ("pypdf", "pypdf (text-only)")):
        try:
            __import__(mod)
            return name
        except ImportError:
            continue
    return "pdftotext (text-only)" if shutil.which("pdftotext") else None


def cmd_convert(src, out_dir, force, exclude=()):
    if not os.path.isdir(src):
        sys.exit("Source folder not found: %s" % src)
    os.makedirs(out_dir, exist_ok=True)
    manifest = load_manifest(out_dir)
    docs = manifest["docs"]
    by_file = {d["file"]: code for code, d in docs.items()}
    next_num = max([int(c[1:]) for c in docs] + [0]) + 1
    seen, report = set(), []
    pdf_engine = best_pdf_engine()

    files = []
    for dirpath, dirnames, filenames in os.walk(src):
        skip = ALWAYS_SKIP | set(exclude)
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in skip)
        for fn in sorted(filenames):
            if fn.startswith(".") or fn.startswith("~$"):
                continue
            if dirpath == src and _is_atlas_placeholder(os.path.join(dirpath, fn)):
                continue
            files.append(os.path.join(dirpath, fn))

    for path in files:
        rel = os.path.relpath(path, src)
        ext = os.path.splitext(path)[1].lower()
        digest = sha256(path)
        code = by_file.get(rel)
        prev = docs.get(code) if code else None
        seen.add(rel)
        doc_dir = os.path.join(out_dir, code) if code else None
        if prev and not force and prev.get("sha256") == digest and os.path.isdir(doc_dir):
            upgrade = ext == ".pdf" and pdf_engine == "pymupdf" and prev.get("engine") != "pymupdf"
            if not upgrade:
                prev["state"] = "UNCHANGED"
                report.append((code, rel, "UNCHANGED", prev.get("note", "")))
                continue
        state = "NEW"
        if prev:
            state = "CHANGED" if prev.get("sha256") != digest else "RECONVERTED"
            backup = doc_dir + ".prev"
            shutil.rmtree(backup, ignore_errors=True)
            if os.path.isdir(doc_dir):
                shutil.move(doc_dir, backup)
        else:
            code = "d%d" % next_num
            next_num += 1
            doc_dir = os.path.join(out_dir, code)
            shutil.rmtree(doc_dir, ignore_errors=True)
        os.makedirs(doc_dir, exist_ok=True)
        media_dir = os.path.join(doc_dir, "media")
        info = {"engine": None, "note": ""}
        if ext in IMAGE_EXT:
            os.makedirs(media_dir, exist_ok=True)
            shutil.copy2(path, os.path.join(media_dir, os.path.basename(path)))
            blocks = [block("> **Image file** — view `media/%s` and describe what it shows under `### Visual notes`." % os.path.basename(path),
                            flags=["visual"])]
            info = {"engine": "image", "note": "standalone image"}
        elif ext in CONVERTERS:
            try:
                blocks, info = CONVERTERS[ext](path, media_dir)
            except Exception as e:  # corrupt or unusual file
                blocks, info = None, {"engine": None, "note": "conversion error: %s" % e}
        else:
            hint = "legacy Office format — re-save as .docx/.xlsx/.pptx" if ext in (".doc", ".xls", ".ppt") else "unsupported type"
            blocks, info = None, {"engine": None, "note": hint}
        if blocks:
            chunks = write_doc(code, rel, blocks, doc_dir)
        else:
            chunks = write_placeholder(code, rel, doc_dir, info.get("note", ""), path)
            state += " · NEEDS_DIRECT_READ"
        note = info.get("note", "")
        if state.startswith(("CHANGED", "RECONVERTED")):
            note = (note + "; " if note else "") + "previous version kept in %s.prev/ (diff: convert_docs.py diff <out> %s.prev %s)" % (code, code, code)
        docs[code] = {"file": rel, "sha256": digest, "state": state, "engine": info.get("engine"),
                      "pages": info.get("pages"), "note": note, "chunks": chunks}
        report.append((code, rel, state, note))

    for code, d in docs.items():
        if d["file"] not in seen:
            d["state"] = "REMOVED"
            report.append((code, d["file"], "REMOVED", "no longer in the source folder — chunks kept on disk"))

    total = write_index(out_dir, manifest)
    print("\nSource inventory\n")
    print(md_table([["Doc", "File", "State", "Chunks", "Notes"]] +
                   [[c, f, s, str(len(docs[c]["chunks"])), n] for c, f, s, n in sorted(report, key=lambda r: int(r[0][1:]))]))
    live = [d for d in docs.values() if d.get("state") != "REMOVED"]
    flagged = collections.Counter(f for d in live for c in d["chunks"] for f in c["flags"])
    print("\n%d document(s), %d chunks, ~%d words (~%d pages)." % (len(live), sum(len(d["chunks"]) for d in live), total, total // 450 + 1))
    todo = {f: n for f, n in flagged.items() if f in ("visual", "needs-read")}
    if todo:
        print("Chunks needing attention: " + ", ".join("%d %s" % (n, f) for f, n in sorted(todo.items())) + " — describe `visual` chunks under `### Visual notes`; read `needs-read` originals directly, then run reindex")
    info = {f: n for f, n in flagged.items() if f not in todo}
    if info:
        print("Also contain: " + ", ".join("%d with %s" % (n, f) for f, n in sorted(info.items())))
    print(strategy(total, len(live)))
    print("Index: %s" % os.path.join(out_dir, "INDEX.md"))
    has_pdf = any(d["file"].lower().endswith(".pdf") for d in live)
    if has_pdf and pdf_engine != "pymupdf":
        print("\nPDF quality is reduced (engine: %s). For tables, headings and figure detection run:\n  %s\n"
              "then convert again." % (pdf_engine or "none", SETUP_HINT))


def cmd_install_deps():
    print("Creating %s and installing the PDF engine (PyMuPDF)…" % VENV_DIR)
    try:
        if not os.path.exists(VENV_PY):
            os.makedirs(ATLAS_HOME, exist_ok=True)
            subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
        subprocess.run([VENV_PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip"], check=False)
        subprocess.run([VENV_PY, "-m", "pip", "install", "--quiet", "--upgrade", "pymupdf"], check=True)
        subprocess.run([VENV_PY, "-c", "import fitz; print('PDF engine ready: PyMuPDF', fitz.VersionBind)"], check=True)
        print("Re-run the conversion; it will use the new engine automatically.")
    except Exception as e:
        print("Install failed: %s\nFallback: read PDFs directly, or try again with network access." % e)
        sys.exit(1)


def doc_text(out_dir, code):
    d = os.path.join(out_dir, code)
    if not os.path.isdir(d):
        sys.exit("No such converted document: %s" % d)
    parts = []
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".md")):
        with open(os.path.join(d, fn), encoding="utf-8") as f:
            parts += [l.rstrip() for l in f if not l.startswith("<!-- chunk:")]
    return [l for l in parts if l.strip()]


def cmd_diff(out_dir, a, b):
    ta, tb = doc_text(out_dir, a), doc_text(out_dir, b)
    diff = list(difflib.unified_diff(ta, tb, a, b, lineterm="", n=1))
    if not diff:
        print("No textual differences between %s and %s." % (a, b))
        return
    added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
    print("# Changes %s → %s  (+%d / -%d lines)\n" % (a, b, added, removed))
    print("\n".join(diff))


def cmd_reindex(out_dir):
    manifest = load_manifest(out_dir)
    for code, d in manifest["docs"].items():
        doc_dir = os.path.join(out_dir, code)
        if not os.path.isdir(doc_dir):
            continue
        old = {c["id"]: c for c in d["chunks"]}
        chunks = []
        for fn in sorted(f for f in os.listdir(doc_dir) if re.match(r"%s-\d+\.md$" % re.escape(code), f)):
            cid = fn[:-3]
            with open(os.path.join(doc_dir, fn), encoding="utf-8") as f:
                text = f.read()
            m = re.match(r"<!-- chunk: [^|]*\|[^|]*(?:\| pages: ([^|]*))?\| section: (.*?) -->", text)
            c = dict(old.get(cid, {"id": cid, "title": "", "pages": "", "flags": []}))
            if m:
                c["pages"] = (m.group(1) or c.get("pages", "")).strip()
                c["title"] = m.group(2).strip() or c.get("title", "")
            flags = set(c.get("flags", [])) - {"needs-read"}
            if "NEEDS DIRECT READ" in text[:300] and "Not converted automatically" in text:
                flags.add("needs-read")
            if re.search(r"^\|.*\|\s*$", text, flags=re.M):
                flags.add("tables")
            c["flags"] = sorted(flags)
            c["words"] = words_in(text)
            chunks.append(c)
        d["chunks"] = chunks
        if chunks and not any("needs-read" in c["flags"] for c in chunks):
            d["state"] = (d.get("state") or "").replace(" · NEEDS_DIRECT_READ", "")
    total = write_index(out_dir, manifest)
    print("Reindexed: ~%d words. %s" % (total, os.path.join(out_dir, "INDEX.md")))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args else 2)
    if args[0] == "--install-deps":
        return cmd_install_deps()
    if args[0] == "diff" and len(args) == 4:
        return cmd_diff(args[1], args[2], args[3])
    if args[0] == "reindex" and len(args) == 2:
        return cmd_reindex(args[1])
    force = "--force" in args
    exclude = [args[i + 1] for i, a in enumerate(args) if a == "--exclude" and i + 1 < len(args)]
    drop = {i for i, a in enumerate(args) if a == "--exclude"} | {i + 1 for i, a in enumerate(args) if a == "--exclude"}
    args = [a for i, a in enumerate(args) if a != "--force" and i not in drop]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    _maybe_reexec_in_venv(args[0])
    cmd_convert(args[0], args[1], force, exclude)


if __name__ == "__main__":
    main()
