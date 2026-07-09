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
            { file: 'experience.html', label: '经验' },
            { file: 'achievements.html', label: '成果' }
        ];

        var path = window.location.pathname.split('/').pop() || 'index.html';
        var nav = document.createElement('nav');
        nav.className = 'topnav';

        navItems.forEach(function (item) {
            var a = document.createElement('a');
            a.href = resolve(item.file);
            a.textContent = item.label;
            if (path === item.file) {
                a.className = 'active';
            }
            nav.appendChild(a);
        });

        document.body.insertBefore(nav, document.body.firstChild);
    }

    if (document.body) {
        buildNav();
    } else {
        document.addEventListener('DOMContentLoaded', buildNav);
    }
})();
