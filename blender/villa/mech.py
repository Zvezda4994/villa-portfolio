"""The aquarium's mech: a downloaded model (config.MECH_MODEL), posed as a pilotless
machine that sat down in the corner of the tank and shut off there, repainted, weathered
and grown over with moss.

It sits on the sand at the right-hand end of the tank, its back and left shoulder against
the side glass, turned about 30° toward the sofa. It has slumped: the torso sags and
twists toward the glass, the shoulders have dropped, the head hangs forward, tipped
toward the glass. The right leg is stretched out along the sand and the left knee is half
raised, falling outward. The right arm hangs, the back of its hand on the sand, palm up;
the left forearm lies loosely over the raised knee. The model's own katana grip has been
taken from its hand and is now the hilt of a long blade driven in through its belly at an
angle, out into the sand beside it; its shield lies on the sand at its right side; the
big swept wings on its back are cut down to their roots so it can sit against the glass.

How it is posed. The model is one fused mesh with no rig (mech_source.py thins it). A
skeleton of SKELETON points is placed inside it by hand (in the model's own frame: y up,
facing +z, about one unit tall, +x its left). Every point is weighted to its nearest
bones, blending smoothly into the parent or child bone near a joint, and each bone is
turned to a target direction in POSE (plus a twist about itself). The katana grip and
the shield are cut out by position and moved as rigid pieces.

How it is painted. The model's own colours only say what each point is: its white
panels become weathered gunmetal under worn, faded bone paint, its red trim dark metal,
its gold trim tarnished bronze, its dark joints darker still; the texture's shading and
panel lines are kept. Then chipped edges (where the surface bends sharply), rust runs,
silt low down and moss on whatever faces up on the head, shoulders and thighs, raised off
the surface in lumps with strands hanging from it. A made-up unit number, 417, is
stencilled in black on a small plate on the front of the right shoulder (toward the sofa)
over a faded red band.

Plain numpy except mech_source (which needs Blender), so the pose can be checked quickly
outside Blender from build/mech_source.npz.
"""
import math

import numpy as np

TARGET_TOP = 1.40            # the top of its head (its crest), metres above the room's floor
YAW = -60.0                  # facing into the tank, turned 30° from the side glass toward the sofa
NOISE = 2.5                  # wear, moss and silt are laid out in the model's frame times this
UNIT = "417"                 # the stencilled unit number (made up)
MOSS = 1.0                   # (0 to look at the bare mech while posing it)


# ---- colours, sRGB ------------------------------------------------------------------------------
GUNMETAL = np.array([0.205, 0.215, 0.24])
DARK_METAL = np.array([0.115, 0.115, 0.12])  # what was red trim
BRONZE = np.array([0.30, 0.25, 0.16])       # what was gold trim, tarnished
FRAME = np.array([0.075, 0.08, 0.09])       # the dark joints
VISOR = np.array([0.03, 0.06, 0.06])
PAINT = np.array([0.56, 0.55, 0.51])        # faded bone white
RED = np.array([0.56, 0.21, 0.15])          # the plate's faded red band
STENCIL = np.array([0.07, 0.07, 0.07])
STEEL = np.array([0.62, 0.62, 0.61])
RUST = np.array([0.36, 0.19, 0.10])
RUST_DARK = np.array([0.20, 0.11, 0.07])
SILT = np.array([0.52, 0.47, 0.38])
ALGAE = np.array([0.24, 0.29, 0.15])
BLADE = np.array([0.50, 0.515, 0.535])
MOSS_DARK, MOSS_MID, MOSS_TIP = np.array([0.04, 0.10, 0.03]), np.array([0.10, 0.22, 0.04]), np.array([0.25, 0.40, 0.07])

SRC, BLADE_K, GUARD_K, PLATE_K = 0, 1, 2, 3
PLATE_FACING = (0.22, 0.06, 0.97)   # the plate faces the sofa (in the mech's frame, before it is turned by YAW)
WHITE, REDC, GOLD, DARKC, GREEN = range(5)
DETAIL_MID = 0.80               # the detail picture's plain level (mech_source); the colours are lifted to match
WHITE_UV = (0.997, 0.997)       # a plain white corner of the detail picture, for the parts it doesn't cover
PLATE = dict(size=(0.13, 0.075, 0.007), text=0.036, text_y=0.006, band=(-0.032, -0.022))   # the unit plate, model units


