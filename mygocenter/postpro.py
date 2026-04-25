"""
personality_results.json の表記ゆれを修正し、別ファイルに保存する。

実行:
    python postpro.py
出力:
    personality_results_postpro.json
"""

import json
import os
import re
import shutil
import subprocess

INPUT_JSON = "personality_results.json"
OUTPUT_JSON = "personality_results_postpro.json"

YT_DLP = shutil.which("yt-dlp") or "yt-dlp"

# 비공개 영상 — yt-dlp fetch 불가, postpro/HTML 양쪽에서 제외
PRIVATE_VIDEO_IDS = {
    "LLOD1ZGkPkE",
    "s4Oss4cMacA",
    "0HklC3CSufw",
    "VM2fwBCQfjI",
    "Tbu9x6gHEvI",
}

# 正規化後の표기に統一するエイリアスマップ
# normalize_name() 적용 후 키와 照合する
ALIAS_MAP = {
    # キャラ名の長形 → 短形 (「燈」「愛音」等に統一)
    "高松燈": "燈",
    "千早愛音": "愛音",
    "要楽奈": "楽奈",
    "長崎そよ": "そよ",
    "椎名立希": "立希",
    # 声優名のみ → 声優（キャラ 役）形式に統一
    "羊宮妃那": "羊宮妃那（高松燈 役）",
    "立石凛": "立石凛（千早愛音 役）",
    "青木陽菜": "青木陽菜（要楽奈 役）",
    "小日向美香": "小日向美香（長崎そよ 役）",
    "林鼓子": "林鼓子（椎名立希 役）",
    # 逆表記 (キャラ（声優 役）형식) → 正規形に統一
    "椎名立希（林鼓子 役）": "林鼓子（椎名立希 役）",
    "千早愛音（立石凛 役）": "立石凛（千早愛音 役）",
    "高松燈（羊宮妃那 役）": "羊宮妃那（高松燈 役）",
    "要楽奈（青木陽菜 役）": "青木陽菜（要楽奈 役）",
    "長崎そよ（小日向美香 役）": "小日向美香（長崎そよ 役）",
}


def normalize_name(name: str) -> str:
    """괄호 통일 + 括弧内スペース정리 (役 직전만 1개)."""
    name = name.replace("(", "（").replace(")", "）")

    def fix_bracket(m: re.Match) -> str:
        inner = re.sub(r"\s+", "", m.group(1))  # 괄호 내 스페이스 전부 제거
        if inner.endswith("役"):
            inner = inner[:-1] + " 役"           # 役 직전에만 스페이스 1개
        return "（" + inner + "）"

    name = re.sub(r"（([^）]+)）", fix_bracket, name)

    # 괄호 앞 이름 부분의 스페이스 제거 (예: 羊宮 妃那 → 羊宮妃那)
    if "（" in name:
        pre, rest = name.split("（", 1)
        name = pre.replace(" ", "") + "（" + rest
    else:
        name = name.replace(" ", "")

    return name.strip()


def canonicalize(name: str) -> str:
    name = normalize_name(name)
    return ALIAS_MAP.get(name, name)


def process_personality(personality: str) -> str | None:
    # 괄호 안에 잘못 끼어든 구분자 수정: 「役、)」→「役）・」
    personality = re.sub(r"役\s*[、。,．]+\s*[)）]", "役）・", personality)

    parts = re.split(r"[・、]", personality)
    seen: list[str] = []
    seen_set: set[str] = set()
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # 앞에 닫힘괄호만 남은 깨진 항목 제거
        if p.startswith(("）", ")")):
            continue
        canonical = canonicalize(p)
        if canonical and canonical not in seen_set:
            seen.append(canonical)
            seen_set.add(canonical)

    return "・".join(seen) if seen else None


def backfill_dates(results: list[dict]) -> int:
    """upload_date 없는 항목을 yt-dlp로 보충하고 원본 JSON에도 저장한다."""
    missing = [r for r in results if not r.get("upload_date") and r.get("video_id") not in PRIVATE_VIDEO_IDS]
    if not missing:
        return 0
    print(f"upload_date 없는 항목 {len(missing)}개 취득 중...")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    fetched = 0
    for i, r in enumerate(missing, 1):
        vid = r["video_id"]
        result = subprocess.run(
            [YT_DLP, "--skip-download", "--print", "upload_date",
             "--extractor-args", "youtube:lang=ja",
             f"https://www.youtube.com/watch?v={vid}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        )
        date = result.stdout.decode("utf-8", errors="replace").strip()
        if date and len(date) == 8 and date.isdigit():
            r["upload_date"] = date
            fetched += 1
        print(f"  [{i}/{len(missing)}] {vid} → {date or '취득 실패'}")
    # 원본에 날짜 저장 → 다음 실행 시 재취득 방지
    if fetched:
        with open(INPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  → {INPUT_JSON} 날짜 {fetched}건 저장")
    return len(missing)


def main() -> None:
    with open(INPUT_JSON, encoding="utf-8") as f:
        results = json.load(f)

    filled = backfill_dates(results)
    if filled:
        print(f"upload_date {filled}건 보충\n")

    changed = 0
    for r in results:
        original = r.get("personality")
        if not original:
            continue
        fixed = process_personality(original)
        if fixed != original:
            print(f"#{r.get('index', '?'):>4}  {original}")
            print(f"      → {fixed}")
            r["personality"] = fixed
            changed += 1

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{changed}건 수정 → {OUTPUT_JSON} 저장 완료")


if __name__ == "__main__":
    main()
