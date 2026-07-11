#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简 Markdown -> 详情页 HTML 转换脚本 + 自动更新分类列表

特性:
  - 支持在 .md 文件头部写 YAML frontmatter 指定元数据（推荐方式）
  - 也保留 --title / --date / --category / --summary 命令行参数（优先级低于 frontmatter）
  - 生成详情页后，自动在对应的分类列表页（articles.html / experience.html / achievements.html）
    中插入或更新条目，并按日期降序排列（最新在前）
  - 重新运行同一文件会原地更新（通过 href 匹配）
  - 若修改了 category，自动从旧分类列表中移除条目

Frontmatter 格式（放在 .md 文件最顶部）:
    ---
    title: "文章标题"
    date: "2026年7月9日"
    category: articles          # articles / experience / achievements
    summary: "一句话摘要，显示在列表页。"
    ---

用法:
    python tools/md2html.py my-post.md
    python tools/md2html.py my-post.md --no-update-list   # 仅生成详情页，不更新列表
    python tools/md2html.py my-post.md --title "自定义标题"  # 覆盖 frontmatter
"""

import argparse
import html
import os
import re
import sys
from datetime import date as DateClass
from datetime import datetime

# ---------------------------------------------------------------------------
# 分类配置
# ---------------------------------------------------------------------------
CATEGORY_BACK = {
    "articles": ("../../articles.html", "返回文章"),
    "experience": ("../../experience.html", "返回经验"),
    "achievements": ("../../achievements.html", "返回成果"),
}

CATEGORY_LIST_FILES = {
    "articles": "articles.html",
    "experience": "experience.html",
    "achievements": "achievements.html",
}

# ---------------------------------------------------------------------------
# Frontmatter 解析
# ---------------------------------------------------------------------------
def parse_frontmatter(md_text):
    """解析 YAML 风格 frontmatter 和正文。返回 (meta_dict, body_str)。"""
    text = md_text.lstrip("\ufeff")  # 去除 BOM
    if not text.startswith("---"):
        return {}, text

    # 找到第二个 ---
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")

    meta = {}
    for line in fm_block.splitlines():
        line = line.strip()
        m = re.match(r'^(\w+)\s*:\s*(.+)$', line)
        if m:
            key = m.group(1)
            value = m.group(2).strip().strip('"').strip("'")
            meta[key] = value

    return meta, body


# ---------------------------------------------------------------------------
# 日期解析（用于排序）
# ---------------------------------------------------------------------------
def parse_date_for_sort(date_str):
    """
    将日期字符串解析为 (year, month, day) 元组用于排序。
    支持格式:
      - 2026年7月9日
      - 2026年07月09日
      - 2026-07-09
      - 2026/07/09
    """
    date_str = date_str.strip()

    # 中文格式：2026年7月9日 或 2026年07月09日
    m = re.match(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?', date_str)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # ISO 格式：2026-07-09 或 2026/07/09
    m = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    raise ValueError(f"无法解析日期: {date_str}")


# ---------------------------------------------------------------------------
# 列表页处理
# ---------------------------------------------------------------------------
ENTRY_PATTERN = re.compile(
    r'<div class="entry">\s*'
    r'<div class="entry-header">\s*'
    r'<a class="entry-title" href="([^"]+)">([^<]*)</a>\s*'
    r'<span class="entry-date">([^<]*)</span>\s*'
    r'</div>\s*'
    r'<div class="entry-content">\s*'
    r'<p>([^<]*)</p>\s*'
    r'</div>\s*'
    r'</div>',
    re.DOTALL,
)

ENTRY_TEMPLATE = """        <div class="entry">
            <div class="entry-header">
                <a class="entry-title" href="{href}">{title}</a>
                <span class="entry-date">{date}</span>
            </div>
            <div class="entry-content">
                <p>{summary}</p>
            </div>
        </div>"""


def _extract_entries(content):
    """从 HTML 内容中提取所有 entry 块，返回 (entries_list, entries_text_dict)"""
    entries = []
    entries_text = {}
    for match in ENTRY_PATTERN.finditer(content):
        href = match.group(1)
        title = match.group(2)
        date_str = match.group(3)
        summary = match.group(4)
        entries.append({
            "href": href,
            "title": title,
            "date_str": date_str,
            "summary": summary,
        })
        entries_text[href] = match.group(0)
    return entries, entries_text


def _rebuild_entries(entries):
    """按日期降序排序并生成 entries HTML 块列表。"""
    def sort_key(e):
        try:
            return parse_date_for_sort(e["date_str"])
        except ValueError:
            return (0, 0, 0)

    entries_sorted = sorted(entries, key=sort_key, reverse=True)

    blocks = []
    for e in entries_sorted:
        blocks.append(ENTRY_TEMPLATE.format(
            href=html.escape(e["href"], quote=True),
            title=html.escape(e["title"]),
            date=html.escape(e["date_str"]),
            summary=html.escape(e["summary"]),
        ))
    return "\n\n".join(blocks)


def update_category_list(category, title, date_str, summary, href, slug):
    """
    更新分类列表页面：
      - 从所有列表中清除该 slug（支持跨分类迁移）
      - 在目标列表中 upsert 条目
      - 按日期降序排列
    """

    list_file = CATEGORY_LIST_FILES.get(category)
    if not list_file:
        print(f"  警告：未知分类 '{category}'，跳过列表更新", file=sys.stderr)
        return

    if not os.path.exists(list_file):
        print(f"  警告：列表文件 {list_file} 不存在，跳过更新", file=sys.stderr)
        return

    with open(list_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 1）解析现有的 entries
    entries, entries_text = _extract_entries(content)

    # 2）从所有列表中删除旧分类的相同 slug（支持跨分类迁移）
    for cat, lf in CATEGORY_LIST_FILES.items():
        if cat == category:
            continue
        if not os.path.exists(lf):
            continue
        with open(lf, "r", encoding="utf-8") as f:
            other_content = f.read()
        other_entries, _ = _extract_entries(other_content)
        old_count = len(other_entries)
        other_entries = [e for e in other_entries if not e["href"].endswith("/" + slug + ".html")]
        if len(other_entries) != old_count:
            other_rebuilt = _rebuild_entries(other_entries)
            other_new = _replace_entries_section(other_content, other_rebuilt)
            with open(lf, "w", encoding="utf-8") as f:
                f.write(other_new)
            print(f"  已从 {lf} 移除旧条目（slug: {slug})")

    # 3）在目标列表中 upsert
    entries = [e for e in entries if e["href"] != href]
    entries.append({
        "href": href,
        "title": title,
        "date_str": date_str,
        "summary": summary,
    })

    rebuilt = _rebuild_entries(entries)
    new_content = _replace_entries_section(content, rebuilt)

    with open(list_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  列表已更新: {list_file}")


def _replace_entries_section(content, entries_html):
    """
    在 HTML 内容中找到 entry 块区域并替换为新的 entriess HTML。
    保留 <h1>...</h1> 和后面的注释。
    """
    # 定位 <h1>...</h1>
    h1_end = re.search(r"</h1>", content)
    if not h1_end:
        # 没有 h1，在 <div class="container"> 后插入
        container_end = re.search(r'<div class="container">', content)
        if container_end:
            ins = container_end.end()
            return (content[:ins] + "\n\n" +
                    "        <!-- 自动管理的条目 -->\n" +
                    entries_html + "\n\n" +
                    content[ins:])
        return content

    after_h1 = h1_end.end()
    # 找到后面第一个非空行
    rest = content[after_h1:]

    # 找到 </div>（container 的闭标签）
    container_close = rest.rfind("</div>")
    if container_close == -1:
        container_close = len(rest)

    # 找到 <div class="entry"> 的起始位置
    first_entry = rest.find('<div class="entry">')
    if first_entry == -1:
        # 没有现有条目，在 h1 后插入
        insert_pos = after_h1
        while insert_pos < len(content) and content[insert_pos] in '\r\n ':
            insert_pos += 1
        return (content[:after_h1] + "\n\n" + entries_html + "\n\n" +
                content[insert_pos:])

    # 找到最后一个 </div>（entry 的闭标签）之后
    # 更准确：找到最后一个 entry 块结束之后到 container 闭标签之间的位置
    # 从第一个 entry 开始到 container 闭标签前的内容替换
    before_entries = content[:after_h1]
    # 去掉 before_entries 后的空白
    # 找到第一个 entry 块前的非空行位置
    # 简单方法：找到第一个 entry 的起始位置，替换到 container 前
    entry_start = after_h1 + first_entry
    # 找到 container 闭标签
    container_close_abs = after_h1 + container_close
    # 将 entry 区域替换
    # 保留 container 闭标签及其后的内容
    after_entries = content[container_close_abs:]
    return (before_entries + "\n\n" + entries_html + "\n\n" +
            "        <!-- 复制上面的 .entry 块即可新增一篇文章 -->\n" +
            after_entries.lstrip("\n"))


# ---------------------------------------------------------------------------
# 内联格式处理
# ---------------------------------------------------------------------------
def inline(text):
    """处理行内语法：代码、粗体、斜体、链接。"""
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)),
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


# ---------------------------------------------------------------------------
# Markdown 正文转换
# ---------------------------------------------------------------------------
def convert(md):
    lines = md.split("\n")
    out = []
    i = 0
    list_type = None

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


# ---------------------------------------------------------------------------
# 详情页构建
# ---------------------------------------------------------------------------
def build_page(title, date_str, category, body_html):
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
        date=html.escape(date_str),
        back=back_href,
        back_label=back_label,
        body=body_html,
    )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="极简 Markdown -> 详情页 HTML + 自动更新分类列表",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Frontmatter 格式（推荐）:
  ---
  title: "文章标题"
  date: "2026年7月9日"
  category: articles        # articles / experience / achievements
  summary: "一句话摘要"
  ---

用法示例:
  python tools/md2html.py my-post.md                          # frontmatter 模式
  python tools/md2html.py my-post.md --no-update-list         # 仅生成详情页
  python tools/md2html.py my-post.md --title "标题" --date "2026-07-09"
        """,
    )
    parser.add_argument("input", help="输入的 Markdown 文件路径")
    parser.add_argument("--title", default=None, help="详情页标题（可选，默认读取 frontmatter）")
    parser.add_argument("--date", default=None, help="日期（可选，如 2026年7月9日）")
    parser.add_argument(
        "--category", default=None,
        choices=list(CATEGORY_BACK.keys()),
        help="分类（可选，articles / experience / achievements）",
    )
    parser.add_argument("--summary", default=None, help="摘要（可选，显示在列表页）")
    parser.add_argument("--out", default=None, help="输出 HTML 路径（可选）")
    parser.add_argument(
        "--no-update-list", action="store_true",
        help="仅生成详情页，不更新分类列表",
    )
    args = parser.parse_args()

    # 读取文件
    with open(args.input, "r", encoding="utf-8-sig") as f:
        md_text = f.read()

    # 解析 frontmatter
    meta, body = parse_frontmatter(md_text)
    has_fm = bool(meta)

    # 合并元数据：CLI 显式提供时覆盖 frontmatter，否则用 frontmatter
    title = args.title if args.title is not None else meta.get("title")
    date_str = args.date if args.date is not None else meta.get("date")
    category = args.category if args.category is not None else meta.get("category")
    summary = args.summary if args.summary is not None else meta.get("summary")

    if not title:
        parser.error("缺少 title：请在 frontmatter 中设置或通过 --title 提供")
    if not date_str:
        parser.error("缺少 date：请在 frontmatter 中设置或通过 --date 提供")
    if not category:
        parser.error("缺少 category：请在 frontmatter 中设置或通过 --category 提供")
    if not summary:
        parser.error("缺少 summary：请在 frontmatter 中设置或通过 --summary 提供")

    # 转换正文
    body_html = convert(body)

    # 构建页面
    page = build_page(title, date_str, category, body_html)

    # 确定输出路径
    if args.out:
        out_path = args.out
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        out_path = os.path.join("posts", category, base + ".html")

    base = os.path.splitext(os.path.basename(args.input))[0]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)

    rel_out = os.path.relpath(out_path)
    print("已生成: %s" % rel_out)

    # 更新分类列表
    if not args.no_update_list:
        href = "posts/%s/%s.html" % (category, base)
        update_category_list(category, title, date_str, summary, href, base)
    else:
        print("  跳过列表更新（--no-update-list）")


if __name__ == "__main__":
    main()
