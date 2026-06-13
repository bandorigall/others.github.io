from __future__ import annotations

import hashlib
import imghdr
import io
import json
import mimetypes
import os
import re
import subprocess
import tempfile
from pathlib import Path
from shutil import which
from typing import Any
from urllib.parse import urlparse

import requests
from PIL import Image


ROOT = Path(__file__).resolve().parent
SITE_DATA_PATH = ROOT / "site" / "site-data.js"
ASSET_ROOT = ROOT / "site" / "assets" / "images"
MANIFEST_PATH = ROOT / "site" / "assets" / "asset-manifest.json"
URL_PREFIX = "window.BANGDREAM_MBTI_DATA = "
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    )
}
SESSION = requests.Session()
SESSION.trust_env = False


def load_payload() -> dict[str, Any]:
    text = SITE_DATA_PATH.read_text(encoding="utf-8").lstrip("\ufeff")
    if not text.startswith(URL_PREFIX):
        raise ValueError("Unexpected site-data.js format")
    payload = text[len(URL_PREFIX):].rstrip()
    if payload.endswith(";"):
        payload = payload[:-1]
    return json.loads(payload)


def dump_payload(payload: dict[str, Any]) -> None:
    script = f"{URL_PREFIX}{json.dumps(payload, ensure_ascii=False, indent=2)};\n"
    SITE_DATA_PATH.write_text(script, encoding="utf-8")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def infer_suffix(url: str, content_type: str | None, content: bytes | None = None) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}:
        return suffix
    if content:
        stripped = content.lstrip()
        if stripped.startswith(b"<svg") or stripped.startswith(b"<?xml") and b"<svg" in stripped[:512]:
            return ".svg"
        detected = imghdr.what(None, h=content)
        if detected == "jpeg":
            return ".jpg"
        if detected:
            return f".{detected}"
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if guessed == ".jpe":
        return ".jpg"
    return guessed or ".bin"


def is_svg_content(content: bytes, content_type: str | None) -> bool:
    text = content.lstrip()
    if (content_type or "").split(";")[0].strip() == "image/svg+xml":
        return True
    return text.startswith(b"<svg") or (text.startswith(b"<?xml") and b"<svg" in text[:512])


def find_chrome() -> str | None:
    candidates = [
        which("chrome"),
        which("chrome.exe"),
        which("msedge"),
        which("msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def svg_bytes_to_png(content: bytes) -> bytes:
    browser = find_chrome()
    if not browser:
        raise RuntimeError("No Chrome/Edge executable found for SVG to PNG conversion")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        svg_path = temp_root / "source.svg"
        png_path = temp_root / "render.png"
        svg_path.write_bytes(content)
        result = subprocess.run(
            [
                browser,
                "--headless",
                "--disable-gpu",
                "--default-background-color=00000000",
                "--window-size=1400,800",
                f"--screenshot={png_path}",
                str(svg_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 or not png_path.exists():
            raise RuntimeError(f"Failed to convert SVG via browser: {result.stderr.strip()}")
        return png_path.read_bytes()


def normalize_to_png(content: bytes, content_type: str | None) -> bytes:
    if is_svg_content(content, content_type):
        return svg_bytes_to_png(content)

    image = Image.open(io.BytesIO(content))
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def fetch_file(url: str) -> tuple[bytes, str | None]:
    response = SESSION.get(url, headers=HEADERS, timeout=45)
    response.raise_for_status()
    return response.content, response.headers.get("Content-Type")


def download_file(content: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)


def build_filename(kind: str, key: str, url: str, suffix: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{slugify(kind)}-{slugify(key)}-{digest}{suffix}"


def main() -> None:
    payload = load_payload()
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict[str, str]] = {}
    cache: dict[str, str] = {}

    for band_key, band in payload["bands"].items():
        for field in ("logo", "icon"):
            url = band[field]
            if not isinstance(url, str) or not url.startswith("http"):
                continue
            if url not in cache:
                content, content_type = fetch_file(url)
                png_content = normalize_to_png(content, content_type)
                filename = build_filename(f"band-{field}", band_key, url, ".png")
                destination = ASSET_ROOT / "bands" / filename
                if not destination.exists():
                    download_file(png_content, destination)
                cache[url] = f"./assets/images/bands/{filename}"
            band[field] = cache[url]
            manifest[f"band:{band_key}:{field}"] = {"source": url, "local": cache[url]}

    for character in payload["characters"]:
        for field in ("portraitUrl", "bandLogoUrl", "bandIconUrl"):
            url = character.get(field)
            if not isinstance(url, str) or not url.startswith("http"):
                continue
            if url not in cache:
                content, content_type = fetch_file(url)
                png_content = normalize_to_png(content, content_type)
                filename = build_filename(field, character["id"], url, ".png")
                folder = "characters" if field == "portraitUrl" else "bands"
                destination = ASSET_ROOT / folder / filename
                if not destination.exists():
                    download_file(png_content, destination)
                cache[url] = f"./assets/images/{folder}/{filename}"
            character[field] = cache[url]
            manifest[f"{character['id']}:{field}"] = {"source": url, "local": cache[url]}

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    dump_payload(payload)
    print(f"downloaded {len(cache)} unique assets")
    print(f"updated {SITE_DATA_PATH}")
    print(f"wrote {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
