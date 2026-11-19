"""The home gym (boxing), furnished: black mats under a hard white light, a heavy
bag, a speed bag, and the gear set out neatly against the wall.

Plan, looking down, seen from the driveway (the front glass at the top, so +x is
on the right):

        front glass, onto the reflecting pool                  (z = 7.85)
     +----------------------------------------------------+
     |                                      [bench]  (cam) |
   s |                                                     | e
   t |      [=========== black mats, 5 x 5 m ===========]   | a
   u |      [  (O) heavy bag                            ]   | s
   d |      [                                           ]   | t
   y |      [                                           ]   |
     |      [                                           ]   | g
   w | rope [                                           ]   | l
   a |  [bench: bag, wraps]          [board]  speed bag (o) | a
   l +-[glove rack][hook]------[door]--------------------+ s
   l          wall to the living room, timer over the door  (z = 0)  s

The gear wall, left of the door to the living room: an oak bench with the open
duffel (shin guards sticking up out of it), the hand wraps and a bottle; over it a
rack with three pairs of gloves, and the worn brown lace-up pair hung from a hook by
its laces. Right of the door, a small whiteboard with the round plan, then the speed
bag. The mat in the middle is left clear but for the heavy bag.

The site's view stands on the mat behind the heavy bag, looking at the gear wall,
the bag in the left foreground. The house's downlights are off; three bare linear LEDs hung under the ceiling give the
clean, hard light.

Everything is lit per vertex, the mats and the plaster linings over the walls on
fine grids, so the room stays clean even from a quick draft bake; it has no
lightmap of its own. The worn brown leather is painted per vertex (_wear).
"""
import math

import numpy as np

from . import config as C
from .house import H1, P
from .kit import Frame, Kit, cushion, grid, panel, rot

ROOM, G = "gym", "ground"

XW = 6.0 + P / 2                 # the wall to the study (6.075)
XE = C.HALF_W - C.WALL           # the east wall's inside face, glass from z 1 to 7 (11.7)
ZN = P / 2                       # the wall to the living room (0.075)
ZF = C.HALF_D - C.WALL           # the front glass's inside face (7.7)
LIVING_DOOR = (8.4, 9.6)

MATS = dict(x=6.45, z=0.55, n=(5, 5), tile=1.0, t=0.02, gap=0.006)
MAT_TOP = MATS["t"]
HEAVY_BAG = (7.35, 3.70)
SPEED_BAG = dict(x=11.18, board_y=2.08, out=0.42)
GEAR_BENCH = (7.18, 1.60)        # the oak bench on the gear wall: middle x, length
RACK = dict(y=1.63, x=(6.40, 6.56, 6.76, 6.92, 7.12, 7.28))     # the glove rack's pegs
HOOK = (7.66, 1.74)              # the hook the brown pair hangs from
BOARD = dict(x=(9.80, 10.70), y=(1.12, 1.72))
ROUND_PLAN = [                   # the whiteboard, top to bottom; the starred line is boxed in red
    ("ROUND PLAN", "title"),
    ("skip  -  3 x 3 min", ""),
    ("shadow  -  3 x 3 min", ""),
    ("12 x 3 min open sparring", "*"),
    ("bag  -  3 x 2 min", ""),
    ("1 min rest between rounds", "small"),
]
BARS_X = (7.15, 8.95, 10.75)

CEILING_LIGHT = 0.5
CEILING_COLOUR = (0.88, 0.93, 1.0)       # cool, hard white
BAR_COLOUR = (0.90, 0.95, 1.0)
LAMPS = []

# Review cameras. The first is also the room's view on the website: standing on the
# mat behind and to the right of the heavy bag, looking at the gear wall, the bag in
# the left foreground. (Its line of sight passes right of the bag, so the bag never
# hides the bench or the gloves.)
GYM_CAM = dict(pos=(8.75, 1.40, 6.30), target=(7.15, 1.00, 0.25), fov=34.0)
GEAR_CAM = dict(pos=(7.95, 1.30, 2.05), target=(7.05, 1.02, 0.10), fov=52.0)
BOARD_CAM = dict(pos=(10.15, 1.45, 1.70), target=(10.35, 1.40, 0.10), fov=50.0)
WIDE_CAM = dict(pos=(6.55, 1.70, 0.55), target=(10.20, 0.85, 5.60), fov=60.0)


def build_gym(b):
    LAMPS.clear()
    paint_timer()
    paint_board()
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    with b.room(ROOM):
        mats(k)
        heavy_bag(k)
        speed_bag(k)
        # the gear wall: the bench, with the bag, wraps and bottle on it; the rack and the hook over it
        bx, bl = GEAR_BENCH
        top = bench(k, Frame((bx, 0.0, ZN + 0.21)), L=bl)
        duffel(k, Frame((bx - 0.40, top, ZN + 0.215), 0.0))
        wraps(k, Frame((bx + 0.16, top, ZN + 0.24), 0.0))
        bottle(k, Frame((bx + 0.66, top, ZN + 0.12)))
        glove_rack(k)
        hung_pair(k)
        whiteboard(k)
        bench(k, Frame((10.50, 0.0, ZF - 0.36)))                    # by the front glass, where the site's view sits
        light_bars(k)
        timer(k)
        jump_rope(k)
        walls(k)


