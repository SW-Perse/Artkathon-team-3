"""
Master pipeline for Artkathon: Text → 14D Vector → Flow Field Art

This script ties together all components:
1. Load poem dataset (CSV or Excel)
2. Convert each poem to 14D semantic vector
3. Render each poem as flow-field artwork
4. Save outputs organized by genre/palette
"""

import sys
import os
import ast
import pandas as pd
import numpy as np
from pathlib import Path
import re
from tools.flow_field import render
from tools.render_embedding import map_embedding_to_params, apply_user_style_bias

# Import vector generation from tools
sys.path.insert(0, str(Path(__file__).parent / 'tools'))
from simple_text_to_vectors import simple_text_to_vectors


def load_dataset(path="data/poem_vectors_simple.csv"):
    """
    Load poem dataset from CSV or Excel.
    
    Expected columns:
    - title: Poem title
    - vector_14d: Pre-computed 14D vector (optional)
    
    OR for raw poems:
    - Title: Poem title
    - Poem: Full text
    - Poet: Author name
    - Genre: Emotional category (fear/anger/sadness/love/joy/surprise)
    """
    file_path = Path(path)
    
    if not file_path.exists():
        print(f"❌ Error: Dataset not found at {path}")
        sys.exit(1)
    
    # Load based on file extension
    if file_path.suffix == '.csv':
        df = pd.read_csv(path)
    elif file_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(path)
    else:
        print(f"❌ Error: Unsupported file format {file_path.suffix}")
        sys.exit(1)
    
    print(f"📚 Dataset loaded: {len(df)} poems")
    print(f"📊 Columns: {list(df.columns)}")
    
    return df


def encode_poems_to_vectors(df):
    """
    Convert poems to 14D semantic vectors.
    
    If 'vector_14d' column exists, parse it.
    Otherwise, compute vectors from text using simple_text_to_vectors.
    """
    vectors = []
    metadata = []
    
    # Check if pre-computed vectors exist
    if 'vector_14d' in df.columns:
        print("✅ Using pre-computed vectors from 'vector_14d' column")
        
        for i, row in df.iterrows():
            try:
                # Parse vector string "[0.1, 0.2, ...]" to list
                vector_str = row['vector_14d']
                if isinstance(vector_str, str):
                    vector = ast.literal_eval(vector_str)  # Safe parsing
                else:
                    vector = vector_str
                
                vectors.append(np.array(vector))
                metadata.append({
                    'index': i,
                    'title': row.get('title', f'Poem_{i}'),
                    'genre': None  # Will be inferred from v[13]
                })
            except Exception as e:
                print(f"⚠️ Error parsing vector for row {i}: {e}")
                continue
    
    # Otherwise compute from raw text
    elif all(col in df.columns for col in ['Title', 'Poem', 'Poet', 'Genre']):
        print("🔄 Computing vectors from raw poem text...")
        
        for i, row in df.iterrows():
            try:
                vector = simple_text_to_vectors(
                    title=row['Title'],
                    poem_text=row['Poem'],
                    poet=row['Poet'],
                    genre=row['Genre']
                )
                
                vectors.append(vector)
                metadata.append({
                    'index': i,
                    'title': row['Title'],
                    'poet': row['Poet'],
                    'genre': row['Genre']
                })
                
                if (i + 1) % 100 == 0:
                    print(f"  Progress: {i+1}/{len(df)} poems vectorized")
                    
            except Exception as e:
                print(f"⚠️ Error processing poem {i} ('{row.get('Title', 'Unknown')}'): {e}")
                continue
    
    else:
        print(f"❌ Error: Dataset missing required columns")
        print(f"   Need either: 'vector_14d' OR ('Title', 'Poem', 'Poet', 'Genre')")
        sys.exit(1)
    
    print(f"✅ Vectors ready: {len(vectors)} poems encoded")
    return vectors, metadata


