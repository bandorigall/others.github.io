"""
generate_our_notes.py
our_notes.csv를 읽어 BanG Dream! Our Notes 대시보드 index.html을 생성합니다.
실행: python generate_our_notes.py [--csv our_notes.csv] [--out index.html]
"""

import csv
import json
import argparse
from pathlib import Path

BAND_ORDER = ["MyGO!!!!!", "Ave Mujica", "무겐다이 뮤타입", "millsage", "일가 DumbRock!"]

BAND_THEMES = {
    "MyGO!!!!!":       {"primary": "#3a82d4", "accent": "#6db9f0", "bg": "#deeefa", "dark": "#0f2a4a"},
    "Ave Mujica":      {"primary": "#7c28b8", "accent": "#b86cf0", "bg": "#efe4fa", "dark": "#30094e"},
    "무겐다이 뮤타입":  {"primary": "#d44e1e", "accent": "#f08050", "bg": "#faeae0", "dark": "#4e1800"},
    "millsage":        {"primary": "#22956a", "accent": "#50cc96", "bg": "#dcf5eb", "dark": "#083d25"},
    "일가 DumbRock!":  {"primary": "#c02a24", "accent": "#f06060", "bg": "#fae0e0", "dark": "#4e0a0a"},
}

BAND_LOGO_FILES = {
    "MyGO!!!!!":       "MyGO!!!!!.webp",
    "Ave Mujica":      "Ave Mujica.webp",
    "무겐다이 뮤타입":  "무겐다이 뮤타입.webp",
    "millsage":        "millsage.webp",
    "일가 DumbRock!":  "일가 DumbRock!.webp",
}


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def group_by_band(rows: list[dict]) -> dict:
    bands: dict[str, list[dict]] = {b: [] for b in BAND_ORDER}
    for row in rows:
        band = row.get("밴드", "").strip()
        if band in bands:
            bands[band].append(row)
    return bands


def build_html(bands: dict) -> str:
    bands_json  = json.dumps(bands,           ensure_ascii=False, indent=2)
    themes_json = json.dumps(BAND_THEMES,     ensure_ascii=False)
    logos_json  = json.dumps(BAND_LOGO_FILES, ensure_ascii=False)
    order_json  = json.dumps(BAND_ORDER,      ensure_ascii=False)

    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>BanG Dream! Our Notes</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;600;700;900&family=M+PLUS+Rounded+1c:wght@300;400;700;800&family=Outfit:wght@300;600;800;900&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --dur:.24s;--ease:cubic-bezier(.4,0,.2,1);
  --band-primary:#3a82d4;--band-accent:#6db9f0;
  --band-bg:#deeefa;--band-dark:#0f2a4a;
  --r:14px;--shadow:0 6px 28px rgba(0,0,0,.13);
  --header-h:52px;
}
html,body{height:100%;width:100%;font-family:'Noto Serif KR',serif;background:#13141a;overflow:hidden}

#app{display:flex;flex-direction:column;height:100vh;width:100vw;overflow:hidden}

/* ── header ── */
#header{
  flex:0 0 var(--header-h);
  display:flex;align-items:center;gap:12px;
  background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.08);
  padding:0 16px;z-index:20;
}
.logo-text{
  font-family:'Outfit',sans-serif;font-size:16px;font-weight:800;
  color:var(--band-dark);white-space:nowrap;transition:color var(--dur);
  letter-spacing:-.3px;flex-shrink:0;
}
.logo-text span{color:var(--band-primary);transition:color var(--dur)}

#back-btn{
  display:none;align-items:center;gap:4px;flex-shrink:0;
  padding:4px 11px;border-radius:14px;
  border:1.5px solid #bbb;background:transparent;
  font-family:'Outfit',sans-serif;font-size:12px;color:#666;cursor:pointer;white-space:nowrap;
  transition:border-color .15s,color .15s;
}
#back-btn:hover{border-color:var(--band-primary);color:var(--band-primary)}
#back-btn.visible{display:flex}

