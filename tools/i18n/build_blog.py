#!/usr/bin/env python3
"""Generador del blog traducido: src/templates/blog-*.html + i18n/blog/<code>.json -> /<code>/blog/...

Uso:
    python tools/i18n/build_blog.py                 # todos los idiomas con i18n/blog/<code>.json (menos en/es)
    python tools/i18n/build_blog.py --code de       # solo uno
    python tools/i18n/build_blog.py --code de --src i18n/blog/_pilot_de.json --out /tmp/blogtest
                                                    # prueba: otro JSON, otro directorio, sin tocar sitemap ni en/es

Solo libreria estandar. Reutiliza build.py (variables, selector de idioma, render).
`en` y `es` NO se generan (sus articulos son los originales hechos a mano, `es/` con slugs en espanol);
`i18n/blog/en.json` es la fuente de claves. Ver tools/i18n/blog/README_traduccion.md.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B  # noqa: E402

ROOT = B.ROOT
BLOG_DIR = os.path.join(ROOT, 'i18n', 'blog')
SLUGS = ['lecturameter-1999', 'how-fast-do-i-really-read', 'fantasy-vs-manga-reading-pace',
         'reading-time-vs-pages', 'export-goodreads-library']
ALIAS = {'how-fast-do-i-really-read': 'hfr', 'fantasy-vs-manga-reading-pace': 'fvm', 'reading-time-vs-pages': 'rtp',
         'export-goodreads-library': 'egl', 'lecturameter-1999': 'l99'}
SLUG_ES = {'how-fast-do-i-really-read': 'a-que-velocidad-leo-de-verdad',
           'export-goodreads-library': 'exportar-biblioteca-goodreads',
           'fantasy-vs-manga-reading-pace': 'fantasia-frente-a-manga-ritmo-lectura',
           'reading-time-vs-pages': 'tiempo-de-lectura-o-paginas',
           'lecturameter-1999': 'lecturameter-1999'}
HAND_MADE = ('en', 'es')
MK_START = '<!-- blog-i18n:start -->'
MK_END = '<!-- blog-i18n:end -->'
CRLF, LF = '\r\n', '\n'


def target(loc, slug):
    """Ruta (desde la raiz del sitio, con / final) del indice (slug=None) o del articulo en ese idioma."""
    if loc['code'] == 'en':
        base = 'blog/'
    elif loc['code'] == 'es':
        base = 'es/blog/'
    else:
        base = loc['path'].lstrip('/') + 'blog/'
    if slug is None:
        return base
    return base + (SLUG_ES[slug] if loc['code'] == 'es' else slug) + '/'


def generated_codes():
    out = []
    if os.path.isdir(BLOG_DIR):
        for f in sorted(os.listdir(BLOG_DIR)):
            if f.endswith('.json') and not f.startswith('_'):
                c = f[:-5]
                if c not in HAND_MADE:
                    out.append(c)
    return out


def read_text(path):
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


def write_if_changed(path, text):
    """Escribe en LF solo si cambia. Devuelve True si cambio."""
    prev = read_text(path).replace(CRLF, LF) if os.path.exists(path) else None
    if prev == text:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline=LF) as f:
        f.write(text)
    return True


def check_keys(code, en, strings, where, errors):
    miss = [k for k in en if k not in strings]
    extra = [k for k in strings if k not in en]
    empty = [k for k in en if k in strings and not str(strings[k]).strip()]
    for k in miss:
        errors.append('%s: falta la clave %s' % (where, k))
    for k in extra:
        errors.append('%s: clave desconocida %s' % (where, k))
    for k in empty:
        errors.append('%s: clave vacia %s' % (where, k))


def render_page(cfg, loc, avail, tpl_name, slug, strings_common, strings_blog, errors):
    """HTML de una pagina del blog (slug=None -> indice) para el idioma `loc`."""
    strings = dict(strings_common)
    strings.update(strings_blog)
    where = '%s/%s' % (loc['code'], tpl_name)
    base = target(loc, slug)
    # build_vars calcula page_dir(loc, page) = loc.path + page.dir; con path='/' page.dir es la ruta completa
    page = {'dir': base}
    loc2 = dict(loc, path='/', blog=target(loc, None))
    v = B.build_vars(cfg, loc2, 'blog', page, [dict(o, path='/') for o in avail])
    # rutas dependientes del idioma real
    here = base.rstrip('/')
    prefix = loc['path'].lstrip('/')
    v['home'] = B.rel(here, prefix)
    v['link_1999'] = B.rel(here, prefix + 'lecturameter-1999/')
    for k, p in loc['features'].items():
        v['link_feat_' + k] = B.rel(here, p)
    for lk, lp in cfg.get('legal_pages', {}).items():
        v['link_' + lk] = B.rel(here, lp['original'] if loc.get('legal_original') else prefix + lp['dir'])
    v['link_blog'] = B.rel(here, target(loc, None))
    v['page_url'] = cfg['site_url'] + base
    v['code'] = loc['code']
    v['head_redirect'] = ''
    v['og_locale_alternates'] = ''.join(
        '    <meta property="og:locale:alternate" content="%s">\n' % o['og_locale'] for o in avail if o['code'] != loc['code'])
    lines = ['    <link rel="alternate" hreflang="%s" href="%s">\n' % (o['hreflang'], cfg['site_url'] + target(o, slug))
             for o in avail]
    lines.append('    <link rel="alternate" hreflang="x-default" href="%s">\n' % (cfg['site_url'] + target(
        [o for o in avail if o['code'] == 'en'][0], slug)))
    v['hreflang_links'] = ''.join(lines)
    v['blog_active'] = ' class="active"' if slug is None else ''
    if slug:
        a = ALIAS[slug]
        for n in ('title', 'description'):
            v['ld_' + n] = html.unescape(strings_blog['blog.%s.%s' % (a, n)])
    v.update(B.release_vars(cfg, strings_common, where, errors))
    v['__loc'] = loc
    v['__shot'] = B.make_shot_resolver(cfg, loc, errors, where)
    v['ios_live'] = '1' if cfg.get('ios_live') else ''
    v['ios_url'] = cfg['app_store_url'] if cfg.get('ios_live') else cfg['testflight_url']
    v['lm_i18n_json'] = B.js_payload(strings_common, bool(cfg.get('ios_live')))
    targets = {o['code']: target(o, slug) for o in avail}
    v['lang_picker'] = B.lang_picker(loc, page, avail, strings_common, ' ' * 12, targets=targets)
    with open(os.path.join(ROOT, 'src', 'templates', tpl_name), encoding='utf-8', newline='') as f:
        tpl = f.read().replace(CRLF, LF)
    return B.render(tpl, v, strings, where, errors)


# ---------------------------------------------------------------- en/es: hreflang
def existing_pages():
    """(ruta del HTML, slug|None, codigo) de los blogs hechos a mano."""
    out = []
    for code in HAND_MADE:
        loc = {'code': code}
        out.append((os.path.join(ROOT, *(target(loc, None) + 'index.html').split('/')), None, code))
        for s in SLUGS:
            out.append((os.path.join(ROOT, *(target(loc, s) + 'index.html').split('/')), s, code))
    return out


def patch_existing_hreflang(cfg, new_locs, avail):
    """Anade (entre marcadores) los hreflang de los idiomas nuevos a los HTML en/es, sin tocar el contenido."""
    changed = []
    for path, slug, code in existing_pages():
        if not os.path.exists(path):
            continue
        raw = read_text(path)
        eol = CRLF if CRLF in raw else LF
        text = raw.replace(CRLF, LF)
        text = re.sub(r'    ' + re.escape(MK_START) + r'\n.*?    ' + re.escape(MK_END) + r'\n', '', text, flags=re.S)
        if new_locs:
            block = '    ' + MK_START + '\n' + ''.join(
                '    <link rel="alternate" hreflang="%s" href="%s">\n' % (o['hreflang'], cfg['site_url'] + target(o, slug))
                for o in new_locs) + '    ' + MK_END + '\n'
            m = re.search(r'^[ \t]*<link rel="alternate" hreflang="x-default"[^\n]*\n', text, re.M)
            if not m:
                print('WARNING: sin x-default en', os.path.relpath(path, ROOT), file=sys.stderr)
                continue
            text = text[:m.start()] + block + text[m.start():]
        out = text.replace(LF, eol)
        if out != raw:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(out)
            changed.append(os.path.relpath(path, ROOT).replace(os.sep, '/'))
    return changed


# ---------------------------------------------------------------- sitemap
def update_sitemap(cfg, gen_locs, avail, changed_files):
    path = os.path.join(ROOT, 'sitemap.xml')
    text = read_text(path).replace(CRLF, LF)
    chunk_re = re.compile(r'  ' + re.escape('<!-- blog-i18n:start (build_blog.py) -->') + r'\n(.*?)  ' +
                          re.escape('<!-- blog-i18n:end -->') + r'\n', re.S)
    block_re = re.compile(r'  <url>\n.*?\n  </url>\n', re.S)
    old_chunk = chunk_re.search(text)
    old = {}
    if old_chunk:
        for m in block_re.finditer(old_chunk.group(1)):
            old[re.search(r'<loc>(.*?)</loc>', m.group(0)).group(1)] = m.group(0)
        text = text[:old_chunk.start()] + text[old_chunk.end():]
    site = cfg['site_url']
    today = datetime.date.today().isoformat()
    en_blocks = {}
    for m in block_re.finditer(text):
        en_blocks[re.search(r'<loc>(.*?)</loc>', m.group(0)).group(1)] = m.group(0)
    out = ''
    if gen_locs:
        for slug in [None] + SLUGS:
            en_loc = [o for o in avail if o['code'] == 'en'][0]
            ref = en_blocks.get(site + target(en_loc, slug), '')
            alts = ''.join('    <xhtml:link rel="alternate" hreflang="%s" href="%s" />\n' % (
                o['hreflang'], site + target(o, slug)) for o in avail)
            alts += '    <xhtml:link rel="alternate" hreflang="x-default" href="%s" />\n' % (site + target(en_loc, slug))
            for o in gen_locs:
                u = site + target(o, slug)
                prev = old.get(u, '')
                fpath = os.path.join(ROOT, *(target(o, slug) + 'index.html').split('/'))

                def field(name, dflt):
                    mm = re.search(r'<%s>(.*?)</%s>' % (name, name), prev) or re.search(
                        r'<%s>(.*?)</%s>' % (name, name), ref)
                    return mm.group(1) if mm else dflt
                lm = today if (fpath in changed_files or not prev) else field('lastmod', today)
                if prev and fpath not in changed_files:
                    mm = re.search(r'<lastmod>(.*?)</lastmod>', prev)
                    lm = mm.group(1) if mm else lm
                out += ('  <url>\n    <loc>%s</loc>\n%s    <lastmod>%s</lastmod>\n    <changefreq>%s</changefreq>\n'
                        '    <priority>%s</priority>\n  </url>\n') % (
                    u, alts, lm, field('changefreq', 'monthly'), field('priority', '0.6'))
    if out:
        out = '  <!-- blog-i18n:start (build_blog.py) -->\n' + out + '  <!-- blog-i18n:end -->\n'
        text = text.replace('</urlset>', out + '</urlset>')
    if text != read_text(path).replace(CRLF, LF):
        with open(path, 'w', encoding='utf-8', newline=LF) as f:
            f.write(text)
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--code', help='solo este idioma')
    ap.add_argument('--src', help='JSON de claves alternativo (pruebas); requiere --code')
    ap.add_argument('--out', help='directorio de salida alternativo (pruebas): no toca sitemap ni paginas en/es')
    args = ap.parse_args()
    if args.src and not args.code:
        ap.error('--src requiere --code')
    cfg = B.load_json(os.path.join(ROOT, 'i18n', 'locales.json'))
    by_code = {l['code']: l for l in cfg['locales']}
    codes = [args.code] if args.code else generated_codes()
    for c in codes:
        if c not in by_code:
            raise B.BuildError('idioma desconocido %s (no esta en locales.json)' % c)
        if not os.path.exists(os.path.join(ROOT, 'i18n', c + '.json')):
            raise B.BuildError('falta i18n/%s.json (textos comunes del sitio)' % c)
    if args.code and args.code in HAND_MADE and not args.out:
        raise B.BuildError('en/es son paginas hechas a mano: usa --out para generar una prueba')
    en = B.load_json(os.path.join(BLOG_DIR, 'en.json'))
    # idiomas disponibles (hreflang/selector): en, es + los que tienen JSON (o el de la prueba)
    avail_codes = set(HAND_MADE) | set(generated_codes()) | set(codes)
    avail = [l for l in cfg['locales'] if l['code'] in avail_codes]
    errors = []
    written = []
    for c in codes:
        loc = by_code[c]
        src = os.path.join(ROOT, args.src) if args.src and not os.path.isabs(args.src) else (
            args.src or os.path.join(BLOG_DIR, c + '.json'))
        strings_blog = B.load_json(src)
        check_keys(c, en, strings_blog, c, errors)
        strings_common = B.load_json(os.path.join(ROOT, 'i18n', c + '.json'))
        if errors:
            continue
        pages = [('blog-index.html', None)] + [('blog-%s.html' % s, s) for s in SLUGS]
        for tpl, slug in pages:
            outhtml = render_page(cfg, loc, avail, tpl, slug, strings_common, strings_blog, errors)
            written.append((target(loc, slug) + 'index.html', outhtml))
    if errors:
        for e in sorted(set(errors)):
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
    outroot = os.path.abspath(args.out) if args.out else ROOT
    changed = set()
    for rel_path, text in written:
        p = os.path.join(outroot, *rel_path.split('/'))
        did = write_if_changed(p, text)
        if did:
            changed.add(p)
        print('updated' if did else 'ok     ', rel_path)
    if not args.out:
        gen_locs = [by_code[c] for c in generated_codes()]
        for f in patch_existing_hreflang(cfg, gen_locs, avail):
            print('hreflang', f)
        if update_sitemap(cfg, gen_locs, avail, changed):
            print('updated sitemap.xml')
    for w in sorted(set(B.WARNINGS)):
        print('WARNING:', w, file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
    except B.BuildError as e:
        print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
