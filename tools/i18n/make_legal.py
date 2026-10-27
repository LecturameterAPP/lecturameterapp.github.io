#!/usr/bin/env python3
"""Deriva las plantillas legales (src/templates/legal-*.html) y sus claves EN/ES a partir de los
originales /privacidad.html, /privacidad-1999.html y /tos.html (bloques EN y ES).

Los originales NO se tocan. Es idempotente: reescribe las plantillas y las claves `legal.*` de
i18n/en.json y i18n/es.json. Solo hace falta volver a ejecutarlo si cambia el texto legal original
(y entonces hay que re-traducir las claves afectadas).
Uso: python tools/i18n/make_legal.py
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PAGES = [
    # (id, original, plantilla)
    ('privacy', 'privacidad.html', 'legal-privacy.html'),
    ('privacy1999', 'privacidad-1999.html', 'legal-privacy-1999.html'),
    ('terms', 'tos.html', 'legal-terms.html'),
]
LEAF = re.compile(
    r'<(?P<tag>h1|h2|h3|p|li)(?P<attr>[^>]*)>(?P<inner>.*?)</(?P=tag)>'
    r'|<div class="(?P<dcls>title|desc)">(?P<dinner>.*?)</div>', re.S)

HEAD = '''<!DOCTYPE html>
<html lang="{{code}}" dir="{{dir}}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{legal.%(id)s.title}}</title>
    <meta name="description" content="{{legal.%(id)s.meta_description}}">
    <meta property="og:title" content="{{legal.%(id)s.title}}">
    <meta property="og:description" content="{{legal.%(id)s.meta_description}}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{{page_url}}">
    <meta property="og:image" content="{{site_url}}social_card.jpg">
    <meta property="og:locale" content="{{og_locale}}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{legal.%(id)s.title}}">
    <meta name="twitter:description" content="{{legal.%(id)s.meta_description}}">
    <meta name="twitter:image" content="{{site_url}}social_card.jpg">
    <meta name="robots" content="noindex, follow">
    <meta name="theme-color" content="#121212">

    <link rel="icon" type="image/png" sizes="32x32" href="{{root}}favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="{{root}}favicon-16x16.png">
    <link rel="apple-touch-icon" href="{{root}}apple-touch-icon.png">
    <link rel="manifest" href="{{root}}site.webmanifest">
    <link rel="shortcut icon" href="{{root}}favicon.ico">

    <link rel="canonical" href="{{page_url}}">
    <link rel="stylesheet" href="{{root}}styles.css?v=6.10">
</head>
<body>

<nav class="nav-bar">
    <div class="nav-inner">
        <a href="{{home}}" class="nav-brand">
            <img src="{{root}}ic_launcher_round.png" alt="{{common.nav.lecturameter.alt}}" width="28" height="28">
            {{common.nav.lecturameter}}
        </a>
        <ul class="nav-pills">
            <li class="has-dropdown">
                <a href="{{home}}#{{anchor.features}}">{{common.nav.features}} <span class="caret" aria-hidden="true">&#x25BE;</span></a>
                <ul class="nav-dropdown">
                    <li><a href="{{link_feat_timer}}">{{common.nav.reading_timer_2}}</a></li>
                    <li><a href="{{link_feat_tracker}}">{{common.nav.reading_tracker}}</a></li>
                    <li><a href="{{link_feat_stats}}">{{common.nav.reading_statistics_2}}</a></li>
                    <li><a href="{{link_feat_goodreads}}">{{common.nav.goodreads_alternative}}</a></li>
                    <li><a href="{{link_feat_catalog}}">{{common.nav.book_catalog}}</a></li>
                </ul>
            </li>
            <li><a href="{{home}}#{{anchor.themes}}">{{common.nav.themes}}</a></li>
            <li><a href="{{home}}#{{anchor.pricing}}">{{common.nav.pro}}</a></li>
            <li><a href="{{home}}#{{anchor.whatsnew}}">{{common.nav.patch_notes}}</a></li>
            <li><a href="{{home}}#{{anchor.history}}">{{common.nav.history}}</a></li>
{{#if has_roadmap}}
            <li><a href="{{home}}#roadmap">{{common.nav.roadmap}}</a></li>
{{/if}}
            <li><a href="{{link_1999}}">1999</a></li>
            <li><a href="{{home}}#faq">{{common.nav.faq}}</a></li>
            <li><a href="{{link_blog}}">{{common.nav.blog}}</a></li>
        </ul>
        <div class="nav-controls">
            <button class="nav-theme-btn" aria-label="{{common.nav.toggle_theme.aria-label}}">&#x263E;</button>
            {{lang_picker}}
            <a href="https://play.google.com/store/apps/details?id=com.lecturameter.public" target="_blank" rel="noopener" class="nav-cta desktop-only">
                <svg viewBox="0 0 24 24"><path d="M3 20.5v-17c0-.59.34-1.11.84-1.35L13.69 12l-9.85 9.85c-.5-.24-.84-.76-.84-1.35zm13.81-5.38L6.05 21.34l8.49-8.49 2.27 2.27zm.91-.52l2.79-1.61c.52-.3.52-1.06 0-1.36l-2.79-1.61-2.47 2.29 2.47 2.29zM6.05 2.66l10.76 6.22-2.27 2.27L6.05 2.66z"/></svg>
                {{common.nav.download}}
            </a>
        </div>
        <button class="nav-hamburger" aria-label="{{common.nav.menu.aria-label}}">
            <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
    </div>
</nav>

<div class="subpage-container">
    <div class="legal-disclaimer" role="note">
        <span>{{legal.disclaimer}}</span> <a href="{{legal_original_url}}">{{legal.disclaimer.link}}</a>
    </div>

    <div class="legal-content">
'''
FOOT = '''    </div>
</div>

<footer class="site-footer">
    <div class="container">
        <div class="footer-bottom">
            <span>{{common.footer.2026_lecturameter_independent_proj_2}}</span>
            <a href="{{home}}">{{common.footer.home}}</a>
            <a href="{{link_privacy}}">{{common.footer.privacy_policy}}</a>
            <a href="{{link_terms}}">{{common.footer.terms_of_service}}</a>
            <a href="{{root}}contact.html">{{common.footer.contact}}</a>
        </div>
    </div>
</footer>

<script id="lm-i18n" type="application/json">{{lm_i18n_json}}</script>
<script src="{{root}}main.js?v=6.5" defer></script>
</body>
</html>
'''


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def block(text, lang):
    i = text.index('id="content-%s"' % lang)
    i = text.index('>', i) + 1
    j = text.index('<div class="footer">', i)
    return text[i:j]


def kind(m):
    if m.group('tag'):
        tag = m.group('tag')
        if tag == 'p' and 'tagline' in m.group('attr'):
            tag = 'tagline'
        return tag
    return 'd' + m.group('dcls')


def extract(blk):
    out = []
    for m in LEAF.finditer(blk):
        inner = m.group('inner') if m.group('tag') else m.group('dinner')
        out.append(norm(inner))
    return out


def main():
    en = json.load(open(os.path.join(ROOT, 'i18n', 'en.json'), encoding='utf-8'))
    es = json.load(open(os.path.join(ROOT, 'i18n', 'es.json'), encoding='utf-8'))
    for d in (en, es):
        for k in [k for k in d if k.startswith('legal.')]:
            del d[k]
    en['legal.disclaimer'] = 'This is an informational translation. In case of doubt, the English or Spanish version prevails.'
    es['legal.disclaimer'] = 'Esta es una traducción informativa. En caso de duda, prevalece la versión en inglés o en español.'
    en['legal.disclaimer.link'] = 'Read the original'
    es['legal.disclaimer.link'] = 'Leer el original'
    for pid, orig, tpl in PAGES:
        text = open(os.path.join(ROOT, orig), encoding='utf-8').read()
        ben, bes = block(text, 'en'), block(text, 'es')
        ven, ves = extract(ben), extract(bes)
        if len(ven) != len(ves):
            print('AVISO %s: %d bloques EN y %d ES; el contexto ES puede desalinearse' % (orig, len(ven), len(ves)))
        keys = []

        def sub(m):
            key = 'legal.%s.%s_%03d' % (pid, kind(m), len(keys))
            keys.append(key)
            whole = m.group(0)
            a = whole.index('>') + 1
            b = whole.rindex('</')
            return whole[:a] + '{{' + key + '}}' + whole[b:]
        body = LEAF.sub(sub, ben)
        for i, k in enumerate(keys):
            en[k] = ven[i]
            es[k] = ves[i] if i < len(ves) else ven[i]
        h = next(k for k in keys if re.search(r'\.h[12]_', k))
        en['legal.%s.title' % pid] = re.sub(r'^[^\w<]+', '', en[h]).strip() + ' – Lecturameter'
        es['legal.%s.title' % pid] = re.sub(r'^[^\w<]+', '', es[h]).strip() + ' – Lecturameter'
        tg = next((k for k in keys if '.tagline_' in k), keys[1])
        en['legal.%s.meta_description' % pid] = en[tg]
        es['legal.%s.meta_description' % pid] = es[tg]
        body = re.sub(r'<h2 class="page-heading">(.*?)</h2>', r'<h1 class="page-heading">\1</h1>', body, flags=re.S)
        body = body.replace(' color:#ddd;', '').replace('#BB86FC', 'var(--accent)')
        body = '\n'.join(('    ' + l if l.strip() else l) for l in body.strip('\n').split('\n')) + '\n'
        with open(os.path.join(ROOT, 'src', 'templates', tpl), 'w', encoding='utf-8', newline='\n') as f:
            f.write(HEAD % {'id': pid} + body + FOOT)
        print(tpl, len(keys), 'claves')
    for name, d in (('en', en), ('es', es)):
        with open(os.path.join(ROOT, 'i18n', name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
