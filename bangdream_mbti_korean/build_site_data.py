from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
DOSSIERS = DATASET / "character_dossiers"
OUTPUT = ROOT / "site" / "site-data.js"
ASSET_MANIFEST = ROOT / "site" / "assets" / "asset-manifest.json"
FANDOM_API = "https://bandori.fandom.com/api.php"
FANDOM_WIKI = "https://bandori.fandom.com/wiki/"

QUESTION_BANK_FILES = {
    "zh": DATASET / "ojts_question_bank_v2_1_zh.json",
    "en": DATASET / "ojts_question_bank_v2_1_en.json",
    "ja": DATASET / "ojts_question_bank_v2_1_ja.json",
}

BAND_PAGES = {
    "popipa": "Poppin'Party",
    "afglo": "Afterglow",
    "pasupare": "Pastel*Palettes",
    "roselia": "Roselia",
    "hhw": "Hello,_Happy_World!",
    "morfo": "Morfonica",
    "ras": "RAISE_A_SUILEN",
    "mygo": "MyGO!!!!!",
    "ave": "Ave_Mujica",
    "sumimi": "sumimi",
}

BAND_NAMES = {
    "popipa": "Poppin'Party",
    "afglo": "Afterglow",
    "pasupare": "Pastel*Palettes",
    "roselia": "Roselia",
    "hhw": "Hello, Happy World!",
    "morfo": "Morfonica",
    "ras": "RAISE A SUILEN",
    "mygo": "MyGO!!!!!",
    "ave": "Ave Mujica",
    "sumimi": "sumimi",
    "bangdream": "BanG Dream!",
}

SPECIAL_BAND_ASSETS = {
    "bangdream": {
        "logo": "https://static.wikia.nocookie.net/bandori/images/4/4b/BanG_Dream%21_Logo.svg/revision/latest?cb=20180922150901",
        "icon": "https://static.wikia.nocookie.net/bandori/images/4/4b/BanG_Dream%21_Logo.svg/revision/latest?cb=20180922150901",
        "page_url": "https://bandori.fandom.com/wiki/BanG_Dream!",
    }
}

SPECIAL_COLORS = {
    "char_mana_mana": "#D8B14D",
    "char_marina_marina": "#E00050",
    "char_owner_livehouse": "#E00050",
    # Fallback sampled from the fandom icon because Asuka is not listed under Character Color Codes.
    "char_asuka_asuka": "#B490E4",
}

