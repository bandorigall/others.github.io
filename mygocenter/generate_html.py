"""
personality_results.json 을 읽어 HTML 리포트를 생성하고 브라우저로 열기.

탭1: 전체 회차 목록 (회차순 정렬, 멤버 필터 버튼)
탭2: 멤버별 통계 (출연 횟수, 월별 출연 그래프)

실행:
    python generate_html.py
출력:
    personality_report.html
"""

import json
import os
import re
import webbrowser
from collections import defaultdict
from datetime import date
from pathlib import Path

MEMBER_ORDER = [
    "燈",
    "愛音",
    "楽奈",
    "そよ",
    "立希",
    "羊宮妃那（高松燈 役）",
    "立石凛（千早愛音 役）",
    "青木陽菜（要楽奈 役）",
    "小日向美香（長崎そよ 役）",
    "林鼓子（椎名立希 役）",
]

MEMBER_KO = {
    "燈":                       "토모리",
    "愛音":                      "아논",
    "楽奈":                      "라나",
    "そよ":                      "소요",
    "立希":                      "타키",
    "羊宮妃那（高松燈 役）":       "요우미야 히나 (타카마츠 토모리 역)",
    "立石凛（千早愛音 役）":       "타테이시 린 (치하야 아논 역)",
    "青木陽菜（要楽奈 役）":       "아오키 히나 (카나메 라나 역)",
    "小日向美香（長崎そよ 役）":   "코히나타 미카 (나가사키 소요 역)",
    "林鼓子（椎名立希 役）":       "하야시 코코 (시이나 타키 역)",
}


def normalize_name(name: str) -> str:
    """괄호 표기와 役 앞 띄어쓰기를 통일한다."""
    name = name.replace("(", "（").replace(")", "）")
    name = re.sub(r"\s*役）", " 役）", name)
    if name.startswith("）"):
        return ""
    return name.strip()


def split_members(personality: str) -> list[str]:
    """・ 또는 、로 구분된 멤버 목록을 정규화해서 반환한다."""
    raw = re.split(r"[・、]", personality)
    result = []
    for n in raw:
        n = normalize_name(n.strip())
        if n:
            result.append(n)
    return result

INPUT_JSON = "personality_results.json"
POSTPRO_JSON = "personality_results_postpro.json"
OUTPUT_HTML = "index.html"


