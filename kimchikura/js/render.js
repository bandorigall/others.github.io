/* =========================================================
   render.js
   - data/*.js 가 전역에 채운 데이터(window.DATA_xxx)를 읽어 렌더링
   - 대상 컨테이너는 [data-render] 속성으로 지정한다.
       <div data-render="lineup"></div>   -> window.DATA_lineup    (data/lineup.js)
       <div data-render="cast"></div>     -> window.DATA_cast      (data/cast.js)
       <div data-render="morfonica"></div>-> window.DATA_morfonica (data/morfonica.js)
   - 데이터 스크립트를 render.js 보다 먼저 <head> 에 넣어야 한다.
   - fetch 를 쓰지 않으므로 file:// 로 더블클릭해 열어도 동작한다.
   ========================================================= */
(function () {
  "use strict";

  // ---------- 유틸 ----------
  function el(tag, opts) {
    var node = document.createElement(tag);
    opts = opts || {};
    if (opts.className) node.className = opts.className;
    if (opts.text != null) node.textContent = opts.text;
    if (opts.html != null) node.innerHTML = opts.html;
    if (opts.href != null) node.href = opts.href;
    if (opts.attrs) {
      Object.keys(opts.attrs).forEach(function (k) {
        node.setAttribute(k, opts.attrs[k]);
      });
    }
    return node;
  }

  // 값이 비었거나 TBD 인지 검사
  function isTBD(v) {
    return v == null || v === "" || String(v).trim().toUpperCase() === "TBD";
  }

  function ytLink(url, label) {
    return el("a", {
      className: "yt-link",
      text: label || "YouTube",
      href: url,
      attrs: { target: "_blank", rel: "noopener" }
    });
  }

  function setState(container, cls, msg) {
    container.innerHTML = "";
    container.appendChild(el("div", { className: cls, text: msg }));
  }

  // ---------- 곡 목록 (cast / lineup 공용) ----------
  function songListEl(songs) {
    var ul = el("ul", { className: "song-list" });
    (songs || []).forEach(function (s) {
      var li = el("li");
      li.appendChild(el("span", { text: isTBD(s.title) ? "TBD" : s.title }));
      if (!isTBD(s.youtube)) li.appendChild(ytLink(s.youtube));
      ul.appendChild(li);
    });
    return ul;
  }

  // ---------- 렌더러: 라인업 ----------
  function renderLineup(container, data) {
    var grid = el("div", { className: "card-grid" });
    data.forEach(function (item) {
      if (item.confirmed === false) return; // 미확정은 별도 플레이스홀더로
      var card = el("div", { className: "card" });
      card.appendChild(el("h3", { text: isTBD(item.name) ? "TBD" : item.name }));
      if (item.confirmed) {
        card.appendChild(el("span", { className: "badge info", text: "출연 확정" }));
      }
      if (!isTBD(item.description)) {
        card.appendChild(el("p", { text: item.description }));
      }
      grid.appendChild(card);
    });

    // 미발표 슬롯 플레이스홀더
    var hasPending = data.some(function (i) { return i.confirmed === false; });
    if (hasPending) {
      var ph = el("div", { className: "card placeholder", text: "추가 발표 예정" });
      grid.appendChild(ph);
    }

    container.innerHTML = "";
    container.appendChild(grid);
  }

  // ---------- 렌더러: 출연진 ----------
  function renderCast(container, data) {
    var list = el("div", { className: "member-list" });
    data.forEach(function (item) {
      var card = el("div", { className: "member-card" });

      // 사진 영역 — 확장자를 순서대로 시도, 모두 실패하면 ? 표시
      var photoWrap = el("div", { className: "member-photo-wrap" });
      var img = document.createElement("img");
      img.className = "member-photo";
      img.alt = item.name;
      var EXTS = ["webp", "jpg", "jpeg", "png", "jfif"];
      var baseName = item.img || item.id;
      // img 필드에 이미 확장자가 있으면 그대로, 없으면 확장자 탐색
      var hasExt = /\.[a-zA-Z]{2,5}$/.test(baseName);
      img.src = "imgs/" + baseName + (hasExt ? "" : "." + EXTS[0]);
      (function tryLoad(exts, i) {
        img.onerror = function () {
          if (i < exts.length) {
            img.src = "imgs/" + baseName + "." + exts[i];
            tryLoad(exts, i + 1);
          } else {
            img.style.display = "none";
            photoWrap.classList.add("member-photo-fallback");
            photoWrap.textContent = "?";
          }
        };
      })(EXTS, 1);
      photoWrap.appendChild(img);
      card.appendChild(photoWrap);

      // 정보 영역
      var info = el("div", { className: "member-info" });

      var nameEl = el("h3", { className: "member-name", text: isTBD(item.name) ? "TBD" : item.name });
      info.appendChild(nameEl);
      if (item.nameJa) {
        info.appendChild(el("span", { className: "member-name-ja", text: item.nameJa }));
      }
      if (!isTBD(item.description)) {
        info.appendChild(el("p", { className: "member-desc", text: item.description }));
      }

      var songs = (item.songs || []).filter(function (s) { return !isTBD(s.title); });
      if (songs.length) {
        info.appendChild(el("div", { className: "songs-label", text: "대표곡" }));
        info.appendChild(songListEl(songs));
      }

      card.appendChild(info);
      list.appendChild(card);
    });
    container.innerHTML = "";
    container.appendChild(list);
  }

  // ---------- 가사 모달 ----------
  var _currentLyricsTitle = null;

  function ensureLyricsModal() {
    if (document.getElementById("lyrics-modal")) return;

    var overlay = document.createElement("div");
    overlay.id = "lyrics-modal";
    overlay.className = "lyrics-overlay";
    overlay.innerHTML =
      '<div class="lyrics-box">' +
        '<div class="lyrics-header">' +
          '<div>' +
            '<div id="lyrics-title" class="lyrics-title"></div>' +
            '<div id="lyrics-title-ko" class="lyrics-title-ko"></div>' +
          '</div>' +
          '<button class="lyrics-close" aria-label="닫기">✕</button>' +
        '</div>' +
        '<div id="lyrics-body" class="lyrics-body"></div>' +
      '</div>';

    document.body.appendChild(overlay);

    function close() { overlay.classList.remove("open"); }
    overlay.querySelector(".lyrics-close").addEventListener("click", close);
    overlay.addEventListener("click", function (e) { if (e.target === overlay) close(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
  }

  function openLyrics(song) {
    ensureLyricsModal();
    var overlay = document.getElementById("lyrics-modal");
    document.getElementById("lyrics-title").textContent = song.title;
    document.getElementById("lyrics-title-ko").textContent = song.titleKo || "";

    var body = document.getElementById("lyrics-body");
    body.innerHTML = "";

    if (!song.lyrics) {
      body.appendChild(el("p", { className: "lyrics-none", text: "가사 데이터가 없습니다." }));
    } else {
      // 3행 묶음(원문/발음/번역)을 한 블록으로 렌더링
      var blocks = song.lyrics.split(/\n{2,}/);
      blocks.forEach(function (block) {
        var lines = block.split("\n").filter(Boolean);
        var div = el("div", { className: "lyrics-block" });
        lines.forEach(function (line, i) {
          var cls = i % 3 === 0 ? "ly-ja" : i % 3 === 1 ? "ly-rom" : "ly-ko";
          div.appendChild(el("p", { className: cls, text: line }));
        });
        body.appendChild(div);
      });
    }

    var shouldReset = _currentLyricsTitle !== song.title;
    _currentLyricsTitle = song.title;
    overlay.classList.add("open");
    if (shouldReset) body.scrollTop = 0;
  }

  // ---------- 렌더러: 모르포니카 곡 ----------
  function renderMorfonica(container, data) {
    ensureLyricsModal();
    var wrap = el("div", { className: "table-wrap" });
    var table = el("table", { className: "morf-table" });
    var thead = el("thead");
    thead.innerHTML = "<tr><th>곡명</th><th>발매일</th><th>링크</th></tr>";
    table.appendChild(thead);

    var tbody = el("tbody");
    data.forEach(function (s) {
      var tr = el("tr");

      // 곡명 셀: 앨범커버 + 제목 (클릭 → 가사 팝업)
      var tdTitle = el("td");
      var wrap2 = el("div", { className: "morf-song-wrap" + (s.lyrics ? " morf-clickable" : "") });
      if (s.lyrics) {
        wrap2.title = "클릭하면 가사를 볼 수 있습니다";
        wrap2.addEventListener("click", (function (song) {
          return function () { openLyrics(song); };
        })(s));
      }
      var img = document.createElement("img");
      img.className = "morf-thumb";
      img.src = s.cover || "";
      img.alt = "";
      img.loading = "lazy";
      wrap2.appendChild(img);
      var textBlock = el("div", { className: "morf-text" });
      textBlock.appendChild(el("span", { className: "morf-title-ja", text: s.title }));
      if (s.titleKo) {
        textBlock.appendChild(el("span", { className: "morf-title-ko", text: s.titleKo }));
      }
      if (s.lyrics) {
        textBlock.appendChild(el("span", { className: "morf-lyrics-hint", text: "가사 보기" }));
      }
      wrap2.appendChild(textBlock);
      tdTitle.appendChild(wrap2);
      tr.appendChild(tdTitle);

      // 발매일 + 뱃지 셀
      var tdMeta = el("td");
      var typeCls = s.type === "타이업" ? "badge-tieup" : "badge-original";
      tdMeta.innerHTML =
        '<span class="morf-badge ' + typeCls + '">' + (s.type || "오리지널") + "</span>" +
        '<span class="morf-date">' + (s.date || "") + "</span>";
      tr.appendChild(tdMeta);

      // 링크 셀
      var tdLink = el("td");
      var linkWrap = el("div", { className: "morf-links" });
      if (!isTBD(s.youtube)) {
        linkWrap.appendChild(el("a", { className: "btn btn-yt", text: "▶ Listen", href: s.youtube, attrs: { target: "_blank", rel: "noopener" } }));
      }
      if (s.namu) {
        linkWrap.appendChild(el("a", { className: "btn btn-namu", text: "출처", href: s.namu, attrs: { target: "_blank", rel: "noopener" } }));
      }
      tdLink.appendChild(linkWrap);
      tr.appendChild(tdLink);

      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.innerHTML = "";
    container.appendChild(wrap);
  }

  var RENDERERS = {
    lineup: renderLineup,
    cast: renderCast,
    morfonica: renderMorfonica
  };

  // ---------- 부트스트랩 ----------
  function run() {
    var containers = document.querySelectorAll("[data-render]");
    containers.forEach(function (container) {
      var key = container.getAttribute("data-render");
      var renderer = RENDERERS[key];
      if (!renderer) return;

      var data = window["DATA_" + key];
      if (!data) {
        setState(container, "error",
          "데이터를 찾을 수 없습니다. (data/" + key + ".js 가 먼저 로드됐는지 확인하세요)");
        return;
      }

      try {
        renderer(container, data);
      } catch (err) {
        console.error(err);
        setState(container, "error", "렌더링 중 오류가 발생했습니다.");
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
