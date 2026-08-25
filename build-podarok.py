#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Публикует подарок «100 заголовков» на сайте, сохраняя авторский дизайн.

Исходник это презентация: 26 слайдов по 1280×720, картинки вшиты в base64,
файл весит 3,3 МБ. Своя вёрстка тут не нужна, дизайн уже сделан. Задача другая:
довезти его до телефона так, чтобы он открывался быстро и читался.

Что делает скрипт:
  1. вынимает картинки из base64 в отдельные файлы, страница худеет до ~60 КБ
  2. на широком экране оставляет слайды как есть, авторский макет не трогает
  3. на телефоне отключает масштабирование слайда и распускает его по высоте:
     те же цвета, шрифты, линованная бумага и красное поле, но текст читаемого
     размера. Наклейки и печати стоят на пиксельных координатах и на узком
     экране разъезжаются, поэтому там они прячутся
  4. добавляет пиксель Meta, кнопку скачивания PDF и метатеги
  5. кладёт PDF в course-site/files/

Запуск из папки course-site:
    python3 build-podarok.py
"""

import base64
import hashlib
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "100_заголовков_подарок.html"
PDF_SRC = ROOT / "100_заголовков_подарок.pdf"
PDF_OUT = HERE / "files" / "100-zagolovkov.pdf"
IMG_DIR = HERE / "images" / "club" / "podarok"
OUT = HERE / "podarok.html"

PIXEL = "1350449057220500"
PDF_URL = "/files/100-zagolovkov.pdf"

EXT = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "webp": "webp", "gif": "gif", "svg+xml": "svg"}


def extract_images(html: str) -> tuple[str, int, int]:
    """base64 → файлы. Одинаковые картинки складываются в один файл."""
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    seen: dict[str, str] = {}
    saved_bytes = 0

    def repl(m: re.Match) -> str:
        nonlocal saved_bytes
        kind, data = m.group(1), m.group(2)
        key = hashlib.sha1(data.encode()).hexdigest()
        if key in seen:
            return seen[key]
        try:
            raw = base64.b64decode(data)
        except Exception:
            return m.group(0)
        name = f"p-{key[:10]}.{EXT.get(kind, 'png')}"
        (IMG_DIR / name).write_bytes(raw)
        saved_bytes += len(raw)
        url = f"/images/club/podarok/{name}"
        seen[key] = url
        return url

    out = re.sub(r"data:image/([a-z+]+);base64,([A-Za-z0-9+/=]+)", repl, html)
    return out, len(seen), saved_bytes


# Слайды на телефоне не масштабируем, а распускаем: масштаб делает текст
# нечитаемым, 32 пикселя при коэффициенте 0.3 превращаются в девять.
MOBILE_CSS = """
/* ── адаптив: авторский макет на широком экране, читаемый на телефоне ── */
@media (max-width:899px){
  /* Обложка сдвинута влево на 160 пикселей: на широком экране это часть композиции,
     на телефоне заголовок уезжал за край. Сдвиг и два кегля вынесены в переменные,
     чтобы обнулить их здесь и не трогать макет на компьютере. */
  :root{--pull:0px;--h2:40px;--sub:16.5px}
  body{padding:0!important;background:var(--paper2)}
  .slide{width:100%!important;height:auto!important;min-height:0!important;
    transform:none!important;margin:0 0 12px!important;overflow:hidden!important}
  .pad{padding:56px 20px 52px!important}
  .ruled .pad{padding-left:34px!important}
  .ruled::after{left:20px!important}
  .run,.foot{left:20px!important;right:20px!important;font-size:9px!important;
    letter-spacing:.14em!important}
  .ruled .run,.ruled .foot{left:34px!important}
  .run{top:20px!important}
  .foot{bottom:18px!important}
  .big{font-size:32px!important}
  .big.sm{font-size:29px!important}
  .big.xs{font-size:26px!important}
  .lede{font-size:16px!important;max-width:none!important}
  .hand{font-size:19px!important}
  .list{gap:13px!important;margin-top:18px!important;justify-content:flex-start!important}
  .row{gap:12px!important}
  .row .n{min-width:22px!important;font-size:12px!important;padding-top:3px!important}
  .row .t{font-size:18px!important;line-height:1.3!important}
  .errs,.steps{grid-template-columns:1fr!important;gap:12px!important;margin-top:20px!important}
  .err{padding:16px 18px!important}
  .err p{font-size:16px!important}
  .st{padding:18px 18px 20px!important}
  .st p{font-size:15.5px!important}
  .st .num{width:36px!important;height:36px!important;font-size:17px!important;margin-bottom:12px!important}
  .cover .pad{padding-top:56px!important;padding-bottom:54px!important}
  /* без !important: второй заголовок держит свой кегль через переменную --h2 */
  .cover .huge{font-size:56px}
  .cover .sub{margin-top:14px!important;max-width:none!important}
  .cover .from{font-size:24px!important;margin-top:14px!important}
  /* полароид лежит в разметке первым, на телефоне он закрывал бы весь первый экран */
  .ph{order:9!important;margin:16px 0 0!important}
  .cta{font-size:15px!important;padding:16px 22px!important;margin-top:22px!important;
    align-self:stretch!important;justify-content:center!important}
  .small{font-size:10px!important}
  /* наклейки, скотч и печати стоят на пиксельных координатах: на узком экране
     они легли бы поверх текста, поэтому здесь их не показываем */
  .stk,.tape,.seal{display:none!important}
  .ph{position:static!important;width:100%!important;height:auto!important;
    transform:none!important;margin:18px 0 0!important;padding:9px!important}
  .ph img{height:auto!important;aspect-ratio:3/4;flex:none!important}
  .ph .cap{font-size:19px!important}
}

