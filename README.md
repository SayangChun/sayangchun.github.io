# sayangchun.github.io

个人静态展示站：简历、文章、经验、成果、动态与工作流。无构建工具，纯 HTML / CSS / JS，适合 GitHub Pages 直接托管。

## 怎么更新

本站不打算做后台或 CMS。日常维护方式是：

1. 把要发布的内容发给 AI（正文、标题、日期、摘要、放在哪个栏目等）
2. 由 AI 直接改仓库里的 HTML / CSS / JS 并提交（或给出可粘贴的改动）
3. 推送到 GitHub 后，Pages 自动上线

**发给 AI 时尽量说清：**

| 信息 | 示例 |
|------|------|
| 栏目 | 文章 / 经验 / 成果 / 动态 / 工作流 / 简历 |
| 标题 | 《某某》 |
| 日期 | 2026年7月13日 |
| 摘要 | 列表页一句话 |
| 正文 | 全文（Markdown 或纯文本均可） |
| 其它 | 外链、是否新建详情页、是否改导航或样式 |

简历中英文分开维护：`index.html`（中文）、`en.html`（英文）。

## 目录结构

```
.
├── index.html              # 简历（中文）
├── en.html                 # 简历（英文）
├── articles.html           # 文章列表
├── experience.html         # 经验列表
├── achievements.html       # 成果列表
├── updates.html            # 动态列表
├── workflow.html           # 工作流
├── avatar.png              # 头像 / favicon
├── assets/
│   ├── style.css           # 全站样式（含暗色模式）
│   └── nav.js              # 侧栏导航注入与当前页高亮
└── posts/
    ├── articles/           # 文章详情
    ├── experience/         # 经验详情
    └── achievements/       # 成果详情
```

- **列表页**：根目录对应栏目的 `*.html`，每条记录是一个 `.entry` 块。
- **详情页**：放在 `posts/<栏目>/` 下，从列表标题链过去；需带返回对应列表的链接。
- **导航**：各页引入 `assets/nav.js` 即可；脚本按站点根路径解析链接，详情页也能点回顶层栏目。

## 本地预览

任意静态服务器打开根目录即可，例如：

```bash
npx serve .
```

或用编辑器 / 浏览器直接打开 `index.html`（部分路径在 `file://` 下可能异常，优先用本地服务）。

## 部署

仓库推送到 GitHub 后，在仓库 Settings → Pages 中选择对应分支与根目录即可。站点域名一般为 `https://sayangchun.github.io`。

## License

MIT · Copyright (c) 2026 SayangChun
