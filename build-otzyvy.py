#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Собирает блок отзывов на лендинге клуба «ПроДвижение».

Что делает:
  1. читает таблицу из ОТЗЫВЫ_КЛУБ/ЗАПОЛНИТЕ-ЭТО.md
  2. жмёт скриншоты из ОТЗЫВЫ_КЛУБ/1-скриншоты-телеграм
  3. режет портреты из ОТЗЫВЫ_КЛУБ/2-фото-учениц в квадрат
  4. складывает результат в course-site/images/club/otzyvy
  5. подменяет блок между метками ОТЗЫВЫ:НАЧАЛО и ОТЗЫВЫ:КОНЕЦ в prodvizhenie.html

Запуск из папки course-site:
    python3 build-otzyvy.py

Ничего не трогает, пока в папках пусто: если скриншотов и карточек нет,
скрипт скажет об этом и выйдет, оставив страницу как была.
"""

import html
import re
import shutil
import sys
import unicodedata
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Нужна библиотека Pillow: pip install pillow --break-system-packages")

HERE = Path(__file__).resolve().parent          # course-site
ROOT = HERE.parent                              # SMM с нуля
SRC = ROOT / "ОТЗЫВЫ_КЛУБ"
SHOTS_IN = SRC / "1-скриншоты-телеграм"
FACES_IN = SRC / "2-фото-учениц"
TABLE = SRC / "ЗАПОЛНИТЕ-ЭТО.md"
OUT = HERE / "images" / "club" / "otzyvy"
PAGE = HERE / "prodvizhenie.html"

SHOT_W = 760        # ширина скриншота на странице с запасом под ретину
FACE_PX = 440       # сторона квадратного портрета
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".HEIC"}


def translit(s: str) -> str:
    """Латиница для имени файла, чтобы путь на сайте был без кириллицы."""
    m = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z",
         "и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r",
         "с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch",
         "ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"}
    s = unicodedata.normalize("NFC", s.strip().lower())
    out = "".join(m.get(ch, ch) for ch in s)
    out = re.sub(r"[^a-z0-9]+", "-", out).strip("-")
    return out or "x"


def read_table():
    """Возвращает список словарей из таблицы. Пустые и примерные строки пропускает."""
    if not TABLE.exists():
        return []
    rows = []
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if cells[0] in ("Имя", "") or set(cells[0]) <= set("-: "):
            continue
        if cells[0] == "Мария" and "944" in cells[2]:
            continue  # строка-пример из инструкции
        ok = cells[4].lower() in ("да", "yes", "+", "ок", "ok")
        if not ok:
            print(f"  пропускаю {cells[0]}: нет разрешения показывать")
            continue
        rows.append({"name": cells[0], "who": cells[1], "result": cells[2], "photo": cells[3]})
    return rows


def prep_shots():
    if not SHOTS_IN.exists():
        return []
    files = sorted(p for p in SHOTS_IN.iterdir()
                   if p.suffix.lower() in PHOTO_EXT and not p.name.startswith("."))
    made = []
    for i, p in enumerate(files, 1):
        try:
            im = Image.open(p)
            im = ImageOps.exif_transpose(im).convert("RGB")
        except Exception as e:
            print(f"  не смог открыть {p.name}: {e}")
            continue
        if im.width > SHOT_W:
            im = im.resize((SHOT_W, round(im.height * SHOT_W / im.width)), Image.LANCZOS)
        name = f"shot-{i:02d}.jpg"
        im.save(OUT / name, quality=86, optimize=True)
        made.append(name)
        print(f"  скриншот {p.name} → {name} ({im.width}×{im.height})")
    return made


def prep_face(filename: str, person: str):
    if not filename or not FACES_IN.exists():
        return None
    src = FACES_IN / filename
    if not src.exists():
        cands = [p for p in FACES_IN.iterdir() if p.stem.lower() == Path(filename).stem.lower()]
        if not cands:
            print(f"  фото {filename} не нашлось, карточка будет без портрета")
            return None
        src = cands[0]
    try:
        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert("RGB")
    except Exception as e:
        print(f"  не смог открыть {src.name}: {e}")
        return None
    # Квадрат по центру, но с уклоном вверх: лица обычно в верхней трети кадра.
    im = ImageOps.fit(im, (FACE_PX, FACE_PX), Image.LANCZOS, centering=(0.5, 0.35))
    name = f"face-{translit(person)}.jpg"
    im.save(OUT / name, quality=88, optimize=True)
    print(f"  портрет {src.name} → {name}")
    return name


def build_html(cards, shots):
    e = html.escape
    parts = ['<!-- ОТЗЫВЫ:НАЧАЛО · этот блок пересобирается скриптом build-otzyvy.py, руками не править -->',
             '<section style="background:var(--paper2)">',
             '  <div class="wrap">',
             '    <div class="c">',
             '      <div class="kicker">Ученицы школы</div>',
             '      <h2>Так это <span class="yl">уже было</span></h2>',
             '      <p class="lede">Это ученицы курса Малены и их собственные слова. '
             'Клуб стартует 1 сентября, и первые истории участниц появятся здесь же.</p>',
             '    </div>']

    if cards:
        parts.append('    <div class="res">')
        for i, c in enumerate(cards, 1):
            # Все карточки одного размера: шесть штук ровно ложатся в три колонки.
            # Главный кейс просто стоит первым, выделять его шириной не нужно.
            d = f" d{min(i, 4)}"
            img = (f'<img src="images/club/otzyvy/{c["file"]}" alt="{e(c["name"])}" '
                   f'loading="lazy" decoding="async">') if c.get("file") else \
                  f'<div class="ini">{e(c["name"][:1].upper())}</div>'
            parts.append(
                f'      <div class="rc rv{d}">{img}'
                f'<div class="nm">{e(c["name"])}</div>'
                f'<div class="mt">{e(c["who"])}</div>'
                f'<p>{e(c["result"])}</p></div>')
        parts.append('    </div>')

    if shots:
        parts += [
            '    <div class="shots-h">Отзывы учениц обучения</div>',
            '    <div class="shots" role="list">']
        for s in shots:
            parts.append(
                f'      <a class="shot" role="listitem" href="images/club/otzyvy/{s}" '
                f'target="_blank" rel="noopener">'
                f'<img src="images/club/otzyvy/{s}" alt="Отзыв в Telegram" '
                f'loading="lazy" decoding="async"></a>')
        parts += ['    </div>',
                  '    <div class="shots-n">Листайте вбок. Нажмите, чтобы открыть крупно</div>']

    parts += ['  </div>', '</section>']

    # Просмотрщик живёт внутри страницы: отдельная вкладка с голой картинкой
    # выбрасывала человека с лендинга и обратно он не всегда возвращался.
    if shots:
        parts += [LIGHTBOX_HTML, LIGHTBOX_JS]

    parts += ['<!-- ОТЗЫВЫ:КОНЕЦ -->']
    return "\n".join(parts)


LIGHTBOX_HTML = """<div class="lb" id="lb" hidden>
  <button class="lb-x" id="lb-x" type="button" aria-label="Закрыть">&times;</button>
  <button class="lb-p" type="button" aria-label="Предыдущий отзыв">&lsaquo;</button>
  <figure class="lb-f"><img id="lb-img" alt="Отзыв в Telegram"></figure>
  <button class="lb-n" type="button" aria-label="Следующий отзыв">&rsaquo;</button>
  <div class="lb-c"><span id="lb-i">1</span> из <span id="lb-t">1</span></div>
