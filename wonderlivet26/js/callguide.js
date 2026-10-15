/* 콜 가이드: 로젤 예상곡 칩 → 콜표 팝업 (data/roselia_calls.js, build_calls.py 가 정제한 HTML만 사용) */
(function () {
  "use strict";
  var data = window.DATA_roselia_calls || [];
  var box = document.getElementById("roselia-chips");
  if (!box || box.children.length) return;

  var overlay = document.createElement("div");
  overlay.className = "lyrics-overlay call-overlay";
  overlay.innerHTML =
    '<div class="lyrics-box" role="dialog" aria-modal="true" aria-labelledby="call-title">' +
      '<div class="lyrics-header"><div><div id="call-title" class="lyrics-title"></div>' +
      '<div id="call-sub" class="lyrics-title-ko"></div></div>' +
      '<button class="lyrics-close" aria-label="닫기">✕</button></div>' +
      '<div id="call-actions" class="call-actions"></div>' +
      '<div id="call-body" class="lyrics-body call-body"></div></div>';
  document.body.appendChild(overlay);
  function close() { overlay.classList.remove("open"); }
  overlay.querySelector(".lyrics-close").addEventListener("click", close);
  overlay.addEventListener("click", function (e) { if (e.target === overlay) close(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });

  function open(s) {
    document.getElementById("call-title").textContent = s.title;
    document.getElementById("call-sub").textContent = s.titleKo || "";
    var act = document.getElementById("call-actions");
    act.innerHTML = "";
    if (s.video) {
      var a = document.createElement("a");
      a.className = "btn ghost"; a.href = s.video; a.target = "_blank"; a.rel = "noopener";
      a.textContent = "▶ 콜 가이드 영상 (팬 제작 · Roselive)";
      act.appendChild(a);
    }
    var body = document.getElementById("call-body");
    body.innerHTML = s.html;   // build_calls.py 화이트리스트 정제본
    body.scrollTop = 0;
    overlay.classList.add("open");
  }

  data.forEach(function (s) {
    var li = document.createElement("li");
    if (s.html) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "chip-btn"; b.textContent = s.title;
      if (s.video) b.textContent += " ▶";
      b.addEventListener("click", function () { open(s); });
      li.appendChild(b);
    } else {
      li.className = "chip-off"; li.textContent = s.title + " · 콜표 없음 (신곡)";
    }
    box.appendChild(li);
  });
})();