def load_results(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_ep_number(title: str) -> int:
    """제목에서 # 뒤 숫자를 회차 번호로 파싱한다."""
    m = re.search(r"#(\d+)", title)
    return int(m.group(1)) if m else 0


def parse_yearmonth(title: str) -> str | None:
    """
    title 에 날짜 정보가 없으므로 video_id 기반 정렬 순서를 활용.
    실제 날짜는 yt-dlp upload_date 가 없으므로 회차 번호로 근사치 추정.
    회차 1 = 2020-04 기준, 주 1회 업로드 가정.
    """
    return None  # 날짜 없이 회차 번호 기반 그래프 사용


def collect_members(results: list[dict]) -> list[str]:
    """전체 멤버 목록을 MEMBER_ORDER 순서로 반환한다. 미등록 멤버는 뒤에 추가."""
    seen: set[str] = set()
    for r in results:
        p = r.get("personality") or ""
        for name in split_members(p):
            seen.add(name)
    known = [m for m in MEMBER_ORDER if m in seen]
    unknown = sorted(seen - set(MEMBER_ORDER))
    return known + unknown


def build_html(results: list[dict]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    # 회차 번호 기준 정렬
    results = sorted(results, key=lambda r: parse_ep_number(r.get("title", "")), reverse=True)

    members = collect_members(results)

    # 캐릭터 퍼스널 컬러 (캐릭명·성우명 공통)
    _char_colors = ["#77BBDD", "#FF8899", "#77DD77", "#FFDD88", "#7777AA"]
    member_color = {m: _char_colors[i % len(_char_colors)] for i, m in enumerate(MEMBER_ORDER)}
    # MEMBER_ORDER 미등록 멤버는 기본색
    for m in members:
        if m not in member_color:
            member_color[m] = "#94a3b8"

    # 멤버 필터 버튼 HTML
    filter_buttons = '<button class="filter-btn active" data-member="all">ALL</button>\n'
    for m in members:
        col = member_color[m]
        label = MEMBER_KO.get(m, m)
        filter_buttons += f'<button class="filter-btn" data-member="{m}" style="--mc:{col}">{label}</button>\n'

    # 테이블 rows
    rows_html = ""
    for r in results:
        title = r.get("title") or ""
        vid = r.get("video_id") or ""
        personality = r.get("personality") or ""
        ep_num = parse_ep_number(title)
        url = f"https://www.youtube.com/watch?v={vid}" if vid else "#"

        member_list = split_members(personality) if personality else []
        data_members = " ".join(member_list)

        badges = ""
        for name in member_list:
            col = member_color.get(name, "#94a3b8")
            label = MEMBER_KO.get(name, name)
            badges += f'<span class="badge" style="--mc:{col}">{label}</span>'

        status_class = "found" if personality else "missing"
        status_text = badges if personality else '<span class="missing-text">정보 없음</span>'

        rows_html += f"""<tr class="{status_class}" data-members="{data_members}">
            <td class="ep-num">#{ep_num}</td>
            <td class="title"><a href="{url}" target="_blank" rel="noopener">{title}</a></td>
            <td class="personality">{status_text}</td>
        </tr>\n"""

    # 통계 탭: 멤버별 카운트
    total = len(results)
    found = sum(1 for r in results if r.get("personality"))
    member_counts: dict[str, int] = {}
    for r in results:
        p = r.get("personality") or ""
        for name in split_members(p):
            member_counts[name] = member_counts.get(name, 0) + 1

    max_count = max(member_counts.values()) if member_counts else 1

    def stat_card(name: str) -> str:
        count = member_counts.get(name, 0)
        pct = round(count / total * 100) if total else 0
        bar_w = round(count / max_count * 100) if max_count else 0
        col = member_color.get(name, "#94a3b8")
        ko = MEMBER_KO.get(name, name)
        return f"""<div class="stat-card">
            <div class="stat-header">
                <span class="stat-name" style="color:{col}">{ko}</span>
                <span class="stat-count">{count}회 <span class="stat-pct">({pct}%)</span></span>
            </div>
            <div class="stat-bar-wrap">
                <div class="stat-bar" style="width:{bar_w}%;background:{col}"></div>
            </div>
        </div>"""

    # 5행 2열 (캐릭 | 성우) 페어드 레이아웃
    char_members = MEMBER_ORDER[:5]
    va_members = MEMBER_ORDER[5:]
    stat_rows_html = ""
    for c, v in zip(char_members, va_members):
        stat_rows_html += f"""<div class="stat-pair-row">{stat_card(c)}{stat_card(v)}</div>\n"""

    # 월별 출연 데이터
    from collections import defaultdict
    month_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in results:
        ud = r.get("upload_date", "")
        if ud and len(ud) == 8 and ud.isdigit():
            ym = f"{ud[:4]}-{ud[4:6]}"
            for name in split_members(r.get("personality") or ""):
                month_counts[ym][name] += 1

    has_dates = len(month_counts) > 0
    if has_dates:
        months = sorted(month_counts.keys())
        chart_labels = json.dumps(months, ensure_ascii=False)
        chart_title = "월별 출연 현황"
    else:
        # upload_date 없는 경우 회차 20단위 폴백
        ep_nums = [parse_ep_number(r.get("title", "")) for r in results]
        min_ep = min((e for e in ep_nums if e > 0), default=1)
        max_ep = max(ep_nums, default=1)
        step = 20
        buckets = list(range((min_ep // step) * step, max_ep + step, step))
        months = [f"#{b}~#{b+step-1}" for b in buckets]
        chart_labels = json.dumps(months, ensure_ascii=False)
        chart_title = "회차 구간별 출연 현황 (20회 단위)"

    char_set = set(MEMBER_ORDER[:5])
    chart_datasets = []
    for name in members:
        col = member_color.get(name, "#94a3b8")
        if has_dates:
            data = [month_counts[ym].get(name, 0) for ym in months]
        else:
            data = [0] * len(months)
            for r in results:
                ep_n = parse_ep_number(r.get("title", ""))
                p = r.get("personality") or ""
                if not p or ep_n == 0:
                    continue
                idx = (ep_n - buckets[0]) // step
                if 0 <= idx < len(months) and name in split_members(p):
                    data[idx] += 1
        chart_datasets.append({
            "label": MEMBER_KO.get(name, name),
            "data": data,
            "color": col,
            "dash": name not in char_set,
        })

    chart_data_json = json.dumps(chart_datasets, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>迷子集会 パーソナリティ</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Space+Mono:wght@400;700&display=swap');

:root {{
  --bg: #080810;
  --surface: #111118;
  --surface2: #18181f;
  --surface3: #1f1f2a;
  --border: #2a2a3a;
  --text: #dde1f0;
  --text-muted: #6b7280;
  --text-dim: #9ca3af;
  --accent: #c084fc;
  --accent2: #818cf8;
  --found-bg: #0f1420;
  --missing-bg: #150e0e;
  --radius: 10px;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'Noto Sans JP', sans-serif;
  min-height: 100vh;
  padding: 0;
}}

/* 헤더 */
.header {{
  padding: 2.5rem 2rem 0;
  max-width: 1200px;
  margin: 0 auto;
}}
.header-top {{
  display: flex;
  align-items: baseline;
  gap: 1rem;
  margin-bottom: 0.3rem;
}}
.header h1 {{
  font-family: 'Space Mono', monospace;
  font-size: 1.5rem;
  background: linear-gradient(120deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}}
.header-sub {{
  font-size: 0.78rem;
  color: var(--text-muted);
  letter-spacing: 0.08em;
}}

/* 요약 배지 */
.summary-row {{
  display: flex;
  gap: 0.6rem;
  margin: 1rem 0 1.5rem;
  flex-wrap: wrap;
}}
.summary-badge {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 0.3rem 0.9rem;
  font-size: 0.8rem;
  color: var(--text-dim);
}}
.summary-badge strong {{
  color: var(--accent);
  font-family: 'Space Mono', monospace;
}}

/* 탭 */
.tabs {{
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}}
.tab-btn {{
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-family: 'Noto Sans JP', sans-serif;
  font-size: 0.88rem;
  padding: 0.75rem 1.2rem;
  margin-bottom: -1px;
  transition: color 0.2s, border-color 0.2s;
}}
.tab-btn:hover {{ color: var(--text); }}
.tab-btn.active {{
  color: var(--accent);
  border-bottom-color: var(--accent);
}}

/* 탭 패널 */
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

.panel-inner {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 2rem 3rem;
}}

/* 필터 */
.filter-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 1.2rem;
  align-items: center;
}}
.mode-btn {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--accent);
  cursor: pointer;
  font-family: 'Space Mono', monospace;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.3rem 0.7rem;
  transition: all 0.15s;
  margin-right: 0.3rem;
}}
.mode-btn:hover {{ background: var(--surface3); }}
.filter-divider {{
  width: 1px;
  height: 1.2rem;
  background: var(--border);
  margin: 0 0.2rem;
}}
.filter-btn {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--text-dim);
  cursor: pointer;
  font-family: 'Noto Sans JP', sans-serif;
  font-size: 0.78rem;
  padding: 0.3rem 0.85rem;
  transition: all 0.15s;
}}
.filter-btn:hover {{
  border-color: var(--mc, var(--accent));
  color: var(--mc, var(--accent));
}}
.filter-btn.active {{
  background: color-mix(in srgb, var(--mc, var(--accent)) 15%, transparent);
  border-color: var(--mc, var(--accent));
  color: var(--mc, var(--accent));
}}