def srgb_to_linear(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---- rotations (as pool.rot and pool.axes) ---------------------------------------------------
def rot(x=0.0, y=0.0, z=0.0):
    """Degrees: first about z (roll), then x (pitch: +y toward +z), then y (+z toward +x)."""
    x, y, z = math.radians(x), math.radians(y), math.radians(z)
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return ry @ rx @ rz


def axes(forward, up):
    """Rotation whose z axis points along `forward` and y axis as close to `up` as it can."""
    f = np.array(forward, float)
    f /= np.linalg.norm(f)
    x = np.cross(np.asarray(up, float), f)
    x /= np.linalg.norm(x)
    return np.stack([x, np.cross(f, x), f], axis=1)


ALONG_X, ALONG_Y = rot(y=90), rot(x=-90)     # turn a piece built along z to lie along x, or y


# ---- primitives: local points, outward quads, and how much of an edge each point is -------------
def _coords(h, r, step, ramp):
    inner = max(h - r, 0.0)
    ends = [inner + (h - inner) * k / ramp for k in range(1, ramp + 1)] if h - inner > 1e-9 else []
    n = max(1, int(math.ceil(2 * inner / step)))
    mid = [-inner + 2 * inner * i / n for i in range(n + 1)] if inner > 1e-9 else [0.0]
    return np.array([-v for v in reversed(ends)] + mid + ends)


def _orient(V, faces, centre):
    """Wind every face anticlockwise seen from outside (`centre` is inside the shape)."""
    out = []
    c = centre if callable(centre) else np.asarray(centre, float)
    for f in faces:
        p = V[list(f)]
        n = np.cross(p[2] - p[0], p[-1] - p[1]) if len(f) == 4 else np.cross(p[1] - p[0], p[2] - p[0])
        m = p.mean(axis=0)
        cc = c(m) if callable(c) else c
        out.append(tuple(f) if np.dot(n, m - cc) >= 0 else tuple(reversed(f)))
    return out


def rbox(size, r, step=0.03, ramp=3, deform=None):
    """A box with rounded edges and corners, centred on the origin, divided evenly
    (about `step` apart) so per-vertex light and paint stay smooth over it."""
    h = np.asarray(size, float) / 2
    r = min(r, float(h.min()) * 0.98)
    cs = [_coords(h[k], r, step, ramp) for k in range(3)]
    index, pts, faces = {}, [], []

    def vid(ijk):
        if ijk not in index:
            index[ijk] = len(pts)
            pts.append((cs[0][ijk[0]], cs[1][ijk[1]], cs[2][ijk[2]]))
        return index[ijk]
    for axis in range(3):
        a, c = [k for k in range(3) if k != axis]
        for fixed in (0, len(cs[axis]) - 1):
            for i in range(len(cs[a]) - 1):
                for j in range(len(cs[c]) - 1):
                    q = []
                    for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        ijk = [0, 0, 0]
                        ijk[axis], ijk[a], ijk[c] = fixed, i + di, j + dj
                        q.append(vid(tuple(ijk)))
                    faces.append(q)
    P = np.array(pts)
    inner = np.maximum(h - r, 0.0)
    Q = np.clip(P, -inner, inner)
    D = P - Q
    m = np.linalg.norm(D, axis=1, keepdims=True)
    m[m < 1e-12] = 1.0
    V = Q + D / m * r
    E = np.clip((1.0 - np.abs(D / m).max(axis=1)) / 0.29, 0.0, 1.0)
    F = _orient(V, faces, (0, 0, 0))
    if deform is not None:
        V = deform(V.copy())
    return V, F, E


def lathe(profile, segs):
    """Spin (radius, z, edge) points round the z axis; radius 0 makes a single pole point."""
    V, E, rings = [], [], []
    for rad, z, e in profile:
        if rad < 1e-9:
            rings.append([len(V)])
            V.append((0.0, 0.0, z))
            E.append(e)
        else:
            ring = []
            for k in range(segs):
                a = 2 * math.pi * k / segs
                ring.append(len(V))
                V.append((rad * math.cos(a), rad * math.sin(a), z))
                E.append(e)
            rings.append(ring)
    F = []
    for r0, r1 in zip(rings, rings[1:]):
        if len(r0) == 1 and len(r1) == 1:
            continue
        if len(r0) == 1:
            F += [(r0[0], r1[k], r1[(k + 1) % segs]) for k in range(segs)]
        elif len(r1) == 1:
            F += [(r0[k], r0[(k + 1) % segs], r1[0]) for k in range(segs)]
        else:
            F += [(r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]) for k in range(segs)]
    V = np.array(V)
    F = _orient(V, F, (0.0, 0.0, (V[:, 2].min() + V[:, 2].max()) / 2))       # (the turned pieces are all convex)
    return V, F, np.array(E)


def cyl(r0, length, r1=None, step=0.03, bevel=0.012, segs=None):
    """A turned piece along +z from 0 to `length`, radius r0 to r1, its ends bevelled and capped."""
    r1 = r0 if r1 is None else r1
    segs = segs or max(10, int(round(2 * math.pi * max(r0, r1) / step)))
    b = min(bevel, length / 3, r0 / 2, r1 / 2)
    prof = [(0.0, 0.0, 0.0)]
    n = max(1, int(round((r0 - b) / step)))
    prof += [((r0 - b) * k / n, 0.0, 0.0) for k in range(1, n)]
    prof += [(r0 - b, 0.0, 1.0), (r0, b, 1.0)]
    m = max(1, int(math.ceil((length - 2 * b) / step)))
    prof += [(r0 + (r1 - r0) * k / m, b + (length - 2 * b) * k / m, 0.0) for k in range(1, m)]
    prof += [(r1, length - b, 1.0), (r1 - b, length, 1.0)]
    n = max(1, int(round((r1 - b) / step)))
    prof += [((r1 - b) * (n - k) / n, length, 0.0) for k in range(1, n)]
    prof += [(0.0, length, 0.0)]
    return lathe(prof, segs)


# ---- noise: smooth random fields over space ---------------------------------------------------
def waves(rng, n, lo, hi, squash=(1.0, 1.0, 1.0)):
    """Roughly -1..1: random plane waves added up, frequencies lo..hi radians per metre.
    `squash` scales the point first (a small y gives vertical streaks)."""
    D = rng.normal(size=(n, 3))
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    fr, ph, a = rng.uniform(lo, hi, n), rng.uniform(0, 2 * math.pi, n), rng.uniform(0.5, 1.0, n)
    norm = math.sqrt(float((a * a).sum()) / 2)
    sq = np.asarray(squash, float)

    def f(P):
        return np.sin((np.asarray(P) * sq) @ D.T * fr + ph) @ a / norm
    return f


