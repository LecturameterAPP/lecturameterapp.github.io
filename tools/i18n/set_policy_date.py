#!/usr/bin/env python3
"""Cambia el DIA de la fecha de «ultima actualizacion» de la politica de privacidad.

La fecha vive en dos sitios:
  1. i18n/<codigo>.json, claves `legal.privacy.p_002` (cabecera) y `legal.privacy.p_006`
     («Ultima actualizacion»), en los 49 idiomas. Alimentan /<codigo>/privacy/ (47 idiomas;
     es/en usan el original, pero las claves se mantienen al dia).
  2. privacidad.html (original ES+EN, escrito a mano): 4 apariciones.

Solo cambia el dia (el mes, noviembre de 2026, ya esta traducido en los 49 idiomas). Si la fecha
nueva cae en otro mes hay que traducir el mes: el script se niega a hacerlo.

Uso (desde la raiz del repo o desde tools/i18n):
    python tools/i18n/set_policy_date.py 20            # edita fuentes (no reconstruye)
    python tools/i18n/set_policy_date.py 20 --build    # y ejecuta build.py, build_blog.py, build.py
NO ejecutar make_legal.py.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
KEYS = ('legal.privacy.p_002', 'legal.privacy.p_006')
BN = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')


def rw(path, fn):
    with open(path, 'rb') as f:
        raw = f.read().decode('utf-8')
    new = fn(raw)
    if new != raw:
        with open(path, 'wb') as f:
            f.write(new.encode('utf-8'))
    return new != raw


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 30:
        sys.exit(__doc__)
    day = int(sys.argv[1])
    with open(os.path.join(ROOT, 'i18n', 'es.json'), encoding='utf-8') as f:
        m = re.search(r'"legal\.privacy\.p_006": ".*?(\d+) de noviembre de 2026', f.read())
    if not m:
        sys.exit('La fecha actual no esta en noviembre de 2026 en es.json: hay que traducir el mes a mano.')
    old = int(m.group(1))
    print('dia actual %d -> %d' % (old, day))
    changed = 0

    def sub_json(code):
        def fn(raw):
            out = []
            for line in raw.split('\n'):
                if any(line.lstrip().startswith('"%s":' % k) for k in KEYS):
                    o, n = (str(old), str(day)) if code != 'bn' else (str(old).translate(BN), str(day).translate(BN))
                    key, _, val = line.partition(': ')
                    assert len(re.findall(r'(?<![\d' + BN_DIGITS + r'])' + o + r'(?![\d' + BN_DIGITS + r'])', val)) == 1, (code, line)
                    val = re.sub(r'(?<![\d' + BN_DIGITS + r'])' + o + r'(?![\d' + BN_DIGITS + r'])', n, val)
                    line = key + ': ' + val
                out.append(line)
            return '\n'.join(out)
        return fn

    for fn_ in sorted(os.listdir(os.path.join(ROOT, 'i18n'))):
        code, ext = os.path.splitext(fn_)
        if ext != '.json' or code in ('locales', 'seo_store_map'):
            continue
        changed += rw(os.path.join(ROOT, 'i18n', fn_), sub_json(code))

    def fn_html(raw):
        raw = raw.replace('%d de noviembre de 2026' % old, '%d de noviembre de 2026' % day)
        return raw.replace('November %d, 2026' % old, 'November %d, 2026' % day)
    rw(os.path.join(ROOT, 'privacidad.html'), fn_html)
    print('ficheros i18n modificados: %d; privacidad.html actualizado' % changed)
    if '--build' in sys.argv:
        d = os.path.join(ROOT, 'tools', 'i18n')
        for s in ('build.py', 'build_blog.py', 'build.py'):
            subprocess.check_call([sys.executable, s], cwd=d)
    else:
        print('Falta reconstruir: cd tools/i18n && python build.py && python build_blog.py && python build.py')


BN_DIGITS = '০-৯'
if __name__ == '__main__':
    main()