/* кнопка скачивания, висит поверх страницы */
.dl{position:fixed;right:18px;bottom:18px;z-index:50;display:inline-flex;align-items:center;gap:9px;
  background:var(--sun);color:var(--ink);text-decoration:none;font-family:var(--pos);font-weight:600;
  font-size:12px;letter-spacing:.14em;text-transform:uppercase;padding:14px 22px;border-radius:999px;
  box-shadow:0 10px 26px rgba(23,19,19,.28);transition:transform .18s}
.dl:active{transform:scale(.96)}
@media (max-width:899px){.dl{right:12px;bottom:12px;font-size:11px;padding:12px 18px}}
@media print{.dl{display:none}}
"""

# На узком экране масштабирование выключаем совсем, там работает адаптив.
FIT_JS = """
function fit(){
  var w=document.documentElement.clientWidth;
  var slides=document.querySelectorAll('.slide');
  if(w>=900&&w<1340){
    var s=(w-20)/1280;
    slides.forEach(function(el){
      el.style.transformOrigin='top left';
      el.style.transform='scale('+s+')';
      el.style.marginBottom=(720*s-720+14)+'px';
    });
  }else{
    slides.forEach(function(el){el.style.transform='';el.style.marginBottom='';});
  }
}
fit();addEventListener('resize',fit);
"""

HEAD_ADD = f"""
<meta name="description" content="Сто цепляющих первых строк для Reels, постов и сторис. Двадцать форматов, в каждом по пять готовых вариантов.">
<meta property="og:title" content="100 заголовков · подарок от Малены Покладовой">
<meta property="og:image" content="https://malenapocladova.com/images/club/og-club-v2.jpg">
<link rel="icon" href="/images/club/favicon.png">
<style>{MOBILE_CSS}</style>
"""

BODY_ADD = f"""
<a class="dl" href="{PDF_URL}" download>Скачать PDF &darr;</a>
<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{PIXEL}');fbq('track','PageView');
fbq('trackCustom','GiftOpened',{{content_name:'100 заголовков'}});
document.querySelector('.dl').addEventListener('click',function(){{fbq('trackCustom','GiftDownload')}});
document.querySelectorAll('a[href*="prodvizhenie"]').forEach(function(a){{
  if(!a.href.includes('utm_')) a.href += (a.href.includes('?')?'&':'?')+'utm_source=podarok&utm_medium=gift&utm_campaign=100-zagolovkov';
  a.addEventListener('click',function(){{fbq('trackCustom','GiftToClub')}});
}});
</script>
"""


def main():
    if not SRC.exists():
        sys.exit(f"Не нашёл исходник: {SRC.name}")

    html = SRC.read_text(encoding="utf-8")
    before = len(html.encode())

    html, n_img, img_bytes = extract_images(html)
    print(f"Картинок вынуто: {n_img} · {img_bytes // 1024} КБ в отдельных файлах")

    # ленивую загрузку картинкам, кроме тех, что на первом экране
    html = html.replace('<img class="stk"', '<img loading="lazy" class="stk"')

    # Жёсткие пиксели обложки переводим в переменные, чтобы адаптив мог их обнулить,
    # а на компьютере всё осталось ровно как задумано.
    pulls = html.count("margin-left:-160px")
    html = html.replace("margin-left:-160px", "margin-left:var(--pull,-160px)")
    html = html.replace("font-size:106px", "font-size:var(--h2,106px)")
    html = html.replace("font-size:30px;max-width:19ch", "font-size:var(--sub,30px);max-width:19ch")
    print(f"Сдвигов обложки переведено в переменные: {pulls}")

    # свой обработчик масштаба вместо авторского
    html = re.sub(r"<script>.*?</script>", f"<script>{FIT_JS}</script>", html, count=1, flags=re.S)

    html = html.replace("</head>", HEAD_ADD + "</head>", 1)
    html = html.replace("</body>", BODY_ADD + "</body>", 1)

    OUT.write_text(html, encoding="utf-8")

    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    if PDF_SRC.exists():
        shutil.copy2(PDF_SRC, PDF_OUT)
        print(f"PDF: files/{PDF_OUT.name} ({PDF_OUT.stat().st_size // 1024} КБ)")

    after = OUT.stat().st_size
    slides = html.count('class="slide')
    rows = html.count('<div class="t">')
    print(f"Слайдов: {slides} · строк-заголовков: {rows}")
    print(f"Страница: {before // 1024} КБ → {after // 1024} КБ")
    print(f"Готово: {OUT.name}")


if __name__ == "__main__":
    main()
