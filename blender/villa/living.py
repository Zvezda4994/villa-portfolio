"""The living room, furnished: sparse and calm. An L-shaped sofa facing a big OLED on
a walnut stand, the floor-to-ceiling tank behind it, and a moodboard on the east wall.

Plan, looking down, seen from the driveway (the wall to the study and gym at the top,
so +x is on the right):

        study door                  TV on its walnut stand          gym door     (z = 0)
     +---[    ]--------------------[=====[ TV ]=====]------------[    ]---------+
   d |                                                                     (fig) |
   i |                         [coffee table]                                    | e
   n |   (lamp)                                         [chaise]      moodboard  | a
   i |              [========== sofa, facing the TV ===][       ]   [bench]      | s
   n |                         ~~~~~~~~~ rug ~~~~~~~~~~                           | t
   g |                                                                           |
     |        [=========== the tank: floor to ceiling, a moss-covered rock ======]|
     +---[ glass ]-----------------------------------------------------[glass]---+
                         back wall, glass onto the pool deck                 (z = -8)

The room is open to the dining room on its west side. The tank sits in a plaster
niche on the back wall: a glowing backdrop, sand and soil, a big moss-covered rock (in
place of the mech, for now), driftwood, grasses and swords, and a few fish. The TV
shows a paused streaming screen with "Hunter × Hunter" in plain type, no artwork.

The moodboard is five frames in mixed sizes. In the file they are plain colour fields;
the site lays your pictures (assets_src/moodboard/, shrunk by `npm run moodboard`)
over them, picked at random each time the room is opened. Blender's renders show a
fixed pick so the review renders have something in the frames.

Everything is lit per vertex, the walls lined over the house's own (as in the kitchen
and gym), so the room stays clean even from a quick draft bake; it has no lightmap.
"""
import math
import random

import numpy as np

from . import config as C
from .house import H1, P
from .kit import Frame, Kit, grid, panel
from .materials import MATS, srgb_to_linear
from .study import _smooth_noise, book_flat
from .textures import load_pixels, picture_path, save_png

ROOM, G = "living", "ground"

# The room's inside faces. On the west it is open to the dining room (x = 1).
XW = 1.0
XE = C.HALF_W - C.WALL              # the east wall (11.7)
ZB = -C.HALF_D + C.WALL             # the back wall, glass onto the deck (-7.7)
ZN = -P / 2                         # the wall to the study and gym (-0.075)
STUDY_DOOR, GYM_DOOR = (3.0, 4.2), (8.4, 9.6)
GLASS = ((1.2, 4.4), (10.5, 11.5))  # the back wall's two full-height windows
LINING = 0.012                      # the walls' plaster lining stands off the house wall (gotcha 30)

# The tank, in a niche on the back wall between the windows.
TANK = dict(x=(4.75, 10.05), front=-6.62, base=0.30, top=2.78, wing=0.10)
ROCK = (7.05, -7.12)                # the moss-covered rock, where the mech will rest one day
TV_X = 6.30                         # the TV's middle, between the doors
CONSOLE = dict(L=2.40, D=0.44, H=0.50)
SCREEN = (1.841, 1.036)             # 83", 16:9
SOFA = dict(x=4.725, z=-4.75, main=3.15, chaise=1.0, D=1.0, Dc=1.9)
TABLE = dict(x=(5.55, 7.05), z=(-3.20, -2.42), top=0.38)
RUG = dict(x=(4.25, 9.35), z=(-5.45, -1.55), t=0.012)
LAMP = (4.05, -4.45)                # off the rug, beside the sofa's west end
GALLERY_Z = -3.70                   # the moodboard's middle along the east wall

# The moodboard's frames, on the east wall seen face on (x to the right, y up):
# outer edges, the moulding ("black" or "oak", and its width) and the mat's width,
# laid out at a base size, then scaled up by MOODBOARD_SCALE about (0, MOODBOARD_Y)
# so the group reads from the sofa. Scaling every size together keeps each picture's
# shape, so the moodboard numbers in materials.py stay right.
MOODBOARD_SCALE, MOODBOARD_Y = 1.5, 1.78
_FRAMES = [
    dict(x=(-1.10, -0.56), y=(1.70, 2.42), wood="oak", fr=0.030, mat=0.055),
    dict(x=(-0.48, 0.42), y=(1.70, 2.32), wood="black", fr=0.025, mat=0.0),
    dict(x=(0.50, 1.02), y=(1.70, 2.22), wood="black", fr=0.025, mat=0.07),
    dict(x=(-0.90, -0.20), y=(1.10, 1.62), wood="black", fr=0.025, mat=0.0),
    dict(x=(-0.12, 0.38), y=(0.96, 1.62), wood="oak", fr=0.030, mat=0.05),
]
_k, _c = MOODBOARD_SCALE, 1.69                       # the base layout's middle height
FRAMES = [dict(fr, x=tuple((v + 0.04) * _k for v in fr["x"]), y=tuple(MOODBOARD_Y + (v - _c) * _k for v in fr["y"]),
               fr=fr["fr"] * _k, mat=fr["mat"] * _k) for fr in _FRAMES]

CEILING_LIGHT = 0.35
TANK_LIGHT = (0.80, 0.94, 1.0)
LAMPS = []

# Review cameras. The first is also the room's view on the website: standing by the
# study door, looking across the sofa to the tank, the moodboard on the right.
LIVING_CAM = dict(pos=(3.45, 1.45, -0.80), target=(9.40, 1.05, -6.20), fov=55.0)
TV_CAM = dict(pos=(6.10, 1.10, -4.12), target=(6.30, 1.00, -0.10), fov=50.0)
MOODBOARD_CAM = dict(pos=(8.95, 1.74, -3.70), target=(11.70, 1.78, -3.70), fov=50.0)
TANK_CAM = dict(pos=(7.75, 1.30, -5.15), target=(7.00, 0.95, -7.40), fov=55.0)


def build_living(b):
    LAMPS.clear()
    paint_pictures()
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    with b.room(ROOM):
        walls(k)
        tank(k)
        rug(k)
        sofa(k, Frame((SOFA["x"], RUG["t"], SOFA["z"])))
        coffee_table(k)
        console(k)
        tv(k)
        floor_lamp(k)
        fig(k)
        moodboard(k)
        bench(k)


def picture_aspects():
    """Each frame's picture: width / height, inside the moulding and the mat."""
    out = []
    for fr in FRAMES:
        inset = fr["fr"] + fr["mat"]
        out.append((fr["x"][1] - fr["x"][0] - 2 * inset) / (fr["y"][1] - fr["y"][0] - 2 * inset))
    return out