#member-nav{display:flex;gap:6px;flex:1;overflow-x:auto;scrollbar-width:none;align-items:center}
#member-nav::-webkit-scrollbar{display:none}
.member-tab{
  flex:0 0 auto;padding:4px 13px;border-radius:18px;
  border:1.5px solid var(--band-primary);
  background:transparent;color:var(--band-primary);
  font-family:'M PLUS Rounded 1c',sans-serif;
  font-size:12px;font-weight:700;cursor:pointer;white-space:nowrap;
  transition:background var(--dur),color var(--dur),transform .14s;
}
.member-tab:hover{background:var(--band-accent);color:#fff;transform:translateY(-1px)}
.member-tab.active{background:var(--band-primary);color:#fff}

/* ══════════════════════════════════════════════════
   band selector  —  squish / expand panels
══════════════════════════════════════════════════ */
#band-selector{
  flex:1;display:flex;overflow:hidden;
  background:#13141a;
}
#band-selector.hidden{display:none}

/* 기본: 5개 패널이 동일 너비(1/5).
   selector 위에 호버 들어오면 모든 패널이 줄어들고,
   그 중 실제 호버된 패널만 다시 커진다 (source order로 우선) */
.band-panel{
  flex:1 1 0;
  position:relative;
  overflow:hidden;
  cursor:pointer;
  transition:flex .55s cubic-bezier(.4,0,.2,1);
}
/* 두 숫자가 호버 시 비율을 결정.
   ─ 호버 패널: 6 → 더 키우려면 ↑, 작게 하려면 ↓
   ─ 나머지   : 0.5 → 더 두껍게 하려면 ↑, 가늘게 하려면 ↓
   현재값 기준: 호버 71%, 나머지 7%씩 */
#band-selector:hover > .band-panel{flex:.5 1 0}
#band-selector > .band-panel:hover{flex:6 1 0}

/* 이미지: 항상 원본 비율 유지(height 100%, width 자동).
   패널 너비가 좁으면 좌우가 잘려 가운데 슬라이스만 보이고,
   패널이 커지면 잘렸던 부분이 점점 드러남(트림 방식). */
.band-panel-img{
  position:absolute;
  top:0;
  left:50%;
  transform:translateX(-50%);
  height:100%;
  width:auto;
  max-width:none;
  display:block;
  user-select:none;
  -webkit-user-drag:none;
}

/* 호버 시에만 떠오르는 라벨 */
.band-panel-label{
  position:absolute;
  left:50%;bottom:26px;
  transform:translate(-50%,8px);
  padding:7px 16px;border-radius:16px;
  background:rgba(0,0,0,.58);
  backdrop-filter:blur(8px);
  font-family:'M PLUS Rounded 1c',sans-serif;
  font-size:14px;font-weight:800;color:#fff;
  white-space:nowrap;letter-spacing:.3px;
  pointer-events:none;
  opacity:0;
  transition:opacity .32s, transform .32s;
}
.band-panel:hover .band-panel-label{
  opacity:1;
  transform:translate(-50%,0);
}

/* ══════════════════════════════════════════════════
   profile area
══════════════════════════════════════════════════ */
#profile-area{flex:1;display:none;position:relative;overflow:hidden}
#profile-area.visible{display:flex}
#profile-bg{
  position:absolute;inset:0;z-index:0;
  background:linear-gradient(140deg,var(--band-bg) 0%,#f8f8ff 55%);
  transition:background var(--dur);
}
#profile-bg::before{
  content:'';position:absolute;left:0;top:0;bottom:0;width:5px;
  background:var(--band-primary);transition:background var(--dur);
}

#profile-card{
  position:relative;z-index:1;
  display:flex;width:100%;height:100%;
  padding:16px 28px 16px 22px;gap:24px;
  animation:fadeUp .26s var(--ease);
  overflow:hidden;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}

#img-panel{flex:0 0 auto;display:flex;align-items:stretch}
#char-img-wrap{
  position:relative;
  height:100%;
  aspect-ratio:3/4.5;
  border-radius:var(--r);overflow:hidden;
  background:var(--band-bg);box-shadow:var(--shadow);
  transition:background var(--dur);
}
#char-img{
  width:100%;height:100%;object-fit:cover;object-position:top center;
  display:block;transition:opacity .2s;
}
#costume-btn{
  position:absolute;bottom:10px;right:10px;
  padding:8px 18px;border-radius:20px;border:none;
  background:rgba(10,10,10,.62);color:#fff;
  font-family:'M PLUS Rounded 1c',sans-serif;
  font-size:13px;font-weight:800;cursor:pointer;
  backdrop-filter:blur(8px);white-space:nowrap;
  box-shadow:0 4px 14px rgba(0,0,0,.28);
  transition:background .15s,transform .12s;
}
#costume-btn:hover{background:rgba(10,10,10,.82);transform:scale(1.05)}

