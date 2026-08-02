/* lightbox.js — 이미지 링크를 오버레이로 확대해서 보여준다.
   대상: <a data-lightbox href="큰이미지.jpg"><img src="썸네일"></a>
   JS가 죽어도 링크 그대로 이미지가 열리므로 기능이 사라지지 않는다. */
(function () {
  'use strict';

  var overlay = null;
  var lastFocus = null;

  function close() {
    if (!overlay) return;
    overlay.remove();
    overlay = null;
    document.body.style.overflow = '';
    document.body.classList.remove('lb-open');
    if (lastFocus) lastFocus.focus();
  }

  function open(src, alt) {
    close();
    lastFocus = document.activeElement;

    overlay = document.createElement('div');
    overlay.className = 'lb-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', alt || '이미지 확대');

    var img = document.createElement('img');
    img.src = src;
    img.alt = alt || '';

    var btn = document.createElement('button');
    btn.className = 'lb-close';
    btn.type = 'button';
    btn.setAttribute('aria-label', '닫기');
    btn.textContent = '×';
    btn.addEventListener('click', close);

    // 배경(이미지 바깥)을 눌렀을 때만 닫는다
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) close();
    });

    overlay.appendChild(img);
    overlay.appendChild(btn);
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';   // 뒤 페이지가 같이 스크롤되지 않게
    // nav.js의 떠 있는 메뉴 버튼이 z-index 최대값이라 오버레이를 뚫고 나온다. 열려 있는 동안 숨긴다.
    document.body.classList.add('lb-open');
    btn.focus();
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[data-lightbox]') : null;
    if (!a) return;
    // 새 탭으로 열려는 조작은 그대로 둔다
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    var inner = a.querySelector('img');
    open(a.getAttribute('href'), inner ? inner.alt : a.getAttribute('aria-label'));
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
  });
})();