def _blade(length, width, thick, step=0.035):
    """A flat blade along +z from its tip (z = 0): a flattened hexagon in section,
    widening over its first 0.3 m. The edge factor marks its two edges."""
    sec = [(0.5, 0.0, 1.0), (0.28, 0.5, 0.0), (-0.28, 0.5, 0.0), (-0.5, 0.0, 1.0), (-0.28, -0.5, 0.0), (0.28, -0.5, 0.0)]
    n = max(2, int(math.ceil(length / step)))
    V, E, F = [(0.0, 0.0, 0.0)], [1.0], []
    for i in range(1, n + 1):
        z = length * i / n
        w = width * min(1.0, (z / 0.30)) ** 0.75
        t = thick * min(1.0, (z / 0.20)) ** 0.6
        for x, y, e in sec:
            V.append((x * w, y * t, z))
            E.append(e)
    ns = len(sec)
    F += [(0, 1 + (k + 1) % ns, 1 + k) for k in range(ns)]
    for i in range(n - 1):
        a, b = 1 + i * ns, 1 + (i + 1) * ns
        F += [(a + k, a + (k + 1) % ns, b + (k + 1) % ns, b + k) for k in range(ns)]
    top = len(V)
    V.append((0.0, 0.0, length))
    E.append(0.0)
    last = 1 + (n - 1) * ns
    F += [(last + k, last + (k + 1) % ns, top) for k in range(ns)]
    V = np.array(V)
    F = _orient(V, F, lambda m: np.array((0.0, 0.0, min(max(m[2], 0.01), length - 0.01))))
    return V, F, np.array(E)


def _grip(length, r, segs=12, step=0.012):
    """A grip wrapped in cord: a cylinder whose radius ripples along it."""
    n = max(4, int(length / step))
    prof = [(0.0, 0.0, 0.0), (r * 0.8, 0.0, 1.0)]
    prof += [(r * (1.0 + 0.10 * math.sin(i * 2.2)), length * i / n, 0.0) for i in range(n + 1)]
    prof += [(r * 0.8, length, 1.0), (0.0, length, 0.0)]
    return lathe(prof, segs)


# ---- the stencil: "417" built from separate pieces, as a stencil would be ------------------------
_GLYPHS = {   # convex pieces on a 5 x 7 grid
    "4": [[(0, 3.9), (1.4, 3.9), (3.0, 7), (1.6, 7)], [(0, 2.3), (5, 2.3), (5, 3.5), (0, 3.5)],
          [(3.2, 7), (4.5, 7), (4.5, 3.9), (3.2, 3.9)], [(3.2, 0), (4.5, 0), (4.5, 1.9), (3.2, 1.9)]],
    "1": [[(2.0, 1.4), (3.3, 1.4), (3.3, 7), (2.0, 7)], [(0.5, 5.0), (1.7, 5.6), (1.7, 6.9), (0.5, 6.3)],
          [(0.6, 0), (4.4, 0), (4.4, 1.0), (0.6, 1.0)]],
    "7": [[(0, 5.8), (4.0, 5.8), (4.0, 7), (0, 7)], [(4.4, 5.8), (5, 5.8), (5, 7), (4.4, 7)],
          [(1.2, 0), (2.6, 0), (5.0, 5.4), (3.5, 5.4)]],
    "0": [[(0, 1), (1.3, 1), (1.3, 6), (0, 6)], [(3.7, 1), (5, 1), (5, 6), (3.7, 6)],
          [(1.0, 6.3), (4.0, 6.3), (4.0, 7), (1.0, 7)], [(1.0, 0), (4.0, 0), (4.0, 0.7), (1.0, 0.7)]],
    "2": [[(0, 5.8), (4.0, 5.8), (4.0, 7), (0, 7)], [(3.7, 3.9), (5, 3.9), (5, 6.6), (3.7, 6.6)],
          [(0, 0), (5, 0), (5, 1.2), (0, 1.2)], [(0, 1.6), (1.3, 1.6), (3.7, 3.5), (2.6, 4.3)]],
    "3": [[(0, 5.8), (4.0, 5.8), (4.0, 7), (0, 7)], [(3.7, 3.9), (5, 3.9), (5, 6.6), (3.7, 6.6)],
          [(1.2, 2.9), (3.6, 2.9), (3.6, 4.0), (1.2, 4.0)], [(3.7, 0.4), (5, 0.4), (5, 3.1), (3.7, 3.1)],
          [(0, 0), (4.0, 0), (4.0, 1.2), (0, 1.2)]],
}


def _in_convex(px, py, poly):
    poly = np.asarray(poly, float)
    area = np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1])
    if area < 0:
        poly = poly[::-1]
    inside = np.ones_like(px, dtype=bool)
    for (x0, y0), (x1, y1) in zip(poly, np.roll(poly, -1, axis=0)):
        inside &= (x1 - x0) * (py - y0) - (y1 - y0) * (px - x0) >= 0
    return inside


def stencil_mask(u, v, text=UNIT, height=0.10):
    """1 where the stencilled number is. u runs across the panel (metres, centred), v up."""
    unit = height / 7.0
    width = len(text) * 5 + (len(text) - 1) * 1.5
    gx = u / unit + width / 2
    gy = v / unit + 3.5
    out = np.zeros_like(u, dtype=bool)
    for i, ch in enumerate(text):
        x0 = i * 6.5
        for poly in _GLYPHS.get(ch, []):
            out |= _in_convex(gx - x0, gy, poly)
    # a rule under the number
    out |= (gx > 0) & (gx < width) & (gy > -1.9) & (gy < -1.1)
    return out