#info-panel{
  flex:1;min-width:0;display:flex;flex-direction:column;
  gap:14px;overflow-y:auto;
  scrollbar-width:thin;scrollbar-color:var(--band-accent) transparent;
  padding-right:4px;padding-top:2px;
}
#info-panel::-webkit-scrollbar{width:4px}
#info-panel::-webkit-scrollbar-thumb{background:var(--band-accent);border-radius:4px}

.info-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.char-role{
  font-family:'Outfit',sans-serif;font-size:13px;font-weight:700;
  color:var(--band-primary);letter-spacing:.6px;margin-bottom:3px;
}
.char-name{
  font-family:'M PLUS Rounded 1c',sans-serif;
  font-size:clamp(22px,3.4vw,42px);font-weight:800;line-height:1.1;
  color:var(--band-dark);
}
.char-name-jp{
  font-family:'Outfit',sans-serif;
  font-size:clamp(13px,1.4vw,18px);font-weight:300;color:#999;margin-top:3px;
}
.char-cv{font-family:'Noto Serif KR',serif;font-size:13px;color:#777;margin-top:5px}
.band-badge{
  flex:0 0 auto;margin-top:4px;padding:5px 13px;border-radius:12px;
  background:var(--band-primary);color:#fff;
  font-family:'M PLUS Rounded 1c',sans-serif;
  font-size:11px;font-weight:800;white-space:nowrap;
  transition:background var(--dur);
}

.divider{height:1.5px;background:linear-gradient(90deg,var(--band-accent),transparent);border-radius:2px}
.char-desc{font-family:'Noto Serif KR',serif;font-size:14px;line-height:1.9;color:#3a3a3a}

.meta-grid{display:flex;flex-direction:column;gap:8px}
.meta-item{
  background:rgba(255,255,255,.74);
  border:1px solid rgba(0,0,0,.05);
  border-left:4px solid var(--band-accent);
  border-radius:10px;
  padding:12px 18px;
  display:flex;align-items:baseline;gap:16px;
}
.meta-label{
  font-family:'Outfit',sans-serif;
  font-size:11px;font-weight:700;color:var(--band-primary);
  letter-spacing:.5px;white-space:nowrap;flex-shrink:0;min-width:72px;
}
.meta-value{
  font-family:'Noto Serif KR',serif;
  font-size:16px;font-weight:600;color:#1a1a2e;line-height:1.4;
}

.action-row{display:flex;flex-wrap:wrap;gap:8px}
.action-btn{
  padding:7px 16px;border-radius:18px;
  border:1.5px solid var(--band-primary);
  background:transparent;color:var(--band-primary);
  font-family:'M PLUS Rounded 1c',sans-serif;
  font-size:12px;font-weight:700;cursor:pointer;
  transition:background .15s,color .15s,transform .12s;
}
.action-btn:hover{background:var(--band-primary);color:#fff;transform:translateY(-1px)}

/* image modal */
#img-modal{
  display:none;position:fixed;inset:0;z-index:300;
  background:rgba(0,0,0,.86);
  align-items:center;justify-content:center;
}
#img-modal.open{display:flex}
#img-modal img{max-width:100vw;max-height:100vh;width:auto;height:auto;object-fit:contain;display:block}
#img-modal-close{
  position:fixed;top:14px;right:18px;
  width:36px;height:36px;border-radius:50%;border:none;
  background:rgba(255,255,255,.18);color:#fff;font-size:20px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  backdrop-filter:blur(4px);transition:background .15s;
}
#img-modal-close:hover{background:rgba(255,255,255,.32)}

/* ── 모바일 ── */
@media(max-width:600px){
  :root{--header-h:48px}
  .logo-text{display:none}
  #header{padding:0 10px;gap:8px}
  .member-tab{font-size:11px;padding:3px 10px}

  /* 모바일: 세로 스택 패널 (높이 1/5 → 호버 시 전체) */
  #band-selector{flex-direction:column}
  .band-panel-label{font-size:13px;bottom:14px}

  #profile-card{
    flex-direction:column;
    padding:12px 14px;gap:12px;overflow-y:auto;
  }
  #img-panel{align-items:center}
  #char-img-wrap{height:auto;width:52vw;aspect-ratio:3/4.5}
  #info-panel{overflow-y:visible;padding-right:0}
  .char-name{font-size:clamp(20px,6vw,30px)}
  .meta-item{padding:10px 14px;gap:10px}
  .meta-label{min-width:58px;font-size:10px}
  .meta-value{font-size:14px}
  .char-desc{font-size:13px;line-height:1.8}
}
</style>
</head>
<body>
<div id="app">

  <div id="header">
    <button id="back-btn" onclick="goBack()">&#8592; 뒤로</button>
    <div class="logo-text">BanG Dream! <span>Our Notes</span></div>
    <div id="member-nav"></div>
  </div>

  <div id="band-selector"></div>

  <div id="profile-area">
    <div id="profile-bg"></div>
    <div id="profile-card">
      <div id="img-panel">
        <div id="char-img-wrap">
          <img id="char-img" src="" alt="">
          <button id="costume-btn" onclick="toggleCostume()">라이브복</button>
        </div>
      </div>
      <div id="info-panel">
        <div class="info-top">
          <div>
            <div class="char-role" id="c-role"></div>
            <div class="char-name"    id="c-name"></div>
            <div class="char-name-jp" id="c-name-jp"></div>
            <div class="char-cv"      id="c-cv"></div>
          </div>
          <div class="band-badge" id="c-band"></div>
        </div>
        <div class="divider"></div>
        <div class="char-desc" id="c-desc"></div>
        <div class="meta-grid"  id="c-meta"></div>
        <div class="action-row" id="c-actions"></div>
      </div>
    </div>
  </div>

