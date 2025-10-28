import numpy as np
from PIL import Image, ImageDraw
import random
import math
from .perlin import generate_perlin_noise_2d

class Bounds:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = x0, y0
        self.x1, self.y1 = x1, y1
        
def build_grid(params):
    """
    Create a grid for the flow field with specified dimensions and cell size
    
    params:
        width: output image width
        height: output image height
        cell_size: size of each grid cell
        margin_factor: fraction of dimension to use as margin (0-1)
    """
    width, height = params['width'], params['height']
    cell = params['cell_size']
    margin = min(width, height) * params['margin_factor']
    
    # Calculate grid dimensions
    nx = int((width - 2*margin) / cell)
    ny = int((height - 2*margin) / cell)
    
    angles = np.zeros((ny, nx))
    bounds = Bounds(margin, margin, width-margin, height-margin)
    
    return (angles, bounds)

def fill_angles(angles, bounds, params):
    """
    Fill the angle grid using Perlin noise and various transformations
    
    params:
        noise_scale: base scale of the Perlin noise
        octaves: number of noise layers to combine
        seed: random seed for reproducibility
        quantize_steps: if > 0, quantize angles to this many steps
        swirl: amount of circular flow to add
        bands: number of distinct angle bands
    """
    ny, nx = angles.shape
    
    # Generate base Perlin noise field with integer resolution
    # Safely extract and validate noise_scale
    try:
        raw_scale = params.get('noise_scale', 4)
        noise_scale = int(max(2, float(raw_scale)))  # Convert to float first, then int, minimum 2
    except (TypeError, ValueError, OverflowError):
        noise_scale = 4  # Safe fallback if invalid value
    
    # Safely extract octaves
    try:
        octaves = int(params.get('octaves', 1))
        octaves = max(1, min(10, octaves))  # Clamp to reasonable range [1, 10]
    except (TypeError, ValueError):
        octaves = 1
    
    # Safely extract seed
    seed = params.get('seed', None)
    try:
        seed_arg = None if seed is None else int(seed)
    except (TypeError, ValueError):
        seed_arg = None
    noise = generate_perlin_noise_2d((ny, nx),
                                     (noise_scale, noise_scale),
                                     octaves=octaves,
                                     seed=seed_arg)
    
    # Convert to angles (radians)
    angles[:] = noise * 2 * np.pi
    
    # Optional: Add swirl effect
    if params.get('swirl', 0) > 0:
        y, x = np.mgrid[0:ny, 0:nx]
        cy, cx = ny/2, nx/2
        dx, dy = x - cx, y - cy
        theta = np.arctan2(dy, dx)
        angles += theta * params['swirl']
    
    # Optional: Quantize angles
    if params.get('quantize_steps', 0) > 0:
        angles = np.round(angles / (2*np.pi) * params['quantize_steps']) 
        angles = angles * 2*np.pi / params['quantize_steps']
    
    return angles

def seed_points(params, bounds):
    """
    Generate starting points for the strokes
    
    params:
        seeding: 'grid' or 'random'
        density: approximate number of points
        margin: additional margin from bounds
    """
    points = []
    area = (bounds.x1 - bounds.x0) * (bounds.y1 - bounds.y0)
    
    if params['seeding'] == 'random':
        n_points = int(area * params['density'])
        for _ in range(n_points):
            x = random.uniform(bounds.x0, bounds.x1)
            y = random.uniform(bounds.y0, bounds.y1)
            points.append((x, y, None))
            
    elif params['seeding'] == 'grid':
        spacing = math.sqrt(area / (params['density']))
        for y in np.arange(bounds.y0, bounds.y1, spacing):
            for x in np.arange(bounds.x0, bounds.x1, spacing):
                points.append((x, y, None))
                
    return points

