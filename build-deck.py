#!/usr/bin/env python3
"""Собирает из одного источника две версии презентации New SMM.
Запуск из course-site:  python3 build-deck.py

Источник: ../ПРЕЗЕНТАЦИЯ_разбор_New_SMM.html (правится только он).

Результаты:
  newsmm-prezentaciya.html  клиентская, /newsmm-prezentaciya
        без заметок, без слайдов «только созвон», финал с кнопкой на /zapis.
        Её отправляем людям.
  newsmm-razbor.html        внутренняя, /newsmm-razbor
        все слайды, заметки спикера по клавише N, финал с тремя шагами.
        Её открывают Малена и Александра перед разбором в Zoom.

Обе закрыты от индексации. Внутренняя ещё и от случайного захода:
ссылку знают только свои, в меню сайта её нет.
"""
import re, pathlib

src = pathlib.Path('../ПРЕЗЕНТАЦИЯ_разбор_New_SMM.html')
raw = src.read_text(encoding='utf-8')


def renumber(h):
    """Сквозная нумерация в футерах после вырезания слайдов."""
    n = [0]
    def one(m):
        n[0] += 1
        return '<span class="n">%02d</span>' % n[0]
    return re.sub(r'<span class="n">\d\d</span>', one, h), n[0]



# ── тумблер «Телефон / Компьютер» (29 сентября) ─────────────────────────
# Внизу слева на широких версиях. Выбор запоминается в браузере (newsmm_deck):
# «Компьютер» на телефоне отключает автопереход на вертикальную версию.
# С внутренней версии «Телефон» ведёт на вертикальную клиентскую, а
# «Компьютер» оттуда возвращает обратно на внутреннюю (sessionStorage).
def toggle_html(internal):
    back = "try{sessionStorage.setItem('newsmm_deck_from','razbor')}catch(e){}" if internal else "try{sessionStorage.removeItem('newsmm_deck_from')}catch(e){}"
    return (
    '<div id="dv" role="group" aria-label="Версия презентации">'
    '<button type="button" data-v="m"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="2.5" width="10" height="19" rx="2.2"/><path d="M11 18.5h2"/></svg>Телефон</button>'
    '<button type="button" data-v="d" class="on" aria-pressed="true"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="1.8"/><path d="M9 20h6M12 16v4"/></svg>Компьютер</button>'
    '</div>\n'
    '<style>\n'
    '#dv{position:fixed;left:16px;bottom:14px;z-index:55;display:flex;padding:3px;border-radius:999px;background:rgba(20,14,14,.8);border:1px solid rgba(255,255,255,.18);'
    'font:600 12px/1 -apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;letter-spacing:.3px}\n'
    '#dv button{display:flex;align-items:center;gap:6px;border:0;border-radius:999px;padding:7px 12px;background:transparent;color:rgba(246,239,226,.7);cursor:pointer;font:inherit}\n'
    '#dv button:hover{color:#F6EFE2}\n'
    '#dv button.on{background:#F5C463;color:#1B1413;cursor:default}\n'
    '#dv svg{width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round}\n'
    '@media print{#dv{display:none}}\n'
    '</style>\n'
    '<script>(function(){var d=document.getElementById("dv");'
    'document.addEventListener("fullscreenchange",function(){d.style.display=document.fullscreenElement?"none":"";});'
    'd.addEventListener("click",function(e){var b=e.target.closest("button");if(!b||b.classList.contains("on"))return;'
    'try{localStorage.setItem("newsmm_deck","m")}catch(x){}' + back + 'location.href="/newsmm-prezentaciya-m";});})();</script>\n')

# ── клиентская ───────────────────────────────────────────────────────────
h = raw
h = h.replace('<html lang="ru" data-variant="call">', '<html lang="ru" data-variant="client">', 1)
h = h.replace('<title>New SMM · презентация</title>',
              '<title>New SMM · обучение Малены Покладовой</title>', 1)
