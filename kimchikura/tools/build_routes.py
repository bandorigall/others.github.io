# -*- coding: utf-8 -*-
"""
build_routes.py — 실제 대중교통 소요시간 행렬을 만들어 data/routes.json 에 굽는다.

왜 빌드 시점인가:
  네이버 지도 대중교통 경로 API(map.naver.com/p/api/directions/pubtrans)는
  CORS 헤더를 주지 않아 GitHub Pages 에서 브라우저가 직접 호출할 수 없다.
  대신 노드 수가 아주 적으므로(출발지 4 + 당일 이벤트 장소 N + 공연장 1)
  모든 방향 쌍을 미리 조회해 JSON 으로 저장하고, 페이지는 그 행렬만 읽는다.

사용법:
  python tools/build_routes.py            # events.csv 자동 탐색
  python tools/build_routes.py --csv <경로>
  python tools/build_routes.py --time 09:00
"""

import argparse
import csv
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
OUT = os.path.join(SITE, "data", "routes.json")

FES_DATE = "2026-08-08"
DEFAULT_TIME = "09:00"

GOAL = {"id": "goal", "name": "경희대학교 평화의전당", "place": "경희대학교 평화의전당",
        "lat": 37.59880038087925, "lng": 127.05265593715515}

ORIGINS = [
    {"id": "o_seoul",    "name": "서울역",          "lat": 37.554648, "lng": 126.970750},
    {"id": "o_yongsan",  "name": "용산역",          "lat": 37.529849, "lng": 126.964561},
    {"id": "o_nambu",    "name": "남부버스터미널",   "lat": 37.484928, "lng": 127.016319},
    {"id": "o_dongseoul","name": "동서울버스터미널", "lat": 37.534605, "lng": 127.094889},
]

API = "https://map.naver.com/p/api/directions/pubtrans"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 기본 CSV 후보 경로 (홈피 폴더 구조 기준)
CSV_CANDIDATES = [
    os.path.join(SITE, "..", "..", "한국오프이벤", "events.csv"),
]


def http_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": "https://map.naver.com/",
        "Accept": "application/json",
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


def query_route(a, b, dep):
    """a → b 대중교통 경로. 실패하면 None."""
    q = urllib.parse.urlencode({
        "start": "%s,%s" % (a["lng"], a["lat"]),
        "goal":  "%s,%s" % (b["lng"], b["lat"]),
        "departureTime": dep,
    })
    try:
        d = http_json(API + "?" + q)
    except Exception as e:                      # 네트워크/차단
        print("    ! %s → %s 실패: %s" % (a["name"], b["name"], e))
        return None

    paths = d.get("paths") or []
    if not paths:
        print("    ! %s → %s 경로 없음(status=%s)" % (a["name"], b["name"], d.get("status")))
        return None

    # duration(분) 최소 경로 선택
    best = min(paths, key=lambda p: p.get("duration") or 10 ** 9)
    return {
        "duration": best.get("duration"),
        "walk": best.get("walkingDuration"),
        "fare": best.get("fare"),
        "type": best.get("type"),
        "summary": summarize(best),
    }


def summarize(path):
    """'1호선 → 동대문01' 처럼 이용 노선 요약."""
    names, seen = [], set()
    for fare in path.get("fares") or []:
        for group in fare.get("routes") or []:
            if not group:
                continue
            nm = (group[0] or {}).get("name")
            if nm and nm not in seen:
                seen.add(nm)
                names.append(nm)
    return " → ".join(names)


# ---------- events.csv 에서 당일 활성 장소 뽑기 ----------
def parse_coord_cell(cell):
    cell = (cell or "").strip()
    if not cell:
        return []
    raw = json.loads(cell) if cell[0] == "[" else [cell]
    out = []
    for s in raw:
        parts = str(s).split(",")
        try:
            out.append((float(parts[0]), float(parts[1])))
        except (ValueError, IndexError):
            pass
    return out


def parse_place_cell(cell):
    cell = (cell or "").strip()
    if not cell:
        return []
    if cell[0] == "[":
        try:
            return json.loads(cell)
        except ValueError:
            pass
    return [s.strip() for s in cell.split(",") if s.strip()]


def load_stops(csv_path, date):
    stops = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            s, e = (row.get("시작기간") or "").strip(), (row.get("종료기간") or "").strip()
            if not (s <= date <= e):
                continue
            title = (row.get("이벤트명") or "").strip()
            coords = parse_coord_cell(row.get("좌표"))
            places = parse_place_cell(row.get("장소"))
            for i, (la, ln) in enumerate(coords):
                # 공연장 자체는 목적지이므로 제외 (대략 300m 이내)
                if abs(la - GOAL["lat"]) < 0.003 and abs(ln - GOAL["lng"]) < 0.004:
                    continue
                place = places[i] if i < len(places) else (places[0] if places else title)
                stops.append({
                    "id": "s%d_%d" % (len(stops), i),
                    "name": place, "place": place, "title": title,
                    "lat": la, "lng": ln,
                    "link": (row.get("통합정보모음") or "").strip(),
                })
    return stops


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None)
    ap.add_argument("--date", default=FES_DATE)
    ap.add_argument("--time", default=DEFAULT_TIME)
    ap.add_argument("--sleep", type=float, default=0.7, help="요청 간 대기(초)")
    args = ap.parse_args()

    csv_path = args.csv
    if not csv_path:
        for c in CSV_CANDIDATES:
            if os.path.exists(c):
                csv_path = c
                break
    if not csv_path or not os.path.exists(csv_path):
        sys.exit("events.csv 를 찾지 못했습니다. --csv 로 지정하세요.")

    stops = load_stops(csv_path, args.date)
    print("[+] %s 활성 장소 %d곳" % (args.date, len(stops)))
    for s in stops:
        print("    - %s (%s)" % (s["place"], s["title"]))

    nodes = ORIGINS + stops + [GOAL]
    by_id = {n["id"]: n for n in nodes}
    dep = "%sT%s:00" % (args.date, args.time)

    # 필요한 방향 쌍만 조회: 출발지→(장소|공연장), 장소→(다른 장소|공연장)
    pairs = []
    for o in ORIGINS:
        for s in stops:
            pairs.append((o["id"], s["id"]))
        pairs.append((o["id"], GOAL["id"]))
    for a in stops:
        for b in stops:
            if a["id"] != b["id"]:
                pairs.append((a["id"], b["id"]))
        pairs.append((a["id"], GOAL["id"]))

    print("[+] 경로 조회 %d건 (출발 %s)" % (len(pairs), dep))
    matrix, fails = {}, 0
    for i, (a, b) in enumerate(pairs, 1):
        r = query_route(by_id[a], by_id[b], dep)
        if r is None:
            fails += 1
        else:
            matrix["%s>%s" % (a, b)] = r
            print("    [%d/%d] %s → %s : %d분 (%s)"
                  % (i, len(pairs), by_id[a]["name"], by_id[b]["name"],
                     r["duration"], r["summary"] or r["type"]))
        time.sleep(args.sleep)          # 레이트리밋 유발 금지

    if fails and not matrix:
        sys.exit("[!] 전부 실패 — 기존 routes.json 을 보존하고 종료합니다.")

    data = {
        "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "date": args.date,
        "departureTime": args.time,
        "source": "네이버 지도 대중교통 경로 (map.naver.com)",
        "goal": GOAL,
        "origins": ORIGINS,
        "stops": stops,
        "matrix": matrix,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("[+] 저장: %s (실패 %d건)" % (OUT, fails))


if __name__ == "__main__":
    main()
