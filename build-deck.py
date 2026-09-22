#!/usr/bin/env python3
"""Собирает клиентскую версию презентации New SMM из деки для созвона.
Запуск из course-site:  python3 build-deck.py
Источник: ../ПРЕЗЕНТАЦИЯ_разбор_New_SMM.html (с заметками, для продажника).
Результат: newsmm-prezentaciya.html (без заметок и слайдов для созвона,
картинки по путям images/...), открывается на /newsmm-prezentaciya.
"""
import re, pathlib
src = pathlib.Path('../ПРЕЗЕНТАЦИЯ_разбор_New_SMM.html')
dst = pathlib.Path('newsmm-prezentaciya.html')
h = src.read_text(encoding='utf-8')
h = h.replace('<html lang="ru" data-variant="call">', '<html lang="ru" data-variant="client">', 1)
h = h.replace('<title>New SMM · презентация</title>', '<title>New SMM · обучение Малены Покладовой · презентация</title>', 1)
# слайды только для созвона вместе с их заметками
h = re.sub(r'<!-- \d\d · [^\n]*только созвон -->\n<section class="slide[^>]*data-call="1"[\s\S]*?</section>\n<div class="notes">[\s\S]*?</div>\n', '', h)
# все заметки
h = re.sub(r'<div class="notes">[\s\S]*?</div>\n', '', h)
# кнопка финала
h = h.replace('<span class="btn" data-client-text="Записаться на разбор">Оформляем?</span>', '<a class="btn" href="https://malenapocladova.com/zapis">Записаться на разбор</a>', 1)
# картинки относительно course-site
h = h.replace('src="course-site/images/', 'src="images/')
# сквозная нумерация в футерах
n = [0]
def renum(m):
    n[0] += 1
    return '<span class="n">%02d</span>' % n[0]
h = re.sub(r'<span class="n">\d\d</span>', renum, h)
dst.write_text(h, encoding='utf-8')
print('клиентская версия:', dst, n[0], 'слайдов,', dst.stat().st_size, 'байт')