</div>"""

LIGHTBOX_JS = """<script>
(function(){
  var shots=[].slice.call(document.querySelectorAll('.shots .shot'));
  var lb=document.getElementById('lb');
  if(!shots.length||!lb)return;
  var img=document.getElementById('lb-img'),
      cur=document.getElementById('lb-i'),
      tot=document.getElementById('lb-t'),
      x=document.getElementById('lb-x'), i=0;
  tot.textContent=shots.length;

  function show(n){
    i=(n+shots.length)%shots.length;
    img.src=shots[i].getAttribute('href');
    cur.textContent=i+1;
  }
  function open(n){
    show(n);
    lb.hidden=false;
    requestAnimationFrame(function(){lb.classList.add('on')});
    document.body.style.overflow='hidden';
    x.focus();
  }
  function close(){
    lb.classList.remove('on');
    document.body.style.overflow='';
    setTimeout(function(){lb.hidden=true;img.removeAttribute('src')},220);
  }

  shots.forEach(function(a,n){
    a.addEventListener('click',function(e){e.preventDefault();open(n)});
  });

  lb.addEventListener('click',function(e){
    var t=e.target;
    if(t.classList.contains('lb-x'))return close();
    if(t.classList.contains('lb-p'))return show(i-1);
    if(t.classList.contains('lb-n'))return show(i+1);
    if(t===lb)close();
  });

  document.addEventListener('keydown',function(e){
    if(lb.hidden)return;
    if(e.key==='Escape')close();
    else if(e.key==='ArrowLeft')show(i-1);
    else if(e.key==='ArrowRight')show(i+1);
  });

  var x0=null;
  lb.addEventListener('touchstart',function(e){x0=e.touches[0].clientX},{passive:true});
  lb.addEventListener('touchend',function(e){
    if(x0===null)return;
    var dx=e.changedTouches[0].clientX-x0; x0=null;
    if(Math.abs(dx)>45)show(dx<0?i+1:i-1);
  });
})();
</script>"""


CSS = """
/* ── отзывы: лента скриншотов ─────────────────────────────── */
.shots-h{font-family:var(--pos);font-weight:600;font-size:11px;letter-spacing:.22em;
  text-transform:uppercase;color:var(--wine);text-align:center;margin:56px 0 18px}
