#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Собирает страницу подарка «100 заголовков» для сайта.

Зачем: исходник лежит презентацией 1280×720, её делали под PDF. На телефоне
такое читать невозможно, а подарок открывают именно с телефона. Скрипт достаёт
из презентации содержание и раскладывает его в обычную страницу в стиле клуба.

Что делает:
  1. читает 100_заголовков_подарок.html (26 слайдов)
  2. вытаскивает форматы, заголовки и подписи
  3. кладёт PDF в course-site/files/
  4. пишет course-site/podarok.html

Запуск из папки course-site:
    python3 build-podarok.py
"""

import html
import re
import shutil
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Нужна библиотека: pip install beautifulsoup4 --break-system-packages")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "100_заголовков_подарок.html"
PDF_SRC = ROOT / "100_заголовков_подарок.pdf"
PDF_OUT = HERE / "files" / "100-zagolovkov.pdf"
OUT = HERE / "podarok.html"

PIXEL = "1350449057220500"


def parse():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "html.parser")
    intro, formats = [], []
    for sl in soup.select(".slide"):
        pad = sl.select_one(".pad")
        if not pad:
            continue
        lst = pad.select_one(".list")
        kicker = pad.find("div", class_=None)
        big = pad.select_one(".big")
        note = pad.select_one("p")

        if lst:
            rows = [r.select_one(".t").get_text(" ", strip=True)
                    for r in lst.select(".row") if r.select_one(".t")]
            formats.append({
                "kicker": kicker.get_text(" ", strip=True) if kicker else "",
                "title": big.get_text(" ", strip=True) if big else "",
                "rows": rows,
                "note": note.get_text(" ", strip=True) if note else "",
            })
        elif big:
            # вводные слайды: заголовок плюс абзацы
            paras = [p.get_text(" ", strip=True) for p in pad.find_all("p")]
            body = [x for x in paras if len(x) > 25]
            intro.append({
                "title": big.get_text(" ", strip=True),
                "body": body,
                "note": paras[-1] if paras and len(paras[-1]) <= 90 else "",
            })
    return intro, formats


CSS = """
:root{--paper:#F2EAD9;--paper2:#FBF6EC;--card:#FFFDF8;--ink:#171313;--ink2:#4A4340;
  --ink3:#7C736C;--line:#E2D7C2;--wine:#6B2138;--navy:#22314A;--sun:#F5C63A;
  --disp:'Prata',Georgia,serif;--pos:'Oswald',Impact,sans-serif;
  --body:'Onest',-apple-system,sans-serif;--hand:'Marck Script',cursive}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--body);
  font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased;-webkit-text-size-adjust:100%}
.wrap{max-width:720px;margin:0 auto;padding:0 20px 80px}
.top{text-align:center;padding:46px 0 34px}
.top .kick{font-family:var(--pos);font-weight:600;font-size:11px;letter-spacing:.26em;
  text-transform:uppercase;color:var(--wine);margin-bottom:16px}
.top .n{font-family:var(--pos);font-weight:700;font-size:clamp(76px,22vw,150px);
  line-height:.84;color:var(--wine);letter-spacing:-.02em}
.top h1{font-family:var(--disp);font-weight:400;font-size:clamp(27px,7vw,44px);
  line-height:1.1;margin:2px 0 14px}
.top p{font-size:17px;color:var(--ink2);max-width:34ch;margin:0 auto}
.top .from{font-family:var(--hand);font-size:25px;color:var(--navy);margin-top:16px}
.btn{display:inline-flex;align-items:center;gap:9px;background:var(--sun);color:var(--ink);
  text-decoration:none;font-family:var(--pos);font-weight:600;font-size:14px;letter-spacing:.1em;
  text-transform:uppercase;padding:16px 28px;border-radius:999px;margin-top:22px;
  box-shadow:0 8px 22px rgba(23,19,19,.16);transition:transform .18s,box-shadow .18s}
.btn:active{transform:scale(.97)}
.btn.wine{background:var(--wine);color:#F7EFE2}
.intro{background:var(--card);border:1px solid var(--line);padding:24px 22px;margin:0 0 16px;
  box-shadow:0 3px 14px rgba(23,19,19,.05)}
.intro h2{font-family:var(--disp);font-weight:400;font-size:23px;line-height:1.2;margin-bottom:10px}
.intro p{font-size:16px;color:var(--ink2);margin-bottom:9px}
.intro .hand{font-family:var(--hand);font-size:21px;color:var(--wine);margin-top:4px}
.sep{font-family:var(--pos);font-weight:600;font-size:11px;letter-spacing:.24em;
  text-transform:uppercase;color:var(--wine);text-align:center;margin:44px 0 18px}
.fmt{background:var(--card);border:1px solid var(--line);padding:22px 20px 20px;margin:0 0 14px;
  box-shadow:0 3px 14px rgba(23,19,19,.05);position:relative}
.fmt .k{font-family:var(--pos);font-weight:600;font-size:10.5px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--ink3);display:block;margin-bottom:5px}
.fmt h3{font-family:var(--disp);font-weight:400;font-size:24px;line-height:1.15;
  color:var(--wine);margin-bottom:14px}