# ---- painting and moss ------------------------------------------------------------------------
def vertex_normals(V, F):
    N = np.zeros_like(V)
    for size in (3, 4):
        fs = np.array([f for f in F if len(f) == size])
        if not len(fs):
            continue
        p = V[fs]
        n = np.cross(p[:, 2] - p[:, 0], p[:, -1] - p[:, 1]) if size == 4 else np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        for k in range(size):
            np.add.at(N, fs[:, k], n)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return N


def _mix(a, b, t):
    t = np.asarray(t, float)[..., None]
    return a * (1 - t) + b * t


def moss_colour(g, f):
    """Fine mottling: dark depths, brighter tips (as the rocks' moss in living.py)."""
    t = np.clip(0.5 + 0.45 * g + 0.25 * f, 0, 1)
    return np.where((t < 0.75)[:, None], _mix(MOSS_DARK, MOSS_MID, t / 0.75), _mix(MOSS_MID, MOSS_TIP, (t - 0.75) / 0.25))


def _ico(level=1):
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    V = [np.array(v) / np.linalg.norm(v) for v in V]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        cache, out = {}, []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m = V[a] + V[b]
                V.append(m / np.linalg.norm(m))
                cache[key] = len(V) - 1
            return cache[key]
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            out += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = out
    return np.array(V), F


def moss_extras(V, N, moss, size, seed=7):
    """Loose cushions of moss on the thickest growth, and strands hanging from its edges,
    `size` metres to a noise unit. Returns (cushions: verts, faces, linear colours) and
    (strands: verts, faces)."""
    rng = np.random.default_rng(seed)
    g, f = waves(rng, 16, 180, 380), waves(rng, 14, 40, 110)
    base, faces0 = _ico(1)
    cv, cf, cc, k = [], [], [], 0
    spots = np.flatnonzero(moss > 0.8)
    for i in rng.choice(spots, size=min(14, len(spots)), replace=False):
        n = N[i]
        r = rng.uniform(0.018, 0.040) * size
        R = axes(n, (0, 1, 0) if abs(n[1]) < 0.9 else (1, 0, 0))
        lump = 1.0 + 0.25 * rng.normal(size=len(base))
        W = V[i] + n * r * 0.15 + ((base * lump[:, None]) * np.array((r, r, r * 0.55))) @ R.T
        cv.append(W)
        cf += [tuple(k + j for j in fc) for fc in faces0]
        k += len(W)
        cc.append(moss_colour(g(W / size), f(W / size)) * (0.8 + 0.35 * np.clip(base[:, 2], 0, 1))[:, None])
    sv, sf, k = [], [], 0
    edges = np.flatnonzero((moss > 0.35) & (np.abs(N[:, 1]) < 0.45))
    for i in rng.choice(edges, size=min(12, len(edges)), replace=False):
        L = rng.uniform(0.05, 0.20) * size
        w0 = rng.uniform(0.008, 0.016) * size
        sway = rng.normal(0, 0.03, 3) * (1, 0, 1) * size
        out = np.array((N[i][0], 0.0, N[i][2]))
        out = out / (np.linalg.norm(out) + 1e-9)
        across = np.cross(out, (0, 1, 0))
        pts = []
        for j in range(5):
            t = j / 4
            c = V[i] + out * (0.01 + 0.02 * t) * size + np.array((0, -L * t, 0)) + sway * t * t
            hw = w0 * (1 - 0.75 * t) / 2
            pts += [c - across * hw, c + across * hw]
        sv.append(np.array(pts))
        sf += [(k + 2 * j, k + 2 * j + 1, k + 2 * j + 3, k + 2 * j + 2) for j in range(4)]
        k += len(pts)
    cush = (np.concatenate(cv), cf, srgb_to_linear(np.clip(np.concatenate(cc), 0, 1))) if cv else None
    strands = (np.concatenate(sv), sf) if sv else None
    return cush, strands


# ---- the skeleton, in the model's own frame (y up, facing +z, +x its left) -------------------
SKELETON = dict(
    pelvis=(0.0, 0.03, 0.11), waist=(0.0, 0.10, 0.12), neck=(0.0, 0.29, 0.09), headtop=(0.0, 0.41, 0.08),
    S_R=(-0.15, 0.27, 0.12), E_R=(-0.23, 0.16, 0.12), W_R=(-0.26, 0.045, 0.24), T_R=(-0.27, -0.03, 0.20),
    S_L=(0.15, 0.27, 0.11), E_L=(0.21, 0.155, 0.08), W_L=(0.19, 0.0, 0.12), T_L=(0.19, -0.06, 0.13),
    H_R=(-0.08, 0.03, 0.11), K_R=(-0.16, -0.21, 0.10), A_R=(-0.20, -0.44, 0.13), O_R=(-0.21, -0.49, 0.26),
    H_L=(0.08, 0.03, 0.11), K_L=(0.14, -0.23, 0.12), A_L=(0.21, -0.44, 0.11), O_L=(0.22, -0.49, 0.24))