# ---- floor ---------------------------------------------------------------------------------
def mats(k):
    """Interlocking rubber mats, 1 m square and 2 cm thick, two shades of black laid
    as a faint chequer, with hairline seams. Lit per vertex on a 10 cm grid."""
    m = MATS
    world = Frame((0.0, 0.0, 0.0))
    nx, nz = m["n"]
    for i in range(nx):
        for j in range(nz):
            x0, z0 = m["x"] + i * m["tile"], m["z"] + j * m["tile"]
            mat = "gym_mat" if (i + j) % 2 == 0 else "gym_mat_b"
            g = m["gap"] / 2
            k.block(mat, world, (x0 + g, 0.0, z0 + g), (x0 + m["tile"] - g, m["t"], z0 + m["tile"] - g), step=0.1,
                    skip=("-y",))


# ---- the bags ---------------------------------------------------------------------------------
def chain(k, p0, p1, link=0.042, wire=0.0042, mat="aluminium"):
    """A chain of oval links between two world points, each link turned a quarter
    turn from the last."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    length = float(np.linalg.norm(d))
    pitch = link * 0.72
    n = max(1, int(length / pitch))
    up = (1.0, 0.0, 0.0) if abs(d[1]) > 0.9 * length else (0.0, 1.0, 0.0)
    from .kit import axes
    M = axes(d, up)
    for i in range(n):
        c = p0 + d * (i + 0.5) / n
        a = (i % 2) * math.pi / 2
        u = M @ np.array((math.cos(a), math.sin(a), 0.0))
        t = d / length
        half, w = link / 2 - wire, link * 0.30 - wire
        pts = []
        for s in np.linspace(0, 2 * math.pi, 17)[:-1]:
            pts.append(tuple(c + t * half * math.cos(s) + u * w * math.sin(s)))
        pts.append(pts[0])
        k.sweep(mat, pts, wire, segments=6, caps=False)


def heavy_bag(k):
    """A 1.2 m heavy bag in black leather with two red bands, on four short chains to a
    swivel and a single chain up to a plate in the ceiling."""
    x, z = HEAVY_BAG
    f = Frame((x, 0.0, z))
    y0, y1, r = 0.48, 1.68, 0.178
    prof = [(0.0, y0), (0.12, y0), (0.16, y0 + 0.008), (0.175, y0 + 0.03), (r, y0 + 0.07)]
    prof += [(r, y) for y in np.arange(y0 + 0.12, y1 - 0.06, 0.06)]
    prof += [(r, y1 - 0.06), (0.172, y1 - 0.022), (0.155, y1 - 0.006), (0.10, y1), (0.0, y1 + 0.004)]
    k.lathe("leather_black", f, prof, 40)
    for yb in (y0 + 0.10, y1 - 0.15):
        k.lathe("bag_band", f, [(r + 0.002, yb), (r + 0.003, yb + 0.002), (r + 0.003, yb + 0.048), (r + 0.002, yb + 0.05)], 40)
    swivel = np.array(f((0.0, 2.16, 0.0)))
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        ring = np.array(f((0.115 * math.cos(a), y1 + 0.01, 0.115 * math.sin(a))))
        k.sweep("aluminium", [tuple(ring + np.array((0.0, 0.018 * math.sin(s), 0.0)) + 0.018 * math.cos(s) *
                                    np.array((math.cos(a), 0.0, math.sin(a)))) for s in np.linspace(0, 2 * math.pi, 13)],
                0.003, segments=6, caps=False)                                 # the D-ring on the bag's top
        chain(k, ring + (0, 0.02, 0), swivel - (0, 0.02, 0), link=0.032, wire=0.003)
    k.lathe("steel_black", Frame(tuple(swivel - (0, 0.025, 0))), [(0.0, 0.0), (0.02, 0.0), (0.024, 0.02), (0.016, 0.05), (0.0, 0.05)], 16)
    chain(k, swivel + (0, 0.025, 0), np.array(f((0.0, H1 - 0.06, 0.0))))
    k.lathe("steel_black", Frame(f((0.0, H1 - 0.06, 0.0))), [(0.0, 0.0), (0.012, 0.0), (0.012, 0.035), (0.0, 0.035)], 12)
    k.lathe("steel_black", Frame(f((0.0, H1 - 0.025, 0.0))), [(0.0, 0.0), (0.09, 0.0), (0.09, 0.025), (0.0, 0.025)], 24)


def speed_bag(k):
    """A speed bag platform on the living room wall: a black steel bracket holding a round
    oak rebound board, with a tan leather bag hanging from the swivel under it."""
    s = SPEED_BAG
    f = Frame((s["x"], 0.0, ZN))                        # +z out of the wall
    by, out = s["board_y"], s["out"]
    k.soft("steel_black", f, (0.0, by + 0.10, 0.022), (0.56, 0.30, 0.016), 0.004, n=1)          # wall plate
    for dx in (-0.20, 0.20):
        k.soft("steel_black", f, (dx, by + 0.065, (out + 0.02) / 2 + 0.02), (0.035, 0.05, out + 0.02), 0.005, n=1)
        k.tube("steel_black", f((dx, by + 0.04, 0.03)), f((dx * 0.5, by + 0.04, out - 0.18)), 0.008, segments=8)
    c = Frame(f((0.0, by, out)))
    k.lathe("oak_light", c, [(0.0, 0.0), (0.29, 0.0), (0.305, 0.008), (0.31, 0.022), (0.305, 0.036), (0.29, 0.045), (0.0, 0.045)], 48)
    k.lathe("steel_black", Frame(c((0, 0.045, 0))), [(0.0, 0.0), (0.33, 0.0), (0.33, 0.012), (0.0, 0.012)], 48)   # the steel ring on top
    k.lathe("steel_black", Frame(c((0, -0.03, 0))), [(0.0, 0.0), (0.008, 0.0), (0.014, 0.012), (0.03, 0.022), (0.03, 0.03), (0.0, 0.03)], 16)
    # the bag: a teardrop hanging from its loop
    top = by - 0.03
    prof = [(0.0, -0.27), (0.03, -0.268), (0.058, -0.258), (0.077, -0.238), (0.087, -0.21), (0.088, -0.18), (0.08, -0.14),
            (0.06, -0.09), (0.036, -0.05), (0.02, -0.025), (0.014, -0.008), (0.0, 0.0)]
    k.lathe("speedbag", Frame(c((0, top - by, 0))), prof, 32)


# ---- the gear ----------------------------------------------------------------------------------
def _place(base, R, pts):
    base = np.asarray(base, float)
    return [tuple(base + R @ np.asarray(p, float)) for p in pts]


def ring(k, mat, centre, axis, r0, r1, segments=24):
    """A flat ring (an annulus) facing along `axis`."""
    from .kit import axes
    M = axes(axis, (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0))
    c = np.asarray(centre, float)
    verts, faces = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        for r in (r0, r1):
            verts.append(tuple(c + M @ np.array((r * math.cos(a), r * math.sin(a), 0.0))))
    for i in range(segments):
        a, b = 2 * i, 2 * ((i + 1) % segments)
        faces.append((a, a + 1, b + 1, b))
    k.b.mesh(k.g, mat, verts, faces, smooth=False)


def _sphere(c, r, n=10):
    verts, faces = [], []
    for i in range(n + 1):
        th = math.pi * i / n
        for j in range(2 * n):
            ph = math.pi * j / n
            verts.append((c[0] + r * math.sin(th) * math.cos(ph), c[1] + r * math.cos(th), c[2] + r * math.sin(th) * math.sin(ph)))
    for i in range(n):
        for j in range(2 * n):
            a, b = i * 2 * n + j, i * 2 * n + (j + 1) % (2 * n)
            faces.append((a, b, b + 2 * n, a + 2 * n))
    return verts, faces


def _loft(rings, flip=False):
    """Faces joining rings of equal size (each a closed loop of points)."""
    m = len(rings[0])
    verts = [p for r in rings for p in r]
    faces = []
    for i in range(len(rings) - 1):
        for j in range(m):
            a, b = i * m + j, i * m + (j + 1) % m
            faces.append((a, a + m, b + m, b) if not flip else (a, b, b + m, a + m))
    return verts, faces


# Boxing gloves. Each is built in its own frame: the wrist at the origin, the fist
# toward +z, the back of the hand toward +y, the thumb on the `side` of x.
GLOVES = {
    # the main pair: lace-up sparring gloves in dark brown leather, worn at the knuckles
    "brown": dict(leather="glove_brown", rim="glove_brown", strap=None, laces=True, worn=True),
    "black": dict(leather="glove_black", rim="glove_white", strap="glove_black", laces=False, worn=False),
    "red":   dict(leather="glove_red", rim="glove_white", strap="glove_white", laces=False, worn=False),
}
CUFF = dict(z=(0.015, -0.165), a=(0.057, 0.061), b=(0.051, 0.054), cy=-0.004)


def _cuff_at(z, extra=0.0):
    t = (z - CUFF["z"][0]) / (CUFF["z"][1] - CUFF["z"][0])
    a = CUFF["a"][0] + (CUFF["a"][1] - CUFF["a"][0]) * t + extra
    b = CUFF["b"][0] + (CUFF["b"][1] - CUFF["b"][0]) * t + extra
    return a, b


def _ellipse(z, extra=0.0, n=28):
    a, b = _cuff_at(z, extra)
    return [(a * math.cos(2 * math.pi * j / n), CUFF["cy"] + b * math.sin(2 * math.pi * j / n), z) for j in range(n)]


def _wear(p):
    """Worn brown leather: rubbed paler over the knuckles and the back of the hand,
    uneven all over, dark down the lacing slit. Returns a linear colour."""
    x, y, z = p
    n1 = 0.5 + 0.25 * math.sin(61 * x + 7.0) * math.sin(47 * y + 1.3) + 0.25 * math.sin(83 * z + 2.1) * math.sin(29 * x - 3 * y)
    n2 = 0.5 + 0.5 * math.sin(140 * x + 90 * z + 4.0) * math.sin(120 * y - 3.0)
    knuckles = math.exp(-((z - 0.20) / 0.035) ** 2) * (1.0 if y > -0.01 else 0.3)
    top = math.exp(-((y - 0.07) / 0.03) ** 2) * (0.6 if z > 0.05 else 0.0)
    wear = min(1.0, 0.75 * knuckles + 0.35 * top + 0.25 * n1 * (z > 0.0))
    base, rubbed = np.array((0.27, 0.15, 0.08)), np.array((0.46, 0.32, 0.21))
    c = base + (rubbed - base) * wear
    c = c * (0.90 + 0.18 * n2)
    if z < -0.01 and y < -0.035 and abs(x) < 0.016:            # the lacing slit, in shadow
        c = c * 0.45
    return tuple(float(v) for v in np.clip(c, 0, 1) ** 2.2)


def glove(k, base, R, side, kind="brown"):
    """A boxing glove: a padded fist, wider and domed over the knuckles, the thumb lying
    along its side and tied in at the tip, and a long cuff with a rolled edge. The lace-up
    kind has eyelets and crossed laces down the palm side of the cuff; the others a strap.
    Returns the two top eyelets (world points), where hanging laces start."""
    from .kit import sweep_geom
    st = GLOVES[kind]
    leather = st["leather"]

    def put(mat, verts, faces, smooth=True):
        colors = [_wear(v) for v in verts] if (st["worn"] and mat == leather) else None
        k.b.mesh(k.g, mat, _place(base, R, verts), faces, smooth=smooth, colors=colors)

    # the fist
    L = 0.21
    verts, faces = cushion((0.128, 0.112, L), 0.054, n=3, div=6)
    shaped = []
    for x, y, z in verts:
        t = (z + L / 2) / L
        x *= 0.80 + 0.26 * min(1.0, t * 1.4)
        if y > 0:
            y = y * (0.86 + 0.24 * t) + 0.010 * math.exp(-((t - 0.62) / 0.22) ** 2)
        else:
            y = y * (0.80 + 0.30 * t)
        z = z + L / 2 + 0.008
        if t > 0.82 and y > 0:
            z += 0.012 * min(1.0, (t - 0.82) / 0.18) * min(1.0, y / 0.05)          # the knuckles roll forward
        shaped.append((x, y, z))
    put(leather, shaped, faces)
    # the thumb, lying along the side, its tip tied in near the knuckles
    s = side
    path = [(s * 0.044, -0.024, 0.028), (s * 0.063, -0.014, 0.078), (s * 0.066, -0.002, 0.128), (s * 0.056, 0.006, 0.166)]
    v, fc = sweep_geom(path, [0.023, 0.027, 0.025, 0.018], 14, caps=False)
    put(leather, v, fc)
    v, fc = _sphere(path[-1], 0.018, 7)
    put(leather, v, fc)
    v, fc = sweep_geom([(s * 0.052, 0.010, 0.170), (s * 0.044, 0.016, 0.190)], 0.009, 10, caps=True)
    put(leather, v, fc)
    # the cuff, a little oval and flaring toward its rolled edge
    zs = np.linspace(CUFF["z"][0], CUFF["z"][1], 10)
    v, fc = _loft([_ellipse(z) for z in zs])
    put(leather, v, fc)
    z_end = CUFF["z"][1]
    a, b = _cuff_at(z_end)
    rim = [(a * math.cos(u), CUFF["cy"] + b * math.sin(u), z_end) for u in np.linspace(0, 2 * math.pi, 33)]
    v, fc = sweep_geom(rim, 0.0065, 10, caps=False)
    put(st["rim"], v, fc)
    v, fc = _loft([_ellipse(z_end - 0.002, -0.011), _ellipse(z_end + 0.07, -0.011)], flip=True)    # the dark inside
    put("glove_inside", v, fc, smooth=False)
    v, fc = _loft([_ellipse(z_end - 0.001, -0.011), _ellipse(z_end - 0.001, -0.001)], flip=True)
    put("glove_inside", v, fc, smooth=False)
    tops = []
    if st["strap"]:
        z0, z1 = -0.035, -0.105
        v, fc = _loft([_ellipse(z, 0.0045) for z in np.linspace(z0, z1, 4)])
        put(st["strap"], v, fc)
        for z, flip in ((z0, False), (z1, True)):
            v, fc = _loft([_ellipse(z, 0.0), _ellipse(z, 0.0047)], flip=flip)
            put(st["strap"], v, fc, smooth=False)
    if st["laces"]:
        # eyelets in two rows either side of the slit on the palm side, laces crossing between
        rows = np.linspace(-0.030, -0.150, 6)
        holes = {}
        for i, z in enumerate(rows):
            a, b = _cuff_at(z)
            for sx in (-1, 1):
                cx = sx * 0.0135
                y = CUFF["cy"] - b * math.sqrt(max(0.0, 1 - (cx / a) ** 2)) - 0.0015
                holes[(i, sx)] = (cx, y, z)
                ring(k, "steel_brushed", _place(base, R, [(cx, y, z)])[0], R @ np.array((0.0, -1.0, 0.0)), 0.0016, 0.0034, 10)
        for i in range(len(rows) - 1):
            for sx in (-1, 1):
                p0, p1 = np.array(holes[(i, sx)]), np.array(holes[(i + 1, -sx)])
                mid = (p0 + p1) / 2 + (0.0, -0.0025, 0.0)
                v, fc = sweep_geom([tuple(p0), tuple(mid), tuple(p1)], 0.0021, 6, caps=False)
                put("lace_tan", v, fc)
        tops = _place(base, R, [holes[(len(rows) - 1, -1)], holes[(len(rows) - 1, 1)]])
    return tops


def shin_guard(k, base, R, length=0.34):
    """A shin and instep guard in its own frame (y up the shin from the ankle, the front
    toward +z): a black padded shin plate with a raised white stripe and a rounded top, piping
    round its edge, two straps closing it round the back of the leg, and a padded foot
    pad hinged at the ankle."""
    th = np.linspace(-1.25, 1.25, 15)
    fr = np.linspace(0.0, 1.0, 13)

    def point(t, f, off):
        e = (t / 1.25) ** 2
        y0, y1 = 0.025 * e, length * (1 - 0.12 * e)
        y = y0 + f * (y1 - y0)
        r = 0.060 + 0.008 * math.sin(math.pi * y / length) + off + (0.010 * math.cos(t) ** 6 if off >= 0 else 0.0)
        return (math.sin(t) * r, y, math.cos(t) * r - 0.045)

    n = len(fr)
    faces = [(i * n + j, (i + 1) * n + j, (i + 1) * n + j + 1, i * n + j + 1) for i in range(len(th) - 1) for j in range(n - 1)]
    outer = [point(t, f, 0.0) for t in th for f in fr]
    inner = [point(t, f, -0.022) for t in th for f in fr]
    # black, with a white padded stripe down the front of the shin
    stripe = [fc for fc in faces if abs(th[fc[0] // n] + th[fc[1] // n]) / 2 < 0.36]
    rest = [fc for fc in faces if abs(th[fc[0] // n] + th[fc[1] // n]) / 2 >= 0.36]
    k.b.mesh(k.g, "shin_white", _place(base, R, outer), stripe)
    k.b.mesh(k.g, "shin_black", _place(base, R, outer), rest)
    k.b.mesh(k.g, "shin_pad", _place(base, R, inner), [fc[::-1] for fc in faces])
    edges = [[i * n for i in range(len(th))], [i * n + n - 1 for i in range(len(th))], list(range(n)), [(len(th) - 1) * n + j for j in range(n)]]
    pts, fc = [], []
    for e in edges:
        for a, c in zip(e[:-1], e[1:]):
            m = len(pts)
            pts += [outer[a], outer[c], inner[c], inner[a]]
            fc += [(m, m + 1, m + 2, m + 3), (m, m + 3, m + 2, m + 1)]
    k.b.mesh(k.g, "shin_pad", _place(base, R, pts), fc, smooth=False)
    # two straps round the back of the leg
    for y0, y1 in ((0.07, 0.11), (0.23, 0.27)):
        tb = np.linspace(1.18, 2 * math.pi - 1.18, 17)
        band = []
        for t in tb:
            for y in (y0, y1):
                r = 0.060 + 0.008 * math.sin(math.pi * y / length) - 0.020
                band.append((math.sin(t) * r, y, math.cos(t) * r - 0.045))
        bf = [(2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(len(tb) - 1)]
        k.b.mesh(k.g, "shin_pad", _place(base, R, band), bf + [f[::-1] for f in bf])
    # the foot pad, hinged at the ankle and angled down over the instep
    Rf = R @ rot(x=22.0)
    foot0 = np.array(base) + R @ np.array((0.0, -0.006, 0.020))
    verts, faces = cushion((0.092, 0.030, 0.125), 0.013, n=2, div=5)
    pad = [(x * (1.0 - 0.15 * (z + 0.0625) / 0.125), y - 0.012 * ((z / 0.0625) ** 2) + 0.004 * (y > 0), z + 0.0625) for x, y, z in verts]
    k.b.mesh(k.g, "shin_black", _place(foot0, Rf, pad), faces)
    hinge, hf = cushion((0.07, 0.022, 0.03), 0.006, n=1, div=1)
    k.b.mesh(k.g, "shin_pad", _place(foot0, R, hinge), hf)


def duffel(k, f):
    """A black holdall standing open on the bench, its zip pulled back and the mouth rolled
    open, two shin guards pushed in knee first with their foot pads sticking up out of it.
    Long side along local x."""
    R = rot(y=f.yaw)
    base = np.array(f((0, 0, 0)))
    L, H, D = 0.64, 0.29, 0.33
    verts, faces = cushion((L, H, D), 0.11, n=3, div=8)
    shaped = []
    for x, y, z in verts:
        y += H / 2
        # sag a little over the length, and dip at the open mouth on top
        y -= 0.02 * (1 - (2 * x / L) ** 2) * (y > H * 0.6)
        if y > H * 0.75 and abs(x) < L * 0.40 and abs(z) < D * 0.30:
            y -= 0.06 * (1 - (abs(z) / (D * 0.30)) ** 2) * (1 - (abs(x) / (L * 0.40)) ** 4)
        shaped.append((x, max(0.0, y), z))
    k.b.mesh(k.g, "duffel_black", _place(base, R, shaped), faces)
    v, fc, _ = grid((-L * 0.36, H - 0.075, D * 0.18), (L * 0.72, 0, 0), (0, 0, -D * 0.36), 8, 4)
    k.b.mesh(k.g, "duffel_inside", _place(base, R, v), fc, smooth=False)
    for zs in (-1, 1):
        edge = [(x, H - 0.035 - 0.01 * (2 * x / L) ** 2, zs * (D * 0.22 + 0.01 * (1 - (2 * x / L) ** 2))) for x in np.linspace(-L * 0.38, L * 0.38, 12)]
        k.sweep("duffel_black", _place(base, R, edge), 0.022, segments=12)
        k.sweep("duffel_zip", _place(base, R, [(x, y + 0.02, z - zs * 0.012) for x, y, z in edge]), 0.004, segments=6)
    r = 0.11

    def side(y):
        d = abs(y - H / 2) - (H / 2 - r)
        return D / 2 if d <= 0 else D / 2 - r + math.sqrt(max(r * r - d * d, 0.0))

    loop = [(-0.125, 0.235), (-0.12, 0.205), (-0.112, 0.17), (-0.10, 0.135), (-0.08, 0.112), (-0.045, 0.102), (0.0, 0.100),
            (0.045, 0.102), (0.08, 0.112), (0.10, 0.135), (0.112, 0.17), (0.12, 0.205), (0.125, 0.235)]
    for zs in (-1, 1):
        k.sweep("duffel_trim", _place(base, R, [(x, y, zs * (side(y) + 0.009)) for x, y in loop]), 0.008, segments=8)
        k.sweep("duffel_black", _place(base, R, [(x, 0.101, zs * (side(0.101) + 0.012)) for x in np.linspace(-0.06, 0.06, 6)]),
                0.015, segments=12)
        for x in (-0.125, 0.125):
            k.soft("duffel_trim", Frame(tuple(base)), tuple(R @ np.array((x, 0.235, zs * (side(0.235) + 0.003)))), (0.035, 0.03, 0.03), 0.006, n=1)
    # the shin guards, knee end down in the bag, fronts toward the room, foot pads up
    for dx, lean, turn, lift in ((-0.10, 16.0, -14.0, 0.56), (0.09, -22.0, 16.0, 0.52)):
        Rg = R @ rot(y=turn) @ rot(z=180.0 + lean)
        shin_guard(k, tuple(np.array(base) + R @ np.array((dx, lift, -0.01))), Rg)


def wraps(k, f):
    """Two black hand wraps on the bench, rolled tight, their ends toward the room showing
    the turns of the roll; the second partly unrolled, its tail lying along the bench
    with the velcro tab and the thumb loop at the end."""
    R = rot(y=f.yaw)
    base = np.array(f((0, 0, 0)))
    w = 0.050
    for x, rr in ((0.0, 0.034), (0.074, 0.028)):
        k.sweep("wrap_black", _place(base, R, [(x, rr, -w / 2), (x, rr, w / 2)]), rr, segments=28, caps=False)
        for zs in (-1, 1):
            radii = list(np.linspace(0.006, rr, 7))
            centre = _place(base, R, [(x, rr, zs * w / 2)])[0]
            for i, (r0, r1) in enumerate(zip(radii[:-1], radii[1:])):
                ring(k, "wrap_black" if i % 2 else "wrap_layer", centre, R @ np.array((0, 0, zs)), r0, r1 - 0.0004, 28)
            ring(k, "glove_inside", centre, R @ np.array((0, 0, zs)), 0.0, 0.006, 16)
    # the tail of the second, off the bottom of its roll and along the bench
    x0 = 0.074
    path = [(x0 + 0.33 * t, 0.0012, 0.03 * math.sin(2.2 * t) * t) for t in np.linspace(0, 1, 16)]
    verts, faces = [], []
    for i, p in enumerate(path):
        d = np.array(path[min(i + 1, len(path) - 1)]) - np.array(path[max(i - 1, 0)])
        d /= np.linalg.norm(d)
        side = np.array((d[2], 0.0, -d[0])) * w / 2
        verts += [tuple(np.array(p) - side), tuple(np.array(p) + side)]
    for i in range(len(path) - 1):
        a = 2 * i
        faces.append((a, a + 2, a + 3, a + 1))
    k.b.mesh(k.g, "wrap_black", _place(base, R, verts), faces, smooth=False)
    end = np.array(path[-1])
    tab = [end + (-0.065, 0.0016, -w / 2 + 0.004), end + (-0.002, 0.0016, -w / 2 + 0.004), end + (-0.002, 0.0016, w / 2 - 0.004),
           end + (-0.065, 0.0016, w / 2 - 0.004)]
    k.b.mesh(k.g, "wrap_velcro", _place(base, R, [tuple(p) for p in tab]), [(0, 3, 2, 1)], smooth=False)
    loop = [tuple(end + np.array((0.004 + 0.035 * (1 - math.cos(u)) / 2, 0.003, 0.016 * math.sin(u)))) for u in np.linspace(0, 2 * math.pi, 17)]
    k.sweep("wrap_black", _place(base, R, loop), 0.0035, segments=6, caps=False)


def bottle(k, f):
    """A brushed steel water bottle with a black cap."""
    k.lathe("steel_brushed", f, [(0.0, 0.0), (0.03, 0.0), (0.036, 0.008), (0.036, 0.20), (0.03, 0.225), (0.022, 0.235), (0.022, 0.24)], 28)
    k.lathe("steel_black", f, [(0.0, 0.238), (0.024, 0.238), (0.025, 0.262), (0.02, 0.27), (0.0, 0.27)], 24)
    k.sweep("steel_black", [f((0.0, 0.27 + 0.016 * math.sin(a), 0.016 * math.cos(a))) for a in np.linspace(0, math.pi, 9)], 0.004, segments=6)


def glove_rack(k):
    """A black steel rail on the wall over the bench with a peg for each glove: three pairs
    hung by their cuffs, black, red and black."""
    y = RACK["y"]
    xs = RACK["x"]
    k.block("steel_black", Frame((0.0, 0.0, 0.0)), (xs[0] - 0.10, y - 0.022, ZN + 0.012), (xs[-1] + 0.10, y + 0.022, ZN + 0.034), step=0.3)
    kinds = ["black", "black", "red", "red", "black", "black"]
    for i, (x, kind) in enumerate(zip(xs, kinds)):
        k.tube("steel_black", (x, y, ZN + 0.03), (x, y + 0.02, ZN + 0.15), 0.008, segments=10)
        side = 1 if i % 2 == 0 else -1                             # thumbs in toward the other of the pair
        glove(k, (x, y - 0.115, ZN + 0.088), rot(x=82.0) @ rot(z=side * 4.0), side, kind)


def hung_pair(k):
    """The brown lace-up pair, hung from a hook by their laces, palms half toward the room
    so the lacing shows."""
    hx, hy = HOOK
    hook = np.array((hx, hy, ZN + 0.075))
    k.soft("steel_black", Frame((hx, hy, ZN + 0.012)), (0.0, 0.0, 0.006), (0.05, 0.08, 0.012), 0.004, n=1)
    k.sweep("steel_black", [(hx, hy, ZN + 0.02), (hx, hy, ZN + 0.06), (hx, hy + 0.01, ZN + 0.078), (hx, hy + 0.035, ZN + 0.08)], 0.005, segments=8)
    for dx, yaw, side in ((-0.10, 218.0, 1), (0.10, 142.0, -1)):
        tops = glove(k, (hx + dx, hy - 0.47, ZN + 0.10), rot(y=yaw) @ rot(x=90.0), side, "brown")
        for t in tops:
            t = np.array(t)
            mid = (t + hook) / 2 + (0.0, -0.02, 0.012)
            k.sweep("lace_tan", [tuple(t), tuple(mid), tuple(hook + (0.0, -0.004, 0.004))], 0.0022, segments=6)
    v, fc = _sphere(tuple(hook + (0.0, -0.006, 0.004)), 0.011, 6)
    k.b.mesh(k.g, "lace_tan", v, fc)


def whiteboard(k):
    """A small whiteboard beside the living room door with the round plan written up in
    marker, in an aluminium frame with a tray and a marker."""
    (x0, x1), (y0, y1) = BOARD["x"], BOARD["y"]
    z = ZN + 0.032
    f = Frame((0.0, 0.0, 0.0))
    k.block("aluminium", f, (x0, y0, ZN + 0.012), (x1, y1, z - 0.004), step=0.3)
    v, fc, uv = grid((x0, y0, z), (x1 - x0, 0, 0), (0, y1 - y0, 0), 18, 12)
    k.mesh("gym_board", f, v, fc, smooth=False, uvs=uv)
    e = 0.018
    for lo, hi in (((x0 - e, y0 - e, z - 0.006), (x1 + e, y0, z + 0.008)), ((x0 - e, y1, z - 0.006), (x1 + e, y1 + e, z + 0.008)),
                   ((x0 - e, y0, z - 0.006), (x0, y1, z + 0.008)), ((x1, y0, z - 0.006), (x1 + e, y1, z + 0.008))):
        k.block("aluminium", f, lo, hi, step=0.3)
    k.block("aluminium", f, (x0 + 0.10, y0 - 0.03, z - 0.004), (x1 - 0.10, y0 - 0.018, z + 0.05), step=0.3)        # the tray
    k.tube("glove_white", (x0 + 0.25, y0 - 0.010, z + 0.03), (x0 + 0.38, y0 - 0.010, z + 0.03), 0.008, segments=10)
    k.tube("glove_red", (x0 + 0.38, y0 - 0.010, z + 0.03), (x0 + 0.40, y0 - 0.010, z + 0.03), 0.0085, segments=10)


# ---- the room ----------------------------------------------------------------------------------
def bench(k, f, L=1.60):
    """A low oak bench on black steel legs, built along local x. Returns its top's height."""
    D, h = 0.38, 0.45
    k.block("oak_light", f, (-L / 2, h - 0.05, -D / 2), (L / 2, h, D / 2), step=0.08)
    for x in (-L / 2 + 0.12, L / 2 - 0.12):
        for z in (-D / 2 + 0.05, D / 2 - 0.05):
            k.tube("steel_black", f((x, 0.0, z)), f((x, h - 0.05, z)), 0.014, segments=10)
        k.tube("steel_black", f((x, 0.10, -D / 2 + 0.05)), f((x, 0.10, D / 2 - 0.05)), 0.01, segments=8)
    return h


