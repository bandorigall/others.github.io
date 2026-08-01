/* 뱅드림 캐릭터 소터
 *
 * [공통 구조] '답변 로그 재생' 방식
 *   비교 결과를 answers 배열에 순서대로 쌓고, 화면을 그릴 때마다 알고리즘을
 *   처음부터 다시 돌린다. 답 없는 쌍을 만나면 NEED 를 던져 그 쌍을 질문으로 띄운다.
 *   덕분에 되돌리기 = 로그 pop 후 재실행, 이어하기 = 로그만 저장으로 끝난다.
 *   60명 재계산은 1ms 미만이라 매 질문마다 다시 돌려도 무방하다.
 *
 * [모드]
 *   full  : 상향식 병합정렬로 60명 전체를 정확히 정렬. 약 280문항.
 *           참고로 60명 전체 순위를 확정하려면 정보이론상 log2(60!)≈273회가
 *           최소이므로, 이보다 크게 줄이는 건 원리적으로 불가능하다.
 *   top10 / top20 : 토너먼트 브래킷을 우승자를 빼면서 반복한다.
 *           이미 답한 비교는 캐시되어 있어, 2위부터는 직전 우승자가 지나간
 *           경로만 새로 물어보게 된다. 상위 K명은 '정확히' 맞으며
 *           TOP10 약 150문항 / TOP20 약 215문항으로 끝난다.
 *           (Elo·스위스 방식도 검토했지만 같은 질문 수에서 정확도가 크게 떨어져 채택하지 않음)
 *
 * [비김] 답변값 0. 두 캐릭터를 eqLink 로 묶어 이후 병합에서 질문 없이 딸려보낸다.
 *   순위 계산에서 인접한 두 캐릭터의 답이 0이면 같은 순위로 묶는다.
 *
 * [시작 명단] 섞지 않는다. 밴드 순서 그대로 시작한다(원본 소터와 동일).
 *   병합정렬은 초기 순서가 취향과 비슷할수록 질문이 줄어들고, 밴드 단위로
 *   취향이 갈리는 사람이 많아 이 배치가 유리하다. 정확도에는 영향이 없다.
 *   실측(60명): 무작위 취향 282, 밴드끼리 뭉친 취향 244, 밴드 순서까지 맞으면 207.
 *   ※ 셔플을 되살리지 말 것. 셔플하면 무조건 282 로 고정된다.
 */