BONES = [  # name, from, to, parent, how much moss it may carry
    ("pelvis", "pelvis", "waist", None, 0.0), ("spine", "waist", "neck", "pelvis", 0.0),
    ("head", "neck", "headtop", "spine", 0.7),
    ("uarm_R", "S_R", "E_R", "spine", 0.7), ("farm_R", "E_R", "W_R", "uarm_R", 0.0), ("hand_R", "W_R", "T_R", "farm_R", 0.0),
    ("uarm_L", "S_L", "E_L", "spine", 0.7), ("farm_L", "E_L", "W_L", "uarm_L", 0.0), ("hand_L", "W_L", "T_L", "farm_L", 0.0),
    ("thigh_R", "H_R", "K_R", "pelvis", 0.6), ("shin_R", "K_R", "A_R", "thigh_R", 0.0), ("foot_R", "A_R", "O_R", "shin_R", 0.0),
    ("thigh_L", "H_L", "K_L", "pelvis", 0.6), ("shin_L", "K_L", "A_L", "thigh_L", 0.0), ("foot_L", "A_L", "O_L", "shin_L", 0.0)]
# Each bone's direction once posed, in the mech's frame (+x its left, the glass side; +z
# forward), and a twist about itself in degrees. Bones left out keep their parent's turn.
POSE = dict(
    pelvis=((0.10, 0.96, -0.26), 0.0),            # sat back against the glass
    spine=((0.20, 0.97, -0.08), 5.0),             # sagging toward the glass, turned a little toward it
    head=((0.42, 0.80, 0.43), -8.0),              # bowed, tipped against the glass, the face still showing
    uarm_R=((-0.15, -0.88, 0.45), 0.0),           # the right arm hangs...
    farm_R=((-0.14, -0.60, 0.79), 0.0),
    hand_R=((-0.10, -0.22, 0.97), 0.0),           # ...the back of its hand on the sand, palm up
    uarm_L=((0.10, -0.55, 0.83), 0.0),            # the left forearm over the raised knee
    farm_L=((-0.55, -0.25, 0.80), 0.0),
    hand_L=((-0.20, -0.95, 0.20), 0.0),
    thigh_R=((-0.62, -0.06, 0.78), 0.0),          # the right leg stretched out along the sand, angled back toward the glass
    shin_R=((-0.66, -0.05, 0.75), 0.0),
    foot_R=((-0.60, 0.78, 0.15), 0.0),            # toes up, fallen outward
    thigh_L=((0.12, 0.90, 0.42), 0.0),            # the left knee drawn up high, falling outward a little
    shin_L=((0.02, -0.99, -0.05), 0.0),
    foot_L=((0.15, -0.10, 0.98), 0.0),
)
SIGMA = 0.018                # how softly a point's weight passes from one bone to the next


def _katana(V):
    """The katana's grip (pommel to guard) in the model's right hand."""
    P0, G = np.array((-0.301, 0.181, 0.451)), np.array((-0.247, 0.06, 0.215))
    u = (G - P0) / np.linalg.norm(G - P0)
    t = (V - P0) @ u
    r = np.linalg.norm(V - P0 - np.outer(t, u), axis=1)
    return (t > -0.03) & (t < np.linalg.norm(G - P0) - 0.035) & (r < 0.035), P0, G


def _cut(V):
    """What goes: the shield on the left arm and the big swept wings on the back (anything
    behind the body that stands well clear of the skeleton), but not the backpack."""
    S = {k: np.array(v) for k, v in SKELETON.items()}
    D = np.min(np.stack([_seg_dist(V, S[a], S[b]) for _, a, b, _, _ in BONES], axis=1), axis=1)
    shield = (V[:, 0] > 0.245) & (V[:, 1] > -0.33) & (V[:, 1] < 0.31)
    pack = (np.abs(V[:, 0]) < 0.10) & (V[:, 1] > 0.12) & (V[:, 2] > -0.10)
    wings = ((V[:, 2] < -0.09) | ((D > 0.07) & (V[:, 2] < 0.02))) & ~pack
    return shield | wings


def _seg_dist(V, a, b):
    ab = b - a
    t = np.clip((V - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(V - (a + np.outer(t, ab)), axis=1)


def skin(V):
    """Each point's weights on the bones: its nearest bone, blending into that bone's
    parent or children (never further) where it is nearly as close to them."""
    S = {k: np.array(v) for k, v in SKELETON.items()}
    names = [b[0] for b in BONES]
    D = np.stack([_seg_dist(V, S[a], S[b]) for _, a, b, _, _ in BONES], axis=1)
    near = np.argmin(D, axis=1)
    nb = len(BONES)
    ok = np.eye(nb, dtype=bool)
    for i, (_, _, _, parent, _) in enumerate(BONES):
        if parent:
            j = names.index(parent)
            ok[i, j] = ok[j, i] = True
    Wt = np.exp(-((D - D.min(axis=1, keepdims=True)) / SIGMA) ** 2) * ok[near]
    return Wt / Wt.sum(axis=1, keepdims=True)


def _align(a, b):
    a, b = np.asarray(a, float) / np.linalg.norm(a), np.asarray(b, float) / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a @ b)
    if c < -0.9999:
        p = np.cross(a, (1, 0, 0) if abs(a[0]) < 0.9 else (0, 1, 0))
        p /= np.linalg.norm(p)
        return 2 * np.outer(p, p) - np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def _about(axis, deg):
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    a = math.radians(deg)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


def solve():
    """Each bone's turn and where its root joint ends up: {bone: (R, rest root, posed root)}."""
    S = {k: np.array(v) for k, v in SKELETON.items()}
    out = {}
    for name, a, b, parent, _ in BONES:
        if parent is None:
            root = S[a]
        else:
            Rp, rp, pp = out[parent]
            root = pp + Rp @ (S[a] - rp)
        if name in POSE:
            d, tw = POSE[name]
            R = _about(d, tw) @ _align(S[b] - S[a], d)
        else:
            R = out[parent][0]
        out[name] = (R, S[a], root)
    return out


def bone_point(sol, bone, p):
    R, rest, root = sol[bone]
    return root + R @ (np.asarray(p, float) - rest)


def deform(V, Wt, sol):
    out = np.zeros_like(V)
    for i, (name, *_rest) in enumerate(BONES):
        R, rest, root = sol[name]
        w = Wt[:, i]
        m = w > 1e-4
        out[m] += w[m, None] * (root + (V[m] - rest) @ R.T)
    return out


def _edges(V, F, N):
    """How sharply the surface bends at each point (0 flat, 1 a crisp edge)."""
    acc = np.zeros_like(N)
    for a, b in ((0, 1), (1, 2), (2, 0)):
        np.add.at(acc, F[:, a], N[F[:, b]])
        np.add.at(acc, F[:, b], N[F[:, a]])
    acc /= np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-9)
    return np.clip((1.0 - np.sum(N * acc, axis=1)) * 7.0, 0, 1)


