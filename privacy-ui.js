/* Politica de privacidad: agrupa cada seccion numerada en una tarjeta y anade un indice.
   Solo reorganiza elementos existentes (no cambia, traduce ni elimina texto). Sin JS, la pagina queda como antes. */
(function () {
  function label(lang) {
    if (lang === 'es') return 'Índice';
    if (lang === 'en') return 'Contents';
    var h = document.querySelector('.page-hero h1, .page-hero .page-heading');
    return h ? h.textContent.replace(/^[^\p{L}\p{N}]+/u, '').trim() : '☰';
  }
  function isHead(el) {
    if (el.tagName !== 'P' || el.children.length !== 1) return false;
    var s = el.firstElementChild;
    return s.tagName === 'SPAN' && s.classList.contains('highlight') &&
      /^\s*\d+\s*[.)]/.test(s.textContent) && el.textContent.trim() === s.textContent.trim();
  }
  function build(box) {
    if (box.classList.contains('pp-on')) return;
    var kids = Array.prototype.slice.call(box.children);
    var heads = kids.filter(isHead);
    if (heads.length < 3) return;
    var lang = document.documentElement.lang.slice(0, 2).toLowerCase();
    var toc = document.createElement('details');
    toc.className = 'pp-toc';
    if (window.matchMedia('(min-width: 641px)').matches) toc.open = true;
    var sum = document.createElement('summary');
    sum.textContent = label(lang);
    var ol = document.createElement('ol');
    toc.appendChild(sum); toc.appendChild(ol);
    var card = document.createElement('section');
    card.className = 'pp-card pp-card--intro';
    box.insertBefore(card, kids[0]);
    var n = 0;
    kids.forEach(function (el) {
      if (isHead(el)) {
        n++;
        card = document.createElement('section');
        card.className = 'pp-card';
        box.insertBefore(card, el);
        el.classList.add('pp-h');
        el.setAttribute('role', 'heading');
        el.setAttribute('aria-level', '3');
        if (!el.id) el.id = 'pp-s' + n;
        var li = document.createElement('li'), a = document.createElement('a');
        a.href = '#' + el.id;
        a.textContent = el.textContent.trim();
        li.appendChild(a); ol.appendChild(li);
      }
      card.appendChild(el);
    });
    var intro = box.querySelector('.pp-card--intro');
    if (!intro.children.length) intro.remove();
    box.parentNode.insertBefore(toc, box);
    box.classList.add('pp-on');
    /* los enlaces con ancla a una seccion (p. ej. #eventos) siguen al elemento, que ahora esta dentro de una tarjeta */
    if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
  }
  function init() {
    Array.prototype.forEach.call(document.querySelectorAll('.privacy-text'), function (b) {
      /* original bilingue: construye tambien el bloque oculto (display:none no impide reorganizar) */
      build(b);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
