#!/usr/bin/env python3
"""Convert speech.md to a print-ready PDF with Chinese font support.

Usage: python3 convert.py
Produces: speech.pdf
"""

from pathlib import Path

# Monkey-patch fontTools so it tolerates WenQuanYi Zen Hei's out-of-range
# Unicode range bits (WQY sets bit 123 in the OS/2 table, but fontTools
# only accepts 0-122, which crashes weasyprint's font subsetter).
from fontTools.ttLib.tables.O_S_2f_2 import table_O_S_2f_2 as _os2_table

_orig_setUnicodeRanges = _os2_table.setUnicodeRanges


def _safe_setUnicodeRanges(self, bits):
    filtered = [b for b in bits if 0 <= b <= 122]
    return _orig_setUnicodeRanges(self, filtered)


_os2_table.setUnicodeRanges = _safe_setUnicodeRanges

import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

SRC = Path(__file__).parent / "speech.md"
OUT = Path(__file__).parent / "speech.pdf"

md_text = SRC.read_text(encoding="utf-8")

# Convert markdown → HTML fragment.
html_body = markdown.markdown(
    md_text,
    extensions=["extra", "tables", "toc", "sane_lists", "nl2br"],
)

# Wrap the fragment in a full HTML document with print-friendly CSS.
full_html = f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
  <meta charset="UTF-8">
  <title>GDC 2026 · Speech Script</title>
</head>
<body>
{html_body}
</body>
</html>
"""

css = CSS(
    string="""
    @page {
      size: A4;
      margin: 22mm 20mm 22mm 20mm;
      @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: "WenQuanYi Zen Hei", sans-serif;
        font-size: 9pt;
        color: #888;
      }
    }

    body {
      font-family: "WenQuanYi Zen Hei", "Noto Sans CJK SC", "SimSun", sans-serif;
      font-size: 10.5pt;
      line-height: 1.65;
      color: #1a1a1a;
    }

    h1 {
      font-size: 22pt;
      color: #c41e2a;
      border-bottom: 2px solid #c41e2a;
      padding-bottom: 6pt;
      margin-bottom: 12pt;
    }

    h2 {
      font-size: 15pt;
      color: #c41e2a;
      margin-top: 16pt;
      margin-bottom: 8pt;
      padding: 6pt 10pt;
      background: #fff1f2;
      border-left: 4px solid #c41e2a;
      page-break-before: always;
      page-break-after: avoid;
    }

    /* Don't force page break before the FIRST h2 */
    body > h2:first-of-type,
    h1 + h2,
    h1 + blockquote + h2,
    h1 + blockquote + p + h2,
    h1 + blockquote + p + table + h2,
    h1 + blockquote + p + table + p + h2,
    h1 + blockquote + p + table + p + ul + h2,
    h1 + blockquote + p + table + p + ul + hr + h2 {
      page-break-before: auto;
    }

    h3 {
      font-size: 12pt;
      color: #333;
      margin-top: 12pt;
      margin-bottom: 6pt;
      page-break-after: avoid;
    }

    p {
      margin: 4pt 0;
      text-align: justify;
    }

    strong {
      color: #c41e2a;
      font-weight: 700;
    }

    em { color: #666; }

    blockquote {
      margin: 6pt 0 6pt 0;
      padding: 6pt 12pt;
      background: #fafafa;
      border-left: 3px solid #d0d0d0;
      color: #333;
      font-size: 10pt;
      page-break-inside: avoid;
    }

    blockquote p { margin: 2pt 0; }

    blockquote strong { color: #c41e2a; }

    ul, ol { margin: 4pt 0 4pt 16pt; padding-left: 8pt; }
    li { margin: 2pt 0; }

    table {
      border-collapse: collapse;
      width: 100%;
      margin: 8pt 0;
      font-size: 9.5pt;
      page-break-inside: avoid;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 4pt 6pt;
      text-align: left;
    }
    th {
      background: #fff1f2;
      color: #c41e2a;
      font-weight: 700;
    }

    hr {
      border: none;
      border-top: 1px solid #ddd;
      margin: 10pt 0;
    }

    code {
      font-family: "Noto Sans Mono", monospace;
      background: #f3f3f3;
      padding: 1pt 4pt;
      border-radius: 2pt;
      font-size: 9.5pt;
    }

    /* avoid breaks inside important units */
    table, blockquote, ul, ol { page-break-inside: avoid; }
    """
)

font_config = FontConfiguration()
HTML(string=full_html).write_pdf(
    OUT,
    stylesheets=[css],
    font_config=font_config,
)

print(f"OK · wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
