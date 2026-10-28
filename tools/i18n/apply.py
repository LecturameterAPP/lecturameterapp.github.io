#!/usr/bin/env python3
"""Valida tools/i18n/work/out/<code>.json (plano clave -> texto) y escribe i18n/<code>.json.

Uso: python tools/i18n/apply.py <code> | --all
Errores (no escribe nada): clave que falta o sobra, valor vacio, cambian etiquetas HTML (nombres y href),
marcadores ({{x}}, %s, %d, {0}), URLs/correos, numeros (los digitos de otros alfabetos cuentan como ASCII)
o comillas dobles en claves que van en atributos. Aviso: valor identico al EN en claves de mas de 4 palabras.
"""
import collections
import json
import os
import re
import sys
import unicodedata

from common import PLACEHOLDER, ROOT, URL, WORK, flatten, load, plain, translatable


def tags(v):
    t = collections.Counter(re.findall(r'<\s*/?\s*([A-Za-z][A-Za-z0-9]*)', v))
    h = collections.Counter(re.findall(r'href\s*=\s*["\']([^"\']*)["\']', v))
    return t, h


def numbers(v):
    v = re.sub(r'<[^>]*>', ' ', v)
    v = re.sub(r'&#?\w+;', ' ', v)
    v = PLACEHOLDER.sub(' ', v)
    v = ''.join(str(unicodedata.digit(c)) if c.isdigit() and unicodedata.digit(c, None) is not None else c for c in v)
    return collections.Counter(re.findall(r'\d+', v))


def check(key, en, val):
    errs = []
    if not isinstance(val, str) or not val.strip():
        return ['vacio'], []
    if tags(en) != tags(val):
        errs.append('etiquetas/href distintos')
    if collections.Counter(PLACEHOLDER.findall(en)) != collections.Counter(PLACEHOLDER.findall(val)):
        errs.append('marcadores distintos')
    if collections.Counter(URL.findall(plain_keep(en))) != collections.Counter(URL.findall(plain_keep(val))):
        errs.append('URLs/correos distintos')
    if numbers(en) != numbers(val) and not os.environ.get('LM_SKIP_NUMBERS'):
        errs.append('numeros distintos')
    base = key.split('#')[0]
    if '"' in val and '"' not in en and (base.endswith(('.alt', '.aria-label')) or base.startswith('head.') or base.endswith('.title') or base.endswith('.meta_description')):
        errs.append('comillas dobles en un atributo')
    warns = []
    if val.strip() == en.strip() and len(plain(en).split()) > 4:
        warns.append('identico al EN (posible sin traducir)')
    return errs, warns


def plain_keep(v):
    return re.sub(r'<(?!a\b)[^>]*>', ' ', v)


def rebuild(en_raw, flat, source):
    """Estructura de en.json con los textos de `flat` (las claves no traducibles se copian del EN)."""
    out = {}
    for k, v in en_raw.items():
        def val(fk, ev):
            return flat[fk] if fk in source else ev
        if isinstance(v, str):
            out[k] = val(k, v)
        else:
            lst = []
            for i, x in enumerate(v):
                if isinstance(x, str):
                    lst.append(val('%s#%d' % (k, i), x))
                else:
                    lst.append({f: val('%s#%d.%s' % (k, i, f), t) for f, t in x.items()})
            out[k] = lst
    return out


def apply(code, source, en_raw):
    path = os.path.join(WORK, 'out', code + '.json')
    if not os.path.exists(path):
        print('%s: no existe %s' % (code, path))
        return False
    flat = load(path)
    bad = []
    for k in sorted(set(source) - set(flat)):
        bad.append((k, 'falta la clave'))
    for k in sorted(set(flat) - set(source)):
        bad.append((k, 'sobra la clave'))
    warns = []
    for k, e in source.items():
        if k in flat:
            errs, w = check(k, e['en'], flat[k])
            bad += [(k, x) for x in errs]
            warns += [(k, x) for x in w]
    for k, w in warns:
        print('  aviso %s: %s [%s]' % (code, k, w))
    if bad:
        print('%s: ERROR, %d claves malas, no se escribe' % (code, len(bad)))
        for k, why in bad:
            print('  %s: %s' % (k, why))
        return False
    out = rebuild(en_raw, flat, source)
    with open(os.path.join(ROOT, 'i18n', code + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('%s: ok (%d claves, %d avisos)' % (code, len(source), len(warns)))
    return True


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    source = load(os.path.join(WORK, 'source.json'))
    en_raw = load(os.path.join(ROOT, 'i18n', 'en.json'))
    if args[0] == '--all':
        d = os.path.join(WORK, 'out')
        codes = sorted(f[:-5] for f in os.listdir(d) if f.endswith('.json')) if os.path.isdir(d) else []
    else:
        codes = args
    ok = [apply(c, source, en_raw) for c in codes]
    sys.exit(0 if all(ok) else 1)


if __name__ == '__main__':
    main()