def light_bars(k):
    """Three bare linear LED fittings hung 18 cm under the ceiling, running the length of
    the mats: black steel with an opal strip underneath."""
    z0, z1 = 1.05, 6.55
    y = H1 - 0.18
    for x in BARS_X:
        f = Frame((x, 0.0, 0.0))
        k.block("steel_black", f, (-0.035, y, z0), (0.035, y + 0.05, z1), step=0.3)
        k.quad("gym_led", f, [(-0.028, y - 0.0005, z0 + 0.01), (0.028, y - 0.0005, z0 + 0.01),
                              (0.028, y - 0.0005, z1 - 0.01), (-0.028, y - 0.0005, z1 - 0.01)])
        for z in (z0 + 0.4, z1 - 0.4):
            k.tube("steel_black", f((0.0, y + 0.05, z)), f((0.0, H1, z)), 0.0015, segments=6)
            k.lathe("steel_black", Frame(f((0.0, H1 - 0.012, z))), [(0.0, 0.0), (0.03, 0.0), (0.03, 0.012), (0.0, 0.012)], 16)
        LAMPS.append(dict(name=f"gym_bar_{x:.2f}", pos=f((0.0, y - 0.01, (z0 + z1) / 2)), size=(0.06, z1 - z0 - 0.05),
                          watts=160.0, aim=(0.0, -1.0, 0.0), colour=BAR_COLOUR))


