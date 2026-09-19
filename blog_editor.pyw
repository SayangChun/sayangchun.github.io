#!/usr/bin/env python3
"""
博客图形化编辑器 - 用于管理博客文章
用法: python blog_editor.pyw
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# 博客根目录
BLOG_ROOT = Path(__file__).parent

# 分类配置（文章详情页）
CATEGORIES = {
    "achievements": {"name": "成果", "file": "achievements.html"},
    "updates": {"name": "动态", "file": "updates.html"},
    "reviews": {"name": "评测", "file": "reviews.html"},
}

# 评测：作品类型（Steam 式二元结论，不打分）
REVIEW_TYPE_LABELS = {
    "game": "游戏",
    "book": "书",
    "movie": "电影",
    "anime": "动画",
    "series": "剧集",
    "music": "音乐",
}
REVIEW_TYPE_KEYS = {v: k for k, v in REVIEW_TYPE_LABELS.items()}
REVIEW_TYPE_ICONS = {
    "game": "🎮",
    "book": "📖",
    "movie": "🎬",
    "anime": "🌸",
    "series": "📺",
    "music": "🎧",
}
VERDICT_LABELS = {
    "recommended": "👍 推荐",
    "not-recommended": "👎 不推荐",
}

# 详情页「主创」行按作品类型显示对应称谓
CREATOR_LABELS = {
    "game": "开发者",
    "book": "作者",
    "movie": "导演",
    "anime": "导演",
    "series": "导演",
    "music": "创作者",
}
CREATOR_LABEL_PATTERN = "开发者|作者|导演|创作者|主创"


def strip_clock(text):
    """去掉日期末尾的时分（如「上午 11:23」），只保留日期部分，与 Steam 口径一致。"""
    if not text:
        return ""
    return re.sub(r'\s*(?:上午|下午|凌晨|中午|早上|晚上)?\s*\d{1,2}:\d{2}(?::\d{2})?\s*$', '', text).strip()

# 单页面（无详情页，直接编辑）
SINGLE_PAGES = {
    "index": {"name": "中文简历", "file": "index.html"},
    "en": {"name": "英文简历", "file": "en.html"},
    "workflow": {"name": "工作流", "file": "workflow.html"},
}

# 详情页模板
DETAIL_TEMPLATE = '''<!DOCTYPE html>
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
        <a class="back-link" href="../../{listing_file}">&larr; 返回{category_name}</a>

        <h1>{title}</h1>
        <p class="entry-date">{date}</p>

        <div class="entry-content">
            {content}
        </div>
    </div>
</body>
</html>
'''

# 评测详情页模板（封面 + 元信息 + Steam 式结论徽章 + 评论正文）
REVIEW_DETAIL_TEMPLATE = '''<!DOCTYPE html>
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
        <a class="back-link" href="../../reviews.html">&larr; 返回评测</a>

        <h1>{title}</h1>

        <div class="review-hero">
            {cover_html}
            <div class="review-hero-meta">
                {verdict_html}
                <table class="review-meta-table">
{meta_rows}
                </table>
            </div>
        </div>

        <div class="entry-content">
            {content}
        </div>
    </div>
</body>
</html>
'''


class BlogEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("博客编辑器 - SayangChun")
        self.root.geometry("950x750")
        self.root.minsize(850, 650)
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="博客文章编辑器", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.create_tab_new()
        self.create_tab_edit()
        self.create_tab_delete()
        self.create_tab_tools()
        
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    # ==================== 新建文章选项卡 ====================
    
    def create_tab_new(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="  新建文章  ")
        
        # 类型选择
        row0 = ttk.Frame(tab)
        row0.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(row0, text="类型:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_type = tk.StringVar(value="成果")
        type_combo = ttk.Combobox(row0, textvariable=self.new_type,
                                  values=["成果", "动态", "评测"], state="readonly", width=12)
        type_combo.pack(side=tk.LEFT)
        type_combo.bind("<<ComboboxSelected>>", self.new_type_change)

        ttk.Label(row0, text="分类:").pack(side=tk.LEFT, padx=(20, 5))
        self.new_category = tk.StringVar(value="achievements")
        self.new_cat_combo = ttk.Combobox(row0, textvariable=self.new_category,
                                          values=list(CATEGORIES.keys()), state="readonly", width=12)
        self.new_cat_combo.pack(side=tk.LEFT)
        self.new_cat_combo.bind("<<ComboboxSelected>>", self.new_cat_change)

        # 标题
        row1 = ttk.Frame(tab)
        row1.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(row1, text="标题:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_title = tk.StringVar()
        ttk.Entry(row1, textvariable=self.new_title, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 日期和文件名
        row2 = ttk.Frame(tab)
        row2.pack(fill=tk.X, pady=(0, 8))

        self.new_date_label = ttk.Label(row2, text="日期:")
        self.new_date_label.pack(side=tk.LEFT, padx=(0, 5))
        self.new_date = tk.StringVar(value=datetime.now().strftime("%Y年%m月%d日"))
        self.new_date_entry = ttk.Entry(row2, textvariable=self.new_date, width=20)
        self.new_date_entry.pack(side=tk.LEFT, padx=(0, 20))

        self.new_slug_label = ttk.Label(row2, text="文件名:")
        self.new_slug_label.pack(side=tk.LEFT, padx=(0, 5))
        self.new_slug = tk.StringVar()
        ttk.Entry(row2, textvariable=self.new_slug, width=35).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 摘要（评测类型时隐藏，由"一句话短评"代替）
        self.new_summary_row = ttk.Frame(tab)
        self.new_summary_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(self.new_summary_row, text="摘要:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_summary = tk.StringVar()
        ttk.Entry(self.new_summary_row, textvariable=self.new_summary, width=65).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 评测属性区（仅"评测"类型显示；创建后不 pack，等待切换）
        self.new_review_frame, self.new_review_fields = self._build_review_fields(
            tab, slug_getter=lambda: self.new_slug.get())

        # 正文
        self.new_content_frame = ttk.LabelFrame(tab, text="正文内容 (支持HTML)", padding="5")
        self.new_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.new_content = scrolledtext.ScrolledText(self.new_content_frame, height=15, wrap=tk.WORD, font=("Consolas", 11))
        self.new_content.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="预览", command=self.new_preview).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="保存并更新列表", command=self.new_save).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空", command=self.new_clear).pack(side=tk.LEFT)
    
    # 类型 <-> 分类一一对应：成果/动态/评测
    _TYPE_CATEGORY = {"成果": "achievements", "动态": "updates", "评测": "reviews"}

    def new_type_change(self, event=None):
        cat = self._TYPE_CATEGORY.get(self.new_type.get(), "achievements")
        self.new_cat_combo.config(values=[cat])
        self.new_category.set(cat)
        self._show_new_review_fields(cat == "reviews")

    def new_cat_change(self, event=None):
        self._show_new_review_fields(self.new_category.get() == "reviews")

    def _show_new_review_fields(self, show):
        """评测类型：隐藏「日期」「摘要」两行，显示评测属性区（日期由「完成时间」承载）"""
        if show:
            self.new_date_label.pack_forget()
            self.new_date_entry.pack_forget()
            self.new_summary_row.pack_forget()
            self.new_review_frame.pack(fill=tk.X, pady=(0, 8), before=self.new_content_frame)
        else:
            self.new_review_frame.pack_forget()
            self.new_date_label.pack(side=tk.LEFT, padx=(0, 5), before=self.new_slug_label)
            self.new_date_entry.pack(side=tk.LEFT, padx=(0, 20), before=self.new_slug_label)
            self.new_summary_row.pack(fill=tk.X, pady=(0, 8), before=self.new_content_frame)
    
    def new_preview(self):
        html = self._generate_html(self.new_category.get(), self.new_title.get(), 
                                   self.new_date.get(), self.new_content.get("1.0", tk.END))
        if html:
            temp_file = BLOG_ROOT / "_preview.html"
            temp_file.write_text(html, encoding="utf-8")
            os.startfile(temp_file)
    
    def new_save(self):
        category = self.new_category.get()
        slug = self.new_slug.get().strip()
        title = self.new_title.get().strip()
        date = self.new_date.get().strip()
        summary = self.new_summary.get().strip()
        content = self.new_content.get("1.0", tk.END).strip()

        if not all([title, slug, content]):
            messagebox.showwarning("警告", "请填写标题、文件名和正文")
            return

        posts_dir = BLOG_ROOT / "posts" / category
        posts_dir.mkdir(parents=True, exist_ok=True)

        if category == "reviews":
            rv = self._collect_review_fields(self.new_review_fields)
            rv.update({"title": title, "slug": slug})
            html = self._generate_review_html(rv, content)
            (posts_dir / f"{slug}.html").write_text(html, encoding="utf-8")
            self._update_review_listing(rv)
        else:
            html = self._generate_html(category, title, date, content)
            (posts_dir / f"{slug}.html").write_text(html, encoding="utf-8")
            self._update_listing(category, slug, title, date, summary or title)

        self._update_homepage_date()

        self.status_var.set(f"已保存: posts/{category}/{slug}.html")
        messagebox.showinfo("成功", "文章已保存并更新列表")
    
    def new_clear(self):
        self.new_title.set("")
        self.new_slug.set("")
        self.new_summary.set("")
        self.new_date.set(datetime.now().strftime("%Y年%m月%d日"))
        self.new_content.delete("1.0", tk.END)
        for var in self.new_review_fields.values():
            var.set("")
        self.new_review_fields["type"].set("游戏")
        self.new_review_fields["verdict"].set("recommended")
    
    # ==================== 修改文章选项卡 ====================
    
    def create_tab_edit(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="  修改文章  ")
        
        # 修改模式选择
        mode_frame = ttk.LabelFrame(tab, text="修改模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.edit_mode = tk.StringVar(value="详情页")
        ttk.Radiobutton(mode_frame, text="详情页文章", variable=self.edit_mode, 
                        value="详情页", command=self.edit_mode_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="单页面（简历/工作流）", variable=self.edit_mode, 
                        value="单页面", command=self.edit_mode_change).pack(side=tk.LEFT)
        
        # 详情页选择区域
        self.edit_detail_frame = ttk.LabelFrame(tab, text="选择文章", padding="10")
        self.edit_detail_frame.pack(fill=tk.X, pady=(0, 10))
        
        row1 = ttk.Frame(self.edit_detail_frame)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row1, text="分类:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_category = tk.StringVar(value="achievements")
        self.edit_cat_combo = ttk.Combobox(row1, textvariable=self.edit_category,
                                           values=list(CATEGORIES.keys()), state="readonly", width=12)
        self.edit_cat_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.edit_cat_combo.bind("<<ComboboxSelected>>", self.edit_cat_changed)
        
        ttk.Label(row1, text="文章:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_post = tk.StringVar()
        self.edit_post_combo = ttk.Combobox(row1, textvariable=self.edit_post, state="readonly", width=40)
        self.edit_post_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(row1, text="加载", command=self.edit_load_post).pack(side=tk.LEFT, padx=(10, 0))
        
        # 单页面选择区域
        self.edit_single_frame = ttk.LabelFrame(tab, text="选择页面", padding="10")
        self.edit_single_frame.pack(fill=tk.X, pady=(0, 10))
        self.edit_single_frame.pack_forget()  # 默认隐藏
        
        row_s = ttk.Frame(self.edit_single_frame)
        row_s.pack(fill=tk.X)
        
        ttk.Label(row_s, text="页面:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_single = tk.StringVar(value="index")
        ttk.Combobox(row_s, textvariable=self.edit_single, 
                     values=list(SINGLE_PAGES.keys()), state="readonly", width=15).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(row_s, text="加载", command=self.edit_load_single).pack(side=tk.LEFT)
        
        # 编辑区域
        edit_frame = ttk.LabelFrame(tab, text="编辑内容", padding="10")
        edit_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        row2 = ttk.Frame(edit_frame)
        row2.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(row2, text="标题:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_title = tk.StringVar()
        ttk.Entry(row2, textvariable=self.edit_title, width=45).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.edit_date_row = ttk.Frame(edit_frame)
        self.edit_date_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(self.edit_date_row, text="日期:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_date = tk.StringVar()
        ttk.Entry(self.edit_date_row, textvariable=self.edit_date, width=20).pack(side=tk.LEFT)

        # 摘要行（评测分类时隐藏，由"一句话短评"代替）
        self.edit_summary_row = ttk.Frame(edit_frame)
        self.edit_summary_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(self.edit_summary_row, text="摘要:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_summary = tk.StringVar()
        ttk.Entry(self.edit_summary_row, textvariable=self.edit_summary, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 评测属性区（仅 reviews 分类显示）
        self.edit_review_frame, self.edit_review_fields = self._build_review_fields(
            edit_frame, slug_getter=lambda: self.edit_post.get())

        self.edit_content_frame = ttk.LabelFrame(edit_frame, text="正文内容", padding="5")
        self.edit_content_frame.pack(fill=tk.BOTH, expand=True)

        self.edit_content = scrolledtext.ScrolledText(self.edit_content_frame, height=12, wrap=tk.WORD, font=("Consolas", 11))
        self.edit_content.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="预览", command=self.edit_preview).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="保存修改", command=self.edit_save).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="更新列表", command=self.edit_update_listing).pack(side=tk.LEFT)
        
        self.edit_load_list()
    
    def edit_mode_change(self):
        if self.edit_mode.get() == "详情页":
            self.edit_detail_frame.pack(fill=tk.X, pady=(0, 10))
            self.edit_single_frame.pack_forget()
        else:
            self.edit_single_frame.pack(fill=tk.X, pady=(0, 10))
            self.edit_detail_frame.pack_forget()

    def edit_cat_changed(self, event=None):
        """切换分类：刷新文章列表 + 评测/普通字段区切换"""
        is_review = self.edit_category.get() == "reviews"
        if is_review:
            self.edit_date_row.pack_forget()
            self.edit_summary_row.pack_forget()
            self.edit_review_frame.pack(fill=tk.X, pady=(0, 5), before=self.edit_content_frame)
        else:
            self.edit_review_frame.pack_forget()
            self.edit_date_row.pack(fill=tk.X, pady=(0, 5), before=self.edit_summary_row)
            self.edit_summary_row.pack(fill=tk.X, pady=(0, 5), before=self.edit_content_frame)
        self.edit_load_list()
    
    def edit_load_list(self, event=None):
        category = self.edit_category.get()
        posts_dir = BLOG_ROOT / "posts" / category
        posts = [f.stem for f in posts_dir.glob("*.html")] if posts_dir.exists() else []
        self.edit_post_combo["values"] = posts
        if posts:
            self.edit_post.set(posts[0])
    
    def edit_load_post(self):
        category = self.edit_category.get()
        post_name = self.edit_post.get()
        if not post_name:
            return
        
        file_path = BLOG_ROOT / "posts" / category / f"{post_name}.html"
        if not file_path.exists():
            return
        
        content = file_path.read_text(encoding="utf-8")
        
        title_match = re.search(r'<h1>(.*?)</h1>', content)
        date_match = re.search(r'<p class="entry-date">(.*?)</p>', content)
        content_match = re.search(r'<div class="entry-content">\s*(.*?)\s*</div>', content, re.DOTALL)

        if title_match:
            self.edit_title.set(title_match.group(1))
        if category == "reviews":
            self.edit_date.set("")          # 评测不再使用独立日期字段，日期由「完成时间」承载
        elif date_match:
            self.edit_date.set(date_match.group(1))
        if content_match:
            raw = content_match.group(1)
            raw = re.sub(r'<p[^>]*>', '', raw)
            raw = re.sub(r'</p>', '\n', raw)
            self.edit_content.delete("1.0", tk.END)
            self.edit_content.insert("1.0", raw.strip())

        if category == "reviews":
            self._load_review_fields(self.edit_review_fields, content, post_name)
            self.edit_summary.set("")
        else:
            listing_file = BLOG_ROOT / CATEGORIES[category]["file"]
            if listing_file.exists():
                listing_content = listing_file.read_text(encoding="utf-8")
                summary_match = re.search(rf'href="posts/{category}/{post_name}\.html">.*?</a>.*?<p>(.*?)</p>', listing_content, re.DOTALL)
                if summary_match:
                    self.edit_summary.set(summary_match.group(1).strip())

        self.status_var.set(f"已加载: {post_name}.html")
    
    def edit_load_single(self):
        page_key = self.edit_single.get()
        config = SINGLE_PAGES[page_key]
        file_path = BLOG_ROOT / config["file"]
        
        if not file_path.exists():
            return
        
        content = file_path.read_text(encoding="utf-8")
        
        title_match = re.search(r'<h1>(.*?)</h1>', content, re.DOTALL)
        if title_match:
            self.edit_title.set(re.sub(r'<[^>]+>', '', title_match.group(1)).strip())
        
        content_match = re.search(r'<div class="entry-content">\s*(.*?)\s*</div>', content, re.DOTALL)
        if content_match:
            raw = content_match.group(1)
            self.edit_content.delete("1.0", tk.END)
            self.edit_content.insert("1.0", raw.strip())
        
        self.edit_date.set("")
        self.edit_summary.set("")
        self.status_var.set(f"已加载: {config['file']}")
    
    def edit_preview(self):
        if self.edit_mode.get() == "详情页":
            html = self._generate_html(self.edit_category.get(), self.edit_title.get(), 
                                       self.edit_date.get(), self.edit_content.get("1.0", tk.END))
        else:
            page_key = self.edit_single.get()
            config = SINGLE_PAGES[page_key]
            html = self._generate_single_html(config["file"], self.edit_content.get("1.0", tk.END))
        
        if html:
            temp_file = BLOG_ROOT / "_preview.html"
            temp_file.write_text(html, encoding="utf-8")
            os.startfile(temp_file)
    
    def edit_save(self):
        content = self.edit_content.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showwarning("警告", "请输入正文内容")
            return
        
        if self.edit_mode.get() == "详情页":
            category = self.edit_category.get()
            post_name = self.edit_post.get()
            title = self.edit_title.get().strip()
            date = self.edit_date.get().strip()

            if not all([post_name, title]):
                messagebox.showwarning("警告", "请填写完整信息")
                return

            file_path = BLOG_ROOT / "posts" / category / f"{post_name}.html"
            if category == "reviews":
                rv = self._collect_review_fields(self.edit_review_fields)
                rv.update({"title": title, "slug": post_name})
                html = self._generate_review_html(rv, content)
            else:
                html = self._generate_html(category, title, date, content)
            file_path.write_text(html, encoding="utf-8")
            self.status_var.set(f"已保存: {post_name}.html")
        else:
            page_key = self.edit_single.get()
            config = SINGLE_PAGES[page_key]
            file_path = BLOG_ROOT / config["file"]
            
            original = file_path.read_text(encoding="utf-8")
            new_content = re.sub(
                r'(<div class="entry-content">)\s*(.*?)\s*(</div>)',
                r'\1\n' + content + r'\n        \3',
                original, flags=re.DOTALL
            )
            file_path.write_text(new_content, encoding="utf-8")
            self.status_var.set(f"已保存: {config['file']}")
        
        self._update_homepage_date()
        messagebox.showinfo("成功", "已保存")
    
    def edit_update_listing(self):
        if self.edit_mode.get() == "单页面":
            messagebox.showinfo("提示", "单页面无需更新列表")
            return

        category = self.edit_category.get()
        post_name = self.edit_post.get()
        title = self.edit_title.get().strip()
        date = self.edit_date.get().strip()
        summary = self.edit_summary.get().strip()

        ok = all([post_name, title]) if category == "reviews" else all([post_name, title, date])
        if not ok:
            messagebox.showwarning("警告", "请填写完整信息")
            return

        listing_file = BLOG_ROOT / CATEGORIES[category]["file"]
        if listing_file.exists():
            content = listing_file.read_text(encoding="utf-8")
            content = self._remove_listing_entry(content, category, post_name)
            listing_file.write_text(content, encoding="utf-8")

        if category == "reviews":
            rv = self._collect_review_fields(self.edit_review_fields)
            rv.update({"title": title, "slug": post_name})
            self._update_review_listing(rv)
        else:
            self._update_listing(category, post_name, title, date, summary or title)
        messagebox.showinfo("成功", "列表已更新")
    
    # ==================== 删除文章选项卡 ====================
    
    def create_tab_delete(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="  删除文章  ")
        
        # 类型选择
        row0 = ttk.Frame(tab)
        row0.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(row0, text="类型:").pack(side=tk.LEFT, padx=(0, 5))
        self.del_type = tk.StringVar(value="成果")
        type_combo = ttk.Combobox(row0, textvariable=self.del_type,
                                  values=["成果", "动态", "评测"], state="readonly", width=12)
        type_combo.pack(side=tk.LEFT)
        type_combo.bind("<<ComboboxSelected>>", self.del_type_change)
        
        ttk.Label(row0, text="分类:").pack(side=tk.LEFT, padx=(20, 5))
        self.del_category = tk.StringVar(value="achievements")
        self.del_cat_combo = ttk.Combobox(row0, textvariable=self.del_category, 
                                          values=list(CATEGORIES.keys()), state="readonly", width=12)
        self.del_cat_combo.pack(side=tk.LEFT)
        self.del_cat_combo.bind("<<ComboboxSelected>>", self.del_load_list)
        
        # 选择文章
        select_frame = ttk.LabelFrame(tab, text="选择要删除的文章", padding="10")
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        row1 = ttk.Frame(select_frame)
        row1.pack(fill=tk.X)
        
        ttk.Label(row1, text="文章:").pack(side=tk.LEFT, padx=(0, 5))
        self.del_post = tk.StringVar()
        self.del_post_combo = ttk.Combobox(row1, textvariable=self.del_post, state="readonly", width=50)
        self.del_post_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(row1, text="刷新", command=self.del_load_list).pack(side=tk.LEFT, padx=(10, 0))
        
        # 预览
        preview_frame = ttk.LabelFrame(tab, text="文章预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.del_preview = scrolledtext.ScrolledText(preview_frame, height=12, wrap=tk.WORD, font=("Consolas", 11), state=tk.DISABLED)
        self.del_preview.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(preview_frame, text="加载预览", command=self.del_load_preview).pack(pady=(5, 0))
        
        # 按钮
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="删除文章", command=self.del_delete_post).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="同步列表", command=self.del_sync_listing).pack(side=tk.LEFT)
        
        self.del_load_list()
    
    def del_type_change(self, event=None):
        cat = self._TYPE_CATEGORY.get(self.del_type.get(), "achievements")
        self.del_cat_combo.config(values=[cat])
        self.del_category.set(cat)
        self.del_load_list()
    
    def del_load_list(self, event=None):
        category = self.del_category.get()
        posts_dir = BLOG_ROOT / "posts" / category
        posts = [f.stem for f in posts_dir.glob("*.html")] if posts_dir.exists() else []
        self.del_post_combo["values"] = posts
        if posts:
            self.del_post.set(posts[0])
        else:
            self.del_post.set("")
    
    def del_load_preview(self):
        category = self.del_category.get()
        post_name = self.del_post.get()
        if not post_name:
            return
        
        file_path = BLOG_ROOT / "posts" / category / f"{post_name}.html"
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            self.del_preview.config(state=tk.NORMAL)
            self.del_preview.delete("1.0", tk.END)
            self.del_preview.insert("1.0", content)
            self.del_preview.config(state=tk.DISABLED)
    
    def del_delete_post(self):
        category = self.del_category.get()
        post_name = self.del_post.get()
        if not post_name:
            messagebox.showwarning("警告", "请选择要删除的文章")
            return
        
        if not messagebox.askyesno("确认删除", f"确定要删除文章 \"{post_name}\" 吗？\n此操作不可恢复。"):
            return
        
        file_path = BLOG_ROOT / "posts" / category / f"{post_name}.html"
        if file_path.exists():
            file_path.unlink()

        listing_file = BLOG_ROOT / CATEGORIES[category]["file"]
        if listing_file.exists():
            content = listing_file.read_text(encoding="utf-8")
            content = self._remove_listing_entry(content, category, post_name)
            listing_file.write_text(content, encoding="utf-8")
        
        self._update_homepage_date()
        self.del_load_list()
        self.del_preview.config(state=tk.NORMAL)
        self.del_preview.delete("1.0", tk.END)
        self.del_preview.config(state=tk.DISABLED)
        
        self.status_var.set(f"已删除: {post_name}.html")
        messagebox.showinfo("成功", "文章已删除")
    
    def del_sync_listing(self):
        self._sync_listing(self.del_category.get())
        self.del_load_list()
        messagebox.showinfo("完成", "列表已同步")
    
    # ==================== 工具选项卡 ====================
    
    def create_tab_tools(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="  工具  ")
        
        sync_frame = ttk.LabelFrame(tab, text="列表同步", padding="10")
        sync_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sync_frame, text="检查并移除列表中已删除文章的条目").pack(anchor=tk.W)
        ttk.Button(sync_frame, text="同步所有列表", command=self.tools_sync_all).pack(pady=(10, 0))
        
        date_frame = ttk.LabelFrame(tab, text="首页日期", padding="10")
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(date_frame, text="更新首页显示的最后更新日期").pack(anchor=tk.W)
        btn_row = ttk.Frame(date_frame)
        btn_row.pack(fill=tk.X, pady=(10, 0))
        
        self.tools_date = tk.StringVar(value=datetime.now().strftime("%Y年%m月%d日"))
        ttk.Entry(btn_row, textvariable=self.tools_date, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_row, text="更新日期", command=self.tools_update_date).pack(side=tk.LEFT)
        
        info_frame = ttk.LabelFrame(tab, text="博客信息", padding="10")
        info_frame.pack(fill=tk.X)
        
        self.tools_info = tk.Text(info_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.tools_info.pack(fill=tk.X)
        self.tools_show_info()
    
    def tools_sync_all(self):
        for category in CATEGORIES:
            self._sync_listing(category)
        self.edit_load_list()
        self.del_load_list()
        messagebox.showinfo("完成", "所有列表已同步")
    
    def tools_update_date(self):
        today = self.tools_date.get().strip()
        if not today:
            today = datetime.now().strftime("%Y年%m月%d日")
        
        index_file = BLOG_ROOT / "index.html"
        if index_file.exists():
            content = index_file.read_text(encoding="utf-8")
            new_content = re.sub(r'\d{4}年\d{1,2}月\d{1,2}日更新', f'{today}更新', content)
            if new_content != content:
                index_file.write_text(new_content, encoding="utf-8")
                messagebox.showinfo("成功", f"首页日期已更新为: {today}")
            else:
                messagebox.showinfo("提示", "日期未变化")
    
    def tools_show_info(self):
        info = ["--- 文章分类 ---"]
        for category, config in CATEGORIES.items():
            posts_dir = BLOG_ROOT / "posts" / category
            count = len(list(posts_dir.glob("*.html"))) if posts_dir.exists() else 0
            info.append(f"  {config['name']}: {count} 篇")
        
        info.append("\n--- 单页面 ---")
        for key, config in SINGLE_PAGES.items():
            exists = "✓" if (BLOG_ROOT / config["file"]).exists() else "✗"
            info.append(f"  {config['name']}: {exists}")
        
        self.tools_info.config(state=tk.NORMAL)
        self.tools_info.delete("1.0", tk.END)
        self.tools_info.insert("1.0", "\n".join(info))
        self.tools_info.config(state=tk.DISABLED)
    
    # ==================== 通用方法 ====================
    
    def _generate_html(self, category, title, date, content):
        if not title:
            messagebox.showwarning("警告", "请输入标题")
            return None
        if not content:
            messagebox.showwarning("警告", "请输入正文内容")
            return None
        
        if "<p>" not in content:
            paragraphs = content.split("\n\n")
            content = "\n".join(f"            <p>{p.strip()}</p>" for p in paragraphs if p.strip())
        
        config = CATEGORIES[category]
        return DETAIL_TEMPLATE.format(
            title=title, date=date, content=content,
            listing_file=config["file"], category_name=config["name"]
        )
    
    def _generate_single_html(self, filename, content):
        file_path = BLOG_ROOT / filename
        if not file_path.exists():
            return None
        
        original = file_path.read_text(encoding="utf-8")
        new_content = re.sub(
            r'(<div class="entry-content">)\s*(.*?)\s*(</div>)',
            r'\1\n' + content + r'\n        \3',
            original, flags=re.DOTALL
        )
        return new_content
    
    def _update_listing(self, category, slug, title, date, summary):
        listing_file = BLOG_ROOT / CATEGORIES[category]["file"]
        if not listing_file.exists():
            return
        
        content = listing_file.read_text(encoding="utf-8")
        
        new_entry = f'''
        <div class="entry">
            <div class="entry-header">
                <a class="entry-title" href="posts/{category}/{slug}.html">{title}</a>
                <span class="entry-date">{date}</span>
            </div>
            <div class="entry-content">
                <p>{summary}</p>
            </div>
        </div>
'''
        
        pattern = r'(        <div class="entry">)'
        match = re.search(pattern, content)
        if match:
            new_content = content[:match.start()] + new_entry + content[match.start():]
        else:
            pattern = r'(        <h1>.*?</h1>\s*)'
            new_content = re.sub(pattern, r'\1' + new_entry, content, flags=re.DOTALL)
        
        listing_file.write_text(new_content, encoding="utf-8")
    
    def _update_homepage_date(self):
        index_file = BLOG_ROOT / "index.html"
        if not index_file.exists():
            return
        
        today = datetime.now().strftime("%Y年%m月%d日")
        content = index_file.read_text(encoding="utf-8")
        new_content = re.sub(r'\d{4}年\d{1,2}月\d{1,2}日更新', f'{today}更新', content)
        
        if new_content != content:
            index_file.write_text(new_content, encoding="utf-8")
    
    def _sync_listing(self, category):
        listing_file = BLOG_ROOT / CATEGORIES[category]["file"]
        if not listing_file.exists():
            return
        
        posts_dir = BLOG_ROOT / "posts" / category
        existing_files = {f.stem for f in posts_dir.glob("*.html")} if posts_dir.exists() else set()
        
        content = listing_file.read_text(encoding="utf-8")
        entries = re.findall(r'(<div class="entry(?: review-card)?"[^>]*>.*?</div>\s*</div>)', content, re.DOTALL)
        
        new_content = content
        for entry in entries:
            href_match = re.search(r'href="posts/[^/]+/(.+?)\.html"', entry)
            if href_match and href_match.group(1) not in existing_files:
                new_content = new_content.replace(entry, '')
        
        new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
        
        if new_content != content:
            listing_file.write_text(new_content, encoding="utf-8")

    # ==================== 评测专属方法 ====================

    def _build_review_fields(self, parent, slug_getter=None):
        """构建评测属性表单区，返回 (frame, fields)。"""
        frame = ttk.LabelFrame(parent, text="评测属性", padding="10")
        fields = {
            "type": tk.StringVar(value="游戏"),
            "verdict": tk.StringVar(value="recommended"),
            "original_title": tk.StringVar(),
            "creator": tk.StringVar(),
            "publisher": tk.StringVar(),
            "release_date": tk.StringVar(),
            "platform": tk.StringVar(),
            "finished_at": tk.StringVar(),
            "hours": tk.StringVar(),
            "one_liner": tk.StringVar(),
            "cover": tk.StringVar(),
        }

        r1 = ttk.Frame(frame); r1.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(r1, text="作品类型:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(r1, textvariable=fields["type"],
                     values=list(REVIEW_TYPE_LABELS.values()), state="readonly", width=10).pack(side=tk.LEFT, padx=(0, 25))
        ttk.Label(r1, text="结论:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(r1, text="👍 推荐", variable=fields["verdict"], value="recommended").pack(side=tk.LEFT)
        ttk.Radiobutton(r1, text="👎 不推荐", variable=fields["verdict"], value="not-recommended").pack(side=tk.LEFT, padx=(8, 0))

        r2 = ttk.Frame(frame); r2.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(r2, text="原名:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r2, textvariable=fields["original_title"], width=22).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Label(r2, text="主创:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r2, textvariable=fields["creator"], width=22).pack(side=tk.LEFT, fill=tk.X, expand=True)

        r3 = ttk.Frame(frame); r3.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(r3, text="发行商:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r3, textvariable=fields["publisher"], width=22).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Label(r3, text="发行日期:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r3, textvariable=fields["release_date"], width=22).pack(side=tk.LEFT, fill=tk.X, expand=True)

        r4 = ttk.Frame(frame); r4.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(r4, text="平台:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r4, textvariable=fields["platform"], width=22).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Label(r4, text="总时数:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r4, textvariable=fields["hours"], width=22).pack(side=tk.LEFT, fill=tk.X, expand=True)

        r5 = ttk.Frame(frame); r5.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(r5, text="完成时间:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r5, textvariable=fields["finished_at"], width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)

        r6 = ttk.Frame(frame); r6.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(r6, text="一句话短评:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r6, textvariable=fields["one_liner"], width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)

        r7 = ttk.Frame(frame); r7.pack(fill=tk.X)
        ttk.Label(r7, text="封面:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(r7, textvariable=fields["cover"], width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        if slug_getter:
            ttk.Button(r7, text="浏览…", command=lambda: self._pick_cover(fields["cover"], slug_getter)).pack(side=tk.LEFT, padx=(8, 0))

        return frame, fields

    def _pick_cover(self, cover_var, slug_getter):
        """选择图片并复制到 assets/covers/，自动填入路径。"""
        path = filedialog.askopenfilename(
            title="选择封面图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.gif")]
        )
        if not path:
            return
        src = Path(path)
        covers_dir = BLOG_ROOT / "assets" / "covers"
        covers_dir.mkdir(parents=True, exist_ok=True)
        stem = (slug_getter().strip() if callable(slug_getter) else str(slug_getter).strip()) or src.stem
        ext = src.suffix.lower() or ".jpg"
        dst = covers_dir / f"{stem}{ext}"
        if dst.exists():
            dst = covers_dir / f"{stem}_{datetime.now().strftime('%H%M%S')}{ext}"
        shutil.copy2(src, dst)
        cover_var.set(f"assets/covers/{dst.name}")
        self.status_var.set(f"封面已复制: {dst.name}")

    def _collect_review_fields(self, fields):
        """从表单 StringVar 收集为 dict。"""
        label = fields["type"].get()
        rv_type = REVIEW_TYPE_KEYS.get(label, "game")
        return {
            "type": rv_type,
            "verdict": fields["verdict"].get() or "recommended",
            "original_title": fields["original_title"].get().strip(),
            "creator": fields["creator"].get().strip(),
            "publisher": fields["publisher"].get().strip(),
            "release_date": fields["release_date"].get().strip(),
            "platform": fields["platform"].get().strip(),
            "finished_at": strip_clock(fields["finished_at"].get().strip()),
            "hours": fields["hours"].get().strip(),
            "one_liner": fields["one_liner"].get().strip(),
            "cover": fields["cover"].get().strip(),
        }

    def _load_review_fields(self, fields, content, post_name):
        """从评测详情页 HTML 解析并回填表单。"""
        m = re.search(r'class="review-verdict (up|down)"', content)
        if m:
            fields["verdict"].set("recommended" if m.group(1) == "up" else "not-recommended")

        m = re.search(r'<tr><th>类型</th><td>(.*?)</td></tr>', content)
        fields["type"].set(m.group(1).strip() if m else "游戏")

        for label, key in [
            ("原名", "original_title"),
            ("发行商", "publisher"),
            ("发行日期", "release_date"),
            ("平台", "platform"),
            ("总时数", "hours"),
            ("完成时间", "finished_at"),
        ]:
            mm = re.search(rf'<tr><th>{label}</th><td>(.*?)</td></tr>', content)
            fields[key].set(mm.group(1).strip() if mm else "")

        # 主创行按作品类型显示为 开发者 / 作者 / 导演 / 创作者
        mm = re.search(rf'<tr><th>(?:{CREATOR_LABEL_PATTERN})</th><td>(.*?)</td></tr>', content)
        fields["creator"].set(mm.group(1).strip() if mm else "")

        m = re.search(r'<img class="review-hero-cover" src="\.\./\.\./(assets/covers/[^"]+)"', content)
        fields["cover"].set(m.group(1) if m else "")

        listing_file = BLOG_ROOT / "reviews.html"
        if listing_file.exists():
            lc = listing_file.read_text(encoding="utf-8")
            m = re.search(rf'href="posts/reviews/{re.escape(post_name)}\.html".*?<p class="review-one">(.*?)</p>', lc, re.DOTALL)
            fields["one_liner"].set(m.group(1).strip() if m else "")

    def _generate_review_html(self, rv, content):
        """生成评测详情页 HTML。"""
        if not rv.get("title"):
            messagebox.showwarning("警告", "请输入标题")
            return None
        if not content:
            messagebox.showwarning("警告", "请输入正文内容")
            return None

        if "<p>" not in content:
            paragraphs = content.split("\n\n")
            content = "\n".join(f"            <p>{p.strip()}</p>" for p in paragraphs if p.strip())

        verdict = rv.get("verdict", "recommended")
        cls = "up" if verdict == "recommended" else "down"
        verdict_html = f'<span class="review-verdict {cls}">{VERDICT_LABELS[verdict]}</span>'

        icon = REVIEW_TYPE_ICONS.get(rv["type"], "🎬")
        if rv.get("cover"):
            cover_html = f'<img class="review-hero-cover" src="../../{rv["cover"]}" alt="{rv["title"]} 封面">'
        else:
            cover_html = f'<div class="review-hero-cover"><span>{icon}</span></div>'

        # 详情页展示完整作品信息（列表卡片另做精简，见 _review_card_html）
        rows = []
        def add_row(label, value):
            if value:
                rows.append(f"                    <tr><th>{label}</th><td>{value}</td></tr>")
        add_row("原名", rv.get("original_title"))
        add_row(CREATOR_LABELS.get(rv["type"], "主创"), rv.get("creator"))
        add_row("发行商", rv.get("publisher"))
        add_row("发行日期", rv.get("release_date"))
        add_row("类型", REVIEW_TYPE_LABELS.get(rv["type"], rv["type"]))
        add_row("平台", rv.get("platform"))
        add_row("总时数", rv.get("hours"))
        add_row("完成时间", rv.get("finished_at"))
        meta_rows = "\n".join(rows)

        return REVIEW_DETAIL_TEMPLATE.format(
            title=rv["title"],
            cover_html=cover_html, verdict_html=verdict_html,
            meta_rows=meta_rows, content=content
        )

    def _review_card_html(self, rv):
        """生成 reviews.html 列表页卡片：只展示 结论 / 总时数 / 完成时间 / 评论。"""
        verdict = rv.get("verdict", "recommended")
        cls = "up" if verdict == "recommended" else "down"
        icon = REVIEW_TYPE_ICONS.get(rv["type"], "🎬")
        href = f'posts/reviews/{rv["slug"]}.html'
        cover_inner = (f'<img src="{rv["cover"]}" alt="{rv["title"]} 封面">'
                       if rv.get("cover") else f'<span>{icon}</span>')
        meta_bits = " · ".join(x for x in [
            (f'总时数 {rv["hours"]}' if rv.get("hours") else ""),
            (f'完成于 {rv["finished_at"]}' if rv.get("finished_at") else ""),
        ] if x)
        meta_html = f'\n                <p class="review-meta">{meta_bits}</p>' if meta_bits else ""
        one = rv.get("one_liner", "")
        one_html = f'\n                <p class="review-one">{one}</p>' if one else ""
        return f'''        <div class="entry review-card" data-type="{rv['type']}" data-verdict="{verdict}">
            <a class="review-cover" href="{href}">{cover_inner}</a>
            <div class="review-body">
                <div class="review-head">
                    <a class="entry-title" href="{href}">{rv['title']}</a>
                    <span class="review-verdict {cls}">{VERDICT_LABELS[verdict]}</span>
                </div>{meta_html}{one_html}
            </div>
        </div>'''

    def _update_review_listing(self, rv):
        """更新 reviews.html：移除旧卡片（如有），插入新卡片到列表顶部。"""
        listing_file = BLOG_ROOT / "reviews.html"
        if not listing_file.exists():
            return
        content = listing_file.read_text(encoding="utf-8")
        content = self._remove_listing_entry(content, "reviews", rv["slug"])
        card = self._review_card_html(rv)
        marker = '<div class="review-list">'
        idx = content.find(marker)
        if idx != -1:
            insert_at = idx + len(marker)
            content = content[:insert_at] + "\n" + card + content[insert_at:]
        listing_file.write_text(content, encoding="utf-8")

    def _remove_listing_entry(self, content, category, post_name):
        """从列表页 HTML 中移除指定 slug 的 entry 或 review-card（通用）。"""
        for pattern in (
            rf'<div class="entry">.*?href="posts/{category}/{post_name}\.html".*?</div>\s*</div>',
            rf'<div class="entry review-card"[^>]*>.*?href="posts/{category}/{post_name}\.html".*?</div>\s*</div>',
        ):
            new_content = re.sub(pattern, '', content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                break
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        return content


def main():
    root = tk.Tk()
    app = BlogEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
