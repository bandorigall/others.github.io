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


# 픽업 해설 사전.
#   keys : specs["픽업"] 문자열에 이 조각이 들어있으면 매칭 (대소문자 무시)
#   tags : 사운드 성격 요약 칩
# 위에 있는 항목이 먼저 매칭된다(구체적인 모델명 → 일반 용어 순으로 둘 것).
PICKUP_GLOSSARY = [
    # --- Seymour Duncan ---
    (["SH-1n", "'59"], "Seymour Duncan SH-1n '59 (넥)",
     ["빈티지", "저출력", "따뜻함"],
     "50~60년대 PAF 험버커를 재현한 표준 넥 픽업. 출력이 낮아 깔끔하고 부드럽게 울리며, "
     "클린 아르페지오나 리드에서 '노래하는' 소리를 낸다. 넥에 넣는 가장 무난한 선택."),
    (["SH-4"], "Seymour Duncan SH-4 JB (브리지)",
     ["고출력", "중고역 강조", "록/메탈 표준"],
     "세상에서 가장 많이 쓰인 브리지 험버커. 중고역이 앞으로 튀어나와 밴드 합주에서 기타가 묻히지 않고, "
     "게인을 걸면 단단한 리프와 잘 뻗는 리드가 나온다."),
    (["SH-11"], "Seymour Duncan SH-11 Custom Custom (브리지)",
     ["중역 두툼", "알니코2", "부드러운 왜곡"],
     "고출력 Custom 계열이지만 자석을 알니코2로 바꿔 날카로움을 덜어낸 픽업. "
     "중역이 도톰하고 왜곡이 매끈해서 리드·백킹 어디에 써도 거칠지 않다."),
    (["SH-16"], "Seymour Duncan SH-16 59/Custom Hybrid (브리지)",
     ["하이브리드", "중출력", "다재다능"],
     "'59의 맑은 코일 + Custom의 두꺼운 코일을 한 픽업에 섞은 구조. 클린은 빈티지처럼 투명하고 "
     "게인을 걸면 모던하게 조여지는, 장르를 안 가리는 성격."),
    (["SH-2n"], "Seymour Duncan SH-2n Jazz (넥)",
     ["저출력", "맑고 투명", "선명한 분리"],
     "'59보다 더 밝고 정돈된 넥 험버커. 코드를 쳐도 음이 뭉치지 않아 재즈·퓨전은 물론 "
     "빠른 리드에서도 한 음 한 음이 또렷하다."),
    (["SH-15"], "Seymour Duncan SH-15 Alternative 8 (브리지)",
     ["초고출력", "알니코8", "공격적"],
     "알니코 자석 중 가장 센 알니코8을 쓴 초고출력 픽업. 액티브급 펀치를 내면서도 패시브 특유의 "
     "다이내믹이 남아 있어, 헤비한 리프에서 가슴을 때리는 저역이 나온다."),
    (["SH-18"], "Seymour Duncan SH-18 Whole Lotta Humbucker",
     ["빈티지 고출력", "70년대 록"],
     "70년대 하드록 톤을 노린 픽업. PAF의 질감을 유지한 채 출력만 끌어올려, "
     "앰프를 살짝 밀어붙였을 때의 걸쭉한 크런치가 특기."),
    (["SSL-6"], "Seymour Duncan SSL-6 (스트랫 싱글코일)",
     ["싱글코일", "고출력", "찰랑임 + 힘"],
     "스트라토캐스터용 싱글코일의 고출력 버전. 싱글 특유의 찰랑거리는 고역은 그대로면서 "
     "출력이 높아 험버커 기타와 같이 서도 힘이 밀리지 않는다."),
    (["SHR-1"], "Seymour Duncan SHR-1 Hot Rails (싱글 사이즈 험버커)",
     ["싱글 크기", "험버커 출력", "잡음 적음"],
     "싱글코일 자리에 그대로 들어가는 미니 험버커. 겉은 싱글인데 소리는 굵고 잡음(험)이 없어, "
     "스트랫에서 브리지만 확 헤비하게 만들고 싶을 때 쓴다."),
    (["SENTIENT"], "Seymour Duncan Sentient (넥)",
     ["모던", "타이트", "메탈 넥"],
     "메탈용으로 설계된 넥 험버커. 고게인에서도 저역이 퍼지지 않고 손가락 움직임이 그대로 들려, "
     "빠른 리드와 클린 아르페지오 둘 다 소화한다."),
    (["NAZGÛL", "NAZGUL"], "Seymour Duncan Nazgûl (브리지)",
     ["초고출력", "저음 강력", "다운튜닝"],
     "다운튜닝 헤비 리프 전용에 가까운 브리지 픽업. 저역이 단단하게 뭉치고 어택이 칼처럼 잘려서, "
     "빠른 뮤트 리프가 기관총처럼 들린다."),
    # --- 액티브 / 기타 브랜드 ---
    (["EMG 707-X", "EMG 707"], "EMG 707-X (7현용 액티브)",
     ["액티브", "7현 전용", "저역 정리"],
     "7현의 굵은 저음줄까지 흐트러지지 않게 잡아주는 액티브 픽업. X 시리즈라 기존 EMG보다 "
     "헤드룸이 넓어 다이내믹이 살아 있고, 노이즈가 거의 없다. 9V 배터리가 필요하다."),
    (["EMG 81"], "EMG 81 (액티브)",
     ["액티브", "고출력", "메탈의 대명사"],
     "메탈 기타 하면 떠오르는 액티브 험버커. 내장 프리앰프로 출력을 밀어 아주 타이트하고 "
     "노이즈 없는 소리를 내지만, 그만큼 톤 성격이 강해 앰프 색을 덮는 편. 배터리가 필요하다."),
    (["GH-1G"], "ESP GH-1G",
     ["패시브", "보급형", "무난한 고출력"],
     "ESP 보급형 모델에 들어가는 패시브 험버커. 액티브만큼 조여지지는 않지만 "
     "배터리 없이 무난한 고출력 록 톤을 내준다."),
    (["Fishman Fluence"], "Fishman Fluence (액티브)",
     ["액티브", "보이스 전환", "노이즈 없음"],
     "코일을 감는 대신 인쇄 회로를 층층이 쌓아 만든 신형 픽업. 스위치 하나로 '빈티지 PAF'와 "
     "'모던 액티브' 두 가지 성격을 오갈 수 있고, 코일 잡음이 원리적으로 없다."),
    (["MONSTER TONE", "MONSTERTONE"], "SCHECTER MONSTER TONE J (싱글)",
     ["싱글코일", "고출력", "일본산"],
     "SCHECTER 재팬의 고출력 싱글코일. 일반 싱글보다 굵고 중역이 차 있어 "
     "험버커와 섞어 써도 음량 차이가 크게 나지 않는다."),
    (["SUPER ROCK"], "SCHECTER SUPER ROCK J (험버커)",
     ["중고출력", "밸런스형", "일본산"],
     "SCHECTER 재팬의 간판 험버커. 지나치게 세지 않은 출력에 고·중·저역이 고르게 나와, "
     "팝부터 하드록까지 무난하게 받아준다."),
    (["Air Norton"], "DiMarzio Air Norton (넥)",
     ["중출력", "부드러움", "리드 특화"],
     "에어버킹 구조로 자석 힘을 줄여 음이 더 길게 늘어지는 넥 픽업. "
     "왜곡을 걸었을 때 기름진 리드 톤이 특기다."),
    (["True Velvet"], "DiMarzio True Velvet (미들 싱글)",
     ["싱글코일", "빈티지", "부드러운 고역"],
     "60년대 싱글코일 감각의 미들 픽업. 고역이 날카롭지 않고 부드러워 "
     "브리지·넥과 섞는 하프톤에서 특히 예쁘다."),
    (["Tone Zone"], "DiMarzio Tone Zone (브리지)",
     ["고출력", "중저역 두툼", "펀치"],
     "중저역이 유난히 두꺼운 고출력 브리지 험버커. 코드를 치면 벽처럼 밀려오고 "
     "리드에서는 굵고 뭉근한 톤이 난다."),
    (["PRS 85/15"], "PRS 85/15 험버커",
     ["밝고 선명", "코일탭 우수", "만능형"],
     "PRS가 창업 초기 픽업을 다시 다듬은 자사 험버커. 고역이 시원하게 열려 있고 "
     "코일을 탭하면 진짜 싱글에 가까운 소리가 나 한 대로 여러 장르를 커버한다."),
    (["Filter'Tron", "FilterTron", "Filtertron"], "TV Jones Filter'Tron 계열",
     ["그레치 사운드", "저출력 험버커", "찰랑+두께"],
     "그레치 특유의 픽업. 험버커인데도 출력이 낮아 싱글처럼 찰랑거리면서 잡음은 적고, "
     "로커빌리·개러지 록의 그 '트왱'한 소리를 만든다."),
    (["ESP CUSTOM LAB"], "ESP CUSTOM LAB",
     ["주문 제작", "사양별 상이"],
     "ESP 커스텀 오더 시 사용되는 자사 픽업. 주문 사양에 따라 출력·성격이 달라져 "
     "개체마다 소리가 같지 않다."),
    (["P-90"], "P-90 (소프바 싱글코일)",
     ["싱글코일", "굵은 중역", "거친 크런치"],
     "싱글코일인데 코일이 넓고 납작해 험버커에 가까운 두께를 가진다. "
     "클린은 통통하고 게인을 걸면 지저분하게 으르렁대는, 개성이 아주 강한 픽업."),
]