/* 테이블 */
.table-wrap {{
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}}
table {{ width: 100%; border-collapse: collapse; }}
thead tr {{
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
}}
th {{
  color: var(--text-muted);
  font-family: 'Space Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  padding: 0.75rem 1rem;
  text-align: left;
  text-transform: uppercase;
}}
tbody tr {{
  background: var(--found-bg);
  border-bottom: 1px solid var(--border);
  transition: background 0.12s;
}}
tbody tr:last-child {{ border-bottom: none; }}
tbody tr:hover {{ background: var(--surface3); }}
tbody tr.missing {{ background: var(--missing-bg); }}
td {{ font-size: 0.85rem; padding: 0.65rem 1rem; vertical-align: middle; }}
.ep-num {{
  color: var(--text-muted);
  font-family: 'Space Mono', monospace;
  font-size: 0.8rem;
  white-space: nowrap;
  width: 4.5rem;
}}
.title a {{ color: #93c5fd; text-decoration: none; }}
.title a:hover {{ text-decoration: underline; }}
.badge {{
  border-radius: 5px;
  border: 1px solid color-mix(in srgb, var(--mc) 40%, transparent);
  background: color-mix(in srgb, var(--mc) 12%, transparent);
  color: var(--mc);
  display: inline-block;
  font-size: 0.75rem;
  margin: 0.1rem 0.2rem 0.1rem 0;
  padding: 0.15rem 0.5rem;
  white-space: nowrap;
}}
.missing-text {{ color: #374151; font-size: 0.78rem; }}

/* 통계 탭 */
.stat-pair-grid {{
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-bottom: 2.5rem;
}}
.stat-pair-row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}}
.stat-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
}}
.stat-header {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.6rem;
}}
.stat-name {{
  font-size: 0.85rem;
  font-weight: 500;
}}
.stat-count {{
  font-family: 'Space Mono', monospace;
  font-size: 0.88rem;
  color: var(--text);
}}
.stat-pct {{
  color: var(--text-muted);
  font-size: 0.75rem;
}}
.stat-bar-wrap {{
  background: var(--surface3);
  border-radius: 3px;
  height: 5px;
  overflow: hidden;
}}
.stat-bar {{
  border-radius: 3px;
  height: 100%;
  transition: width 0.6s cubic-bezier(.4,0,.2,1);
}}

