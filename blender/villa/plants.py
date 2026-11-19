"""Date palms, agaves, desert shrubs and rocks, all generated so nothing needs a license.

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
    from .exterior import PLANTERS
    rng = random.Random(7)
    for x, z, h in PALMS:
        palm(b, rng, x, z, h)
    scatter(b, rng)
    edges(b, random.Random(11))
    for p in PLANTERS:
        plant_planter(b, random.Random(5), p)


# ---- palms -----------------------------------------------------------------
def _norm(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def _cross(a, c):
    return (a[1] * c[2] - a[2] * c[1], a[2] * c[0] - a[0] * c[2], a[0] * c[1] - a[1] * c[0])


def _add(a, c, k=1.0):
    return (a[0] + c[0] * k, a[1] + c[1] * k, a[2] + c[2] * k)


def palm(b, rng, x, z, height, base=G):
    """A date palm whose crown sits at `height`. `base` is the ground it grows
    from (the sand, or the soil in a planter)."""
    lean_dir = rng.uniform(0, 2 * math.pi)
    lean = rng.uniform(0.02, 0.09) * (height - base)
    trunk(b, rng, x, z, height, lean_dir, lean, base)

    top = (x + math.cos(lean_dir) * lean, height, z + math.sin(lean_dir) * lean)
    count = 24
    for f in range(count):
        age = f / (count - 1)                       # 0 = newest, standing up; 1 = oldest, hanging down
        azimuth = f * 2.39996 + rng.uniform(-0.2, 0.2)
        frond(b, rng, top, azimuth,
              start=math.radians(78 - 95 * age ** 0.85),
              droop=math.radians(55 + 45 * age),
              length=rng.uniform(2.9, 3.7) * (0.75 + 0.25 * math.sin(math.pi * min(1.0, age + 0.25))))


def trunk(b, rng, x, z, height, lean_dir, lean, base=G):
    """A date palm trunk: a stack of short rings, each swelling out to a ledge where
    an old leaf was cut off. Every other ring is turned half a step, so the stubs
    form the diamond pattern real trunks have. Low sun picks the ledges out."""
    sides = 12
    rings = max(8, int((height - base + 0.2) / rng.uniform(0.26, 0.32)))

    def centre(t):
        return x + math.cos(lean_dir) * lean * t * t, z + math.sin(lean_dir) * lean * t * t

    rows = []                                   # (height fraction, radius factor, half-step turn)
    for k in range(rings):
        for frac, swell in ((0.0, 0.92), (0.55, 1.0), (0.9, 1.11)):
            rows.append(((k + frac) / rings, swell, 0.5 * (k % 2)))
    rows.append((1.0, 0.95, 0.0))
    verts, faces = [], []
    for t, swell, turn in rows:
        cx, cz = centre(t)
        radius = (0.27 - 0.08 * t + 0.12 * (1 - t) ** 8) * swell     # tapers upward, flares at the foot
        for s in range(sides):
            a = 2 * math.pi * (s + turn) / sides
            verts.append((cx + math.cos(a) * radius, base - 0.2 + t * (height - base + 0.2), cz + math.sin(a) * radius))
    for r in range(len(rows) - 1):
        for s in range(sides):
            a, c = r * sides + s, r * sides + (s + 1) % sides
            faces.append((a, a + sides, c + sides, c))
    b.mesh("out", "bark", verts, faces, smooth=True)

    # A collar of stubby old leaf bases just under the crown.
    cx, cz = centre(1.0)
    stubs, sfaces = [], []
    for row in range(2):
        for i in range(14):
            az = 2 * math.pi * (i + 0.5 * row) / 14 + rng.uniform(-0.1, 0.1)
            out = (math.cos(az), 0.0, math.sin(az))
            side = (-math.sin(az), 0.0, math.cos(az))
            up_angle = math.radians(rng.uniform(30, 55))
            d = _norm((out[0] * math.cos(up_angle), math.sin(up_angle), out[2] * math.cos(up_angle)))
            root = (cx + out[0] * 0.2, height - 0.15 - 0.22 * row, cz + out[2] * 0.2)
            tip = _add(root, d, rng.uniform(0.25, 0.4))
            w = 0.06
            j = len(stubs)
            stubs += [_add(root, side, -w), _add(root, side, w), _add(tip, side, w * 0.4), _add(tip, side, -w * 0.4)]
            sfaces.append((j, j + 1, j + 2, j + 3))
    b.mesh("out", "bark", stubs, sfaces, smooth=False)


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


def agave(b, rng, x, z, y, size):
    """A blue-green rosette of thick, pointed, slightly folded leaves."""
    verts, faces = [], []
    n = rng.randint(16, 22)
    for i in range(n):
        layer = i / (n - 1)                                  # 0 = inner leaves, standing up
        az = i * 2.39996 + rng.uniform(-0.15, 0.15)
        elev = math.radians(80 - 52 * layer + rng.uniform(-6, 6))
        long = size * (0.55 + 0.45 * layer) * rng.uniform(0.85, 1.05)
        w = size * 0.11 * (0.8 + 0.4 * layer)
        d = (math.cos(elev) * math.cos(az), math.sin(elev), math.cos(elev) * math.sin(az))
        side = (-math.sin(az), 0.0, math.cos(az))
        fold = _norm(_cross(side, d))                       # the midrib stands proud of the edges
        root = (x, y + 0.02, z)
        mid = _add(root, d, long * 0.45)
        tip = _add(_add(root, d, long), (0.0, -1.0, 0.0), long * 0.15 * layer)
        j = len(verts)
        verts += [_add(root, side, -w * 0.6), _add(root, fold, w * 0.15), _add(root, side, w * 0.6),
                  _add(mid, side, -w), _add(mid, fold, w * 0.3), _add(mid, side, w), tip]
        faces += [(j, j + 1, j + 4, j + 3), (j + 1, j + 2, j + 5, j + 4), (j + 3, j + 4, j + 6), (j + 4, j + 5, j + 6)]
    b.mesh("out", "agave", verts, faces, smooth=False)


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
    """A weathered boulder: a lumpy ball chopped by a few random planes, which
    gives it the flat fractured faces real rock has, then half buried."""
    base, faces = _icosphere()
    waves = [(_norm((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))), rng.uniform(1.5, 4.0),
              rng.uniform(0, 6.28), rng.uniform(0.04, 0.1)) for _ in range(5)]
    cuts = [(_norm((rng.uniform(-1, 1), rng.uniform(-0.3, 1), rng.uniform(-1, 1))), rng.uniform(0.5, 0.8)) for _ in range(rng.randint(4, 7))]
    sx, sy, sz = size * rng.uniform(0.8, 1.5), size * rng.uniform(0.5, 0.85), size * rng.uniform(0.7, 1.2)
    turn = rng.uniform(0, 6.28)
    ct, st = math.cos(turn), math.sin(turn)
    verts = []
    for p in base:
        k = 1.0 + sum(a * math.sin((p[0] * d[0] + p[1] * d[1] + p[2] * d[2]) * fr + ph) for d, fr, ph, a in waves)
        q = (p[0] * k, p[1] * k, p[2] * k)
        for n, depth in cuts:                     # push anything beyond a cut back onto its plane
            over = q[0] * n[0] + q[1] * n[1] + q[2] * n[2] - depth
            if over > 0:
                q = (q[0] - n[0] * over, q[1] - n[1] * over, q[2] - n[2] * over)
        px, py, pz = q[0] * sx, q[1] * sy, q[2] * sz
        verts.append((x + px * ct - pz * st, y + py - sy * 0.15, z + px * st + pz * ct))
    b.mesh("out", "rock", verts, faces, smooth=False)


def _ground(x, z):
    from .terrain import height
    import numpy as np
    return float(height(np.array([x]), np.array([z]))[0])


def _clear_of_paving(x, z, margin):
    from .terrain import edge_distance
    import numpy as np
    return float(edge_distance(np.array([x]), np.array([z]))[0]) > margin


def scatter(b, rng):
    """Sprinkle shrubs and rocks over the open sand further out."""
    def free(x, z):
        return _clear_of_paving(x, z, 3.0) and not (-13.5 < x < -3.9 and z > 0)

    placed = 0
    while placed < 55:
        r = 16 + 80 * rng.random() ** 1.6
        a = rng.uniform(0, 2 * math.pi)
        x, z = r * math.cos(a), r * math.sin(a)
        if not free(x, z):
            continue
        # shrubs come in little clumps
        for _ in range(rng.randint(1, 3)):
            ox, oz = x + rng.uniform(-0.8, 0.8), z + rng.uniform(-0.8, 0.8)
            if free(ox, oz):
                shrub(b, rng, ox, oz, _ground(ox, oz), rng.uniform(0.45, 1.0))
        placed += 1

    placed = 0
    while placed < 38:
        r = 15 + 90 * rng.random() ** 1.4
        a = rng.uniform(0, 2 * math.pi)
        x, z = r * math.cos(a), r * math.sin(a)
        if not free(x, z):
            continue
        rock(b, rng, x, z, _ground(x, z), rng.uniform(0.25, 1.1) * (1.6 if rng.random() < 0.15 else 1.0))
        placed += 1
    # a few shrubs at the foot of each palm
    for px, pz, _h in PALMS:
        for _ in range(2):
            ox, oz = px + rng.uniform(-1.6, 1.6), pz + rng.uniform(-1.6, 1.6)
            if _clear_of_paving(ox, oz, 0.4):
                shrub(b, rng, ox, oz, _ground(ox, oz), rng.uniform(0.4, 0.8))


def edges(b, rng):
    """Rocks, shrubs and the odd agave along the gravel where paving meets sand,
    so no edge runs dead straight into open desert."""
    from .exterior import hard_surfaces

    # Every edge near the house, and the first stretch of the drive.
    spans = []
    for x0, x1, z0, z1 in hard_surfaces():
        z1 = min(z1, 60.0)
        spans += [((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))]
    lengths = [math.dist(a, c) for a, c in spans]
    total = sum(lengths)

    placed = tries = 0
    while placed < 95 and tries < 4000:
        tries += 1
        pick = rng.random() * total
        for (a, c), length in zip(spans, lengths):
            if pick <= length:
                break
            pick -= length
        t = rng.random()
        px, pz = a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t
        # push it outward, mostly within the gravel band
        nx, nz = (c[1] - a[1]) / max(length, 1e-6), -(c[0] - a[0]) / max(length, 1e-6)
        off = 0.35 + 2.2 * rng.random() ** 1.5
        x, z = px + nx * off, pz + nz * off
        if not _clear_of_paving(x, z, 0.3) or any(math.dist((x, z), (qx, qz)) < 1.2 for qx, qz, _ in PALMS):
            continue
        y = _ground(x, z)
        kind = rng.random()
        if kind < 0.38:
            for _ in range(rng.randint(1, 3)):
                rock(b, rng, x + rng.uniform(-0.5, 0.5), z + rng.uniform(-0.5, 0.5), y, rng.uniform(0.12, 0.42))
        elif kind < 0.82:
            for _ in range(rng.randint(1, 3)):
                ox, oz = x + rng.uniform(-0.6, 0.6), z + rng.uniform(-0.6, 0.6)
                if _clear_of_paving(ox, oz, 0.25):
                    shrub(b, rng, ox, oz, _ground(ox, oz), rng.uniform(0.35, 0.8))
        else:
            agave(b, rng, x, z, y, rng.uniform(0.6, 0.95))
        placed += 1


def plant_planter(b, rng, p):
    """Agaves spaced along the planter, with grasses between them."""
    (x0, x1), (z0, z1), soil = p["x"], p["z"], p["soil"]
    zc = (z0 + z1) / 2
    n = max(2, round((x1 - x0) / 1.7))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n + rng.uniform(-0.15, 0.15)
        agave(b, rng, x, zc + rng.uniform(-0.08, 0.08), soil, rng.uniform(0.75, 0.95))
        for _ in range(3):
            gx = x + (x1 - x0) / n * rng.uniform(0.3, 0.55) * rng.choice((-1, 1))
            if x0 + 0.3 < gx < x1 - 0.3:
                shrub(b, rng, gx, zc + rng.uniform(-0.3, 0.3), soil, rng.uniform(0.35, 0.55))
