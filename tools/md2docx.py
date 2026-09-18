"""Markdown → DOCX 转换器（本项目文档专用）。

支持：标题(#/##/###/####)、表格、代码块(```)、引用(>)、
无序/有序列表、分隔线(---)、粗体(**)、行内代码(`)。

用法：
    python tools/md2docx.py <input.md> <output.docx> [--title "标题"]

设计取舍：不追求完整 Markdown 兼容，只覆盖本项目文档实际用到的语法；
宁可显式报出未识别的行，也不静默丢内容。
"""
from __future__ import annotations

import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

BODY_FONT = "Microsoft YaHei"
MONO_FONT = "Consolas"
BODY_SIZE = Pt(10.5)

INLINE_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+?`)")


def set_font(run, name=BODY_FONT, size=None, bold=None, mono=False, color=None):
    f = run.font
    f.name = MONO_FONT if mono else name
    if size is not None:
        f.size = size
    if bold is not None:
        f.bold = bold
    if color is not None:
        f.color.rgb = color
    # 东亚字体必须单独设置，否则中文会回退
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rf)
    rf.set(qn("w:eastAsia"), MONO_FONT if mono else name)


def add_inline(par, text, size=BODY_SIZE, base_bold=False):
    """写入带行内格式的文本。"""
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = par.add_run(part[2:-2])
            set_font(r, size=size, bold=True)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = par.add_run(part[1:-1])
            set_font(r, size=Pt(size.pt - 0.5), mono=True,
                     color=RGBColor(0xB0, 0x30, 0x30))
        else:
            r = par.add_run(part)
            set_font(r, size=size, bold=base_bold)


def strip_inline(text):
    return INLINE_RE.sub(lambda m: m.group(0).strip("*`"), text)


def is_sep_row(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip() != "") \
        and any(c.strip() for c in cells)


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def add_table(doc, rows):
    ncol = max(len(r) for r in rows)
    t = doc.add_table(rows=0, cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j in range(ncol):
            txt = row[j] if j < len(row) else ""
            p = cells[j].paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            add_inline(p, txt, size=Pt(9.5), base_bold=(i == 0))
    return t


def convert(src: str, dst: str, title: str | None = None):
    lines = open(src, encoding="utf-8").read().split("\n")
    doc = Document()
    if title:
        doc.core_properties.title = title

    # 文档默认字体
    st = doc.styles["Normal"]
    st.font.name = BODY_FONT
    st.font.size = BODY_SIZE
    st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.15

    i = 0
    unknown = []
    prev_i = -1
    while i < len(lines):
        # 通用护栏：若上一轮未推进游标，强制推进（防止死循环）
        if i == prev_i:
            unknown.append((i, lines[i][:60]))
            i += 1
            prev_i = -1
            continue
        prev_i = i
        line = lines[i]
        s = line.rstrip()

        # ---- 代码块
        if s.strip().startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(12)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run("\n".join(buf))
            set_font(r, size=Pt(9), mono=True)
            continue

        # ---- 表格
        if s.strip().startswith("|") and i + 1 < len(lines) \
                and is_sep_row(split_row(lines[i + 1])):
            rows = [split_row(s)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            add_table(doc, rows)
            doc.add_paragraph()
            continue

        # ---- 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            text = m.group(2).strip()
            h = doc.add_heading(level=min(lvl, 4))
            h.paragraph_format.space_before = Pt(10 if lvl > 1 else 0)
            r = h.add_run(strip_inline(text))
            set_font(r, size=Pt([20, 15, 12.5, 11][min(lvl, 4) - 1]),
                     bold=True, color=RGBColor(0x1A, 0x1A, 0x1A))
            i += 1
            continue

        # ---- 分隔线
        if re.fullmatch(r"-{3,}", s.strip()):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run("─" * 42)
            set_font(r, size=Pt(8), color=RGBColor(0xAA, 0xAA, 0xAA))
            i += 1
            continue

        # ---- 引用
        if s.strip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            add_inline(p, " ".join(buf), size=Pt(10))
            for r in p.runs:
                r.font.italic = True
            continue

        # ---- 列表
        m = re.match(r"^(\s*)[-*]\s+(.*)$", s)
        if m:
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            add_inline(p, m.group(2))
            i += 1
            continue
        m = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", s)
        if m:
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(2)
            add_inline(p, m.group(3))
            i += 1
            continue

        # ---- 空行
        if not s.strip():
            i += 1
            continue

        # ---- 普通段落
        p = doc.add_paragraph()
        add_inline(p, s.strip())
        i += 1

    doc.save(dst)
    return unknown


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    title = None
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    convert(sys.argv[1], sys.argv[2], title)
    print(f"wrote {sys.argv[2]}")
