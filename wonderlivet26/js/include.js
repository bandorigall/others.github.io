/* =========================================================
   include.js
   - 공통 헤더를 <body> 최상단에 삽입 (fetch 없이 JS 문자열로 직접 삽입
     -> file:// 로 더블클릭해 열어도 동작한다)
   - 현재 페이지에 해당하는 탭에 active 클래스 부여
   - 모바일 햄버거 토글 연결

   사용법: 각 HTML <head> 에 아래 한 줄 추가
     <script src="js/include.js"></script>

   메뉴를 바꾸려면 아래 HEADER_HTML 의 링크만 수정하면 된다.
   ========================================================= */
(function () {
  "use strict";

  var HEADER_HTML =
    '<header class="site-header">' +
      '<nav class="nav" aria-label="주 메뉴">' +
        '<a class="nav-brand" href="index.html">WONDERLIVET 2026</a>' +
        '<button class="nav-toggle" aria-label="메뉴 열기" aria-expanded="false">☰</button>' +
        '<ul class="nav-links">' +
          '<li><a href="index.html">홈</a></li>' +
          '<li><a href="lineup.html">출연진·시간표</a></li>' +
          '<li><a href="ticket.html">입장·예매</a></li>' +
          '<li><a href="access.html">오시는 길</a></li>' +
          '<li><a href="songs.html">곡 목록</a></li>' +
          '<li><a href="callguide.html">콜 가이드</a></li>' +
        '</ul>' +
      '</nav>' +
    '</header>';

  // 현재 페이지 파일명 (예: "lineup.html"). 루트로 끝나면 index.html 로 간주.
  function currentPage() {
    var path = location.pathname;
    var last = path.substring(path.lastIndexOf("/") + 1);
    return last === "" ? "index.html" : last;
  }

  // 헤더 링크 중 현재 페이지와 일치하는 항목에 active 부여
  function markActive(headerEl) {
    var here = currentPage();
    var links = headerEl.querySelectorAll(".nav-links a");
    links.forEach(function (a) {
      var href = a.getAttribute("href");
      if (!href) return;
      var file = href.substring(href.lastIndexOf("/") + 1);
      if (file === here) a.classList.add("active");
    });
  }

  // 모바일 햄버거 토글
  function wireToggle(headerEl) {
    var btn = headerEl.querySelector(".nav-toggle");
    var menu = headerEl.querySelector(".nav-links");
    if (!btn || !menu) return;
    btn.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    menu.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        menu.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  var FLOAT_HTML =
    '<div class="float-btns">' +
      '<a class="float-btn" href="https://gall.dcinside.com/mgallery/board/view/?id=bang_dream&no=6220267"' +
         ' target="_blank" rel="noopener" title="팬 커뮤니티 종합 직관 가이드">' +
        '<span class="float-btn-icon">📋</span>' +
        '<span class="float-btn-label">직관 가이드</span>' +
      '</a>' +
      '<a class="float-btn" href="https://gall.dcinside.com/mgallery/board/view/?id=bang_dream&no=6223804"' +
         ' target="_blank" rel="noopener" title="공연 위생 에티켓 가이드">' +
        '<span class="float-btn-icon">🚿</span>' +
        '<span class="float-btn-label">씻는법</span>' +
      '</a>' +
    '</div>';

  function injectHeader() {
    var wrap = document.createElement("div");
    wrap.innerHTML = HEADER_HTML;
    var headerEl = wrap.firstElementChild;
    document.body.insertBefore(headerEl, document.body.firstChild);
    markActive(headerEl);
    wireToggle(headerEl);

    var floatWrap = document.createElement("div");
    floatWrap.innerHTML = FLOAT_HTML;
    document.body.appendChild(floatWrap.firstElementChild);

    var disclaimer = document.createElement("p");
    disclaimer.className = "site-disclaimer";
    disclaimer.innerHTML =
      "이 사이트는 디시인사이드 BanG Dream! 마이너 갤러리 유저가 만든 비공식 팬 안내 페이지이며, " +
      "WONDERLIVET 주최사(LIVET·원더로크), 부시로드, 예매처, 셔틀 운영사와 관계가 없습니다.<br>" +
      "일정·티켓·입장·교통 정보는 바뀔 수 있으니 관람 전 반드시 공식 안내와 예매처 공지를 확인하세요. " +
      "대표곡·세트리스트는 예습용 예상이며 실제 공연과 다를 수 있습니다.<br>" +
      "이미지·음원·영상의 저작권은 각 권리자에게 있으며, 콜표 등 팬 제작 자료의 권리는 원 작성자에게 있습니다.";

    var existingFooter = document.querySelector(".site-footer");
    var credit = document.createElement("div");
    credit.className = "site-credit";
    credit.textContent = "Made by Bangbung Kim";
    if (existingFooter) {
      existingFooter.appendChild(disclaimer);
      existingFooter.appendChild(credit);
    } else {
      var footer = document.createElement("footer");
      footer.className = "site-footer";
      footer.appendChild(disclaimer);
      footer.appendChild(credit);
      document.body.appendChild(footer);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectHeader);
  } else {
    injectHeader();
  }
})();
