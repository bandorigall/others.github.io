# -*- coding: utf-8 -*-
"""
guitars.json -> index.html 생성기.
데이터는 반드시 guitars.json 만 수정하고 이 스크립트를 다시 돌릴 것.

레이아웃: 밴드별 썸네일 그리드(캐릭터 얼굴 + 기타 사진 + 모델명)
          → 카드 클릭 시 모달로 스펙/가격/판매처 전체 표시.

이미지 규칙:
  - char_img   : BanG Dream! 공식 사이트 이미지 URL (원격)
  - guitar_img : img/{id}.jpg 로컬 파일. 없으면 자동으로 플레이스홀더 표시.
사용법: python generate_html.py
"""
import json
import html
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "guitars.json"
OUT = BASE / "index.html"


def e(s):
    return html.escape(str(s), quote=True)


def render_thumb(g, band):
    """그리드에 들어가는 작은 카드."""
    badge = "공식" if g.get("official_model") else "추정"
    badge_cls = "official" if g.get("official_model") else "fan"
    return f"""
        <button class="thumb" data-id="{e(g['id'])}" type="button">
          <span class="thumb-imgs">
            <span class="ti char"><img loading="lazy" src="{e(g['char_img'])}" alt="{e(g['char_ko'])}"
                 onerror="this.closest('.ti').classList.add('noimg')"></span>
            <span class="ti gt"><img loading="lazy" src="{e(g['guitar_img'])}" alt="{e(g['model'])}"
                 onerror="this.closest('.ti').classList.add('noimg')"></span>
          </span>
          <span class="thumb-body">
            <span class="thumb-name">{e(g['char_ko'])}</span>
            <span class="thumb-model"><b>{e(g['brand'])}</b> {e(g['model'])}</span>
            <span class="badge {badge_cls}">{badge}</span>
          </span>
        </button>"""


def render_band(b):
    thumbs = "".join(render_thumb(g, b) for g in b["guitarists"])
    return f"""
    <section class="band" id="{e(b['id'])}" style="--accent:{e(b['color'])}">
      <h2 class="band-title">
        <span class="dot"></span>
        <span class="ko">{e(b['name_ko'])}</span>
        <span class="orig">{e(b['name'])}</span>
        <a class="band-link" href="{e(b['official'])}" target="_blank" rel="noopener">공식 ↗</a>
      </h2>
      <div class="grid">{thumbs}</div>
    </section>"""


def render_nav(bands):
    items = "".join(
        f'<a href="#{e(b["id"])}" style="--accent:{e(b["color"])}">{e(b["name_ko"])}</a>'
        for b in bands
    )
    return f'<nav class="bandnav">{items}</nav>'


def detail_payload(bands):
    """모달에서 쓸 상세 데이터만 추려 JS로 넘긴다."""
    out = {}
    for b in bands:
        for g in b["guitarists"]:
            out[g["id"]] = {
                "band": b["name_ko"],
                "bandOrig": b["name"],
                "color": b["color"],
                "char": g["char_ko"],
                "charJp": g["char"],
                "part": g["part"],
                "brand": g["brand"],
                "model": g["model"],
                "official": bool(g.get("official_model")),
                "desc": g["desc"],
                "specs": g.get("specs") or {},
                "variants": g.get("variants") or [],
                "shops": g.get("shops") or [],
                "charImg": g["char_img"],
                "guitarImg": g["guitar_img"],
                "credit": g.get("img_credit"),
            }
    return out


