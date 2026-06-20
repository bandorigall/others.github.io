# KIMCHIKURA

Morfonica · 센고쿠 유노(무한대 뮤타입) 외 출연 공연 안내용 정적 웹사이트입니다.
GitHub Pages 정적 호스팅 환경(`others.github.io/kimchikura/`)에서 동작합니다.

- 일시: 2026년 8월 8일 (토) 15:00 ~ 20:30
- 장소: 경희대학교 서울캠퍼스 평화의전당

> 모든 일정/정보는 변동될 수 있습니다.

---

## 로컬 실행 방법

헤더 삽입(`include.js`)과 데이터(`data/*.js`)는 `fetch` 를 쓰지 않고 JS 전역 변수로
직접 주입하므로 **`file://` 로 HTML 을 더블클릭해 열어도 동작**합니다.
그래도 배포 환경과 동일하게 확인하려면 HTTP 서버로 여는 것을 권장합니다.

### 방법 1) Python 내장 서버
```bash
# kimchikura 폴더에서
python -m http.server 8000
# 브라우저에서 http://localhost:8000/ 접속
```

### 방법 2) VS Code Live Server
- VS Code 확장 "Live Server" 설치 후 `index.html` 에서 우클릭 → "Open with Live Server"

---

## 파일 구조

```
kimchikura/
├── index.html          # 홈 (행사 개요 + About + 포스터)
├── cast.html           # 출연진 & 대표곡 (data/cast.js 렌더링)
├── morfonica.html      # 모르포니카 곡 (data/morfonica.js 렌더링, 가사 팝업) + 콜 가이드
├── fan.html            # 제단/나눔존
├── ticket.html         # 예매 안내
├── access.html         # 오시는 길 & 주변 (구글 지도 임베드)
├── lineup.html         # cast.html 로 리다이렉트 (구 URL 호환용)
├── js/
│   ├── include.js      # 공통 헤더/플로팅 버튼/푸터 주입 + active 처리 + 모바일 햄버거
│   └── render.js       # data/*.js 의 전역 데이터를 읽어 페이지 콘텐츠 렌더링
├── css/
│   └── style.css       # 순수 CSS (라이트/다크 모드, 모바일 반응형)
├── data/
│   ├── cast.js         # window.DATA_cast
│   └── morfonica.js    # window.DATA_morfonica
├── _build_lyrics.py    # morfonica_lyrics_cache.txt → morfonica.js 가사 필드 생성
└── README.md
```

### 동작 원리
- 각 HTML 은 `<script src="js/include.js"></script>` 한 줄로 공통 헤더를 자동 삽입합니다.
- 콘텐츠가 동적인 페이지는 `<div data-render="cast"></div>` 처럼 컨테이너만 두고,
  해당 `data/<key>.js`(전역 변수 `window.DATA_<key>`)를 `render.js` 보다 먼저 로드하면
  `render.js` 가 그 데이터를 읽어 채웁니다. `fetch` 를 쓰지 않습니다.
- **경로는 모두 상대경로**입니다. 이 앱이 루트가 아닌 하위 폴더(`/kimchikura/`)에
  배포되므로 `/js/...` 같은 절대경로를 쓰면 안 됩니다.

---

## 콘텐츠 업데이트 방법

대부분의 내용은 **`data/*.js` 의 배열만 수정**하면 페이지에 자동 반영됩니다. HTML 을 건드릴 필요가 없습니다.
(각 파일은 `window.DATA_<key> = [ ... ];` 형태의 JS 배열입니다.)

### 출연진 & 대표곡 — `data/cast.js` (`window.DATA_cast`)
```js
{
  "id": "고유id",
  "name": "이름",
  "nameJa": "일본어 표기(선택)",
  "img": "imgs/ 안의 파일 기본명(확장자 생략 가능 — webp/jpg/png/jfif 순 자동 탐색)",
  "description": "소개",
  "songs": [
    { "title": "곡명", "youtube": "https://youtu.be/...", "note": "비고(선택)" }
  ],
  "link": { "url": "외부 링크(선택)", "label": "표시 텍스트" }
}
```

### 모르포니카 곡 — `data/morfonica.js` (`window.DATA_morfonica`)
```js
{
  "title": "원어 제목", "titleKo": "한국어 번역",
  "date": "발매일", "cover": "앨범 커버 URL",
  "type": "오리지널 | 타이업 | 커버",
  "youtube": "YouTube 링크", "namu": "출처 링크",
  "lyrics": "원문\n발음\n번역 3행 반복 (가사 팝업용)"
}
```

> `lyrics` 는 `_build_lyrics.py` 로 `발매곡목록/morfonica_lyrics_cache.txt` 에서 자동 생성합니다.
> 빌드 스크립트가 `<<<END>>>` 구분자를 제거하며, 렌더러가 `&amp;` 등 HTML 엔티티를 디코드합니다.
> 값을 비워두거나 `"TBD"` 로 두면 화면에 "TBD" 로 표시됩니다.

### 그 외 직접 수정이 필요한 곳
- 예매 가이드 / 취켓팅 / 콜 가이드 / 주변 맛집 외부 링크 URL
  → 해당 HTML 의 `<!-- TODO ... -->` 주석이 달린 `href="#"` 를 교체
- 마지막 업데이트 날짜 → 각 HTML 하단 `footer` 텍스트
- 메뉴 항목 / 플로팅 버튼 추가·변경 → `js/include.js` 의 `HEADER_HTML` · `FLOAT_HTML`

---

## 제약 / 메모
- 서버 사이드 코드 없음(정적 호스팅). 외부 의존성은 Google Fonts(Noto Sans KR)와 구글 지도 iframe 뿐입니다.
- 라이트/다크 모드는 OS 설정(`prefers-color-scheme`)을 따릅니다.
