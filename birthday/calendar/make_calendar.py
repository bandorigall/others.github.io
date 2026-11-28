# -*- coding: utf-8 -*-
"""월별 생일 캘린더 생성기 (캐릭터 + 성우).
사용: python make_calendar.py 10   → october.json 을 읽어 october.html 생성
데이터: <month>.json (gather 단계에서 만든 것), 색은 ../../../characters.json 에서 담당 캐릭터 색을 따라감.
"""
import calendar, datetime, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MONTHS = {10: "october"}
YEAR = 2026

m = int(sys.argv[1]) if len(sys.argv) > 1 else 10
slug = MONTHS[m]
items = json.load(open(os.path.join(HERE, slug + ".json"), encoding="utf-8"))
chars = json.load(open(os.path.join(ROOT, "characters.json"), encoding="utf-8"))["characters"]
color_by_name = {c["name"]: c["color"] for c in chars}
for it in items:
    # 얼굴 크롭본(코 = 정중앙, 320px 정사각) 사용 — img/face/
    it["img"] = "img/face/" + os.path.splitext(os.path.basename(it["img"]))[0] + ".jpg"
    if it["type"] == "va":
        it["color"] = color_by_name.get(it["role"], "#c9b6e4")

by_day = {}
for it in items:
    by_day.setdefault(int(it["date"][3:]), []).append(it)

e = html.escape
cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
weeks = cal.monthdayscalendar(YEAR, m)


def face(it, cls=""):
    tag = "성우" if it["type"] == "va" else ""
    return (f'<span class="face {it["type"]} {cls}" style="--c:{e(it["color"])};background-image:url(\'{e(it["img"])}\')" '
            f'title="{e(it["name"])}">{f"<i>{tag}</i>" if tag else ""}</span>')


cells = []
for w in weeks:
    for i, d in enumerate(w):
        if not d:
            cells.append('<div class="cell empty"></div>')
            continue
        its = by_day.get(d, [])
        wd = " sun" if i == 0 else (" sat" if i == 6 else "")
        has = " has" if its else ""
        faces = "".join(face(it) for it in its)
        names = "".join(f'<span class="nm">{e(it["name"])}</span>' for it in its)
        attr = f' tabindex="0" role="button" data-day="{d}" aria-label="{m}월 {d}일 생일 {len(its)}명"' if its else ""
        cells.append(f'<div class="cell{wd}{has}"{attr}><b class="dn">{d}</b><div class="faces n{min(len(its), 3)}">{faces}</div><div class="nms">{names}</div></div>')


def card(it):
    sub = (f'{e(it["role"])} 역 · {e(it["band"])}' if it["type"] == "va" else e(it["band"]))
    x = (f' · <a href="https://x.com/{e(it["x"])}" target="_blank" rel="noopener noreferrer">@{e(it["x"])}</a>' if it.get("x") else "")
    kind = "성우" if it["type"] == "va" else "캐릭터"
    return (f'<li class="card" style="--c:{e(it["color"])}"><span class="face big {it["type"]}" style="--c:{e(it["color"])};background-image:url(\'{e(it["img"])}\')"></span>'
            f'<div><div class="cdate">{m}월 {int(it["date"][3:])}일 <span class="kind {it["type"]}">{kind}</span></div>'
            f'<div class="cname">{e(it["name"])}{" <small>" + e(it["ja"]) + "</small>" if it.get("ja") else ""}</div><div class="csub">{sub}{x}</div></div></li>')


lists = "".join(card(it) for it in items)
n_char = sum(1 for it in items if it["type"] == "char")
n_va = len(items) - n_char
title_month = datetime.date(YEAR, m, 1).strftime("%B").upper()

page = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>뱅드림 {m}월 생일 캘린더</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Playfair+Display:ital,wght@1,700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fbf6f1;--ink:#3b2f3a;--muted:#8a7b86;--line:#eadfd8;--accent:#e0607e;--paper:#fffdfb}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:'Gowun Dodum',system-ui,sans-serif;
  background-image:radial-gradient(circle at 10% 0%,#f9e3e8 0,transparent 40%),radial-gradient(circle at 100% 100%,#ece4f6 0,transparent 45%)}}
.wrap{{max-width:1040px;margin:0 auto;padding:28px 16px 56px}}
header{{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:18px}}
.mon{{font-family:'Playfair Display',serif;font-style:italic;font-size:clamp(2.6rem,9vw,4.6rem);line-height:.9;color:var(--accent);letter-spacing:-1px}}
.mon small{{display:block;font-family:'Gowun Dodum';font-style:normal;font-size:1rem;color:var(--muted);letter-spacing:0;margin-top:8px}}
.legend{{display:flex;gap:14px;font-size:.9rem;color:var(--muted);align-items:center}}
.legend .face{{width:22px;height:22px}}
.sheet{{background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:14px;box-shadow:0 10px 30px rgba(120,80,90,.08)}}
.dow,.grid{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px}}
.dow div{{text-align:center;font-size:.8rem;color:var(--muted);padding:4px 0 8px;letter-spacing:1px}}
.dow div:first-child{{color:#d0566f}} .dow div:last-child{{color:#5875c9}}
.cell{{position:relative;min-height:118px;border-radius:14px;padding:6px;background:#fff;border:1px solid var(--line);display:flex;flex-direction:column;align-items:center;gap:4px;transition:transform .15s,box-shadow .15s}}
.cell.empty{{background:transparent;border:none}}
.dn{{align-self:flex-start;font-size:.85rem;font-weight:400;color:var(--muted)}}
.cell.sun .dn{{color:#d0566f}} .cell.sat .dn{{color:#5875c9}}
.cell.has{{cursor:pointer;background:linear-gradient(180deg,#fff 0,#fff7f8 100%)}}
.cell.has:hover,.cell.has:focus-visible,.cell.sel{{transform:translateY(-2px);box-shadow:0 8px 18px rgba(224,96,126,.18);outline:none;border-color:#f1b8c5}}
.cell.today{{border:2px solid var(--accent)}}
.faces{{display:flex;justify-content:center;flex-wrap:wrap;gap:4px}}
.face{{position:relative;display:inline-block;width:54px;height:54px;border-radius:50%;background-size:cover;background-position:center;background-color:#f3eef0;
  border:3px solid var(--c);box-shadow:0 0 0 2px #fff,0 3px 8px rgba(0,0,0,.08)}}
.face i{{position:absolute;right:-4px;bottom:-4px;font-style:normal;font-size:.6rem;background:var(--ink);color:#fff;border-radius:8px;padding:1px 4px}}
.faces.n2 .face{{width:44px;height:44px}} .faces.n3 .face{{width:36px;height:36px}}
.nms{{display:flex;flex-direction:column;align-items:center;font-size:.72rem;line-height:1.25;text-align:center;word-break:keep-all}}
h2{{font-size:1.05rem;margin:28px 4px 10px;color:var(--muted);font-weight:400}}
.list{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}}
.card{{display:flex;gap:12px;align-items:center;background:#fff;border:1px solid var(--line);border-left:6px solid var(--c);border-radius:14px;padding:10px 12px;scroll-margin-top:16px}}
.card.hl{{box-shadow:0 0 0 3px #f6c4cf}}
.face.big{{width:64px;height:64px;flex:none}}
.cdate{{font-size:.8rem;color:var(--muted)}}
.kind{{font-size:.7rem;padding:1px 6px;border-radius:8px;background:#f1e8ee;margin-left:4px}}
.kind.va{{background:var(--ink);color:#fff}}
.cname{{font-size:1.05rem;margin:2px 0}} .cname small{{color:var(--muted);font-size:.78rem}}
.csub{{font-size:.82rem;color:var(--muted)}} .csub a{{color:var(--accent)}}
footer{{margin-top:26px;font-size:.75rem;color:var(--muted);text-align:center}}
@media (max-width:640px){{
  .wrap{{padding:18px 10px 40px}} .sheet{{padding:8px;border-radius:16px}}
  .dow,.grid{{gap:3px}} .cell{{min-height:74px;padding:3px;border-radius:9px}}
  .dn{{font-size:.7rem}} .face{{width:34px;height:34px;border-width:2px}}
  .faces.n2 .face{{width:26px;height:26px}} .faces.n3 .face{{width:22px;height:22px}}
  .face i{{display:none}} .nms{{display:none}}
}}
</style></head><body><div class="wrap">
<header><div class="mon">{title_month}<small>{YEAR}</small></div></header>
<div class="sheet"><div class="dow"><div>SUN</div><div>MON</div><div>TUE</div><div>WED</div><div>THU</div><div>FRI</div><div>SAT</div></div>
<div class="grid">{''.join(cells)}</div></div>
<ul class="list" style="margin-top:24px">{lists}</ul>
</div>
<script>
(function(){{
  var t=new Date(); if(t.getFullYear()=={YEAR}&&t.getMonth()+1=={m}){{var c=document.querySelector('.cell[data-day="'+t.getDate()+'"]')||[].find.call(document.querySelectorAll('.cell:not(.empty)'),function(x){{return x.querySelector('.dn').textContent==t.getDate()}});if(c)c.classList.add('today');}}
  var cards=[].slice.call(document.querySelectorAll('.card'));
  function go(day){{
    document.querySelectorAll('.cell.sel').forEach(function(x){{x.classList.remove('sel')}});
    var cell=document.querySelector('.cell[data-day="'+day+'"]'); if(cell)cell.classList.add('sel');
    var first=null; cards.forEach(function(k){{var on=k.querySelector('.cdate').textContent.indexOf('{m}월 '+day+'일')===0;k.classList.toggle('hl',on);if(on&&!first)first=k;}});
    if(first)first.scrollIntoView({{behavior:'smooth',block:'center'}});
  }}
  document.querySelectorAll('.cell.has').forEach(function(c){{
    c.addEventListener('click',function(){{go(c.dataset.day)}});
    c.addEventListener('keydown',function(ev){{if(ev.key==='Enter'||ev.key===' '){{ev.preventDefault();go(c.dataset.day)}}}});
  }});
}})();
</script></body></html>"""
open(os.path.join(HERE, slug + ".html"), "w", encoding="utf-8").write(page)
print("written", slug + ".html", len(items), "items")