CHARACTER_CONFIG = {
    "char_ako_ako": {"page_title": "Udagawa_Ako", "english_name": "Udagawa Ako", "band": "roselia", "color_template": "Ako"},
    "char_anon_anon": {"page_title": "Chihaya_Anon", "english_name": "Chihaya Anon", "band": "mygo", "color_template": "Anon"},
    "char_arisa_arisa": {"page_title": "Ichigaya_Arisa", "english_name": "Ichigaya Arisa", "band": "popipa", "color_template": "Arisa"},
    "char_asuka_asuka": {"page_title": "Toyama_Asuka", "english_name": "Toyama Asuka", "band": "bangdream", "portrait_strategy": "page"},
    "char_aya_aya": {"page_title": "Maruyama_Aya", "english_name": "Maruyama Aya", "band": "pasupare", "color_template": "Aya"},
    "char_chisato_chisato": {"page_title": "Shirasagi_Chisato", "english_name": "Shirasagi Chisato", "band": "pasupare", "color_template": "Chisato"},
    "char_chiyu_chiyu": {"page_title": "CHU²", "portrait_page_title": "Tamade_Chiyu", "english_name": "CHU²", "band": "ras", "color_template": "Chu2"},
    "char_eve_eve": {"page_title": "Wakamiya_Eve", "english_name": "Wakamiya Eve", "band": "pasupare", "color_template": "Eve"},
    "char_hagumi_hagumi": {"page_title": "Kitazawa_Hagumi", "english_name": "Kitazawa Hagumi", "band": "hhw", "color_template": "Hagumi"},
    "char_himari_himari": {"page_title": "Uehara_Himari", "english_name": "Uehara Himari", "band": "afglo", "color_template": "Himari"},
    "char_hina_hina": {"page_title": "Hikawa_Hina", "english_name": "Hikawa Hina", "band": "pasupare", "color_template": "Hina"},
    "char_kanon_kanon": {"page_title": "Matsubara_Kanon", "english_name": "Matsubara Kanon", "band": "hhw", "color_template": "Kanon"},
    "char_kaoru_kaoru": {"page_title": "Seta_Kaoru", "english_name": "Seta Kaoru", "band": "hhw", "color_template": "Kaoru"},
    "char_kasumi_kasumi": {"page_title": "Toyama_Kasumi", "english_name": "Toyama Kasumi", "band": "popipa", "color_template": "Kasumi"},
    "char_kokoro_kokoro": {"page_title": "Tsurumaki_Kokoro", "english_name": "Tsurumaki Kokoro", "band": "hhw", "color_template": "Kokoro"},
    "char_lisa_lisa": {"page_title": "Imai_Lisa", "english_name": "Imai Lisa", "band": "roselia", "color_template": "Lisa"},
    "char_mana_mana": {"page_title": "Sumita_Mana", "english_name": "Sumita Mana", "band": "sumimi", "portrait_strategy": "page"},
    "char_marina_marina": {"page_title": "Tsukishima_Marina", "english_name": "Tsukishima Marina", "band": "bangdream", "portrait_strategy": "page"},
    "char_mashiro_mashiro": {"page_title": "Kurata_Mashiro", "english_name": "Kurata Mashiro", "band": "morfo", "color_template": "Mashiro"},
    "char_masuki_masuki": {"page_title": "MASKING", "portrait_page_title": "Satou_Masuki", "english_name": "MASKING", "band": "ras", "color_template": "Masking"},
    "char_maya_maya": {"page_title": "Yamato_Maya", "english_name": "Yamato Maya", "band": "pasupare", "color_template": "Maya"},
    "char_misaki_misaki": {"page_title": "Okusawa_Misaki", "english_name": "Okusawa Misaki", "band": "hhw", "color_template": "Michelle"},
    "char_moca_moca": {"page_title": "Aoba_Moca", "english_name": "Aoba Moca", "band": "afglo", "color_template": "Moca"},
    "char_mutsumi_mutsumi": {"page_title": "Wakaba_Mutsumi", "english_name": "Wakaba Mutsumi", "band": "ave", "portrait_strategy": "page", "color_template": "Mortis"},
    "char_nanami_nanami": {"page_title": "Hiromachi_Nanami", "english_name": "Hiromachi Nanami", "band": "morfo", "color_template": "Nanami"},
    "char_nyamu_nyamu": {"page_title": "Yuutenji_Nyamu", "english_name": "Yuutenji Nyamu", "band": "ave", "portrait_strategy": "page", "color_template": "Amoris"},
    "char_owner_livehouse": {"page_title": "Tsuzuki_Shifune", "english_name": "Tsuzuki Shifune", "band": "bangdream", "portrait_strategy": "page"},
    "char_rana_rana": {"page_title": "Kaname_Raana", "english_name": "Kaname Raana", "band": "mygo", "color_template": "Raana"},
    "char_ran_ran": {"page_title": "Mitake_Ran", "english_name": "Mitake Ran", "band": "afglo", "color_template": "Ran"},
    "char_rei_rei": {"page_title": "LAYER", "portrait_page_title": "Wakana_Rei", "english_name": "LAYER", "band": "ras", "color_template": "Layer"},
    "char_reona_reona": {"page_title": "PAREO", "portrait_page_title": "Nyubara_Reona", "english_name": "PAREO", "band": "ras", "color_template": "PAREO"},
    "char_rimi_rimi": {"page_title": "Ushigome_Rimi", "english_name": "Ushigome Rimi", "band": "popipa", "color_template": "Rimi"},
    "char_rinko_rinko": {"page_title": "Shirokane_Rinko", "english_name": "Shirokane Rinko", "band": "roselia", "color_template": "Rinko"},
    "char_rokka_rokka": {"page_title": "LOCK", "portrait_page_title": "Asahi_Rokka", "english_name": "LOCK", "band": "ras", "color_template": "Lock"},
    "char_rui_rui": {"page_title": "Yashio_Rui", "english_name": "Yashio Rui", "band": "morfo", "color_template": "Rui"},
    "char_saaya_saaya": {"page_title": "Yamabuki_Saaya", "english_name": "Yamabuki Saaya", "band": "popipa", "color_template": "Saaya"},
    "char_sakiko_sakiko": {"page_title": "Togawa_Sakiko", "english_name": "Togawa Sakiko", "band": "ave", "portrait_strategy": "page", "color_template": "Oblivionis"},
    "char_sayo_sayo": {"page_title": "Hikawa_Sayo", "english_name": "Hikawa Sayo", "band": "roselia", "color_template": "Sayo"},
    "char_soyo_soyo": {"page_title": "Nagasaki_Soyo", "english_name": "Nagasaki Soyo", "band": "mygo", "color_template": "Soyo"},
    "char_tae_tae": {"page_title": "Hanazono_Tae", "english_name": "Hanazono Tae", "band": "popipa", "color_template": "Tae"},
    "char_taki_taki": {"page_title": "Shiina_Taki", "english_name": "Shiina Taki", "band": "mygo", "color_template": "Taki"},
    "char_tomoe_tomoe": {"page_title": "Udagawa_Tomoe", "english_name": "Udagawa Tomoe", "band": "afglo", "color_template": "Tomoe"},
    "char_tomori_tomori": {"page_title": "Takamatsu_Tomori", "english_name": "Takamatsu Tomori", "band": "mygo", "color_template": "Tomori"},
    "char_touko_touko": {"page_title": "Kirigaya_Touko", "english_name": "Kirigaya Touko", "band": "morfo", "color_template": "Touko"},
    "char_tsugumi_tsugumi": {"page_title": "Hazawa_Tsugumi", "english_name": "Hazawa Tsugumi", "band": "afglo", "color_template": "Tsugumi"},
    "char_tsukushi_tsukushi": {"page_title": "Futaba_Tsukushi", "english_name": "Futaba Tsukushi", "band": "morfo", "color_template": "Tsukushi"},
    "char_uika_uika": {"page_title": "Misumi_Uika", "english_name": "Misumi Uika", "band": "ave", "portrait_strategy": "page", "color_template": "Doloris"},
    "char_umiri_umiri": {"page_title": "Yahata_Umiri", "english_name": "Yahata Umiri", "band": "ave", "portrait_strategy": "page", "color_template": "Timoris"},
    "char_yukina_yukina": {"page_title": "Minato_Yukina", "english_name": "Minato Yukina", "band": "roselia", "color_template": "Yukina"},
}

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}