# слайды только для созвона вместе с их заметками
h = re.sub(r'<!-- \d\d · [^\n]*только созвон -->\n<section class="slide[^>]*data-call="1"[\s\S]*?</section>\n<div class="notes">[\s\S]*?</div>\n', '', h)
# блок финала только для созвона
h = re.sub(r'<div class="only-call">[\s\S]*?\n    </div>\n', '', h)
# все заметки
h = re.sub(r'<div class="notes">[\s\S]*?</div>\n', '', h)
h = h.replace('src="course-site/images/', 'src="images/')
# телефоны сразу на вертикальную версию /newsmm-prezentaciya-m (правится руками,
# отдельный файл). ?desktop=1 оставляет широкую версию.
h = h.replace('<meta name="robots" content="noindex, nofollow">',
    '<meta name="robots" content="noindex, nofollow">\n<script>(function(){try{'
    'if(/desktop=1/.test(location.search)){localStorage.setItem("newsmm_deck","d");return;}'
    'if(localStorage.getItem("newsmm_deck")==="d")return;'
    'if(Math.min(screen.width,screen.height)<600)location.replace("/newsmm-prezentaciya-m"+location.search)}catch(e){}})();</script>', 1)
h = h.replace('</body>', toggle_html(False) + '</body>', 1)
h, n = renumber(h)
dst = pathlib.Path('newsmm-prezentaciya.html')
dst.write_text(h, encoding='utf-8')
print('клиентская:  %-26s %2d слайдов, %6d байт  → /newsmm-prezentaciya' % (dst, n, dst.stat().st_size))

# ── внутренняя ───────────────────────────────────────────────────────────
g = raw
g = g.replace('<title>New SMM · презентация</title>',
              '<title>Разбор New SMM · для команды</title>', 1)
# блок финала только для клиентской версии
g = re.sub(r'<div class="only-client"[^>]*>[\s\S]*?\n    </div>\n', '', g)
g = g.replace('src="course-site/images/', 'src="images/')
# полоска-напоминание: это внутренняя версия. Закрывается крестиком навсегда
# (запоминается в браузере) и сама прячется в полноэкранном режиме, чтобы
# не светиться при показе экрана в Zoom.
banner = r'''<div id="int">Внутренняя версия · заметки по клавише N · клиенту отправлять <b>malenapocladova.com/newsmm-prezentaciya</b><button id="intx" title="Скрыть насовсем">&times;</button></div>
<style>
#int{position:fixed;left:0;right:0;top:0;z-index:80;background:#6E1E2B;color:#F6EFE2;
  font:600 12px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;letter-spacing:.4px;
  text-align:center;padding:7px 38px 7px 14px;opacity:.94;transition:opacity .25s}
#int b{color:#F5C463}
#int:hover{opacity:.22}
#intx{position:absolute;right:8px;top:50%;transform:translateY(-50%);width:22px;height:22px;border:0;
  border-radius:50%;background:rgba(255,255,255,.18);color:#F6EFE2;font:400 15px/1 sans-serif;cursor:pointer;padding:0}
#intx:hover{background:rgba(255,255,255,.36)}
#int.off{display:none}
@media print{#int{display:none}}
</style>
<script>
(function(){
  var b=document.getElementById('int');
  /* крестик прячет полоску навсегда на этом компьютере */
  try{ if(localStorage.getItem('newsmm_int_hidden')==='1') b.classList.add('off'); }catch(e){}
  document.getElementById('intx').addEventListener('click',function(){
    b.classList.add('off');
    try{ localStorage.setItem('newsmm_int_hidden','1'); }catch(e){}
  });
  /* в полноэкранном режиме полоски нет: идёт показ экрана */
  document.addEventListener('fullscreenchange',function(){
    b.style.visibility=document.fullscreenElement?'hidden':'';
  });
})();
</script>
'''
g = g.replace('<body>\n', '<body>\n' + banner, 1)
g = g.replace('</body>', toggle_html(True) + '</body>', 1)
g, n = renumber(g)
dst2 = pathlib.Path('newsmm-razbor.html')
dst2.write_text(g, encoding='utf-8')
print('внутренняя:  %-26s %2d слайдов, %6d байт  → /newsmm-razbor' % (dst2, n, dst2.stat().st_size))
