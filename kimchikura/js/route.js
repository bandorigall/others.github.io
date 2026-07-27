/* =========================================================
   route.js — "당일 성지순례 경로 최적화"

   공연 당일에 활성화된 국내 오프라인 이벤트 장소를 체크박스로 고르면
   출발지 → (선택 장소들) → 경희대 평화의전당 순서를 최적화한다.

   소요 시간은 추정이 아니라 **네이버 지도 대중교통 경로 API 실측값**이다.
   해당 API 는 CORS 를 허용하지 않아 브라우저에서 직접 못 부르므로,
   tools/build_routes.py 가 모든 방향 쌍을 미리 조회해 data/routes.json 에
   구워두고 이 스크립트는 그 행렬만 읽는다.
   (이벤트가 바뀌면 python tools/build_routes.py 재실행)
   ========================================================= */
(function () {
  "use strict";

  var DATA_URL = "data/routes.json";
  var DOOR_OPEN = 12 * 60 + 30;      // 작년 기준 추정 개장 12:30

  var D = null;                       // routes.json
  var NODE = {};                      // id -> node

  function leg(aId, bId) {
    return D.matrix[aId + ">" + bId] || null;
  }

  /* ---------- 순서 최적화 (종점 고정 open-path TSP) ---------- */
  function pathCost(originId, order, dwell) {
    var cost = 0, cur = originId, i, l;
    for (i = 0; i < order.length; i++) {
      l = leg(cur, order[i]);
      if (!l) return Infinity;
      cost += l.duration + dwell;
      cur = order[i];
    }
    l = leg(cur, D.goal.id);
    return l ? cost + l.duration : Infinity;
  }

  function permute(arr) {
    if (arr.length <= 1) return [arr];
    var out = [];
    arr.forEach(function (v, i) {
      permute(arr.slice(0, i).concat(arr.slice(i + 1))).forEach(function (p) {
        out.push([v].concat(p));
      });
    });
    return out;
  }

  function optimize(originId, ids, dwell) {
    if (ids.length <= 1) return ids.slice();
    if (ids.length <= 7) {            // 7! = 5040 — 완전탐색으로 최적해 보장
      var best = ids.slice(), bestC = Infinity;
      permute(ids).forEach(function (p) {
        var c = pathCost(originId, p, dwell);
        if (c < bestC) { bestC = c; best = p; }
      });
      return best;
    }
    // 그 이상은 최근접 이웃 + 2-opt
    var remain = ids.slice(), order = [], cur = originId;
    while (remain.length) {
      var bi = 0, bd = Infinity;
      remain.forEach(function (id, i) {
        var l = leg(cur, id), d = l ? l.duration : Infinity;
        if (d < bd) { bd = d; bi = i; }
      });
      cur = remain[bi]; order.push(cur); remain.splice(bi, 1);
    }
    var improved = true;
    while (improved) {
      improved = false;
      for (var i = 0; i < order.length - 1; i++) {
        for (var j = i + 1; j < order.length; j++) {
          var cand = order.slice(0, i)
            .concat(order.slice(i, j + 1).reverse(), order.slice(j + 1));
          if (pathCost(originId, cand, dwell) < pathCost(originId, order, dwell)) {
            order = cand; improved = true;
          }
        }
      }
    }
    return order;
  }

  /* ---------- 유틸 ---------- */
  function naverDir(a, b) {
    return "https://map.naver.com/p/directions/" +
      a.lng + "," + a.lat + "," + encodeURIComponent(a.name) + ",,/" +
      b.lng + "," + b.lat + "," + encodeURIComponent(b.name) + ",,/-/transit";
  }
  function kakaoDir(a, b) {
    return "https://map.kakao.com/?sName=" + encodeURIComponent(a.name) +
           "&eName=" + encodeURIComponent(b.name);
  }
  function fmtClock(m) {
    m = ((Math.round(m) % 1440) + 1440) % 1440;
    var h = Math.floor(m / 60), mm = m % 60;
    return (h < 10 ? "0" : "") + h + ":" + (mm < 10 ? "0" : "") + mm;
  }
  function fmtDur(m) {
    return m >= 60 ? Math.floor(m / 60) + "시간 " + (m % 60) + "분" : m + "분";
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ---------- 렌더 ---------- */
  function renderStopList(el) {
    if (!D.stops.length) {
      el.innerHTML = '<p class="route-empty">공연 당일 활성화된 다른 이벤트 장소가 없습니다.</p>';
      return;
    }
    el.innerHTML = D.stops.map(function (s) {
      return '<label class="route-stop">' +
        '<input type="checkbox" value="' + esc(s.id) + '">' +
        '<span class="route-stop-body">' +
          '<span class="route-stop-title">' + esc(s.title) + '</span>' +
          '<span class="route-stop-place">' + esc(s.place) + '</span>' +
        '</span>' +
      '</label>';
    }).join("");
  }

  function legHtml(a, b, l) {
    var meta = l.summary ? esc(l.summary) : esc(l.type || "대중교통");
    if (l.walk) meta += " · 도보 " + l.walk + "분";
    if (l.fare) meta += " · " + l.fare.toLocaleString() + "원";
    return '<li class="route-step move">' +
      '<span class="route-time">' + fmtDur(l.duration) + '</span>' +
      '<span class="route-node">' +
        '<span class="route-line">' + meta + '</span>' +
        '<span class="route-sub">' +
          '<a href="' + naverDir(a, b) + '" target="_blank" rel="noopener">네이버 길찾기</a>' +
          ' · <a href="' + kakaoDir(a, b) + '" target="_blank" rel="noopener">카카오맵</a>' +
        '</span>' +
      '</span></li>';
  }

  function run(root) {
    var originId = root.querySelector(".route-origin").value;
    var origin = NODE[originId];
    var dwell = parseInt(root.querySelector(".route-dwell").value, 10);
    if (!isFinite(dwell) || dwell < 0) dwell = 0;
    var sp = (root.querySelector(".route-start").value || "09:00").split(":");
    var t = (parseInt(sp[0], 10) || 0) * 60 + (parseInt(sp[1], 10) || 0);
    var startMin = t;

    var picked = [];
    Array.prototype.forEach.call(
      root.querySelectorAll(".route-stop input:checked"),
      function (cb) { picked.push(cb.value); });

    var order = optimize(originId, picked, dwell);
    var out = root.querySelector(".route-result");

    if (pathCost(originId, order, dwell) === Infinity) {
      out.innerHTML = '<p class="route-verdict bad">이 조합의 대중교통 경로 데이터가 없습니다. ' +
                      'tools/build_routes.py 를 다시 실행해 주세요.</p>';
      return;
    }

    var cur = origin, totalFare = 0;
    var html = '<ol class="route-steps">';
    html += '<li class="route-step start"><span class="route-time">' + fmtClock(t) + '</span>' +
            '<span class="route-node"><strong>' + esc(origin.name) + '</strong> 출발</span></li>';

    order.forEach(function (id) {
      var s = NODE[id], l = leg(cur.id, id);
      html += legHtml(cur, s, l);
      t += l.duration;
      totalFare += l.fare || 0;
      html += '<li class="route-step stop"><span class="route-time">' + fmtClock(t) + '</span>' +
              '<span class="route-node"><strong>' + esc(s.place) + '</strong>' +
              '<span class="route-sub">' + esc(s.title) + ' · 체류 ' + dwell + '분</span>' +
              '</span></li>';
      t += dwell;
      cur = s;
    });

    var lastLeg = leg(cur.id, D.goal.id);
    html += legHtml(cur, D.goal, lastLeg);
    t += lastLeg.duration;
    totalFare += lastLeg.fare || 0;
    html += '<li class="route-step goal"><span class="route-time">' + fmtClock(t) + '</span>' +
            '<span class="route-node"><strong>경희대학교 평화의전당 도착</strong></span></li>';
    html += "</ol>";

    var total = t - startMin, stay = dwell * order.length;
    html += '<p class="route-total">총 <strong>' + fmtDur(total) + '</strong>' +
            ' (이동 ' + fmtDur(total - stay) + ' + 체류 ' + fmtDur(stay) + ')' +
            (totalFare ? ' · 교통비 약 ' + totalFare.toLocaleString() + '원' : '') + '</p>';

    if (t <= DOOR_OPEN) {
      html += '<p class="route-verdict ok">추정 개장 시각(12:30)보다 ' +
              fmtDur(DOOR_OPEN - t) + ' 여유 있게 도착합니다.</p>';
    } else {
      html += '<p class="route-verdict bad">추정 개장 시각(12:30)을 ' +
              fmtDur(t - DOOR_OPEN) + ' 넘깁니다. 출발을 앞당기거나 체류 시간을 줄여보세요.</p>';
    }
    out.innerHTML = html;
  }

  function init(data, root) {
    D = data;
    D.origins.concat(D.stops).concat([D.goal]).forEach(function (n) { NODE[n.id] = n; });

    var sel = root.querySelector(".route-origin");
    sel.innerHTML = D.origins.map(function (o) {
      return '<option value="' + esc(o.id) + '">' + esc(o.name) + "</option>";
    }).join("");

    renderStopList(root.querySelector(".route-stops"));

    root.addEventListener("change", function () { run(root); });
    root.addEventListener("input", function (e) {
      if (e.target.classList.contains("route-start") ||
          e.target.classList.contains("route-dwell")) run(root);
    });

    var stamp = root.querySelector(".route-stamp");
    if (stamp) {
      stamp.textContent = "경로 데이터: " + D.source +
        " · " + D.date + " " + D.departureTime + " 출발 기준 · 갱신 " + D.generatedAt;
    }
    run(root);
  }

  function boot() {
    var root = document.getElementById("route-planner");
    if (!root) return;
    var out = root.querySelector(".route-result");

    fetch(DATA_URL, { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (d) { init(d, root); })
      .catch(function () {
        out.innerHTML = '<p class="route-verdict bad">경로 데이터(data/routes.json)를 불러오지 못했습니다. ' +
          'file:// 로 직접 열면 브라우저 보안 정책에 막히니 ' +
          '<code>python -m http.server</code> 로 확인하세요.</p>';
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else boot();
})();
