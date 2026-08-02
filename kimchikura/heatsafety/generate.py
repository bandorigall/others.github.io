# -*- coding: utf-8 -*-
"""
열중증(열사병) 안내 픽토그램 생성기 - OpenAI Images API

사용법:
    set OPENAI_API_KEY=sk-...        (PowerShell:  $env:OPENAI_API_KEY="sk-...")
    python generate.py               # prompts.json 전체 생성
    python generate.py 01_hydrate    # 특정 패널만 재생성
    python generate.py --model gpt-image-1 --size 1024x1024 --quality high

결과: out/<id>.png
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
OUT = HERE / "out"
API = "https://api.openai.com/v1/images/generations"


def load_dotenv():
    """같은 폴더의 .env를 읽어 환경변수로 올린다 (KEY=VALUE 한 줄씩)."""
    f = HERE / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def build_prompt(panel, style_suffix):
    return f"{panel['prompt']}\n\nStyle: {style_suffix}"


def generate(prompt, model, size, quality, key, retries=3):
    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
    if quality:
        payload["quality"] = quality
    for attempt in range(1, retries + 1):
        r = requests.post(
            API,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=300,
        )
        if r.status_code == 200:
            return base64.b64decode(r.json()["data"][0]["b64_json"])
        if r.status_code in (429, 500, 502, 503) and attempt < retries:
            wait = 5 * attempt
            print(f"    {r.status_code} - {wait}s 후 재시도 ({attempt}/{retries})")
            time.sleep(wait)
            continue
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="생성할 패널 id (없으면 전체)")
    ap.add_argument("--model", default="gpt-image-1")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--quality", default="low",
                    help="low|medium|high. 기본 low(가장 저렴). 구도 확정 후 --quality high로 최종본만 재생성")
    ap.add_argument("--dry-run", action="store_true", help="프롬프트만 출력하고 호출 안 함")
    args = ap.parse_args()

    load_dotenv()
    key = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key and not args.dry_run:
        sys.exit(".env에 OPENAI_KEY(또는 OPENAI_API_KEY)가 없습니다.")

    spec = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
    # 안내 패널 + 준비물 아이콘. 각자 다른 style_suffix를 쓴다.
    panels = [dict(p, _style=spec["style_suffix"]) for p in spec["panels"]]
    panels += [dict(p, _style=spec["kit_style"]) for p in spec.get("kit", [])]
    if args.ids:
        panels = [p for p in panels if p["id"] in args.ids]
        if not panels:
            sys.exit(f"해당 id 없음: {args.ids}")

    OUT.mkdir(exist_ok=True)
    for p in panels:
        prompt = build_prompt(p, p["_style"])
        print(f"[{p['id']}] {p['ko']}")
        if args.dry_run:
            print(prompt + "\n")
            continue
        img = generate(prompt, args.model, args.size, args.quality or None, key)
        dest = OUT / f"{p['id']}.png"
        dest.write_bytes(img)
        print(f"    -> {dest}")


if __name__ == "__main__":
    main()
