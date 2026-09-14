#!/usr/bin/env python3
"""Собирает kurs-review.html из kurs.html.
Запускать после любой правки страницы курса:  python3 build-review-kurs.py

Отличие от build-review.py: тот собирает лендинг клуба, этот страницу курса.
Полоса фактов и липкая плашка в kurs.html это <div>, а review.js ищет
header, section, nav, footer и классы tick и strip. Поэтому перед сборкой
дописываем им класс strip, иначе эти два блока нельзя будет прокомментировать.
"""
import pathlib

src = pathlib.Path('kurs.html')
dst = pathlib.Path('kurs-review.html')
h = src.read_text(encoding='utf-8')

h = h.replace('<title>', '<title>Правки · ', 1)

# Версия для правок закрыта от индексации. Пароля тут нет сознательно:
# страница ещё не в рекламе, а лишний барьер мешает быстро открыть с телефона.
h = h.replace('<link rel="preconnect" href="https://fonts.googleapis.com">',
              '<meta name="robots" content="noindex, nofollow">\n'
              '<link rel="preconnect" href="https://fonts.googleapis.com">', 1)

# Блоки, которые review.js иначе не увидит.
h = h.replace('<div class="facts">', '<div class="facts strip">', 1)
h = h.replace('<div class="bar" id="bar">', '<div class="bar strip" id="bar">', 1)

banner = (
'<div id="rv-top">Режим правок. Тыкайте в любой блок и пишите, что не так. '
'Всё сохраняется только в этом браузере. Закончили, нажмите «Собрать всё» и пришлите файл.</div>\n'
'<style>#rv-top{background:#6E1E2B;color:#F6EFE2;font-family:-apple-system,BlinkMacSystemFont,'
'"Segoe UI",Roboto,sans-serif;font-size:13px;line-height:1.45;text-align:center;padding:10px 18px}'
'.nav{top:0}@media(max-width:640px){#rv-top{font-size:12px;padding:9px 14px}}</style>\n'
)
h = h.replace('<body>\n', '<body>\n' + banner, 1)
h = h.replace('</body>', '<script src="review.js"></script>\n</body>', 1)

dst.write_text(h, encoding='utf-8')
print('готово:', dst, len(h), 'байт')
