# -*- coding: utf-8 -*-
"""
out/*.png 를 세트로 통일한다. API 호출 없음 = 공짜.

  1) 팔레트 스냅   : 모든 픽셀을 흰/검/파/빨 4색 중 최근접으로 치환
                    -> 글로우, 그라디언트, 회색 배경, 형광 원색이 한 번에 제거됨
  2) 여백 정규화   : 내용 bounding box를 잡아 모든 장의 인물 크기/위치를 동일하게
  3) 슈퍼샘플링    : 2배로 키워 스냅 후 축소 -> 계단현상 없는 매끈한 벡터 느낌

    python normalize.py
    python normalize.py 02_shade_rest
결과: norm/<id>.png  (caption.py가 norm/을 우선으로 읽음)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "out"
DST = HERE / "norm"

# 채도를 낮춘 안전표지 신호색
PALETTE = {
    "white": (255, 255, 255),
    "black": (26, 26, 26),
    "blue":  (0, 87, 184),
    "red":   (200, 16, 46),
}
SHADE = (214, 222, 232)   # 그늘 면 (팔레트 스냅 이후에 칠하므로 색이 살아남는다)
SIZE = 1024
CONTENT = 0.80   # 캔버스 대비 내용이 차지할 비율


def snap(im):
    """각 픽셀을 팔레트 최근접색으로. 2배 슈퍼샘플 후 축소해 AA를 살린다."""
    im = im.convert("RGB").resize((SIZE * 2, SIZE * 2), Image.LANCZOS)
    # int32 필수: 제곱합이 최대 195075라 int16이면 오버플로로 색이 뒤집힌다
    a = np.asarray(im).astype(np.int32)
    cols = np.array(list(PALETTE.values()), dtype=np.int32)
    # (H,W,1,3) - (4,3) -> (H,W,4)
    d = ((a[:, :, None, :] - cols[None, None, :, :]) ** 2).sum(axis=3)
    idx = d.argmin(axis=2)
    out = cols[idx].astype(np.uint8)
    return Image.fromarray(out).resize((SIZE, SIZE), Image.LANCZOS)


def bg_is_dark(im):
    a = np.asarray(im.convert("L"))
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    return np.median(border) < 128


def renorm(im, shade=False):
    """흰색이 아닌 영역을 찾아 크기/위치를 통일. shade=True면 뒤에 그늘 면을 깐다."""
    a = np.asarray(im.convert("RGB")).astype(np.int32)
    mask = (np.abs(a - 255).sum(axis=2) > 40)
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return im
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    crop = im.crop(box)
    cw, ch = crop.size
    scale = (SIZE * CONTENT) / max(cw, ch)
    crop = crop.resize((max(1, int(cw * scale)), max(1, int(ch * scale))), Image.LANCZOS)
    canvas = Image.new("RGB", (SIZE, SIZE), "white")
    px = (SIZE - crop.size[0]) // 2
    py = (SIZE - crop.size[1]) // 2

    if shade:
        # 인물 뒤에 깔리는 연한 그늘 면. 우산을 그리는 대신 "그늘 안"임을 보여준다.
        from PIL import ImageDraw
        pad = int(SIZE * 0.05)
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle(
            [px - pad, py - pad, px + crop.size[0] + pad, py + crop.size[1] + pad],
            radius=int(SIZE * 0.06), fill=SHADE)
        # 흰 배경을 빼고 도형만 얹기
        ca = np.asarray(crop.convert("RGB")).astype(np.int32)
        m = Image.fromarray(((np.abs(ca - 255).sum(axis=2) > 40) * 255).astype(np.uint8))
        canvas.paste(crop, (px, py), m)
    else:
        canvas.paste(crop, (px, py))
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    args = ap.parse_args()

    spec = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
    allp = spec["panels"] + spec.get("kit", [])
    panels = [p for p in allp if not args.ids or p["id"] in args.ids]

    DST.mkdir(exist_ok=True)
    for p in panels:
        src = SRC / f"{p['id']}.png"
        if not src.exists():
            print(f"[skip] {src.name} 없음")
            continue
        im = Image.open(src)
        if bg_is_dark(im):
            print(f"[warn] {p['id']}: 배경이 어두움. 팔레트 스냅으로 살릴 수 없으니 재생성 필요")
            print(f"        python generate.py {p['id']}")
            continue
        out = DST / f"{p['id']}.png"
        renorm(snap(im), shade=p.get("shade", False)).save(out)
        print(f"[ok] {out}")


if __name__ == "__main__":
    main()