def timer(k):
    """A round timer over the door to the living room: a black box, its red digits
    reading 3:00."""
    f = Frame(((LIVING_DOOR[0] + LIVING_DOOR[1]) / 2, 0.0, ZN))
    y = 2.62
    k.soft("steel_black", f, (0.0, y, 0.03), (0.46, 0.17, 0.06), 0.008, n=1)
    k.quad("gym_timer", f, [(-0.20, y - 0.065, 0.0605), (0.20, y - 0.065, 0.0605), (0.20, y + 0.065, 0.0605), (-0.20, y + 0.065, 0.0605)],
           uv=[(0, 0), (1, 0), (1, 1), (0, 1)])


def jump_rope(k):
    """A jump rope hung on a hook on the study wall: two black handles side by side and
    the rope's loop hanging below."""
    f = Frame((XW, 0.0, 1.45), 90.0)                    # +z out of the wall, +x toward the back of the room
    hy = 1.78
    k.tube("steel_black", f((0.0, hy, 0.0)), f((0.0, hy, 0.06)), 0.005, segments=8)
    k.tube("steel_black", f((0.0, hy, 0.06)), f((0.0, hy + 0.03, 0.065)), 0.005, segments=8)
    for dx in (-0.025, 0.025):
        k.tube("steel_black", f((dx, hy - 0.02, 0.045)), f((dx, hy - 0.20, 0.03)), 0.013, segments=12)
    rope = [(-0.025 * math.cos(s) + 0.02 * math.sin(s), hy - 0.20 - 0.62 * math.sin(s / 2) ** 1.4, 0.03 + 0.03 * math.sin(s / 2))
            for s in np.linspace(0, 2 * math.pi, 40)]
    k.sweep("rope", [f(p) for p in rope], 0.0035, segments=6)


