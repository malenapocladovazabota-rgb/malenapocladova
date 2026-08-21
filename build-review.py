#!/usr/bin/env python3
"""Собирает prodvizhenie-review.html из prodvizhenie.html.
Запускать после любой правки лендинга:  python3 build-review.py"""
import re, pathlib

src = pathlib.Path('prodvizhenie.html')
dst = pathlib.Path('prodvizhenie-review.html')
h = src.read_text(encoding='utf-8')

h = h.replace('<title>ПРОДВИЖЕНИЕ · клуб · учебный год 2026/27</title>',
              '<title>Правки · ПРОДВИЖЕНИЕ · клуб</title>')

# Боевая страница открыта, а версия для правок остаётся под паролем и вне индексации.
h = h.replace('<link rel="preconnect" href="https://fonts.googleapis.com">',
              '<meta name="robots" content="noindex, nofollow">\n'
              '<script src="gate-prodvizhenie.js"></script>\n'
              '<link rel="preconnect" href="https://fonts.googleapis.com">', 1)

banner = (
'<div id="rv-top">Режим правок. Всё, что вы отметите, сохраняется только в этом браузере. '
'Закончили — нажмите «Собрать всё» и пришлите файл.</div>\n'
'<style>#rv-top{background:#6B2138;color:#FBF3E6;font-family:-apple-system,BlinkMacSystemFont,'
'"Segoe UI",Roboto,sans-serif;font-size:13px;line-height:1.45;text-align:center;padding:10px 18px}'
'nav{top:0}@media(max-width:640px){#rv-top{font-size:12px;padding:9px 14px}}</style>\n'
)
h = h.replace('<body>\n', '<body>\n' + banner, 1)
h = h.replace('</body>', '<script src="review.js"></script>\n</body>', 1)

dst.write_text(h, encoding='utf-8')
print('готово:', dst, len(h), 'байт')
