# -*- coding: utf-8 -*-
"""
게시 직전에 이것 하나만 실행하면 된다. 이미지 생성 API 미사용 = 공짜.

  1) poster.py     최신 예보를 받아 통합 포스터 재생성
  2) webexport.py  웹용 경량 이미지 재출력
  3) index.html    카드에 박힌 기온 숫자·기준일을 같은 값으로 갱신

    python update.py

이미지와 HTML의 숫자가 어긋나는 것을 막는 것이 이 스크립트의 존재 이유다.
그림 자체를 바꾸려면 generate.py(과금) -> normalize.py -> caption.py/kit.py 를 먼저 돌릴 것.
"""
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
INDEX = HERE.parent / "index.html"


def run(script):
    print(f"--- {script} ---")
    r = subprocess.run([sys.executable, str(HERE / script)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout or "").strip())
    if r.returncode != 0:
        print((r.stderr or "").strip())
        sys.exit(f"[err] {script} 실패")


def patch_html(tmax, feels, rain):
    html = INDEX.read_text(encoding="utf-8")
    today = dt.date.today()
    before = html

    html = re.sub(r'(<span class="heat-temp-num">)\d+(</span>)',
                  rf'\g<1>{tmax:.0f}\g<2>', html)
    html = re.sub(r'(<span class="heat-temp-sub">)[^<]*(</span>)',
                  rf'\g<1>체감 {feels:.0f}℃ · 강수확률 {rain}%\g<2>', html)
    html = re.sub(r'※ 기온은 \d+월 \d+일 기준 예보이며',
                  f'※ 기온은 {today.month}월 {today.day}일 기준 예보이며', html)

    if html == before:
        print("[i] index.html 변경 없음 (숫자가 이미 최신이거나 마크업이 바뀜)")
    else:
        INDEX.write_text(html, encoding="utf-8")
        print(f"[ok] index.html 갱신: 최고 {tmax:.0f}℃ / 체감 {feels:.0f}℃ / 강수 {rain}%")


def main():
    sys.path.insert(0, str(HERE))
    import poster

    try:
        tmax, feels, rain = poster.fetch_forecast()
    except Exception as e:
        sys.exit(f"[err] 예보 수신 실패: {e}")
    print(f"[예보] 최고 {tmax}℃ / 체감 {feels}℃ / 강수 {rain}%")

    run("poster.py")
    run("webexport.py")
    patch_html(tmax, feels, rain)
    print("\n완료. 변경사항을 커밋·푸시하세요.")


if __name__ == "__main__":
    main()