</div>

<div id="img-modal" onclick="closeImgModal(event)">
  <button id="img-modal-close" onclick="closeImgModal()">&#x2715;</button>
  <img id="img-modal-img" src="" alt="">
</div>

<script>
const BANDS  = """ + order_json + """;
const THEMES = """ + themes_json + """;
const LOGOS  = """ + logos_json + """;
const DATA   = """ + bands_json + """;

let currentMember = null;
let costumeMode   = 'daily';

function applyTheme(band) {
  const t = THEMES[band] || THEMES['MyGO!!!!!'];
  const r = document.documentElement;
  r.style.setProperty('--band-primary', t.primary);
  r.style.setProperty('--band-accent',  t.accent);
  r.style.setProperty('--band-bg',      t.bg);
  r.style.setProperty('--band-dark',    t.dark);
}

function initBandSelector() {
  const sel = document.getElementById('band-selector');
  BANDS.forEach(band => {
    const panel = document.createElement('div');
    panel.className = 'band-panel';

    const img = document.createElement('img');
    img.className = 'band-panel-img';
    img.src = LOGOS[band];
    img.alt = band;
    img.draggable = false;

    const label = document.createElement('div');
    label.className = 'band-panel-label';
    label.textContent = band;

    panel.appendChild(img);
    panel.appendChild(label);
    panel.addEventListener('click', () => selectBand(band));
    sel.appendChild(panel);
  });
}

function selectBand(band) {
  applyTheme(band);
  document.getElementById('band-selector').classList.add('hidden');
  document.getElementById('profile-area').classList.add('visible');
  document.getElementById('back-btn').classList.add('visible');
  buildMemberNav(band);
  const members = DATA[band] || [];
  if (members.length) selectMember(members[0]);
}

function buildMemberNav(band) {
  const nav = document.getElementById('member-nav');
  nav.innerHTML = '';
  (DATA[band] || []).forEach(m => {
    const btn = document.createElement('button');
    btn.className = 'member-tab';
    btn.textContent = m['이름(한글)'];
    btn.addEventListener('click', () => selectMember(m));
    nav.appendChild(btn);
  });
}

function selectMember(m) {
  currentMember = m;
  costumeMode   = 'daily';
  document.querySelectorAll('.member-tab').forEach(b =>
    b.classList.toggle('active', b.textContent === m['이름(한글)']));
  renderProfile(m);
}

