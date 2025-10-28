"""
Render a specific embedding vector using the flow field system.
"""
import sys
import ast
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from .flow_field import render
from .color_schemes import get_scheme

# Default vector if none provided
embedding = [0.1, 1.0, 0.2, 2.2, 2.267, 1.0, 0.25, 0.264, 0.287, 0.814, 22.0, 0.4, 0.75, 0.1]

# Check for command line vector and optional style
style_flag = None
if '--vector' in sys.argv:
    try:
        idx = sys.argv.index('--vector')
        embedding = ast.literal_eval(sys.argv[idx+1])
        if len(embedding) != 14:
            print("Error: Vector must have 14 dimensions")
            sys.exit(1)
    except Exception:
        print("Error: Invalid vector format")
        sys.exit(1)

if '--style' in sys.argv:
    try:
        idx = sys.argv.index('--style')
        style_flag = sys.argv[idx+1]
    except Exception:
        style_flag = None

def map_embedding_to_params(v, color_scheme='expressive'):
    """Map 14D vector to flow field parameters based on poetic metrics
    
    v[0]: Title length / 10.0
    v[1]: Title lexical complexity
    v[2]: Verse count / 20.0
    v[3]: Average words per verse / 10.0
    v[4]: Verse length variability / 5.0
    v[5]: Rhyme diversity
    v[6]: Dominant rhyme frequency
    v[7]: Alliteration score
    v[8]: Vowel dominance
    v[9]: Vowel entropy / 3.0
    v[10]: Raw rhythm (avg words per verse)
    v[11]: Poet name length / 5.0
    v[12]: Poet name diversity
    v[13]: Genre (for color palette)
    
    color_scheme: name of color scheme from color_schemes.py
    """
    # Load color scheme configuration
    scheme = get_scheme(color_scheme)
    palette_mapping = scheme['palette_mapping']
    
    # Map genre (v[13]) to matplotlib colormap
    def get_color_palette(genre_val):
        """Map genre value to (colormap_name, sample_positions)
        
        Mapping :

        v[13] < 0.2  → FEAR      → bone colormap     (greyscale ominous)
        v[13] < 0.3  → ANGER     → hot colormap      (black→red→yellow)
        v[13] < 0.4  → SADNESS   → PuBu colormap     (purple→blue)
        v[13] < 0.5  → LOVE      → RdPu colormap     (red→purple→pink)
        v[13] < 0.6  → JOY       → rainbow colormap  (full spectrum)
        v[13] < 0.7  → SURPRISE  → cividis colormap  (blue→yellow)
        v[13] ≥ 0.7  → DEFAULT   → grey colormap     (neutral greyscale)

        Returns colormap name and tuple of (start_pos, end_pos) to sample from [0, 1]
        """
        if genre_val < 0.2:      return palette_mapping['fear']
        elif genre_val < 0.3:    return palette_mapping['anger']
        elif genre_val < 0.4:    return palette_mapping['sadness']
        elif genre_val < 0.5:    return palette_mapping['love']
        elif genre_val < 0.6:    return palette_mapping['joy']
        elif genre_val < 0.7:    return palette_mapping['surprise']
        else:                    return palette_mapping['default']
    
    cmap_name, (pos_start, pos_end) = get_color_palette(v[13])
    cmap = plt.colormaps.get_cmap(cmap_name)
    
    # Sample multiple colors across the colormap range for full spectrum
    n_colors = 8  # Number of color stops to sample for coarse palette
    color_positions = np.linspace(pos_start, pos_end, n_colors)
    color_palette = [tuple(int(c * 255) for c in cmap(pos)[:3]) for pos in color_positions]

    # High-resolution LUT for smooth transitions (used by renderer)
    lut_size = 256
    lut_positions = np.linspace(pos_start, pos_end, lut_size)
    color_lut = [tuple(int(c * 255) for c in cmap(pos)[:3]) for pos in lut_positions]

    # For backward compatibility, still set start/end
    color_start = color_palette[0]
    color_end = color_palette[-1]
    
    return {
        'width': 3000,
        'height': 3000,
        'cell_size': int(4 + v[3] * 8),       # Scale with avg words per verse
        'margin_factor': 0.08,
        
        # Flow field characteristics
        'noise_scale': max(2, v[4] * 8),      # Verse variability → complexity
        'octaves': int(3 + v[7] * 4),         # Alliteration → detail layers
        'seed': int(v[9] * 1000),             # Vowel entropy → seed
        'quantize_steps': int(v[5] * 12),     # Rhyme diversity → quantization
        'swirl': v[6] * 0.3,                  # Dominant rhyme freq → swirl
        
        # Seeding and strokes
        'seeding': 'random',
        'density': max(0.001, min(0.006, v[2] * 0.002)),  # Verse count → density
        'max_length': int(400 + v[10] * 20),  # Raw rhythm → stroke length
        'step_size': 2 + v[8] * 4,            # Vowel dominance → step size
        'angle_gain': 0.6 + v[1] * 0.3,       # Title complexity → flow following
        'jitter': v[0] * 0.15,                # Title length → jitter
        
        # Visual style
        'color_start': color_start,
        'color_end': color_end,
        'color_palette': color_palette,  # Full palette for diverse stroke colors
    'color_lut': color_lut,          # High-res LUT for smooth gradients
    'palette_axis': scheme['palette_axis'],
    'palette_within_stroke': scheme['palette_within_stroke'],
        'palette_name': cmap_name,  # Store for filename labeling
        'width_start': 6 + v[11] * 0.3,       # Poet name length → stroke width
        'width_end': 0.8,
        'background': (250, 250, 245)
    }