# ---- walls ---------------------------------------------------------------------------------
def walls(k):
    """Plaster linings just over the house's walls, lit per vertex on a grid (as in the
    kitchen and the gym), so the walls stay smooth even from a quick draft bake."""
    from .house import DOOR
    e, m = LINING, "plaster_v"
    tx0, tx1 = TANK["x"][0] - TANK["wing"], TANK["x"][1] + TANK["wing"]
    # the east wall, facing -x: the moodboard's wall, one even grid finer than the other
    # walls', so each frame's shadow stays a narrow edge (a finer patch behind the frames
    # alone showed as a rectangle)
    panel(k, m, (XE - e, 0.0, ZB), (0, 0, ZN - ZB), (0, H1, 0), step=0.10)
    # the ceiling, facing down, with its own downlight fittings: it belongs to the
    # upstairs floor's group, so it lifts off with it in the Ground view
    up = Kit(k.b, "upper", None)
    cy = H1 - 0.014
    panel(up, m, (XW, cy, ZB), (XE - XW, 0, 0), (0, 0, ZN - ZB), step=0.25)
    from .house import downlight_spots
    s = 0.07
    for px, pz in downlight_spots(ROOM):
        up.b.quad("upper", "light_warm", [(px - s, cy - 0.002, pz - s), (px + s, cy - 0.002, pz - s),
                                          (px + s, cy - 0.002, pz + s), (px - s, cy - 0.002, pz + s)])
    # the wall to the study and the gym, facing -z: the TV's wall, round both doors
    # (behind the TV stand it starts at the stand's top: points buried behind a closed box
    # bake dark and muddy the wall above it, gotcha 26)
    s0, s1 = TV_X - CONSOLE["L"] / 2, TV_X + CONSOLE["L"] / 2
    for x0, x1, y0 in ((XW, STUDY_DOOR[0], 0.0), (STUDY_DOOR[1], s0, 0.0), (s0, s1, CONSOLE["H"]), (s1, GYM_DOOR[0], 0.0),
                       (GYM_DOOR[1], XE, 0.0), (STUDY_DOOR[0], STUDY_DOOR[1], DOOR), (GYM_DOOR[0], GYM_DOOR[1], DOOR)):
        panel(k, m, (x1, y0, ZN - e), (x0 - x1, 0, 0), (0, H1 - y0, 0))
    # the back wall, facing +z, either side of the tank's niche
    for x0, x1 in ((GLASS[0][1], tx0), (tx1, GLASS[1][0]), (GLASS[1][1], XE)):
        panel(k, m, (x0, 0.0, ZB + e), (x1 - x0, 0, 0), (0, H1, 0))


# ---- the tank ------------------------------------------------------------------------------
def tank(k):
    """A tank from a low plinth almost to the ceiling, set in a plaster niche: glass in a
    slim black frame, a glowing blue-green backdrop, soil and sand, the moss-covered
    rock, smaller stones, driftwood, grasses along the back, swords and a carpet of
    moss in front, and a few fish."""
    (x0, x1), zf, base, top, wing = TANK["x"], TANK["front"], TANK["base"], TANK["top"], TANK["wing"]
    world = Frame((0.0, 0.0, 0.0))
    zb = ZB + 0.01
    # the niche: plaster wings either side, a fascia over the glass hiding the light
    for wx0, wx1, inner in ((x0 - wing, x0, "+x"), (x1, x1 + wing, "-x")):
        k.block("plaster_v", world, (wx0, 0.0, ZB), (wx1, H1, zf), step=0.12, skip=("-z", "-y", "+y", inner))
    panel(k, "plaster_v", (x0, top, zf), (x1 - x0, 0, 0), (0, H1 - top, 0), step=0.12)
    panel(k, "tank_black", (x0, H1 - 0.03, zb), (x1 - x0, 0, 0), (0, 0, zf - zb), step=0.25)       # the hood's dark inside
    # the plinth under the glass, and the glass in its frame
    panel(k, "tank_plinth", (x0, 0.0, zf), (x1 - x0, 0, 0), (0, base, 0), step=0.10)
    k.b.quad(G, "tank_glass", [(x0, base, zf), (x1, base, zf), (x1, top, zf), (x0, top, zf)])
    t = 0.022
    for lo, hi in (((x0, base, zf - 0.004), (x1, base + t, zf + 0.012)), ((x0, top - t, zf - 0.004), (x1, top, zf + 0.012)),
                   ((x0, base, zf - 0.004), (x0 + t, top, zf + 0.012)), ((x1 - t, base, zf - 0.004), (x1, top, zf + 0.012))):
        k.block("tank_black", world, lo, hi, step=0.25, skip=("-z",))
    # inside: the glowing backdrop, black sides
    v, fc, uv = grid((x0, base, zb), (x1 - x0, 0, 0), (0, top - base, 0), 20, 8)
    k.b.mesh(G, "tank_back", v, fc, smooth=False, uvs=uv)
    panel(k, "tank_black", (x0 + 0.001, base, zf), (0, 0, zb - zf), (0, top - base, 0), step=0.15)
    panel(k, "tank_black", (x1 - 0.001, base, zb), (0, 0, zf - zb), (0, top - base, 0), step=0.15)
    rng = np.random.default_rng(41)
    height = substrate(k, rng)
    stones(k, rng, height)
    driftwood(k, height)
    plants(k, rng, height)
    fish(k, rng)
    # the tank's own light, in the hood, and its glow out into the room
    cx = (x0 + x1) / 2
    LAMPS.append(dict(name="tank_light", pos=(cx, top - 0.03, (zb + zf) / 2), size=(x1 - x0 - 0.2, 0.8), watts=260.0,
                      aim=(0.0, -1.0, 0.0), colour=TANK_LIGHT))
    LAMPS.append(dict(name="tank_glow", pos=(cx, 1.55, zf + 0.10), size=(x1 - x0 - 0.3, 2.1), watts=22.0,
                      aim=(0.0, 0.0, 1.0), colour=(0.55, 0.85, 0.95)))


