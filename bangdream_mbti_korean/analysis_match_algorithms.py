from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
SITE_DATA = ROOT / "site" / "site-data.js"
OUT_DISTRIBUTION = ROOT / "analysis_character_distribution.png"
OUT_ALGORITHMS = ROOT / "analysis_algorithm_comparison.png"
OUT_SUMMARY = ROOT / "analysis_algorithm_summary.json"

AXES = ["EI", "SN", "FT", "JP"]
BAND_ORDER = ["popipa", "afglo", "pasupare", "roselia", "hhw", "morfo", "ras", "mygo", "ave", "sumimi", "bangdream"]
POLE_ORDER = ["E", "S", "T", "J", "I", "N", "F", "P"]
USER_STRETCH_POWER = 0.7
CHARACTER_SHRINK = 0.85
DIRECTION_WEIGHT = 0.7
EXTREMENESS_WEIGHT = 2.0

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "MS Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load_payload() -> dict:
    text = SITE_DATA.read_text(encoding="utf-8")
    prefix = "window.BANGDREAM_MBTI_DATA = "
    if not text.startswith(prefix):
        raise ValueError("Unexpected site-data.js format")
    body = text[len(prefix):].rstrip()
    if body.endswith(";"):
        body = body[:-1]
    return json.loads(body)


def signed_axes(percentages: dict[str, float]) -> np.ndarray:
    return np.array(
        [
            (percentages["E"] - percentages["I"]) / 100,
            (percentages["S"] - percentages["N"]) / 100,
            (percentages["F"] - percentages["T"]) / 100,
            (percentages["J"] - percentages["P"]) / 100,
        ],
        dtype=float,
    )


def signed_to_percentages(users4: np.ndarray) -> np.ndarray:
    e = (users4[:, 0] + 1) * 50
    s = (users4[:, 1] + 1) * 50
    f = (users4[:, 2] + 1) * 50
    j = (users4[:, 3] + 1) * 50
    i = 100 - e
    n = 100 - s
    t = 100 - f
    p = 100 - j
    return np.stack([e, s, t, j, i, n, f, p], axis=1)


