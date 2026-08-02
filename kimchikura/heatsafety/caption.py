# -*- coding: utf-8 -*-
"""
out/*.png 픽토그램 아래에 한글 캡션을 얹어 final/*.png 로 저장.
API 호출 없음 = 공짜. 문구 수정은 prompts.json의 "ko" 값만 고치고 다시 실행.

    python caption.py              # 전체
    python caption.py 03_warning_signs
    python caption.py --sheet      # 4장을 2x2 한 장으로 합친 시트도 생성
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
NORM = HERE / "norm"     # normalize.py 결과가 있으면 이쪽을 우선 사용
RAW = HERE / "out"
DST = HERE / "final"
FONT = r"C:\Windows\Fonts\malgunbd.ttf"

BAR_RATIO = 0.18   # 캡션 띠 높이 (이미지 폭 대비)
PAD = 0.08


def caption_one(img_path, text, accent):
    """그림 아래에 accent 색 통띠를 깔고 흰 글씨를 얹는다(표지판 느낌)."""
    im = Image.open(img_path).convert("RGB")
    w, h = im.size
    bar = int(w * BAR_RATIO)
    canvas = Image.new("RGB", (w, h + bar), "white")
    canvas.paste(im, (0, 0))
    d = ImageDraw.Draw(canvas)

    d.rectangle([0, h, w, h + bar], fill=accent)

    size = int(bar * 0.46)
    max_w = w * (1 - PAD * 2)
    while size > 10:
        f = ImageFont.truetype(FONT, size)
        if d.textlength(text, font=f) <= max_w:
            break
        size -= 2
    f = ImageFont.truetype(FONT, size)

    tw = d.textlength(text, font=f)
    box = d.textbbox((0, 0), text, font=f)
    th = box[3] - box[1]
    d.text(((w - tw) / 2, h + (bar - th) / 2 - box[1]), text, font=f, fill="white")
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--sheet", action="store_true", help="2x2 통합 시트도 생성")
    args = ap.parse_args()

    spec = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
    panels = spec["panels"]
    if args.ids:
        panels = [p for p in panels if p["id"] in args.ids]

    DST.mkdir(exist_ok=True)
    made = []
    for p in panels:
        src = NORM / f"{p['id']}.png"
        if not src.exists():
            src = RAW / f"{p['id']}.png"
        if not src.exists():
            print(f"[skip] {p['id']} 없음 - generate.py 먼저 실행")
            continue
        accent = p.get("accent", "#c8102e" if "warning" in p["id"] or "help" in p["id"] else "#1a1a1a")
        out = DST / f"{p['id']}.png"
        caption_one(src, p["ko"], accent).save(out)
        made.append(out)
        print(f"[ok] {out}")

    if args.sheet and len(made) == 4:
        ims = [Image.open(m) for m in made]
        cw, ch = ims[0].size
        g = int(cw * 0.03)
        sheet = Image.new("RGB", (cw * 2 + g * 3, ch * 2 + g * 3), "white")
        for i, im in enumerate(ims):
            x = g + (i % 2) * (cw + g)
            y = g + (i // 2) * (ch + g)
            sheet.paste(im.resize((cw, ch)), (x, y))
        sheet.save(DST / "sheet.png")
        print(f"[ok] {DST / 'sheet.png'}")


if __name__ == "__main__":
    main()
