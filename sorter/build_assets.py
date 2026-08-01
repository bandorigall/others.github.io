# -*- coding: utf-8 -*-
"""소터용 캐릭터 자산 빌더.

레포 최상단 characters.json 을 읽어서
  - 초상 60장을 webp 로 변환·리사이즈  -> others/sorter/assets/<id>.webp
  - 소터가 바로 읽는 data.js          -> others/sorter/data.js

원본 초상은 크기·비율이 제각각이라, 얼굴이 위쪽에 오도록
가로 기준으로 맞춘 뒤 상단 정렬로 잘라 카드 비율(3:4)을 맞춘다.

사용법:  python build_assets.py
"""
import json
import os
import unicodedata

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MASTER = os.path.join(ROOT, "characters.json")
OUT_DIR = os.path.join(HERE, "assets")
OUT_DATA = os.path.join(HERE, "data.js")

CARD_W, CARD_H = 420, 560          # 대결 화면용 3:4 카드. 레티나에서도 버틸 정도만.
THUMB_W, THUMB_H = 132, 176        # 결과표용 썸네일(60장이 한 번에 뜨므로 따로 뽑는다)
QUALITY = 82
THUMB_QUALITY = 76


def romanize_id(ch):
    """파일명으로 쓸 안전한 id. 영문명이 있으면 그걸, 없으면 초상 파일명을 쓴다."""
    en = ch.get("nameEn")
    if en:
        return en.lower().replace(" ", "-").replace(".", "").replace("'", "")
    base = os.path.basename(ch["portrait"]).rsplit(".", 1)[0]
    return base


def fit_card(im, box_w, box_h):
    """가로를 지정 폭에 맞추고, 세로는 상단 정렬로 잘라 3:4 를 만든다.
    원본이 세로로 짧으면 아래를 투명으로 채운다(잘라내지 않음)."""
    im = im.convert("RGBA")
    w, h = im.size
    scale = box_w / w
    new_h = max(1, round(h * scale))
    im = im.resize((box_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    if new_h >= box_h:
        canvas.paste(im.crop((0, 0, box_w, box_h)), (0, 0))
    else:
        canvas.paste(im, (0, 0))
    return canvas


def main():
    data = json.load(open(MASTER, encoding="utf-8"))
    os.makedirs(OUT_DIR, exist_ok=True)

    out, total, total_th = [], 0, 0
    for ch in data["characters"]:
        cid = romanize_id(ch)
        src = os.path.join(ROOT, ch["portrait"].replace("/", os.sep))
        dst = os.path.join(OUT_DIR, cid + ".webp")
        dst_th = os.path.join(OUT_DIR, cid + "_t.webp")

        with Image.open(src) as im:
            fit_card(im, CARD_W, CARD_H).save(
                dst, "WEBP", quality=QUALITY, method=6)
            fit_card(im, THUMB_W, THUMB_H).save(
                dst_th, "WEBP", quality=THUMB_QUALITY, method=6)
        total += os.path.getsize(dst)
        total_th += os.path.getsize(dst_th)

        out.append({
            "id": cid,
            "name": ch["name"],
            "band": ch["bandName"],
            "bandKey": ch["band"],
            "color": ch["color"],
            "img": f"assets/{cid}.webp",
            "thumb": f"assets/{cid}_t.webp",
        })

    # 파일 하나로 묶어 fetch 없이 로드(file:// 로 열어도 동작)
    with open(OUT_DATA, "w", encoding="utf-8") as f:
        f.write("// 자동 생성 파일. 수정하지 말 것 (python build_assets.py 로 재생성)\n")
        f.write("window.SORTER_DATA = ")
        json.dump({"bands": data["bands"], "characters": out},
                  f, ensure_ascii=False, indent=1)
        f.write(";\n")

    print(f"[OK] {len(out)}명 / 카드 {total/1024:.0f}KB "
          f"(평균 {total/len(out)/1024:.1f}KB) + 썸네일 {total_th/1024:.0f}KB "
          f"(평균 {total_th/len(out)/1024:.1f}KB) -> {OUT_DIR}")
    print(f"[OK] {OUT_DATA}")


if __name__ == "__main__":
    raise SystemExit(main())
