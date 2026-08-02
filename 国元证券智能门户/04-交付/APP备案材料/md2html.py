#!/usr/bin/env python3
"""
Markdown → 自包含 HTML 转换脚本
用法: python md2html.py <输入.md> [输出.html]
不指定输出文件时，自动替换扩展名为 .html 同目录输出。
"""

import sys
import os
from pathlib import Path
from markdown import Markdown
from markdown.extensions.toc import TocExtension


CSS_TEMPLATE = """\
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", "Hiragino Sans GB", sans-serif;
    font-size: 15px; line-height: 1.8; color: #1a1a1a;
    max-width: 860px; margin: 0 auto; padding: 32px 20px 60px;
    background: #fff;
}
h1 { font-size: 26px; margin: 32px 0 16px; border-bottom: 2px solid #0d2b45; padding-bottom: 8px; color: #0d2b45; }
h2 { font-size: 21px; margin: 28px 0 12px; color: #0d2b45; }
h3 { font-size: 17px; margin: 20px 0 8px; color: #333; }
h4 { font-size: 15px; margin: 16px 0 6px; color: #555; }

strong { color: #0d2b45; }

a { color: #1a6fb5; text-decoration: none; }
a:hover { text-decoration: underline; }

table {
    width: 100%; border-collapse: collapse; margin: 12px 0 20px;
    font-size: 14px;
}
th, td {
    border: 1px solid #ddd; padding: 8px 12px; text-align: left;
    vertical-align: top;
}
th { background: #f0f4f8; font-weight: 600; color: #0d2b45; white-space: nowrap; }
tr:nth-child(even) td { background: #fafbfc; }

pre {
    background: #f5f6f8; border: 1px solid #e0e3e8; border-radius: 6px;
    padding: 14px 18px; overflow-x: auto; font-size: 13px;
    line-height: 1.6; margin: 12px 0 20px;
}
code { font-family: "SF Mono", "Fira Code", "Consolas", monospace; font-size: 13px; }
:not(pre) > code {
    background: #f0f2f5; padding: 1px 5px; border-radius: 3px; color: #c7254e;
}

ul, ol { padding-left: 24px; margin: 8px 0 16px; }
li { margin: 2px 0; }

blockquote {
    border-left: 3px solid #c4a44a; padding: 8px 16px; margin: 12px 0 20px;
    background: #fefdf7; color: #666;
}

hr { border: none; border-top: 1px solid #e0e3e8; margin: 24px 0; }

.toc { background: #f8f9fb; border: 1px solid #e0e3e8; border-radius: 6px;
       padding: 16px 20px; margin: 20px 0 28px; }
.toc ul { list-style: none; padding-left: 0; }
.toc li { margin: 4px 0; }
.toc a { font-size: 14px; }

/* Print styles */
@media print {
    body { max-width: 100%; padding: 0; }
    table { page-break-inside: avoid; }
    h2, h3 { page-break-after: avoid; }
    pre { white-space: pre-wrap; word-wrap: break-word; }
}
"""


def md_to_html(md_path: str, out_path: str = None) -> str:
    md_path = Path(md_path).resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"文件不存在: {md_path}")

    if out_path is None:
        out_path = md_path.with_suffix(".html")
    else:
        out_path = Path(out_path).resolve()

    # Read markdown
    md_text = md_path.read_text(encoding="utf-8")

    # Convert to HTML body
    md = Markdown(
        extensions=[
            "extra",                           # tables, fenced_code, footnotes, abbr, attr_list, def_list
            "nl2br",                           # newline → <br>
            TocExtension(permalink=False),      # generate TOC with [TOC] marker
            "sane_lists",                      # better list handling
        ],
        output_format="html5",
    )
    body = md.convert(md_text)

    # Compose full HTML
    title = md_path.stem
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{CSS_TEMPLATE}
</style>
</head>
<body>
{body}
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python md2html.py <输入.md> [输出.html]")
        print("示例: python md2html.py report.md")
        print("      python md2html.py report.md ../output/report.html")
        sys.exit(1)

    md_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = md_to_html(md_file, out_file)
        md_size = os.path.getsize(md_file)
        html_size = os.path.getsize(result)
        print(f"[OK] Generated: {result}")
        print(f"     MD {md_size:>6,} bytes -> HTML {html_size:>6,} bytes")
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)
