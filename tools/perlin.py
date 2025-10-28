import numpy as np

def generate_perlin_noise_2d(shape, res, octaves=1, persistence=0.5, seed=None):
    """
    Generate 2D Perlin noise
    
    Args:
        shape: (height, width) of output
        res: (y_scale, x_scale) for base noise
        octaves: number of noise layers to combine
        persistence: how quickly amplitudes diminish for subsequent octaves
        seed: random seed
    """
    
    if seed is not None:
        np.random.seed(seed)
        
    def interpolant(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    # Ensure integer sizes
    res = (int(res[0]), int(res[1]))
    shape = (int(shape[0]), int(shape[1]))

    def single_octave(shape, res, seed=None):
        """Compute one octave of Perlin noise for given integer res and shape."""
        res_y, res_x = int(res[0]), int(res[1])
        h, w = int(shape[0]), int(shape[1])

        # Gradients at lattice points (res_y+1, res_x+1, 2)
        if seed is not None:
            rng = np.random.RandomState(seed)
            angles = 2 * np.pi * rng.rand(res_y + 1, res_x + 1)
        else:
            angles = 2 * np.pi * np.random.rand(res_y + 1, res_x + 1)
        gradients = np.dstack((np.cos(angles), np.sin(angles)))

        # Coordinates in the lattice for each output pixel
        xs = np.linspace(0, res_x, w, endpoint=False)
        ys = np.linspace(0, res_y, h, endpoint=False)
        X, Y = np.meshgrid(xs, ys)

        xi = X.astype(int)
        yi = Y.astype(int)
        xf = X - xi
        yf = Y - yi

        # Helper to fetch gradients safely
        def grad_at(y_idx, x_idx):
            return gradients[y_idx, x_idx]

        g00 = grad_at(yi, xi)
        g10 = grad_at(yi, xi + 1)
        g01 = grad_at(yi + 1, xi)
        g11 = grad_at(yi + 1, xi + 1)

        # Dot products
        dot00 = g00[..., 0] * xf + g00[..., 1] * yf
        dot10 = g10[..., 0] * (xf - 1) + g10[..., 1] * yf
        dot01 = g01[..., 0] * xf + g01[..., 1] * (yf - 1)
        dot11 = g11[..., 0] * (xf - 1) + g11[..., 1] * (yf - 1)

        # Interpolate
        u = interpolant(xf)
        v = interpolant(yf)

        nx0 = dot00 * (1 - u) + u * dot10
        nx1 = dot01 * (1 - u) + u * dot11
        n = nx0 * (1 - v) + v * nx1
        return n

    # Sum octaves
    total = np.zeros(shape)
    amplitude = 1.0
    max_amp = 0.0
    for o in range(octaves):
        freq = 2 ** o
        res_o = (res[0] * freq, res[1] * freq)
        seed_o = None if seed is None else int(seed) + o
        octave_noise = single_octave(shape, res_o, seed=seed_o)
        total += amplitude * octave_noise
        max_amp += amplitude
        amplitude *= persistence

    # Normalize
    if max_amp != 0:
        total = total / max_amp
    return total