/* 차트 */
.chart-section {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  position: relative;
}}
.chart-tooltip {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  display: none;
  min-width: 180px;
  padding: 0.6rem 0.8rem;
  pointer-events: none;
  position: absolute;
  z-index: 10;
}}
.tt-title {{
  color: var(--text-muted);
  font-family: 'Space Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.05em;
  margin-bottom: 0.4rem;
}}
.tt-row {{
  align-items: center;
  display: flex;
  font-size: 0.78rem;
  gap: 0.4rem;
  padding: 0.1rem 0;
}}
.tt-dot {{
  border-radius: 50%;
  flex-shrink: 0;
  height: 7px;
  width: 7px;
}}
.tt-val {{
  font-family: 'Space Mono', monospace;
  margin-left: auto;
  color: var(--text);
}}
.chart-section h2 {{
  color: var(--text-dim);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  margin-bottom: 1.2rem;
  text-transform: uppercase;
}}
.chart-legend {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}}
.legend-item {{
  align-items: center;
  display: flex;
  font-size: 0.75rem;
  gap: 0.35rem;
  cursor: pointer;
  opacity: 1;
  transition: opacity 0.2s;
}}
.legend-item.hidden {{ opacity: 0.3; }}
.legend-dot {{
  border-radius: 50%;
  height: 8px;
  width: 8px;
  flex-shrink: 0;
}}
canvas {{ width: 100% !important; }}

@media (max-width: 640px) {{
  .header, .tabs, .panel-inner {{ padding-left: 1rem; padding-right: 1rem; }}
  th:nth-child(2), td:nth-child(2) {{ display: none; }}
  .stat-pair-row {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <h1>迷子集会</h1>
    <span class="header-sub">MyGO!!!!! パーソナリティ DATABASE</span>
  </div>
  <div class="summary-row">
    <span class="summary-badge">총 <strong>{total}</strong>회차</span>
    <span class="summary-badge">정보 있음 <strong>{found}</strong></span>
    <span class="summary-badge">정보 없음 <strong>{total - found}</strong></span>
    <span class="summary-badge" style="margin-left:auto">updated <strong>{today}</strong></span>
  </div>
</div>

<div class="tabs">
  <button class="tab-btn active" data-tab="list">회차 목록</button>
  <button class="tab-btn" data-tab="stats">멤버 통계</button>
</div>

<!-- 탭1: 회차 목록 -->
<div class="tab-panel active" id="tab-list">
  <div class="panel-inner">
    <div class="filter-row">
      <button class="mode-btn" id="mode-btn">OR</button>
      <div class="filter-divider"></div>
      {filter_buttons}
    </div>
    <div class="table-wrap">
      <table id="main-table">
        <thead>
          <tr>
            <th>회차</th>
            <th>제목</th>
            <th>パーソナリティ</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- 탭2: 멤버 통계 -->
<div class="tab-panel" id="tab-stats">
  <div class="panel-inner">
    <div class="stat-pair-grid">
      {stat_rows_html}
    </div>
    <div class="chart-section">
      <h2>{chart_title}</h2>
      <div class="chart-legend" id="chart-legend"></div>
      <canvas id="chart" height="320"></canvas>
      <div class="chart-tooltip" id="chart-tooltip"></div>
    </div>
  </div>
</div>

<script>
// 탭 전환
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  }});
}});

