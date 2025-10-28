import csv
import os
import re
import ast
import sys
from typing import List, Tuple, Optional

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


def find_poem(dataset: List[Tuple[str, List[float]]], search: str) -> Optional[Tuple[str, List[float]]]:
    """Find poem by partial case-insensitive title match."""
    search_lower = search.lower()
    for title, vec in dataset:
        if search_lower in title.lower():
            return (title, vec)
    return None


def main(titles: List[str], style: str | None = None, color_scheme: str = 'expressive'):
    os.makedirs(OUT_DIR, exist_ok=True)
    dataset = load_dataset(CSV_PATH)
    if not dataset:
        print(f"No data loaded from {CSV_PATH}")
        return 1

    print(f"Loaded {len(dataset)} poems from dataset.")
    print(f"Rendering {len(titles)} specified poems with '{color_scheme}' color scheme...\n")

    found = 0
    missing = []
    
    for search_title in titles:
        result = find_poem(dataset, search_title)
        if not result:
            missing.append(search_title)
            print(f"⚠ Not found: '{search_title}'")
            continue
        
        title, vec = result
        params = map_embedding_to_params(vec, color_scheme=color_scheme)
        params = apply_user_style_bias(params, style)
        img = render(params)

        palette = params.get('palette_name', 'palette')
        slug = slugify(title)
        style_tag = (style or 'regular').lower()
        scheme_tag = color_scheme if color_scheme != 'expressive' else ''
        out_name = f"{slug}_{palette}_{style_tag}"
        if scheme_tag:
            out_name += f"_{scheme_tag}"
        out_path = os.path.join(OUT_DIR, f"{out_name}.png")
        img.save(out_path)
        print(f"✓ Saved -> {out_path}")
        found += 1

    print(f"\n{found}/{len(titles)} poems rendered successfully.")
    if missing:
        print(f"Missing: {', '.join(missing)}")
    return 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Render specific poems by title')
    parser.add_argument('titles', nargs='+', help='Poem titles to render (partial match OK)')
    parser.add_argument('--style', type=str, default=None, help="Optional style bias: 'sharp' or 'preferred'")
    parser.add_argument('--color-scheme', type=str, default='expressive', help="Color scheme: 'very_smooth', 'expressive', or 'wild'")
    args = parser.parse_args()

    raise SystemExit(main(titles=args.titles, style=args.style, color_scheme=args.color_scheme))
