"""
generate_info.py
our_notes.csv + 아래 수집 데이터로 아워노츠 정보 페이지 info.html 을 생성합니다.
실행: python generate_info.py [--csv our_notes.csv] [--out info.html]

데이터 출처 (2026-08-21 수집)
  - 공식 사이트 bang-dream-on.bushimo.jp  : News / Band / Character / System / Music / Pre-register
  - 공식 X @bang_dream_on(JP) / @bangdreamon_KR(KR)
  - 부시로드 프레스 릴리스(PR TIMES)
"""

import csv
import json
import argparse
from html import escape as esc

from generate_html import BAND_ORDER, BAND_THEMES, BAND_LOGO_FILES

UPDATED = "2026-08-21"

SPECS = [
    ("Title", "BanG Dream! Our Notes"),
    ("장르", "격주(撃奏) 리듬 × 어드벤처"),
    ("가격", "기본 무료 (인앱 결제)"),
    ("대응 OS", "iOS / Android"),
    ("사전등록", "글로벌 120만 명 돌파"),
    ("출시", "2026년 예정 · 일자 미발표"),
]

BAND_INTRO = {
    "MyGO!!!!!": (
        "",
        "긍정하지 못한 마음도, 답을 찾지 못한 고민도 전부 끌어안은 채 무대에 선다. "
        "멜로코어를 축으로 포에트리 리딩을 엮은 펑크록."),
    "Ave Mujica": (
        "",
        "고딕으로 가득한 탐미적이고 헤비한 사운드. "
        "토가와 사키코가 세운 독자적 세계관을 무대 위에서 끝까지 밀어붙인다."),
    "무겐다이 뮤타입": (
        "夢限大みゅーたいぷ",
        "라이브는 물론 방송·창작까지 각자의 영역에서 활약하는 버추얼 걸즈밴드. "
        "틀에 얽매이지 않는 음악으로 무한(夢限)의 우주를 항해 중."),
    "millsage": (
        "",
        "Key.&Vo. 시오미 호타루의 천재적인 가창과 연주가 주축. "
        "한 번뿐인 인생에 행복과 축복이 있기를 — 그 바람을 담아 오늘도 연주한다."),
    "일가 DumbRock!": (
        "一家Dumb Rock!",
        "생활의 고난을 폭음으로 지워버리는 펑키 & 그루비 사운드, 트윈 보컬 편성. "
        "배경도 성격도 제각각인 다섯 '가족'이 평온하기 위해 무대에 선다."),
}

# 밴드별 공식 영상 — {밴드: [(라벨, YouTube ID), ...]}
BAND_MOVIES = {
    "MyGO!!!!!": [
        ("게임 소개 CM", "afzJmVWdBOU"),
        ("애니메이션 CM", "_I6Xd50xdFI"),
        ("밴드 소개 영상", "gOP2VqxVEEw"),
    ],
    "Ave Mujica": [
        ("게임 소개 CM", "8ozRUTkPZf0"),
        ("애니메이션 CM", "YOR1--95WU0"),
        ("밴드 소개 영상", "YoHsLj47i4s"),
    ],
    "무겐다이 뮤타입": [
        ("애니메이션 CM", "S0nK80t3HIc"),
        ("밴드 소개 영상", "HNnRmfwWgCw"),
    ],
    "millsage": [
        ("스토리 소개 트레일러", "5TYMKyncKsM"),
        ("애니메이션 CM", "4dBoXrtaSJk"),
        ("밴드 소개 영상", "6OeuA3UWPRg"),
    ],
    "일가 DumbRock!": [
        ("스토리 소개 트레일러", "VEsoKpN7hZ0"),
        ("애니메이션 CM", "IFGgK4vgCwg"),
        ("밴드 소개 영상", "4JscPlBnvhs"),
    ],
}

# 밴드 공통 영상
PV = [
    ("티저 PV", "vCtvCf61uUQ"),
    ("티저 PV 제2탄", "liul_-0nev4"),
]

