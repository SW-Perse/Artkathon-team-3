# 🎨 Flow Field Art Generator from Poetry Corpus

This project is a lightweight algorithmic pipeline that transforms poems into abstract artworks guided by flow fields. Poems are converted to 14D vectors based on their linguistic features, which then control visual parameters like color, turbulence, density, and flow patterns.

The choice of flow field as a rendering method is inspired by the works of Tyler Hobbs: 
https://www.tylerxhobbs.com/words/flow-fields

Many of the poems in the corpus can be found on the Poetry Foundation website
https://www.poetryfoundation.org/

---

## The Team

### M1 AI
- Mame Yacine NDIAYE
- Imrane TITAOU LATIF

### M1 Data Engineer
- Sophie CAPRON
- Valentin FALQUET
- Yves Malick Jordan MAO
- Mama Aïssata SAKHO

---

## Quick Start

### 1. Setup
```powershell
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Art
```powershell
# Render all poems in dataset
python pipeline.py

# Test with 5 poems
python pipeline.py --limit 5

# Use different color scheme
python pipeline.py --color-scheme wild --limit 10
```

**Output**: `out/` directory with PNG images organized by genre

---

## Core Concept

### Pipeline: Text → Vector → Image

1. **Text Analysis** → Poem is analyzed for linguistic features (rhyme, rhythm, alliteration, etc.)
2. **14D Vector** → Features are encoded as 14 numbers between 0-1
3. **Parameter Mapping** → Vector values control flow field parameters
4. **Rendering** → Flow field algorithm generates abstract artwork

---

## The 14D Embedding Vector

### Vector Structure

Each poem is vectorized into exactly 14 dimensions that capture its poetic structure:

| Dimension |        Feature               |    Normalization   |          Visual Effect         |
|-----------|------------------------------|--------------------|--------------------------------|
| **v[0]**  |       Title length           |       / 10.0       | Stroke jitter (random)         |
| **v[1]**  | Title lexical complexity     |    word diversity  |        Flow fidelity           |
| **v[2]**  |        Verse count           |       / 20.0       |        Number of strokes       |
| **v[3]**  |     Average words per verse  |       / 10.0       |      Grid resolution           |
| **v[4]**  |   Verse length variability   |       / 5.0        |     Turbulence/complexity      |
| **v[5]**  |      Rhyme diversity         |  unique frequency  |    Angular quantization        |
| **v[6]**  |       Dominant rhyme         |    max frequency   |       Spiral distortion        |
| **v[7]**  |     Alliteration score       |  repeated bigrams  |        Detail layers           |
| **v[8]**  |     Vowel dominance          | dominant vowel     |       Stroke smoothing         |
| **v[9]**  |      Vowel entropy           |       / 3.0        |        Random seed             |
| **v[10]** |          Raw rhythm          |      words/verse   |      Stroke length             |
| **v[11]** |      Poet name length        |       / 5.0        |      Stroke thickness          |
| **v[12]** |      Poet name diversity     |   unique letters   |           (reserved)           |
| **v[13]** |         Genre/Emotion        |       0.0-1.0      |    **Color palette**           |

### Genre → Color Mapping

Dimension **v[13]** determines the color palette according to emotional genre:

| Genre               | v[13] Value               | Colormap | Visual Style                 |
|---------------------|---------------------------|----------|------------------------------|
| **Fear**            | 0.0 - 0.2 (center: 0.1)   | bone     | Grayscale, ominous           |
| **Anger**           | 0.2 - 0.3 (center: 0.25)  | hot      | Fire colors (red/yellow)     |
| **Sadness**         | 0.3 - 0.4 (center: 0.35)  | PuBu     | Purple-blue gradients        |
| **Love**            | 0.4 - 0.5 (center: 0.45)  | RdPu     | Red-pink-purple              |
| **Joy**             | 0.5 - 0.6 (center: 0.55)  | rainbow  | Full color spectrum          |
| **Surprise**        | 0.6 - 0.7 (center: 0.65)  | cividis  | Blue-yellow                  |

### Rendering Process

1. **Grid construction**: Create an angle grid based on image size and cell_size
2. **Flow generation**: Generate a Perlin noise field with multiple octaves
3. **Point placement**: Arrange starting points on the canvas (density parameter)
4. **Stroke drawing**: Follow flow field angles and draw colored lines
   - Color varies according to position or flow angle
   - Width tapers from thick to thin
   - Length is determined by the rhythm parameter

### Flow Field Parameters

| Parameter         | Formula             | Range     | Controls                             |
|-------------------|---------------------|-----------|--------------------------------------|
| `cell_size`       | 4 + v[3] × 8        | 4-20 px   | Grid resolution (small = detailed)   |
| `noise_scale`     | max(2, v[4] × 8)    | 2-16      | Flow complexity                      |
| `octaves`         | 3 + v[7] × 4        | 3-7       | Perlin noise layers                  |
| `seed`            | v[9] × 1000         | 0-1000    | Deterministic seed                   |
| `quantize_steps`  | v[5] × 12           | 0-12      | Sharp angles (rhymes)                |
| `swirl`           | v[6] × 0.3          | 0.0-0.3   | Spiral distortion                    |

### Stroke Parameters

| Parameter      | Formula                                 | Range         | Controls                |
|----------------|-----------------------------------------|---------------|-------------------------|
| `density`      | max(0.001, min(0.006, v[2] × 0.002))    | 0.001-0.006   | Number of strokes       |
| `max_length`   | 400 + v[10] × 20                        | 400-1400 px   | Maximum length          |
| `step_size`    | 2 + v[8] × 4                            | 2-6 px        | Stroke smoothing        |
| `angle_gain`   | 0.6 + v[1] × 0.3                        | 0.6-0.9       | Flow fidelity           |
| `jitter`       | v[0] × 0.15                             | 0.0-0.3       | Random variation        |
| `width_start`  | 6 + v[11] × 0.3                         | 6.0-6.3       | Initial thickness       |
| `width_end`    | 0.8                                     | fixed         | Final thickness         |

---

## Color Schemes

### Expressive (Default)
- **Palette axis**: Vertical (top to bottom)
- **Within-stroke variation**: High (0.5)
- **Effect**: Bold color shifts, dramatic gradients
- **Best for**: Emotional, dynamic compositions

### Very Smooth
- **Palette axis**: Horizontal (left to right)
- **Within-stroke variation**: Low (0.2)
- **Effect**: Subtle transitions, cohesive palette
- **Best for**: Calm, harmonious artworks

### Wild
- **Palette axis**: Flow field driven
- **Within-stroke variation**: Extreme (0.7)
- **Effect**: Rainbow chaos following flow angles
- **Best for**: Experimental, vibrant pieces

---

## Performance

- **Resolution**: 3000×3000 pixels
- **Render time**: ~10-15 seconds per image
- **Memory**: ~2GB RAM for large batches
- **Recommended**: Process 50-100 poems maximum at a time

---

## Quick Installation

### Clone the GitHub Repo
```powershell
git clone https://github.com/your-username/Artkathon.git
cd Artkathon
```

### Installation
```powershell
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Image Generation
```powershell
# Render all poems in dataset
python pipeline.py

# Test with 5 poems
python pipeline.py --limit 5

# Test with a different color scheme
python pipeline.py --color-scheme wild --limit 10
```

