"""Date palms, desert shrubs and rocks, all generated so nothing needs a license.

These are small, bumpy shapes, so instead of a lightmap their light is baked
into their vertices.
"""
import math
import random

G = -0.12

# x, z, height of each palm. Placed to frame the landing shot and the pool view.
PALMS = [
    (-17.5, 6.0, 7.0), (-24.5, 15.5, 8.2), (-21.0, 27.5, 7.4), (9.5, 14.5, 6.6),
    (16.0, 9.0, 7.8), (17.5, -7.0, 7.2), (-15.5, -13.0, 6.4), (21.5, -15.5, 8.4),
    (-10.0, -23.5, 7.6), (6.0, 26.0, 7.0),
]


def build_plants(b):
    rng = random.Random(7)
    for x, z, h in PALMS:
        palm(b, rng, x, z, h)
    scatter(b, rng)


# ---- palms -----------------------------------------------------------------
def _norm(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def _cross(a, c):
    return (a[1] * c[2] - a[2] * c[1], a[2] * c[0] - a[0] * c[2], a[0] * c[1] - a[1] * c[0])


def _add(a, c, k=1.0):
    return (a[0] + c[0] * k, a[1] + c[1] * k, a[2] + c[2] * k)


def palm(b, rng, x, z, height):
    lean_dir = rng.uniform(0, 2 * math.pi)
    lean = rng.uniform(0.02, 0.09) * height
    sides, rings = 9, 14
    verts, faces = [], []
    for k in range(rings + 1):
        t = k / rings
        cx = x + math.cos(lean_dir) * lean * t * t
        cz = z + math.sin(lean_dir) * lean * t * t
        radius = (0.30 - 0.11 * t) * (1.0 + 0.07 * (k % 2)) + (0.10 * (1 - t) ** 6)   # ringed, flared at the foot
        for s in range(sides):
            a = 2 * math.pi * s / sides
            verts.append((cx + math.cos(a) * radius, G - 0.2 + t * (height + 0.2), cz + math.sin(a) * radius))
    for k in range(rings):
        for s in range(sides):
            a, c = k * sides + s, k * sides + (s + 1) % sides
            faces.append((a, a + sides, c + sides, c))
    b.mesh("out", "bark", verts, faces, smooth=True)

    top = (x + math.cos(lean_dir) * lean, height, z + math.sin(lean_dir) * lean)
    count = 24
    for f in range(count):
        age = f / (count - 1)                       # 0 = newest, standing up; 1 = oldest, hanging down
        azimuth = f * 2.39996 + rng.uniform(-0.2, 0.2)
        frond(b, rng, top, azimuth,
              start=math.radians(78 - 95 * age ** 0.85),
              droop=math.radians(55 + 45 * age),
              length=rng.uniform(2.9, 3.7) * (0.75 + 0.25 * math.sin(math.pi * min(1.0, age + 0.25))))


def frond(b, rng, base, azimuth, start, droop, length):
    """One palm leaf: a curved rib with a row of narrow leaflets down each side."""
    steps = 30
    ca, sa = math.cos(azimuth), math.sin(azimuth)
    p = base
    pts, tans = [], []
    for i in range(steps + 1):
        s = i / steps
        e = start - droop * s ** 1.4
        d = (math.cos(e) * ca, math.sin(e), math.cos(e) * sa)
        pts.append(p)
        tans.append(d)
        p = _add(p, d, length / steps)

    side0 = (-sa, 0.0, ca)
    verts, faces = [], []

    def quad(a, c, d, e):
        i = len(verts)
        verts.extend((a, c, d, e))
        faces.append((i, i + 1, i + 2, i + 3))

    # the rib
    for i in range(0, steps, 5):
        w0, w1 = 0.035 * (1 - i / steps) + 0.008, 0.035 * (1 - (i + 5) / steps) + 0.008
        quad(_add(pts[i], side0, -w0), _add(pts[i], side0, w0), _add(pts[i + 5], side0, w1), _add(pts[i + 5], side0, -w1))
    # leaflets
    for i in range(4, steps + 1):
        s = i / steps
        tng = tans[i]
        up = _norm(_cross(side0, tng))
        long = 0.72 * math.sin(math.pi * min(1.0, 0.1 + 0.9 * s)) ** 0.6 * (length / 3.3) + 0.08
        for sign in (-1.0, 1.0):
            d = _norm(_add(_add((side0[0] * sign, 0.0, side0[2] * sign), tng, 0.55), up, -0.35 + rng.uniform(-0.12, 0.12)))
            d = _norm((d[0], d[1] - 0.25, d[2]))          # gravity
            tip = _add(pts[i], d, long * rng.uniform(0.85, 1.05))
            w = 0.038
            quad(_add(pts[i], tng, -w), _add(pts[i], tng, w), _add(tip, tng, w * 0.2), _add(tip, tng, -w * 0.2))
    b.mesh("out", "palm_leaf", verts, faces, smooth=False)


# ---- shrubs and rocks --------------------------------------------------------
def shrub(b, rng, x, z, y, size):
    """A spiky tuft of dry desert grass."""
    verts, faces = [], []
    for _ in range(rng.randint(16, 26)):
        a = rng.uniform(0, 2 * math.pi)
        e = math.radians(rng.uniform(28, 86))
        long = size * rng.uniform(0.5, 1.0)
        d = (math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a))
        side = (-math.sin(a), 0.0, math.cos(a))
        w = 0.035 * size + 0.012
        root = (x + math.cos(a) * 0.06 * size, y - 0.03, z + math.sin(a) * 0.06 * size)
        mid = _add(root, d, long * 0.55)
        tip = _add(_add(root, d, long), (0, -1, 0), long * 0.18)
        i = len(verts)
        verts.extend((_add(root, side, -w), _add(root, side, w), _add(mid, side, w * 0.7), _add(mid, side, -w * 0.7),
                      _add(tip, side, w * 0.08), _add(tip, side, -w * 0.08)))
        faces.append((i, i + 1, i + 2, i + 3))
        faces.append((i + 3, i + 2, i + 4, i + 5))
    b.mesh("out", "shrub", verts, faces, smooth=False)


