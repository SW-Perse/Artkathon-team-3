import csv
import os
import re
import ast
import random
import sys
import glob
from typing import List, Tuple

# Ensure project root is on sys.path for absolute imports
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.render_embedding import map_embedding_to_params, apply_user_style_bias
from tools.flow_field import render


CSV_PATH = os.path.join('data', 'poem_vectors_simple.csv')
OUT_DIR = 'out'


def slugify(text: str, max_len: int = 60) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip('_')
    if len(text) > max_len:
        text = text[:max_len].rstrip('_')
    return text or 'untitled'


def load_dataset(csv_path: str) -> List[Tuple[str, List[float]]]:
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('title', '').strip()
            vec_str = row.get('vector_14d', '').strip()
            if not title or not vec_str:
                continue
            try:
                vec = ast.literal_eval(vec_str)
                if isinstance(vec, list) and len(vec) == 14:
                    rows.append((title, vec))
            except Exception:
                continue
    return rows


def pick_random(rows: List[Tuple[str, List[float]]], n: int = 6, seed: int | None = None):
    if seed is not None:
        random.seed(seed)
    if n >= len(rows):
        return rows
    return random.sample(rows, n)


def _existing_index_and_slugs(out_dir: str) -> tuple[int, set[str]]:
    """Determine next file index and collect existing title slugs from out_dir.

    Expects filenames like 'NN_slug_palette_style.png'.
    """
    max_idx = 0
    slugs: set[str] = set()
    for path in glob.glob(os.path.join(out_dir, '*.png')):
        base = os.path.basename(path)
        # Match number, slug (greedy), palette, style
        m = re.match(r'^(\d{2})_(.+)_([A-Za-z]+)_(?:regular|sharp|preferred)\.png$', base)
        if m:
            try:
                idx = int(m.group(1))
                if idx > max_idx:
                    max_idx = idx
                slugs.add(m.group(2))
            except ValueError:
                continue
    return (max_idx + 1 if max_idx >= 0 else 1, slugs)


def main(n: int = 6, style: str | None = None, seed: int | None = None, start_index: int | None = None, color_scheme: str = 'expressive'):
    os.makedirs(OUT_DIR, exist_ok=True)
    dataset = load_dataset(CSV_PATH)
    if not dataset:
        print(f"No data loaded from {CSV_PATH}")
        return 1

    # Determine next index and avoid duplicates by slug
    next_idx, existing_slugs = _existing_index_and_slugs(OUT_DIR)
    if start_index is None:
        start_index = next_idx

    remaining = [(t, v) for (t, v) in dataset if slugify(t) not in existing_slugs]
    source = remaining if len(remaining) >= n else dataset

    picks = pick_random(source, n=n, seed=seed)
    print(f"Selected {len(picks)} random poems (seed={seed}) from {len(source)} candidates (total={len(dataset)}). Starting at index {start_index:02d}.")

    for i, (title, vec) in enumerate(picks):
        params = map_embedding_to_params(vec, color_scheme=color_scheme)
        params = apply_user_style_bias(params, style)
        img = render(params)

        palette = params.get('palette_name', 'palette')
        slug = slugify(title)
        style_tag = (style or 'regular').lower()
        out_idx = start_index + i
        out_path = os.path.join(OUT_DIR, f"{out_idx:02d}_{slug}_{palette}_{style_tag}.png")
        img.save(out_path)
        print(f"Saved -> {out_path}")

    return 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Render N random poems from CSV dataset')
    parser.add_argument('--n', type=int, default=6, help='Number of random poems to render')
    parser.add_argument('--style', type=str, default=None, help="Optional style bias: 'sharp' or 'preferred'")
    parser.add_argument('--seed', type=int, default=None, help='Optional RNG seed for reproducibility')
    parser.add_argument('--start-index', type=int, default=None, help='Optional starting index for filenames (auto-detected if omitted)')
    parser.add_argument('--color-scheme', type=str, default='expressive', help="Color scheme: 'very_smooth', 'expressive', or 'wild'")
    args = parser.parse_args()

    raise SystemExit(main(n=args.n, style=args.style, seed=args.seed, start_index=args.start_index, color_scheme=args.color_scheme))