TIMELINE = [
    ("2026.01.12", "공식 사이트 오픈 · 티저 PV 공개",
     "신작 모바일 게임 『BanG Dream! Our Notes』 발표. 걸파는 운영을 계속하고 아워노츠는 2026년 출시로 별개 전개.", False),
    ("2026.01.12", "millsage · 일가 Dumb Rock! 데뷔 무대 결정",
     "MyGO!!!!! × Ave Mujica 투맨 라이브의 오프닝 액트로 신규 2밴드 출연 발표.", False),
    ("2026.03.01", "클로즈드 베타 테스트 참가자 모집",
     "일본 전화번호 인증이 필요했다.", False),
    ("2026.06.10", "「아워노츠 사전등록 개시 기념 특번」 편성 발표", "", False),
    ("2026.06.26", "글로벌 동시 사전등록 개시",
     "특번에서 격주 라이브 · 어시스트 모드 · 70곡 이상 수록 등을 공개. 1st 싱글 발매 기념 배포회 & 시연회도 결정.", True),
    ("2026.08.03", "글로벌 사전등록 100만 명 돌파",
     "유료 「미션 패스」 시즌 1이 전원 무료로 전환. 150만까지의 추가 보상도 함께 공개.", False),
    ("2026.08.06", "한국 사전예약 이벤트 「LIVE HOUSE 스태프 모집」",
     "매일 미션 + 친구 초대로 스타 · SR 스냅 · 실물 굿즈까지.", False),
    ("2026.08.10", "X 추첨 캠페인 개시 (총 5탄, 9월 14일까지)",
     "매일 10시 캠페인 포스트 리포스트 → 총액 300만 엔 상당 えらべるPay를 3,000명에게 추첨.", False),
    ("2026.08.21", "사전등록 120만 명 돌파 (현재)",
     "다음 목표는 150만 — SSR 이상 확정 가챠 티켓.", True),
    ("2026.09.30", "1st 싱글 동시 발매 (예정)", "", False),
    ("2026.12", "millsage · 일가 Dumb Rock! 단독 라이브 (예정)",
     "게임 출시일 자체는 아직 미발표.", False),
]

SYSTEM = [
    ("리듬 게임",
     "Live2D 모드(라이브 현장을 실시간 재현) · MV 모드(2D/3D MV, 애니 영상, 신작 오리지널 MV) · "
     "연출을 걷어낸 경량 모드까지, 플레이 스타일에 맞춰 고를 수 있다."),
    ("격주(撃奏) 라이브",
     "최대 5인이 함께 즐기는 파티형 리듬게임. 콤보로 겨루는 COMBO 격주, 운과 스킬의 LUCK 격주, "
     "정확도의 JUST 격주. 곡 중간 「격주 구간」에서 점수를 몰아친다."),
    ("어시스트 모드",
     "플릭을 탭으로 대체 가능. 실력에 맞춰 콤보 유지 보정 강도를 자동 조절해, "
     "리듬게임이 약해도 고난도 보면에 도전할 수 있다."),
    ("이머시브 홈",
     "멤버들의 일상이 움직이는 홈 화면. 스토리와 이벤트를 진행할수록 밴드별 장면이 하나씩 해금된다."),
    ("시네마틱 스토리",
     "캐릭터 연기와 카메라 워크가 대폭 진화했고, 특정 장면에서는 애니메이션이 이음매 없이 재생된다."),
]

# 커버곡 — (밴드, 곡명, 원곡 가수, 출처, CBT 이후 공개 여부)
MUSIC = [
    ("MyGO!!!!!", "青春コンプレックス", "결속 밴드", "TVA 봇치 더 록! 1기 OP", False),
    ("MyGO!!!!!", "ないものねだり", "KANA-BOON", "", False),
    ("MyGO!!!!!", "シャルル", "밸룬 (v flower)", "", False),
    ("MyGO!!!!!", "ホワイトノイズ", "Official髭男dism", "TVA 도쿄 리벤저스 OP", True),
    ("Ave Mujica", "残酷な天使のテーゼ", "타카하시 요코", "TVA 신세기 에반게리온 OP", False),
    ("Ave Mujica", "堕天", "Creepy Nuts", "TVA 철야의 노래 1기 OP", False),
    ("Ave Mujica", "暗黒天国", "ALI PROJECT", "TVA 꼬마여신 카린 OP", False),
    ("무겐다이 뮤타입", "オリオンをなぞる", "UNISON SQUARE GARDEN", "TVA TIGER & BUNNY OP", False),
    ("무겐다이 뮤타입", "唱", "Ado", "", False),
    ("millsage", "ロウワー", "누유리 (v flower)", "", False),
    ("millsage", "Pretender", "Official髭男dism", "", False),
    ("millsage", "unravel", "TK from 凛として時雨", "TVA 도쿄 구울 OP", True),
    ("일가 DumbRock!", "イケナイ太陽", "ORANGE RANGE", "드라마 「아름다운 그대에게」 주제가", False),
    ("일가 DumbRock!", "革命道中", "아이나 디 엔드", "TVA 단다단 2기 OP", False),
]

