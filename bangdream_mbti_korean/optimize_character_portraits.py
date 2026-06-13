from __future__ import annotations

import io
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
CHARACTER_DIR = ROOT / "site" / "assets" / "images" / "characters"
MAX_WIDTH = 420
MAX_HEIGHT = 656
PALETTE_COLORS = 192


def fit_size(width: int, height: int) -> tuple[int, int]:
    scale = min(MAX_WIDTH / width, MAX_HEIGHT / height, 1)
    return max(1, round(width * scale)), max(1, round(height * scale))


def optimize_image(path: Path) -> tuple[int, int]:
    before = path.stat().st_size

    with Image.open(path) as image:
        image = image.convert("RGBA")
        target_size = fit_size(image.width, image.height)
        if target_size != image.size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)

        quantized = image.quantize(colors=PALETTE_COLORS, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
        output = io.BytesIO()
        quantized.save(output, format="PNG", optimize=True)
        path.write_bytes(output.getvalue())

    after = path.stat().st_size
    return before, after


def main() -> None:
    files = sorted(CHARACTER_DIR.glob("*.png"))
    total_before = 0
    total_after = 0

    for path in files:
        before, after = optimize_image(path)
        total_before += before
        total_after += after
        print(f"{path.name}: {before} -> {after}")

    saved = total_before - total_after
    ratio = (saved / total_before * 100) if total_before else 0
    print()
    print(f"optimized {len(files)} portraits")
    print(f"total_before={total_before}")
    print(f"total_after={total_after}")
    print(f"saved={saved} ({ratio:.2f}%)")


if __name__ == "__main__":
    main()