// 멤버 필터 (다중 선택 + AND/OR)
const filterBtns = document.querySelectorAll('.filter-btn');
const tableRows = document.querySelectorAll('#main-table tbody tr');
const modeBtn = document.getElementById('mode-btn');
let filterMode = 'or';
let selected = new Set();

function applyFilter() {{
  tableRows.forEach(row => {{
    if (selected.size === 0) {{ row.style.display = ''; return; }}
    const rowMembers = (row.dataset.members || '').split(' ').filter(Boolean);
    const match = filterMode === 'or'
      ? [...selected].some(m => rowMembers.includes(m))
      : [...selected].every(m => rowMembers.includes(m));
    row.style.display = match ? '' : 'none';
  }});
}}

modeBtn.addEventListener('click', () => {{
  filterMode = filterMode === 'or' ? 'and' : 'or';
  modeBtn.textContent = filterMode.toUpperCase();
  applyFilter();
}});

filterBtns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    const member = btn.dataset.member;
    if (member === 'all') {{
      selected.clear();
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }} else {{
      document.querySelector('.filter-btn[data-member="all"]').classList.remove('active');
      if (selected.has(member)) {{
        selected.delete(member);
        btn.classList.remove('active');
      }} else {{
        selected.add(member);
        btn.classList.add('active');
      }}
      if (selected.size === 0)
        document.querySelector('.filter-btn[data-member="all"]').classList.add('active');
    }}
    applyFilter();
  }});
}});