# 오리지널곡 — (밴드, CBT 수록 곡 수, 대표/전곡 표기)
ORIGINAL = [
    ("MyGO!!!!!", 13, "迷星叫 · 壱雫空 · 碧天伴走 · 春日影(MyGO!!!!! ver.) · 詩超絆 · 迷路日々 · 名無声 외"),
    ("Ave Mujica", 10, "Ave Mujica · Mas?uerade Rhapsody Re?uest 외"),
    ("무겐다이 뮤타입", 6, "✞animaるパーティ✞開催中✞ · エンプティパペット · 夢現妄想世界 · 限界現実サバイブ天使 · コハク · ビッグマウス"),
    ("millsage", 1, "起死開戦"),
    ("일가 DumbRock!", 1, "ホーミー・タイッ！！"),
]

REWARD = [
    ("50만", "스타 4,000개 (가챠 20연분)", True),
    ("60만", "악곡 티켓 3장", True),
    ("70만", "SR 이상 확정 가챠 티켓", True),
    ("80만", "EX 레어도 스냅 카드", True),
    ("90만", "뱅드림 애니 로고 스티커 3종", True),
    ("100만", "미션 패스 시즌 1 무료화", True),
    ("110~140만", "출시 기념 가챠 티켓 (단계별)", False),
    ("150만", "SSR 이상 멤버 / 스냅 확정 가챠 티켓", False),
]

CAMPAIGN = [
    ("X 추첨 캠페인 (일본)",
     "매일 10시 캠페인 포스트를 리포스트하고 스토어 사전등록을 마치면 즉석 추첨. "
     "총액 300만 엔 상당 えらべるPay를 3,000명에게. 8월 10일부터 9월 14일까지 총 5탄이며 "
     "각 탄마다 당첨될 때까지 매일 응모할 수 있다. 리플라이로 참여하는 W찬스는 10만 엔권 10명."),
    ("LIVE HOUSE 스태프 모집 (한국)",
     "한국 공식 계정이 8월 6일 시작한 글로벌 서버 사전예약 이벤트. "
     "매일 미션과 친구 초대로 「입고 횟수」를 모아 스타 · SR 스냅 · 실물 굿즈를 받는다."),
    ("집계 방식",
     "사전등록 수는 언어별이 아니라 글로벌 전체 합산. 한국어판은 App Store 예약 주문 + "
     "Google Play 사전등록 + 공식 X 팔로워 수를 더해 계산한다. 보상은 정식 서비스 시작 후 계정당 1회 수령."),
]

CHANNELS = [
    ("공식 사이트 (일본)", "https://bang-dream-on.bushimo.jp/", "bang-dream-on.bushimo.jp", "—"),
    ("공식 X (일본)", "https://x.com/bang_dream_on", "@bang_dream_on · バンドリ！アワーノーツ", "126,726"),
    ("공식 X (한국)", "https://x.com/bangdreamon_KR", "@bangdreamon_KR · 뱅드림! 아워 노트", "13,515"),
    ("한국 사전예약", "https://bdon.biligames.com/pre-register", "bdon.biligames.com/pre-register", "—"),
    ("한국 공식 디스코드", "https://discord.gg/ournotes", "discord.gg/ournotes", "—"),
    ("공식 YouTube", "https://www.youtube.com/channel/UCN-bFIdJM0gQlgX7h6LKcZA",
     "밴드별 소개 영상 · 애니메이션 CM", "—"),
]


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --ink:#13141a; --ink2:#3b3a45; --muted:#7a7787; --line:#e3e0ea;
  --paper:#f4f2f7; --card:#fff; --gold:#c9a227;
  --dur:.45s cubic-bezier(.4,0,.2,1);
}
html{scroll-behavior:smooth;scroll-padding-top:64px}
body{
  background:var(--paper);color:var(--ink);
  font-family:'Noto Serif KR',serif;font-weight:300;line-height:1.85;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1060px;margin:0 auto;padding:0 20px}
a{color:inherit}
:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
h1,h2,h3,.ui{font-family:'Outfit','M PLUS Rounded 1c',sans-serif}
h2,h3{font-weight:800;letter-spacing:-.3px}