def walls(k):
    """Plaster linings laid just over the house's walls, lit per vertex on a grid, so the
    hard light falls cleanly across them even from a quick draft bake."""
    from .house import DOOR
    e, m = 0.012, "plaster_v"
    study_door, glass = (3.4, 4.6), (1.0, 7.0)
    # the study wall (facing +x), round its door
    for z0, z1, y0 in ((ZN, study_door[0], 0.0), (study_door[1], ZF, 0.0), (study_door[0], study_door[1], DOOR)):
        panel(k, m, (XW + e, y0, z1), (0, 0, z0 - z1), (0, H1 - y0, 0))
    # the living room wall (facing +z), round its door
    for x0, x1, y0 in ((XW, LIVING_DOOR[0], 0.0), (LIVING_DOOR[1], XE, 0.0), (LIVING_DOOR[0], LIVING_DOOR[1], DOOR)):
        panel(k, m, (x0, y0, ZN + e), (x1 - x0, 0, 0), (0, H1 - y0, 0))
    # the east wall (facing -x), either side of its glass
    for z0, z1 in ((ZN, glass[0]), (glass[1], ZF)):
        panel(k, m, (XE - e, 0.0, z0), (0, 0, z1 - z0), (0, H1, 0))


# ---- pictures --------------------------------------------------------------------------------
def paint_timer(w=384, h=124):
    """The timer's face: red digits on black, in plain type."""
    from .labels import text_mask
    from .textures import picture_path, save_png
    mask = text_mask((w, h), [("3:00", 0.5, 0.20, 0.72, "CENTER", 1.08)])
    img = np.ones((h, w, 3)) * 0.02
    red = np.array([1.0, 0.16, 0.10])
    img = img * (1 - mask[..., None]) + red * mask[..., None]
    save_png(picture_path("gym_timer"), np.clip(img, 0, 1).astype(np.float32))