_ICO = None


def _icosphere():
    """A sphere made of triangles, subdivided twice. Built once and reused."""
    global _ICO
    if _ICO:
        return _ICO
    t = (1 + 5 ** 0.5) / 2
    v = [_norm(p) for p in ((-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
                            (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1))]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(2):
        cache, out = {}, []

        def mid(a, c):
            key = (min(a, c), max(a, c))
            if key not in cache:
                v.append(_norm(_add(v[a], v[c])))
                cache[key] = len(v) - 1
            return cache[key]

        for a, c, d in f:
            ab, cd, da = mid(a, c), mid(c, d), mid(d, a)
            out += [(a, ab, da), (c, cd, ab), (d, da, cd), (ab, cd, da)]
        f = out
    _ICO = (v, f)
    return _ICO


def rock(b, rng, x, z, y, size):
    base, faces = _icosphere()
    waves = [(_norm((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))), rng.uniform(1.5, 4.0),
              rng.uniform(0, 6.28), rng.uniform(0.05, 0.16)) for _ in range(6)]
    sx, sy, sz = size * rng.uniform(0.8, 1.5), size * rng.uniform(0.45, 0.8), size * rng.uniform(0.7, 1.2)
    turn = rng.uniform(0, 6.28)
    ct, st = math.cos(turn), math.sin(turn)
    verts = []
    for p in base:
        k = 1.0 + sum(a * math.sin((p[0] * d[0] + p[1] * d[1] + p[2] * d[2]) * fr + ph) for d, fr, ph, a in waves)
        px, py, pz = p[0] * k * sx, p[1] * k * sy, p[2] * k * sz
        verts.append((x + px * ct - pz * st, y + py + sy * 0.25, z + px * st + pz * ct))
    b.mesh("out", "rock", verts, faces, smooth=True)


def scatter(b, rng):
    """Sprinkle shrubs and rocks over the sand, keeping clear of the house, paving and drive."""
    from .terrain import height
    import numpy as np

    def free(x, z):
        if abs(x) < 15.0 and -21.5 < z < 20.5:
            return False                              # house, forecourt, pool deck
        if -13.5 < x < -4.5 and z > 0:
            return False                              # the drive
        return True

    def ground(x, z):
        return float(height(np.array([x]), np.array([z]))[0])

    placed = 0
    while placed < 55:
        r = 16 + 80 * rng.random() ** 1.6
        a = rng.uniform(0, 2 * math.pi)
        x, z = r * math.cos(a), r * math.sin(a)
        if not free(x, z):
            continue
        y = ground(x, z)
        # shrubs come in little clumps
        for _ in range(rng.randint(1, 3)):
            ox, oz = x + rng.uniform(-0.8, 0.8), z + rng.uniform(-0.8, 0.8)
            if free(ox, oz):
                shrub(b, rng, ox, oz, ground(ox, oz), rng.uniform(0.45, 1.0))
        placed += 1

    placed = 0
    while placed < 38:
        r = 15 + 90 * rng.random() ** 1.4
        a = rng.uniform(0, 2 * math.pi)
        x, z = r * math.cos(a), r * math.sin(a)
        if not free(x, z):
            continue
        rock(b, rng, x, z, ground(x, z), rng.uniform(0.25, 1.1) * (1.6 if rng.random() < 0.15 else 1.0))
        placed += 1
    # a few shrubs at the foot of each palm
    for px, pz, _h in PALMS:
        for _ in range(2):
            ox, oz = px + rng.uniform(-1.6, 1.6), pz + rng.uniform(-1.6, 1.6)
            if free(ox, oz):
                shrub(b, rng, ox, oz, ground(ox, oz), rng.uniform(0.4, 0.8))
