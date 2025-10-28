"""
Color scheme configurations for flow field rendering.

Each scheme defines the palette mapping and rendering parameters.
"""

SCHEMES = {
    'very_smooth': {
        'description': 'Smooth gradients with subtle within-stroke color transitions',
        'palette_mapping': {
            'fear': ('bone', (0.2, 0.9)),
            'anger': ('hot', (0.1, 0.95)),
            'sadness': ('PuBu', (0.4, 0.95)),
            'love': ('RdPu', (0.2, 0.9)),
            'joy': ('rainbow', (0.0, 1.0)),
            'surprise': ('cividis', (0.1, 0.9)),
            'default': ('grey', (0.2, 0.9))
        },
        'palette_axis': 'x',
        'palette_within_stroke': 0.2
    },
    
    'expressive': {
        'description': 'Bold color shifts with vertical gradients and per-stroke variation',
        'palette_mapping': {
            'fear': ('bone', (0.0, 1.0)),
            'anger': ('hot', (0.0, 1.0)),
            'sadness': ('PuBu', (0.2, 1.0)),
            'love': ('RdPu', (0.0, 1.0)),
            'joy': ('rainbow', (0.0, 1.0)),
            'surprise': ('cividis', (0.0, 1.0)),
            'default': ('grey', (0.0, 1.0))
        },
        'palette_axis': 'y',  # Vertical gradient instead of horizontal
        'palette_within_stroke': 0.5  # Much more dramatic color sweep per stroke
    },
    
    'wild': {
        'description': 'Flow-driven color chaos with rainbow strokes following field direction',
        'palette_mapping': {
            'fear': ('bone', (0.0, 1.0)),
            'anger': ('hot', (0.0, 1.0)),
            'sadness': ('PuBu', (0.0, 1.0)),
            'love': ('RdPu', (0.0, 1.0)),
            'joy': ('rainbow', (0.0, 1.0)),
            'surprise': ('cividis', (0.0, 1.0)),
            'default': ('grey', (0.0, 1.0))
        },
        'palette_axis': 'field',  # Colors follow flow field angles
        'palette_within_stroke': 0.7  # Extreme rainbow effect per stroke
    }
}


def get_scheme(name='expressive'):
    """Get a color scheme configuration by name."""
    return SCHEMES.get(name, SCHEMES['expressive'])