CSS = """
:root{
  --bg:#0f1115; --panel:#171a21; --panel2:#1d212a; --line:#2a2f3a;
  --tx:#e8eaf0; --tx2:#a3a9b8; --tx3:#6e7686; --shadow:0 12px 40px rgba(0,0,0,.55);
}
@media (prefers-color-scheme: light){
  :root{ --bg:#f6f7fa; --panel:#fff; --panel2:#f0f2f7; --line:#e2e5ec;
         --tx:#1a1d24; --tx2:#525a6b; --tx3:#8b93a3; --shadow:0 12px 40px rgba(20,25,40,.18); }
}
:root[data-theme="dark"]{
  --bg:#0f1115; --panel:#171a21; --panel2:#1d212a; --line:#2a2f3a;
  --tx:#e8eaf0; --tx2:#a3a9b8; --tx3:#6e7686; --shadow:0 12px 40px rgba(0,0,0,.55);
}
:root[data-theme="light"]{
  --bg:#f6f7fa; --panel:#fff; --panel2:#f0f2f7; --line:#e2e5ec;
  --tx:#1a1d24; --tx2:#525a6b; --tx3:#8b93a3; --shadow:0 12px 40px rgba(20,25,40,.18);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
  font-family:"Pretendard","Noto Sans KR",-apple-system,"Segoe UI",sans-serif;
  line-height:1.6;-webkit-text-size-adjust:100%}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px 80px}
header.top{padding:52px 0 24px;border-bottom:1px solid var(--line);margin-bottom:20px}
header.top h1{margin:0 0 8px;font-size:2rem;letter-spacing:-.02em}
header.top p.sub{margin:0;color:var(--tx2)}
.updated{font-size:.8rem;color:var(--tx3);margin-top:6px}
header.top p.note{margin:14px 0 0;font-size:.82rem;color:var(--tx3);
  background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.bandnav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 30px;
  position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0}
.bandnav a{font-size:.82rem;text-decoration:none;color:var(--tx2);
  border:1px solid var(--line);border-radius:999px;padding:5px 12px;background:var(--panel);transition:.15s}
.bandnav a:hover{color:var(--accent);border-color:var(--accent)}
.band{margin:0 0 40px;scroll-margin-top:64px}
.band-title{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  font-size:1.3rem;margin:0 0 14px;letter-spacing:-.01em}
.band-title .dot{width:12px;height:12px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 22%,transparent)}
.band-title .orig{font-size:.84rem;color:var(--tx3);font-weight:400}
.band-link{margin-left:auto;font-size:.78rem;color:var(--tx3);text-decoration:none}
.band-link:hover{color:var(--accent)}

/* ---- 썸네일 그리드 ---- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px}
.thumb{all:unset;cursor:pointer;display:flex;flex-direction:column;
  background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--accent);
  border-radius:13px;overflow:hidden;transition:transform .12s,border-color .12s,box-shadow .12s}
.thumb:hover,.thumb:focus-visible{transform:translateY(-3px);box-shadow:var(--shadow);
  border-color:color-mix(in srgb,var(--accent) 60%,var(--line))}
.thumb-imgs{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
.ti{position:relative;background:var(--panel2);aspect-ratio:3/4;overflow:hidden;display:block}
.ti img{width:100%;height:100%;object-fit:cover;object-position:top center;display:block}
.ti.gt img{object-fit:contain;object-position:center;padding:6px}
.ti.noimg img{display:none}
.ti.noimg::after{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  font-size:.7rem;color:var(--tx3);text-align:center;padding:6px;line-height:1.3}
.ti.char.noimg::after{content:"이미지\\A불러오기 실패";white-space:pre}
.ti.gt.noimg::after{content:"기타 사진\\A없음";white-space:pre}
.thumb-body{padding:11px 12px 13px;display:flex;flex-direction:column;gap:3px}
.thumb-name{font-size:.95rem;font-weight:700}
.thumb-model{font-size:.76rem;color:var(--tx2);line-height:1.35;word-break:break-word}
.thumb-model b{color:var(--accent)}
.badge{align-self:flex-start;margin-top:5px;font-size:.68rem;padding:2px 8px;border-radius:999px}
.badge.official{background:color-mix(in srgb,var(--accent) 18%,transparent);color:var(--accent);
  border:1px solid color-mix(in srgb,var(--accent) 45%,transparent)}
.badge.fan{background:var(--panel2);color:var(--tx3);border:1px solid var(--line)}

/* ---- 모달 ---- */
.backdrop{position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(3px);
  display:none;align-items:center;justify-content:center;padding:20px;z-index:50}
.backdrop.on{display:flex}
.modal{background:var(--panel);border:1px solid var(--line);border-top:4px solid var(--accent);
  border-radius:16px;box-shadow:var(--shadow);max-width:840px;width:100%;
  max-height:88vh;overflow-y:auto;position:relative}
.modal-close{position:sticky;float:right;top:10px;right:10px;margin:10px 12px 0 0;
  all:unset;cursor:pointer;width:32px;height:32px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  background:var(--panel2);color:var(--tx2);font-size:1.1rem;z-index:2}
.modal-close:hover{color:var(--accent)}
.modal-in{padding:22px 24px 26px}
.m-head{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;margin-bottom:16px}
.m-face{width:96px;aspect-ratio:3/4;border-radius:10px;overflow:hidden;background:var(--panel2);flex:none}
.m-face img{width:100%;height:100%;object-fit:cover;object-position:top center}
.m-who{min-width:0;flex:1}
.m-band{font-size:.76rem;color:var(--accent);font-weight:700;letter-spacing:.02em}
.m-who h3{margin:2px 0 2px;font-size:1.45rem;letter-spacing:-.01em}
.m-jp{margin:0;font-size:.82rem;color:var(--tx3)}
.part{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:5px;
  background:var(--panel2);color:var(--tx2);font-size:.72rem}
.m-model{margin:10px 0 0;font-size:1.05rem;font-weight:700;word-break:break-word}
.m-model b{color:var(--accent)}
.m-shot{width:100%;max-height:320px;object-fit:contain;background:var(--panel2);
  border:1px solid var(--line);border-radius:12px;margin:0 0 16px;display:block;padding:8px}
.m-shot.noimg{display:flex;align-items:center;justify-content:center;min-height:120px;
  color:var(--tx3);font-size:.82rem;margin-bottom:16px;border:1px dashed var(--line)}
.credit{margin:-8px 0 16px;font-size:.74rem;color:var(--tx3);text-align:right}
.credit a{color:var(--tx3)}
.credit a:hover{color:var(--accent)}
.m-desc{margin:0 0 18px;font-size:.9rem;color:var(--tx2)}
h4.sec{margin:20px 0 8px;font-size:.76rem;letter-spacing:.06em;color:var(--tx3);text-transform:uppercase}
.specs{margin:0;border-top:1px solid var(--line)}
.spec-row{display:grid;grid-template-columns:96px 1fr;gap:12px;
  padding:8px 0;border-bottom:1px solid var(--line);font-size:.86rem}
.spec-row dt{color:var(--tx3);margin:0}
.spec-row dd{margin:0;word-break:break-word}
.tbl-wrap{overflow-x:auto}
.variants{width:100%;border-collapse:collapse;font-size:.85rem;min-width:320px}
.variants th{text-align:left;color:var(--tx3);font-weight:500;font-size:.76rem;
  padding:5px 0;border-bottom:1px solid var(--line)}
.variants td{padding:7px 0;border-bottom:1px solid var(--line);vertical-align:top}
.variants td.price{text-align:right;white-space:nowrap;color:var(--accent);font-weight:700;padding-left:12px}
.empty{font-size:.85rem;color:var(--tx3);margin:0}
.shops{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:7px}
.shops a{font-size:.8rem;text-decoration:none;color:var(--tx2);background:var(--panel2);
  border:1px solid var(--line);border-radius:8px;padding:5px 11px;display:inline-block}
.shops a:hover{color:var(--accent);border-color:var(--accent)}
footer{border-top:1px solid var(--line);padding-top:18px;color:var(--tx3);font-size:.8rem}
@media (max-width:520px){
  .grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
  header.top h1{font-size:1.55rem}
  .modal-in{padding:18px 16px 22px}
  .spec-row{grid-template-columns:80px 1fr}
  .m-face{width:76px}
}
"""

