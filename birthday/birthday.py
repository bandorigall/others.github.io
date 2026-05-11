import sys
import os
import csv
import re

# 1. '디시 색상 인코딩' 폴더 경로 설정 및 import
current_dir = os.path.dirname(os.path.abspath(__file__))
color_lib_path = os.path.join(current_dir, '디시 색상 인코딩')
sys.path.append(color_lib_path)

try:
    from replace_colour import char_to_rgb
except ImportError:
    print("경고: '디시 색상 인코딩/replace_colour.py'를 찾을 수 없습니다. 색상이 적용되지 않습니다.")
    char_to_rgb = {}

# ---------------------------------------------------------
# 설정 및 스타일
# ---------------------------------------------------------
BASE_URL = "https://gall.dcinside.com/mgallery/board/view?id=bang_dream&no={}"
FIXED_HEADERS = ["날짜", "생일자", "공식 생일 축전", "생일 스토리", "생일 축하 대사"]

# [테이블 스타일]
TABLE_STYLE = (
    "width: 100%; border-collapse: collapse; table-layout: fixed; "
    "font-size: 13px; font-family: 'Malgun Gothic', sans-serif; "
    "margin: 10px 0; border-top: 2px solid #555;"
)

# [헤더 스타일]
TH_STYLE = (
    "background-color: #f9f9f9; color: #555; padding: 12px 0; "
    "border-bottom: 1px solid #ccc; font-weight: bold; text-align: center;"
)

# [셀 스타일 - 중요 변경]
# TD에서 padding을 제거(0px)하고, 내부 요소가 꽉 차게 만듭니다.
TD_STYLE_NORMAL = (
    "padding: 12px 2px; border-bottom: 1px solid #eee; "
    "text-align: center; vertical-align: middle; word-break: keep-all;"
)

# 링크가 들어갈 셀은 패딩을 0으로 줍니다. (링크 태그가 패딩 역할을 대신함)
TD_STYLE_LINK = (
    "padding: 0; border-bottom: 1px solid #eee; "
    "text-align: center; vertical-align: middle;"
)

NAME_MAPPING = {
    "레이": "레이야", "마스키": "마스킹", "롯카": "록", "레오나": "파레오", "치유": "츄츄"
}

# ---------------------------------------------------------
# 함수 정의
# ---------------------------------------------------------
def get_contrast_text_color(rgb_str):
    if not rgb_str: return "#333333"
    nums = re.findall(r'\d+', rgb_str)
    if len(nums) < 3: return "#333333"
    r, g, b = map(int, nums[:3])
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return "#ffffff" if luminance < 128 else "#222222"

def find_color_by_name(name):
    for key, mapped_key in NAME_MAPPING.items():
        if key in name: return char_to_rgb.get(mapped_key, "")
    for key, color in char_to_rgb.items():
        if key in name: return color
    return ""

def make_link_html(text_id):
    """
    [최종 해결책]
    display: block을 사용하여 링크 영역을 셀 전체로 확장합니다.
    이렇게 하면 '글자'가 아니라 '네모 칸' 전체가 버튼이 되어 터치 인식이 잘 됩니다.
    """
    text_id = str(text_id).strip()
    
    # 데이터가 없을 때: 높이를 맞춰주기 위해 빈 div나 span에 패딩을 줌
    if not text_id or text_id.lower() == "nan" or text_id == "":
        return '<div style="padding: 12px 0; color: #ccc;">-</div>'
    
    url = BASE_URL.format(text_id)
    
    # [핵심] 
    # display: block -> 링크를 블록 요소로 만듦
    # width: 100% -> 가로 꽉 채움
    # padding: 12px 0 -> 세로 높이 확보 (기존 TD 패딩을 여기서 대체)
    # text-decoration: none -> 밑줄 제거 (깔끔하게)
    return (
        f'<a href="{url}" '
        f'style="display: block; width: 100%; padding: 12px 0; '
        f'color: #0000FF; font-weight: bold; text-decoration: none;">'
        f'보기</a>'
    )