/* ── top bar ── */
#top{position:sticky;top:0;z-index:30;background:rgba(244,242,247,.93);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
#top .wrap{display:flex;align-items:center;gap:8px;height:56px;overflow-x:auto;scrollbar-width:none}
#top .wrap::-webkit-scrollbar{display:none}
#top .home{font-family:'Outfit',sans-serif;font-size:12px;font-weight:800;
  border:1.5px solid #c8c4d2;border-radius:14px;padding:4px 12px;text-decoration:none;
  color:#666;white-space:nowrap;transition:border-color .15s,color .15s}
#top .home:hover{border-color:var(--ink);color:var(--ink)}
#top nav{display:flex;gap:4px;margin-left:4px}
#top nav a{font-family:'M PLUS Rounded 1c',sans-serif;font-weight:700;font-size:12.5px;
  text-decoration:none;color:var(--ink2);padding:5px 12px;border-radius:16px;white-space:nowrap;
  transition:background .15s,color .15s}
#top nav a:hover{background:var(--ink);color:#fff}

/* ── hero ── */
header.hero{background:var(--ink);color:#fff;position:relative;overflow:hidden}
header.hero::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:
    repeating-linear-gradient(115deg,rgba(255,255,255,.045) 0 1px,transparent 1px 9px),
    radial-gradient(80% 120% at 88% -20%,rgba(201,162,39,.28),transparent 62%)}
header.hero .wrap{padding:72px 20px 60px;position:relative;z-index:1}
.eyebrow{font-family:'Outfit',sans-serif;font-size:11px;font-weight:600;letter-spacing:.28em;
  text-transform:uppercase;color:var(--gold);margin-bottom:22px}
h1{font-size:clamp(34px,6.4vw,64px);font-weight:900;line-height:1.08;letter-spacing:-1.2px}
h1 .jp{display:block;font-family:'Noto Serif KR',serif;font-weight:300;
  font-size:clamp(13px,1.8vw,17px);letter-spacing:.34em;color:rgba(255,255,255,.5);margin-bottom:14px}
.lede{max-width:60ch;margin-top:22px;font-size:clamp(14px,1.6vw,16.5px);color:rgba(255,255,255,.76)}
.lede b{color:#fff;font-weight:400;box-shadow:inset 0 -8px 0 rgba(201,162,39,.35)}
.spec{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:1px;margin-top:42px;
  background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.12);border-radius:12px;overflow:hidden}
.spec div{background:var(--ink);padding:14px 16px}
.spec dt{font-family:'Outfit',sans-serif;font-size:10px;font-weight:600;letter-spacing:.16em;
  text-transform:uppercase;color:rgba(255,255,255,.45)}
