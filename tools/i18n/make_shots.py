#!/usr/bin/env python3
"""Convierte las capturas por idioma (fuera del repo, solo lectura) a WebP 720 px de ancho.

- Lecturameter 3.8: C:/Refrac/lm-qa-1910/capt38/raw_mi11/<loc>/0N_*.png  ->  capturas/3.8/<code>/<nombre>.webp
- Lecturameter 1999: C:/Refrac/Recursos LM/lm1999/capturas_play/<loc>/lm99_*.png ->
  capturas-1999/<code>/, capturas-1999/temas/<code>/, capturas-1999/salvapantallas/<code>/
Solo los idiomas nuevos (no en/es). Requiere Pillow. Uso: python tools/i18n/make_shots.py
"""
import json
import os
import sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW38 = 'C:/Refrac/lm-qa-1910/capt38/raw_mi11'
RAW99 = 'C:/Refrac/Recursos LM/lm1999/capturas_play'
# pantalla de la app (raw 3.8) -> nombre en capturas/3.8/<code>/ (ver screenshots.3.8.localized en locales.json)
MAP38 = {'01_portada.png': 'portada.webp', '05_retos.png': 'retos.webp', '04_estadisticas.png': 'estadisticas.webp'}
# captura del 1999 -> (subcarpeta, nombre en la web)
MAP99 = {
    'lm99_biblioteca.png': ('', 'lm99_biblioteca.webp'),
    'lm99_cronometro.png': ('', 'lm99_cronometro.webp'),
    'lm99_informe.png': ('', 'lm99_informe.webp'),
    'lm99_historial.png': ('', 'lm99_historial.webp'),
    'lm99_tema_a.png': ('temas', 'lm99_tema_1984.webp'),
    'lm99_tema_b.png': ('temas', 'lm99_tema_8bits.webp'),
    'lm99_salvapantallas.png': ('salvapantallas', 'lm99_saver_tuberias.webp'),
}
LOC38 = {'pt': 'pt-PT', 'pt-br': 'pt-BR', 'zh-cn': 'zh-CN'}
LOC99 = {'id': 'in', 'pt-br': 'pt-rBR', 'zh-cn': 'zh-rCN'}


def conv(src, dst, quality=80):
    im = Image.open(src).convert('RGB')
    h = round(im.height * 720 / im.width)
    im = im.resize((720, h), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst, 'WEBP', quality=quality, method=6)
    return os.path.getsize(dst)


def main():
    cfg = json.load(open(os.path.join(ROOT, 'i18n', 'locales.json'), encoding='utf-8'))
    total = 0
    missing = []
    for loc in cfg['locales']:
        c = loc['code']
        if loc.get('legal_original'):
            continue
        d38 = os.path.join(RAW38, LOC38.get(c, c))
        for src, name in MAP38.items():
            p = os.path.join(d38, src)
            if os.path.exists(p):
                total += conv(p, os.path.join(ROOT, 'capturas', '3.8', c, name))
            else:
                missing.append(p)
        d99 = os.path.join(RAW99, LOC99.get(c, c))
        for src, (sub, name) in MAP99.items():
            p = os.path.join(d99, src)
            if os.path.exists(p):
                dst = os.path.join(ROOT, 'capturas-1999', *( [sub] if sub else []), c, name)
                total += conv(p, dst)
            else:
                missing.append(p)
    print('total %.1f MB' % (total / 1048576))
    for m in missing:
        print('FALTA', m, file=sys.stderr)


if __name__ == '__main__':
    main()
