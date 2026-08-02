# -*- coding: utf-8 -*-
"""
poster.png 를 웹용 경량 이미지로 내보낸다. (원본 2208x5196 / 670KB 는 모바일에 너무 무겁다)

    python webexport.py

  ../imgs/heat_poster.jpg  확대용 (폭 1000)
  ../imgs/heat_thumb.jpg   카드 썸네일용 (폭 420)
poster.py 를 다시 돌려 예보를 갱신했다면 이것도 다시 실행할 것.
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "final" / "poster.png"
IMGS = HERE.parent / "imgs"


def export(im, w, name, quality):
    h = round(im.size[1] * w / im.size[0])
    out = IMGS / name
    im.resize((w, h), Image.LANCZOS).convert("RGB").save(
        out, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"[ok] {out}  {w}x{h}  {out.stat().st_size // 1024}KB")


def main():
    if not SRC.exists():
        print("[err] final/poster.png 없음 - poster.py 먼저 실행")
        return
    IMGS.mkdir(exist_ok=True)
    im = Image.open(SRC)
    export(im, 1000, "heat_poster.jpg", 86)
    export(im, 420, "heat_thumb.jpg", 82)


if __name__ == "__main__":
    main()