**Output**: `out/` folder containing generated images
A diverse sample has been processed and rendered using all three color schemes to be used as a demo, and can be found in the `out/` folder 

---

## Tools

### Main Pipeline (Batch Processing)

```powershell
# Basic usage
python pipeline.py

# Custom dataset
python pipeline.py --dataset path/to/poems.csv

# Color schemes
python pipeline.py --color-scheme expressive   # Bold vertical gradients (default)
python pipeline.py --color-scheme very_smooth  # Subtle horizontal gradients
python pipeline.py --color-scheme wild         # Flow-driven chaos

# Style variations
python pipeline.py --style sharp               # High contrast, turbulent
python pipeline.py --style natural             # Default rendering

# Output control
python pipeline.py --output gallery --limit 20
python pipeline.py --organize-by-genre         # Structure by genre folders
```

### Individual Tools

#### Render Specific Poems
```powershell
python tools/render_specific_poems.py "The Raven" "Fire and Ice"
python tools/render_specific_poems.py "Annabel Lee" --style sharp
```

#### Render Random Samples
```powershell
python tools/render_random_samples.py --n 10
python tools/render_random_samples.py --n 5 --seed 42 --color-scheme wild
```

---

## Advanced Usage

### Batch Process Multiple Schemes
```powershell
# Generate complete galleries with each color scheme
python pipeline.py --color-scheme expressive --output gallery_expressive
python pipeline.py --color-scheme very_smooth --output gallery_smooth
python pipeline.py --color-scheme wild --output gallery_wild
```

