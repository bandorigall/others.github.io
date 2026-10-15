"""
발매곡목록/<band>.csv + 발매곡목록/lyrics/<원어제목>.txt → data/songs.js
(kimchikura 의 _build_lyrics.py 는 캐시 파일 파싱 + JS 정규식 패치 방식이었음.
 여기서는 CSV·가사 파일을 단일 소스로 두고 매번 통째로 재생성한다.)
사용: python build_data.py
"""
import csv, hashlib, io, json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', '발매곡목록')
OUT = os.path.join(HERE, 'data', 'songs.js')

# 방갤 마이고 콜표 v1.0 (no=6582806) 수록곡 → 곡 목록에 '콜표' 배지
CALLSHEET = {'mygo': {'迷星叫', '壱雫空', '影色舞', '聿日箋秋', '往欄印', '焚音打', '砂寸奏', '歩拾道', '証命讃歌', '音一会', '孤壊牢'}}

# (키, 탭 라벨, CSV 파일명) — 탭 순서대로
BANDS = [
    ('mygo', 'MyGO!!!!!', 'mygo.csv'),
    ('roselia', 'Roselia', 'roselia.csv'),
]


COVER_DIR = os.path.join(HERE, 'imgs', 'covers')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120'


def local_cover(url):
    """외부 커버는 CORP 헤더로 핫링크가 막혀(ERR_BLOCKED_BY_RESPONSE) 로컬 webp(96px)로 저장해 쓴다."""
    if not url:
        return ''
    from PIL import Image
    name = hashlib.md5(url.encode()).hexdigest()[:12] + '.webp'
    path = os.path.join(COVER_DIR, name)
    if not os.path.exists(path):
        raw = subprocess.run(['curl', '-sL', '-A', UA, '-e', 'https://bandori.fandom.com/', url],
                             capture_output=True).stdout
        try:
            im = Image.open(io.BytesIO(raw)).convert('RGB')
        except Exception:
            print('  커버 실패:', url)
            return ''
        im.thumbnail((96, 96))
        os.makedirs(COVER_DIR, exist_ok=True)
        im.save(path, 'WEBP', quality=80)
    return 'imgs/covers/' + name


def read_lyrics(title):
    path = os.path.join(SRC, 'lyrics', title + '.txt')
    if not os.path.exists(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return f.read().strip()


data = {'bands': []}
for key, label, fname in BANDS:
    songs = []
    with open(os.path.join(SRC, fname), encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            title = (row.get('제목(원어)') or '').strip()
            if not title:
                continue
            songs.append({
                'title': title,
                'titleKo': (row.get('제목(한국어)') or '').strip(),
                'date': (row.get('발매일 / 커버일') or '').strip(),
                'cover': local_cover((row.get('앨범커버') or '').strip()),
                'type': (row.get('곡유형') or '').strip(),
                'artist': (row.get('원곡가수') or '').strip(),
                'youtube': (row.get('링크') or '').strip(),
                'namu': (row.get('번역가사 링크') or '').strip(),
                'lyrics': read_lyrics(title),
                'call': title in CALLSHEET.get(key, set()),
            })
    n_ly = sum(1 for s in songs if s['lyrics'])
    print(f'{label}: {len(songs)}곡 (가사 {n_ly})')
    data['bands'].append({'key': key, 'label': label, 'songs': songs})

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('/* build_data.py 로 생성. 직접 수정하지 말고 발매곡목록 CSV·가사 파일을 고친 뒤 재빌드. */\n')
    f.write('window.DATA_songs = ')
    json.dump(data, f, ensure_ascii=False, indent=1)
    f.write(';\n')
print('→', OUT)