def draw_strokes(angles, bounds, params):
    """
    Draw strokes following the flow field
    
    params:
        width: image width
        height: image height
        max_length: maximum stroke length
        step_size: distance to move each step
        angle_gain: how much to weight the field angle vs current direction
        jitter: random angle variation per step
        color_start/end: RGB tuples for gradient
        width_start/end: stroke width range
    """
    img = Image.new('RGB', (params['width'], params['height']), params['background'])
    draw = ImageDraw.Draw(img)
    
    points = seed_points(params, bounds)
    
    # Check for palette inputs
    use_palette = 'color_palette' in params and len(params['color_palette']) > 2
    lut = params.get('color_lut') or []
    use_lut = isinstance(lut, list) and len(lut) > 0
    lut_len = len(lut)
    palette_axis = params.get('palette_axis', 'x')
    within_stroke = float(params.get('palette_within_stroke', 0.0))
    
    def get_field_angle(x, y):
        # Convert position to grid coordinates
        gx = int((x - bounds.x0) / params['cell_size'])
        gy = int((y - bounds.y0) / params['cell_size'])
        if 0 <= gy < angles.shape[0] and 0 <= gx < angles.shape[1]:
            return angles[gy, gx]
        return 0
    
    for x0, y0, _ in points:
        x, y = x0, y0
        positions = [(x, y)]
        heading = get_field_angle(x, y)
        
        # Follow flow field
        for _ in range(int(params['max_length'])):
            # Get flow field angle
            field_angle = get_field_angle(x, y)
            
            # Update heading (blend current and field)
            heading = heading * (1 - params['angle_gain']) + field_angle * params['angle_gain']
            
            # Add jitter
            heading += random.uniform(-params['jitter'], params['jitter'])
            
            # Move
            x += math.cos(heading) * params['step_size']
            y += math.sin(heading) * params['step_size']
            
            # Stop if out of bounds
            if not (bounds.x0 <= x <= bounds.x1 and bounds.y0 <= y <= bounds.y1):
                break
                
            positions.append((x, y))
        
        # Draw the stroke with varying width and color
        if len(positions) > 1:
            # Determine base color for this stroke using LUT
            # Base position along axis for smooth spatial gradient
            if palette_axis == 'y':
                base = (y0 - bounds.y0) / max(1.0, (bounds.y1 - bounds.y0))
            elif palette_axis == 'field':
                # Use flow field angle at stroke start
                angle = get_field_angle(x0, y0)
                base = (angle % (2 * math.pi)) / (2 * math.pi)
            elif palette_axis == 'random':
                # Random base for each stroke (deterministic via current random state)
                base = random.random()
            else:  # default 'x' axis
                base = (x0 - bounds.x0) / max(1.0, (bounds.x1 - bounds.x0))
            
            base = max(0.0, min(1.0, base))
            
            # Compute span and clamp base so we don't wrap the LUT at the right/bottom edge
            # Handle edge cases: empty LUT (shouldn't happen) or single-color LUT
            if lut_len <= 1:
                # Single color or empty - no gradient possible
                base_idx = 0
                span = 0
            else:
                # Normal case: multiple colors available for gradient
                span = int((lut_len - 1) * within_stroke)
                span = max(0, span)  # Ensure non-negative
                max_base_idx = max(0, (lut_len - 1) - span)
                base_idx = int(base * max_base_idx)
            
            # Draw stroke with color gradient from LUT
            for i in range(len(positions) - 1):
                t = i / (len(positions) - 1)
                if lut_len > 0:
                    idx = base_idx + int(t * span)
                    if idx >= lut_len:
                        idx = lut_len - 1
                    color = lut[idx]
                else:
                    # Fallback if LUT is empty (shouldn't happen)
                    color = params['color_start']
                
                width = params['width_start'] + (params['width_end'] - params['width_start']) * t
                draw.line(positions[i:i+2], fill=tuple(color), width=int(width))
    
    return img

def render(params):
    """
    Main rendering function that coordinates the flow field generation and drawing
    
    params: dictionary containing all necessary parameters
    """
    # Set random seed for reproducible stroke positions and jitter
    if 'seed' in params and params['seed'] is not None:
        random.seed(params['seed'])
    
    grid = build_grid(params)
    fill_angles(*grid, params)
    img = draw_strokes(grid[0], grid[1], params)
    return img


# =============================================================================
# EXAMPLE CODE BELOW - For testing and documentation purposes only
# Production code uses render_embedding.py to generate parameters
# =============================================================================

# Example parameters showing all available options with typical values
default_params = {
    'width': 1000,
    'height': 1000,
    'cell_size': 20,
    'margin_factor': 0.1,
    'noise_scale': 4,
    'octaves': 4,
    'seed': 42,
    'quantize_steps': 0,
    'swirl': 0.2,
    'seeding': 'random',
    'density': 0.001,
    'max_length': 100,
    'step_size': 5,
    'angle_gain': 0.5,
    'jitter': 0.1,
    'color_start': (50, 50, 200),
    'color_end': (200, 50, 50),
    'width_start': 3,
    'width_end': 1,
    'background': (240, 240, 240)
}


if __name__ == '__main__':
    # Example: Test the flow field renderer with simple embedding
    # This demonstrates how to map abstract values to visual parameters
    
    def map_poetry_to_params(embedding):
        params = default_params.copy()
        
        # Map emotional content to color palette
        emotion = embedding[0]  # Assuming first dimension is emotion
        if emotion < 0.33:  # Sad/dark
            params['color_start'] = (20, 20, 50)
            params['color_end'] = (50, 50, 150)
        elif emotion < 0.66:  # Neutral
            params['color_start'] = (50, 100, 50)
            params['color_end'] = (150, 200, 150)
        else:  # Happy/warm
            params['color_start'] = (200, 100, 50)
            params['color_end'] = (250, 150, 50)
            
        # Map other dimensions to visual parameters
        params['noise_scale'] = 2 + embedding[1] * 4  # Turbulence
        params['jitter'] = embedding[2] * 0.2  # Chaos/order
        params['density'] = 0.0005 + embedding[3] * 0.001  # Density
        params['swirl'] = embedding[4] * 0.4  # Flow complexity
        
        return params
    
    # Example usage - Test the renderer standalone
    sample_embedding = [0.7, 0.5, 0.3, 0.6, 0.4]  # Sample 5D embedding
    params = map_poetry_to_params(sample_embedding)
    img = render(params)
    img.save('flow_field_art.png')
    print("✓ Test render saved to flow_field_art.png")
    print("  (In production, use pipeline.py or render_embedding.py instead)")