def _plate_frame(V, N):
    """Where the unit plate goes: the flat front face of the right shoulder armour."""
    m = (V[:, 0] > -0.31) & (V[:, 0] < -0.15) & (V[:, 1] > 0.21) & (V[:, 1] < 0.33) & (N[:, 2] > 0.75)
    m &= V[:, 2] > np.percentile(V[m, 2], 60)
    c, n = V[m].mean(axis=0), N[m].mean(axis=0)
    n /= np.linalg.norm(n)
    return c, axes(n, (0, 1, 0))


def classify(C):
    """What each point of the model was: white panel, red trim, gold trim, dark joint, visor."""
    r, g, b = C[:, 0], C[:, 1], C[:, 2]
    lum = C.mean(axis=1)
    red = (r > g + 0.12) & (r > b + 0.10)
    gold = (r > b + 0.10) & (g > b + 0.06) & ~red
    green = (g > r + 0.08) & (g > b + 0.02)
    dark = (lum < 0.22) & ~red & ~gold & ~green
    cls = np.full(len(C), WHITE)
    cls[red], cls[gold], cls[dark], cls[green] = REDC, GOLD, DARKC, GREEN
    shade = np.ones(len(C))
    for k in range(5):                  # keep the texture's shading and panel lines, relative to its class
        m = cls == k
        if m.sum():
            shade[m] = np.clip(lum[m] / max(np.median(lum[m]), 1e-3), 0.45, 1.25) ** 0.8
    return cls, shade


def paint(Vn, N, E, kind, cls, shade, mossw, decal, floor_n, paintw, seed=417):
    """Colours (sRGB), moss thickness (noise units) and moss amount for every point.
    Vn is each point's place in noise units (the model's frame times NOISE), N the
    posed normals, floor_n the sand's height in noise units."""
    rng = np.random.default_rng(seed)
    wear, fine, grain = waves(rng, 10, 3, 9), waves(rng, 14, 40, 110), waves(rng, 16, 180, 380)
    streak = waves(rng, 12, 40, 110, squash=(1.0, 0.05, 1.0))
    patch, lumps = waves(rng, 10, 5, 14), waves(rng, 12, 25, 60)
    w, f, g, st = wear(Vn), fine(Vn), grain(Vn), streak(Vn)
    rnd = rng.random(len(Vn))
    ny = N[:, 1]
    src = kind == SRC

    base = np.array([GUNMETAL, DARK_METAL, BRONZE, FRAME, VISOR])[cls] * shade[:, None] / DETAIL_MID
    C = np.where(src[:, None], base, np.array([GUNMETAL, BLADE, GUNMETAL * 0.8, GUNMETAL])[kind])
    C = C * (0.92 + 0.10 * (0.5 + 0.5 * f) + 0.04 * g)[:, None]

    # faded paint over what were the white panels, worn through in ragged patches and at edges
    cover = np.clip(((0.5 + 0.5 * w) + 0.08 * f + 0.04 * g - 0.05) * 4.0 - E * 1.2, 0, 1) * paintw
    pc = PAINT * (0.93 + 0.10 * (0.5 + 0.5 * g))[:, None] / np.where(src, DETAIL_MID, 1.0)[:, None]
    pc = _mix(pc, np.array([0.50, 0.51, 0.50]), np.clip(0.30 - 0.30 * w, 0, 0.45))
    C = _mix(C, pc, cover)

    # the unit plate: a field of paint, a faded red band, the stencilled number
    has = ~np.isnan(decal[:, 0])
    field = np.zeros(len(Vn))
    if has.any():
        d, P = decal[has], PLATE
        front = d[:, 2] > P["size"][2] / 2 - 0.001
        field[has] = front
        col = PAINT * (0.95 + 0.08 * f[has, None])
        band = front & (d[:, 1] > P["band"][0]) & (d[:, 1] < P["band"][1])
        col = np.where(band[:, None], RED * (0.9 + 0.15 * f[has, None]), col)
        mark = front & stencil_mask(d[:, 0], d[:, 1] - P["text_y"], height=P["text"]) & (f[has] + 0.4 * g[has] > -1.05)
        col = np.where(mark[:, None], STENCIL, col)
        C[has] = np.where(front[:, None], col, C[has])

    # chipped edges: bright steel, a little rust round them
    metal = (kind != PLATE_K) | ~(field > 0)
    chipness = E * 0.80 + 0.25 * f + 0.25 * rnd
    chip = metal & (E > 0.55) & (chipness > 0.97)
    halo = metal & (E > 0.45) & (chipness > 0.88) & ~chip
    C = np.where(halo[:, None], _mix(C, RUST_DARK, 0.45), C)
    C = np.where(chip[:, None], STEEL * (0.85 + 0.2 * rnd)[:, None], C)
    C = np.where(((kind == BLADE_K) & (E > 0.5))[:, None], _mix(C, STEEL * 1.25, 0.8), C)

    # thin rust runs down the sides, rust patches on the blade
    side = np.clip(1.0 - np.abs(ny) * 1.6, 0, 1)
    runs = np.clip((0.5 + 0.5 * st - 0.74) * 4.0, 0, 1) * side * (1 - field)
    C = _mix(C, RUST, runs * 0.45)
    C = _mix(C, RUST, (kind == BLADE_K) * np.clip((w + 0.4 * f - 0.3) * 1.5, 0, 0.35))

    # a little algae, silt on what faces up and banked round the bottom
    C = _mix(C, ALGAE, 0.03 + 0.05 * (0.5 + 0.5 * w))
    C = _mix(C, SILT, np.clip(ny, 0, 1) ** 2 * 0.16 * (0.6 + 0.4 * rnd))
    C = _mix(C, SILT, np.clip((floor_n + 0.18 - Vn[:, 1]) / 0.18, 0, 1) * 0.6)

    # moss: thick on the tops, ragged at the edges, creeping into the hollows
    reach = ny * 2.0 - 1.15 + 0.40 * patch(Vn) + 0.12 * f + 0.05 * g
    moss = np.clip(reach * 2.4, 0, 1) * mossw * (1 - field) * ~(src & (cls == GREEN))
    moss = np.clip((moss - 0.12) / 0.45, 0, 1) * (1 - E) ** 2 * MOSS     # patches on the tops; edges stay clean metal
    C = _mix(C, moss_colour(g, f), moss ** 0.7)
    thick = moss ** 0.8 * (0.022 + 0.016 * (0.5 + 0.5 * lumps(Vn)) + 0.006 * g)
    return np.clip(C, 0, 1), thick, moss


