/* Lecturameter web: consentimiento de cookies y almacenamiento no esencial.
 *
 * - Sin consentimiento NO se carga nada de terceros (StartupBar, EmailJS) ni se escribe su almacenamiento.
 * - La eleccion se guarda en localStorage["lm_consent"] = {v, ts, third_party}. Si sube CONSENT_VERSION se vuelve a preguntar.
 * - Las preferencias pedidas por el usuario (lm-theme, lm_lang, promo-dismissed) estan exentas y no pasan por aqui.
 * - Textos: claves js.consent_* del idioma (script#lm-i18n); si faltan, respaldo ES/EN integrado.
 * - Enlace "Preferencias de cookies": cualquier [data-lm-cookie-prefs]; si la pagina no lo tiene se anade al pie.
 */
(function () {
    'use strict';
    var KEY = 'lm_consent';
    var CONSENT_VERSION = 1;
    var STARTUPBAR_SRC = 'https://startupbar.co/widget/loader.js';
    var STARTUPBAR_ID = '95bfcbaf-c0bf-4c7b-bd09-b012c0b19d1e';

    var FALLBACK = {
        es: {
            title: 'Cookies y almacenamiento',
            body: 'Usamos un widget de terceros (StartupBar) que guarda datos en tu navegador y mide impresiones. Solo se carga si aceptas. Tu tema, tu idioma y el aviso cerrado se guardan sin pedirte nada, porque los has elegido tú.',
            accept: 'Aceptar',
            reject: 'Rechazar',
            policy: 'Política de cookies',
            prefs: 'Preferencias de cookies'
        },
        en: {
            title: 'Cookies and storage',
            body: 'We use a third-party widget (StartupBar) that stores data in your browser and counts impressions. It only loads if you accept. Your theme, language and dismissed notice are saved without asking, because you chose them.',
            accept: 'Accept',
            reject: 'Reject',
            policy: 'Cookie policy',
            prefs: 'Cookie preferences'
        }
    };

    var script = document.currentScript;
    var I18N = {};
    try { I18N = JSON.parse(document.getElementById('lm-i18n').textContent) || {}; } catch (e) {}
    var lang = ((document.documentElement.getAttribute('lang') || 'en').toLowerCase().split('-')[0]);
    var base = FALLBACK[lang] || FALLBACK.en;
    function t(k) { return I18N['consent_' + k] || base[k]; }

    // Sin data-policy (blog, paginas escritas a mano): la politica del idioma de la ruta (/xx/ o /xx-yy/), si no la inglesa.
    var seg = (location.pathname.split('/')[1] || '').toLowerCase();
    var policyUrl = (script && script.getAttribute('data-policy')) ||
        (seg !== 'en' && /^[a-z]{2}(-[a-z]{2})?$/.test(seg) ? '/' + seg + '/cookies/' : '/cookies/');

    function read() {
        try {
            var c = JSON.parse(localStorage.getItem(KEY));
            if (c && c.v === CONSENT_VERSION && typeof c.third_party === 'boolean') return c;
        } catch (e) {}
        return null;
    }
    function write(value) {
        try {
            localStorage.setItem(KEY, JSON.stringify({ v: CONSENT_VERSION, ts: new Date().toISOString(), third_party: value }));
        } catch (e) {}
    }

    var loaded = false;
    function loadThirdParty() {
        if (loaded) return;
        loaded = true;
        var s = document.createElement('script');
        s.async = true;
        s.src = STARTUPBAR_SRC;
        s.setAttribute('data-startup-id', STARTUPBAR_ID);
        document.head.appendChild(s);
        var deferred = document.querySelectorAll('script[type="text/plain"][data-lm-consent-src]');
        for (var i = 0; i < deferred.length; i++) {
            var d = document.createElement('script');
            d.src = deferred[i].getAttribute('data-lm-consent-src');
            d.defer = true;
            document.head.appendChild(d);
        }
    }

    var bar = null;
    var lastFocus = null;

    function css() {
        if (document.getElementById('lm-consent-css')) return;
        var st = document.createElement('style');
        st.id = 'lm-consent-css';
        st.textContent =
            '.lm-cb{position:fixed;inset-inline:12px;bottom:12px;z-index:2147483000;max-width:760px;margin-inline:auto;' +
            'background:var(--card,#fff);color:var(--text,#222);border:1px solid var(--line,#ccc);border-radius:14px;' +
            'box-shadow:0 10px 40px rgba(0,0,0,.35);padding:16px 18px;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}' +
            '.lm-cb h2{font-size:16px;margin:0 0 6px;color:var(--text-strong,inherit)}' +
            '.lm-cb p{margin:0 0 12px}' +
            '.lm-cb a{color:var(--accent-text,var(--accent,#41755A));text-decoration:underline}' +
            '.lm-cb-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}' +
            '.lm-cb-btn{flex:1 1 130px;min-width:130px;font:600 15px/1 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:12px 18px;' +
            'border-radius:999px;cursor:pointer;background:var(--accent,#41755A);color:var(--on-accent,#fff);border:2px solid var(--accent,#41755A)}' +
            '.lm-cb-btn:hover{filter:brightness(1.1)}' +
            '.lm-cb-btn:focus-visible,.lm-cb a:focus-visible{outline:3px solid var(--accent-text,#9AA5FF);outline-offset:2px}' +
            '.lm-cb-link{flex:1 1 100%;font-size:14px;margin-top:2px}' +
            '@media (min-width:560px){.lm-cb-link{flex:0 0 auto;margin-inline-start:auto;margin-top:0}}';
        document.head.appendChild(st);
    }

    function close() {
        if (bar && bar.parentNode) bar.parentNode.removeChild(bar);
        bar = null;
        if (lastFocus && lastFocus.focus) { try { lastFocus.focus(); } catch (e) {} }
        lastFocus = null;
    }

    function choose(accepted) {
        var prev = read();
        write(accepted);
        close();
        if (accepted) {
            loadThirdParty();
        } else if (loaded || (prev && prev.third_party)) {
            // retirada del consentimiento: borrar lo que dejo el widget y recargar sin el
            try { sessionStorage.removeItem('startupbar:sid'); } catch (e) {}
            location.reload();
        }
    }

    function show(fromPrefs) {
        if (bar) return;
        css();
        lastFocus = fromPrefs ? document.activeElement : null;
        bar = document.createElement('div');
        bar.className = 'lm-cb';
        bar.setAttribute('role', 'dialog');
        bar.setAttribute('aria-labelledby', 'lm-cb-title');
        var h = document.createElement('h2');
        h.id = 'lm-cb-title';
        h.textContent = t('title');
        var p = document.createElement('p');
        p.textContent = t('body');
        var row = document.createElement('div');
        row.className = 'lm-cb-row';
        var rej = document.createElement('button');
        rej.type = 'button'; rej.className = 'lm-cb-btn'; rej.textContent = t('reject');
        var acc = document.createElement('button');
        acc.type = 'button'; acc.className = 'lm-cb-btn'; acc.textContent = t('accept');
        var a = document.createElement('a');
        a.className = 'lm-cb-link'; a.href = policyUrl; a.textContent = t('policy');
        rej.addEventListener('click', function () { choose(false); });
        acc.addEventListener('click', function () { choose(true); });
        row.appendChild(rej); row.appendChild(acc); row.appendChild(a);
        bar.appendChild(h); bar.appendChild(p); bar.appendChild(row);
        bar.addEventListener('keydown', function (e) { if (e.key === 'Escape' && read()) close(); });
        document.body.appendChild(bar);
        if (fromPrefs) rej.focus();
    }

    function wirePrefs() {
        var links = document.querySelectorAll('[data-lm-cookie-prefs]');
        if (!links.length) {
            var host = document.querySelector('.footer-bottom') || document.querySelector('.footer') || document.querySelector('footer');
            if (host) {
                var a = document.createElement('a');
                a.href = '#';
                a.setAttribute('data-lm-cookie-prefs', '');
                a.textContent = t('prefs');
                host.appendChild(document.createTextNode(' '));
                host.appendChild(a);
                links = [a];
            }
        }
        for (var i = 0; i < links.length; i++) {
            links[i].addEventListener('click', function (e) { e.preventDefault(); show(true); });
        }
    }

    function init() {
        wirePrefs();
        var c = read();
        if (!c) show(false);
        else if (c.third_party) loadThirdParty();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
