/* Lecturameter web: contador propio y anonimo de visitas y clics (sin cookies, sin terceros).
 *
 * - Envia {t:"view"|"click", path, target?, lang?, ref?} al Worker de LM Intelligence (POST /web/hit).
 * - A los visitantes no se les guarda nada en el navegador (ni cookies ni localStorage); solo el propietario guarda una marca de exclusion (ver abajo). El servidor no guarda la IP.
 * - Si el navegador manda "No rastrear" (Do Not Track), no envia nada.
 * - Exclusion del propietario: abrir <web>/?lm_owner=1 deja una marca local (localStorage "lm_owner") en ESE navegador y
 *   desde entonces no se envia nada (ni visitas ni clics); <web>/?lm_owner=0 la quita. La marca la pone solo quien abre la URL,
 *   no identifica a nadie y nunca se envia al servidor.
 * - UTM: si la URL trae utm_source / utm_medium / utm_campaign (convencion: landing_utm.md en Recursos LM/mockups/tanda_1211/landing/), se envian junto a la
 *   visita y a los clics de esa misma pagina como utm:{s,m,c}. No se guardan en el navegador.
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

    // Exclusion del propietario (ver cabecera).
    try {
        var qs = new URLSearchParams(location.search);
        if (qs.get('lm_owner') === '1') localStorage.setItem('lm_owner', '1');
        else if (qs.get('lm_owner') === '0') localStorage.removeItem('lm_owner');
        if (localStorage.getItem('lm_owner') === '1') return;
    } catch (e) {}

    // UTM de la pagina actual (solo en memoria).
    var utm = null;
    try {
        var q = new URLSearchParams(location.search);
        var clean = function (v) { return (v || '').toLowerCase().replace(/[^a-z0-9_.-]/g, '').slice(0, 40); };
        var us = clean(q.get('utm_source')), um = clean(q.get('utm_medium')), uc = clean(q.get('utm_campaign'));
        if (us || um || uc) utm = { s: us, m: um, c: uc };
    } catch (e) {}

    function send(payload) {
        try {
            var body = JSON.stringify(payload);
            // text/plain: peticion "simple" de CORS, sin preflight.
            if (navigator.sendBeacon && navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'text/plain;charset=UTF-8' }))) return;
            fetch(ENDPOINT, { method: 'POST', body: body, headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, keepalive: true, credentials: 'omit', mode: 'cors' }).catch(function () {});
        } catch (e) {}
    }

    function lang() { return document.documentElement.getAttribute('lang') || ''; }

    var view = { t: 'view', path: location.pathname, lang: lang(), ref: document.referrer || '' };
    if (utm) view.utm = utm;
    send(view);

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
        if (target) {
            var click = { t: 'click', path: location.pathname, target: target, lang: lang() };
            if (utm) click.utm = utm;
            send(click);
        }
    }
    document.addEventListener('click', onClick, true);
    document.addEventListener('auxclick', onClick, true);
})();
