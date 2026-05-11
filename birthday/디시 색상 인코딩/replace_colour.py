from pathlib import Path
import re

char_to_rgb = {
    # 기존 캐릭터
    "카스미": "rgb(255, 85, 34)", "타에": "rgb(0, 119, 221)", "리미": "rgb(255, 85, 187)",
    "사아야": "rgb(255, 204, 17)", "아리사": "rgb(170, 102, 221)", "란": "rgb(238, 0, 34)",
    "모카": "rgb(0, 204, 170)", "히마리": "rgb(255, 153, 153)", "토모에": "rgb(187, 0, 51)",
    "츠구미": "rgb(255, 238, 136)", "아야": "rgb(255,136,187)", "치사토": "rgb(255, 238, 170)",
    "히나": "rgb(85, 221, 238)", "이브": "rgb(221, 187, 255)", "마야": "rgb(153, 221, 136)",
    "유키나": "rgb(136, 17, 136)", "사요": "rgb(0, 170, 187)", "리사": "rgb(221, 34, 0)",
    "아코": "rgb(221, 0, 136)", "린코": "rgb(187, 187, 187)", "코코로": "rgb(255, 238, 34)",
    "카오루": "rgb(170, 51, 204)", "하구미": "rgb(255, 153, 34)", "카논": "rgb(68,221,255)",
    "미사키": "rgb(0, 102, 153)", "마시로": "rgb(102, 119, 204)", "나나미": "rgb(238, 119, 68)",
    "루이": "rgb(102, 153, 136)", "토우코": "rgb(238, 102, 102)", "츠쿠시": "rgb(238, 119, 136)",
    "레이야": "rgb(204, 0, 0)", "록": "rgb(170,238,34)", "마스킹": "rgb(238, 187, 68)",
    "파레오": "rgb(253,153,187)", "츄츄": "rgb(0, 187, 255)", "토모리": "rgb(119,187,221)",
    "라나": "rgb(119,221,119)", "아논": "rgb(255,136,153)", "소요": "rgb(255,221,136)",
    "타키": "rgb(119,119,170)", "미셸": "rgb(245, 141, 176)", 
    "우이카": "rgb(187,153,85)", "사키코": "rgb(119,153,204)", "모르티스": "rgb(119,153,119)",
    "무츠미": "rgb(119,153,119)", "우미리": "rgb(51,85,102)", "냐무": "rgb(170,68,119)",

    # 신규 추가 (Hex -> RGB 변환 적용)
    "아라레": "rgb(255, 221, 51)",   # #ffdd33
    "노노카": "rgb(255, 170, 204)",  # #ffaacc
    "리츠": "rgb(85, 136, 221)",     # #5588dd
    "미야코": "rgb(153, 119, 221)",  # #9977dd
    "유노": "rgb(255, 102, 136)",     # #ff6688

    "호타루": "rgb(153, 255, 153)",
    "나츠메": "rgb(255, 68, 68)",
    "나기": "rgb(85, 85, 255)",
    "마호로": "rgb(102, 255, 255)",
    "호우카": "rgb(230, 134, 246)",

    "라이카": "rgb(255, 127, 0)",
    "미쿠": "rgb(51, 204, 255)",
    "요모기": "rgb(68, 139, 139)",
    "치에리": "rgb(255, 85, 170)",
    "시즈쿠": "rgb(139, 139, 255)",
    
}

bold_only = {"마리나", "리리코", "라디오 스태프", "스태프", '하루미', }

# 1. 모든 이름을 패턴으로 만듦 (긴 이름 우선)
all_names = list(char_to_rgb.keys()) + list(bold_only)
all_names.sort(key=len, reverse=True)
name_pattern = re.compile("|".join(map(re.escape, all_names)))

# <p> 태그 찾기 패턴
p_tag_pattern = re.compile(r"<p>(.*?)</p>")

input_path = Path("original.txt")
output_path = Path("result.txt")

def style_replacer(match):
    """이름에 스타일을 입혀주는 함수"""
    name = match.group(0)
    if name in char_to_rgb:
        return f'<span style="background-color: {char_to_rgb[name]};">{name}</span>'
    elif name in bold_only:
        return f"<b>{name}</b>"
    return name

def process_p_content(match):
    """
    <p> 태그 내용을 분석하여, '이름+구분자'로만 구성된 줄인지 확인
    """
    original_content = match.group(1) # <p>와 </p> 사이의 내용
    
    # 1. 내용 중에서 '캐릭터 이름들'을 모두 제거해 봅니다.
    # 예: "나나미, 카논" -> ", "
    # 예: "이브 쨩~!" -> " 쨩~!"
    content_without_names = name_pattern.sub('', original_content)
    
    # 2. 남은 문자열에서 '허용된 구분자'들을 싹 제거합니다.
    # 허용 구분자: 공백(\s), 쉼표(,), 앤드(&), 가운뎃점(·), 슬래시(/), 플러스(+), 하이픈(-)
    clean_residue = re.sub(r"[\s,&·/+\-・]+", "", content_without_names)
    
    # 3. 판별:
    # 만약 이름과 구분자를 다 지웠는데도 글자가 남아있다면? (len > 0)
    # 그건 '쨩', '!', '어라?', '가자' 같은 대사 내용입니다. -> 색칠하지 않음
    if len(clean_residue) > 0:
        return match.group(0) # 원본 그대로 반환
    
    # 4. 남은 게 없다면(len == 0), 이 줄은 오직 '이름'과 '구분자'로만 이루어진 줄입니다.
    # -> 스타일 적용
    new_content = name_pattern.sub(style_replacer, original_content)
    return f"<p>{new_content}</p>"

if input_path.exists():
    with input_path.open(encoding="utf-8") as f:
        text = f.read()

    # 전체 텍스트에서 <p> 태그를 찾아 검사 및 변환
    text = p_tag_pattern.sub(process_p_content, text)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"변환이 완료되었습니다. {output_path}")

else:
    print("original.txt 파일이 없습니다.")