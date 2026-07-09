#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简 Markdown -> 详情页 HTML 转换脚本（仅依赖 Python 标准库）

用法:
    python tools/md2html.py input.md --title "文章标题" --date "2026年7月9日" --category articles

参数:
    --title     详情页标题（必填）
    --date      日期，显示在标题下方（必填）
    --category  articles | experience | achievements（必填，决定返回链接与输出目录）
    --out       输出 HTML 路径（可选，默认 posts/<category>/<输入文件名>.html）

支持的 Markdown 语法:
    # / ## / ###       标题
    **粗体**  *斜体*   行内样式
    `代码`              行内代码
    [文字](链接)        超链接
    - 或 * 列表项       无序列表
    1. 列表项          有序列表
    > 引用             块引用
    ---                分隔线
    空行               段落分隔
"""
import argparse
import html
import os
import re
import sys

CATEGORY_BACK = {
    "articles": ("../../articles.html", "返回文章"),
    "experience": ("../../experience.html", "返回经验"),
    "achievements": ("../../achievements.html", "返回成果"),
}


def inline(text):
    """处理行内语法：代码、粗体、斜体、链接。"""
    text = html.escape(text)
    # 行内代码
    text = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), text)
    # 链接 [文字](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)),
        text,
    )
    # 粗体
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # 斜体
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def convert(md):
    lines = md.split("\n")
    out = []
    i = 0
    list_type = None  # 'ul' or 'ol'

    def close_list():
        nonlocal list_type
        if list_type:
            out.append("</%s>" % list_type)
            list_type = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            close_list()
            i += 1
            continue

        if stripped == "---":
            close_list()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith("### "):
            close_list()
            out.append("<h3>%s</h3>" % inline(stripped[4:]))
        elif stripped.startswith("## "):
            close_list()
            out.append("<h2>%s</h2>" % inline(stripped[3:]))
        elif stripped.startswith("# "):
            close_list()
            out.append("<h1>%s</h1>" % inline(stripped[2:]))
        elif stripped.startswith("> "):
            close_list()
            out.append("<blockquote>%s</blockquote>" % inline(stripped[2:]))
        elif re.match(r"^[-*]\s+", stripped):
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            out.append("<li>%s</li>" % inline(re.sub(r"^[-*]\s+", "", stripped)))
        elif re.match(r"^\d+\.\s+", stripped):
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append("<li>%s</li>" % inline(re.sub(r"^\d+\.\s+", "", stripped)))
        else:
            close_list()
            out.append("<p>%s</p>" % inline(stripped))

        i += 1

    close_list()
    return "\n".join(out)


def build_page(title, date, category, body_html):
    back_href, back_label = CATEGORY_BACK[category]
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} / SayangChun</title>
    <link rel="icon" type="image/png" href="../../avatar.png">
    <link rel="stylesheet" href="../../assets/style.css">
    <script src="../../assets/nav.js"></script>
</head>
<body>
    <div class="container">
        <a class="back-link" href="{back}">&larr; {back_label}</a>

        <h1>{title}</h1>
        <p class="entry-date">{date}</p>

        <div class="entry-content">
{body}
        </div>
    </div>
</body>
</html>
""".format(
        title=html.escape(title),
        date=html.escape(date),
        back=back_href,
        back_label=back_label,
        body=body_html,
    )


def main():
    parser = argparse.ArgumentParser(description="极简 Markdown -> 详情页 HTML")
    parser.add_argument("input", help="输入的 Markdown 文件路径")
    parser.add_argument("--title", required=True, help="详情页标题")
    parser.add_argument("--date", required=True, help="日期，如 2026年7月9日")
    parser.add_argument(
        "--category", required=True, choices=list(CATEGORY_BACK.keys()),
        help="分类，决定返回链接与输出目录",
    )
    parser.add_argument("--out", default=None, help="输出 HTML 路径（可选）")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig") as f:
        md = f.read()

    body = convert(md)
    page = build_page(args.title, args.date, args.category, body)

    if args.out:
        out_path = args.out
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        out_path = os.path.join("posts", args.category, base + ".html")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)

    print("已生成: %s" % out_path)


if __name__ == "__main__":
    main()
