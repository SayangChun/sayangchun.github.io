/* 共享顶部导航：所有页面引入本脚本即可注入导航条，并高亮当前页 */
(function () {
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
            a.href = item.file;
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