.spec dd{margin-top:4px;font-size:14.5px;font-weight:400;line-height:1.5;color:#fff}

/* ── sections ── */
section{padding:70px 0 4px}
.shead{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  border-bottom:2px solid var(--ink);padding-bottom:12px;margin-bottom:28px}
.shead h2{font-size:clamp(21px,3.2vw,30px)}
.shead p{font-size:12.5px;color:var(--muted)}
.note{font-size:12.5px;color:var(--muted);max-width:70ch}

/* timeline */
ol.tl{list-style:none;border-left:2px solid var(--line);margin-left:4px}
ol.tl li{position:relative;padding:0 0 24px 24px}
ol.tl li::before{content:"";position:absolute;left:-7px;top:11px;width:12px;height:12px;border-radius:50%;
  background:var(--paper);border:2px solid #bfbbc9}
ol.tl li.hi::before{background:var(--gold);border-color:var(--gold);box-shadow:0 0 0 5px rgba(201,162,39,.2)}
ol.tl time{font-family:'Outfit',sans-serif;font-size:11.5px;font-weight:600;letter-spacing:.06em;color:var(--muted)}
ol.tl h3{font-size:16px;margin:2px 0 3px}
ol.tl p{font-size:13.5px;color:var(--ink2);max-width:62ch}

/* bands */
.band{margin-bottom:44px;background:var(--card);border:1px solid var(--line);border-radius:16px;
  overflow:hidden;box-shadow:0 1px 2px rgba(19,20,26,.04),0 10px 26px rgba(19,20,26,.05)}
.band-top{display:flex;align-items:center;gap:18px;padding:20px 22px;
  border-left:6px solid var(--bc);background:var(--bbg)}
.band-top img{height:46px;width:auto;max-width:150px;object-fit:contain;flex-shrink:0}
.band-top .jp{font-family:'Outfit',sans-serif;font-size:10.5px;font-weight:600;
  letter-spacing:.2em;color:var(--bdk);opacity:.6}
.band-top h3{font-size:clamp(19px,2.7vw,26px);color:var(--bdk)}
.band-top p{font-size:13.5px;color:var(--bdk);opacity:.85;max-width:66ch;margin-top:6px}
.vids{display:flex;gap:10px;flex-wrap:wrap;padding:0 22px 18px}
.vids.pv{padding:0 0 24px}
.vid{width:150px;text-decoration:none;color:var(--ink2)}
.vid .thumb{position:relative;display:block;border-radius:9px;overflow:hidden;
  background:#000;aspect-ratio:16/9;border:1px solid var(--line)}
.vid img{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .4s cubic-bezier(.4,0,.2,1),opacity .2s;opacity:.92}
.vid:hover img{transform:scale(1.06);opacity:1}
.vid .play{position:absolute;left:50%;top:50%;width:0;height:0;
  transform:translate(-38%,-50%);
  border-left:13px solid rgba(255,255,255,.94);
  border-top:8px solid transparent;border-bottom:8px solid transparent;
  filter:drop-shadow(0 1px 3px rgba(0,0,0,.6))}
.vid .vlabel{display:block;margin-top:6px;font-family:'M PLUS Rounded 1c',sans-serif;
  font-size:11.5px;font-weight:700;line-height:1.4}
.vid:hover .vlabel{color:var(--ink)}

.lineup{padding:15px 22px 8px;font-size:13.5px;color:var(--ink2);
  display:flex;flex-wrap:wrap;gap:4px 14px}
.lineup b{font-family:'Outfit',sans-serif;font-size:10px;font-weight:800;letter-spacing:.12em;
  color:var(--bc);margin-right:3px}

/* cards */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(252px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:19px}
.card h3{font-size:16.5px;margin-bottom:7px}
.card p{font-size:13.5px;color:var(--ink2)}

/* table */
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{text-align:left;font-family:'Outfit',sans-serif;font-size:10px;font-weight:600;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted);padding:0 12px 8px 0;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:11px 12px 11px 0;border-bottom:1px solid var(--line);vertical-align:top}
td.b{font-family:'M PLUS Rounded 1c',sans-serif;font-weight:700;white-space:nowrap}
td.song{font-size:15px}
td.dim{color:var(--muted)}
td.num{font-family:'Outfit',sans-serif;font-variant-numeric:tabular-nums;color:var(--muted)}
.tag{display:inline-block;margin-left:7px;padding:1px 7px;border-radius:9px;
  background:#fbf6e6;border:1px solid var(--gold);color:#8c6f12;
  font-family:'M PLUS Rounded 1c',sans-serif;font-size:9.5px;font-weight:700;vertical-align:2px}

/* rewards */
.rw{display:grid;grid-template-columns:repeat(auto-fit,minmax(206px,1fr));gap:9px}
.rw div{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:12px 14px}
.rw div.done{border-color:var(--gold);background:#fbf6e6}
.rw .n{font-family:'Outfit',sans-serif;font-size:11.5px;font-weight:800;letter-spacing:.05em;color:var(--gold)}
.rw .t{font-size:12.5px;color:var(--ink2);margin-top:2px}
.rw .ck{font-family:'Outfit',sans-serif;font-size:9.5px;font-weight:700;letter-spacing:.1em;
  color:var(--gold);margin-top:5px}

.subh{font-family:'Outfit',sans-serif;font-size:15px;font-weight:800;margin:34px 0 13px}
footer{margin-top:74px;background:var(--ink);color:rgba(255,255,255,.55)}
footer .wrap{padding:32px 20px 54px}
footer p{font-size:12px;max-width:78ch;margin-bottom:6px}

@media (max-width:640px){
  header.hero .wrap{padding:50px 20px 42px}
  .band-top{flex-direction:column;align-items:flex-start;gap:10px}
}
"""


def vids_html(items):
    """유튜브 썸네일 카드 스트립."""
    if not items:
        return ""
    o = ['<div class="vids">']
    for label, vid in items:
        o.append(
            f'<a class="vid" href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener">'
            f'<span class="thumb"><img src="https://i.ytimg.com/vi/{vid}/mqdefault.jpg" alt="" loading="lazy">'
            f'<span class="play"></span></span>'
            f'<span class="vlabel">{esc(label)}</span></a>')
    o.append('</div>')
    return "".join(o)


def build(bands):
    o = []
    w = o.append
    w('<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="UTF-8">')
    w('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w('<title>BanG Dream! Our Notes 정보</title>')
    w('<meta name="description" content="BanG Dream! Our Notes 공식 발표 정보 정리.">')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">')
    w('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;600;700;900'
      '&family=M+PLUS+Rounded+1c:wght@300;400;700;800&family=Outfit:wght@300;600;800;900&display=swap" rel="stylesheet">')
    w('<style>' + CSS + '</style>\n</head>\n<body>')

    # top bar
    w('<div id="top"><div class="wrap">')
    w('<a class="home" href="index.html">&#8592; 아워노츠</a>')
    w('<nav>'
      '<a href="#tl">타임라인</a><a href="#bands">5밴드</a><a href="#sys">시스템</a>'
      '<a href="#music">수록곡</a><a href="#pre">사전등록</a>'
      '</nav>')
    w('</div></div>')

    # hero
    w('<header class="hero"><div class="wrap">')
    w('<p class="eyebrow">BanG Dream! Project · 신작 모바일 게임</p>')
    w('<h1>BanG Dream!<br>Our Notes</h1>')
    w('<p class="lede">MyGO!!!!!와 Ave Mujica에서 시작하는 <b>다섯 밴드의 이야기</b>. '
      '공식 사이트와 일본 · 한국 공식 X, 부시로드 프레스 릴리스에 공개된 정보를 정리했다. '
      f'기준 {UPDATED}.</p>')
    w('<dl class="spec">')
    for k, v in SPECS:
        w(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>')
    w('</dl></div></header>')

    w('<div class="wrap">')

    # timeline
    w('<section id="tl"><div class="shead"><h2>발표 타임라인</h2>'
      '<p>공식 사이트 NEWS · 프레스 릴리스 기준</p></div><ol class="tl">')
    for d, t, s, hi in TIMELINE:
        cls = ' class="hi"' if hi else ''
        w(f'<li{cls}><time>{esc(d)}</time><h3>{esc(t)}</h3>'
          + (f'<p>{esc(s)}</p>' if s else '') + '</li>')
    w('</ol></section>')

    # bands
    w('<section id="bands"><div class="shead"><h2>다섯 밴드</h2>'
      '<p>기존 3밴드 + 신규 millsage · 일가 Dumb Rock! · 공식 영상 16편</p></div>')
    w(vids_html(PV).replace('<div class="vids">', '<div class="vids pv">', 1))
    for band in BAND_ORDER:
        th = BAND_THEMES[band]
        jp, intro = BAND_INTRO[band]
        w(f'<div class="band" style="--bc:{th["primary"]};--bbg:{th["bg"]};--bdk:{th["dark"]}">')
        w('<div class="band-top">')
        w(f'<img src="{esc(BAND_LOGO_FILES[band])}" alt="{esc(band)} 로고" loading="lazy">')
        jp_html = f'<span class="jp">{esc(jp)}</span>' if jp else ''
        w(f'<div>{jp_html}<h3>{esc(band)}</h3><p>{esc(intro)}</p></div>')
        w('</div>')
        names = ' · '.join(
            f'<b>{esc(r["악기"])}</b> {esc(r["이름(한글)"])}' for r in bands[band])
        w(f'<div class="lineup">{names}</div>')
        w(vids_html(BAND_MOVIES.get(band, [])))
        w('</div>')
    w('<p class="note" style="margin-top:-26px">스토리 소개 트레일러는 신규 2밴드만 공개됐고, '
      'MyGO!!!!! · Ave Mujica는 게임 소개 CM이 따로 있다. 영상은 전부 공식 YouTube. '
      '멤버별 상세 프로필 — CV · 소속 · 생일 · 좋아하는 것 · 의상 전환은 '
      '<a href="index.html">캐릭터 프로필</a>에 있다. '
      '무겐다이 뮤타입은 버추얼 밴드라 CV와 소속이 공개되지 않았고, '
      'millsage는 야쿠시지 리아, 일가 Dumb Rock!은 타치바나 메이 · 스즈미 사쿠라가 신규 캐스트로 먼저 공개됐다.</p></section>')

    # system
    w('<section id="sys"><div class="shead"><h2>게임 시스템</h2><p>공식 사이트 System 페이지</p></div><div class="cards">')
    for t, d in SYSTEM:
        w(f'<div class="card"><h3>{esc(t)}</h3><p>{esc(d)}</p></div>')
    w('</div></section>')

    # music
    w('<section id="music"><div class="shead"><h2>수록곡</h2>'
      '<p>출시 시점 70곡 이상 · 아래는 CBT 실측 + 이후 공식 발표분</p></div>')
    w('<div class="subh" style="margin-top:0">커버곡</div><div class="scroll"><table>')
    w('<thead><tr><th>밴드</th><th>곡명</th><th>원곡</th><th>출처</th></tr></thead><tbody>')
    for b, s, artist, src, later in MUSIC:
        tag = '<span class="tag">CBT 이후 공개</span>' if later else ''
        w(f'<tr><td class="b">{esc(b)}</td><td class="song">{esc(s)}{tag}</td>'
          f'<td>{esc(artist)}</td><td class="dim">{esc(src)}</td></tr>')
    w('</tbody></table></div>')
    w('<div class="subh">오리지널곡</div><div class="scroll"><table>')
    w('<thead><tr><th>밴드</th><th>곡 수</th><th>수록곡</th></tr></thead><tbody>')
    for b, n, songs in ORIGINAL:
        w(f'<tr><td class="b">{esc(b)}</td><td class="num">{n}</td><td>{esc(songs)}</td></tr>')
    w('</tbody></table></div>')
    w('<p class="note" style="margin-top:14px">곡 목록은 2026년 6월 클로즈드 베타 수록분이 기준이라 정식 서비스 시점에는 달라질 수 있다. '
      'ホワイトノイズ와 unravel은 CBT 이후 공식 발표된 곡이고, millsage의 unravel은 8월 20일 각 음원 서비스에 선행 배포됐다. '
      '나머지 수록곡은 공식 X에서 순차 공개 예정.</p></section>')

    # pre-register
    w('<section id="pre"><div class="shead"><h2>사전등록 · 캠페인</h2><p>일본 / 한국 동시 진행 중</p></div>')
    w('<div class="subh" style="margin-top:0">등록자 수 달성 보상</div><div class="rw">')
    for n, t, done in REWARD:
        w(f'<div class="{"done" if done else ""}"><div class="n">{esc(n)} 명</div>'
          f'<div class="t">{esc(t)}</div>' + ('<div class="ck">달성</div>' if done else '') + '</div>')
    w('</div>')
    w('<div class="cards" style="margin-top:24px">')
    for t, d in CAMPAIGN:
        w(f'<div class="card"><h3>{esc(t)}</h3><p>{esc(d)}</p></div>')
    w('</div>')
    w('<div class="scroll" style="margin-top:24px"><table>'
      '<thead><tr><th>채널</th><th>계정 / 주소</th><th>팔로워</th></tr></thead><tbody>')
    for label, url, txt, fol in CHANNELS:
        w(f'<tr><td class="b">{esc(label)}</td>'
          f'<td><a href="{esc(url)}" target="_blank" rel="noopener">{esc(txt)}</a></td>'
          f'<td class="num">{esc(fol)}</td></tr>')
    w('</tbody></table></div></section>')

    w('</div>')  # /wrap

    w('<footer><div class="wrap">')
    w('<p>자료 출처 — BanG Dream! Our Notes 공식 사이트(News / Band / Character / System / Music / Pre-register), '
      '공식 X @bang_dream_on · @bangdreamon_KR, 부시로드 프레스 릴리스(PR TIMES). '
      f'갱신 {UPDATED}.</p>')
    w('<p>캐릭터 프로필과 초상은 our_notes.csv 기준. 팬이 만든 비영리 정리본이다.</p>')
    w('<p>©BanG Dream! Project ©FROMTOKYO ©Bushiroad</p>')
    w('</div></footer>')
    w('<script src="nav.js"></script>')
    w('</body>\n</html>')
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="our_notes.csv")
    ap.add_argument("--out", default="info.html")
    a = ap.parse_args()

    rows = load_csv(a.csv)
    bands = {b: [] for b in BAND_ORDER}
    for r in rows:
        b = (r.get("밴드") or "").strip()
        if b in bands:
            bands[b].append(r)
    html = build(bands)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"생성 완료: {a.out}  (멤버 {len(rows)}명)")


if __name__ == "__main__":
    main()
