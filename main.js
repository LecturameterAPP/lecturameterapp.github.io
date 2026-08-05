/* ═══ LECTURAMETER WEB 3.0 ═══ */
(function () {
    // ─── SCROLL-SPY ───
    var pills = document.querySelectorAll('.nav-pills a[href^="#"]');
    var sections = [];
    pills.forEach(function (a) {
        var id = a.getAttribute('href').slice(1);
        var el = document.getElementById(id);
        if (el) sections.push({ el: el, link: a });
    });

    if (sections.length && 'IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    pills.forEach(function (p) { p.classList.remove('active'); });
                    var match = sections.find(function (s) { return s.el === e.target; });
                    if (match) match.link.classList.add('active');
                }
            });
        }, { rootMargin: '-20% 0px -60% 0px' });
        sections.forEach(function (s) { observer.observe(s.el); });
    }

    // ─── HAMBURGER ───
    var hamburger = document.querySelector('.nav-hamburger');
    var navPills = document.querySelector('.nav-pills');
    if (hamburger && navPills) {
        hamburger.addEventListener('click', function () {
            navPills.classList.toggle('open');
        });
        navPills.addEventListener('click', function (e) {
            if (e.target.tagName === 'A') navPills.classList.remove('open');
        });
    }

    // ─── THEME TOGGLE ───
    var themeBtn = document.querySelector('.nav-theme-btn');
    if (themeBtn) {
        var saved = localStorage.getItem('lm-theme');
        if (saved) document.documentElement.setAttribute('data-theme', saved);

        function getIsDark() {
            var current = document.documentElement.getAttribute('data-theme');
            if (current) return current === 'dark';
            return window.matchMedia('(prefers-color-scheme: dark)').matches;
        }

        function updateIcon() {
            themeBtn.textContent = getIsDark() ? '☾' : '☀';
        }

        themeBtn.addEventListener('click', function () {
            var next = getIsDark() ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('lm-theme', next);
            updateIcon();
        });

        updateIcon();
    }

    // ─── FAQ ACCORDION ───
    document.querySelectorAll('.faq-q').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var item = btn.closest('.faq-item');
            var answer = item.querySelector('.faq-a');
            var isOpen = item.classList.contains('open');

            document.querySelectorAll('.faq-item.open').forEach(function (other) {
                other.classList.remove('open');
                other.querySelector('.faq-a').style.maxHeight = '0';
            });

            if (!isOpen) {
                item.classList.add('open');
                answer.style.maxHeight = answer.scrollHeight + 'px';
            }
        });
    });

    // ─── LIGHTBOX ───
    var overlay = document.getElementById('lightbox');
    if (overlay) {
        var lbxImg = overlay.querySelector('.lbx-img');
        var lbxClose = overlay.querySelector('.lbx-close');

        document.querySelectorAll('[data-lbx]').forEach(function (el) {
            el.style.cursor = 'zoom-in';
            el.addEventListener('click', function () {
                lbxImg.src = el.getAttribute('data-lbx') || el.src;
                overlay.classList.add('open');
            });
        });

        function closeLbx() { overlay.classList.remove('open'); }
        if (lbxClose) lbxClose.addEventListener('click', closeLbx);
        overlay.addEventListener('click', function (e) { if (e.target === overlay) closeLbx(); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeLbx(); });
    }
})();
