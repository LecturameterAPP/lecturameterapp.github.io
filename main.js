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

        // Swap screenshots for current theme. Two strategies:
        //  - imgs with data-src-dark: switch src/data-lbx between stored light and dark variants.
        //  - otherwise: replace _claro_ <-> _oscuro_ token in path.
        // Theme gallery is always skipped (each figure shows a specific theme).
        function swapCapturesForTheme() {
            var dark = getIsDark();
            document.querySelectorAll('img[src*="capturas%20para%20v3/"], img[src*="capturas para v3/"]').forEach(function (img) {
                if (img.closest('.themes-gallery')) return;
                var explicitDark = img.getAttribute('data-src-dark');
                if (explicitDark) {
                    if (!img.dataset.srcLight) img.dataset.srcLight = img.getAttribute('src');
                    var target = dark ? explicitDark : img.dataset.srcLight;
                    img.setAttribute('src', target);
                    if (img.hasAttribute('data-lbx')) img.setAttribute('data-lbx', target);
                    return;
                }
                var from = dark ? '_claro_' : '_oscuro_';
                var to   = dark ? '_oscuro_' : '_claro_';
                ['src', 'data-lbx'].forEach(function (attr) {
                    var v = img.getAttribute(attr);
                    if (v && v.indexOf(from) !== -1) img.setAttribute(attr, v.split(from).join(to));
                });
            });
        }

        themeBtn.addEventListener('click', function () {
            var next = getIsDark() ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('lm-theme', next);
            updateIcon();
            swapCapturesForTheme();
            if (typeof window.__lmUpdateTimerVideo === 'function') window.__lmUpdateTimerVideo();
        });

        updateIcon();
        swapCapturesForTheme();
    }

    // ─── TIMER VIDEO (normal / immersive × light / dark × es / en) ───
    var timerShot = document.querySelector('.timer-shot');
    if (timerShot) {
        var timerVideo = timerShot.querySelector('video');
        var soundBtn = timerShot.querySelector('.sound-btn');
        var modeButtons = timerShot.querySelectorAll('.mode-toggle button');

        function currentTheme() {
            var attr = document.documentElement.getAttribute('data-theme');
            if (attr) return attr;
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }

        function currentMode() {
            return timerShot.getAttribute('data-mode') || 'normal';
        }

        function updateTimerVideo(forcePlay) {
            var lang = timerVideo.getAttribute('data-lang');
            var theme = currentTheme();
            var mode = currentMode();
            var src = '/timer_video_' + lang + '_' + theme + '_' + mode + '.mp4';
            var currentSrc = timerVideo.currentSrc || timerVideo.src;
            if (currentSrc.indexOf(src) === -1) {
                timerVideo.src = src;
                timerVideo.load();
            }
            if (mode === 'normal') {
                timerVideo.muted = true;
                soundBtn.classList.add('muted');
            }
            if (forcePlay) {
                var playAttempt = timerVideo.play();
                if (playAttempt && playAttempt.catch) playAttempt.catch(function () {});
            }
        }

        modeButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                modeButtons.forEach(function (b) { b.classList.remove('active'); });
                btn.classList.add('active');
                timerShot.setAttribute('data-mode', btn.getAttribute('data-mode'));
                updateTimerVideo(true);
            });
        });

        soundBtn.addEventListener('click', function () {
            timerVideo.muted = !timerVideo.muted;
            soundBtn.classList.toggle('muted', timerVideo.muted);
            if (!timerVideo.muted) {
                var p = timerVideo.play();
                if (p && p.catch) p.catch(function () {});
            }
        });

        // React to system theme changes when user hasn't forced one
        var mq = window.matchMedia('(prefers-color-scheme: dark)');
        if (mq.addEventListener) mq.addEventListener('change', function () { updateTimerVideo(false); });
        else if (mq.addListener) mq.addListener(function () { updateTimerVideo(false); });

        // Expose an updater for the theme toggle handler below
        window.__lmUpdateTimerVideo = function () { updateTimerVideo(false); };

        updateTimerVideo(false);
    }

    // ─── PAGI STAR CLICK (Universo Lector) ───
    var pagiStar = document.querySelector('.roadmap-item.universo .pagi-star');
    if (pagiStar) {
        pagiStar.style.cursor = 'pointer';
        var neutralHTML = pagiStar.innerHTML;
        var pagiState = 'neutral';
        var pagiCache = {};
        var pagiTimer = null;

        function fetchPagi(name) {
            if (pagiCache[name]) return Promise.resolve(pagiCache[name]);
            return fetch('../pagi/star-' + name + '.svg').then(function (r) { return r.text(); }).then(function (t) {
                pagiCache[name] = t;
                return t;
            });
        }

        function setPagi(name) {
            pagiState = name;
            if (name === 'neutral') {
                pagiStar.innerHTML = neutralHTML;
                return;
            }
            fetchPagi(name).then(function (svg) {
                if (pagiState === name) pagiStar.innerHTML = svg;
            });
        }

        var pendingStarClick = null;
        var STAR_DBL_MS = 350;
        var pagiCard = pagiStar.closest('.roadmap-item');
        var pagiCardP = pagiCard && pagiCard.querySelector('p');
        var pagiCardPOriginal = pagiCardP ? pagiCardP.innerHTML : null;
        var lang = (document.documentElement.lang || 'es').slice(0, 2);
        var HAPPY = lang === 'en'
            ? ['Pagi applauds you!', 'Shine, little star!', 'Shhh, I\'m reading.', 'Pagi is watching…']
            : ['¡Pagi te aplaude!', '¡Brilla, estrellita!', 'Shhh, estoy leyendo.', 'Pagi te observa…'];
        var ANGRY = lang === 'en'
            ? ['Ouch! That hurt!', 'Enough clicks!', 'Grr, leave me alone.', 'Not funny anymore.']
            : ['¡Ay! ¡Eso ha dolido!', '¡Basta ya de clicks!', 'Grr, déjame en paz.', 'Ya no tiene gracia.'];
        function pickRandom(arr, prev) {
            var pool = arr.filter(function (x) { return x !== prev; });
            return pool[Math.floor(Math.random() * pool.length)];
        }
        var lastPhrase = null;
        function setCardPhrase(arr) {
            if (!pagiCardP) return;
            var phrase = pickRandom(arr, lastPhrase);
            lastPhrase = phrase;
            pagiCardP.textContent = phrase;
        }
        function restoreCardPhrase() {
            if (pagiCardP && pagiCardPOriginal !== null) {
                pagiCardP.innerHTML = pagiCardPOriginal;
                lastPhrase = null;
            }
        }

        function burstSparks(angry) {
            var n = angry ? 8 : 6;
            for (var i = 0; i < n; i++) {
                var s = document.createElement('span');
                s.className = 'pagi-spark' + (angry ? ' angry' : '');
                var ang = (Math.PI * 2 * i) / n + (Math.random() - 0.5) * 0.4;
                var dist = 40 + Math.random() * 30;
                s.style.setProperty('--dx', (Math.cos(ang) * dist).toFixed(1) + 'px');
                s.style.setProperty('--dy', (Math.sin(ang) * dist).toFixed(1) + 'px');
                s.style.width = s.style.height = (5 + Math.random() * 5).toFixed(0) + 'px';
                pagiStar.appendChild(s);
                setTimeout(function (el) { return function () { el.remove(); }; }(s), 800);
            }
        }
        var origSetPagi = setPagi;
        setPagi = function (name) {
            if (name === 'neutral') restoreCardPhrase();
            else if (name === 'celebrando') { setCardPhrase(HAPPY); burstSparks(false); }
            else if (name === 'enfadado') { setCardPhrase(ANGRY); burstSparks(true); pagiStar.classList.add('pagi-spin-once'); setTimeout(function(){pagiStar.classList.remove('pagi-spin-once');}, 700); }
            origSetPagi(name);
        };

        // Expose safe setter for shared idle handler (only touches state when currently neutral, or when reverting to neutral)
        window.__lmStarSetState = function (target) {
            if (target === 'sorprendido' && pagiState === 'neutral') { setPagi('sorprendido'); }
            else if (target === 'neutral' && pagiState === 'sorprendido') { setPagi('neutral'); }
        };

        pagiStar.addEventListener('click', function () {
            if (pendingStarClick) {
                clearTimeout(pendingStarClick);
                pendingStarClick = null;
                if (pagiTimer) clearTimeout(pagiTimer);
                setPagi('enfadado');
                pagiTimer = setTimeout(function () { setPagi('neutral'); }, 3500);
                return;
            }
            pendingStarClick = setTimeout(function () {
                pendingStarClick = null;
                if (pagiTimer) clearTimeout(pagiTimer);
                setPagi('celebrando');
                pagiTimer = setTimeout(function () { setPagi('neutral'); }, 3000);
            }, STAR_DBL_MS);
        });
    }

    // ─── PAGI FAQ CLICK (dark, pensativo → celebrando → enfadado) ───
    var pagiFaq = document.querySelector('.pagi-faq');
    if (pagiFaq) {
        var faqCache = {};
        var faqState = null;
        var faqTimer = null;

        function fetchFaqPagi(name) {
            if (faqCache[name]) return Promise.resolve(faqCache[name]);
            return fetch('../pagi/dark-' + name + '.svg').then(function (r) { return r.text(); }).then(function (t) {
                faqCache[name] = t;
                return t;
            });
        }

        function setFaqPagi(name) {
            faqState = name;
            fetchFaqPagi(name).then(function (svg) {
                if (faqState === name) pagiFaq.innerHTML = svg;
            });
        }

        setFaqPagi('pensativo');

        var pendingClick = null;
        var DBL_MS = 350;

        pagiFaq.addEventListener('click', function () {
            if (pendingClick) {
                clearTimeout(pendingClick);
                pendingClick = null;
                if (faqTimer) clearTimeout(faqTimer);
                setFaqPagi('enfadado');
                faqTimer = setTimeout(function () { setFaqPagi('pensativo'); }, 3500);
                return;
            }
            pendingClick = setTimeout(function () {
                pendingClick = null;
                if (faqTimer) clearTimeout(faqTimer);
                setFaqPagi('celebrando');
                faqTimer = setTimeout(function () { setFaqPagi('pensativo'); }, 3000);
            }, DBL_MS);
        });
        pagiFaq.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pagiFaq.click(); }
        });
    }

    // ─── PAGI HERO EYE TRACKING (re-queries per frame so it survives SVG swaps) ───
    (function () {
        if (!window.matchMedia('(pointer: fine)').matches) return;
        var heroContainer = document.querySelector('.pagi-hero');
        if (!heroContainer) return;
        var HERO_MAX_X = 14, HERO_MAX_Y = 18;
        var heroRaf = false, heroLX = 0, heroLY = 0;
        function updateHeroPupil() {
            heroRaf = false;
            var pupil = heroContainer.querySelector('.pg-pupil');
            if (!pupil) return;
            var svg = pupil.ownerSVGElement;
            if (!svg) return;
            var r = svg.getBoundingClientRect();
            if (!r.width) return;
            var cx = r.left + r.width * 0.42;
            var cy = r.top + r.height * 0.38;
            var dx = heroLX - cx, dy = heroLY - cy;
            var dist = Math.hypot(dx, dy) || 1;
            var norm = Math.min(1, dist / 400);
            var tx = (dx / dist) * HERO_MAX_X * norm;
            var ty = (dy / dist) * HERO_MAX_Y * norm;
            pupil.setAttribute('transform', 'translate(' + tx.toFixed(1) + ' ' + ty.toFixed(1) + ')');
        }
        window.addEventListener('mousemove', function (e) {
            heroLX = e.clientX; heroLY = e.clientY;
            if (!heroRaf) { heroRaf = true; requestAnimationFrame(updateHeroPupil); }
        }, { passive: true });
    })();

    // ─── SHARED IDLE HANDLER (15s idle → all Pagis to their "surprised/confused" state) ───
    (function () {
        var IDLE_MS = 8000;
        var MOUSE_THRESHOLD = 6; // ignore <6px mouse jitter so a still hand doesn't reset the timer
        var idleTimer = null;
        var isIdle = false;
        var handlers = [];
        var lastX = null, lastY = null;
        function trigger() { isIdle = true; handlers.forEach(function (h) { try { h.onIdle(); } catch (e) {} }); }
        function reset() {
            if (isIdle) { isIdle = false; handlers.forEach(function (h) { try { h.onActive(); } catch (e) {} }); }
            clearTimeout(idleTimer);
            idleTimer = setTimeout(trigger, IDLE_MS);
        }
        function onMouseMove(e) {
            if (lastX !== null && Math.abs(e.clientX - lastX) < MOUSE_THRESHOLD && Math.abs(e.clientY - lastY) < MOUSE_THRESHOLD) return;
            lastX = e.clientX; lastY = e.clientY;
            reset();
        }
        window.addEventListener('mousemove', onMouseMove, { passive: true });
        ['scroll', 'keydown', 'touchstart', 'click'].forEach(function (ev) {
            window.addEventListener(ev, reset, { passive: true });
        });

        // Hero → hero-sorprendido on idle, restore original on activity
        var heroContainer = document.querySelector('.pagi-hero');
        if (heroContainer) {
            var heroOriginalHTML = heroContainer.innerHTML;
            var heroSorprSvg = null;
            handlers.push({
                onIdle: function () {
                    if (heroSorprSvg) { heroContainer.innerHTML = heroSorprSvg; return; }
                    fetch('../pagi/hero-sorprendido.svg').then(function (r) { return r.text(); }).then(function (t) {
                        heroSorprSvg = t;
                        if (isIdle) heroContainer.innerHTML = t;
                    });
                },
                onActive: function () { heroContainer.innerHTML = heroOriginalHTML; }
            });
        }
        // Star → sorprendido on idle (setter is registered later in this file; look up dynamically)
        handlers.push({
            onIdle: function () { if (window.__lmStarSetState) window.__lmStarSetState('sorprendido'); },
            onActive: function () { if (window.__lmStarSetState) window.__lmStarSetState('neutral'); }
        });
        // Lago → confuso on idle
        handlers.push({
            onIdle: function () { if (window.__lmLagoSetState) window.__lmLagoSetState('confuso'); },
            onActive: function () { if (window.__lmLagoSetState) window.__lmLagoSetState('neutro'); }
        });
        reset();
    })();

    // ─── THEME PILLS (temas section: change Pagi mascot color) ───
    (function () {
        var pills = document.querySelectorAll('.theme-pills .theme-pill');
        var mascot = document.querySelector('.pagi-mascot');
        if (!pills.length || !mascot) return;
        pills.forEach(function (pill) {
            pill.addEventListener('click', function () {
                var color = pill.getAttribute('data-color');
                mascot.style.setProperty('--pagi-color', color);
                pills.forEach(function (p) { p.classList.remove('active'); p.setAttribute('aria-selected', 'false'); p.style.removeProperty('--pill-color'); });
                pill.classList.add('active');
                pill.setAttribute('aria-selected', 'true');
                pill.style.setProperty('--pill-color', color);
            });
        });
    })();

    // ─── PAGI FAQ EYE TRACKING (only in pensativo state) ───
    (function () {
        if (!window.matchMedia('(pointer: fine)').matches) return;
        var faqContainer = document.querySelector('.pagi-faq');
        if (!faqContainer) return;
        var FAQ_MAX_X = 12, FAQ_MAX_Y = 15;
        var faqRaf = false, faqLX = 0, faqLY = 0;
        function updateFaqPupil() {
            faqRaf = false;
            var pupil = faqContainer.querySelector('.pg-pupil-faq');
            if (!pupil) return;
            var svg = pupil.ownerSVGElement;
            if (!svg) return;
            var r = svg.getBoundingClientRect();
            if (!r.width) return;
            var cx = r.left + r.width * 0.5;
            var cy = r.top + r.height * 0.4;
            var dx = faqLX - cx, dy = faqLY - cy;
            var dist = Math.hypot(dx, dy) || 1;
            var norm = Math.min(1, dist / 400);
            var tx = (dx / dist) * FAQ_MAX_X * norm;
            var ty = (dy / dist) * FAQ_MAX_Y * norm;
            pupil.setAttribute('transform', 'translate(' + tx.toFixed(1) + ' ' + ty.toFixed(1) + ')');
        }
        window.addEventListener('mousemove', function (e) {
            faqLX = e.clientX; faqLY = e.clientY;
            if (!faqRaf) { faqRaf = true; requestAnimationFrame(updateFaqPupil); }
        }, { passive: true });
    })();

    // ─── PAGI LAGO (iOS section) ───
    var pagiLago = document.querySelector('.pagi-lago');
    if (pagiLago) {
        var lagoCache = {};
        var lagoState = null;
        var lagoTimer = null;
        var lagoLang = (document.documentElement.lang || 'es').slice(0, 2);
        var LAGO_HAPPY = lagoLang === 'en'
            ? ['iOS coming soon!', 'More readers to meet!', 'Get your AirPods ready!', 'See you on the App Store.']
            : ['¡iOS pronto!', '¡Voy a conocer más lectores!', '¡Preparad los AirPods!', 'Nos vemos en el App Store.'];
        var LAGO_ANGRY = lagoLang === 'en'
            ? ['You are not taking me there…', 'I prefer Android.', 'I refuse to jump the fence.', 'Do NOT put me in a box.']
            : ['¿A que no me llevas?', 'Prefiero Android.', 'No pienso saltar la manzana.', 'Ni se te ocurra meterme ahí.'];

        function fetchLago(name) {
            if (lagoCache[name]) return Promise.resolve(lagoCache[name]);
            return fetch('../pagi/lago-' + name + '.svg').then(function (r) { return r.text(); }).then(function (t) {
                lagoCache[name] = t;
                return t;
            });
        }
        function setLago(name) {
            lagoState = name;
            fetchLago(name).then(function (svg) { if (lagoState === name) pagiLago.innerHTML = svg; });
        }
        function pickLagoPhrase(arr, prev) {
            var pool = arr.filter(function (x) { return x !== prev; });
            return pool[Math.floor(Math.random() * pool.length)];
        }
        var lagoStatus = document.querySelector('#ios .ios-status');
        var lagoLastPhrase = null;
        function flashLagoPhrase(arr, cls) {
            if (!lagoStatus) return;
            var p = pickLagoPhrase(arr, lagoLastPhrase);
            lagoLastPhrase = p;
            lagoStatus.textContent = p;
            lagoStatus.className = 'ios-status ' + cls;
            clearTimeout(flashLagoPhrase._t);
            flashLagoPhrase._t = setTimeout(function () {
                if (lagoStatus.textContent === p) { lagoStatus.textContent = ''; lagoStatus.className = 'ios-status'; }
            }, 3200);
        }

        setLago('neutro');

        var pendingLagoClick = null;
        var LAGO_DBL_MS = 350;
        pagiLago.addEventListener('click', function () {
            if (pendingLagoClick) {
                clearTimeout(pendingLagoClick);
                pendingLagoClick = null;
                if (lagoTimer) clearTimeout(lagoTimer);
                setLago('enfadado');
                flashLagoPhrase(LAGO_ANGRY, 'err');
                lagoTimer = setTimeout(function () { setLago('neutro'); }, 3500);
                return;
            }
            pendingLagoClick = setTimeout(function () {
                pendingLagoClick = null;
                if (lagoTimer) clearTimeout(lagoTimer);
                setLago('feliz');
                flashLagoPhrase(LAGO_HAPPY, 'ok');
                lagoTimer = setTimeout(function () { setLago('neutro'); }, 3000);
            }, LAGO_DBL_MS);
        });
        pagiLago.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pagiLago.click(); }
        });

        // Expose safe setter for shared idle handler
        window.__lmLagoSetState = function (target) {
            if (target === 'confuso' && lagoState === 'neutro') { if (lagoTimer) clearTimeout(lagoTimer); setLago('confuso'); }
            else if (target === 'neutro' && lagoState === 'confuso') { if (lagoTimer) clearTimeout(lagoTimer); setLago('neutro'); }
        };

        // Eye tracking on lago (only in neutro state, only pointer:fine)
        if (window.matchMedia('(pointer: fine)').matches) {
            var LAGO_MAX_X = 18, LAGO_MAX_Y = 20;
            var lagoRaf = false, lagoLX = 0, lagoLY = 0;
            function updateLagoPupil() {
                lagoRaf = false;
                var pupil = pagiLago.querySelector('.pg-pupil-lago');
                if (!pupil) return;
                var svg = pupil.ownerSVGElement;
                if (!svg) return;
                var r = svg.getBoundingClientRect();
                if (!r.width) return;
                var cx = r.left + r.width * 0.5;
                var cy = r.top + r.height * 0.5;
                var dx = lagoLX - cx, dy = lagoLY - cy;
                var dist = Math.hypot(dx, dy) || 1;
                var norm = Math.min(1, dist / 400);
                var tx = (dx / dist) * LAGO_MAX_X * norm;
                var ty = (dy / dist) * LAGO_MAX_Y * norm;
                pupil.setAttribute('transform', 'translate(' + tx.toFixed(1) + ' ' + ty.toFixed(1) + ')');
            }
            window.addEventListener('mousemove', function (e) {
                lagoLX = e.clientX; lagoLY = e.clientY;
                if (!lagoRaf) { lagoRaf = true; requestAnimationFrame(updateLagoPupil); }
            }, { passive: true });
        }
    }

    // ─── SUBPAGE LANGUAGE TOGGLE (setLang — global for privacy/contact/precios) ───
    window.setLang = function (lang) {
        if (lang !== 'es' && lang !== 'en') lang = 'es';
        document.documentElement.lang = lang;
        document.querySelectorAll('.lang-content').forEach(function (el) {
            el.classList.toggle('active', el.id === 'content-' + lang);
        });
        document.querySelectorAll('.lang-bar button').forEach(function (btn) {
            btn.classList.toggle('active', btn.id === 'btn-' + lang);
        });
        document.querySelectorAll('[data-es][data-en]').forEach(function (el) {
            var txt = el.getAttribute('data-' + lang);
            if (txt != null) el.textContent = txt;
        });
        document.querySelectorAll('[data-href-es][data-href-en]').forEach(function (el) {
            var href = el.getAttribute('data-href-' + lang);
            if (href != null) el.setAttribute('href', href);
        });
        try { localStorage.setItem('lm_lang', lang); } catch (e) {}
    };
    (function () {
        if (!document.querySelector('.lang-content')) return;
        var saved = null;
        try { saved = localStorage.getItem('lm_lang'); } catch (e) {}
        var urlLang = null;
        try { urlLang = new URLSearchParams(location.search).get('lang'); } catch (e) {}
        // Default EN; ES only if explicitly requested via URL or saved preference.
        var lang = urlLang || saved || 'en';
        window.setLang(lang);
    })();

    // ─── CONTACT FORM sendFeedback (mailto — global for contact.html) ───
    window.sendFeedback = function (lang) {
        var nameEl = document.getElementById('fbName-' + lang);
        var msgEl = document.getElementById('fbMsg-' + lang);
        var capQEl = document.getElementById('captchaQuestionFb-' + lang);
        var capIEl = document.getElementById('captchaInputFb-' + lang);
        var status = document.getElementById('fbStatus-' + lang);
        if (!msgEl || !capIEl || !capQEl) return;
        var name = (nameEl && nameEl.value || '').trim();
        var msg = (msgEl.value || '').trim();
        var capMatch = (capQEl.textContent || '').match(/(\d+)\s*\+\s*(\d+)/);
        var expected = capMatch ? (parseInt(capMatch[1], 10) + parseInt(capMatch[2], 10)) : null;
        var given = parseInt((capIEl.value || '').trim(), 10);
        var setStatus = function (txt, ok) { if (status) { status.textContent = txt; status.style.color = ok ? '#41755A' : '#d9534f'; } };
        if (!msg) { setStatus(lang === 'en' ? 'Please write a message.' : 'Escribe un mensaje.', false); return; }
        if (expected !== null && given !== expected) { setStatus(lang === 'en' ? 'Captcha wrong, try again.' : 'Captcha incorrecto, prueba otra vez.', false); return; }
        var subject = lang === 'en' ? 'Feedback from web' : 'Mensaje desde la web';
        var body = (name ? 'Name: ' + name + '\n\n' : '') + msg + '\n\n(Sent from lecturameterapp.github.io)';
        window.location.href = 'mailto:lecturameter.app@gmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
        setStatus(lang === 'en' ? 'Opening your email app… if nothing happens, write directly to lecturameter.app@gmail.com.' : 'Abriendo tu cliente de email… si no pasa nada, escríbenos directamente a lecturameter.app@gmail.com.', true);
    };

    // ─── iOS WAITLIST (mailto MVP + captcha) ───
    (function () {
        var q = document.querySelector('.ios-captcha-question');
        if (q) {
            var a = 1 + Math.floor(Math.random() * 8);
            var b = 1 + Math.floor(Math.random() * 8);
            q.textContent = a + ' + ' + b + ' = ?';
            q.dataset.expected = String(a + b);
        }
    })();
    window.submitIosWaitlist = function (e, lang) {
        e.preventDefault();
        var form = e.target;
        var email = (form.email.value || '').trim();
        var name = (form.name.value || '').trim();
        var status = form.querySelector('.ios-status');
        var capQ = form.querySelector('.ios-captcha-question');
        var capI = form.querySelector('.ios-captcha-input');
        function fail(msg) { if (status) { status.textContent = msg; status.className = 'ios-status err'; } return false; }
        if (!email || email.indexOf('@') < 1) return fail(lang === 'en' ? 'Please enter a valid email.' : 'Introduce un email válido.');
        if (capQ && capI) {
            var expected = parseInt(capQ.dataset.expected || '-1', 10);
            var given = parseInt((capI.value || '').trim(), 10);
            if (isNaN(given) || given !== expected) return fail(lang === 'en' ? 'Captcha wrong, try again.' : 'Captcha incorrecto, prueba otra vez.');
        }
        var subject = 'iOS waitlist';
        var body = 'Email: ' + email + '\n' + (name ? 'Name: ' + name + '\n' : '') + '\n(Sent from lecturameterapp.github.io)';
        window.location.href = 'mailto:lecturameter.app@gmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
        if (status) {
            status.textContent = lang === 'en'
                ? 'Opening your email app… if nothing happens, write directly to lecturameter.app@gmail.com.'
                : 'Abriendo tu cliente de email… si no pasa nada, escríbenos directamente a lecturameter.app@gmail.com.';
            status.className = 'ios-status ok';
        }
        return false;
    };

    // ─── PAGI STAR EYE TRACKING (only while in neutral state) ───
    (function () {
        if (!window.matchMedia('(pointer: fine)').matches) return;
        var starContainer = document.querySelector('.roadmap-item.universo .pagi-star');
        if (!starContainer) return;
        // Star: pupil r=18 inside eye rx=32/ry=36 → safe room 14×18 SVG units.
        var STAR_MAX_X = 12, STAR_MAX_Y = 15;
        var starRafPending = false, starLastX = 0, starLastY = 0;
        function updateStar() {
            starRafPending = false;
            var pupil = starContainer.querySelector('.pg-pupil-star');
            if (!pupil) return; // state swapped out of neutral, tracker idles
            var svg = pupil.ownerSVGElement;
            if (!svg) return;
            var r = svg.getBoundingClientRect();
            if (!r.width) return;
            var cx = r.left + r.width * 0.46;
            var cy = r.top + r.height * 0.50;
            var dx = starLastX - cx, dy = starLastY - cy;
            var dist = Math.hypot(dx, dy) || 1;
            var norm = Math.min(1, dist / 400);
            var tx = (dx / dist) * STAR_MAX_X * norm;
            var ty = (dy / dist) * STAR_MAX_Y * norm;
            pupil.setAttribute('transform', 'translate(' + tx.toFixed(1) + ' ' + ty.toFixed(1) + ')');
        }
        window.addEventListener('mousemove', function (e) {
            starLastX = e.clientX; starLastY = e.clientY;
            if (!starRafPending) { starRafPending = true; requestAnimationFrame(updateStar); }
        }, { passive: true });
    })();

    // ─── REVEAL ON SCROLL ───
    var revealSelectors = '.reveal-up, .section-head, .theme-card, .pricing-card, .roadmap-item, .whatsnew-col';
    var revealEls = document.querySelectorAll(revealSelectors);
    if (revealEls.length && 'IntersectionObserver' in window) {
        var revealObs = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    e.target.classList.add('in-view');
                    revealObs.unobserve(e.target);
                }
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });
        revealEls.forEach(function (el) {
            if (!el.classList.contains('in-view')) revealObs.observe(el);
        });
    } else {
        revealEls.forEach(function (el) { el.classList.add('in-view'); });
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
        var lbxPrev = overlay.querySelector('.lbx-prev');
        var lbxNext = overlay.querySelector('.lbx-next');
        var currentGroup = [];
        var currentIndex = -1;

        function srcOf(el) { return el.getAttribute('data-lbx') || el.getAttribute('src'); }

        function openLbxFrom(el) {
            var container = el.closest('.themes-gallery');
            currentGroup = container
                ? Array.prototype.slice.call(container.querySelectorAll('[data-lbx]'))
                : [el];
            currentIndex = currentGroup.indexOf(el);
            if (currentIndex < 0) currentIndex = 0;
            var multi = currentGroup.length > 1;
            overlay.classList.toggle('has-nav', multi);
            lbxImg.src = srcOf(currentGroup[currentIndex]);
            overlay.classList.add('open');
        }

        function nav(delta) {
            if (!currentGroup.length) return;
            currentIndex = (currentIndex + delta + currentGroup.length) % currentGroup.length;
            lbxImg.src = srcOf(currentGroup[currentIndex]);
        }

        document.querySelectorAll('[data-lbx]').forEach(function (el) {
            el.style.cursor = 'zoom-in';
            el.addEventListener('click', function () { openLbxFrom(el); });
        });

        function closeLbx() { overlay.classList.remove('open'); overlay.classList.remove('has-nav'); }
        if (lbxClose) lbxClose.addEventListener('click', function (e) { e.stopPropagation(); closeLbx(); });
        if (lbxPrev) lbxPrev.addEventListener('click', function (e) { e.stopPropagation(); nav(-1); });
        if (lbxNext) lbxNext.addEventListener('click', function (e) { e.stopPropagation(); nav(1); });
        overlay.addEventListener('click', function (e) { if (e.target === overlay) closeLbx(); });
        document.addEventListener('keydown', function (e) {
            if (!overlay.classList.contains('open')) return;
            if (e.key === 'Escape') closeLbx();
            else if (e.key === 'ArrowLeft') nav(-1);
            else if (e.key === 'ArrowRight') nav(1);
        });
    }
})();
