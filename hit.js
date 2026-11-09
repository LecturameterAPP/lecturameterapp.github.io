/* Lecturameter web: contador propio y anonimo de visitas y clics (sin cookies, sin terceros).
 *
 * - Envia {t:"view"|"click", path, target?, lang?, ref?} al Worker de LM Intelligence (POST /web/hit).
 * - No guarda nada en el navegador (ni cookies ni localStorage). El servidor no guarda la IP.
 * - Si el navegador manda "No rastrear" (Do Not Track), no envia nada.
 * - Clics: target = data-track del enlace (o de un ancestro); si no, se deduce del href:
 *   play / appstore / lm99-play / lm99-appstore / blog / outbound:<host>. Otros enlaces internos no se cuentan.
 */
(function () {
    'use strict';
    var ENDPOINT = 'https://lecturameter-intelligence.appaugur.workers.dev/web/hit';

    try {
        if (navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.msDoNotTrack === '1') return;
    } catch (e) {}
    if (!/^https?:$/.test(location.protocol)) return;

    function send(payload) {
        try {
            var body = JSON.stringify(payload);
            // text/plain: peticion "simple" de CORS, sin preflight.
            if (navigator.sendBeacon && navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'text/plain;charset=UTF-8' }))) return;
            fetch(ENDPOINT, { method: 'POST', body: body, headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, keepalive: true, credentials: 'omit', mode: 'cors' }).catch(function () {});
        } catch (e) {}
    }

    function lang() { return document.documentElement.getAttribute('lang') || ''; }

    send({ t: 'view', path: location.pathname, lang: lang(), ref: document.referrer || '' });

    function targetFor(a) {
        var tracked = a.closest('[data-track]');
        if (tracked) return tracked.getAttribute('data-track');
        var u;
        try { u = new URL(a.href, location.href); } catch (e) { return ''; }
        if (u.protocol !== 'http:' && u.protocol !== 'https:') return '';
        var is99 = /1999|id6825334284|ySpHndhY/i.test(u.href);
        if (u.hostname === 'play.google.com') return is99 ? 'lm99-play' : 'play';
        if (u.hostname === 'apps.apple.com' || u.hostname === 'testflight.apple.com') return is99 ? 'lm99-appstore' : 'appstore';
        if (u.host === location.host) return /(^|\/)blog(\/|$)/.test(u.pathname) ? 'blog' : '';
        return 'outbound:' + u.hostname;
    }

    function onClick(ev) {
        var el = ev.target;
        if (!el || !el.closest) return;
        var a = el.closest('a[href]');
        if (!a) return;
        var target = targetFor(a);
        if (target) send({ t: 'click', path: location.pathname, target: target, lang: lang() });
    }
    document.addEventListener('click', onClick, true);
    document.addEventListener('auxclick', onClick, true);
})();
