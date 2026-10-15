"""
토요일(DAY2) 출연진·타임테이블 → lineup.html
- 시간표: 공식 사이트 API https://www.wonderli.vet/api/trpc/timetable.list (DAY2)
- 대표곡: 공식 채널(아티스트/레이블/Topic) 영상만. youtube oembed author_name 으로 검증한 값.
  MyGO!!!!! / Roselia = setlist.fm 2025-10~2026-08 공연 셋리 빈도 + 페스 단골 + 신곡 (곡별 근거 4번째 칸)
  로젤 서울 공연(2025-12-24) 셋리는 bandori.miraheze.org 기준(setlist.fm엔 곡 없음)
사용: python build_lineup.py
"""
import html, os, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape

# (스테이지, 시작, 끝, 이름, 한글명, 이미지, [(곡, 영상ID, 채널)], 곡 선정 근거)
LINEUP = [
 ('LIVET', '12:00', '12:30', 'The Shepherd Bois', '양치기소년단', 'the_shepherd_bois', [
   ('락스타가 된대도 난 너만 있으면 돼', 'GqIpQ7Crqys', '양치기소년단'),
   ('구름을 타고', 'UWjW769ajwA', '양치기소년단'),
   ('명예와 영광 (그리움과 기다림)', 'RRUV2DuFgHM', '양치기소년단')], ''),
 ('WONDER', '12:30', '13:00', 'Midnight Grand Orchestra', '', 'midnight_grand_orchestra', [
   ('Hyper Vip', 'FcNJfwfW52A', 'Midnight Grand Orchestra'),
   ('Midnight Mission', 'h0JrFYBqgEU', 'Midnight Grand Orchestra'),
   ('夜を待つよ', 'kX7ldIKFD60', 'Midnight Grand Orchestra'),
   ('Moonlightspeed', 'NI8KqzCvFsc', 'Midnight Grand Orchestra'),
   ('Highway', '5qwPLurdPsk', 'Midnight Grand Orchestra')], ''),
 ('LIVET', '13:00', '13:35', 'TAK with Hatsune Miku & Kasane Teto', '', 'tak_with_hatsune_miku_kasane_teto', [
   ('PPPP', '8Cm-7oCq9HA', 'TAK / DORIDORI'),
   ('numb numb', 'ba7YbGO2aq4', 'TAK / DORIDORI')], ''),
 ('WONDER', '13:35', '14:10', 'MyGO!!!!!', '마이고', 'mygo', [
   ('迷星叫', 'w-Gvclnnfpc', 'MyGO!!!!!', '2026년 공연 7/7 전부 · 통산 최다 46회'),
   ('壱雫空', 'cjyxTk_IfIY', 'MyGO!!!!! - Topic', '2026년 공연 6/7 · 10주년·MAJ·럭키페스 전부'),
   ('影色舞', 'iFIXi6zzCls', 'MyGO!!!!!', '2026년 공연 7/7 · 9th 양일 앵콜'),
   ('往欄印', 'JbSA9GjoUmU', 'MyGO!!!!! (1절 시청 영상)', '2026년 페스 3곳(10주년·MAJ·럭키페스) 전부'),
   ('聿日箋秋', 'MaogbGr8Qhg', 'MyGO!!!!!', 'MAJ · 9th 양일 · 상하이'),
   ('証命讃歌', 'I5s3q-_HCSk', 'MyGO!!!!! - Topic', '2026-03 싱글 · 9th 양일 · 럭키페스'),
   ('羅永線', 'fwTsHwFzOlg', 'MyGO!!!!! - Topic', '2026-07 신곡 · 9th 양일 · 럭키페스'),
   ('砂寸奏', 'uiWLU577gYY', 'MyGO!!!!!', '투맨·대만·9th 양일·럭키페스'),
   ('孤壊牢', 'sXJAfhKiUAI', 'MyGO!!!!! - Topic', '투맨·대만·9th DAY2·럭키페스'),
   ('歌いましょう鳴らしましょう', '_0FI8xSgI1s', 'MyGO!!!!!', '투맨·대만·9th 양일'),
   ('掌心正銘', 'Aww91itH5cQ', 'MyGO!!!!! - Topic', '투맨·대만·9th 양일'),
   ('素寄曲', 'uZSAArx6jKM', 'MyGO!!!!! - Topic', '2026-07-15 신곡 · 확인된 셋리 기준 라이브 미공개'),
   ('騒混出', 'GzbCOAHhwzM', 'MyGO!!!!! - Topic', '2026-07-15 신곡 · 확인된 셋리 기준 라이브 미공개')],
   '2026년 공연(10주년·투맨·대만·MAJ·9th 양일·럭키페스) 등장 빈도와 페스 무대 단골곡, 최신곡을 함께 고려해 고른 예습용 목록. 실제 세트리스트가 아님. 35분 무대라 이 중 7곡 안팎이 예상 범위.'),
 ('LIVET', '14:10', '14:50', 'Tani Yuuki', '', 'tani_yuuki', [
   ('Myra', '-9HxeXHuNjQ', 'Tani Yuuki - Topic'),
   ('W/X/Y', 'mp2-w15SXms', 'Tani Yuuki'),
   ('運命', 'yXG8qtd_Qag', 'Tani Yuuki')], ''),
 ('WONDER', '14:50', '15:30', 'yama', '', 'yama', [
   ('春を告げる', 'DC6JppqHkaM', 'yama'),
   ('色彩', 'E9Dru15yq9w', 'yama')], ''),
 ('LIVET', '15:30', '16:10', 'CHiCO with HoneyWorks', '', 'chico_with_honeyworks', [
   ('世界は恋に落ちている', 'wM4laths4-Y', 'Sony Music (Japan)'),
   ('我武者羅', 'iw557YNs6g0', 'CHiCO / CHiCO with HoneyWorks'),
   ('決戦スピリット', 'ErqUUYWfOBo', 'CHiCO / CHiCO with HoneyWorks'),
   ('リベンジゲーム', 'fhfV99A_OiY', 'CHiCO / CHiCO with HoneyWorks')], ''),
 ('WONDER', '16:10', '16:50', 'Roselia', '로젤리아', 'roselia', [
   ('FIRE BIRD', 'ac66DA0pDbg', 'Roselia - Topic', '서울 앵콜 · 10주년 · AX · 아리아케 양일'),
   ('BLACK SHOUT', 'MmnU-s1TdsI', 'Roselia - Topic', '서울 · 10주년 · AX · 아리아케 8/30'),
   ('PASSIONATE ANTHEM', '68Gwwqp1DK4', 'Roselia - Topic', '서울 앵콜 · 10주년 · AX · 아리아케 양일'),
   ('R', 'ZqdMPCDsCeE', 'Roselia - Topic', '서울 · AX · 아리아케 8/29'),
   ('Neo-Aspect', '03iVXFZ8jrs', 'Roselia - Topic', '서울 · AX · 아리아케 양일 오프닝'),
   ('VIOLET LINE', '-yVtSiKoc1c', 'Roselia - Topic', '10주년 · 아리아케 8/30'),
   ('ROZEN HORIZON', '8Cygbjd1h8Y', 'Roselia - Topic', '아리아케 양일'),
   ('ZEAL of proud', 'LKvJhHQN4Y8', 'Roselia - Topic', '10주년 · 아리아케 8/29'),
   ('熱色スターマイン', 'DZNOUNsvWps', 'Roselia - Topic', '서울'),
   ('Ringing Bloom', 'h4cEEXCPO8M', 'Roselia - Topic', '서울 · 아리아케 8/29'),
   ('陽だまりロードナイト', 'KjgjeK-ppd0', 'Roselia - Topic', '서울 · 아리아케 8/30'),
   ('この蒼き闇と光', 'IOTOr1UCyis', 'Roselia - Topic', '2026-09-10 신곡 · 확인된 셋리 기준 라이브 미공개'),
   ('XV', 'P9PXzNniuaY', 'Roselia - Topic', '2026-05-02 신곡 · 확인된 셋리 기준 라이브 미공개')],
   '2025-12-24 서울 내한(Neuweltfahrt, 고려대 화정체육관) 셋리, 2026년 10주년·애니메엑스포(AX)·아리아케 공연, 신곡을 함께 고려해 고른 예습용 목록. 실제 세트리스트가 아님. 40분 무대.'),
 ('LIVET', '16:50', '17:35', 'indigo la End', '', 'indigo_la_end', [
   ('夏夜のマジック', 'IMU0ctb7E60', 'indigo la End Official YouTube Channel'),
   ('名前は片想い', 'aqoeNOw4_uQ', 'indigo la End Official YouTube Channel')], ''),
 ('WONDER', '17:35', '18:20', 'Kyary Pamyu Pamyu', '캬리 파뮤파뮤', 'kyary_pamyu_pamyu', [
   ('PONPONPON', 'yzC4hFK5P3g', 'Warner Music Japan'),
   ('つけまつける', 'NLy4cvRx7Vc', 'Warner Music Japan'),
   ('にんじゃりばんばん', 'teMdjJ3w9iM', 'Warner Music Japan'),
   ('ファッションモンスター', 'GivkxpAVVC4', 'Warner Music Japan')], ''),
 ('LIVET', '18:20', '19:10', 'FREDERIC', '프레데릭', 'frederic', [
   ('オドループ', 'PCp2iXA1uLE', 'フレデリック FREDERIC official'),
   ('オンリーワンダー', 'oCrwzN6eb4Q', 'フレデリック FREDERIC official'),
   ('ジャンキー', 'VTUgZ3-Ovws', 'フレデリック FREDERIC official')], ''),
 ('WONDER', '19:10', '20:00', 'HANRORO', '한로로', 'hanroro', [
   ('입춘', 'pNi9PjmbUrI', '한로로 HANRORO'),
   ('사랑하게 될 거야', 'h0KIWaUEIgQ', '한로로 HANRORO'),
   ('0+0', '_Ngk-DCHfD0', '한로로 HANRORO')], ''),
 ('LIVET', '20:00', '21:00', 'SAMBOMASTER', '삼보마스터', 'sambomaster', [
   ('できっこないを やらなくちゃ', 'hFXaeaACCOk', 'サンボマスター'),
   ('世界はそれを愛と呼ぶんだぜ', 'izlKehxIEcA', 'サンボマスター'),
   ('花束', 'v03zRqF3o0U', 'サンボマスター')], ''),
 ('WONDER', '21:00', '22:00', '[Alexandros]', '알렉산드로스', 'alexandros', [
   ('ワタリドリ', 'O_DLtVuiqhI', 'ALEXANDROSchannel'),
   ('閃光', 'xfG6L9I7N8I', 'ALEXANDROSchannel'),
   ('Starrrrrrr', 'iCO8c7HafII', '[Alexandros] - Topic')], ''),
]

