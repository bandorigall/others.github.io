# -*- coding: utf-8 -*-
# =============================================================
#  3초 곡 퀴즈 - 클립 생성기
# =============================================================
#  ▶ 사용법
#    1) 아래 SONGS 목록만 원하는 대로 고친다.
#         ("유튜브영상ID", "원어제목", "한국어제목")
#         - 영상ID = youtube.com/watch?v=XXXX 의 XXXX 부분
#         - 한국어제목이 없으면 원어와 똑같이 적으면 됨
#    2) 같은 폴더의  재생성.bat  을 더블클릭 (또는 python build_quiz.py)
#    3) audio/ 폴더에 3초 클립, quizdata.js 가 새로 만들어짐 → 끝
#
#  ⚙ 필요 프로그램: yt-dlp, ffmpeg  (PATH에 있어야 함)
#  ⚙ 옵션은 맨 아래 [설정] 부분에서 바꿀 수 있음
# =============================================================

SONGS = [
    ("DhYniTbW2P0", "Daylight -デイライト-", "Daylight -데이라이트-"),
    ("Qam2U-LF_Ks", "金色へのプレリュード", "금빛의 프렐류드"),
    ("ulnZ8yiS7Jg", "ブルームブルーム", "Bloom Bloom"),
    ("NuhjVeWwvoM", "ハーモニー・デイ", "하모니 데이"),
    ("RD_6TSNkxg0", "Fateful...", "Fateful..."),
    ("6C4NOz-t3QA", "寄る辺のSunny, Sunny", "의지하는 Sunny, Sunny"),
    ("nnpD32__lAY", "誓いのWingbeat", "맹세의 Wingbeat"),
    ("HqDa4NOAt8w", "カラフルリバティー", "컬러풀 리버티"),
    ("D_uUbtZUOPc", "メランコリックララバイ", "멜랑콜릭 럴러바이"),
    ("yuG78deMpUo", "フレージング ミラージュ", "프레이징 미라지"),
    ("mKGMgDGj0kQ", "わたしまちがいさがし", "나 틀린 그림 찾기"),
    ("Wl5LZ3iJNzM", "Sonorous", "Sonorous"),
    ("eWqv5RB6jng", "Secret Dawn", "Secret Dawn"),
    ("eAjX1Ihvtac", "蒼穹へのトレイル", "창궁으로의 트레일"),
    # 여기에 줄을 추가/삭제하면 됨:
    # ("영상ID", "원어제목", "한국어제목"),
]

# ---------------- [설정] ----------------
CLIP_SEC     = 3      # 클립 길이(초)
CLIPS_PER    = 3      # 곡당 만들 클립 수 (매번 다른 구간에서 랜덤 재생)
RANGE_LO     = 0.25   # 곡의 몇 %~ 지점부터 뽑을지 (0.25 = 25%)
RANGE_HI     = 0.70   #            ~ 몇 % 지점까지 (인트로/아웃트로 회피용)
BITRATE      = "96k"  # mp3 음질
SEED         = None   # 숫자로 고정하면 매번 같은 구간, None이면 실행마다 랜덤
# ----------------------------------------

import os, sys, subprocess, json, random, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(HERE, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
if SEED is not None:
    random.seed(SEED)

def have(cmd):
    from shutil import which
    return which(cmd) is not None

if not have("yt-dlp") or not have("ffmpeg"):
    print("!! yt-dlp / ffmpeg 가 필요합니다. 설치 후 PATH에 등록하세요.")
    sys.exit(1)

def ffprobe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0

TMP = tempfile.mkdtemp(prefix="quizdl_")
data = []
used_names = set()

for vid, title, titleKo in SONGS:
    src = os.path.join(TMP, vid + ".m4a")
    print(f"[다운로드] {title}  ({vid})", flush=True)
    subprocess.run(["yt-dlp", "-f", "bestaudio[ext=m4a]/bestaudio",
                    "-o", src, "--no-playlist", "-q", "--no-warnings",
                    "https://www.youtube.com/watch?v=" + vid])
    if not os.path.exists(src):
        print("   !! 다운로드 실패 — 건너뜀", flush=True)
        continue

    dur = ffprobe_dur(src)
    if dur < CLIP_SEC + 5:
        print("   !! 곡이 너무 짧음 — 건너뜀", flush=True)
        continue

    lo, hi = dur * RANGE_LO, dur * RANGE_HI
    candidates = [round(lo + (hi - lo) * i / 8, 1) for i in range(9)]
    offs = sorted(random.sample(candidates, min(CLIPS_PER, len(candidates))))

    clips = []
    for k, off in enumerate(offs):
        name = f"{vid}_{k}.mp3"
        used_names.add(name)
        outp = os.path.join(AUDIO_DIR, name)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(off),
                        "-t", str(CLIP_SEC), "-i", src,
                        "-af", f"afade=t=in:st=0:d=0.15,afade=t=out:st={CLIP_SEC-0.15}:d=0.15",
                        "-ac", "2", "-ar", "44100", "-b:a", BITRATE, outp])
        clips.append("audio/" + name)

    data.append({"id": vid, "title": title, "titleKo": titleKo, "clips": clips})
    print(f"   ok  {len(clips)}개 클립", flush=True)

# 목록에서 빠진 곡의 옛 클립 청소
removed = 0
for f in os.listdir(AUDIO_DIR):
    if f.endswith(".mp3") and f not in used_names:
        os.remove(os.path.join(AUDIO_DIR, f)); removed += 1

with open(os.path.join(HERE, "quizdata.js"), "w", encoding="utf-8") as f:
    f.write("window.QUIZ_SONGS = ")
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write(";\n")

print(f"\n완료! {len(data)}곡 / 안 쓰는 클립 {removed}개 정리됨.")
print("브라우저에서 quiz.html 새로고침하면 반영됩니다.")