@lru_cache(maxsize=1)
def load_asset_manifest() -> dict[str, dict[str, str]]:
    if not ASSET_MANIFEST.exists():
        return {}
    return json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))


def localize_image_url(url: str) -> str:
    if not url:
        return url
    for item in load_asset_manifest().values():
        if item.get("source") == url:
            return item.get("local", url)
    return url


def fetch_json(params: dict[str, Any]) -> dict[str, Any]:
    for _ in range(3):
        try:
            response = requests.get(FANDOM_API, params=params, headers=USER_AGENT, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception:
            continue
    raise RuntimeError(f"Failed fandom API call: {params}")


@lru_cache(maxsize=None)
def parse_page_html(title: str) -> str:
    data = fetch_json(
        {
            "action": "parse",
            "page": title,
            "prop": "text",
            "formatversion": "2",
            "format": "json",
        }
    )
    if "parse" not in data:
        raise KeyError(f"Missing page: {title}")
    return data["parse"]["text"]


@lru_cache(maxsize=None)
def page_soup(title: str) -> BeautifulSoup:
    return BeautifulSoup(parse_page_html(title), "html.parser")


def clean_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def strip_markdown_heading(markdown_text: str) -> str:
    text = clean_text(markdown_text)
    text = re.sub(r"^# .*\n+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_profile_language(label: str) -> str | None:
    normalized = clean_text(label).lower()
    if "中文" in label or normalized == "chinese":
        return "zh"
    if "english" in normalized:
        return "en"
    if "日本語" in label or "日本语" in label or normalized == "japanese":
        return "ja"
    return None


def parse_personality_profile(markdown_text: str, fallback_full_name: str, fallback_english_name: str) -> dict[str, dict[str, str]]:
    names = {
        "zh": fallback_full_name,
        "en": fallback_english_name,
        "ja": fallback_full_name,
    }
    descriptions = {
        "zh": "",
        "en": "",
        "ja": "",
    }

    current_lang: str | None = None
    current_lines: list[str] = []

    def flush_section() -> None:
        nonlocal current_lang, current_lines
        if current_lang:
            descriptions[current_lang] = clean_text("\n".join(current_lines))
        current_lines = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            if current_lang and current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue

        if line.startswith("# "):
            continue

        name_match = re.match(r"-\s*(中文名|English Name|日本語名|日本语名)\s*[:：]\s*(.+)$", line)
        if name_match:
            lang = normalize_profile_language(name_match.group(1))
            if lang:
                names[lang] = clean_text(name_match.group(2))
            continue

        section_match = re.match(r"##\s*(.+)$", line)
        if section_match:
            flush_section()
            current_lang = normalize_profile_language(section_match.group(1))
            continue

        if current_lang:
            current_lines.append(line)

    flush_section()

    for lang in ("zh", "en", "ja"):
        if not descriptions[lang]:
            descriptions[lang] = descriptions["zh"] or descriptions["en"] or descriptions["ja"]

    if not names["ja"]:
        names["ja"] = names["zh"]

    return {
        "names": names,
        "descriptions": descriptions,
    }


def load_questions() -> dict[str, dict[str, Any]]:
    payload = {}
    for lang, path in QUESTION_BANK_FILES.items():
        payload[lang] = json.loads(path.read_text(encoding="utf-8"))
    return payload


def normalize_image_url(tag: Any) -> str:
    return tag.get("data-src") or tag.get("src") or ""


def extract_characters_page_portraits() -> dict[str, str]:
    soup = page_soup("Characters")
    portraits: dict[str, str] = {}
    for card in soup.select("div.mp_char_container div.mp_char_bg"):
        anchor = card.select_one("div.mp_char_name a")
        image = card.select_one("div.mp_char_img img")
        if not anchor or not image:
            continue
        title = unquote(anchor.get("href", "").split("/wiki/")[-1])
        if title:
            portraits[title] = normalize_image_url(image)
    return portraits


def choose_page_portrait(page_title: str) -> str:
    soup = page_soup(page_title)
    ranked: list[tuple[int, str]] = []
    for image in soup.select("img.pi-image-thumbnail"):
        alt = (image.get("alt") or "").lower()
        name = (image.get("data-image-name") or "").lower()
        score = 0
        if "live2d" in alt or "live2d" in name:
            score += 400
        if "casual" in alt or "casual" in name:
            score += 80
        if "original" in alt or "original" in name:
            score += 60
        if "anime" in alt or "anime" in name:
            score += 40
        if "manga" in alt or "manga" in name:
            score += 20
        ranked.append((score, normalize_image_url(image)))
    if not ranked:
        raise KeyError(f"No portrait found for {page_title}")
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def extract_band_assets(page_title: str) -> dict[str, str]:
    soup = page_soup(page_title)
    logo_url = ""
    icon_url = ""
    for image in soup.select("img"):
        alt = (image.get("alt") or "").lower()
        name = (image.get("data-image-name") or "").lower()
        src = normalize_image_url(image)
        if not logo_url and "logo" in alt + " " + name and "white outline" not in alt + " " + name:
            logo_url = src
        if not icon_url and ("icon_" in name or name.startswith("icon ") or " icon." in name or alt.startswith("icon ")):
            icon_url = src
    if not logo_url:
        for image in soup.select("img"):
            alt = (image.get("alt") or "").lower()
            name = (image.get("data-image-name") or "").lower()
            if "logo" in alt + " " + name:
                logo_url = normalize_image_url(image)
                break
    if not icon_url:
        icon_url = logo_url
    return {
        "logo": localize_image_url(logo_url),
        "icon": localize_image_url(icon_url),
        "page_url": f"{FANDOM_WIKI}{page_title}",
    }


@lru_cache(maxsize=None)
def extract_color_from_template(template_name: str) -> str:
    data = fetch_json(
        {
            "action": "query",
            "prop": "revisions",
            "titles": f"Template:{template_name}",
            "rvslots": "main",
            "rvprop": "content",
            "formatversion": "2",
            "format": "json",
        }
    )
    page = data["query"]["pages"][0]
    revisions = page.get("revisions") or []
    if not revisions:
        raise KeyError(f"Missing template revision for {template_name}")
    content = revisions[0]["slots"]["main"]["content"]
    match = re.search(r"color:\s*(#[0-9A-Fa-f]{6})", content)
    if not match:
        raise ValueError(f"No color found in template {template_name}")
    return match.group(1).upper()


def build_band_assets() -> dict[str, dict[str, str]]:
    assets = {}
    for band_key, page_title in BAND_PAGES.items():
        assets[band_key] = extract_band_assets(page_title)
    assets["sumimi"]["icon"] = assets["sumimi"]["logo"]
    assets.update(SPECIAL_BAND_ASSETS)
    return assets


def build_character_record(folder_name: str, portraits_from_characters: dict[str, str], band_assets: dict[str, dict[str, str]]) -> dict[str, Any]:
    folder = DOSSIERS / folder_name
    config = CHARACTER_CONFIG[folder_name]
    mbti = json.loads((folder / "mbti_answers.json").read_text(encoding="utf-8"))
    profile = parse_personality_profile(
        (folder / "personality_description.md").read_text(encoding="utf-8"),
        fallback_full_name=mbti["character_name"],
        fallback_english_name=config["english_name"],
    )

    portrait = portraits_from_characters.get(config["page_title"], "")
    if config.get("portrait_strategy") == "page" or not portrait:
        portrait = choose_page_portrait(config.get("portrait_page_title", config["page_title"]))

    if folder_name in SPECIAL_COLORS:
        color = SPECIAL_COLORS[folder_name]
    else:
        color = extract_color_from_template(config["color_template"])

    band_key = config["band"]
    band = band_assets[band_key]
    return {
        "id": folder_name,
        "pageTitle": config["page_title"],
        "pageUrl": "",
        "englishName": profile["names"]["en"],
        "japaneseName": profile["names"]["ja"],
        "displayName": mbti["display_name"],
        "fullName": profile["names"]["zh"],
        "names": profile["names"],
        "bandKey": band_key,
        "bandName": BAND_NAMES[band_key],
        "type": mbti["type"],
        "percentages": mbti["percentages"],
        "color": color,
        "portraitUrl": localize_image_url(portrait),
        "description": profile["descriptions"]["zh"],
        "descriptions": profile["descriptions"],
        "bandLogoUrl": localize_image_url(band["logo"]),
        "bandIconUrl": localize_image_url(band["icon"]),
        "bandPageUrl": "",
    }


def build_payload() -> dict[str, Any]:
    questions = load_questions()
    portraits = extract_characters_page_portraits()
    band_assets = build_band_assets()

    characters = []
    for folder_name in sorted(CHARACTER_CONFIG):
        characters.append(build_character_record(folder_name, portraits, band_assets))

    return {
        "meta": {
            "title": "BanG Dream! MBTI Character Match Test",
            "ojtsSource": "https://openpsychometrics.org/tests/OJTS/",
            "ojtsLicense": "CC BY-NC-SA 4.0",
            "referenceSite": "https://jcver.github.io/Gakumas-idolmaster-MBTI-test/",
            "fandomCharacters": "https://bandori.fandom.com/wiki/Characters",
            "fandomColorCodes": "https://bandori.fandom.com/wiki/Category:Character_Color_Codes",
            "fandomWiki": "https://bandori.fandom.com/wiki/BanG_Dream!_Wikia",
            "copyrightNotice": "版权声明：页面中使用的 BanG Dream! 相关素材版权归 Bushiroad 所有，仅用于非商业角色性格拟合展示。",
        },
        "questions": questions,
        "bands": band_assets,
        "characters": characters,
    }


def main() -> None:
    payload = build_payload()
    script = "window.BANGDREAM_MBTI_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(script, encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