def substrate(k, rng):
    """The tank's floor: dark soil banked up at the back, a sand path in front, and the
    cut edge of it all against the glass. Returns a function giving its height."""
    (x0, x1), zf, base = TANK["x"], TANK["front"], TANK["base"]
    zb = ZB + 0.01
    nx, nz = int((x1 - x0) / 0.05), int((zf - zb) / 0.05)
    lumps = _smooth_noise((nz + 1, nx + 1), 4, rng)
    rx, rz = ROCK

    def h(x, z, j=None, i=None):
        s = (z - zf) / (zb - zf)                                    # 0 at the glass, 1 at the back
        y = base + 0.07 + 0.17 * s ** 1.3
        y += 0.06 * math.exp(-((x - rx) ** 2 / 0.9 + (z - rz) ** 2 / 0.25))   # banked up round the rock
        if j is not None:
            y += 0.012 * lumps[j, i]
        return y

    verts, colors = [], []
    soil, sand = np.array([0.16, 0.12, 0.09]), np.array([0.74, 0.66, 0.52])
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = x0 + (x1 - x0) * i / nx, zf + (zb - zf) * j / nz
            verts.append((x, h(x, z, j, i), z))
            s = (z - zf) / (zb - zf)
            path = 1.0 - min(1.0, max(0.0, (s - 0.25 + 0.08 * lumps[j, i]) / 0.15))
            c = soil * (1 - path) + sand * path
            c = c * (0.9 + 0.2 * rng.random())
            colors.append(srgb_to_linear(tuple(np.clip(c, 0, 1))))
    faces = [(i * (nz + 1) + j, (i + 1) * (nz + 1) + j, (i + 1) * (nz + 1) + j + 1, i * (nz + 1) + j + 1)
             for i in range(nx) for j in range(nz)]
    k.b.mesh(G, "living_albedo", verts, faces, smooth=True, colors=colors)
    # its cut edge, seen through the glass: layers of sand over dark soil
    verts, colors, faces = [], [], []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        hy = h(x, zf, 0, i)
        for r in range(5):
            y = base + (hy - base) * r / 4
            verts.append((x, y, zf - 0.006))
            c = np.array([0.20, 0.15, 0.11]) if r < 3 else np.array([0.62, 0.55, 0.43])
            colors.append(srgb_to_linear(tuple(c * (0.85 + 0.25 * rng.random()))))
    for i in range(nx):
        for r in range(4):
            a, c = i * 5 + r, (i + 1) * 5 + r
            faces.append((a, c, c + 1, a + 1))
    k.b.mesh(G, "living_albedo", verts, faces, smooth=True, colors=colors)
    return lambda x, z: h(x, z)