rows = []
for stage, st, en, name, ko, img, songs, note in LINEUP:
    bang = name in ('MyGO!!!!!', 'Roselia')
    li = ''.join(
        f'<li><a href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener">{E(x[0])}</a>'
        f'<span class="s-note">{E(x[2])}</span>'
        + (f'<span class="s-why">{E(x[3])}</span>' if len(x) > 3 else '') + '</li>'
        for x in songs for t, vid in [(x[0], x[1])])
    rows.append(f'''      <details class="setlist{' bang' if bang else ''}"{' open' if bang else ''}{f' id="{img}"' if bang else ''}>
        <summary><span class="setlist-no">{st}</span><span class="setlist-artist">{E(name)}{f' <em>{E(ko)}</em>' if ko else ''}</span><span class="setlist-count">{stage} · ~{en}</span></summary>
        <div class="lineup-body">
          <img class="lineup-img" src="imgs/artists/{img}.webp" alt="{E(name)}" loading="lazy">
          <div>
            {f'<p class="setlist-note">{E(note)}</p>' if note else ''}
            <ol class="setlist-songs unnum">{li}</ol>
          </div>
        </div>
      </details>''')

page = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>토요일 출연진 · WONDERLIVET 2026</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DotGothic16&family=Noto+Sans+KR:wght@400;500;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/style.css">
  <script src="js/include.js"></script>