def generate_html_from_csv(input_csv, output_html):
    if not os.path.exists(input_csv):
        print(f"오류: {input_csv} 파일이 없습니다.")
        return

    html_lines = []
    html_lines.append('<!DOCTYPE html>')
    html_lines.append('<html lang="ko">')
    html_lines.append('<head>')
    html_lines.append('  <meta charset="UTF-8">')
    html_lines.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_lines.append('  <title>2026년 방캐 생일 일람표</title>')
    html_lines.append('</head>')
    html_lines.append('<body style="margin: 0; padding: 16px; background-color: #fff;">')
    html_lines.append('  <div style="width: 1000px; max-width: 100%; margin: 0 auto; text-align: center;">')
    html_lines.append('    <img src="title.png" style="max-width: 100%; height: auto; display: block; margin: 0 auto 12px;">')
    html_lines.append(f'<table style="{TABLE_STYLE}">')
    
    html_lines.append('  <thead>\n    <tr>')
    for h in FIXED_HEADERS:
        html_lines.append(f'      <th style="{TH_STYLE}">{h}</th>')
    html_lines.append('    </tr>\n  </thead>')
    html_lines.append('  <tbody>')
    
    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader, None)
        
        for row in reader:
            if not row or len(row) < 2: continue
            
            date = row[0]
            name = row[1]
            id_official = row[2] if len(row) > 2 else ""
            id_story = row[3] if len(row) > 3 else ""
            id_line = row[4] if len(row) > 4 else ""

            bg_color = find_color_by_name(name)
            if not bg_color:
                name_html = f"<b>{name}</b>"
            else:
                text_color = get_contrast_text_color(bg_color)
                span_style = (f"background-color: {bg_color}; color: {text_color}; "
                              f"padding: 4px 10px; border-radius: 50px; "
                              f"display: inline-block; font-weight: bold; font-size: 11px; "
                              f"line-height: 1.2;")
                name_html = f'<span style="{span_style}">{name}</span>'
            
            html_lines.append('    <tr style="background-color: #ffffff;">')
            # 일반 텍스트 셀 (날짜, 이름)은 기존 TD 스타일 사용
            html_lines.append(f'      <td style="{TD_STYLE_NORMAL} color: #666;">{date}</td>')
            html_lines.append(f'      <td style="{TD_STYLE_NORMAL}">{name_html}</td>')
            
            # 링크가 들어가는 셀은 패딩이 없는 TD 스타일 사용 (a태그가 패딩 가짐)
            html_lines.append(f'      <td style="{TD_STYLE_LINK}">{make_link_html(id_official)}</td>')
            html_lines.append(f'      <td style="{TD_STYLE_LINK}">{make_link_html(id_story)}</td>')
            html_lines.append(f'      <td style="{TD_STYLE_LINK}">{make_link_html(id_line)}</td>')
            html_lines.append('    </tr>')

    html_lines.append('  </tbody>\n</table>')
    html_lines.append('  <img src="birthday_detail.png" style="max-width: 100%; height: auto; display: block; margin: 32px auto 0;">')
    html_lines.append('  <div style="margin: 20px 0 8px;">')
    html_lines.append('    <a href="https://gall.dcinside.com/mgallery/board/view/?id=bang_dream&no=6162054" '
                       'style="display: inline-block; padding: 10px 24px; background-color: #555; color: #fff; '
                       'text-decoration: none; border-radius: 6px; font-size: 13px; font-family: \'Malgun Gothic\', sans-serif;">'
                       '사진 원본 링크</a>')
    html_lines.append('  </div>')
    html_lines.append('  </div>')
    html_lines.append('</body>')
    html_lines.append('</html>')

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_lines))

    print(f"완료! '{output_html}' 파일이 생성되었습니다.")

if __name__ == "__main__":
    generate_html_from_csv('birthday.csv', 'index.html')