.shots{display:flex;gap:16px;overflow-x:auto;padding:6px 4px 18px;
  scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch}
.shots::-webkit-scrollbar{height:6px}
.shots::-webkit-scrollbar-thumb{background:rgba(23,19,19,.22);border-radius:3px}
.shot{flex:0 0 auto;width:260px;scroll-snap-align:center;display:block;
  background:var(--card);padding:8px;border:1px solid var(--line);
  box-shadow:0 10px 26px rgba(23,19,19,.10);transition:transform .2s,box-shadow .2s}
.shot:nth-child(odd){transform:rotate(-.7deg)}
.shot:nth-child(even){transform:rotate(.6deg)}
.shot:hover{transform:rotate(0) translateY(-4px);box-shadow:0 16px 34px rgba(23,19,19,.16)}
.shot img{display:block;width:100%;height:auto}
.shots-n{text-align:center;font-size:13.5px;color:var(--ink3);margin-top:2px}
.res .ini{aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;
  background:var(--wine);color:var(--paper2);font-family:var(--disp);font-size:40px;margin-bottom:17px}
@media(max-width:640px){
  .shot{width:220px}
  .shots{gap:12px}
  .shots-h{margin:40px 0 14px}
}
"""

LIGHTBOX_CSS = """
/* ── отзывы: просмотрщик внутри страницы ──────────────────── */
.lb{position:fixed;inset:0;z-index:200;display:flex;align-items:center;justify-content:center;
  background:rgba(23,19,19,.88);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);
  padding:60px 16px;opacity:0;transition:opacity .22s ease}
.lb.on{opacity:1}
.lb[hidden]{display:none}
.lb-f{margin:0;padding:10px;background:var(--card);display:flex;max-height:100%;
  box-shadow:0 30px 70px rgba(0,0,0,.5)}
.lb-f img{display:block;width:auto;height:auto;object-fit:contain;
  max-width:min(520px,86vw);max-height:calc(100vh - 140px)}
.lb button{position:absolute;border:none;cursor:pointer;background:var(--card);color:var(--ink);
  font-family:var(--pos);line-height:1;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 6px 18px rgba(0,0,0,.34);transition:background .18s,transform .18s}
.lb button:hover{background:var(--sun)}
.lb button:active{transform:scale(.93)}
.lb-x{top:16px;right:16px;width:42px;height:42px;font-size:25px;padding-bottom:3px}
.lb-p,.lb-n{top:50%;margin-top:-23px;width:46px;height:46px;font-size:30px;padding-bottom:5px}
.lb-p{left:16px}
.lb-n{right:16px}
.lb-c{position:absolute;left:0;right:0;bottom:18px;text-align:center;
  font-family:var(--pos);font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;
  color:rgba(242,234,217,.66)}
@media(max-width:640px){
  .lb{padding:56px 8px}
  .lb-x{top:10px;right:10px;width:38px;height:38px;font-size:23px}
  .lb-p,.lb-n{width:38px;height:38px;font-size:26px;margin-top:-19px}
  .lb-p{left:6px}
  .lb-n{right:6px}
  .lb-f img{max-width:93vw;max-height:calc(100vh - 128px)}
}
@media(prefers-reduced-motion:reduce){.lb{transition:none}}
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Собираю отзывы\n")

    cards = read_table()
    for c in cards:
        c["file"] = prep_face(c.get("photo", ""), c["name"])
    shots = prep_shots()

    if not cards and not shots:
        sys.exit("\nВ папке ОТЗЫВЫ_КЛУБ пока пусто. Страницу не трогаю.")

    print(f"\nКарточек: {len(cards)} · скриншотов: {len(shots)}")

    page = PAGE.read_text(encoding="utf-8")

    if ".shots-h{" not in page:
        page = page.replace("</style>", CSS + "</style>", 1)
        print("Стили ленты добавлены")

    if ".lb{position:fixed" not in page:
        page = page.replace("</style>", LIGHTBOX_CSS + "</style>", 1)
        print("Стили просмотрщика добавлены")

    block = build_html(cards, shots)
    new, n = re.subn(
        r"<!-- ОТЗЫВЫ:НАЧАЛО.*?<!-- ОТЗЫВЫ:КОНЕЦ -->",
        lambda _: block, page, count=1, flags=re.S)
    if not n:
        sys.exit("Не нашёл метки ОТЗЫВЫ:НАЧАЛО и ОТЗЫВЫ:КОНЕЦ в prodvizhenie.html")

    PAGE.write_text(new, encoding="utf-8")
    print(f"\nГотово: {PAGE.name} обновлён")
    print("Дальше: python3 build-review.py, посмотреть на /prodvizhenie-review, потом deploy.sh")


if __name__ == "__main__":
    main()