// 라인 차트 (Canvas 직접 구현)
(function() {{
  const labels = {chart_labels};
  const datasets = {chart_data_json};
  const canvas = document.getElementById('chart');
  const ctx = canvas.getContext('2d');
  const tooltip = document.getElementById('chart-tooltip');
  const pad = {{ top: 24, right: 24, bottom: 64, left: 40 }};
  const H = 340;
  const hiddenSets = new Set();
  let hoverIdx = -1;

  // 범례 생성
  const legend = document.getElementById('chart-legend');
  datasets.forEach((ds, i) => {{
    const item = document.createElement('div');
    item.className = 'legend-item';
    const lineStyle = ds.dash
      ? `border-top: 2px dashed ${{ds.color}}; width:14px; height:0`
      : `border-top: 2px solid ${{ds.color}}; width:14px; height:0`;
    item.innerHTML = `<span style="${{lineStyle}}; display:inline-block; flex-shrink:0"></span>${{ds.label}}`;
    item.addEventListener('click', () => {{
      hiddenSets.has(i) ? hiddenSets.delete(i) : hiddenSets.add(i);
      item.classList.toggle('hidden');
      draw();
    }});
    legend.appendChild(item);
  }});

  function dims() {{
    const W = canvas.parentElement.clientWidth - 48;
    return {{ W, cW: W - pad.left - pad.right, cH: H - pad.top - pad.bottom }};
  }}

  function xOf(li, cW) {{
    return labels.length < 2
      ? pad.left + cW / 2
      : pad.left + (li / (labels.length - 1)) * cW;
  }}

  function yOf(val, maxVal, cH) {{
    return pad.top + cH * (1 - val / maxVal);
  }}

  function draw(hIdx) {{
    const {{ W, cW, cH }} = dims();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, W, H);

    const vis = datasets.filter((_, i) => !hiddenSets.has(i));
    const maxVal = Math.max(...labels.map((_, li) =>
      Math.max(...vis.map(ds => ds.data[li] || 0))
    ), 1);

    // 격자선 + y축 레이블
    for (let i = 0; i <= 4; i++) {{
      const y = pad.top + cH * (1 - i / 4);
      ctx.strokeStyle = '#2a2a3a';
      ctx.lineWidth = 1;
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + cW, y); ctx.stroke();
      ctx.fillStyle = '#4b5563';
      ctx.font = '10px Space Mono, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(Math.round(maxVal * i / 4), pad.left - 6, y + 3);
    }}

    // 호버 세로선
    if (hIdx != null && hIdx >= 0) {{
      const hx = xOf(hIdx, cW);
      ctx.strokeStyle = 'rgba(255,255,255,0.12)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(hx, pad.top); ctx.lineTo(hx, pad.top + cH); ctx.stroke();
      ctx.setLineDash([]);
    }}

    // 라인 + 점
    vis.forEach(ds => {{
      ctx.strokeStyle = ds.color;
      ctx.lineWidth = ds.dash ? 1.5 : 2;
      ctx.globalAlpha = 0.9;
      ctx.setLineDash(ds.dash ? [5, 3] : []);
      ctx.beginPath();
      labels.forEach((_, li) => {{
        const x = xOf(li, cW), y = yOf(ds.data[li] || 0, maxVal, cH);
        li === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }});
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = ds.color;
      labels.forEach((_, li) => {{
        const x = xOf(li, cW), y = yOf(ds.data[li] || 0, maxVal, cH);
        const r = (hIdx != null && li === hIdx) ? 4.5 : 2.5;
        ctx.globalAlpha = (hIdx != null && li === hIdx) ? 1 : 0.8;
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      }});
    }});
    ctx.globalAlpha = 1;

    // x축 레이블
    ctx.fillStyle = '#6b7280';
    ctx.font = '9px Space Mono, monospace';
    ctx.textAlign = 'center';
    labels.forEach((label, li) => {{
      const x = xOf(li, cW);
      ctx.save();
      ctx.translate(x, pad.top + cH + 14);
      ctx.rotate(-Math.PI / 4);
      ctx.fillText(label, 0, 0);
      ctx.restore();
    }});
  }}

  // 호버
  canvas.addEventListener('mousemove', e => {{
    const rect = canvas.getBoundingClientRect();
    const {{ cW }} = dims();
    const mx = (e.clientX - rect.left) * (canvas.width / rect.width / (window.devicePixelRatio || 1));
    const step = labels.length > 1 ? cW / (labels.length - 1) : cW;
    let idx = Math.round((mx - pad.left) / step);
    idx = Math.max(0, Math.min(labels.length - 1, idx));
    if (idx !== hoverIdx) {{ hoverIdx = idx; draw(hoverIdx); }}
    showTooltip(e, idx);
  }});

  canvas.addEventListener('mouseleave', () => {{
    hoverIdx = -1;
    tooltip.style.display = 'none';
    draw();
  }});

  function showTooltip(e, idx) {{
    const vis = datasets.filter((_, i) => !hiddenSets.has(i));
    const entries = vis
      .map(ds => ({{ label: ds.label, val: ds.data[idx] || 0, color: ds.color }}))
      .filter(en => en.val > 0)
      .sort((a, b) => b.val - a.val);
    if (!entries.length) {{ tooltip.style.display = 'none'; return; }}
    tooltip.innerHTML = `<div class="tt-title">${{labels[idx]}}</div>` +
      entries.map(en =>
        `<div class="tt-row"><span class="tt-dot" style="background:${{en.color}}"></span><span>${{en.label}}</span><span class="tt-val">${{en.val}}회</span></div>`
      ).join('');
    tooltip.style.display = 'block';
    const pr = canvas.parentElement.getBoundingClientRect();
    let left = e.clientX - pr.left + 14;
    let top = e.clientY - pr.top - 10;
    if (left + tooltip.offsetWidth + 10 > pr.width) left -= tooltip.offsetWidth + 28;
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
  }}

  draw();
  window.addEventListener('resize', () => draw(hoverIdx >= 0 ? hoverIdx : undefined));
}})();
</script>
</body>
</html>"""
    return html


def main():
    if not Path(INPUT_JSON).exists():
        print(f"[ERROR] {INPUT_JSON} 파일이 없습니다. 먼저 extract_personality.py 를 실행하세요.")
        return

    import postpro
    postpro.main()

    results = load_results(POSTPRO_JSON)
    html = build_html(results)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    path = str(Path(OUTPUT_HTML).resolve())
    print(f"완료. {OUTPUT_HTML} 생성됨 ({len(results)}개 회차)")
    webbrowser.open(f"file:///{path}")


if __name__ == "__main__":
    main()