# KIMCHIKURA

Morfonica · 센고쿠 유노(무한대 뮤타입) 외 출연 공연 안내용 정적 웹사이트입니다.
GitHub Pages 정적 호스팅 환경(`others.github.io/kimchikura/`)에서 동작합니다.

- 일시: 2026년 8월 8일 (토) 15:00 ~ 20:30
- 장소: 경희대학교 서울캠퍼스 평화의전당

> 모든 일정/정보는 변동될 수 있습니다.

---

## 로컬 실행 방법

⚠️ **`file://` 로 HTML 을 직접 열면 안 됩니다.**
헤더 삽입(`include.js`)과 데이터 렌더링(`render.js`)이 `fetch` 를 사용하기 때문에
`file://` 프로토콜에서는 CORS 오류로 동작하지 않습니다. 반드시 HTTP 서버로 열어주세요.

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
├── index.html          # 홈 (행사 개요 + 바로가기 카드)
├── lineup.html         # 라인업 (data/lineup.json 렌더링)
├── cast.html           # 출연진 & 대표곡 (data/cast.json 렌더링)
├── morfonica.html      # 모르포니카 곡 (data/morfonica.json 렌더링) + 콜 가이드
├── ticket.html         # 예매 안내
├── access.html         # 오시는 길 & 주변 (구글 지도 임베드)
├── components/
│   └── header.html     # 공통 헤더(네비게이션) 마크업
├── js/
│   ├── include.js      # header.html 삽입 + 현재 탭 active 처리 + 모바일 햄버거
│   └── render.js       # data/*.json 을 읽어 페이지 콘텐츠 렌더링
├── css/
│   └── style.css       # 순수 CSS (라이트/다크 모드, 모바일 반응형)
├── data/
│   ├── lineup.json
│   ├── cast.json
│   └── morfonica.json
└── README.md
```

### 동작 원리
- 각 HTML 은 `<script src="js/include.js"></script>` 한 줄로 공통 헤더를 자동 삽입합니다.
- 콘텐츠가 동적인 페이지는 `<div data-render="lineup"></div>` 처럼 컨테이너만 두면
  `render.js` 가 같은 이름의 `data/<key>.json` 을 읽어 채웁니다.
- **경로는 모두 상대경로**입니다. 이 앱이 루트가 아닌 하위 폴더(`/kimchikura/`)에
  배포되므로 `/js/...` 같은 절대경로를 쓰면 안 됩니다.

---

## 콘텐츠 업데이트 방법

대부분의 내용은 **JSON 파일만 수정**하면 페이지에 자동 반영됩니다. HTML 을 건드릴 필요가 없습니다.

### 라인업 추가/수정 — `data/lineup.json`
```json
{
  "id": "고유id",
  "name": "표시 이름",
  "confirmed": true,        // true: 확정 카드 / false: "추가 발표 예정" 플레이스홀더
  "description": "소개 (없으면 \"TBD\" 또는 \"\")"
}
```

### 출연진 & 대표곡 — `data/cast.json`
```json
{
  "id": "고유id",
  "name": "이름",
  "description": "소개",
  "songs": [
    { "title": "곡명", "youtube": "https://youtu.be/..." }
  ]
}
```

### 모르포니카 곡 — `data/morfonica.json`
```json
{ "title": "곡명", "album": "수록 앨범", "youtube": "https://youtu.be/..." }
```

> 값을 비워두거나 `"TBD"` 로 두면 화면에 "TBD" 로 표시됩니다.
> 곡 목록의 실제 유튜브 링크/앨범명은 확인 후 채워 넣으세요(초기값은 TBD).

### 그 외 직접 수정이 필요한 곳
- 예매 가이드 / 취켓팅 / 콜 가이드 / 주변 맛집 외부 링크 URL
  → 해당 HTML 의 `<!-- TODO ... -->` 주석이 달린 `href="#"` 를 교체
- 마지막 업데이트 날짜 → 각 HTML 하단 `footer` 텍스트
- 메뉴 항목 추가/변경 → `components/header.html`

---

## 제약 / 메모
- 서버 사이드 코드 없음(정적 호스팅). 외부 의존성은 Google Fonts(Noto Sans KR)와 구글 지도 iframe 뿐입니다.
- 라이트/다크 모드는 OS 설정(`prefers-color-scheme`)을 따릅니다.