</head>
<body>
  <main class="container">
    <section>
      <h1 class="section-title"><span class="nowrap">토요일(11/21)</span> <span class="nowrap">출연진·타임테이블</span></h1>
      <p class="subtitle">WONDER STAGE / LIVET STAGE 번갈아 진행. 시간은 공식 사이트 타임테이블 기준.</p>
      <div class="jump"><a class="btn" href="#mygo">MyGO!!!!! 13:35</a><a class="btn" href="#roselia">Roselia 16:10</a></div>
      <img class="poster" src="imgs/timetable_day2.webp" alt="11/21 타임테이블 (공식)">
      <p class="setlist-note">대표곡은 아티스트·레이블 공식 채널(또는 공식 Topic 음원) 영상만 링크했습니다. 오른쪽 회색 글씨가 업로드 채널명입니다.
      실제 공연 세트리스트가 아닙니다.</p>
    </section>
    <section>
{chr(10).join(rows)}
    </section>
    <section>
      <p class="setlist-note">출처: <a href="https://www.wonderli.vet/" target="_blank" rel="noopener">WONDERLIVET 공식 사이트</a> 타임테이블·아티스트 사진 /
      <a href="https://bang-dream.com/events/wonderlivet-2026/" target="_blank" rel="noopener">BanG Dream! 공식 이벤트 페이지</a> 타임테이블 이미지 /
      마이고·로젤 선곡 근거: <a href="https://www.setlist.fm/setlists/mygo-1bfd2508.html" target="_blank" rel="noopener">setlist.fm MyGO!!!!!</a>,
      <a href="https://www.setlist.fm/setlists/roselia-73cca2e1.html" target="_blank" rel="noopener">setlist.fm Roselia</a>,
      <a href="https://bandori.miraheze.org/wiki/Roselia_ASIA_TOUR_%22Neuweltfahrt%22" target="_blank" rel="noopener">BanG Dream! Wiki</a>·<a href="https://www.livefans.jp/events/1853294" target="_blank" rel="noopener">LiveFans</a> (로젤 서울 공연, 곡 목록 일치·일부 순서는 출처마다 다름)</p>
    </section>
  </main>
  <footer class="site-footer">마지막 업데이트: 2026-10-15</footer>
<script src="nav.js"></script>
</body>
</html>
'''
open(os.path.join(HERE, 'lineup.html'), 'w', encoding='utf-8').write(page)
print('lineup.html', len(LINEUP), '팀', sum(len(x[6]) for x in LINEUP), '곡')