def _tris(F):
    """Faces as triangles (quads split in two)."""
    out = []
    for f in F:
        out.append(f[:3])
        if len(f) == 4:
            out.append((f[0], f[2], f[3]))
    return np.array(out, dtype=np.int64)


def _sub(mask, F):
    """The faces wholly inside `mask`, renumbered to the points it keeps."""
    idx = np.flatnonzero(mask)
    remap = np.full(len(mask), -1)
    remap[idx] = np.arange(len(idx))
    keep = mask[F].all(axis=1)
    return idx, remap[F[keep]], keep


JOINT_OF = {"neck": "neck", "shoulder+": "S_L", "shoulder-": "S_R", "elbow+": "E_L", "elbow-": "E_R", "wrist+": "W_L",
            "wrist-": "W_R", "hip+": "H_L", "hip-": "H_R", "knee+": "K_L", "knee-": "K_R", "ankle+": "A_L", "ankle-": "A_R"}


def build(height, side_x, z_range, source=None, z_guess=-7.25):
    """The mech, posed, painted, scaled and pushed into the tank's right-hand end, or None
    if no model is set. `height(x, z)` is the sand; `side_x` how far right it may reach
    (the side glass); `z_range` (back, front) for the rest of it. Returns (verts, faces,
    linear colours, info); info has key points in the world (for the plants and fish),
    its seat, the moss cushions and strands, and each face's UVs on the detail picture."""
    if source is None:
        from .mech_source import load
        source = load()
        if source is None:
            return None
    V0, F0, C0, UV0 = (np.asarray(a, float) for a in source)
    F0 = F0.astype(np.int64)
    grip, P0, G = _katana(V0)
    body = ~grip & ~_cut(V0)
    N0 = vertex_normals(V0, F0)

    sol = solve()
    parts = []          # (posed points, faces, rest points, kind, class, moss, decal, edge, bone paint, face UVs)
    white = np.array(WHITE_UV)
    bi, BF, keep = _sub(body, F0)
    Vb = V0[bi]
    Wt = skin(Vb)
    Pb = deform(Vb, Wt, sol)
    cls, _shade = classify(C0[bi])
    mossw = Wt @ np.array([b[4] for b in BONES])
    Nb = vertex_normals(Pb, BF)
    # bone paint survives only on a few plates: the chest, the right shoulder, the left shin
    names = [b[0] for b in BONES]
    dom = np.argmax(Wt, axis=1)
    chest = (dom == names.index("spine")) & (Vb[:, 1] > 0.13) & (Vb[:, 1] < 0.30) & (Vb[:, 2] > 0.13)
    shoulder = (dom == names.index("uarm_R")) & (Vb[:, 1] > 0.20)
    shin = (dom == names.index("shin_L")) & (Vb[:, 2] > 0.10)
    plates = (chest | shoulder | shin) & (cls == WHITE)
    parts.append((Pb, BF, Vb, np.full(len(Pb), SRC), cls, mossw, None, _edges(Pb, BF, Nb), plates.astype(float), UV0[keep]))
    floor = Pb[:, 1].min()

    # the unit plate, on the front of the right shoulder armour, carried by the upper arm
    c, Rp = _plate_frame(V0, N0)
    pv, pf, pe = rbox(PLATE["size"], 0.002, step=0.003, ramp=1)
    Rf = axes(PLATE_FACING, (0, 1, 0))
    at = bone_point(sol, "uarm_R", c) + Rf @ np.array((0.0, -0.01, 0.012))
    rest = c + pv @ Rp.T
    pf = _tris(pf)
    parts.append((at + pv @ Rf.T, pf, rest, np.full(len(pv), PLATE_K), None, np.zeros(len(pv)), pv, pe, None,
                  np.broadcast_to(white, (len(pf), 3, 2))))

    # the sword: the katana's grip on a long blade, in through the belly and down into the
    # sand beside the right hip
    entry = bone_point(sol, "spine", (0.025, 0.125, 0.25))
    tip = bone_point(sol, "thigh_R", SKELETON["H_R"]) + np.array((-0.13, 0.0, 0.02))
    tip[1] = floor - 0.05
    d = (entry - tip) / np.linalg.norm(entry - tip)
    guard = entry + d * 0.05
    across = np.cross((0, 1, 0), d)
    across /= np.linalg.norm(across)
    Rs = np.stack([across, np.cross(d, across), d], axis=1)
    bv, bf, be = _blade(float(np.linalg.norm(guard - tip)), 0.052, 0.010, step=0.012)
    pts = tip + bv @ Rs.T
    bf = _tris(bf)
    parts.append((pts, bf, pts, np.full(len(bv), BLADE_K), None, np.zeros(len(bv)), None, be, None,
                  np.broadcast_to(white, (len(bf), 3, 2))))
    tv, tf, te = cyl(0.034, 0.009, step=0.008, bevel=0.002)
    pts = guard + tv @ Rs.T
    tf = _tris(tf)
    parts.append((pts, tf, pts, np.full(len(tv), GUARD_K), None, np.full(len(tv), 0.3), None, te, None,
                  np.broadcast_to(white, (len(tf), 3, 2))))
    gi, GF, gkeep = _sub(grip, F0)
    Rg = _align(G - P0, -d)
    pts = guard + d * 0.009 + (V0[gi] - G) @ Rg.T
    gcls, _gshade = classify(C0[gi])
    parts.append((pts, GF, V0[gi], np.full(len(gi), SRC), gcls, np.full(len(gi), 0.15), None,
                  _edges(pts, GF, vertex_normals(pts, GF)), None, UV0[gkeep]))

    # put it together
    P, F, Rest, kind, CL, MW, DEC, E, PW, UV = [], [], [], [], [], [], [], [], [], []
    n = 0
    for pts, fc, rest, k, cl, mw, dec, e, pw, uv in parts:
        P.append(pts)
        F.append(np.asarray(fc) + n)
        Rest.append(rest)
        kind.append(k)
        CL.append(cl if cl is not None else np.zeros(len(pts), int))
        MW.append(mw)
        DEC.append(dec if dec is not None else np.full((len(pts), 3), np.nan))
        E.append(np.asarray(e, float))
        PW.append(pw if pw is not None else np.zeros(len(pts)))
        UV.append(np.asarray(uv, float))
        n += len(pts)
    P, F, Rest = np.concatenate(P), np.concatenate(F), np.concatenate(Rest)
    kind, CL, MW, DEC, E, PW, UV = (np.concatenate(a) for a in (kind, CL, MW, DEC, E, PW, UV))
    P = P - np.array((0.0, floor, 0.0))                 # the seat on y = 0
    head_top = P[:len(Pb)][Wt[:, 2] > 0.5, 1].max()

    # scale it, turn it, settle it into the corner on the sand
    Ry = rot(y=YAW)
    x, z, ground = side_x - 0.3, z_guess, 0.0
    for _ in range(4):
        ground = height(x, z) - 0.02
        scale = (TARGET_TOP - ground) / head_top
        Q = (P * scale) @ Ry.T
        x = side_x - Q[:, 0].max()
        z = min(max(z, z_range[0] - Q[:, 2].min()), z_range[1] - Q[:, 2].max())

    def place(Q):
        return np.array((x, ground, z)) + ((np.asarray(Q) - np.array((0.0, floor, 0.0))) * scale) @ Ry.T
    W = np.array((x, ground, z)) + (P * scale) @ Ry.T
    N = vertex_normals(W, F)
    C, thick, moss = paint(Rest * NOISE, N, E, kind, CL, np.ones(len(P)), MW, DEC, (Rest[:len(Pb), 1].min()) * NOISE, PW)
    size = scale / NOISE
    W = W + N * (thick * size)[:, None]
    cush, strands = moss_extras(W, N, moss, size)
    S = {k: np.array(v) for k, v in SKELETON.items()}
    pts = {}
    for key, j in JOINT_OF.items():
        bone = next(b for b in BONES if b[1] == j or b[2] == j)
        pts[key] = place(bone_point(sol, bone[0], S[j]))
    pts.update(sword_tip=place(tip), sword_entry=place(entry), guard=place(guard))
    info = dict(points=pts, seat=(x, ground, z), scale=scale, cushions=cush, strands=strands)
    info["uvs"] = [[tuple(c) for c in face] for face in UV]
    return W, [tuple(f) for f in F], srgb_to_linear(C), info
