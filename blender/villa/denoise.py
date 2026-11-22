"""Smooths the grain out of a baked lightmap. Pure numpy, so it runs outside Blender too.

Cycles can't denoise a bake, and 768 samples still leave walls lit only by bounced light
with a 4-5 % speckle per texel (more in the darker rooms), which reads as a gritty
plaster on the site. This is an edge-keeping blur (a bilateral filter):

- it averages each texel with its neighbours up to RADIUS texels away, weighted by distance;
- it only uses neighbours in the same chart (the rectangles the atlas was packed with), so
  light never bleeds from one surface onto another;
- it gives little weight to a neighbour much brighter or darker than the texel, compared in
  log brightness against that chart's own noise level, so a sun patch on the floor or a
  contact shadow keeps its edge while the speckle, a few per cent, is averaged away.
"""

import numpy as np

RADIUS = 3          # texels: 7 x 7 neighbourhood, about 5 cm on a wall at 56 texels per metre
SIGMA_S = 2.0       # texels, the distance weighting
EDGE = 3.0          # a step this many times the chart's noise counts as an edge, not grain
MIN_NOISE = 0.01    # relative; charts cleaner than this are left almost untouched
LUM = np.array([0.2126, 0.7152, 0.0722])


def chart_ids(shape, rects, scale=1.0):
    """An integer per texel: which packed rectangle it belongs to, -1 for the gaps."""
    ids = np.full(shape, -1, dtype=np.int32)
    if rects is None:                                   # the sand covers its whole lightmap
        ids[:] = 0
        return ids
    for i, (x, y, w, h) in enumerate(rects):
        ids[int(np.ceil(y * scale)):int(np.floor((y + h) * scale)), int(np.ceil(x * scale)):int(np.floor((x + w) * scale))] = i
    return ids


def chart_noise(loglum, ids):
    """Each chart's grain: the robust spread of each texel against its four neighbours'
    mean, in log brightness. Small charts borrow the atlas-wide figure."""
    nb = (np.roll(loglum, 1, 0) + np.roll(loglum, -1, 0) + np.roll(loglum, 1, 1) + np.roll(loglum, -1, 1)) / 4
    same = ids >= 0
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        same &= np.roll(ids, (dy, dx), axis=(0, 1)) == ids
    d = np.abs(loglum - nb)
    # the difference against a 4-neighbour mean has 1.12x the spread of the texel itself
    overall = float(np.median(d[same])) * 1.4826 / 1.118 if same.any() else MIN_NOISE
    n = int(ids.max()) + 1
    noise = np.full(n, overall)
    if n:
        flat = ids[same]
        order = np.argsort(flat, kind="stable")
        flat, vals = flat[order], d[same][order]
        starts = np.searchsorted(flat, np.arange(n))
        ends = np.searchsorted(flat, np.arange(n), side="right")
        for i in range(n):
            if ends[i] - starts[i] >= 400:
                noise[i] = float(np.median(vals[starts[i]:ends[i]])) * 1.4826 / 1.118
    return np.maximum(noise, MIN_NOISE), overall


def denoise(light, rects, scale=1.0):
    """light: (h, w, 3) linear values. Returns the smoothed light and the atlas-wide
    noise before and after (relative, per texel), for the bake's report."""
    h, w, _ = light.shape
    ids = chart_ids((h, w), rects, scale)
    lum = np.maximum(light @ LUM, 1e-4)
    loglum = np.log(lum).astype(np.float32)
    noise, before = chart_noise(loglum, ids)
    sigma_r = np.where(ids >= 0, noise[np.maximum(ids, 0)] * EDGE, 1.0).astype(np.float32)
    inv = 1.0 / (2.0 * sigma_r ** 2)
    # Brightness is compared on a 3 x 3 median of the texels, not the texels themselves:
    # a lone bright or dark texel (light bounced up off a sunlit floor speckles a ceiling
    # like that) would otherwise count as an edge and be kept. A median keeps real edges.
    stack = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            same = np.roll(ids, (dy, dx), axis=(0, 1)) == ids
            stack.append(np.where(same, np.roll(loglum, (dy, dx), axis=(0, 1)), loglum))
    guide = np.median(np.stack(stack), axis=0).astype(np.float32)
    del stack
    rgb = light.astype(np.float32)
    acc = np.zeros_like(rgb)
    wsum = np.zeros((h, w), dtype=np.float32)
    for dy in range(-RADIUS, RADIUS + 1):
        for dx in range(-RADIUS, RADIUS + 1):
            ws = np.float32(np.exp(-(dy * dy + dx * dx) / (2 * SIGMA_S ** 2)))
            o_ids = np.roll(ids, (dy, dx), axis=(0, 1))
            o_log = np.roll(guide, (dy, dx), axis=(0, 1))
            wgt = ws * np.exp(-((o_log - guide) ** 2) * inv)
            wgt *= (o_ids == ids)
            acc += wgt[..., None] * np.roll(rgb, (dy, dx), axis=(0, 1))
            wsum += wgt
    out = np.where(ids[..., None] >= 0, acc / np.maximum(wsum, 1e-12)[..., None], rgb).astype(np.float64)
    after = chart_noise(np.log(np.maximum(out @ LUM, 1e-4)).astype(np.float32), ids)[1]
    return out, before, after
