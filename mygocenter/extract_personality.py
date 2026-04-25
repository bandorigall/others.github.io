"""
유튜브 플레이리스트에서 パーソナリティ 줄을 전체 회차 추출 후 JSON 저장.

- 매 회차마다 JSON 즉시 저장 (중간에 끊겨도 이어받기 가능)
- 일본어 제목/설명 강제

사전 준비:
    pip install yt-dlp

실행:
    python extract_personality.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLUFFl4hYd1R0SQPSCAqPVuT5F2By4pqO7"
PLAYLIST_END = None  # None 이면 전체
OUTPUT_JSON = "personality_results.json"

YT_DLP = shutil.which("yt-dlp") or "yt-dlp"


def run_yt_dlp(cmd: list[str]) -> str:
    """
    yt-dlp 실행 후 stdout을 utf-8 문자열로 반환.
    - stderr 완전 분리 (Windows cp949 오염 방지)
    - PYTHONUTF8=1 주입으로 yt-dlp stdout utf-8 강제
    - Accept-Language: ja-JP 헤더로 일본어 응답 강제
    """
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [cmd[0]] + [
        "--extractor-args", "youtube:lang=ja",
        "--add-header", "Accept-Language:ja-JP,ja;q=0.9",
    ] + cmd[1:]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return result.stdout.decode("utf-8", errors="replace")


def fetch_video_ids(playlist_url: str, count: int | None) -> list[dict]:
    """플레이리스트 전체(또는 count개)의 영상 ID/제목/순서를 가져온다."""
    cmd = [YT_DLP, "--flat-playlist", "--dump-json", playlist_url]
    if count is not None:
        cmd += ["--playlist-end", str(count)]

    output = run_yt_dlp(cmd)
    if not output.strip():
        print("[ERROR] 플레이리스트 조회 결과가 비어 있습니다.", file=sys.stderr)
        sys.exit(1)

    videos = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        videos.append({
            "index": data.get("playlist_index") or data.get("playlist_autonumber"),
            "id": data["id"],
            "title": data.get("title", ""),
        })
    return videos


def fetch_video_meta(video_id: str) -> tuple[str, str]:
    """단일 영상의 upload_date와 설명을 반환한다."""
    cmd = [
        YT_DLP,
        "--skip-download",
        "--print", "upload_date",
        "--print", "description",
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    output = run_yt_dlp(cmd)
    lines = output.splitlines()
    upload_date = lines[0].strip() if lines else ""
    description = "\n".join(lines[1:]) if len(lines) > 1 else ""
    return upload_date, description


def extract_personality(description: str) -> str | None:
    """설명에서 パーソナリティ： 줄의 이름 부분만 반환한다."""
    for line in description.splitlines():
        if "パーソナリティ" in line:
            if "：" in line:
                return line.split("：", 1)[1].strip()
            return line.strip()
    return None


def load_existing(path: str) -> tuple[list[dict], set[str]]:
    """기존 JSON을 로드해 결과 리스트와 완료된 video_id 집합을 반환한다."""
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            results = json.load(f)
        done_ids = {r["video_id"] for r in results}
        print(f"기존 저장분 {len(results)}개 로드. 이어서 진행합니다.\n")
        return results, done_ids
    return [], set()


def save(results: list[dict], path: str) -> None:
    """결과를 JSON으로 저장한다."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    results, done_ids = load_existing(OUTPUT_JSON)

    videos = fetch_video_ids(PLAYLIST_URL, PLAYLIST_END)
    total = len(videos)
    pending = [v for v in videos if v["id"] not in done_ids]
    print(f"총 {total}개 영상 / 미처리 {len(pending)}개\n")

    for i, v in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] #{v['index']} {v['title']} (id={v['id']})")
        upload_date, desc = fetch_video_meta(v["id"])
        personality = extract_personality(desc)
        if personality:
            print(f"  -> {personality}")
        else:
            print("  -> 찾을 수 없음")

        results.append({
            "index": v["index"],
            "title": v["title"],
            "video_id": v["id"],
            "upload_date": upload_date,
            "personality": personality,
        })

        # 매 회차마다 즉시 저장
        save(results, OUTPUT_JSON)

    # 회차 번호 기준으로 정렬 후 최종 저장
    results.sort(key=lambda r: r["index"] or 0)
    save(results, OUTPUT_JSON)
    print(f"\n완료. {OUTPUT_JSON} 저장됨 (총 {len(results)}개)")


if __name__ == "__main__":
    main()