(function () {
  'use strict';

  var DATA = window.SORTER_DATA;
  var CHARS = DATA.characters;
  var BY_ID = {};
  CHARS.forEach(function (c) { BY_ID[c.id] = c; });

  var SAVE_KEY = 'bangdream_sorter_v2';
  var NEED = {};                 // 비교가 필요할 때 던지는 신호 객체

  var MODES = {
    full:  { label: '전체 순위', k: 0 },
    top20: { label: 'TOP 20',   k: 20 },
    top10: { label: 'TOP 10',   k: 10 }
  };

  /** 진행률 분모(= 예상 최대 질문 수). 인원수 n 에 따라 계산한다.
   *  full  : 병합정렬 최악 비교 횟수 n*ceil(log2 n) - 2^ceil(log2 n) + 1
   *  topK  : 브래킷 n-1 회 + 2위부터 우승자 경로 재질문(실측 계수 2.2)
   *  비김을 쓰면 실제론 이보다 훨씬 적게 끝난다(진행률은 99%에서 멈춰 둔다). */
  function estFor(mode, n) {
    if (n < 2) return 1;
    var lg = Math.ceil(Math.log2(n));
    var k = MODES[mode].k;
    if (!k) return n * lg - Math.pow(2, lg) + 1;
    return Math.round((n - 1) + Math.min(k, n) * lg * 2.2);
  }

  var state = {
    mode: 'full',
    order: [],                   // 시작 명단(밴드 순서, 섞지 않음)
    answers: [],                 // [[idA, idB, v], ...]  v: 1=A선호, -1=B선호, 0=비김
    map: {},                     // "idA|idB" -> v
    eqLink: {},                  // 비김으로 묶인 쌍 (idA -> idB)
    pending: null,               // 지금 화면에 띄운 [idA, idB]
    result: null                 // 완료 시 정렬된 id 배열
  };

  // ── 밴드 선택 ────────────────────────────────────────────────────────
  var BAND_ORDER = [];
  CHARS.forEach(function (c) {
    if (BAND_ORDER.indexOf(c.bandKey) < 0) BAND_ORDER.push(c.bandKey);
  });
  var picked = {};
  BAND_ORDER.forEach(function (b) { picked[b] = true; });

  function pickedChars() {
    return CHARS.filter(function (c) { return picked[c.bandKey]; });
  }

  function renderBands() {
    var box = $('band-pick');
    box.innerHTML = '';
    BAND_ORDER.forEach(function (b) {
      var info = DATA.bands[b] || { name: b, color: '#888' };
      var n = CHARS.filter(function (c) { return c.bandKey === b; }).length;
      var el = document.createElement('button');
      el.type = 'button';
      el.className = 'band' + (picked[b] ? ' on' : '');
      el.style.setProperty('--band', info.color);
      el.innerHTML = '<span class="b-dot"></span>' + esc(info.name) +
        '<span class="b-n">' + n + '</span>';
      el.addEventListener('click', function () {
        picked[b] = !picked[b];
        el.classList.toggle('on', picked[b]);
        updatePicked();
      });
      box.appendChild(el);
    });
    updatePicked();
  }

  function updatePicked() {
    var n = pickedChars().length;
    $('picked-count').textContent = n;
    Array.prototype.forEach.call(
      document.querySelectorAll('[data-mode]'), function (el) {
        var m = el.dataset.mode;
        var few = n < 2 || (MODES[m].k && n <= MODES[m].k);
        el.disabled = few;
        // '전체 60위' 라벨도 선택 인원에 맞춘다
        if (m === 'full') {
          var nm = el.querySelector('.m-name');
          if (nm) nm.innerHTML = '전체 ' + n + '위<em>추천</em>';
        }
        var q = el.querySelector('.m-q');
        if (q) {
          q.textContent = few
            ? (n < 2 ? '2명 이상 골라주세요' : (MODES[m].k + '명보다 많이 골라주세요'))
            : '최대 ' + estFor(m, n) + '문항' + (m === 'full' ? ' (비김 쓰면 더 줄어요)' : '');
        }
      });
  }

  // ── DOM ─────────────────────────────────────────────────────────────
  var $ = function (id) { return document.getElementById(id); };
  var screens = {
    intro: $('screen-intro'),
    battle: $('screen-battle'),
    result: $('screen-result')
  };

  function show(name) {
    Object.keys(screens).forEach(function (k) { screens[k].hidden = (k !== name); });
    window.scrollTo(0, 0);
  }

  // ── 답변 로그 ────────────────────────────────────────────────────────
  function keyOf(a, b) { return a + '|' + b; }

  function rebuildMap() {
    state.map = {};
    state.eqLink = {};
    state.answers.forEach(function (r) {
      state.map[keyOf(r[0], r[1])] = r[2];
      state.map[keyOf(r[1], r[0])] = -r[2];
      // 비김이면 두 캐릭터를 '동점 링크'로 묶는다(원본 ary_EqualData 와 동일).
      // 한 번 묶이면 출력에서 늘 붙어 다니므로, 이후 모든 병합 단계에서
      // 이 묶음은 질문 한 번으로 통과한다 — 비김의 절약 효과가 누적된다.
      if (r[2] === 0) state.eqLink[r[0]] = r[1];
    });
  }

  function lookup(a, b) {
    var k = keyOf(a, b);
    return Object.prototype.hasOwnProperty.call(state.map, k) ? state.map[k] : null;
  }

  // ── 정렬 ─────────────────────────────────────────────────────────────
  function compare(a, b) {
    var v = lookup(a, b);
    if (v === null) {
      NEED.pair = [a, b];
      throw NEED;
    }
    return v;   // 1 이면 a 가 앞(더 선호)
  }

  function merge(left, right) {
    var out = [], i = 0, j = 0;

    // 방금 내보낸 캐릭터에 동점 링크가 걸려 있고 같은 쪽 다음 캐릭터가
    // 그 상대라면, 물어보지 않고 딸려 내보낸다(묶음은 절대 갈라지지 않는다).
    function drain(list, idx) {
      while (idx < list.length && state.eqLink[out[out.length - 1]] === list[idx]) {
        out.push(list[idx++]);
      }
      return idx;
    }

    while (i < left.length && j < right.length) {
      var v = compare(left[i], right[j]);
      if (v === 0) {
        out.push(left[i++]);
        i = drain(left, i);
        out.push(right[j++]);
        j = drain(right, j);
      } else if (v > 0) {
        out.push(left[i++]);
        i = drain(left, i);
      } else {
        out.push(right[j++]);
        j = drain(right, j);
      }
    }
    while (i < left.length) out.push(left[i++]);
    while (j < right.length) out.push(right[j++]);
    return out;
  }

  /** 정렬을 처음부터 다시 돌린다.
   *  끝까지 돌면 {done:true, list}, 질문이 필요하면 {done:false, pair}. */
  function runSort() {
    var arr = state.order.slice();
    var width = 1;
    try {
      while (width < arr.length) {
        var next = [];
        for (var i = 0; i < arr.length; i += 2 * width) {
          var L = arr.slice(i, i + width);
          var R = arr.slice(i + width, i + 2 * width);
          next = next.concat(R.length ? merge(L, R) : L);
        }
        arr = next;
        width *= 2;
      }
    } catch (e) {
      if (e !== NEED) throw e;
      return { done: false, pair: NEED.pair };
    }
    return { done: true, list: arr };
  }

  /** 토너먼트 브래킷 1회 → 우승자 반환. */
  function bracket(list) {
    var cur = list;
    while (cur.length > 1) {
      var next = [];
      for (var i = 0; i < cur.length; i += 2) {
        if (i + 1 >= cur.length) { next.push(cur[i]); continue; }
        next.push(compare(cur[i], cur[i + 1]) >= 0 ? cur[i] : cur[i + 1]);
      }
      cur = next;
    }
    return cur[0];
  }

  /** 우승자를 빼면서 브래킷을 K번 반복 → 상위 K명을 정확히 뽑는다. */
  function runTopK(k) {
    var pool = state.order.slice();
    var out = [];
    try {
      for (var i = 0; i < k && pool.length; i++) {
        var w = bracket(pool);
        out.push(w);
        pool = pool.filter(function (x) { return x !== w; });
      }
    } catch (e) {
      if (e !== NEED) throw e;
      return { done: false, pair: NEED.pair };
    }
    return { done: true, list: out };
  }

  function estTotal() { return estFor(state.mode, state.order.length); }

  // ── 저장/복원 ────────────────────────────────────────────────────────
  function save() {
    try {
      localStorage.setItem(SAVE_KEY, JSON.stringify({
        mode: state.mode, order: state.order, answers: state.answers, ts: Date.now()
      }));
    } catch (e) { /* 사파리 프라이빗 모드 등 — 저장 실패해도 진행엔 지장 없음 */ }
  }

  function loadSaved() {
    try {
      var raw = localStorage.getItem(SAVE_KEY);
      if (!raw) return null;
      var s = JSON.parse(raw);
      if (!s || !Array.isArray(s.order) || s.order.length < 2) return null;
      if (!s.order.every(function (id) { return BY_ID[id]; })) return null;
      if (!MODES[s.mode]) return null;
      return s;
    } catch (e) { return null; }
  }

  function clearSaved() {
    try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* noop */ }
  }

  // ── 게임 진행 ────────────────────────────────────────────────────────
  function startNew(mode) {
    state.mode = MODES[mode] ? mode : 'full';
    // 밴드끼리 뭉쳐서, 섞지 않고 시작한다(원본 소터와 동일).
    //   병합정렬은 초기 순서가 취향과 비슷할수록 질문이 줄어드는데,
    //   밴드 단위로 최애/비최애가 갈리는 사람이 많아서 이 배치가 크게 유리하다.
    //   같은 취향으로 실측: 무작위 취향 282→281(손해 없음),
    //   밴드끼리 뭉친 취향 281→248, 밴드 순서까지 맞으면 282→207.
    //   (참고 사이트도 셔플 없이 밴드 순서 그대로 시작한다 — 45명에 136~150문항)
    var byBand = [];
    BAND_ORDER.forEach(function (b) {
      byBand = byBand.concat(
        pickedChars().filter(function (c) { return c.bandKey === b; })
          .map(function (c) { return c.id; }));
    });
    state.order = byBand;
    state.answers = [];
    state.result = null;
    rebuildMap();
    clearSaved();
    step();
  }

  function resume(s) {
    state.mode = s.mode;
    state.order = s.order;
    state.answers = s.answers || [];
    state.result = null;
    rebuildMap();
    step();
  }

  function step() {
    var k = MODES[state.mode].k;
    var r = k ? runTopK(k) : runSort();
    if (r.done) {
      state.result = r.list;
      renderResult();
      show('result');
      return;
    }
    state.pending = r.pair;
    renderBattle(r.pair);
    show('battle');
  }

  function answer(v) {
    if (!state.pending) return;
    state.answers.push([state.pending[0], state.pending[1], v]);
    rebuildMap();
    save();
    step();
  }

  function undo() {
    if (!state.answers.length) return;
    state.answers.pop();
    rebuildMap();
    save();
    step();
  }

  // ── 대결 화면 렌더 ───────────────────────────────────────────────────
  var preloaded = {};
  function preload(id) {
    if (!id || preloaded[id]) return;
    preloaded[id] = true;
    var im = new Image();
    im.src = BY_ID[id].img;
  }

  function renderBattle(pair) {
    var L = BY_ID[pair[0]], R = BY_ID[pair[1]];

    setSide('left', L);
    setSide('right', R);

    var pct = Math.min(99, Math.round(state.answers.length / estTotal() * 100));
    $('progress-fill').style.width = pct + '%';
    $('progress-pct').textContent = pct;
    $('progress-cnt').textContent = state.answers.length + 1;
    $('btn-undo').disabled = state.answers.length === 0;

    // 다음에 나올 법한 카드 몇 장을 미리 받아둔다(모바일 체감 개선)
    var nextGuess = state.order.indexOf(pair[1]) + 1;
    preload(state.order[nextGuess]);
    preload(state.order[nextGuess + 1]);
  }

  function setSide(side, ch) {
    var card = $('card-' + side);
    card.style.setProperty('--band', ch.color);
    card.classList.remove('picked');
    var img = $('img-' + side);
    img.src = ch.img;
    img.alt = ch.name;
    $('name-' + side).textContent = ch.name;
    $('band-' + side).textContent = ch.band;
  }

  function pick(side) {
    var card = $('card-' + side);
    card.classList.add('picked');
    // 눌린 게 보이도록 아주 짧게 지연
    setTimeout(function () { answer(side === 'left' ? 1 : -1); }, 90);
  }

  // ── 순위 계산 (비김 = 같은 순위) ──────────────────────────────────────
  function rankedGroups() {
    var groups = [], cur = [state.result[0]];
    for (var i = 1; i < state.result.length; i++) {
      var prev = state.result[i - 1], now = state.result[i];
      if (lookup(prev, now) === 0) cur.push(now);
      else { groups.push(cur); cur = [now]; }
    }
    groups.push(cur);

    var rows = [], rank = 1;
    groups.forEach(function (g) {
      g.forEach(function (id) { rows.push({ rank: rank, ch: BY_ID[id] }); });
      rank += g.length;   // 공동 2위가 둘이면 다음은 4위
    });
    return rows;
  }

  // ── 결과 화면 렌더 ───────────────────────────────────────────────────
  var lastRows = [];

  function renderResult() {
    var rows = lastRows = rankedGroups();
    var d = new Date();
    $('result-date').textContent =
      d.getFullYear() + '.' + pad(d.getMonth() + 1) + '.' + pad(d.getDate());
    $('result-qcount').textContent = state.answers.length;
    $('result-mode').textContent = MODES[state.mode].label;
    $('result-note').hidden = !MODES[state.mode].k;

    var podium = $('podium');
    podium.innerHTML = '';
    rows.slice(0, 3).forEach(function (r) {
      var el = document.createElement('div');
      el.className = 'p-item';
      el.style.setProperty('--band', r.ch.color);
      el.innerHTML =
        '<img src="' + r.ch.img + '" alt="" loading="lazy">' +
        '<div class="p-rank">' + r.rank + '위</div>' +
        '<div class="p-name">' + esc(r.ch.name) + '</div>';
      podium.appendChild(el);
    });

    var list = $('rank-list');
    list.innerHTML = '';
    rows.forEach(function (r) {
      var li = document.createElement('li');
      li.style.setProperty('--band', r.ch.color);
      li.innerHTML =
        '<span class="r-num">' + r.rank + '</span>' +
        '<img src="' + r.ch.thumb + '" alt="" loading="lazy">' +
        '<span class="r-name">' + esc(r.ch.name) + '</span>' +
        '<span class="r-band">' + esc(r.ch.band) + '</span>';
      list.appendChild(li);
    });

    clearSaved();   // 완료됐으므로 '이어하기' 대상에서 뺀다
  }

  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  // ── 결과 이미지(캔버스 직접 그리기 — 외부 라이브러리 없음) ─────────────
  function buildCanvas() {
    var rows = lastRows;
    var COLS = rows.length > 30 ? 3 : (rows.length > 12 ? 2 : 1);
    var PER = Math.ceil(rows.length / COLS);
    var W = 1080, PAD = 40, HEAD = 190, FOOT = 92;
    var RH = 64, COLW = (W - PAD * 2) / COLS;
    var H = HEAD + PER * RH + FOOT;

    var cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    var g = cv.getContext('2d');

    // 배경
    var bg = g.createLinearGradient(0, 0, W, H);
    bg.addColorStop(0, '#15121f');
    bg.addColorStop(.5, '#0e0d14');
    bg.addColorStop(1, '#1a1428');
    g.fillStyle = bg; g.fillRect(0, 0, W, H);

    var glow = g.createRadialGradient(W * .15, 0, 0, W * .15, 0, 620);
    glow.addColorStop(0, 'rgba(255,92,158,.30)');
    glow.addColorStop(1, 'rgba(255,92,158,0)');
    g.fillStyle = glow; g.fillRect(0, 0, W, 620);

    // 헤더
    g.textAlign = 'center';
    g.fillStyle = '#ffffff';
    g.font = '900 52px "Noto Sans KR", sans-serif';
    g.fillText(MODES[state.mode].k
      ? '내 뱅드림 최애 TOP ' + MODES[state.mode].k
      : '내 뱅드림 최애 순위', W / 2, 84);

    var d = new Date();
    g.fillStyle = '#9a94b0';
    g.font = '500 22px "Noto Sans KR", sans-serif';
    g.fillText(d.getFullYear() + '.' + pad(d.getMonth() + 1) + '.' + pad(d.getDate())
      + ' · ' + rows.length + '명 · 질문 ' + state.answers.length + '회',
      W / 2, 124);

    g.strokeStyle = 'rgba(255,255,255,.12)';
    g.lineWidth = 1;
    g.beginPath(); g.moveTo(PAD, HEAD - 34); g.lineTo(W - PAD, HEAD - 34); g.stroke();

    // 순위 행
    g.textAlign = 'left';
    rows.forEach(function (r, i) {
      var col = Math.floor(i / PER), row = i % PER;
      var x = PAD + col * COLW, y = HEAD + row * RH;

      // 밴드 색 막대
      g.fillStyle = r.ch.color;
      g.fillRect(x, y + 6, 4, 46);

      // 썸네일
      var im = r.ch._im;
      if (im) {
        g.save();
        roundRect(g, x + 14, y + 10, 40, 40, 8);
        g.fillStyle = 'rgba(255,255,255,.06)';
        g.fill();
        g.clip();
        g.drawImage(im, x + 14, y + 10, 40, 40);
        g.restore();
      }

      // 등수
      g.fillStyle = r.rank <= 3 ? '#ffd76a' : '#7d7794';
      g.font = '900 22px "Noto Sans KR", sans-serif';
      g.fillText(String(r.rank), x + 64, y + 37);

      // 이름
      g.fillStyle = '#f2f0f8';
      g.font = '700 22px "Noto Sans KR", sans-serif';
      g.fillText(r.ch.name, x + 106, y + 30);

      // 밴드
      g.fillStyle = '#8b85a3';
      g.font = '500 15px "Noto Sans KR", sans-serif';
      g.fillText(r.ch.band, x + 106, y + 49);
    });

    // 푸터
    g.textAlign = 'center';
    g.fillStyle = '#6f6a85';
    g.font = '500 19px "Noto Sans KR", sans-serif';
    g.fillText('뱅드림 캐릭터 소터 · bandorigall.github.io/others.github.io/sorter/',
      W / 2, H - 38);

    return cv;
  }

  function roundRect(g, x, y, w, h, r) {
    g.beginPath();
    g.moveTo(x + r, y);
    g.arcTo(x + w, y, x + w, y + h, r);
    g.arcTo(x + w, y + h, x, y + h, r);
    g.arcTo(x, y + h, x, y, r);
    g.arcTo(x, y, x + w, y, r);
    g.closePath();
  }

  /** 썸네일을 전부 로드한 뒤 캔버스를 만든다(그릴 때 비어 있으면 안 되므로). */
  function withImages() {
    return Promise.all(lastRows.map(function (r) {
      if (r.ch._im) return Promise.resolve();
      return new Promise(function (res) {
        var im = new Image();
        im.onload = function () { r.ch._im = im; res(); };
        im.onerror = function () { res(); };   // 한 장 실패해도 나머지는 그린다
        im.src = r.ch.thumb;
      });
    })).then(buildCanvas);
  }

  function toast(msg) {
    var t = $('toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.hidden = true; }, 2200);
  }

  function savePng() {
    withImages().then(function (cv) {
      cv.toBlob(function (blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'bangdream_sorter.png';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
        toast('이미지를 저장했어요');
      }, 'image/png');
    });
  }

  function copyPng() {
    if (!navigator.clipboard || !window.ClipboardItem) {
      toast('이 브라우저는 이미지 복사가 안 돼요. 저장을 써주세요');
      return;
    }
    withImages().then(function (cv) {
      cv.toBlob(function (blob) {
        navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
          .then(function () { toast('이미지를 복사했어요'); })
          .catch(function () { toast('복사 실패 — 저장을 써주세요'); });
      }, 'image/png');
    });
  }

  function copyText() {
    var byRank = {};
    lastRows.forEach(function (r) {
      (byRank[r.rank] = byRank[r.rank] || []).push(r.ch.name);
    });
    var lines = Object.keys(byRank)
      .sort(function (a, b) { return a - b; })
      .map(function (k) { return k + '위 ' + byRank[k].join(', '); });
    var txt = '[내 뱅드림 최애 순위]\n' + lines.join('\n')
      + '\n\nbandorigall.github.io/others.github.io/sorter/';

    copyToClipboard(txt)
      .then(function () { toast('순위를 복사했어요'); })
      .catch(function () { toast('복사 실패'); });
  }

  function copyToClipboard(txt) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(txt);
    }
    // 구형 브라우저 폴백
    return new Promise(function (res, rej) {
      var ta = document.createElement('textarea');
      ta.value = txt;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      ta.remove();
      ok ? res() : rej();
    });
  }

  // ── 이벤트 ───────────────────────────────────────────────────────────
  $('card-left').addEventListener('click', function () { pick('left'); });
  $('card-right').addEventListener('click', function () { pick('right'); });
  $('btn-tie').addEventListener('click', function () { answer(0); });
  $('btn-undo').addEventListener('click', undo);
  $('btn-quit').addEventListener('click', function () {
    save();
    location.reload();
  });
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-mode]'), function (el) {
      el.addEventListener('click', function () { startNew(el.dataset.mode); });
    });
  $('btn-restart').addEventListener('click', function () {
    clearSaved();
    location.reload();          // 모드를 다시 고를 수 있게 시작 화면으로
  });
  $('btn-png').addEventListener('click', savePng);
  $('btn-copy-img').addEventListener('click', copyPng);
  $('btn-copy-txt').addEventListener('click', copyText);

  document.addEventListener('keydown', function (e) {
    if (screens.battle.hidden) return;
    if (e.key === 'ArrowLeft') { e.preventDefault(); pick('left'); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); pick('right'); }
    else if (e.key === ' ') { e.preventDefault(); answer(0); }
    else if (e.key === 'z' || e.key === 'Z') { e.preventDefault(); undo(); }
  });

  // ── 초기화 ───────────────────────────────────────────────────────────
  $('intro-count').textContent = CHARS.length + '명';
  $('btn-band-all').addEventListener('click', function () {
    BAND_ORDER.forEach(function (b) { picked[b] = true; });
    renderBands();
  });
  $('btn-band-none').addEventListener('click', function () {
    BAND_ORDER.forEach(function (b) { picked[b] = false; });
    renderBands();
  });
  renderBands();

  var saved = loadSaved();
  if (saved && saved.answers && saved.answers.length) {
    var pct = Math.min(99, Math.round(saved.answers.length / estFor(saved.mode, saved.order.length) * 100));
    $('resume-progress').textContent = pct;
    $('resume-mode').textContent = MODES[saved.mode].label;
    $('resume-box').hidden = false;
    $('btn-resume').addEventListener('click', function () { resume(saved); });
    $('btn-discard').addEventListener('click', function () {
      clearSaved();
      $('resume-box').hidden = true;
    });
  }
})();
