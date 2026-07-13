/* 共享顶部导航：所有页面引入本脚本即可注入导航条，并高亮当前页。
   链接始终基于站点根目录解析，因此在详情页（posts/.../xxx.html）中
   点击导航也能正确跳回顶层页面。 */
(function () {
    /* 通过 nav.js 自身的 URL 推算站点根目录，避免相对路径在子目录中出错 */
    var scriptSrc = (document.currentScript && document.currentScript.src) || '';
    var baseUrl = '';
    if (scriptSrc) {
        baseUrl = scriptSrc.replace(/assets\/nav\.js(\?.*)?$/, '');
    }

    function resolve(file) {
        if (baseUrl) {
            return baseUrl + file;
        }
        /* 兜底：根据当前路径深度补 ../（多数情况下 currentScript 可用，此分支极少触发） */
        var segs = window.location.pathname.split('/').filter(Boolean);
        segs.pop(); /* 去掉文件名 */
        var prefix = '';
        for (var i = 0; i < segs.length; i++) {
            prefix += '../';
        }
        return prefix + file;
    }

    function buildNav() {
        var navItems = [
            { file: 'index.html', label: '简历' },
            { file: 'articles.html', label: '文章' },
            { file: 'thinking.html', label: '思考' },
            { file: 'achievements.html', label: '成果' },
            { file: 'updates.html', label: '动态' },
            { file: 'workflow.html', label: '工作流' }
        ];

        var path = window.location.pathname.split('/').pop() || 'index.html';
        var nav = document.createElement('nav');
        nav.className = 'sidenav';

        navItems.forEach(function (item) {
            var a = document.createElement('a');
            a.href = resolve(item.file);
            a.textContent = item.label;
            /* en.html 是简历英文版，仍高亮「简历」 */
            if (path === item.file || (item.file === 'index.html' && path === 'en.html')) {
                a.className = 'active';
            }
            nav.appendChild(a);
        });

        /* 将导航与页面内容包裹进一个 flex 布局：左侧导航，右侧内容 */
        var layout = document.createElement('div');
        layout.className = 'layout';
        while (document.body.firstChild) {
            layout.appendChild(document.body.firstChild);
        }
        document.body.appendChild(layout);
        layout.insertBefore(nav, layout.firstChild);
    }

    if (document.body) {
        buildNav();
    } else {
        document.addEventListener('DOMContentLoaded', buildNav);
    }
})();
