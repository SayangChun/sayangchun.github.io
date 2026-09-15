#!/usr/bin/env python3
"""
博客图形化编辑器 - 用于管理博客文章
用法: python blog_editor.pyw
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import re
from pathlib import Path
from datetime import datetime

# 博客根目录
BLOG_ROOT = Path(__file__).parent

# 分类配置（文章详情页）
CATEGORIES = {
    "achievements": {"name": "成果", "file": "achievements.html"},
    "updates": {"name": "动态", "file": "updates.html"},
}

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
                                  values=["成果", "动态"], state="readonly", width=12)
        type_combo.pack(side=tk.LEFT)
        type_combo.bind("<<ComboboxSelected>>", self.new_type_change)
        
        ttk.Label(row0, text="分类:").pack(side=tk.LEFT, padx=(20, 5))
        self.new_category = tk.StringVar(value="achievements")
        self.new_cat_combo = ttk.Combobox(row0, textvariable=self.new_category, 
                                          values=list(CATEGORIES.keys()), state="readonly", width=12)
        self.new_cat_combo.pack(side=tk.LEFT)
        
        # 标题
        row1 = ttk.Frame(tab)
        row1.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(row1, text="标题:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_title = tk.StringVar()
        ttk.Entry(row1, textvariable=self.new_title, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 日期和文件名
        row2 = ttk.Frame(tab)
        row2.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(row2, text="日期:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_date = tk.StringVar(value=datetime.now().strftime("%Y年%m月%d日"))
        ttk.Entry(row2, textvariable=self.new_date, width=20).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row2, text="文件名:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_slug = tk.StringVar()
        ttk.Entry(row2, textvariable=self.new_slug, width=35).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 摘要
        row3 = ttk.Frame(tab)
        row3.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(row3, text="摘要:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_summary = tk.StringVar()
        ttk.Entry(row3, textvariable=self.new_summary, width=65).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 正文
        content_frame = ttk.LabelFrame(tab, text="正文内容 (支持HTML)", padding="5")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.new_content = scrolledtext.ScrolledText(content_frame, height=15, wrap=tk.WORD, font=("Consolas", 11))
        self.new_content.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="预览", command=self.new_preview).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="保存并更新列表", command=self.new_save).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空", command=self.new_clear).pack(side=tk.LEFT)
    
    def new_type_change(self, event=None):
        if self.new_type.get() == "动态":
            self.new_cat_combo.config(values=["updates"])
            self.new_category.set("updates")
        else:
            self.new_cat_combo.config(values=list(CATEGORIES.keys()))
            self.new_category.set("achievements")
    
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
        
        html = self._generate_html(category, title, date, content)
        posts_dir = BLOG_ROOT / "posts" / category
        posts_dir.mkdir(parents=True, exist_ok=True)
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
        self.edit_cat_combo.bind("<<ComboboxSelected>>", self.edit_load_list)
        
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
        
        row3 = ttk.Frame(edit_frame)
        row3.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row3, text="日期:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_date = tk.StringVar()
        ttk.Entry(row3, textvariable=self.edit_date, width=20).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row3, text="摘要:").pack(side=tk.LEFT, padx=(0, 5))
        self.edit_summary = tk.StringVar()
        ttk.Entry(row3, textvariable=self.edit_summary, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        content_frame = ttk.LabelFrame(edit_frame, text="正文内容", padding="5")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.edit_content = scrolledtext.ScrolledText(content_frame, height=12, wrap=tk.WORD, font=("Consolas", 11))
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
        if date_match:
            self.edit_date.set(date_match.group(1))
        if content_match:
            raw = content_match.group(1)
            raw = re.sub(r'<p[^>]*>', '', raw)
            raw = re.sub(r'</p>', '\n', raw)
            self.edit_content.delete("1.0", tk.END)
            self.edit_content.insert("1.0", raw.strip())
        
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
            
            html = self._generate_html(category, title, date, content)
            file_path = BLOG_ROOT / "posts" / category / f"{post_name}.html"
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
        
        if not all([post_name, title, date]):
            messagebox.showwarning("警告", "请填写完整信息")
            return
        
        listing_file = BLOG_ROOT / CATEGORIES[category]["file"]
        if listing_file.exists():
            content = listing_file.read_text(encoding="utf-8")
            pattern = rf'<div class="entry">.*?href="posts/{category}/{post_name}\.html".*?</div>\s*</div>'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            listing_file.write_text(content, encoding="utf-8")
        
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
                                  values=["成果", "动态"], state="readonly", width=12)
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
        if self.del_type.get() == "动态":
            self.del_cat_combo.config(values=["updates"])
            self.del_category.set("updates")
        else:
            self.del_cat_combo.config(values=list(CATEGORIES.keys()))
            self.del_category.set("achievements")
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
            pattern = rf'<div class="entry">.*?href="posts/{category}/{post_name}\.html".*?</div>\s*</div>'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
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
        entries = re.findall(r'(<div class="entry">.*?</div>\s*</div>)', content, re.DOTALL)
        
        new_content = content
        for entry in entries:
            href_match = re.search(r'href="posts/[^/]+/(.+?)\.html"', entry)
            if href_match and href_match.group(1) not in existing_files:
                new_content = new_content.replace(entry, '')
        
        new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
        
        if new_content != content:
            listing_file.write_text(new_content, encoding="utf-8")


def main():
    root = tk.Tk()
    app = BlogEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