# 일반 용어. 위 모델 해설이 2개 미만일 때만 보조로 덧붙인다.
GENERAL_GLOSSARY = [
    (["싱글코일", "싱글 코일", "싱글"], "싱글코일이란?",
     ["얇고 맑음", "잡음 있음"],
     "코일 하나로 소리를 받는 가장 오래된 방식. 고역이 밝고 음의 윤곽이 또렷하지만 "
     "형광등·모니터 근처에서 '지-' 하는 험 노이즈가 잘 탄다. 펜더 계열의 상징."),
    (["험버커", "Humbucker"], "험버커란?",
     ["굵고 힘 있음", "잡음 상쇄"],
     "코일 두 개를 반대로 감아 잡음(험)을 서로 지워(bucking) 없앤 방식. "
     "싱글보다 출력이 높고 중저역이 두꺼워 왜곡과 궁합이 좋다. 깁슨 계열의 상징."),
    (["액티브"], "액티브 픽업이란?",
     ["배터리 필요", "노이즈 최소"],
     "픽업 안에 소형 프리앰프가 들어 있어 9V 건전지로 신호를 증폭한다. "
     "출력이 일정하고 잡음이 거의 없어 고게인에 유리한 대신, 배터리가 닳으면 소리가 죽는다."),
    (["코일탭", "push/pull", "코일 탭"], "코일탭(코일 스플릿)이란?",
     ["1대 2가지 소리"],
     "험버커의 코일 하나만 살려 싱글코일처럼 쓰는 스위치. 볼륨 노브를 당기는(push/pull) 식이 흔하며, "
     "기타 한 대로 굵은 소리와 맑은 소리를 오갈 수 있다."),
    (["HSH"], "HSH 배열이란?",
     ["험-싱글-험"],
     "넥과 브리지에 험버커, 가운데에 싱글코일을 두는 배치. 헤비한 리프와 맑은 커팅을 "
     "한 대에서 모두 뽑으려는 만능형 구성이다."),
    (["SSS"], "SSS 배열이란?",
     ["싱글 3기", "스트랫 표준"],
     "싱글코일 3개를 얹은 스트라토캐스터의 표준 배치. 5-way 스위치로 픽업을 섞어 "
     "찰랑거리는 '하프톤'까지 다섯 가지 소리를 만든다."),
]