function renderProfile(m) {
  const g = k => (m[k] || '').trim();
  const name      = g('이름(한글)');
  const nameJp    = g('이름(일본어)');
  const band      = g('밴드');
  const inst      = g('악기');
  const cv        = g('CV');
  const school    = g('소속');
  const cls       = g('반');
  const bday      = g('생일');
  const food      = g('좋아하는 음식');
  const hobby     = g('취미');
  const desc      = g('설명');
  const imgDaily  = g('일상복');
  const imgLive   = g('라이브복');
  const imgOrig   = g('이미지(원문)');
  const imgKr     = g('이미지(한글)');
  const comment   = g('성우 코멘트');
  const bandIntro = g('밴드 소개');

  document.getElementById('c-role').textContent    = inst;
  document.getElementById('c-name').textContent    = name;
  document.getElementById('c-name-jp').textContent = nameJp ? `(${nameJp})` : '';
  document.getElementById('c-cv').textContent      = cv ? 'CV. ' + cv : '';
  document.getElementById('c-band').textContent    = band;
  document.getElementById('c-desc').textContent    = desc;

  const img = document.getElementById('char-img');
  img.src = imgDaily || imgOrig || '';
  img.alt = name;

  const cosBtn = document.getElementById('costume-btn');
  cosBtn.style.display = imgLive ? '' : 'none';
  cosBtn.textContent   = '라이브복';

  const meta = document.getElementById('c-meta');
  meta.innerHTML = '';
  [['소속', school], ['반', cls], ['생일', bday],
   ['좋아하는 음식', food], ['취미', hobby]]
    .filter(([, v]) => v)
    .forEach(([label, val]) => {
      const d = document.createElement('div');
      d.className = 'meta-item';
      d.innerHTML = `<div class="meta-label">${label}</div>
                     <div class="meta-value">${val}</div>`;
      meta.appendChild(d);
    });

  const row = document.getElementById('c-actions');
  row.innerHTML = '';
  if (imgOrig)   mkBtn(row, '이미지 원문',          () => openImgModal(imgOrig));
  if (imgKr)     mkBtn(row, '이미지 한글',          () => openImgModal(imgKr));
  if (comment)   mkBtn(row, '성우 코멘트 (트위터)', () => window.open(comment,   '_blank', 'noopener'));
  if (bandIntro) mkBtn(row, '밴드 소개 (트위터)',   () => window.open(bandIntro, '_blank', 'noopener'));
}

function mkBtn(parent, label, handler) {
  const b = document.createElement('button');
  b.className = 'action-btn';
  b.textContent = label;
  b.onclick = handler;
  parent.appendChild(b);
}

function toggleCostume() {
  if (!currentMember) return;
  const liveImg  = (currentMember['라이브복']  || '').trim();
  const dailyImg = (currentMember['일상복'] || '').trim();
  const img = document.getElementById('char-img');
  const btn = document.getElementById('costume-btn');
  const next = costumeMode === 'daily' ? liveImg : dailyImg;
  if (!next) return;
  img.style.opacity = '0';
  setTimeout(() => { img.src = next; img.style.opacity = '1'; }, 180);
  if (costumeMode === 'daily') { btn.textContent = '일상복';  costumeMode = 'live'; }
  else                         { btn.textContent = '라이브복'; costumeMode = 'daily'; }
}

function goBack() {
  currentMember = null;
  document.getElementById('profile-area').classList.remove('visible');
  document.getElementById('band-selector').classList.remove('hidden');
  document.getElementById('back-btn').classList.remove('visible');
  document.getElementById('member-nav').innerHTML = '';
  applyTheme('MyGO!!!!!');
}

function openImgModal(url) {
  document.getElementById('img-modal-img').src = url;
  document.getElementById('img-modal').classList.add('open');
}
function closeImgModal(e) {
  if (e && e.target === document.getElementById('img-modal-img')) return;
  document.getElementById('img-modal').classList.remove('open');
}

applyTheme('MyGO!!!!!');
initBandSelector();
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate Our Notes index.html from CSV")
    parser.add_argument("--csv", default="our_notes.csv", help="입력 CSV 파일 경로")
    parser.add_argument("--out", default="index.html",    help="출력 HTML 파일 경로")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    rows  = load_csv(str(csv_path))
    bands = group_by_band(rows)
    out   = Path(args.out)
    out.write_text(build_html(bands), encoding="utf-8")
    print(f"[OK] {out}  ({len(rows)}명 / {sum(1 for b in bands if bands[b])}개 밴드)")


if __name__ == "__main__":
    main()