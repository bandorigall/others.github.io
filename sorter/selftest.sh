#!/bin/bash
# ============================================================
#  selftest.sh — 소터 자동 점검 (헤드리스 크롬)
#  사용법: ./selftest.sh
#  하는 일:
#    1) 로컬 서버를 띄우고
#    2) ?autotest=cup|full 로 게임을 자동 완주시킨 뒤
#    3) 가로 넘침(scrollWidth > clientWidth) 이 없는지
#       결과 이미지(shot)가 PC/모바일에서 같은 크기로, 아래 여백 없이 나오는지 확인한다.
#    실패하면 빨간 FAIL 을 찍고 1 을 반환한다.
#  ※ 사람이 눈으로 볼 스크린샷도 남긴다(--shots 옵션).
# ============================================================
cd "$(dirname "$0")" || exit 1

CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
[ -x "$CHROME" ] || CHROME="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
[ -x "$CHROME" ] || { echo "크롬/엣지를 못 찾음"; exit 1; }

PORT=8791
python -m http.server $PORT >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
sleep 1

FAIL=0
ok()   { echo "  [OK]   $1"; }
bad()  { echo "  [FAIL] $1"; FAIL=1; }

# 페이지를 열고 <title> 을 읽어온다(진단 결과가 title 에 실려 나온다)
title() {
  "$CHROME" --headless=new --disable-gpu --virtual-time-budget=25000 \
    --window-size="$2","$3" --dump-dom "http://localhost:$PORT/index.html?$1" 2>/dev/null \
    | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g'
}

echo "[1] 가로 넘침 검사 (월드컵 결과)"
for W in 1280 700 485; do
  T=$(title "autotest=cup&diag=1" $W 900)
  VW=$(echo "$T" | sed -n 's/.*vw=\([0-9]*\).*/\1/p')
  SW=$(echo "$T" | sed -n 's/.*sw=\([0-9]*\).*/\1/p')
  if [ -n "$VW" ] && [ "$VW" = "$SW" ]; then ok "폭 $VW : 넘침 없음"
  else bad "폭 요청 $W → vw=$VW sw=$SW ($T)"; fi
done

echo "[2] 가로 넘침 검사 (전체 순위 결과)"
for W in 1280 485; do
  T=$(title "autotest=full&diag=1" $W 900)
  VW=$(echo "$T" | sed -n 's/.*vw=\([0-9]*\).*/\1/p')
  SW=$(echo "$T" | sed -n 's/.*sw=\([0-9]*\).*/\1/p')
  if [ -n "$VW" ] && [ "$VW" = "$SW" ]; then ok "폭 $VW : 넘침 없음"
  else bad "폭 요청 $W → vw=$VW sw=$SW"; fi
done

echo "[3] 결과 이미지(복사/저장용) 크기 — PC·모바일이 같아야 하고 아래 여백이 없어야 함"
PC=$(title "autotest=cup&shot=1" 1280 900 | sed 's/SHOT //')
MO=$(title "autotest=cup&shot=1" 485 900 | sed 's/SHOT //')
[ -n "$PC" ] && ok "PC   $PC"   || bad "PC 이미지 생성 실패"
[ -n "$MO" ] && ok "모바일 $MO" || bad "모바일 이미지 생성 실패"
[ "$PC" = "$MO" ] && ok "PC = 모바일 (폭 1080 고정 동작)" \
  || bad "PC($PC) 와 모바일($MO) 이 다름 → 아래 여백이 생긴다"
H=$(echo "$PC" | sed 's/.*x//')
[ -n "$H" ] && [ "$H" -lt 2000 ] && ok "높이 $H (여백 없음)" \
  || bad "높이 $H — 내용에 비해 너무 김(빈 공간 의심)"

echo "[4] 결과 이미지 글자색 — 검은 글씨로 떨어지지 않았는지"
T=$(title "autotest=cup&shot=1&colorcheck=1" 1280 900)
case "$T" in
  *TEXTOK*) ok "흰 글씨 확인" ;;
  *)        bad "글자색 검사 실패 ($T)" ;;
esac

if [ -n "$1" ] && [ "$1" = "--shots" ]; then
  echo "[5] 스크린샷 저장 (_shots/)"
  mkdir -p _shots
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=25000 \
    --window-size=1280,2200 --screenshot="_shots/pc_result.png" \
    "http://localhost:$PORT/index.html?autotest=cup" 2>/dev/null
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=25000 \
    --window-size=485,2600 --screenshot="_shots/mobile_result.png" \
    "http://localhost:$PORT/index.html?autotest=cup" 2>/dev/null
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=25000 \
    --window-size=1280,1600 --screenshot="_shots/copied_image.png" \
    "http://localhost:$PORT/index.html?autotest=cup&shot=1" 2>/dev/null
  echo "  _shots/ 에 저장됨"
fi

echo
[ $FAIL -eq 0 ] && echo "===== 전부 통과 =====" || echo "===== 실패 있음 ====="
exit $FAIL
