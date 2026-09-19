/* 评测列表页脚本：类型 / 结论双维筛选 + 顶部统计条。
   卡片由 .review-card[data-type][data-verdict] 标注，
   编辑器增删卡片后本脚本自动适应（筛选按钮按现有条目动态生成），
   无需修改此文件。支持 URL hash 分享筛选结果：
   reviews.html#type=game&verdict=not-recommended */
(function () {
    var TYPE_LABELS = {
        game: '游戏',
        book: '书',
        movie: '电影',
        anime: '动画',
        series: '剧集',
        music: '音乐'
    };
    var TYPE_ICONS = {
        game: '🎮',
        book: '📖',
        movie: '🎬',
        anime: '🌸',
        series: '📺',
        music: '🎧'
    };
    var VERDICT_LABELS = {
        recommended: '👍 推荐',
        'not-recommended': '👎 不推荐'
    };

    var state = { type: 'all', verdict: 'all' };

    function qsa(sel) {
        return Array.prototype.slice.call(document.querySelectorAll(sel));
    }

    function init() {
        var cards = qsa('.review-card');
        buildStats(cards);
        buildTypeButtons(cards);
        buildVerdictButtons();
        bindHash();
        applyFromHash();
    }

    /* 统计条：N 篇评测 · M 篇推荐（xx%） */
    function buildStats(cards) {
        var el = document.querySelector('.review-stats');
        if (!el) return;
        var rec = cards.filter(function (c) {
            return c.getAttribute('data-verdict') === 'recommended';
        }).length;
        var pct = cards.length ? Math.round((rec / cards.length) * 100) : 0;
        el.textContent = '共 ' + cards.length + ' 篇评测 · ' + rec + ' 篇推荐（' + pct + '%）';
    }

    /* 类型按钮只列出实际有条目的类型，按预定义顺序排列 */
    function buildTypeButtons(cards) {
        var wrap = document.querySelector('[data-filter-group="type"]');
        if (!wrap) return;

        var present = [];
        cards.forEach(function (c) {
            var t = c.getAttribute('data-type');
            if (t && present.indexOf(t) === -1) present.push(t);
        });
        var order = Object.keys(TYPE_LABELS);
        present.sort(function (a, b) {
            return order.indexOf(a) - order.indexOf(b);
        });

        appendBtn(wrap, '全部', 'all', 'type');
        present.forEach(function (t) {
            var icon = TYPE_ICONS[t] ? TYPE_ICONS[t] + ' ' : '';
            appendBtn(wrap, icon + (TYPE_LABELS[t] || t), t, 'type');
        });
    }

    function buildVerdictButtons() {
        var wrap = document.querySelector('[data-filter-group="verdict"]');
        if (!wrap) return;
        appendBtn(wrap, '全部', 'all', 'verdict');
        appendBtn(wrap, VERDICT_LABELS.recommended, 'recommended', 'verdict');
        appendBtn(wrap, VERDICT_LABELS['not-recommended'], 'not-recommended', 'verdict');
    }

    function appendBtn(wrap, label, value, group) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'filter-btn' + (value === 'all' ? ' active' : '');
        b.textContent = label;
        b.setAttribute('data-value', value);
        b.addEventListener('click', function () {
            state[group] = value;
            wrap.querySelectorAll('.filter-btn').forEach(function (x) {
                x.classList.remove('active');
            });
            b.classList.add('active');
            applyFilter();
            writeHash();
        });
        wrap.appendChild(b);
    }

    function applyFilter() {
        var cards = qsa('.review-card');
        var shown = 0;
        cards.forEach(function (c) {
            var okType = state.type === 'all' || c.getAttribute('data-type') === state.type;
            var okVerdict = state.verdict === 'all' || c.getAttribute('data-verdict') === state.verdict;
            var show = okType && okVerdict;
            c.classList.toggle('hidden', !show);
            if (show) shown++;
        });
        var empty = document.querySelector('.review-empty');
        if (empty) {
            empty.style.display = shown ? 'none' : 'block';
        }
    }

    /* ---- URL hash 读写，便于分享筛选结果 ---- */
    function parseHash() {
        var h = window.location.hash.replace(/^#/, '');
        if (!h) return;
        h.split('&').forEach(function (kv) {
            var pair = kv.split('=');
            if (pair.length === 2 && (pair[0] === 'type' || pair[0] === 'verdict')) {
                state[pair[0]] = decodeURIComponent(pair[1]);
            }
        });
    }

    function applyFromHash() {
        parseHash();
        ['type', 'verdict'].forEach(function (group) {
            var wrap = document.querySelector('[data-filter-group="' + group + '"]');
            if (!wrap) return;
            wrap.querySelectorAll('.filter-btn').forEach(function (b) {
                var on = b.getAttribute('data-value') === state[group];
                b.classList.toggle('active', on);
            });
        });
        applyFilter();
    }

    function writeHash() {
        var parts = [];
        if (state.type !== 'all') parts.push('type=' + encodeURIComponent(state.type));
        if (state.verdict !== 'all') parts.push('verdict=' + encodeURIComponent(state.verdict));
        var h = parts.length ? '#' + parts.join('&') : '';
        if (h !== window.location.hash) {
            window.history.replaceState(null, '', window.location.pathname + window.location.search + h);
        }
    }

    function bindHash() {
        window.addEventListener('hashchange', applyFromHash);
    }

    if (document.body) {
        init();
    } else {
        document.addEventListener('DOMContentLoaded', init);
    }
})();
