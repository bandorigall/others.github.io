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
 *   cup   : 진짜 이상형 월드컵. 단판 토너먼트를 한 번만 돌려 우승자 한 명을 뽑는다.
 *           순위는 매기지 않고 '32강 → 16강 → … → 결승' 라운드만 보여준다.
 *           인원이 2의 거듭제곱이 아니면 예선(부전승)으로 먼저 줄인다.
 *           질문 수는 항상 n-1 (60명이면 59문항). 비김은 쓰지 않는다.
 *           ※ 예전의 TOP10/TOP20(브래킷 반복으로 상위 K명 정확 산출) 모드는
 *             2026-08-01 사용자 요청으로 제거했다. 되살리지 말 것.
 *
 * [비김] 답변값 0. 두 캐릭터를 eqLink 로 묶어 이후 병합에서 질문 없이 딸려보낸다.
 *   순위 계산에서 인접한 두 캐릭터의 답이 0이면 같은 순위로 묶는다.
 *
 * [시작 명단] 무작위로 섞는다. 밴드로는 묶지 않는다.
 *   초기 순서는 결과 정확도에 영향이 없고 질문 수에만 영향을 주는데,
 *   밴드 군집을 안 쓰는 이상 어떤 순서든 질문 수가 같다(실측 280 내외).
 *   그래서 매번 다른 대진이 나오도록 섞는 쪽을 택했다.
 *   ※ 밴드 군집은 되살리지 말 것 — 밴드 단위로 취향이 갈리는 사람에게만
 *     이득인데, 실제로는 그렇지 않다는 판단(2026-08-01 사용자 결정).
 *
 * [좌우 배치] 매 질문마다 좌우를 결정적 해시로 뒤집는다.
 *   병합정렬은 한쪽을 고정한 채 상대만 바꿔 묻기 때문에, 자리까지 고정하면
 *   같은 캐릭터가 계속 왼쪽에 박혀 보여 편향·지루함을 준다.
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
    full: { label: '전체 순위', cup: false },
    cup:  { label: '월드컵',    cup: true }
  };

  /** 진행률 분모(= 예상 최대 질문 수). 인원수 n 에 따라 계산한다.
   *  full : 병합정렬 최악 비교 횟수 n*ceil(log2 n) - 2^ceil(log2 n) + 1
   *         (비김을 쓰면 실제론 이보다 훨씬 적게 끝난다 — 진행률은 99%에서 멈춰 둔다)
   *  cup  : 탈락 토너먼트라 정확히 n-1 회. */
  function estFor(mode, n) {
    if (n < 2) return 1;
    if (MODES[mode].cup) return n - 1;
    var lg = Math.ceil(Math.log2(n));
    return n * lg - Math.pow(2, lg) + 1;
  }

  /** 월드컵 본선 시작 라운드(= n 이하의 가장 큰 2의 거듭제곱). 60명이면 32. */
  function cupTop(n) {
    var p = 1;
    while (p * 2 <= n) p *= 2;
    return p;
  }

  var state = {
    mode: 'cup',
    order: [],                   // 시작 명단(무작위로 섞음)
    answers: [],                 // [[idA, idB, v], ...]  v: 1=A선호, -1=B선호, 0=비김
    map: {},                     // "idA|idB" -> v
    eqLink: {},                  // 비김으로 묶인 쌍 (idA -> idB)
    pending: null,               // 지금 화면에 띄운 [idA, idB]
    swapped: false,              // 화면에서 좌우를 뒤집어 보여주는 중인지
    result: null,                // 완료 시 정렬된 id 배열
    matches: null                // 월드컵 전 경기 기록(대진표용)
  };

  // ── 밴드 선택 ────────────────────────────────────────────────────────
  var BAND_ORDER = [];
  CHARS.forEach(function (c) {
    if (BAND_ORDER.indexOf(c.bandKey) < 0) BAND_ORDER.push(c.bandKey);
  });
  // 부가(조연) 캐릭터는 기본 제외. 원하는 사람만 칩을 켜서 넣는다.
  function isOptionalBand(b) {
    return CHARS.every(function (c) { return c.bandKey !== b || c.optional; });
  }
  var picked = {};
  BAND_ORDER.forEach(function (b) { picked[b] = !isOptionalBand(b); });

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
      el.className = 'band' + (picked[b] ? ' on' : '') +
        (isOptionalBand(b) ? ' optional' : '');
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
        var few = n < 2;
        el.disabled = few;
        // '전체 60위' 라벨도 선택 인원에 맞춘다
        if (m === 'full') {
          var nm = el.querySelector('.m-name');
          if (nm) nm.innerHTML = '전체 ' + n + '위<kbd class="k">2</kbd>';
        }
        var q = el.querySelector('.m-q');
        if (q) {
          q.textContent = few
            ? '2명 이상 골라주세요'
            : (MODES[m].cup
                ? cupTop(n) + '강부터 · 딱 ' + estFor(m, n) + '문항'
                : '최대 ' + estFor(m, n) + '문항 (비김 쓰면 더 줄어요)');
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

  /** 월드컵(단판 토너먼트) — 우승자 한 명만 뽑는다. 순위는 만들지 않는다.
   *  인원이 2의 거듭제곱이 아니면 먼저 예선을 치러 2의 거듭제곱으로 줄인다.
   *  (예: 60명 → 예선 28경기 → 32강. 예선을 안 치른 4명은 부전승)
   *  질문이 필요하면 NEED 에 지금 라운드 정보(round/matchNo/matchTotal)를 실어 던진다. */
  function runCup() {
    var round = { size: 0, no: 0, total: 0, prelim: false };
    var matches = [];               // 대진표를 그리려고 모든 경기를 기록한다

    function play(a, b) {
      round.no++;
      NEED.round = {
        size: round.size, no: round.no, total: round.total, prelim: round.prelim
      };
      var w = compare(a, b) >= 0 ? a : b;   // 월드컵엔 비김이 없다(0이면 앞쪽 승)
      matches.push({ size: round.size, prelim: round.prelim, a: a, b: b, w: w });
      return w;
    }

    try {
      var cur = state.order.slice();
      var pow = 1;
      while (pow * 2 <= cur.length) pow *= 2;
      var extra = cur.length - pow;          // 예선을 치러야 하는 경기 수

      if (extra > 0) {
        round.size = cur.length; round.no = 0; round.total = extra; round.prelim = true;
        var after = [];
        for (var i = 0; i < extra * 2; i += 2) after.push(play(cur[i], cur[i + 1]));
        cur = after.concat(cur.slice(extra * 2));   // 나머지는 부전승
      }

      while (cur.length > 1) {
        round.size = cur.length; round.no = 0;
        round.total = cur.length / 2; round.prelim = false;
        var next = [];
        for (var j = 0; j < cur.length; j += 2) next.push(play(cur[j], cur[j + 1]));
        cur = next;
      }
    } catch (e) {
      if (e !== NEED) throw e;
      return { done: false, pair: NEED.pair, round: NEED.round };
    }
    return { done: true, list: cur, matches: matches };
  }

  /** '16강' · '결승' 같은 라운드 이름. */
  function roundLabel(r) {
    if (!r) return '';
    if (r.prelim) return '예선';
    if (r.size === 2) return '결승';
    if (r.size === 4) return '4강';
    return r.size + '강';
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
  function shuffle(list) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function startNew(mode) {
    state.mode = MODES[mode] ? mode : 'cup';
    // 시작 명단은 무작위로 섞는다.
    //   밴드 군집은 쓰지 않기로 했으므로(=이미 취향과 무관한 순서) 섞어도
    //   질문 수가 늘지 않는다. 대신 매번 다른 대진이 나와 덜 지루하다.
    state.order = shuffle(pickedChars().map(function (c) { return c.id; }));
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
    var r = MODES[state.mode].cup ? runCup() : runSort();
    if (r.done) {
      state.result = r.list;
      state.matches = r.matches || null;
      renderResult();
      show('result');
      return;
    }
    state.pending = r.pair;
    renderBattle(r.pair, r.round);
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

  /** 카드를 어느 쪽에 놓을지 결정한다.
   *  병합정렬은 한쪽 캐릭터를 고정한 채 상대만 바꿔가며 묻기 때문에,
   *  자리까지 고정하면 "같은 애가 계속 왼쪽에 박혀 있다"는 느낌이 강해진다.
   *  쌍과 진행도로 해시를 만들어 좌우를 섞되, 되돌리기를 해도 같은 배치가
   *  다시 나오도록 '결정적으로' 계산한다. */
  function isSwapped(pair) {
    var s = pair[0] + '|' + pair[1] + '|' + state.answers.length;
    var h = 0;
    for (var i = 0; i < s.length; i++) {
      h = ((h << 5) - h + s.charCodeAt(i)) | 0;
    }
    return (h & 1) === 1;
  }

  function renderBattle(pair, round) {
    state.swapped = isSwapped(pair);
    var first = state.swapped ? pair[1] : pair[0];
    var second = state.swapped ? pair[0] : pair[1];
    var L = BY_ID[first], R = BY_ID[second];

    setSide('left', L);
    setSide('right', R);

    var cup = MODES[state.mode].cup;
    $('btn-tie').hidden = cup;      // 월드컵엔 비김이 없다
    var pct = Math.round(state.answers.length / estTotal() * 100);
    if (!cup) pct = Math.min(99, pct);   // 병합정렬은 끝나는 지점을 정확히 못 잡는다
    $('progress-fill').style.width = pct + '%';

    // 월드컵은 진행률 대신 라운드를 보여준다 ('16강 · 3/8경기')
    if (cup) {
      $('progress-txt').innerHTML = '<b>' + esc(roundLabel(round)) + '</b> · ' +
        (round ? round.no + '/' + round.total + '경기' : '');
      $('battle-q').textContent =
        round && !round.prelim && round.size === 2 ? '결승! 최애는?' : '더 좋아하는 쪽은?';
    } else {
      $('progress-txt').innerHTML = '<b id="progress-pct">' + pct + '</b>% · ' +
        '<span id="progress-cnt">' + (state.answers.length + 1) + '</span>번째 질문';
    }
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
    // 화면에서 좌우를 뒤집었을 수 있으므로, 누른 자리를 원래 쌍 기준으로 되돌린다.
    var leftIsFirst = !state.swapped;
    var v = (side === 'left') === leftIsFirst ? 1 : -1;
    // 눌린 게 보이도록 아주 짧게 지연
    setTimeout(function () { answer(v); }, 90);
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
    var cup = MODES[state.mode].cup;
    var d = new Date();
    $('result-date').textContent =
      d.getFullYear() + '.' + pad(d.getMonth() + 1) + '.' + pad(d.getDate());
    $('result-qcount').textContent = state.answers.length;
    $('result-mode').textContent = MODES[state.mode].label;
    $('result-note').hidden = !cup;
    $('result-title').textContent = cup ? '내 뱅드림 최애 월드컵 우승' : '내 뱅드림 최애 순위';

    // 월드컵은 우승자 한 명만 크게 띄운다(순위표·시상대 없음)
    $('cup-top').hidden = !cup;
    $('bracket-wrap').hidden = !cup;
    $('podium').hidden = cup;
    $('rank-list').hidden = cup;
    if (cup) {
      var w = rows[0].ch;
      var el = $('champion');
      el.style.setProperty('--band', w.color);
      el.innerHTML =
        '<div class="c-crown">우승</div>' +
        '<img src="' + w.img + '" alt="">' +
        '<div class="c-name">' + esc(w.name) + '</div>' +
        '<div class="c-band">' + esc(w.band) + '</div>';
      renderTopBracket(w.id);
      renderBracket(w.id);
      // 예선까지 든 전체 대진표는 세로로 아주 길다. 폰에서는 접어둔다.
      $('full-bracket').open = window.innerWidth > 780;
      clearSaved();
      return;
    }

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

  /** 우승자가 밟고 온 경기들(예선 → 결승 순). */
  function championPath(champId) {
    return (state.matches || []).filter(function (m) { return m.w === champId; });
  }

  /** 경기 기록을 라운드별로 묶는다(기록 순서 = 진행 순서라 그대로 훑으면 된다). */
  function groupRounds(ms) {
    var rounds = [], cur = null;
    ms.forEach(function (m) {
      var label = roundLabel(m);
      if (!cur || cur.label !== label) { cur = { label: label, list: [], size: m.size, prelim: m.prelim }; rounds.push(cur); }
      cur.list.push(m);
    });
    return rounds;
  }

  /** 상위 토너먼트에 그릴 라운드(8강·4강·결승). 화면과 결과 이미지가 같이 쓴다. */
  function topRounds() {
    return groupRounds(state.matches || []).filter(function (r) {
      return !r.prelim && r.size <= 8;
    });
  }

  /** 우승 카드 오른쪽의 '상위 토너먼트'. 예선·초반 라운드는 빼고 8강부터만 그린다.
   *  (인원이 적어 8강이 없으면 있는 라운드만. 전체 대진표는 아래에 따로 있다)
   *  라운드 j번째 경기의 승자가 다음 라운드 j/2번째 경기로 가므로,
   *  기록 순서대로 칸을 세우면 그대로 대진표 모양이 된다.
   *  ★ 칸 순서는 뒤집어서(결승 → 4강 → 8강) 왼쪽 우승 카드 쪽으로 좁아지게 그린다.
   *    그래야 왼쪽 우승 카드가 대진표의 끝점처럼 이어져 보인다. */
  function renderTopBracket(champId) {
    var wrap = $('top-bracket');
    wrap.innerHTML = '';
    var rounds = topRounds();
    if (!rounds.length) { $('top-bracket-wrap').hidden = true; return; }
    $('top-bracket-wrap').hidden = false;
    $('top-bracket-title').textContent = '상위 토너먼트 · ' + rounds[0].label + '부터';

    rounds.slice().reverse().forEach(function (r) {
      var col = document.createElement('div');
      col.className = 'tb-round';
      var html = '<h4>' + esc(r.label) + '</h4><div class="tb-col">';
      r.list.forEach(function (m) {
        html += '<div class="tb-m">' + tbSide(m.a, m) + '<span class="tb-vs">vs</span>' + tbSide(m.b, m) + '</div>';
      });
      col.innerHTML = html + '</div>';
      wrap.appendChild(col);
    });

    function tbSide(id, m) {
      var c = BY_ID[id];
      return '<span class="tb-p' + (m.w === id ? ' win' : ' lose') +
        '" style="--band:' + c.color + '">' +
        '<img src="' + c.img + '" alt="" loading="lazy">' +
        '<b>' + esc(c.name) + '</b></span>';
    }
  }

  /** 대진표. 라운드별로 세로 한 칸씩, 가로로 훑어보는 형태(모바일은 좌우 스크롤).
   *  경기 수가 많은 예선까지 전부 그리되 우승자 경로만 강조한다. */
  function renderBracket(champId) {
    var ms = state.matches || [];
    var wrap = $('bracket');
    wrap.innerHTML = '';
    if (!ms.length) return;

    // 우승자 경로 요약 (예선 vs OO → 32강 vs OO → …)
    var path = championPath(champId);
    $('bracket-path').innerHTML = path.map(function (m) {
      var foe = BY_ID[m.a === champId ? m.b : m.a];
      return '<span class="bp-item"><b>' + esc(roundLabel(m)) + '</b> ' + esc(foe.name) + '</span>';
    }).join('<span class="bp-sep">›</span>');

    groupRounds(ms).forEach(function (r) {
      var col = document.createElement('div');
      col.className = 'br-round';
      var html = '<h4>' + esc(r.label) + '<span>' + r.list.length + '경기</span></h4>';
      r.list.forEach(function (m) {
        html += '<div class="br-m">' + side(m.a, m) + side(m.b, m) + '</div>';
      });
      col.innerHTML = html;
      wrap.appendChild(col);
    });

    // 마지막에 우승자 칸
    var last = document.createElement('div');
    last.className = 'br-round';
    var ch = BY_ID[champId];
    last.innerHTML = '<h4>우승<span>&nbsp;</span></h4>' +
      '<div class="br-m"><span class="br-p win champ" style="--band:' + ch.color + '">' +
      '<img src="' + ch.thumb + '" alt="" loading="lazy">' + esc(ch.name) + '</span></div>';
    wrap.appendChild(last);

    function side(id, m) {
      var c = BY_ID[id];
      return '<span class="br-p' + (m.w === id ? ' win' : '') +
        (m.w === id && id === champId ? ' champ' : '') +
        '" style="--band:' + c.color + '">' +
        '<img src="' + c.thumb + '" alt="" loading="lazy">' + esc(c.name) + '</span>';
    }
  }

  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  // ── 결과 이미지(캔버스 직접 그리기 — 외부 라이브러리 없음) ─────────────
  function buildCanvas() {
    if (MODES[state.mode].cup) return buildCupCanvas();
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

  /** 월드컵 결과 이미지.
   *  화면과 같은 구성 — 왼쪽에 우승 카드, 오른쪽에 상위 토너먼트(결승 → 4강 → 8강).
   *  라운드가 없을 만큼 인원이 적으면 우승 카드만 가운데에 크게 그린다. */
  function buildCupCanvas() {
    var ch = lastRows[0].ch;
    var rounds = topRounds().slice().reverse();   // 왼쪽부터 결승 → 4강 → 8강
    var path = championPath(ch.id);
    var solo = !rounds.length;

    var W = 1080, CT = 176, CH = 560;             // 내용 시작 y, 내용 높이
    var pathH = solo ? 56 + path.length * 34 : 0;
    var H = CT + CH + pathH + 122;

    var cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    var g = cv.getContext('2d');

    var bg = g.createLinearGradient(0, 0, W, H);
    bg.addColorStop(0, '#15121f');
    bg.addColorStop(.5, '#0e0d14');
    bg.addColorStop(1, '#1a1428');
    g.fillStyle = bg; g.fillRect(0, 0, W, H);

    var cx = solo ? W / 2 : 254;                  // 우승 카드 가로 중심
    var glow = g.createRadialGradient(cx, CT + 240, 0, cx, CT + 240, 520);
    glow.addColorStop(0, hexA(ch.color, .34));
    glow.addColorStop(1, hexA(ch.color, 0));
    g.fillStyle = glow; g.fillRect(0, 0, W, H);

    // 머리말
    g.textAlign = 'center';
    g.fillStyle = '#9a94b0';
    g.font = '700 26px "Noto Sans KR", sans-serif';
    g.fillText('뱅드림 캐릭터 월드컵 · ' + cupTop(state.order.length) + '강', W / 2, 72);
    g.fillStyle = '#ffd76a';
    g.font = '900 44px "Noto Sans KR", sans-serif';
    g.fillText('우승', cx, 136);

    // 우승자 카드
    var S = solo ? 460 : 420, ix = cx - S / 2, iy = CT;
    if (ch._im) {
      g.save();
      roundRect(g, ix, iy, S, S, 28);
      g.fillStyle = 'rgba(255,255,255,.06)';
      g.fill();
      g.strokeStyle = ch.color; g.lineWidth = 5; g.stroke();
      g.clip();
      g.drawImage(ch._im, ix, iy, S, S);
      g.restore();
    }
    g.fillStyle = '#ffffff';
    g.font = '900 54px "Noto Sans KR", sans-serif';
    g.fillText(ch.name, cx, iy + S + 60);
    g.fillStyle = lighten(ch.color);   // 어두운 밴드색은 검은 배경에 묻힌다
    g.font = '700 26px "Noto Sans KR", sans-serif';
    g.fillText(ch.band, cx, iy + S + 98);

    if (solo) {
      // 대진표를 그릴 라운드가 없을 때만 '우승까지의 길'을 글로 적는다
      g.fillStyle = '#8b85a3';
      g.font = '700 22px "Noto Sans KR", sans-serif';
      g.fillText('우승까지의 길', W / 2, CT + CH + 20);
      path.forEach(function (m, i) {
        var foe = BY_ID[m.a === ch.id ? m.b : m.a], y = CT + CH + 62 + i * 34;
        g.textAlign = 'right';
        g.fillStyle = '#ffd76a';
        g.font = '700 21px "Noto Sans KR", sans-serif';
        g.fillText(roundLabel(m), W / 2 - 14, y);
        g.textAlign = 'left';
        g.fillStyle = '#cfcadd';
        g.font = '500 21px "Noto Sans KR", sans-serif';
        g.fillText('vs ' + foe.name, W / 2 + 14, y);
      });
    } else {
      drawTopBracket(g, rounds, ch.id, 512, CT - 40, W - 512 - 40, CH + 40);
    }

    g.textAlign = 'center';
    var d = new Date();
    g.fillStyle = '#8b85a3';
    g.font = '500 22px "Noto Sans KR", sans-serif';
    g.fillText(d.getFullYear() + '.' + pad(d.getMonth() + 1) + '.' + pad(d.getDate())
      + ' · ' + state.order.length + '명 · ' + state.answers.length + '경기',
      W / 2, H - 78);

    g.fillStyle = '#6f6a85';
    g.font = '500 19px "Noto Sans KR", sans-serif';
    g.fillText('뱅드림 캐릭터 소터 · bandorigall.github.io/others.github.io/sorter/',
      W / 2, H - 34);
    return cv;
  }

  /** 상위 토너먼트를 (x,y,w,h) 안에 그린다. 라운드 = 세로 칸, 경기 = 칸 안 셀.
   *  경기 수가 절반씩 줄어드는 걸 이용해 셀을 균등 배치하면 대진표 모양이 된다. */
  function drawTopBracket(g, rounds, champId, x, y, w, h) {
    var GAP = 12;
    var CW = (w - GAP * (rounds.length - 1)) / rounds.length;
    var TOP = y + 34;                   // 라운드 이름 아래부터가 경기 영역
    var BH = h - 34;

    rounds.forEach(function (r, ri) {
      var cxx = x + ri * (CW + GAP);
      g.textAlign = 'center';
      g.fillStyle = '#8b85a3';
      g.font = '900 20px "Noto Sans KR", sans-serif';
      g.fillText(r.label, cxx + CW / 2, y + 22);

      var cell = BH / r.list.length;
      r.list.forEach(function (m, mi) {
        var cy = TOP + cell * (mi + .5);           // 셀 세로 중심
        var boxH = 116;
        g.fillStyle = 'rgba(255,255,255,.04)';
        roundRect(g, cxx, cy - boxH / 2, CW, boxH, 12);
        g.fill();
        player(m.a, m, cxx + 6, cy - boxH / 2 + 6, CW - 12);
        g.fillStyle = '#6f6a85';
        g.font = '500 13px "Noto Sans KR", sans-serif';
        g.textAlign = 'center';
        g.fillText('vs', cxx + CW / 2, cy + 4);
        player(m.b, m, cxx + 6, cy + 6, CW - 12);
      });
    });

    /** 한 명 = 썸네일 + 이름. 이긴 쪽만 밴드색으로 켠다(진 쪽은 흐리게). */
    function player(id, m, px, py, pw) {
      var c = BY_ID[id], win = m.w === id, T = 40;
      if (win) {
        g.fillStyle = hexA(c.color, .18);
        roundRect(g, px, py, pw, T + 8, 9);
        g.fill();
      }
      g.save();
      g.globalAlpha = win ? 1 : .4;
      roundRect(g, px + 4, py + 4, T, T, 8);
      g.fillStyle = 'rgba(255,255,255,.06)';
      g.fill();
      g.clip();
      if (c._imT) g.drawImage(c._imT, px + 4, py + 4, T, T);
      g.restore();

      g.textAlign = 'left';
      g.fillStyle = win ? (id === champId ? lighten(c.color, .6) : '#f2f0f8') : '#7d7794';
      g.font = (win ? '700 ' : '500 ') + '18px "Noto Sans KR", sans-serif';
      fitText(g, c.name, px + T + 12, py + 30, pw - T - 16);
    }
  }

  /** 폭을 넘치면 뒤를 잘라 '…' 를 붙여 그린다. */
  function fitText(g, text, x, y, max) {
    var t = text;
    while (t.length > 1 && g.measureText(t + '…').width > max) t = t.slice(0, -1);
    g.fillText(t === text ? t : t + '…', x, y);
  }

  /** 밴드색에 흰색을 섞어 밝게. 검은 배경 위 글자색으로 쓰려고(CSS 쪽도 같은 처리). */
  function lighten(hex, amt) {
    var m = /^#?([0-9a-f]{6})$/i.exec(String(hex));
    if (!m) return '#ffffff';
    var n = parseInt(m[1], 16), a = amt === undefined ? .45 : amt;
    function mix(c) { return Math.round(c + (255 - c) * a); }
    return 'rgb(' + mix(n >> 16 & 255) + ',' + mix(n >> 8 & 255) + ',' + mix(n & 255) + ')';
  }

  /** '#rrggbb' + 알파 → rgba() 문자열. 밴드색을 그라데이션에 쓰려고. */
  function hexA(hex, a) {
    var m = /^#?([0-9a-f]{6})$/i.exec(String(hex));
    if (!m) return 'rgba(255,92,158,' + a + ')';
    var n = parseInt(m[1], 16);
    return 'rgba(' + (n >> 16 & 255) + ',' + (n >> 8 & 255) + ',' + (n & 255) + ',' + a + ')';
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
    // 월드컵은 우승자를 크게 그리므로 썸네일 대신 카드 이미지를 쓴다
    var big = MODES[state.mode].cup;
    var jobs = lastRows.map(function (r) {
      if (r.ch._im && r.ch._imBig === big) return Promise.resolve();
      return load(big ? r.ch.img : r.ch.thumb).then(function (im) {
        if (im) { r.ch._im = im; r.ch._imBig = big; }
      });
    });

    // 월드컵이면 대진표에 나오는 캐릭터들의 썸네일(_imT)도 같이 받아둔다
    if (big) {
      var seen = {};
      topRounds().forEach(function (r) {
        r.list.forEach(function (m) {
          [m.a, m.b].forEach(function (id) {
            var c = BY_ID[id];
            if (seen[id] || c._imT) return;
            seen[id] = 1;
            jobs.push(load(c.thumb).then(function (im) { if (im) c._imT = im; }));
          });
        });
      });
    }
    return Promise.all(jobs).then(buildCanvas);

    function load(src) {
      return new Promise(function (res) {
        var im = new Image();
        im.onload = function () { res(im); };
        im.onerror = function () { res(null); };   // 한 장 실패해도 나머지는 그린다
        im.src = src;
      });
    }
  }

  // ── 결과 이미지 ② 화면 그대로 찍기(DOM → SVG foreignObject → 캔버스) ────
  //  캔버스로 다시 그린 그림은 화면과 미묘하게 달라서(레이아웃을 손으로 계산하니
  //  글자가 겹치거나 잘렸다) 결국 화면 자체를 스냅샷 뜨는 쪽으로 바꿨다.
  //  외부 라이브러리(html2canvas) 없이:
  //    ① 결과 화면을 복제 → 버튼·토스트·전체 대진표를 뺀다
  //    ② <img> 를 전부 data URI 로 바꾼다(외부 참조가 있으면 SVG 가 안 그려진다)
  //    ③ styles.css 본문을 <style> 로 넣고 통째로 <foreignObject> 에 담아
  //       data:image/svg+xml 이미지로 만들어 캔버스에 그린다.
  //  ※ 외부 폰트(Noto Sans KR)는 SVG 안에서 못 받아오므로 시스템 폰트로 대체된다.
  //  ※ 실패하면(구형 브라우저·fetch 차단 등) 예전 캔버스 그림으로 자동 폴백한다.
  var CSS_TEXT = null;

  function loadCss() {
    if (CSS_TEXT !== null) return Promise.resolve(CSS_TEXT);
    return fetch('styles.css').then(function (r) { return r.text(); })
      .then(function (t) { CSS_TEXT = t; return t; });
  }

  /** 스냅샷 안에서 쓸 웹폰트를 통째로 심는다.
   *  SVG(foreignObject) 안에서는 외부 폰트를 못 받아오므로, 안 심으면 시스템 폰트로
   *  대체돼 화면과 굵기·모양이 달라진다(= '화면이랑 다르게 찍힌다'의 원인).
   *  구글 폰트의 text= 파라미터로 '실제로 쓰인 글자'만 뽑아 오면 몇십 KB면 된다. */
  function fontCss(chars) {
    var url = 'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900'
      + '&text=' + encodeURIComponent(chars);
    return fetch(url).then(function (r) { return r.text(); }).then(function (css) {
      var links = css.match(/https:\/\/fonts\.gstatic\.com[^)'"]+/g) || [];
      var uniq = links.filter(function (u, i) { return links.indexOf(u) === i; });
      return Promise.all(uniq.map(function (u) {
        return fetch(u).then(function (r) { return r.blob(); }).then(function (b) {
          return new Promise(function (res) {
            var fr = new FileReader();
            fr.onload = function () { css = css.split(u).join(fr.result); res(); };
            fr.onerror = function () { res(); };
            fr.readAsDataURL(b);
          });
        }).catch(function () {});
      })).then(function () { return css; });
    }).catch(function () { return ''; });   // 폰트를 못 받아도 그림은 나오게
  }

  /** 같은 폴더의 이미지들을 data URI 로 바꿔 끼운다. */
  function inlineImages(root) {
    var imgs = Array.prototype.slice.call(root.querySelectorAll('img'));
    return Promise.all(imgs.map(function (im) {
      return fetch(im.src).then(function (r) { return r.blob(); })
        .then(function (b) {
          return new Promise(function (res) {
            var fr = new FileReader();
            fr.onload = function () { im.setAttribute('src', fr.result); res(); };
            fr.onerror = function () { res(); };
            fr.readAsDataURL(b);
          });
        })
        .catch(function () { im.removeAttribute('src'); });
    }));
  }

  function buildDomCanvas() {
    var src = $('screen-result');
    // 폭은 화면과 무관하게 1080 고정. foreignObject 안에서는 미디어쿼리가
    // SVG 뷰포트(=이 폭) 기준으로 걸리므로, 폰에서도 PC 배치(우승 카드+토너먼트 2단)로 찍힌다.
    var W = 1080;

    var clone = src.cloneNode(true);
    clone.removeAttribute('id');
    // 이미지에 남으면 안 되는 것들(버튼·안내·토스트·긴 전체 대진표)
    ['.result-actions', '.toast', '#bracket-wrap', '.result-note', '.bracket-hint']
      .forEach(function (sel) {
        Array.prototype.forEach.call(clone.querySelectorAll(sel), function (el) {
          el.parentNode.removeChild(el);
        });
      });
    var foot = document.createElement('p');
    foot.className = 'shot-foot';
    foot.textContent = '뱅드림 캐릭터 소터 · bandorigall.github.io/others.github.io/sorter/';
    clone.appendChild(foot);

    // 높이를 재려면 실제로 배치해봐야 한다 → 화면 밖에 잠깐 붙였다 뗀다
    var stage = document.createElement('div');
    stage.setAttribute('style',
      'position:fixed;left:-10000px;top:0;width:' + W + 'px;pointer-events:none;');
    stage.appendChild(clone);
    document.body.appendChild(stage);

    // 이미지에 실제로 들어가는 글자만 모아 폰트를 subset 으로 받는다
    var used = (clone.textContent || '').replace(/\s+/g, '');
    var chars = '';
    for (var ci = 0; ci < used.length; ci++) {
      if (chars.indexOf(used[ci]) < 0) chars += used[ci];
    }

    return Promise.all([loadCss(), fontCss(chars), inlineImages(clone)])
      .then(function (r) {
        var css = r[1] + '\n' + r[0];
        var H = Math.ceil(clone.getBoundingClientRect().height);
        // ★ SVG 안에는 <html>/<body> 가 없다. styles.css 의 글자색·폰트·CSS 변수는
        //   html,body / :root 에 걸려 있어서 그대로 두면 전부 기본값(검은 글씨)이 된다.
        //   → 루트 div 에 직접 다시 박아준다. (2026-08-01 '복사하면 검은 글씨' 원인)
        var extra =
          '.shot-root{--bg:#0e0d14;--bg-soft:#171522;--bg-card:#1e1b2c;--line:#2e2a40;' +
          '--text:#f2f0f8;--text-muted:#9a94b0;--accent:#ff5c9e;--accent-2:#7b8cff;' +
          '--radius:18px;--safe-b:0px;' +
          'color:#f2f0f8;font-family:"Noto Sans KR",system-ui,sans-serif;font-size:16px;' +
          'width:' + W + 'px;background:#0e0d14;' +
          'background-image:radial-gradient(1100px 520px at 12% -12%,rgba(255,92,158,.16),transparent 60%),' +
          'radial-gradient(900px 480px at 88% 4%,rgba(123,140,255,.14),transparent 60%);}' +
          '.shot-foot{text-align:center;color:#6f6a85;font-size:.72rem;margin:18px 0 0;}' +
          '.screen{padding-bottom:22px;}' +
          // 어두운 배경에 묻히지 않게 글자색을 못 박는다(색 계산이 렌더러마다 달라질 여지 제거)
          '.champion .c-crown{color:#ffd76a;background:none;}' +
          '.tb-p.win,.tb-p.win b{color:#f2f0f8;}' +
          '.result-head h2{color:#ffffff;}';
        var body = new XMLSerializer().serializeToString(clone);
        document.body.removeChild(stage);

        var svg =
          '<svg xmlns="http://www.w3.org/2000/svg" width="' + W + '" height="' + H + '">' +
          '<foreignObject x="0" y="0" width="100%" height="100%">' +
          '<div xmlns="http://www.w3.org/1999/xhtml" class="shot-root">' +
          '<style>' + xmlEsc(css + extra) + '</style>' + body +
          '</div></foreignObject></svg>';

        return new Promise(function (res, rej) {
          var im = new Image();
          im.onload = function () {
            var S = 2;                     // 2배로 그려 글자를 또렷하게
            var cv = document.createElement('canvas');
            cv.width = W * S; cv.height = H * S;
            var g = cv.getContext('2d');
            g.fillStyle = '#0e0d14';
            g.fillRect(0, 0, cv.width, cv.height);
            g.drawImage(im, 0, 0, cv.width, cv.height);
            res(cv);
          };
          im.onerror = function () { rej(new Error('svg render failed')); };
          im.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
        });
      })
      .catch(function (e) {
        if (stage.parentNode) document.body.removeChild(stage);
        throw e;
      });
  }

  function xmlEsc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

  /** 결과 이미지 한 장. 화면 스냅샷을 먼저 시도하고, 안 되면 캔버스로 그린다. */
  function shot() {
    return buildDomCanvas().catch(function () { return withImages(); });
  }

  function toast(msg) {
    var t = $('toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.hidden = true; }, 2200);
  }

  function savePng() {
    shot().then(toBlob).then(function (blob) {
      var file = null;
      // 모바일에선 '다운로드'가 어디로 갔는지 모르는 경우가 많다 →
      // 공유 시트를 띄워 사진 앨범/앱으로 바로 보낼 수 있게 한다(지원할 때만).
      try { file = new File([blob], 'bangdream_sorter.png', { type: 'image/png' }); } catch (e) {}
      if (file && navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file] })
          .catch(function () { download(blob); });
        return;
      }
      download(blob);
    });

    function download(blob) {
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'bangdream_sorter.png';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
      toast('이미지를 저장했어요');
    }
  }

  function toBlob(cv) {
    return new Promise(function (res) { cv.toBlob(res, 'image/png'); });
  }

  /** 이미지 복사.
   *  ★ 사파리(iOS 포함)는 클릭 직후 '동기적으로' clipboard.write 를 불러야 허용한다.
   *    그래서 blob 을 기다렸다가 쓰지 않고, Promise<Blob> 을 그대로 ClipboardItem 에 넘긴다.
   *    (크롬도 Promise 를 받는다. 안 받는 구형 브라우저는 catch 로 예전 방식 폴백) */
  function copyPng() {
    if (!navigator.clipboard || !window.ClipboardItem) {
      toast('이 브라우저는 이미지 복사가 안 돼요. 저장을 써주세요');
      return;
    }
    var blobP = shot().then(toBlob);
    var done = function () { toast('이미지를 복사했어요'); };
    var fail = function () { toast('복사 실패 — 저장을 써주세요'); };
    try {
      navigator.clipboard.write([new ClipboardItem({ 'image/png': blobP })])
        .then(done).catch(fail);
    } catch (e) {
      blobP.then(function (blob) {
        return navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
      }).then(done).catch(fail);
    }
  }

  function copyText() {
    if (MODES[state.mode].cup) {
      var w = lastRows[0].ch;
      copyToClipboard('[뱅드림 캐릭터 월드컵 ' + cupTop(state.order.length) + '강]\n'
        + '우승 — ' + w.name + ' (' + w.band + ')'
        + '\n\nbandorigall.github.io/others.github.io/sorter/')
        .then(function () { toast('결과를 복사했어요'); })
        .catch(function () { toast('복사 실패'); });
      return;
    }
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

  // 마우스 없이 끝까지 갈 수 있게. 손 위치에 따라 화살표/숫자/AD 를 모두 받는다.
  var KEY = {
    left:  ['ArrowLeft', 'a', 'A', '1', 'ㅁ'],
    right: ['ArrowRight', 'd', 'D', '2', 'ㅇ'],
    tie:   [' ', 'ArrowDown', 's', 'S', '3', 'ㄴ'],
    undo:  ['z', 'Z', 'Backspace', 'ㅋ']
  };
  function keyIs(e, name) { return KEY[name].indexOf(e.key) >= 0; }

  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    // 시작 화면: 1/2/3 또는 Enter 로 모드 선택
    if (!screens.intro.hidden) {
      var modeKeys = { '1': 'cup', '2': 'full', 'Enter': 'cup' };
      var m = modeKeys[e.key];
      if (m) {
        var btn = document.querySelector('[data-mode="' + m + '"]');
        if (btn && !btn.disabled) { e.preventDefault(); startNew(m); }
      }
      return;
    }

    if (!screens.battle.hidden) {
      if (keyIs(e, 'left')) { e.preventDefault(); pick('left'); }
      else if (keyIs(e, 'right')) { e.preventDefault(); pick('right'); }
      else if (keyIs(e, 'tie')) {
        e.preventDefault();
        if (!MODES[state.mode].cup) answer(0);
      }
      else if (keyIs(e, 'undo')) { e.preventDefault(); undo(); }
      return;
    }

    // 결과 화면: S 저장 / C 텍스트 복사 / R 다시하기
    if (!screens.result.hidden) {
      if (e.key === 's' || e.key === 'S') { e.preventDefault(); savePng(); }
      else if (e.key === 'c' || e.key === 'C') { e.preventDefault(); copyText(); }
      else if (e.key === 'r' || e.key === 'R') { e.preventDefault(); $('btn-restart').click(); }
    }
  });

  // ── 초기화 ───────────────────────────────────────────────────────────
  $('intro-count').textContent = pickedChars().length + '명';
  $('btn-band-all').addEventListener('click', function () {
    BAND_ORDER.forEach(function (b) { picked[b] = true; });
    renderBands();
  });
  $('btn-band-none').addEventListener('click', function () {
    BAND_ORDER.forEach(function (b) { picked[b] = false; });
    renderBands();
  });
  $('btn-band-reset').addEventListener('click', function () {
    BAND_ORDER.forEach(function (b) { picked[b] = !isOptionalBand(b); });
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
