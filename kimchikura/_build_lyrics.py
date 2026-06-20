"""
morfonica_lyrics_cache.txt를 읽어 data/morfonica.js의 각 곡에 lyrics 필드를 추가한다.
사용: python _build_lyrics.py
"""
import re, json, sys, os

sys.stdout.reconfigure(encoding='utf-8')

CACHE = r'D:\서울대학원\통계 관련\뱅드림 관련\[] 홈피_깃헙io\발매곡목록\morfonica_lyrics_cache.txt'
MORFONICA_JS = os.path.join(os.path.dirname(__file__), 'data', 'morfonica.js')

# ── 1. 캐시 파싱 ──────────────────────────────────────────────
with open(CACHE, encoding='utf-8') as f:
    content = f.read()

lyric_map = {}
for block in re.split(r'\n(?=제목: )', content.strip()):
    title = block.split('\n')[0].replace('제목: ', '').strip()
    parts = block.split('\n가사:\n', 1)
    lyrics = parts[1].strip() if len(parts) > 1 else ''
    # 빌드 sentinel(<<<END>>>) 제거 — 렌더 시 가사 끝에 노출되지 않도록
    lyrics = re.sub(r'\s*<<<END>>>\s*$', '', lyrics)
    lyric_map[title] = lyrics

print(f'캐시: {len(lyric_map)}곡')

# ── 2. morfonica.js 읽기 ──────────────────────────────────────
with open(MORFONICA_JS, encoding='utf-8') as f:
    js_src = f.read()

# window.DATA_morfonica = [ ... ]; 추출
m = re.search(r'window\.DATA_morfonica\s*=\s*(\[[\s\S]*?\]);', js_src)
if not m:
    print('ERROR: DATA_morfonica 파싱 실패')
    sys.exit(1)

data = json.loads(m.group(1))

# ── 3. lyrics 필드 삽입 ───────────────────────────────────────
matched = 0
for song in data:
    lyrics = lyric_map.get(song['title'], '')
    song['lyrics'] = lyrics
    if lyrics:
        matched += 1

print(f'가사 매칭: {matched}/{len(data)}곡')

# ── 4. morfonica.js 덮어쓰기 ─────────────────────────────────
header = """/* 모르포니카 발매곡 데이터 (발매곡목록/morfonica.csv + lyrics_cache 에서 생성).
   title   : 원어 제목          titleKo: 한국어 번역
   date    : 발매일              cover  : 앨범 커버 URL
   type    : 오리지널|타이업|커버  youtube: YouTube 링크
   namu    : 나무위키/출처 링크   lyrics : 가사 (원문\\n발음\\n번역 3행 반복) */
window.DATA_morfonica = """

# JSON을 예쁘게 직렬화 (indent 2, ensure_ascii False)
json_str = json.dumps(data, ensure_ascii=False, indent=2)
new_js = header + json_str + ';\n'

with open(MORFONICA_JS, 'w', encoding='utf-8') as f:
    f.write(new_js)

print(f'완료: {MORFONICA_JS}')
