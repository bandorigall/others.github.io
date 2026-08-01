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
    mode: 'full',
    order: [],                   // 시작 명단(무작위로 섞음)
    answers: [],                 // [[idA, idB, v], ...]  v: 1=A선호, -1=B선호, 0=비김
    map: {},                     // "idA|idB" -> v
    eqLink: {},                  // 비김으로 묶인 쌍 (idA -> idB)
    pending: null,               // 지금 화면에 띄운 [idA, idB]
    swapped: false,              // 화면에서 좌우를 뒤집어 보여주는 중인지
    result: null                 // 완료 시 정렬된 id 배열
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
          if (nm) nm.innerHTML = '전체 ' + n + '위<em>추천</em>';
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

    function play(a, b) {
      round.no++;
      NEED.round = {
        size: round.size, no: round.no, total: round.total, prelim: round.prelim
      };
      return compare(a, b) >= 0 ? a : b;   // 월드컵엔 비김이 없다(0이면 앞쪽 승)
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
    return { done: true, list: cur };
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
    state.mode = MODES[mode] ? mode : 'full';
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
    $('champion').hidden = !cup;
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

  /** 월드컵 결과 이미지 — 우승자 한 명만 크게. */
  function buildCupCanvas() {
    var ch = lastRows[0].ch;
    var W = 1080, H = 1080;
    var cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    var g = cv.getContext('2d');

    var bg = g.createLinearGradient(0, 0, W, H);
    bg.addColorStop(0, '#15121f');
    bg.addColorStop(.5, '#0e0d14');
    bg.addColorStop(1, '#1a1428');
    g.fillStyle = bg; g.fillRect(0, 0, W, H);

    var glow = g.createRadialGradient(W / 2, 470, 0, W / 2, 470, 520);
    glow.addColorStop(0, hexA(ch.color, .34));
    glow.addColorStop(1, hexA(ch.color, 0));
    g.fillStyle = glow; g.fillRect(0, 0, W, H);

    g.textAlign = 'center';
    g.fillStyle = '#9a94b0';
    g.font = '700 26px "Noto Sans KR", sans-serif';
    g.fillText('뱅드림 캐릭터 월드컵 · ' + cupTop(state.order.length) + '강', W / 2, 80);

    g.fillStyle = '#ffd76a';
    g.font = '900 44px "Noto Sans KR", sans-serif';
    g.fillText('우승', W / 2, 148);

    var im = ch._im;
    if (im) {
      var S = 560, x = (W - S) / 2, y = 195;
      g.save();
      roundRect(g, x, y, S, S, 28);
      g.fillStyle = 'rgba(255,255,255,.06)';
      g.fill();
      g.strokeStyle = ch.color; g.lineWidth = 5; g.stroke();
      g.clip();
      g.drawImage(im, x, y, S, S);
      g.restore();
    }

    g.fillStyle = '#ffffff';
    g.font = '900 62px "Noto Sans KR", sans-serif';
    g.fillText(ch.name, W / 2, 848);
    g.fillStyle = ch.color;
    g.font = '700 30px "Noto Sans KR", sans-serif';
    g.fillText(ch.band, W / 2, 898);

    var d = new Date();
    g.fillStyle = '#8b85a3';
    g.font = '500 22px "Noto Sans KR", sans-serif';
    g.fillText(d.getFullYear() + '.' + pad(d.getMonth() + 1) + '.' + pad(d.getDate())
      + ' · ' + state.order.length + '명 · ' + state.answers.length + '경기', W / 2, 968);

    g.fillStyle = '#6f6a85';
    g.font = '500 19px "Noto Sans KR", sans-serif';
    g.fillText('뱅드림 캐릭터 소터 · bandorigall.github.io/others.github.io/sorter/',
      W / 2, H - 38);
    return cv;
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
    return Promise.all(lastRows.map(function (r) {
      if (r.ch._im && r.ch._imBig === big) return Promise.resolve();
      return new Promise(function (res) {
        var im = new Image();
        im.onload = function () { r.ch._im = im; r.ch._imBig = big; res(); };
        im.onerror = function () { res(); };   // 한 장 실패해도 나머지는 그린다
        im.src = big ? r.ch.img : r.ch.thumb;
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
      var modeKeys = { '1': 'cup', '2': 'full', 'Enter': 'full' };
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