### Custom Vector Creation
```python
from tools.simple_text_to_vectors import simple_text_to_vectors
from tools.render_embedding import map_embedding_to_params
from tools.flow_field import render

# Create custom vector
vector = simple_text_to_vectors(
    title="My Poem",
    poem_text="Roses are red...",
    poet="Anonymous",
    genre="love"
)

# Render
params = map_embedding_to_params(vector, color_scheme='expressive')
img = render(params)
img.save('my_artwork.png')
```

---

## Project Structure

```
Artkathon/
├── pipeline.py                       # Main script
├── requirements.txt                  # Dependencies
│
├── tools/                            # Modules and utilities
│   ├── color_schemes.py              # Rendering style configurations
│   ├── flow_field.py                 # Rendering engine
│   ├── perlin.py                     # Noise generator
│   ├── render_embedding.py           # Vector → parameter mapping
│   ├── render_random_samples.py      # Random selection
│   ├── render_specific_poems.py      # Render by title
│   └── simple_text_to_vectors.py     # Text → 14D vector conversion
│
├── data/                             # Datasets
│   ├── PoemsDataset_cleaned.csv      # Full raw poems dataset
│   └── poem_vectors_simple.csv       # Pre-computed vectors (main)
│
└── out/                              # Generated images (auto-created)

```

---

## Dataset Format

### Option 1: Pre-computed Vectors (Recommended)
CSV with columns: `title`, `vector_14d`

```csv
title,vector_14d
"The Raven","[0.2, 1.0, 0.9, 0.85, 0.4, 0.3, 0.7, 0.6, 0.5, 0.7, 8.5, 0.4, 0.8, 0.1]"
"Fire and Ice","[0.3, 0.9, 0.3, 0.6, 0.2, 0.5, 0.4, 0.3, 0.6, 0.8, 6.0, 0.4, 0.75, 0.25]"
```

### Option 2: Raw Poems (Computed On-the-Fly)
CSV/Excel with columns: `Title`, `Poem`, `Poet`, `Genre`

```csv
Title,Poem,Poet,Genre
"The Raven","Once upon a midnight dreary...","Edgar Allan Poe","fear"
"Fire and Ice","Some say the world will end...","Robert Frost","anger"
```

**Supported genres**: `fear`, `anger`, `sadness`, `love`, `joy`, `surprise`

---

## Troubleshooting

### "Dataset not found"
- Check that the file path is correct
- Use an absolute path if relative doesn't work
- Ensure the file is `.csv`, `.xlsx`, or `.xls`

### Import errors
```powershell
# Make sure you're in the Artkathon directory
cd Artkathon

# Activate virtual environment
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Slow rendering
- Use `--limit 10` for testing
- Consider reducing resolution in `flow_field.py` (change width/height to 1500)
- Run on a subset first

---

## Advanced Usage

### Batch Process Multiple Schemes
```powershell
# Generate complete galleries with each color scheme
python pipeline.py --color-scheme expressive --output gallery_expressive
python pipeline.py --color-scheme very_smooth --output gallery_smooth
python pipeline.py --color-scheme wild --output gallery_wild
```

### Custom Vector Creation
```python
from tools.simple_text_to_vectors import simple_text_to_vectors
from render_embedding import map_embedding_to_params
from flow_field import render

# Create custom vector
vector = simple_text_to_vectors(
    title="My Poem",
    poem_text="Roses are red...",
    poet="Anonymous",
    genre="love"
)

# Render
params = map_embedding_to_params(vector, color_scheme='expressive')
img = render(params)
img.save('my_artwork.png')
```

### Direct Parameter Control
```python
from flow_field import render

params = {
    'width': 3000,
    'height': 3000,
    'cell_size': 10,
    'noise_scale': 6,
    'octaves': 4,
    'quantize_steps': 8,
    'swirl': 0.2,
    'density': 0.003,
    'max_length': 600,
    'color_start': (50, 50, 200),
    'color_end': (200, 50, 50),
    # ... see flow_field.py for all parameters
}

img = render(params)
img.save('custom_art.png')
```

---

## Contributing

When modifying the code:

1. **Vector dimensions**: If you add/change dimensions in `simple_text_to_vectors.py`, update the mapping in `render_embedding.py`
2. **Color schemes**: Add new schemes in `color_schemes.py` following the existing structure
3. **Parameters**: Document any new rendering parameters in this guide

---

## Files Reference

- **pipeline.py**: Master orchestrator for batch processing
- **flow_field.py**: Core rendering engine (Perlin noise + stroke drawing)
- **render_embedding.py**: Maps 14D vectors to visual parameters
- **color_schemes.py**: Defines color palette configurations
- **perlin.py**: Multi-octave Perlin noise implementation
- **simple_text_to_vectors.py**: Text analysis and vectorization

---