def slugify(text, max_length=50):
    """Convert text to filesystem-safe slug."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = slug.strip('_')
    return slug[:max_length]


def get_genre_from_vector(v):
    """Infer genre name from v[13] value."""
    genre_val = v[13]
    if genre_val < 0.2:
        return 'fear'
    elif genre_val < 0.3:
        return 'anger'
    elif genre_val < 0.4:
        return 'sadness'
    elif genre_val < 0.5:
        return 'love'
    elif genre_val < 0.6:
        return 'joy'
    elif genre_val < 0.7:
        return 'surprise'
    else:
        return 'neutral'


def render_poems(vectors, metadata, color_scheme='expressive', style=None, 
                 output_dir='out', organize_by_genre=False, limit=None):
    """
    Render all poems as flow-field artworks.
    
    Args:
        vectors: List of 14D numpy arrays
        metadata: List of dicts with title, genre info
        color_scheme: 'expressive', 'very_smooth', or 'wild'
        style: Optional style bias ('sharp', 'preferred', or None)
        output_dir: Directory to save images
        organize_by_genre: Create subdirectories per genre (default: False, flat structure)
        limit: Maximum number of poems to render (None = all)
        output_dir: Directory to save images
        organize_by_genre: Create subdirectories per genre
        limit: Maximum number of poems to render (None = all)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    if organize_by_genre:
        for genre in ['fear', 'anger', 'sadness', 'love', 'joy', 'surprise', 'neutral']:
            (output_path / genre).mkdir(exist_ok=True)
    
    total = len(vectors) if limit is None else min(limit, len(vectors))
    
    print(f"\n🎨 Starting render pipeline...")
    print(f"   Total poems: {total}")
    print(f"   Color scheme: {color_scheme}")
    print(f"   Style: {style or 'default'}")
    print(f"   Output: {output_dir}")
    print(f"   Organize by genre: {organize_by_genre}\n")
    
    for i, (vector, meta) in enumerate(zip(vectors[:total], metadata[:total])):
        try:
            # Generate parameters
            params = map_embedding_to_params(vector, color_scheme=color_scheme)
            
            if style:
                params = apply_user_style_bias(params, style)
            
            # Determine output path
            title = meta['title']
            genre = meta.get('genre') or get_genre_from_vector(vector)
            palette = params.get('palette_name', 'unknown')
            
            # Create filename
            slug = slugify(title)
            filename = f"{i+1:04d}_{slug}_{palette}.png"
            
            if organize_by_genre:
                save_path = output_path / genre / filename
            else:
                save_path = output_path / filename
            
            # Render
            print(f"[{i+1}/{total}] Rendering: {title[:40]}... (genre: {genre}, palette: {palette})")
            img = render(params)
            img.save(save_path)
            
        except Exception as e:
            print(f"❌ Error rendering poem {i+1} ('{meta['title']}'): {e}")
            continue
    
    print(f"\n✅ Pipeline complete! {total} artworks generated.")
    print(f"📁 Output directory: {output_dir}")


def main():
    """Main pipeline execution."""
    print("=" * 80)
    print("✨ ARTKATHON PIPELINE: Text → Vector → Flow Field Art")
    print("=" * 80)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Generate flow-field art from poem dataset')
    parser.add_argument('--dataset', type=str, default='data/poem_vectors_simple.csv',
                        help='Path to poem dataset (CSV or Excel)')
    parser.add_argument('--color-scheme', type=str, default='expressive',
                        choices=['expressive', 'very_smooth', 'wild'],
                        help='Color scheme to use')
    parser.add_argument('--style', type=str, default=None,
                        choices=['sharp', 'preferred', 'natural'],
                        help='Style bias (sharp, preferred, or natural)')
    parser.add_argument('--output', type=str, default='out',
                        help='Output directory')
    parser.add_argument('--organize-by-genre', action='store_true', default=False,
                        help='Create subdirectories per genre (default: flat structure)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of poems to render')
    
    args = parser.parse_args()
    
    # Step 1: Load dataset
    print("\n[STEP 1] Loading dataset...")
    df = load_dataset(args.dataset)
    
    # Step 2: Encode to vectors
    print("\n[STEP 2] Encoding poems to 14D vectors...")
    vectors, metadata = encode_poems_to_vectors(df)
    
    # Step 3: Render artworks
    print("\n[STEP 3] Rendering flow-field artworks...")
    render_poems(
        vectors=vectors,
        metadata=metadata,
        color_scheme=args.color_scheme,
        style=args.style,
        output_dir=args.output,
        organize_by_genre=args.organize_by_genre,
        limit=args.limit
    )
    
    print("\n" + "=" * 80)
    print("🎉 Pipeline completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