def pickup_html(pickup_text):
    """픽업 스펙 문자열에서 해설이 있는 낱말에 말풍선 트리거를 씌운 HTML을 만든다."""
    if not pickup_text:
        return ""
    low = pickup_text.lower()
    spans = []  # (start, end, note)
    for keys, name, tags, desc in PICKUP_GLOSSARY + GENERAL_GLOSSARY:
        hit = None
        for k in keys:
            i = low.find(k.lower())
            if i >= 0:
                hit = (i, i + len(k))
                break
        if not hit:
            continue
        # 이미 다른 해설이 덮은 구간이면 건너뛴다(구체적인 모델명 우선).
        if any(hit[0] < s_end and s_start < hit[1] for s_start, s_end, _ in spans):
            continue
        spans.append((hit[0], hit[1],
                      {"name": name, "tags": tags, "desc": desc}))
    spans.sort()

    out, cur = [], 0
    for s, t, note in spans:
        out.append(e(pickup_text[cur:s]))
        tips = "".join(f'<span class="pk-tag">{e(x)}</span>' for x in note["tags"])
        out.append(
            '<span class="pk-term" tabindex="0" role="button" aria-label="픽업 설명 보기">'
            f'{e(pickup_text[s:t])}'
            '<span class="pk-pop" role="tooltip">'
            f'<b class="pk-name">{e(note["name"])}</b>'
            f'<span class="pk-tags">{tips}</span>'
            f'<span class="pk-desc">{e(note["desc"])}</span>'
            '</span></span>')
        cur = t
    out.append(e(pickup_text[cur:]))
    return "".join(out)


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
                "pickupHtml": pickup_html((g.get("specs") or {}).get("픽업", "")),
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
/* 픽업 말풍선 */
.pk-term{position:relative;cursor:help;color:var(--tx);font-weight:600;
    border-bottom:1px dashed var(--accent);padding-bottom:1px;outline:none}