def pca_2d(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    return centered @ vt[:2].T


def weighted_entropy(shares: np.ndarray) -> float:
    nonzero = shares[shares > 0]
    return float(-(nonzero * np.log(nonzero)).sum())


def effective_count(shares: np.ndarray) -> float:
    return float(np.exp(weighted_entropy(shares)))


def signed_power(values: np.ndarray, power: float) -> np.ndarray:
    return np.sign(values) * np.power(np.abs(values), power)


def score_current_linear(users4: np.ndarray, chars4: np.ndarray, chars8: np.ndarray, axis_std: np.ndarray) -> np.ndarray:
    user8 = signed_to_percentages(users4)
    diffs = user8[:, None, :] - chars8[None, :, :]
    return -np.sqrt((diffs * diffs).sum(axis=2))


def score_four_linear(users4: np.ndarray, chars4: np.ndarray, chars8: np.ndarray, axis_std: np.ndarray) -> np.ndarray:
    diffs = users4[:, None, :] - chars4[None, :, :]
    return -np.sqrt((diffs * diffs).sum(axis=2))


def score_four_gaussian(users4: np.ndarray, chars4: np.ndarray, chars8: np.ndarray, axis_std: np.ndarray) -> np.ndarray:
    sigma = 0.40
    diffs = users4[:, None, :] - chars4[None, :, :]
    sims = np.exp(-((diffs * diffs) / (2 * sigma * sigma)))
    return sims.mean(axis=2)


def score_four_gaussian_penalized(users4: np.ndarray, chars4: np.ndarray, chars8: np.ndarray, axis_std: np.ndarray) -> np.ndarray:
    sigma = 0.35
    diffs = users4[:, None, :] - chars4[None, :, :]
    sims = np.exp(-((diffs * diffs) / (2 * sigma * sigma)))
    weights = 0.6 + 0.4 * np.maximum(np.abs(users4[:, None, :]), np.abs(chars4[None, :, :]))
    mismatch = np.sign(users4[:, None, :]) != np.sign(chars4[None, :, :])
    active = mismatch & (np.abs(users4[:, None, :]) > 0.12) & (np.abs(chars4[None, :, :]) > 0.12)
    sims = np.where(active, sims * 0.35, sims)
    return (sims * weights).sum(axis=2) / weights.sum(axis=2)


def score_four_balanced(users4: np.ndarray, chars4: np.ndarray, chars8: np.ndarray, axis_std: np.ndarray) -> np.ndarray:
    sigma = 0.85
    scaled_diffs = (users4[:, None, :] - chars4[None, :, :]) / axis_std[None, None, :]
    sims = np.exp(-((scaled_diffs * scaled_diffs) / (2 * sigma * sigma)))
    weights = 0.55 + 0.45 * np.maximum(np.abs(users4[:, None, :]), np.abs(chars4[None, :, :]))
    mismatch = np.sign(users4[:, None, :]) != np.sign(chars4[None, :, :])
    active = mismatch & (np.abs(users4[:, None, :]) > 0.12) & (np.abs(chars4[None, :, :]) > 0.12)
    sims = np.where(active, sims * 0.45, sims)
    type_bonus = (
        (np.sign(users4[:, None, :]) == np.sign(chars4[None, :, :]))
        .sum(axis=2)
        .astype(float)
        / chars4.shape[1]
    ) * 0.05
    return (sims * weights).sum(axis=2) / weights.sum(axis=2) + type_bonus


def score_directional_stretched(users4: np.ndarray, chars4: np.ndarray, chars8: np.ndarray, axis_std: np.ndarray) -> np.ndarray:
    users_transformed = signed_power(users4, USER_STRETCH_POWER)
    chars_transformed = chars4 * CHARACTER_SHRINK

    dot = users_transformed @ chars_transformed.T
    user_norm = np.linalg.norm(users_transformed, axis=1, keepdims=True)
    char_norm = np.linalg.norm(chars_transformed, axis=1, keepdims=True).T
    cosine = dot / np.maximum(user_norm * char_norm, 1e-9)
    direction_score = (np.clip(cosine, -1, 1) + 1) / 2

    diffs = np.abs(users_transformed[:, None, :] - chars_transformed[None, :, :])
    closeness = np.clip(1 - diffs / 2, 0, 1)
    weights = 1 + np.maximum(np.abs(users_transformed[:, None, :]), np.abs(chars_transformed[None, :, :])) * EXTREMENESS_WEIGHT
    axis_closeness = (closeness * weights).sum(axis=2) / weights.sum(axis=2)

    return direction_score * DIRECTION_WEIGHT + axis_closeness * (1 - DIRECTION_WEIGHT)


ALGORITHMS = {
    "current_linear_8d": score_current_linear,
    "four_linear": score_four_linear,
    "four_gaussian": score_four_gaussian,
    "four_gaussian_penalized": score_four_gaussian_penalized,
    "four_balanced": score_four_balanced,
    "directional_stretched": score_directional_stretched,
}


def analyze_top_matches(scores: np.ndarray, ids: list[str]) -> dict:
    winners = scores.argmax(axis=1)
    counts = Counter(ids[index] for index in winners)
    shares = np.array([counts.get(char_id, 0) for char_id in ids], dtype=float) / scores.shape[0]
    top = [
        {"id": char_id, "share": round(counts[char_id] / scores.shape[0], 4)}
        for char_id, _ in counts.most_common(8)
    ]
    return {
        "max_share": float(shares.max()),
        "effective_count": effective_count(shares),
        "winners_used": int((shares > 0).sum()),
        "top_winners": top,
    }


def main() -> None:
    payload = load_payload()
    characters = payload["characters"]

    ids = [character["id"] for character in characters]
    names = [character["names"]["zh"] for character in characters]
    bands = [character["bandKey"] for character in characters]
    chars4 = np.stack([signed_axes(character["percentages"]) for character in characters], axis=0)
    chars8 = np.stack(
        [
            np.array([character["percentages"][pole] for pole in POLE_ORDER], dtype=float)
            for character in characters
        ],
        axis=0,
    )

    palette = list(plt.cm.tab10.colors) + list(plt.cm.Set3.colors)
    band_palette = dict(zip(BAND_ORDER, palette[: len(BAND_ORDER)]))
    coords = pca_2d(chars4)
    mean4 = chars4.mean(axis=0)
    axis_std = chars4.std(axis=0) + 0.15

    rng = np.random.default_rng(42)
    users_uniform = rng.uniform(-1, 1, size=(80000, 4))
    users_mean = np.clip(rng.normal(loc=mean4, scale=0.18, size=(30000, 4)), -1, 1)
    average_point = mean4[None, :]

    summary: dict[str, object] = {
        "character_count": len(characters),
        "mean_point": {
            axis: round(float(value), 4)
            for axis, value in zip(AXES, mean4)
        },
        "algorithms": {},
    }

    comparison_rows = []
    for key, scorer in ALGORITHMS.items():
        uniform_scores = scorer(users_uniform, chars4, chars8, axis_std)
        mean_scores = scorer(users_mean, chars4, chars8, axis_std)
        avg_scores = scorer(average_point, chars4, chars8, axis_std)[0]
        avg_index = int(avg_scores.argmax())
        uniform_stats = analyze_top_matches(uniform_scores, ids)
        mean_stats = analyze_top_matches(mean_scores, ids)
        summary["algorithms"][key] = {
            "average_point_best": {
                "id": ids[avg_index],
                "name_zh": names[avg_index],
                "band": bands[avg_index],
            },
            "uniform": uniform_stats,
            "mean_centered": mean_stats,
        }
        comparison_rows.append(
            {
                "algorithm": key,
                "uniform_max_share": uniform_stats["max_share"],
                "uniform_effective_count": uniform_stats["effective_count"],
                "mean_max_share": mean_stats["max_share"],
                "mean_effective_count": mean_stats["effective_count"],
            }
        )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=160)
    ax = axes[0]
    for band in BAND_ORDER:
        mask = np.array([item == band for item in bands])
        if not mask.any():
            continue
        ax.scatter(coords[mask, 0], coords[mask, 1], s=48, alpha=0.8, label=band, color=band_palette[band])
    for x, y, name in zip(coords[:, 0], coords[:, 1], names):
        ax.text(x + 0.01, y + 0.01, name, fontsize=7, alpha=0.8)
    mean_coord = pca_2d(np.vstack([chars4, mean4]))[-1]
    ax.scatter([mean_coord[0]], [mean_coord[1]], marker="X", s=180, color="black", label="mean point")
    ax.set_title("49 characters in signed 4-axis space (PCA 2D)")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(loc="best", fontsize=8, ncol=2)

    ax = axes[1]
    for index, axis in enumerate(AXES):
        color = palette[index]
        ax.hist(
            chars4[:, index],
            bins=14,
            range=(-1, 1),
            histtype="step",
            linewidth=2,
            color=color,
            label=axis,
        )
        ax.axvline(mean4[index], linestyle="--", linewidth=1, color=color)
    ax.set_title("Axis density of the 49 characters")
    ax.set_xlabel("signed axis value")
    ax.set_xlim(-1, 1)
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUT_DISTRIBUTION, bbox_inches="tight")
    plt.close(fig)

    labels = [row["algorithm"] for row in comparison_rows]
    x = np.arange(len(labels))
    width = 0.36

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=160)
    ax = axes[0]
    ax.bar(x - width / 2, [row["uniform_max_share"] for row in comparison_rows], width, label="uniform users")
    ax.bar(x + width / 2, [row["mean_max_share"] for row in comparison_rows], width, label="mean-centered users")
    ax.set_title("Top-1 concentration (lower is better)")
    ax.set_ylabel("share of most frequent winner")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()

    ax = axes[1]
    ax.bar(x - width / 2, [row["uniform_effective_count"] for row in comparison_rows], width, label="uniform users")
    ax.bar(x + width / 2, [row["mean_effective_count"] for row in comparison_rows], width, label="mean-centered users")
    ax.set_title("Effective number of top-1 winners (higher is better)")
    ax.set_ylabel("exp(entropy)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUT_ALGORITHMS, bbox_inches="tight")
    plt.close(fig)

    print(f"wrote {OUT_DISTRIBUTION.name}")
    print(f"wrote {OUT_ALGORITHMS.name}")
    print(f"wrote {OUT_SUMMARY.name}")
    print()
    print("Average point winners:")
    for key, item in summary["algorithms"].items():
        best = item["average_point_best"]
        print(f"  {key}: {best['name_zh']} ({best['id']})")
    print()
    print("Uniform-user concentration:")
    for row in comparison_rows:
        print(
            "  "
            f"{row['algorithm']}: max_share={row['uniform_max_share']:.3f}, "
            f"effective_count={row['uniform_effective_count']:.2f}"
        )


if __name__ == "__main__":
    main()
