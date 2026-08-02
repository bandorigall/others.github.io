# -*- coding: utf-8 -*-
"""
안내 4장 + 준비물 + 당일 기온예보를 한 장으로 합친다. 이미지 생성 API 미사용 = 공짜.

    python poster.py                 # 예보를 실시간으로 받아옴 (Open-Meteo, 무료·키 불필요)
    python poster.py --no-fetch      # 네트워크 없이, 아래 기본값으로
    python poster.py --tmax 35 --feels 41

결과: final/poster.png
예보는 공연이 가까워질수록 바뀌므로 올리기 직전에 다시 실행할 것.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FINAL = HERE / "final"
FONT = r"C:\Windows\Fonts\malgunbd.ttf"

EVENT_DATE = "2026-08-08"
EVENT_NAME = "김치쿠라26"
VENUE = "경희대학교 평화의 전당"
LAT, LON = 37.596, 127.052

INK = "#1a1a1a"
RED = "#c8102e"
MARGIN = 60
GAP = 40
PANELS = ["01_hydrate", "02_shade_rest", "03_warning_signs", "04_help_call"]


def fetch_forecast():
    import requests
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": LAT, "longitude": LON,
            "daily": "temperature_2m_max,apparent_temperature_max,precipitation_probability_max",
            "timezone": "Asia/Seoul",
            "start_date": EVENT_DATE, "end_date": EVENT_DATE,
        }, timeout=30)
    r.raise_for_status()
    d = r.json()["daily"]
    return d["temperature_2m_max"][0], d["apparent_temperature_max"][0], d["precipitation_probability_max"][0]


def font(size):
    return ImageFont.truetype(FONT, size)


def fit(draw, text, max_w, start):
    s = start
    while s > 10:
        f = font(s)
        if draw.textlength(text, font=f) <= max_w:
            return f
        s -= 2
    return font(10)


def centered(draw, text, f, cx, cy, fill):
    """(cx, cy)를 글자 중심으로 삼아 그린다."""
    bb = draw.textbbox((0, 0), text, font=f)
    w = draw.textlength(text, font=f)
    draw.text((cx - w / 2, cy - (bb[3] + bb[1]) / 2), text, font=f, fill=fill)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--tmax", type=float)
    ap.add_argument("--feels", type=float)
    ap.add_argument("--rain", type=int)
    args = ap.parse_args()

    tmax, feels, rain = args.tmax, args.feels, args.rain
    stamp = dt.date.today()
    if not args.no_fetch and tmax is None:
        try:
            tmax, feels, rain = fetch_forecast()
            print(f"[예보] 최고 {tmax}C / 체감 {feels}C / 강수 {rain}%")
        except Exception as e:
            print(f"[warn] 예보 수신 실패({e}) - --tmax/--feels 로 직접 넣으세요")
            return

    panels = []
    for pid in PANELS:
        p = FINAL / f"{pid}.png"
        if not p.exists():
            print(f"[err] {p.name} 없음. caption.py 먼저 실행")
            return
        panels.append(Image.open(p).convert("RGB"))
    kit_path = FINAL / "05_kit.png"
    kit = Image.open(kit_path).convert("RGB") if kit_path.exists() else None

    pw, ph = panels[0].size
    content_w = pw * 2 + GAP
    W = MARGIN * 2 + content_w

    title_h = 150
    date_h = 110
    weather_h = 260
    grid_h = ph * 2 + GAP
    kit_h = int(kit.size[1] * (content_w / kit.size[0])) if kit else 0
    note_h = 90
    H = (MARGIN + title_h + date_h + weather_h + GAP + grid_h
         + (GAP + kit_h if kit else 0) + note_h + MARGIN)

    cv = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(cv)
    y = MARGIN

    # 제목
    t = f"{EVENT_NAME} 폭염 안전 안내"
    d.rectangle([MARGIN, y, W - MARGIN, y + title_h], fill=INK)
    centered(d, t, fit(d, t, content_w * 0.9, int(title_h * 0.56)),
             W / 2, y + title_h / 2, "white")
    y += title_h

    # 날짜/장소
    sub = f"8월 8일(토) · {VENUE}"
    centered(d, sub, fit(d, sub, content_w * 0.9, int(date_h * 0.44)),
             W / 2, y + date_h / 2, INK)
    y += date_h

    # 기온 예보 (가장 크게)
    d.rectangle([MARGIN, y, W - MARGIN, y + weather_h], fill=RED)
    big = f"당일 예상 최고 {tmax:.0f}℃"
    centered(d, big, fit(d, big, content_w * 0.9, int(weather_h * 0.42)),
             W / 2, y + weather_h * 0.36, "white")
    small = f"체감 {feels:.0f}℃" + (f"  ·  강수확률 {rain}%" if rain is not None else "")
    centered(d, small, fit(d, small, content_w * 0.8, int(weather_h * 0.2)),
             W / 2, y + weather_h * 0.74, "white")
    y += weather_h + GAP

    # 안내 4장
    for i, im in enumerate(panels):
        cv.paste(im, (MARGIN + (i % 2) * (pw + GAP), y + (i // 2) * (ph + GAP)))
    y += grid_h

    # 준비물
    if kit:
        y += GAP
        cv.paste(kit.resize((content_w, kit_h), Image.LANCZOS), (MARGIN, y))
        y += kit_h

    # 출처/주의
    note = (f"기온은 Open-Meteo 예보({stamp.month}월 {stamp.day}일 기준)이며 "
            f"실제와 다를 수 있습니다  ·  응급상황 119")
    f = fit(d, note, content_w, int(note_h * 0.34))
    centered(d, note, f, W / 2, y + note_h / 2, "#777777")

    FINAL.mkdir(exist_ok=True)
    out = FINAL / "poster.png"
    cv.save(out)
    print(f"[ok] {out}  ({W}x{H})")


if __name__ == "__main__":
    main()
