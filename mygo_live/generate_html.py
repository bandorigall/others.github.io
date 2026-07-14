# -*- coding: utf-8 -*-
"""mygo_lives.json -> index.html 의 LIVES 배열을 재생성한다.

index.html 의 나머지(스타일/스크립트/레이아웃)는 건드리지 않는다.
LIVES 블록은 아래 두 마커 사이만 교체된다.

  // <LIVES:AUTO-GENERATED>  ... // </LIVES:AUTO-GENERATED>

데이터 수정은 mygo_lives.json 에만 하고 이 스크립트를 돌린다.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "mygo_lives.json"
DST = HERE / "index.html"

BEGIN = "// <LIVES:AUTO-GENERATED>"
END = "// </LIVES:AUTO-GENERATED>"

# LIVES 에 싣는 필드(순서 유지). display 오버라이드가 있으면 그 값을 쓴다.
FIELDS = ["no", "type", "tour", "title", "subtitle", "date", "venue",
          "city", "capacity", "milestone", "setlist", "encore",
          "setlist_note", "source"]
OVERRIDABLE = {"title", "venue", "city", "tour", "subtitle", "milestone", "type"}
WEATHER_FIELDS = ["tmax_c", "precip_mm", "desc"]  # 렌더에 쓰는 것만


def js(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "[" + ",".join(js(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join("%s:%s" % (k, js(x)) for k, x in v.items()) + "}"
    return json.dumps(v, ensure_ascii=False)


def entry_to_js(e):
    disp = e.get("display") or {}
    out = {}
    for f in FIELDS:
        v = disp.get(f, e.get(f)) if f in OVERRIDABLE else e.get(f)
        if f in ("tour", "subtitle", "milestone", "setlist_note", "source") and not v:
            continue  # 값 없으면 아예 생략(기존 HTML과 동일)
        out[f] = [] if f in ("setlist", "encore") and v is None else v
    w = e.get("weather")
    out["weather"] = {k: w[k] for k in WEATHER_FIELDS if k in w} if w else None
    return "{" + ",".join("%s:%s" % (k, js(v)) for k, v in out.items()) + "}"


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    lives = data["lives"]
    body = ",\n".join(entry_to_js(e) for e in lives)
    block = "%s\nconst LIVES = [\n%s\n];\n%s" % (BEGIN, body, END)

    html = DST.read_text(encoding="utf-8")
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if pat.search(html):
        html = pat.sub(lambda _: block, html, count=1)
    else:  # 최초 1회: 기존 const LIVES 배열을 마커째로 감싼다
        i = html.index("const LIVES = [")
        j = html.index("\n];", i) + len("\n];")
        html = html[:i] + block + html[j:]
    DST.write_text(html, encoding="utf-8")

    filled = sum(1 for e in lives if e.get("setlist"))
    print("LIVES %d건 생성 (세트리스트 있음 %d / 없음 %d)"
          % (len(lives), filled, len(lives) - filled))


if __name__ == "__main__":
    main()
