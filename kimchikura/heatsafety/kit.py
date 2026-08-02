# -*- coding: utf-8 -*-
"""
준비물 아이콘 6종을 3x2 격자 + 한글 라벨로 조립. API 호출 없음 = 공짜.

    python kit.py
결과: final/05_kit.png

라벨/구성 수정은 prompts.json의 "kit" 배열만 고치고 다시 실행하면 된다.
아이콘 자체를 바꿀 때만 generate.py 재호출(=과금)이 필요하다.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
NORM = HERE / "norm"
RAW = HERE / "out"
DST = HERE / "final"
FONT = r"C:\Windows\Fonts\malgunbd.ttf"

COLS, ROWS = 3, 2
CELL = 420          # 아이콘 한 칸
LABEL = 90          # 라벨 높이
GAP = 40
MARGIN = 60
TITLE_H = 170
INK = "#1a1a1a"


def find(pid):
    for base in (NORM, RAW):
        p = base / f"{pid}.png"
        if p.exists():
            return p
    return None


def fit_font(draw, text, max_w, start):
    size = start
    while size > 10:
        f = ImageFont.truetype(FONT, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(FONT, 10)


def main():
    spec = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
    items = spec["kit"]

    W = MARGIN * 2 + CELL * COLS + GAP * (COLS - 1)
    H = MARGIN * 2 + TITLE_H + (CELL + LABEL) * ROWS + GAP * (ROWS - 1)
    canvas = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(canvas)

    # 제목 띠
    d.rectangle([0, 0, W, TITLE_H], fill=INK)
    title = spec.get("kit_title", "준비물")
    tf = fit_font(d, title, W - MARGIN * 2, int(TITLE_H * 0.52))
    bb = d.textbbox((0, 0), title, font=tf)
    d.text(((W - d.textlength(title, font=tf)) / 2,
            (TITLE_H - (bb[3] - bb[1])) / 2 - bb[1]), title, font=tf, fill="white")

    missing = []
    for i, it in enumerate(items[:COLS * ROWS]):
        cx = MARGIN + (i % COLS) * (CELL + GAP)
        cy = MARGIN + TITLE_H + (i // COLS) * (CELL + LABEL + GAP)

        src = find(it["id"])
        if src is None:
            missing.append(it["id"])
            d.rectangle([cx, cy, cx + CELL, cy + CELL], outline="#cccccc", width=3)
        else:
            icon = Image.open(src).convert("RGB").resize((CELL, CELL), Image.LANCZOS)
            canvas.paste(icon, (cx, cy))

        lf = fit_font(d, it["ko"], CELL * 0.94, int(LABEL * 0.52))
        bb = d.textbbox((0, 0), it["ko"], font=lf)
        d.text((cx + (CELL - d.textlength(it["ko"], font=lf)) / 2,
                cy + CELL + (LABEL - (bb[3] - bb[1])) / 2 - bb[1]),
               it["ko"], font=lf, fill=INK)

    DST.mkdir(exist_ok=True)
    out = DST / "05_kit.png"
    canvas.save(out)
    if missing:
        print(f"[warn] 아직 없는 아이콘(빈칸으로 표시): {', '.join(missing)}")
        print("       python generate.py " + " ".join(missing))
    print(f"[ok] {out}")


if __name__ == "__main__":
    main()