def _icosphere(level=2):
    t = (1 + 5 ** 0.5) / 2
    verts = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
             (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    verts = [tuple(np.array(v) / np.linalg.norm(v)) for v in verts]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
             (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
             (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        cache, out = {}, []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m = (np.array(verts[a]) + np.array(verts[b])) / 2
                verts.append(tuple(m / np.linalg.norm(m)))
                cache[key] = len(verts) - 1
            return cache[key]
        for a, b_, c in faces:
            ab, bc, ca = mid(a, b_), mid(b_, c), mid(c, a)
            out += [(a, ab, ca), (b_, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = out
    return verts, faces


def _waves(rng, n=7, lo=1.5, hi=6.0):
    """A smooth random function on the sphere, roughly -1 to 1: random waves added together."""
    ks = []
    for _ in range(n):
        d = rng.normal(size=3)
        ks.append((d / np.linalg.norm(d), rng.uniform(lo, hi), rng.uniform(0, 2 * math.pi), rng.uniform(0.5, 1.0)))
    norm = math.sqrt(sum(a * a for *_, a in ks) / 2)

    def f(p):
        return sum(a * math.sin(fr * float(np.dot(d, p)) + ph) for d, fr, ph, a in ks) / norm
    return f


def rock(k, centre, size, seed, moss=0.0, level=3, sink=0.25, cushion=False):
    """A boulder: a lumpy, faceted sphere, flattened where it sits in the soil, grey
    stone darker in its hollows. Moss grows over its top in patches (moss: 0 none, 1
    most of the top): a fine, dark, mottled coat a little proud of the stone, thinning
    at its ragged edges so the stone shows through, and gathering in the hollows. A
    `cushion` is a small mound that is all moss."""
    rng = np.random.default_rng(seed)
    big, small, patch, speck, grain = (_waves(rng, 7, 1.0, 2.6), _waves(rng, 9, 4.0, 8.0), _waves(rng, 10, 3.0, 9.0),
                                       _waves(rng, 14, 18.0, 34.0), _waves(rng, 16, 45.0, 90.0))
    verts, faces = _icosphere(level)
    sx, sy, sz = size
    out, colors = [], []
    stone, hollow = np.array([0.40, 0.39, 0.36]), np.array([0.17, 0.165, 0.155])
    dark, mid, tip = np.array([0.045, 0.085, 0.030]), np.array([0.10, 0.17, 0.045]), np.array([0.20, 0.29, 0.07])
    for v in verts:
        p = np.array(v)
        lump = 0.20 * big(p) + 0.07 * small(p)
        r = 1.0 + lump
        g, fine = grain(p), speck(p)
        if cushion:
            cover = 1.0
        elif moss > 0:
            # how much moss: most on top, in patches, more in the hollows, ragged at the edge
            reach = p[1] + 0.45 * patch(p) - 0.9 * lump + 0.12 * fine + 0.06 * g - (0.55 - 0.75 * moss)
            cover = float(np.clip(reach * 3.0, 0.0, 1.0))
        else:
            cover = 0.0
        r += cover * (0.022 + 0.010 * g + 0.006 * fine)            # a thin coat, fuzzy on the surface
        q = p * r
        q[1] = max(q[1], -sink)                                   # flat where it sits in the soil
        out.append((centre[0] + q[0] * sx, centre[1] + q[1] * sy, centre[2] + q[2] * sz))
        rock_c = stone * (1 - np.clip(-lump * 2.2, 0, 0.65)) + hollow * np.clip(-lump * 2.2, 0, 0.65)
        rock_c = rock_c * (0.88 + 0.14 * (0.5 + 0.5 * fine))
        t = float(np.clip(0.5 + 0.45 * g + 0.25 * fine, 0, 1))      # fine mottling: dark depths, brighter tips
        moss_c = dark * (1 - t) + mid * t if t < 0.75 else mid + (tip - mid) * (t - 0.75) / 0.25
        # thin moss at the patches' edges lets the stone show through
        a = cover ** 0.7
        c = rock_c * (1 - a) + moss_c * a
        colors.append(srgb_to_linear(tuple(np.clip(c, 0, 1))))
    k.b.mesh(G, "living_albedo", out, faces, smooth=True, colors=colors)


def stones(k, rng, height):
    rx, rz = ROCK
    # the big one, mossy all over its top: about 1.3 m across and 0.8 m high
    rock(k, (rx, height(rx, rz) + 0.10, rz), (0.66, 0.52, 0.44), seed=7, moss=1.0, level=5)
    for x, z, s, moss, seed in ((rx - 0.95, -7.30, 0.32, 0.8, 11), (rx + 0.90, -6.97, 0.22, 0.5, 12),
                                (rx + 1.30, -7.40, 0.36, 0.9, 13), (5.35, -7.25, 0.28, 0.7, 14),
                                (9.45, -7.05, 0.30, 0.6, 15), (rx - 0.55, -6.86, 0.12, 0.0, 16),
                                (8.65, -6.82, 0.10, 0.0, 17), (5.95, -6.88, 0.09, 0.3, 18),
                                (rx + 0.45, -6.86, 0.08, 0.0, 19), (9.80, -6.85, 0.07, 0.0, 20)):
        rock(k, (x, height(x, z) + s * 0.17, z), (s, s * 0.78, s * 0.85), seed=seed, moss=moss, level=5 if s > 0.25 else 4)


def driftwood(k, height):
    """Two gnarled pieces of dark driftwood, each a short root crown low behind the
    rocks with branches that wander up and out, thinning as they go."""
    rng = np.random.default_rng(5)
    for bx, bz, lean in ((5.85, -7.38, 1.0), (8.35, -7.34, -1.0)):
        base = np.array((bx, height(bx, bz) - 0.04, bz))
        for n in range(5):
            # each branch: a random walk upward, leaning away from the rock
            d = np.array((lean * rng.uniform(0.15, 0.55), 1.0, rng.uniform(-0.15, 0.25)))
            d /= np.linalg.norm(d)
            length = rng.uniform(0.7, 1.7) * (1.0 if n else 1.15)
            pts, p = [tuple(base + rng.normal(0, 0.03, 3) * (1, 0, 1))], base.copy()
            steps = 14
            for _ in range(steps):
                d = d + rng.normal(0, 0.22, 3) * np.array((1.0, 0.35, 0.6))
                d[1] = max(d[1], 0.25)
                d /= np.linalg.norm(d)
                p = p + d * length / steps
                p[2] = min(max(p[2], -7.62), -6.80)
                pts.append(tuple(p))
            r0 = rng.uniform(0.028, 0.045) * (1.3 if n == 0 else 1.0)
            k.sweep("driftwood", pts, [r0, r0 * 0.7, r0 * 0.45, r0 * 0.2, 0.004], segments=9)
            # a twig off it, about halfway up
            if rng.random() < 0.7:
                mid = np.array(pts[steps // 2])
                tip = mid + np.array((lean * rng.uniform(-0.2, 0.35), rng.uniform(0.2, 0.4), rng.uniform(-0.05, 0.1)))
                k.sweep("driftwood", [tuple(mid), tuple((mid + tip) / 2 + rng.normal(0, 0.03, 3)), tuple(tip)],
                        [r0 * 0.4, r0 * 0.25, 0.003], segments=7)


def _ribbon(k, mat, base, h, w, lean, twist, turn=0.0, n=8):
    """One blade of grass (or a sword plant's leaf): a strip rising from `base`, `h` long,
    tapering from `w`, bending over by `lean` (a world vector), its width facing `turn`
    (radians about the vertical) and twisting by `twist` from foot to tip."""
    bx, by, bz = base
    verts, faces = [], []
    for i in range(n + 1):
        t = i / n
        c = np.array((bx, by + h * t, bz)) + np.asarray(lean) * t ** 2
        a = turn + twist * t
        half = w * (1 - 0.7 * t) / 2
        d = np.array((math.cos(a), 0.0, math.sin(a))) * half
        verts += [tuple(c - d), tuple(c + d)]
    for i in range(n):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    k.b.mesh(G, mat, verts, faces, smooth=True)


def plants(k, rng, height):
    """Ribbon grass along the back, reaching the surface and bending over along it;
    bushy red and olive stem plants either side of the rock; sword plants; and a
    carpet of moss cushions over the sand."""
    (x0, x1) = TANK["x"]
    surface = TANK["top"] - 0.12
    for cx in np.linspace(x0 + 0.15, x1 - 0.15, 22):
        edge = min(cx - x0, x1 - cx) / ((x1 - x0) / 2)
        for _ in range(int(rng.integers(5, 9))):
            x, z = cx + rng.normal(0, 0.07), -7.56 + rng.uniform(-0.05, 0.10)
            y = height(x, z)
            reach = surface - y
            tall = reach * rng.uniform(0.55, 1.0) * (1.0 - 0.35 * edge * rng.random())
            # blades that reach the surface lie over along it
            over = max(0.0, tall - reach * 0.85) * 2.5
            lean = (rng.normal(0, 0.12) + over * rng.choice((-1, 1)), 0.0, rng.uniform(0.04, 0.22))
            _ribbon(k, "aqua_grass", (x, y, z), tall, rng.uniform(0.016, 0.026), lean, rng.uniform(-2.0, 2.0),
                    rng.uniform(0, math.pi), n=10)
    # bushy stem plants: dense tufts of short leaves, reddish and olive
    for cx, cz, mat, n, hgt in ((5.15, -7.35, "aqua_red", 70, 0.65), (9.70, -7.40, "aqua_red", 60, 0.55),
                                (6.15, -7.45, "aqua_olive", 60, 0.75), (8.10, -7.50, "aqua_olive", 70, 0.85),
                                (9.25, -7.30, "aqua_olive", 45, 0.45)):
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = abs(rng.normal(0, 0.10))
            x, z = cx + r * math.cos(a), min(-6.85, cz + r * math.sin(a) * 0.6)
            y = height(x, z) + rng.uniform(0.0, hgt)
            L = rng.uniform(0.06, 0.12)
            out = np.array((math.cos(a), rng.uniform(0.3, 0.9), math.sin(a)))
            _ribbon(k, mat, (x, y, z), L * 0.4, L * 0.30, tuple(out * L), rng.uniform(-0.4, 0.4), turn=a + math.pi / 2, n=3)
        for _ in range(6):                                       # their stems
            x, z = cx + rng.normal(0, 0.06), cz + rng.normal(0, 0.04)
            y = height(x, z)
            k.tube(mat, (x, y, z), (x + rng.normal(0, 0.05), y + hgt, z + rng.normal(0, 0.03)), 0.004, segments=5, step=0.1)
    # sword plants: rosettes of broad leaves arching out
    for cx, cz, size in ((5.85, -7.02, 0.42), (8.45, -7.12, 0.46), (9.55, -6.95, 0.32), (6.30, -6.95, 0.28)):
        y = height(cx, cz)
        for i in range(13):
            a = 2 * math.pi * i / 13 + rng.uniform(-0.2, 0.2)
            L = size * rng.uniform(0.7, 1.1)
            out = np.array((math.cos(a), 0.0, math.sin(a)))
            _ribbon(k, "aqua_leaf", (cx, y, cz), L * 0.9, L * 0.22, tuple(out * L * 0.55), rng.uniform(-0.3, 0.3),
                    turn=a + math.pi / 2, n=6)
    # moss cushions over the sand in front
    for _ in range(40):
        x, z = rng.uniform(x0 + 0.15, x1 - 0.15), rng.uniform(-7.05, -6.72)
        if abs(x - ROCK[0]) < 0.75 and z < -6.95:
            continue
        s = rng.uniform(0.035, 0.075)
        rock(k, (x, height(x, z) + 0.004, z), (s, s * 0.45, s * 0.9), seed=int(rng.integers(1000, 9999)), level=2,
             sink=0.0, cushion=True)


def _fish_body(k, f, L, H, W, colour, n=10, seg=8):
    """A small fish along local +x (head at +x): a lens of a body and a fan of a tail,
    painted per vertex by colour(s, around), with s from the tail (0) to the head (1)."""
    verts, colors, faces = [], [], []
    for i in range(n + 1):
        s = i / n
        r = math.sin(math.pi * (0.06 + 0.94 * s) ** 0.85)
        for j in range(seg):
            a = 2 * math.pi * j / seg
            p = (L * (s - 0.5), H / 2 * r * math.sin(a), W / 2 * r * math.cos(a))
            verts.append(f(p))
            colors.append(srgb_to_linear(colour(s, math.sin(a))))
    for i in range(n):
        for j in range(seg):
            a, c = i * seg + j, i * seg + (j + 1) % seg
            faces.append((a, a + seg, c + seg, c))
    base = len(verts)
    for p in ((-L * 0.48, 0, 0), (-L * 0.80, H * 0.45, 0), (-L * 0.80, -H * 0.45, 0)):
        verts.append(f(p))
        colors.append(srgb_to_linear(colour(0.0, 0.0)))
    faces += [(base, base + 1, base + 2), (base, base + 2, base + 1)]
    k.b.mesh(G, "living_albedo", verts, faces, smooth=True, colors=colors)


def fish(k, rng):
    """A school of small tetras, blue above and red below, and three angelfish."""
    def tetra(s, up):
        if up > 0.05 and 0.2 < s < 0.92:
            return (0.10, 0.62, 0.95)
        if up <= 0.05 and s > 0.08:
            return (0.88, 0.14, 0.10)
        return (0.80, 0.82, 0.84)
    centre = np.array((8.55, 1.45, -7.05))
    for _ in range(26):
        p = centre + rng.normal(0, 1, 3) * (0.42, 0.16, 0.14)
        _fish_body(k, Frame(tuple(p), 180.0 + rng.normal(0, 14)), 0.055, 0.016, 0.008, tetra)

    def angel(s, up):
        bar = any(abs(s - c) < 0.05 for c in (0.30, 0.55, 0.80))
        return (0.12, 0.11, 0.10) if bar else (0.86, 0.85, 0.80)
    for x, y, z, heading in ((6.15, 1.70, -7.10, 15.0), (6.55, 1.95, -7.25, 190.0), (9.30, 1.15, -7.00, 160.0)):
        f = Frame((x, y, z), heading)
        _fish_body(k, f, 0.10, 0.075, 0.014, angel)
        for sgn in (1, -1):                        # the long dorsal and anal fins
            k.b.mesh(G, "living_albedo", f.many([(0.02, sgn * 0.03, 0.0), (-0.035, sgn * 0.03, 0.0), (-0.055, sgn * 0.11, 0.0)]),
                     [(0, 1, 2), (0, 2, 1)], colors=[srgb_to_linear((0.80, 0.80, 0.76))] * 3)


# ---- the rug, the sofa and the table -------------------------------------------------------
def rug(k):
    """A large flat-woven wool rug in stone grey, a little mottled, with a pale line set
    in from its edge. Painted per vertex on a fine grid."""
    (x0, x1), (z0, z1), t = RUG["x"], RUG["z"], RUG["t"]
    rng = np.random.default_rng(8)
    step = 0.05
    nx, nz = round((x1 - x0) / step), round((z1 - z0) / step)
    mottle = _smooth_noise((nx + 1, nz + 1), 6, rng)
    field, line = np.array([0.44, 0.42, 0.39]), np.array([0.80, 0.77, 0.70])
    verts, colors = [], []
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = x0 + (x1 - x0) * i / nx, z0 + (z1 - z0) * j / nz
            verts.append((x, t, z))
            d = min(x - x0, x1 - x, z - z0, z1 - z)
            c = line if 0.14 < d < 0.19 else field * (1 + 0.05 * mottle[i, j])
            colors.append(srgb_to_linear(tuple(np.clip(c, 0, 1))))
    faces = [(i * (nz + 1) + j, i * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j)
             for i in range(nx) for j in range(nz)]
    k.b.mesh(G, "living_albedo", verts, faces, smooth=False, colors=colors)
    edge = srgb_to_linear(tuple(field * 0.8))
    for a, c in (((x1, z0), (x0, z0)), ((x0, z0), (x0, z1)), ((x0, z1), (x1, z1)), ((x1, z1), (x1, z0))):
        k.b.mesh(G, "living_albedo", [(a[0], 0.0, a[1]), (c[0], 0.0, c[1]), (c[0], t, c[1]), (a[0], t, a[1])], [(0, 1, 2, 3)],
                 colors=[edge] * 4)


def sofa(k, f):
    """A low L-shaped sofa in oatmeal linen: a long run facing the TV with a chaise on
    its east end, on a dark recessed base. Built facing +z, its back along z = 0, from
    its west end at x = 0."""
    Lm, Lc, D, Dc = SOFA["main"], SOFA["chaise"], SOFA["D"], SOFA["Dc"]
    L = Lm + Lc
    fab = "living_sofa"
    seat, base_y, arm = 0.43, 0.075, 0.20
    k.block("frame", f, (0.06, 0.0, 0.06), (L - 0.06, base_y, D - 0.06), step=0.3, skip=("-y",))
    k.block("frame", f, (Lm + 0.06, 0.0, D - 0.07), (L - 0.06, base_y, Dc - 0.06), step=0.3, skip=("-y",))
    k.soft(fab, f, (L / 2, base_y + 0.10, D / 2), (L, 0.20, D), 0.03)                                 # the base
    k.soft(fab, f, (Lm + Lc / 2, base_y + 0.10, (D + Dc) / 2 - 0.01), (Lc, 0.20, Dc - D + 0.02), 0.03)
    k.soft(fab, f, (L / 2, base_y + 0.37, 0.10), (L, 0.54, 0.20), 0.06)                               # the back
    k.soft(fab, f, (arm / 2, base_y + 0.26, D / 2), (arm, 0.52, D), 0.07)                             # the west arm
    k.soft(fab, f, (L - arm / 2, base_y + 0.22, Dc / 2 + 0.06), (arm, 0.44, Dc - 0.12), 0.07)         # the chaise's arm
    # seat cushions: three along the run, one long one on the chaise
    n = 3
    cw = (Lm - arm) / n
    for i in range(n):
        cx = arm + cw * (i + 0.5)
        k.soft(fab, f, (cx, seat - 0.075, 0.20 + (D - 0.20) / 2 + 0.01), (cw - 0.012, 0.15, D - 0.19), 0.06)
        k.soft(fab, f, (cx, seat + 0.20, 0.32), (cw - 0.02, 0.42, 0.20), 0.09, tilt=-12, pivot=(cx, seat, 0.32))
    ccx = Lm + (Lc - arm) / 2
    k.soft(fab, f, (ccx, seat - 0.075, 0.20 + (Dc - 0.20) / 2 + 0.01), (Lc - arm - 0.012, 0.15, Dc - 0.19), 0.06)
    k.soft(fab, f, (ccx, seat + 0.20, 0.32), (Lc - arm - 0.02, 0.42, 0.20), 0.09, tilt=-12, pivot=(ccx, seat, 0.32))
    # pillows, and a charcoal throw folded over the foot of the chaise
    for mat, x, turn, s in (("pillow_teal", arm + 0.28, 14, 0.46), ("pillow_sand", arm + 0.62, 4, 0.42),
                            ("pillow_rust", Lm - 0.12, -10, 0.44), ("pillow_teal", Lm + 0.30, -16, 0.42)):
        k.soft(mat, f, (x, seat + 0.21, 0.50), (s, s - 0.02, 0.14), 0.07, tilt=-16, pivot=(x, seat, 0.50), turn=turn)
    front = 0.20 + (Dc - 0.20)
    k.soft("living_throw", f, (ccx - 0.02, seat + 0.03, front - 0.30), (Lc - arm - 0.06, 0.06, 0.40), 0.025, n=3, turn=4)


def coffee_table(k):
    """A low walnut table, a slab on a recessed plinth, with a bowl, two books and the
    TV's remote."""
    (x0, x1), (z0, z1), top = TABLE["x"], TABLE["z"], TABLE["top"]
    world = Frame((0.0, 0.0, 0.0))
    t, r = RUG["t"], 0.045
    k.grain("living_walnut", world, (x0, top - r, z0), (x1, top, z1), step=0.07)
    k.grain("living_walnut", world, (x0 + 0.16, t, z0 + 0.13), (x1 - 0.16, top - r, z1 - 0.13), step=0.08, skip=("+y", "-y"))
    k.lathe("ceramic_white", Frame((x0 + 0.32, top, (z0 + z1) / 2 + 0.05)),
            [(0.0, 0.0), (0.06, 0.0), (0.12, 0.03), (0.15, 0.075), (0.142, 0.077), (0.11, 0.035), (0.0, 0.012)], 40)
    f = Frame((x1 - 0.36, top, (z0 + z1) / 2 + 0.02), 84.0)
    book_flat(k, f, (0.0, 0.0), (0.30, 0.028, 0.23), "book_charcoal")
    book_flat(k, Frame(f((0.0, 0.028, 0.0)), 70.0), (0.0, 0.0), (0.24, 0.02, 0.18), "book_cream")
    k.soft("tv_black", Frame(((x0 + x1) / 2 + 0.10, top, z1 - 0.20), 12.0), (0.0, 0.009, 0.0), (0.045, 0.018, 0.16), 0.008, n=2)


# ---- the TV ---------------------------------------------------------------------------------
def console_frame():
    """The TV stand's frame: origin on the wall at the TV's middle, +z out into the
    room, +x to the right as you face it."""
    return Frame((TV_X, 0.0, ZN - 0.02), 180.0)


def console(k):
    """A long low walnut stand: four doors with hairline gaps over a black recessed
    plinth, a vase and two books on top."""
    f = console_frame()
    L, D, H = CONSOLE["L"], CONSOLE["D"], CONSOLE["H"]
    x0, x1 = -L / 2, L / 2
    plinth = 0.08
    k.block("tv_black", f, (x0 + 0.05, 0.0, 0.03), (x1 - 0.05, plinth, D - 0.06), step=0.3, skip=("-y", "-z"))
    k.grain("living_walnut", f, (x0, H - 0.03, 0.0), (x1, H, D), step=0.08, skip=("-z",))
    for x in (x0, x1 - 0.025):
        k.grain("living_walnut", f, (x, plinth, 0.0), (x + 0.025, H - 0.03, D), step=0.08, skip=("-z", "-y"), along="y")
    k.grain("living_walnut", f, (x0 + 0.025, plinth, 0.0), (x1 - 0.025, plinth + 0.02, D), step=0.1, skip=("-z", "-y"))
    n, gap = 4, 0.003
    w = (L - 0.05) / n
    for i in range(n):
        a = x0 + 0.025 + i * w
        k.grain("living_walnut", f, (a + gap / 2, plinth + 0.02 + gap, D - 0.02), (a + w - gap / 2, H - 0.03 - gap, D),
                step=0.07, skip=("-z",), along="y")
    k.block("tv_black", f, (x0 + 0.025, plinth + 0.02, D - 0.03), (x1 - 0.025, H - 0.03, D - 0.02), step=0.3, skip=("-z",))
    # on top: a tall stoneware vase at one end, two books at the other
    k.lathe("ceramic_white", Frame(f((x1 - 0.22, H, D / 2))),
            [(0.0, 0.0), (0.05, 0.0), (0.07, 0.04), (0.075, 0.12), (0.05, 0.24), (0.032, 0.30), (0.036, 0.32),
             (0.030, 0.32), (0.0, 0.31)], 36)
    g = Frame(f((x0 + 0.30, H, D / 2 + 0.02)), f.yaw + 3)
    book_flat(k, g, (0.0, 0.0), (0.28, 0.03, 0.21), "book_navy")
    book_flat(k, Frame(g((0.0, 0.03, 0.0)), f.yaw - 4), (0.0, 0.0), (0.24, 0.022, 0.17), "book_rust")


def tv(k):
    """An 83-inch OLED on its own pedestal on the stand: a 6 mm panel, a deeper box
    behind its lower half, the paused screen on the front."""
    f = console_frame()
    H = CONSOLE["H"]
    sw, sh = SCREEN
    zc = CONSOLE["D"] * 0.55
    y0 = H + 0.075
    # the pedestal: a flat foot and a short neck
    k.soft("tv_black", f, (0.0, H + 0.006, zc - 0.02), (0.46, 0.012, 0.24), 0.005, n=1)
    k.soft("tv_black", f, (0.0, H + 0.05, zc - 0.05), (0.16, 0.10, 0.03), 0.008, n=1)
    # the panel and the box behind it
    bz = zc
    k.soft("tv_black", f, (0.0, y0 + sh / 2, bz - 0.003), (sw + 0.012, sh + 0.012, 0.006), 0.002, n=1)
    k.soft("tv_black", f, (0.0, y0 + 0.30, bz - 0.03), (sw - 0.6, 0.48, 0.045), 0.01, n=2)
    v, fc, uv = grid((-sw / 2, y0, bz + 0.0006), (sw, 0, 0), (0, sh, 0), 16, 9)
    k.mesh("tv_screen", f, v, fc, smooth=False, uvs=uv)
    LAMPS.append(dict(name="tv_glow", pos=f((0.0, y0 + sh / 2, bz + 0.25)), size=(sw * 0.9, sh * 0.9), watts=5.0,
                      aim=tuple(np.subtract(f((0, 0, 1)), f((0, 0, 0)))), colour=(0.75, 0.85, 1.0)))


# ---- lamp, plant, bench --------------------------------------------------------------------
def floor_lamp(k):
    """A slim brass floor lamp with a linen drum shade at the sofa's west end."""
    x, z = LAMP
    f = Frame((x, RUG["t"] * 0, z))
    k.lathe("tv_black", f, [(0.0, 0.0), (0.16, 0.0), (0.16, 0.012), (0.14, 0.024), (0.02, 0.03), (0.0, 0.03)], 40)
    k.tube("living_brass", (x, 0.025, z), (x, 1.42, z), 0.0095, segments=10)
    y0, y1, r = 1.24, 1.56, 0.22
    k.lathe("living_shade", f, [(r, y0), (r, y1)], 48)
    k.lathe("living_shade", f, [(r - 0.004, y1), (r - 0.004, y0)], 48)
    k.disc("light_warm", f, (0.0, y0 + 0.06, 0.0), r - 0.03, 32, down=True)
    for a in range(3):
        ang = 2 * math.pi * a / 3
        k.tube("living_brass", (x, 1.42, z), (x + (r - 0.005) * math.cos(ang), y1 - 0.01, z + (r - 0.005) * math.sin(ang)),
               0.003, segments=6)
    LAMPS.append(dict(name="living_lamp_down", pos=(x, y0 + 0.04, z), size=(0.3, 0.3), watts=30.0, aim=(0.0, -1.0, 0.0)))
    LAMPS.append(dict(name="living_lamp_up", pos=(x, y1 - 0.04, z), size=(0.3, 0.3), watts=16.0, aim=(0.0, 1.0, 0.0)))
    LAMPS.append(dict(name="living_lamp_glow", kind="point", pos=(x, (y0 + y1) / 2, z), watts=6.0, radius=0.12))


def fig(k):
    """A fig (Poly Haven's potted_plant_01, CC0) in a pale stone pot, in the corner
    beside the TV."""
    from .props import load, place
    x, z = XE - 0.55, ZN - 0.55
    f = Frame((x, 0.0, z))
    h = 0.50
    k.lathe("ceramic_white", f, [(0.0, 0.0), (0.18, 0.0), (0.21, 0.05), (0.22, h), (0.205, h), (0.205, h - 0.04), (0.0, h - 0.04)], 40)
    plant = load("potted_plant_01", only={"potted_plant_01_leaves", "potted_plant_01_stem"},
                 thin={"potted_plant_01_leaves": 0.25})
    for name, piece in plant.items():
        mat = "living_fig_leaves" if name.endswith("leaves") else "living_fig_stems"
        place(k.b, G, mat, piece, (x, h - 0.04, z), yaw=0.4, scale=1.75, origin=(0.0, 0.5, 0.0))


def gallery_frame():
    """The moodboard's frame: origin on the east wall's lining at its middle, +z out
    into the room, +x to the right as you face it."""
    return Frame((XE - LINING, 0.0, GALLERY_Z), -90.0)


def bench(k):
    """A low walnut bench under the moodboard, with a vase and a stack of books."""
    f = gallery_frame()
    L, D, H = 1.90, 0.38, 0.40
    k.grain("living_walnut", f, (-L / 2, H - 0.04, 0.02), (L / 2, H, 0.02 + D), step=0.07)
    for x in (-L / 2 + 0.04, L / 2 - 0.08):
        k.grain("living_walnut", f, (x, 0.0, 0.06), (x + 0.04, H - 0.04, D - 0.02), step=0.07, along="y")
    k.lathe("ceramic_white", Frame(f((-L / 2 + 0.28, H, 0.02 + D / 2))),
            [(0.0, 0.0), (0.07, 0.0), (0.10, 0.06), (0.10, 0.14), (0.06, 0.22), (0.045, 0.24), (0.04, 0.26), (0.0, 0.25)], 36)
    g = Frame(f((L / 2 - 0.34, H, 0.02 + D / 2)), f.yaw + 6)
    book_flat(k, g, (0.0, 0.0), (0.30, 0.035, 0.24), "book_olive")
    book_flat(k, Frame(g((0.0, 0.035, 0.0)), f.yaw - 2), (0.0, 0.0), (0.26, 0.024, 0.20), "book_cream")
    book_flat(k, Frame(g((0.0, 0.059, 0.0)), f.yaw + 9), (0.0, 0.0), (0.22, 0.02, 0.16), "book_charcoal")


# ---- the moodboard --------------------------------------------------------------------------
def moodboard(k):
    """Five frames in mixed sizes, hung salon style about a line between two rows. Each
    has its own picture material (moodboard_1 to 5), so the site can give each a
    different picture. Mats are strips round the picture, not one sheet behind it
    (gotcha 26). Two ceiling spots wash the wall."""
    f = gallery_frame()
    aspects = picture_aspects()
    for i, (fr, aspect) in enumerate(zip(FRAMES, aspects)):
        listed = MATS[f"moodboard_{i + 1}"]["moodboard"]
        if abs(listed - aspect) > 0.005:
            raise ValueError(f"moodboard_{i + 1} lists its picture as {listed} wide per unit high, but its frame makes it "
                             f"{aspect:.3f}; update materials.py")
        (x0, x1), (y0, y1) = fr["x"], fr["y"]
        w, d = fr["fr"], 0.035
        wood = "frame" if fr["wood"] == "black" else "oak_light"
        for lo, hi in (((x0, y0, 0.004), (x0 + w, y1, d)), ((x1 - w, y0, 0.004), (x1, y1, d)),
                       ((x0 + w, y0, 0.004), (x1 - w, y0 + w, d)), ((x0 + w, y1 - w, 0.004), (x1 - w, y1, d))):
            k.block(wood, f, lo, hi, step=0.08, skip=("-z",))
        a0, a1, b0, b1 = x0 + w, x1 - w, y0 + w, y1 - w
        m = fr["mat"]
        p0, p1, q0, q1 = a0 + m, a1 - m, b0 + m, b1 - m
        z = d - 0.012
        if m:
            for sa, sb, ta, tb in ((a0, a1, b0, q0), (a0, a1, q1, b1), (a0, p0, q0, q1), (p1, a1, q0, q1)):
                v, fc, _ = grid((sa, ta, z), (sb - sa, 0, 0), (0, tb - ta, 0), max(1, round((sb - sa) / 0.05)),
                                max(1, round((tb - ta) / 0.05)))
                k.mesh("mat_white", f, v, fc, smooth=False)
            # the mat's bevelled inner edge, a hair in front of the picture
        v, fc, uv = grid((p0, q0, z - (0.003 if m else 0.0)), (p1 - p0, 0, 0), (0, q1 - q0, 0),
                         max(2, round((p1 - p0) / 0.05)), max(2, round((q1 - q0) / 0.05)))
        k.mesh(f"moodboard_{i + 1}", f, v, fc, smooth=False, uvs=uv)
    for dz in (-0.95, 0.95):
        spot = f((dz, H1 - 0.06, 1.55))
        aim = f((dz * 0.6, MOODBOARD_Y, 0.0))
        LAMPS.append(dict(name=f"moodboard_spot_{'l' if dz < 0 else 'r'}", kind="spot", pos=spot,
                          aim=tuple(np.subtract(aim, spot)), watts=55.0, cone=62.0))


# ---- pictures ---------------------------------------------------------------------------------
def paint_pictures():
    paint_tv()
    paint_tank_back()
    paint_moodboard_previews()


def paint_tv(w=1024, h=576):
    """A dark, paused streaming screen: a dimmed frame behind, darker to the left where
    the title sits, the title in plain type, and the paused progress bar. No logo, no
    artwork. Laid out from the bottom left, like the text masks."""
    from .labels import text_mask
    rng = np.random.default_rng(23)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    yy, xx = yy / h, xx / w                                              # yy: height from the bottom
    img = np.zeros((h, w, 3))
    # the dimmed picture behind: a few soft dark-green and dusky shapes, out of focus
    for cx, cy, r, c in ((0.70, 0.45, 0.30, (0.05, 0.09, 0.07)), (0.88, 0.70, 0.22, (0.08, 0.07, 0.05)),
                         (0.55, 0.75, 0.25, (0.04, 0.06, 0.07)), (0.80, 0.20, 0.25, (0.06, 0.08, 0.10))):
        d = ((xx - cx) * w / h) ** 2 + (yy - cy) ** 2
        img += np.array(c) * np.exp(-d / (2 * r * r))[..., None]
    img *= (1 + 0.05 * _smooth_noise((h, w), 40, rng))[..., None]
    img *= np.clip(0.25 + 0.95 * xx, 0, 1)[..., None]                   # darker to the left, behind the title
    img *= (1 - 0.6 * np.clip(1 - yy / 0.3, 0, 1))[..., None]           # and along the bottom, behind the bar
    grey, white = np.array([0.55, 0.55, 0.56]), np.array([0.93, 0.93, 0.93])
    lines = [("You're watching", 0.065, 0.765, 0.040, "LEFT", 1.0),
             ("Hunter × Hunter", 0.062, 0.630, 0.105, "LEFT", 1.0),
             ("Season 1  ·  Episode 1", 0.065, 0.555, 0.042, "LEFT", 1.0),
             ("Paused", 0.065, 0.470, 0.038, "LEFT", 1.0),
             ("9:46", 0.065, 0.085, 0.034, "LEFT", 1.0),
             ("13:54", 0.935, 0.085, 0.034, "RIGHT", 1.0)]
    mask = text_mask((w, h), lines)[..., None]
    ink = np.where(((yy > 0.60) & (yy < 0.76))[..., None], white, grey)   # the title in white, the rest grey
    img = img * (1 - mask) + ink * mask
    # the progress bar along the bottom, 41% of the way through, with its handle
    by = int(h * 0.155)
    bx0, bx1 = int(w * 0.065), int(w * 0.935)
    done = bx0 + int((bx1 - bx0) * 0.41)
    img[by - 2:by + 2, bx0:bx1] = np.array([0.30, 0.30, 0.31])
    img[by - 2:by + 2, bx0:done] = white
    img[np.hypot(xx * w - done, yy * h - by) < 8] = white
    # a play triangle above the bar, on the left
    tx, ty, ts = int(w * 0.065), int(h * 0.255), int(h * 0.045)
    for r in range(ts):
        half = int(ts / 2 * (1 - r / ts))
        img[ty - half:ty + half + 1, tx + r] = white
    save_png(picture_path("living_tv"), np.clip(img, 0, 1).astype(np.float32))


def paint_tank_back(w=512, h=256):
    """The tank's backdrop, lit from behind: deep blue-green at the bottom, paler
    toward the surface, brightest in the middle."""
    rng = np.random.default_rng(29)
    v = np.linspace(0, 1, h)[:, None]                   # bottom row first
    u = np.linspace(0, 1, w)[None, :]
    low, high = np.array([0.02, 0.09, 0.11]), np.array([0.16, 0.42, 0.46])
    t = np.clip(v, 0, 1) ** 1.4
    img = low * (1 - t[..., None]) + high * t[..., None]
    img = img * (0.75 + 0.25 * np.exp(-((u - 0.5) / 0.45) ** 2))[..., None]
    img *= (1 + 0.04 * _smooth_noise((h, w), 30, rng))[..., None]
    img = np.broadcast_to(img, (h, w, 3))
    save_png(picture_path("tank_back"), np.clip(img, 0, 1).astype(np.float32))


def preview_pick(images, aspects, seed=4):
    """The pictures Blender's renders put in the frames: the same matching the site does
    (each frame gets a picture close to its shape), with a fixed shuffle."""
    rest = list(images)
    random.Random(seed).shuffle(rest)
    out = []
    for a in aspects:
        if not rest:
            out.append(None)
            continue
        best = min(rest[:3], key=lambda im: abs(math.log((im["w"] / im["h"]) / a)))
        rest.remove(best)
        out.append(best)
    return out


def paint_moodboard_previews():
    """Crop the pictures Blender's renders show into each frame's shape. Without
    pictures the frames stay plain colour fields, in Blender and on the site."""
    from .moodboard import listed, process
    process()
    images = listed()
    aspects = picture_aspects()
    for i, (im, a) in enumerate(zip(preview_pick(images, aspects), aspects)):
        path = picture_path(f"moodboard_{i + 1}")
        if im is None:
            path.unlink(missing_ok=True)
            continue
        px = load_pixels(C.ASSETS / im["file"])[..., :3]
        h, w = px.shape[:2]
        if w / h > a:                                   # wider than the frame: trim the sides
            cw = int(round(h * a))
            px = px[:, (w - cw) // 2:(w - cw) // 2 + cw]
        else:                                           # taller: trim top and bottom
            ch = int(round(w / a))
            px = px[(h - ch) // 2:(h - ch) // 2 + ch]
        save_png(path, np.ascontiguousarray(px).astype(np.float32))
