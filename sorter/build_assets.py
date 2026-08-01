# -*- coding: utf-8 -*-
"""소터용 캐릭터 자산 빌더 (얼굴 기준 상반신 크롭).

레포 최상단 characters.json 을 읽어서
  - 초상 60장을 '머리 전체 + 어깨' 로 크롭 -> assets/<id>.webp, <id>_t.webp
  - 소터가 바로 읽는 data.js

[크롭 방식]
  1) lbpcascade_animeface 로 얼굴 상자를 찾는다(애니 얼굴 전용 캐스케이드).
  2) 얼굴 상자를 기준으로 위로는 머리카락 끝까지, 아래로는 어깨까지 잡는다.
     - 위: 얼굴 높이의 1.15배 (트윈테일·리본 등 큰 머리 대비)
     - 아래: 얼굴 높이의 1.45배 (턱 아래 목+어깨)
     - 좌우: 얼굴 폭의 2.5배 (어깨 너비)
  3) 잡은 상자를 알파(내용물) 범위 안으로 밀어넣고, 위쪽은 머리카락이
     잘리지 않도록 알파 상단을 넘어서면 알파 상단에 맞춘다.
  4) 얼굴을 못 찾으면 알파 폭 프로파일로 어깨선을 추정하는 폴백을 쓴다.

사용법:  python build_assets.py [--check]
   --check 를 주면 크롭 결과를 한 장의 대조 시트(_crop_check.png)로 저장한다.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MASTER = os.path.join(ROOT, "characters.json")
OUT_DIR = os.path.join(HERE, "assets")
OUT_DATA = os.path.join(HERE, "data.js")
CASCADE = os.path.join(HERE, "animeface.xml")

# 상반신이므로 정사각에 가깝게. 카드가 작아져 용량도 크게 준다.
CARD = 320          # 대결 화면용 (1:1)
THUMB = 112         # 결과표 썸네일
QUALITY = 78
THUMB_QUALITY = 72

# 얼굴 상자 대비 크롭 배율 (얼굴 높이 fh 기준)
#   정사각 한 변 = fh * ZOOM, 얼굴 상단에서 위로 fh * UP 만큼이 머리 공간.
#   ZOOM 을 키우면 멀어지고, UP 을 키우면 머리가 더 들어온다.
ZOOM = 2.70         # 머리 전체 + 어깨가 딱 들어오는 배율
UP = 0.95           # 얼굴 위(머리카락·리본)


def alpha_bbox(arr_a, thr=8):
    ys, xs = np.where(arr_a > thr)
    if not len(ys):
        return None
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def detect_face(rgb, cascade):
    """가장 위쪽에 있는 큰 얼굴을 고른다(전신 이미지에서 얼굴은 위에 있음).
    한 번에 못 찾는 그림이 꽤 있어서 조건을 완화해가며 여러 번 시도한다."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)
    h = gray.shape[0]

    # (scaleFactor, minNeighbors, minSize비율) 을 점점 느슨하게
    ladder = [
        (1.05, 4, 40), (1.03, 3, 50), (1.02, 2, 60), (1.01, 1, 80),
    ]
    for sf, mn, div in ladder:
        faces = cascade.detectMultiScale(
            gray, scaleFactor=sf, minNeighbors=mn,
            minSize=(max(16, h // div), max(16, h // div)))
        if len(faces):
            # 위쪽 + 큰 것 우선
            faces = sorted(faces, key=lambda f: (f[1] - f[3] * 0.6))
            return tuple(int(v) for v in faces[0])
    return None


def shoulder_fallback(a, box):
    """얼굴 검출 실패용. 알파 폭이 급격히 넓어지는 지점을 어깨로 본다."""
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1] > 8
    widths = sub.sum(axis=1)
    if not len(widths):
        return None
    h = len(widths)
    head_zone = widths[: max(1, int(h * 0.18))]
    head_w = max(1, int(np.median(head_zone[head_zone > 0])) if (head_zone > 0).any() else 1)

    shoulder = None
    for i in range(int(h * 0.10), int(h * 0.60)):
        if widths[i] > head_w * 1.7:
            shoulder = i
            break
    if shoulder is None:
        shoulder = int(h * 0.34)          # 흉상 이미지 등 — 위쪽 1/3 사용

    top = y0
    bottom = y0 + min(h, int(shoulder * 1.35))
    side_w = max(widths[: bottom - y0].max(), 1)
    cx = x0 + int(np.argmax(widths[: bottom - y0] == widths[: bottom - y0].max()) * 0) + (x1 - x0) // 2
    half = int(max(bottom - top, side_w) * 0.62)
    return (cx - half, top, cx + half, bottom)


def crop_box(im, cascade):
    """(left, top, right, bottom) 반환. 실패하면 None."""
    rgba = im.convert("RGBA")
    a = np.array(rgba)[:, :, 3]
    bb = alpha_bbox(a)
    if bb is None:
        return None, "빈이미지"
    x0, y0, x1, y1 = bb

    # 얼굴 검출은 알파 영역만, 흰 배경 위에 합성해서 (투명부 잡음 제거)
    sub = rgba.crop(bb)
    bgw = Image.new("RGBA", sub.size, (255, 255, 255, 255))
    bgw.alpha_composite(sub)
    rgb = np.array(bgw.convert("RGB"))

    f = detect_face(rgb, cascade)
    if f is None:
        box = shoulder_fallback(a, bb)
        return box, "폴백"

    fx, fy, fw, fh = f
    fx += x0
    fy += y0                              # 원본 좌표계로
    cx = fx + fw / 2

    # 얼굴 높이에 비례한 정사각. 위쪽 여백(UP)만 지정하면 나머지는 따라온다.
    side = fh * ZOOM
    top = fy - fh * UP
    box = [cx - side / 2, top, cx + side / 2, top + side]

    # 머리카락이 잘리는 게 최악이므로, 위가 알파 상단보다 아래면 위로 끌어올린다
    if box[1] > y0 - 2:
        shift = box[1] - max(0, y0 - 2)
        box[1] -= shift
        box[3] -= shift
    return tuple(int(round(v)) for v in box), "얼굴"


def render(im, box, size, quality, dst):
    """투명 배경을 유지한 채 정사각으로 크롭·리사이즈해서 저장."""
    rgba = im.convert("RGBA")
    l, t, r, b = box
    side = max(r - l, b - t)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    # 원본 범위를 벗어나는 부분은 투명으로 남는다(패딩)
    src_l, src_t = max(0, l), max(0, t)
    src_r, src_b = min(rgba.width, l + side), min(rgba.height, t + side)
    if src_r <= src_l or src_b <= src_t:
        return False
    piece = rgba.crop((src_l, src_t, src_r, src_b))
    canvas.paste(piece, (src_l - l, src_t - t))
    canvas.resize((size, size), Image.LANCZOS).save(
        dst, "WEBP", quality=quality, method=6)
    return True


def romanize_id(ch):
    en = ch.get("nameEn")
    if en:
        return en.lower().replace(" ", "-").replace(".", "").replace("'", "")
    return os.path.basename(ch["portrait"]).rsplit(".", 1)[0]


def main():
    check = "--check" in sys.argv
    # OpenCV 는 경로에 한글이 있으면 파일을 못 연다.
    # 레포 경로가 한글이므로 ASCII 임시 경로로 복사해서 로드한다.
    import shutil
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "lbpcascade_animeface.xml")
    shutil.copyfile(CASCADE, tmp)
    cascade = cv2.CascadeClassifier(tmp)
    if cascade.empty():
        print("[!] animeface.xml 을 못 읽었습니다.")
        return 1

    data = json.load(open(MASTER, encoding="utf-8"))
    os.makedirs(OUT_DIR, exist_ok=True)

    out, total, total_th, fallbacks = [], 0, 0, []
    sheet = []

    for ch in data["characters"]:
        cid = romanize_id(ch)
        src = os.path.join(ROOT, ch["portrait"].replace("/", os.sep))
        dst = os.path.join(OUT_DIR, cid + ".webp")
        dst_th = os.path.join(OUT_DIR, cid + "_t.webp")

        with Image.open(src) as im:
            box, how = crop_box(im, cascade)
            if box is None:
                print(f"[!] {ch['name']}: 크롭 실패 — 원본 그대로 사용")
                w, h = im.size
                box = (0, 0, w, min(h, w))
                how = "실패"
            if how != "얼굴":
                fallbacks.append(f"{ch['name']}({how})")
            render(im, box, CARD, QUALITY, dst)
            render(im, box, THUMB, THUMB_QUALITY, dst_th)
            if check:
                sheet.append((ch["name"], Image.open(dst).convert("RGBA")))

        total += os.path.getsize(dst)
        total_th += os.path.getsize(dst_th)
        out.append({
            "id": cid, "name": ch["name"], "band": ch["bandName"],
            "bandKey": ch["band"], "color": ch["color"],
            "img": f"assets/{cid}.webp", "thumb": f"assets/{cid}_t.webp",
        })

    with open(OUT_DATA, "w", encoding="utf-8") as f:
        f.write("// 자동 생성 파일. 수정하지 말 것 (python build_assets.py 로 재생성)\n")
        f.write("window.SORTER_DATA = ")
        json.dump({"bands": data["bands"], "characters": out},
                  f, ensure_ascii=False, indent=1)
        f.write(";\n")

    n = len(out)
    print(f"[OK] {n}명 / 카드 {total/1024:.0f}KB (평균 {total/n/1024:.1f}KB)"
          f" + 썸네일 {total_th/1024:.0f}KB (평균 {total_th/n/1024:.1f}KB)")
    print(f"[OK] {OUT_DATA}")
    if fallbacks:
        print(f"[i] 얼굴 검출 실패 {len(fallbacks)}명 (폭 프로파일로 대체): "
              + ", ".join(fallbacks))

    if check and sheet:
        cols = 10
        rows = (len(sheet) + cols - 1) // cols
        cell = CARD // 2
        sh = Image.new("RGB", (cols * cell, rows * cell), (24, 22, 34))
        for i, (_, img) in enumerate(sheet):
            img = img.resize((cell, cell), Image.LANCZOS)
            bgc = Image.new("RGBA", img.size, (24, 22, 34, 255))
            bgc.alpha_composite(img)
            sh.paste(bgc.convert("RGB"), ((i % cols) * cell, (i // cols) * cell))
        p = os.path.join(HERE, "_crop_check.png")
        sh.save(p)
        print(f"[OK] 대조 시트 -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