def paint_board(w=512, h=340):
    """The whiteboard: the round plan in marker (Kalam), the title underlined and the
    sparring line boxed in red, with faint ghosts of earlier plans."""
    import random
    from .labels import text_mask
    from .study import _smooth_noise, _strokes, _wobbly
    from .textures import picture_path, save_png
    rng = np.random.default_rng(23)
    rnd = random.Random(23)
    img = np.ones((h, w, 3)) * np.array([0.93, 0.94, 0.94])
    img -= (np.clip(_smooth_noise((h, w), 16, rng), 0, 1) * 0.045)[..., None]
    ink, red = np.array([0.10, 0.12, 0.20]), np.array([0.70, 0.10, 0.08])
    black_lines, red_lines, boxed = [], [], []
    y = 0.84
    for text, style in ROUND_PLAN:
        size = 0.115 if style == "title" else (0.072 if style == "small" else 0.088)
        line = (text, 0.08, y, size, "LEFT", 1.0)
        if style == "*":
            red_lines.append(line)
            boxed.append(y)
        else:
            black_lines.append(line)
        y -= 0.165 if style == "title" else 0.135
    black = text_mask((w, h), black_lines, font="Kalam-Bold.ttf")
    reds = text_mask((w, h), red_lines, font="Kalam-Bold.ttf")
    under = _strokes((h, w), [_wobbly([(0.075 * w, 0.80 * h), (0.47 * w, 0.805 * h)], rnd, 1.5, 6)], 3.6)
    loops = []
    for yy in boxed:                                   # a loose red box round the sparring line
        cy = (yy + 0.03) * h
        loops.append(_wobbly([(0.06 * w, cy - 22), (0.92 * w, cy - 24), (0.93 * w, cy + 26), (0.055 * w, cy + 25), (0.06 * w, cy - 22)], rnd, 2.0, 5))
    box = _strokes((h, w), loops, 3.2)
    streak = 1.0 - 0.18 * np.clip(_smooth_noise((h, w), 3, rng), 0, 1)
    for mask, colour in ((black, ink), (under, ink), (reds, red), (box, red)):
        m = (np.clip(mask, 0, 1) * streak)[..., None]
        img = img * (1 - m) + colour * m
    save_png(picture_path("gym_board"), np.clip(img, 0, 1).astype(np.float32))