.pk-term:hover,.pk-term:focus-visible,.pk-term.on{color:var(--accent)}
.pk-pop{position:absolute;left:0;bottom:calc(100% + 9px);z-index:30;
    width:min(280px,72vw);display:block;visibility:hidden;opacity:0;
    transform:translateY(4px);transition:opacity .13s,transform .13s,visibility .13s;
    background:var(--panel2);border:1px solid var(--line);border-radius:10px;
    box-shadow:0 10px 28px rgba(0,0,0,.45);padding:10px 12px;
    font-size:.79rem;font-weight:400;line-height:1.65;color:var(--tx2);
    text-align:left;white-space:normal;cursor:auto;pointer-events:none}
.pk-pop::after{content:'';position:absolute;top:100%;left:16px;border:7px solid transparent;
    border-top-color:var(--panel2);filter:drop-shadow(0 1px 0 var(--line))}
.pk-term:hover>.pk-pop,.pk-term:focus-visible>.pk-pop,.pk-term.on>.pk-pop{
    visibility:visible;opacity:1;transform:translateY(0);pointer-events:auto}
.pk-term.flip>.pk-pop{left:auto;right:0}
.pk-term.flip>.pk-pop::after{left:auto;right:16px}
.pk-name{display:block;color:var(--tx);font-size:.82rem;margin-bottom:6px}
.pk-tags{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:7px}
.pk-tag{font-size:.67rem;color:var(--tx2);background:var(--panel);
    border:1px solid var(--line);border-radius:99px;padding:2px 7px;white-space:nowrap}
.pk-desc{display:block}
@media (hover:none){.pk-term{cursor:pointer}}
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
    ? '<dl class="specs">'+Object.entries(d.specs).map(([k,v])=>
        (k === '픽업' && d.pickupHtml)
          ? '<div class="spec-row"><dt>'+esc(k)+'</dt><dd>'+d.pickupHtml+'</dd></div>'
          : row(k,v)).join('')+'</dl>'
    : '';
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
  bindPickups();
  bd.classList.add('on');
  document.body.style.overflow='hidden';
  mo.querySelector('.modal-close').focus();
}
function bindPickups(){
  mo.querySelectorAll('.pk-term').forEach(el=>{
    el.addEventListener('click',ev=>{
      ev.stopPropagation();
      const was = el.classList.contains('on');
      mo.querySelectorAll('.pk-term.on').forEach(o=>o.classList.remove('on'));
      if(!was) el.classList.add('on');
    });
    // 말풍선이 화면 밖으로 나가면 오른쪽 기준으로 뒤집는다.
    const fix = ()=>{
      el.classList.remove('flip');
      const r = el.querySelector('.pk-pop').getBoundingClientRect();
      if(r.right > window.innerWidth - 8) el.classList.add('flip');
    };
    el.addEventListener('mouseenter',fix);
    el.addEventListener('click',fix);
    el.addEventListener('focus',fix);
  });
}
document.addEventListener('click',()=>{
  document.querySelectorAll('.pk-term.on').forEach(o=>o.classList.remove('on'));
});

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