.fmt ol{list-style:none;counter-reset:h}
.fmt li{counter-increment:h;display:flex;gap:12px;padding:9px 0;border-top:1px solid var(--line);
  font-size:16.5px;line-height:1.45}
.fmt li::before{content:counter(h);font-family:var(--pos);font-weight:600;font-size:12px;
  color:var(--sun);-webkit-text-stroke:.6px var(--wine);flex:none;width:16px;padding-top:3px}
.fmt .note{font-family:var(--hand);font-size:20px;color:var(--navy);margin-top:14px;line-height:1.3}
.fin{background:var(--navy);color:#EFE7DA;padding:34px 24px;margin:46px 0 0;text-align:center}
.fin h2{font-family:var(--disp);font-weight:400;font-size:clamp(24px,6vw,32px);line-height:1.16;margin-bottom:12px}
.fin h2 em{font-style:italic;color:var(--sun)}
.fin p{font-size:16.5px;color:rgba(239,231,218,.86);max-width:38ch;margin:0 auto 4px}
.foot{text-align:center;font-size:13.5px;color:var(--ink3);margin-top:26px}
.foot a{color:var(--wine)}
@media(max-width:520px){body{font-size:16px}.wrap{padding:0 15px 60px}
  .fmt{padding:19px 16px 17px}.intro{padding:20px 17px}}
"""


def build(intro, formats):
    e = html.escape
    p = []
    p.append(f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>100 заголовков · подарок от Малены Покладовой</title>
<meta name="description" content="Сто цепляющих первых строк для Reels, постов и сторис. Двадцать форматов, в каждом по пять готовых вариантов.">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="100 заголовков · подарок от Малены Покладовой">
<meta property="og:image" content="https://malenapocladova.com/images/club/og-club.jpg">
<link rel="icon" href="/images/club/favicon.png">
<link href="https://fonts.googleapis.com/css2?family=Prata&family=Oswald:wght@400;600;700&family=Onest:wght@400;500;600&family=Marck+Script&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <div class="top">
    <div class="kick">Подарок для тех, кто оставил заявку</div>
    <div class="n">100</div>
    <h1>заголовков</h1>
    <p>Цепляющие первые строки для ваших Reels, постов и сторис. Двадцать форматов, в каждом по пять готовых вариантов.</p>
    <div class="from">от Малены Покладовой</div>
    <a class="btn" href="/files/100-zagolovkov.pdf" download>Скачать PDF <span>&darr;</span></a>
  </div>
""")

    for b in intro:
        p.append('  <div class="intro">')
        p.append(f'    <h2>{e(b["title"])}</h2>')
        for line in b["body"]:
            p.append(f"    <p>{e(line)}</p>")
        if b["note"] and b["note"] not in b["body"]:
            p.append(f'    <div class="hand">{e(b["note"])}</div>')
        p.append("  </div>")

    if formats:
        p.append('  <div class="sep">Двадцать форматов, сто строк</div>')
    for f in formats:
        p.append('  <div class="fmt">')
        if f["kicker"]:
            p.append(f'    <span class="k">{e(f["kicker"])}</span>')
        p.append(f'    <h3>{e(f["title"])}</h3>')
        p.append("    <ol>")
        for row in f["rows"]:
            p.append(f"      <li>{e(row)}</li>")
        p.append("    </ol>")
        if f["note"]:
            p.append(f'    <div class="note">{e(f["note"])}</div>')
        p.append("  </div>")

    p.append("""
  <div class="fin">
    <h2>А дальше начинается <em>самое интересное</em></h2>
    <p>Заголовок вытаскивает первые две секунды. Всё остальное решает система: что снимать, когда выкладывать и кто вас поддержит, когда снимать не хочется.</p>
    <p>Ровно это и есть клуб «ПроДвижение». Старт 1 сентября, $19 в месяц.</p>
    <a class="btn" href="/prodvizhenie?utm_source=podarok&utm_medium=pdf&utm_campaign=100-zagolovkov">Посмотреть клуб</a>
  </div>

  <div class="foot">
    Малена Покладова · <a href="/prodvizhenie">клуб «ПроДвижение»</a><br>
    Материал для личного использования. Пересылать можно, продавать нельзя.
  </div>

</div>
""")

    p.append(f"""
<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{PIXEL}');fbq('track','PageView');
fbq('trackCustom','GiftOpened',{{content_name:'100 заголовков'}});
document.querySelectorAll('a[href$=".pdf"]').forEach(function(a){{
  a.addEventListener('click',function(){{fbq('trackCustom','GiftDownload')}});
}});
</script>
</body>
</html>
""")
    return "\n".join(p)


def main():
    if not SRC.exists():
        sys.exit(f"Не нашёл исходник: {SRC.name}")
    intro, formats = parse()
    print(f"Вводных блоков: {len(intro)} · форматов: {len(formats)} · "
          f"заголовков: {sum(len(f['rows']) for f in formats)}")

    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    if PDF_SRC.exists():
        shutil.copy2(PDF_SRC, PDF_OUT)
        print(f"PDF скопирован: files/{PDF_OUT.name} ({PDF_OUT.stat().st_size // 1024} КБ)")
    else:
        print("PDF не найден, страница соберётся без файла для скачивания")

    OUT.write_text(build(intro, formats), encoding="utf-8")
    print(f"Готово: {OUT.name} ({OUT.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()
