"""
로젤내한/roselia.csv '가사(콜표)' → data/roselia_calls.js  (원본은 로젤내한 CSV 하나, 여기선 매번 재생성)
- HTML 화이트리스트 정제: p, br, b 만 남기고 색 표시는 클래스로 치환
    font color 빨강계열 → <span class="c-call">   (콜)
    font color 보라 등 기타 색 → <span class="c-call2">
    style background-color 있는 span → <span class="c-hl"> (하이콜 등 구간 표시)
  인라인 style·font-family·data-* 전부 제거 (다크 배경에서 글자 사라짐 방지)
- 콜가이드영상: 팬 채널(Roselive) 영상. playlist 파라미터는 떼고 저장.
사용: python build_calls.py
"""
import csv, html, json, os, re, sys, urllib.parse
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', '로젤내한', 'roselia.csv')
OUT = os.path.join(HERE, 'data', 'roselia_calls.js')

# 출연진 페이지(build_lineup.py)의 로젤 예상곡과 같은 목록·순서
SONGS = ['FIRE BIRD', 'BLACK SHOUT', 'PASSIONATE ANTHEM', 'R', 'Neo-Aspect', 'VIOLET LINE', 'ROZEN HORIZON',
         'ZEAL of proud', '熱色スターマイン', 'Ringing Bloom', '陽だまりロードナイト', 'この蒼き闇と光', 'XV']


class Clean(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.stack = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        style = (a.get('style') or '').lower()
        if tag in ('p', 'div'):
            self.out.append('<p>'); self.stack.append('</p>')
        elif tag == 'br':
            self.out.append('<br>')
        elif tag == 'b':
            self.out.append('<b>'); self.stack.append('</b>')
        elif tag == 'font' and a.get('color'):
            c = a['color'].lower()
            cls = 'c-call' if c in ('#ff0000', 'red', '#f00') else 'c-call2'
            self.out.append(f'<span class="{cls}">'); self.stack.append('</span>')
        elif tag == 'span' and 'background-color' in style:
            self.out.append('<span class="c-hl">'); self.stack.append('</span>')
        else:
            self.stack.append('')   # 태그 버리고 내용만

    def handle_endtag(self, tag):
        if tag == 'br':
            return
        if self.stack:
            self.out.append(self.stack.pop())

    def handle_data(self, data):
        self.out.append(html.escape(data))


def clean(h):
    p = Clean(); p.feed(h); p.close()
    s = ''.join(p.out) + ''.join(reversed(p.stack))
    s = re.sub(r'<p>\s*</p>', '', s)
    s = re.sub(r'(<p><br></p>){2,}', '<p><br></p>', s)
    return s


def strip_list(u):
    if not u:
        return ''
    q = urllib.parse.urlparse(u)
    v = urllib.parse.parse_qs(q.query).get('v')
    return f'https://www.youtube.com/watch?v={v[0]}' if v else u


rows = {r['제목(원어)']: r for r in csv.DictReader(open(SRC, encoding='utf-8-sig'))}
data = []
for t in SONGS:
    r = rows.get(t)
    h = clean((r['가사(콜표)'] + r['가사(콜표) 2'])) if r else ''
    data.append({'title': t, 'titleKo': (r or {}).get('제목(한국어)', ''), 'html': h,
                 'video': strip_list((r or {}).get('콜가이드영상', '').strip())})
    print(f'{t}: 콜표 {len(h)}자, 영상 {"O" if data[-1]["video"] else "-"}')
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('/* build_calls.py 로 생성 (원본: 로젤내한/roselia.csv). 직접 수정 금지. */\n')
    f.write('window.DATA_roselia_calls = ')
    json.dump(data, f, ensure_ascii=False)
    f.write(';\n')
print('→', OUT)