def apply_user_style_bias(params, style):
    """Apply a user preference bias to make renders sharper, higher-contrast, and more turbulent.

    Supported styles:
      - 'sharp' or 'preferred': high contrast, sharp angles, turbulent grain
      - 'natural' : (no change)
    """
    if not style:
        return params

    s = style.lower()
    if s in ('sharp', 'preferred'):
        # Stronger noise and detail
        params['noise_scale'] = int(max(3, params.get('noise_scale', 4) * 1.6))
        params['octaves'] = int(params.get('octaves', 3) + 2)

        # Make quantization explicit for sharp angles
        qs = params.get('quantize_steps', 0)
        params['quantize_steps'] = max(12, qs if qs > 0 else 16)

        # Reduce smooth jitter and follow field more closely for crisp strokes
        params['jitter'] = max(0.001, params.get('jitter', 0.1) * 0.35)
        params['angle_gain'] = min(0.99, params.get('angle_gain', 0.6) + 0.25)

        # Finer grid for grainy detail
        params['cell_size'] = max(2, int(params.get('cell_size', 20) * 0.6))

        # Increase density (more strokes) but cap to reasonable max
        params['density'] = min(0.02, params.get('density', 0.001) * 2.0)

        # Contrast boost: make start darker and end brighter
        cs = params.get('color_start', (20,20,20))
        ce = params.get('color_end', (200,200,200))
        params['color_start'] = tuple(max(0, c-40) for c in cs)
        params['color_end'] = tuple(min(255, c+40) for c in ce)

        # Slightly thicker strokes to emphasize edges
        params['width_start'] = params.get('width_start', 3) * 1.4
        params['width_end'] = max(0.6, params.get('width_end', 1) * 0.9)

    return params

if __name__ == '__main__':
    print("Rendering your embedding vector...")
    params = map_embedding_to_params(embedding)
    # Apply user style bias if requested
    params = apply_user_style_bias(params, style_flag)
    
    # Render and save
    img = render(params)
    # Ensure out directory exists
    import os
    os.makedirs('out', exist_ok=True)
    img.save('out/your_embedding.png')
    print("\nSaved to out/your_embedding.png")