JS = """
const DATA = __DATA__;
const bd = document.getElementById('bd');
const mo = document.getElementById('mo');
let lastFocus = null;

function row(k,v){return '<div class="spec-row"><dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd></div>';}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

function open(id){
  const d = DATA[id]; if(!d) return;
  lastFocus = document.activeElement;
  const specs = Object.keys(d.specs).length
    ? '<dl class="specs">'+Object.entries(d.specs).map(([k,v])=>row(k,v)).join('')+'</dl>' : '';
  const vars = d.variants.length
    ? '<div class="tbl-wrap"><table class="variants"><thead><tr><th>모델 / 사양</th><th>가격</th></tr></thead><tbody>'
      + d.variants.map(v=>'<tr><td>'+esc(v.name)+'</td><td class="price">'+esc(v.price)+'</td></tr>').join('')
      + '</tbody></table></div>'
    : '<p class="empty">판매 중인 모델 정보 없음</p>';
  const shops = d.shops.length
    ? '<ul class="shops">'+d.shops.map(s=>'<a href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.name)+'</a>').join('')+'</ul>'
    : '';
  const badge = d.official
    ? '<span class="badge official">공식 콜라보 모델</span>'
    : '<span class="badge fan">비공식 / 추정</span>';
  mo.style.setProperty('--accent', d.color);
  mo.querySelector('.modal-in').innerHTML =
    '<div class="m-head">'
    + '<div class="m-face"><img src="'+esc(d.charImg)+'" alt="'+esc(d.char)+'" onerror="this.style.display=\\'none\\'"></div>'
    + '<div class="m-who"><div class="m-band">'+esc(d.band)+' · '+esc(d.bandOrig)+'</div>'
    + '<h3>'+esc(d.char)+'</h3>'
    + '<p class="m-jp">'+esc(d.charJp)+'<span class="part">'+esc(d.part)+'</span></p>'
    + '<p class="m-model"><b>'+esc(d.brand)+'</b> '+esc(d.model)+'</p>'
    + '<div style="margin-top:8px">'+badge+'</div></div></div>'
    + (d.guitarImg
        ? '<img class="m-shot" src="'+esc(d.guitarImg)+'" alt="'+esc(d.model)+'"'
          + ' onerror="this.replaceWith(Object.assign(document.createElement(\\'div\\'),'
          + '{className:\\'m-shot noimg\\',textContent:\\'기타 사진 없음\\'}))">'
        : '<div class="m-shot noimg">모델이 특정되지 않아 사진 없음</div>')
    + (d.credit
        ? '<p class="credit">사진: <a href="'+esc(d.credit.url)+'" target="_blank" rel="noopener">'
          + esc(d.credit.text)+'</a></p>' : '')
    + '<p class="m-desc">'+esc(d.desc)+'</p>'
    + (specs ? '<h4 class="sec">스펙</h4>'+specs : '')
    + '<h4 class="sec">가격</h4>'+vars
    + (shops ? '<h4 class="sec">공식 / 판매처</h4>'+shops : '');
  bd.classList.add('on');
  document.body.style.overflow='hidden';
  mo.querySelector('.modal-close').focus();
}
function close(){
  bd.classList.remove('on');
  document.body.style.overflow='';
  if(lastFocus) lastFocus.focus();
}
document.querySelectorAll('.thumb').forEach(t=>t.addEventListener('click',()=>open(t.dataset.id)));
bd.addEventListener('click',ev=>{ if(ev.target===bd) close(); });
mo.querySelector('.modal-close').addEventListener('click',close);
document.addEventListener('keydown',ev=>{ if(ev.key==='Escape' && bd.classList.contains('on')) close(); });
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{subtitle}">
<style>{css}</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <h1>{title}</h1>
  <p class="sub">{subtitle}</p>
  <p class="updated">최종 갱신: {updated} · 카드를 누르면 상세 스펙·가격·판매처가 열립니다</p>
  <p class="note">{note}</p>
</header>
{nav}
{bands}
<footer>
  데이터 출처: ESP GUITARS 공식, SCHECTER 재팬, .strandberg*(키쿠타니 뮤직), Ibanez / PRS / Fender 공식,
  BanG Dream! 공식 사이트, 나무위키.<br>
  캐릭터 이미지는 BanG Dream! 공식 사이트에서 불러옵니다. 비영리 팬 페이지이며 상표·이미지 권리는 각 권리자에게 있습니다.
</footer>
</div>

<div class="backdrop" id="bd" role="dialog" aria-modal="true">
  <div class="modal" id="mo">
    <button class="modal-close" type="button" aria-label="닫기">✕</button>
    <div class="modal-in"></div>
  </div>
</div>

<script>{js}</script>
<script src="nav.js"></script>
</body>
</html>
"""


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    meta = data["meta"]
    bands = data["bands"]
    js = JS.replace(
        "__DATA__", json.dumps(detail_payload(bands), ensure_ascii=False)
    )
    out = TEMPLATE.format(
        title=e(meta["title"]),
        subtitle=e(meta["subtitle"]),
        updated=e(meta["updated"]),
        note=e(meta["note"] + " " + meta.get("img_note", "")),
        css=CSS,
        nav=render_nav(bands),
        bands="".join(render_band(b) for b in bands),
        js=js,
    )
    OUT.write_text(out, encoding="utf-8")
    n = sum(len(b["guitarists"]) for b in bands)
    missing = [
        g["id"] for b in bands for g in b["guitarists"]
        if not (BASE / g["guitar_img"]).exists()
    ]
    print(f"OK -> {OUT}  ({len(bands)} bands / {n} guitarists)")
    if missing:
        print(f"기타 사진 없음({len(missing)}): " + ", ".join(missing))


if __name__ == "__main__":
    main()
