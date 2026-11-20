"""The trophy room (wins in coding, boxing and esports), furnished: a display wall of
spotlit glass cases, a championship belt and medals, the cup, an empty frame waiting for
the team photo, and a chess table by the glass onto the terrace.

Plan, looking down, seen from the driveway (the library wall at the top, so +x is on
the right):

                     library door                                       (z = 0)
     +------------------[    ]--------------------------------------+
   g |                                                        (fig)  |
   a |                                               [ case: wins ]  |  e
   m |                                                                |  a
   e door         [~~~~~~~~~~ rug ~~~~~~~~~~]  photo over [ console ] |  s
   s |                       [bench]           the cup                |  t
     |                                                                |
     |                     (chair)[chess](chair)   [ case: boxing ]  |
     +-----[==================== glass onto the terrace =============]+
                                                                    (z = -8)

The east wall is the display: two tall glass cases on walnut bases, each lit from
inside and by a spot from the ceiling track. The boxing case holds the belt, wrapped
round a dark velvet form, a second belt hung flat on the velvet above it, medals hung
either side and two more on stands; the
other holds the coding and esports wins (medals on ribbons, a silver cup, a crystal
award). Between them, the team photo's frame (empty for now, a plain linen board) over
a walnut console with the cup on it.

Everything is lit per vertex, the walls and the ceiling lined over the house's own, so
the room stays clean from a quick draft bake; it has no lightmap.
"""
import math

import numpy as np

from . import config as C
from .house import P
from .kit import Frame, Kit, cushion, grid, panel, rot, sweep_geom, wall
from .materials import srgb_to_linear

ROOM, G = "trophy", "upper"
F2, RY = C.F2, C.ROOF_Y
H = RY - F2                       # floor to ceiling (3.0)

# The room's inside faces (heights below are above the trophy room's floor, F2).
XW = 4.0 + P / 2                  # the wall to the games room (4.075)
XE = C.HALF_W - C.WALL            # the east wall, the display wall (11.7)
ZB = -C.HALF_D + C.WALL           # the back wall, glass onto the terrace from x 5 to 11 (-7.7)
ZN = -P / 2                       # the wall to the library (-0.075)
GAMES_DOOR = (-4.6, -3.4)
LIBRARY_DOOR = (7.0, 8.2)
GLASS = (5.0, 11.0)
LINING = 0.012                    # the walls' linings stand off the house's (gotcha 30)

CASE = dict(w=1.20, d=0.48, base=0.86, top=2.36, cap=0.12)
CASE_Z = {"boxing": -6.15, "wins": -1.95}       # the two cases' middles along the east wall
WALL_Z = -4.05                                  # the photo, the console and the cup between them
PHOTO = dict(w=1.40, h=0.98, y=1.95, fr=0.035, mat=0.12)
CONSOLE = dict(L=1.80, D=0.42, H=0.74)
CHESS = dict(x=9.20, z=-6.55, top=0.74, size=0.72)
SQUARE = 0.058                    # the chess set's own square size (as in the dining room)
BENCH = dict(x=8.55, z=WALL_Z, L=1.60, D=0.46, H=0.46)
RUG = dict(x=(6.55, 10.35), z=(-5.55, -2.25), t=0.012)
FIG = (11.12, -0.68)
TRACK_X = 10.30                   # the ceiling track of spots, along the display wall

# The chess table's position, in standard notation (FEN): the start, set up and waiting.
FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

CEILING_LIGHT = 0.30
CASE_LIGHT = (1.0, 0.88, 0.74)
LAMPS = []

# Review cameras. The first is also the room's view on the website: just inside the games
# room's door, looking across at the display wall, the terrace through the glass on the left.
TROPHY_CAM = dict(pos=(4.60, F2 + 1.55, -3.00), target=(11.70, F2 + 1.20, -4.60), fov=55.0)
CASES_CAM = dict(pos=(9.45, F2 + 1.50, -5.30), target=(11.70, F2 + 1.45, -5.95), fov=50.0)
BELT_CAM = dict(pos=(XE - LINING - 1.30, F2 + 1.36, CASE_Z["boxing"] - 0.10),
                target=(XE - LINING - 0.25, F2 + 1.33, CASE_Z["boxing"]), fov=40.0)
CHESS_CAM = dict(pos=(7.95, F2 + 1.45, -5.15), target=(9.35, F2 + 0.75, -6.65), fov=50.0)


def build_trophy(b):
    LAMPS.clear()
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    with b.room(ROOM):
        walls(k)
        ceiling(Kit(b, "roof", None))
        rug(k)
        for name, zc in CASE_Z.items():
            vitrine(k, name, zc)
        belt(k, case_frame(CASE_Z["boxing"]))
        boxing_medals(k, case_frame(CASE_Z["boxing"]))
        hung_belt(k, case_frame(CASE_Z["boxing"]))
        wins(k, case_frame(CASE_Z["wins"]))
        console(k)
        cup(k)
        photo_frame(k)
        bench(k)
        chess_table(k)
        fig(k)
        track(k)


# ---- walls and ceiling ------------------------------------------------------------------------
def walls(k):
    """Deep slate linings over the house's walls, lit per vertex on a grid. Behind the cases
    and the console they start at the piece's top: points buried behind a closed box bake
    dark and muddy the wall round it (gotcha 26)."""
    from .house import DOOR
    e, m = LINING, "trophy_wall"
    top = CASE["top"] + CASE["cap"]
    zb, zw = CASE_Z["boxing"], CASE_Z["wins"]
    w2, c2 = CASE["w"] / 2, CONSOLE["L"] / 2
    # the display wall (facing -x): one grid, with holes behind the cases, the console and the photo
    py0, py1 = PHOTO["y"] - PHOTO["h"] / 2, PHOTO["y"] + PHOTO["h"] / 2
    holes = [(zb - w2 - ZB, zb + w2 - ZB, 0.0, top), (zw - w2 - ZB, zw + w2 - ZB, 0.0, top),
             (WALL_Z - c2 - ZB, WALL_Z + c2 - ZB, 0.0, CONSOLE["H"]),
             (WALL_Z - PHOTO["w"] / 2 - ZB, WALL_Z + PHOTO["w"] / 2 - ZB, py0, py1)]
    wall(k, m, (XE - e, F2, ZB), (0, 0, ZN - ZB), (0, H, 0), step=0.12, holes=holes)
    # the library wall (facing -z), round its door
    d0, d1 = LIBRARY_DOOR
    wall(k, m, (XE, F2, ZN - e), (XW - XE, 0, 0), (0, H, 0), step=0.15, holes=[(XE - d1, XE - d0, 0.0, DOOR)])
    # the games room wall (facing +x), round its door
    g0, g1 = GAMES_DOOR
    wall(k, m, (XW + e, F2, ZN), (0, 0, ZB - ZN), (0, H, 0), step=0.15, holes=[(ZN - g1, ZN - g0, 0.0, DOOR)])
    # the back wall's two short stretches either side of the glass (facing +z)
    for x0, x1 in ((XW, GLASS[0]), (GLASS[1], XE)):
        panel(k, m, (x0, F2, ZB + e), (x1 - x0, 0, 0), (0, H, 0), step=0.15)


def ceiling(k):
    """The house's oak ceiling again, laid just under it and lit per vertex (as in the
    library), with its own downlight fittings. It lifts off with the roof."""
    from .house import downlight_spots
    y = RY - 0.014
    k.grain("trophy_ceiling", Frame((0.0, 0.0, 0.0)), (XW, y - 0.012, ZB), (XE, y, ZN), step=0.3,
            skip=("+y", "+x", "-x", "+z", "-z"), along="z")
    s = 0.07
    for px, pz in downlight_spots(ROOM):
        k.b.quad("roof", "light_warm", [(px - s, y - 0.014, pz - s), (px + s, y - 0.014, pz - s),
                                        (px + s, y - 0.014, pz + s), (px - s, y - 0.014, pz + s)])


def rug(k):
    """A flat-woven rug in deep navy, a little mottled, with a fine cream line inside its
    edge. Painted per vertex on a fine grid."""
    from .study import _smooth_noise
    (x0, x1), (z0, z1), t = RUG["x"], RUG["z"], RUG["t"]
    rng = np.random.default_rng(31)
    step = 0.05
    nx, nz = round((x1 - x0) / step), round((z1 - z0) / step)
    mottle = _smooth_noise((nx + 1, nz + 1), 6, rng)
    field, line = np.array([0.13, 0.15, 0.24]), np.array([0.78, 0.74, 0.64])
    verts, colors = [], []
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = x0 + (x1 - x0) * i / nx, z0 + (z1 - z0) * j / nz
            verts.append((x, F2 + t, z))
            d = min(x - x0, x1 - x, z - z0, z1 - z)
            c = line if 0.12 < d < 0.16 else field * (1 + 0.06 * mottle[i, j])
            colors.append(srgb_to_linear(tuple(np.clip(c, 0, 1))))
    faces = [(i * (nz + 1) + j, i * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j)
             for i in range(nx) for j in range(nz)]
    k.b.mesh(G, "trophy_albedo", verts, faces, smooth=False, colors=colors)
    edge = srgb_to_linear(tuple(field * 0.8))
    for a, c in (((x1, z0), (x0, z0)), ((x0, z0), (x0, z1)), ((x0, z1), (x1, z1)), ((x1, z1), (x1, z0))):
        k.b.mesh(G, "trophy_albedo", [(a[0], F2, a[1]), (c[0], F2, c[1]), (c[0], F2 + t, c[1]), (a[0], F2 + t, a[1])],
                 [(0, 1, 2, 3)], colors=[edge] * 4)


# ---- small shared shapes ----------------------------------------------------------------------
def soft_fine(k, mat, f, centre, size, r, div=8, tilt=0.0, pivot=(0, 0, 0), shape=None):
    """A rounded box like Kit.soft, but with its flat sides divided (kit.cushion), so
    light falling across it stays smooth; `shape` can bend its points first."""
    verts, faces = cushion(size, r, n=3, div=div)
    if shape:
        verts = [shape(*v) for v in verts]
    T, c, pv = rot(x=tilt), np.asarray(centre, float), np.asarray(pivot, float)
    k.b.mesh(G, mat, [f(pv + T @ (c + np.asarray(v, float) - pv)) for v in verts], faces)


def facing(verts, faces, want):
    """Turn round any face whose normal points away from want(centre of the face)."""
    out = []
    for q in faces:
        p = [np.asarray(verts[i], float) for i in q]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if len(p) > 3 and np.linalg.norm(n) < 1e-12:
            n = np.cross(p[2] - p[0], p[3] - p[0])
        c = sum(p) / len(p)
        out.append(q if np.dot(n, want(c)) >= 0 else q[::-1])
    return out


def sphere(k, mat, p, r, segments=14):
    """A small ball at world point p (a pin's head, a stud)."""
    prof = [(r * math.sin(math.pi * s), -r * math.cos(math.pi * s)) for s in np.linspace(0, 1, 8)]
    k.lathe(mat, Frame(p), [(0.0, -r)] + prof[1:-1] + [(0.0, r)], segments)


def strip(k, path, side, width, stripes, flip=False):
    """A flat ribbon along a path of world points, `width` across along the world
    vector `side`, in stripes of colour (sRGB) from one edge to the other. Each stripe
    has its own points so its edges stay crisp. Painted per vertex."""
    side = np.asarray(side, float)
    side /= np.linalg.norm(side)
    n = len(stripes)
    verts, faces, colors = [], [], []
    for si, colour in enumerate(stripes):
        a, c = -width / 2 + width * si / n, -width / 2 + width * (si + 1) / n
        base = len(verts)
        for p in path:
            p = np.asarray(p, float)
            verts += [tuple(p + side * a), tuple(p + side * c)]
        lin = srgb_to_linear(colour)
        colors += [lin] * (2 * len(path))
        for i in range(len(path) - 1):
            q = (base + 2 * i, base + 2 * i + 1, base + 2 * i + 3, base + 2 * i + 2)
            faces.append(q[::-1] if flip else q)
    k.b.mesh(G, "trophy_albedo", verts, faces, smooth=False, colors=colors)


# ---- the cases ----------------------------------------------------------------------------------
def case_frame(zc):
    """A case's frame: origin on the display wall's lining at its middle, +z out into
    the room, +x to the right as you face it."""
    return Frame((XE - LINING, F2, zc), -90.0)


def vitrine(k, name, zc):
    """A tall glass case on a walnut base: a black recessed plinth, the base with two
    doors, a glass box in slim bronze posts, a dark velvet back and floor, a walnut cap
    with an LED strip along its front underside, and a lamp inside."""
    f = case_frame(zc)
    W, D, b0, b1, cap = CASE["w"], CASE["d"], CASE["base"], CASE["top"], CASE["cap"]
    x0, x1 = -W / 2, W / 2
    k.block("trophy_black", f, (x0 + 0.04, 0.0, 0.0), (x1 - 0.04, 0.07, D - 0.04), step=0.3, skip=("-y", "-z", "+y"))
    k.grain("trophy_walnut", f, (x0, 0.07, 0.0), (x1, b0, D), step=0.08, skip=("-z", "-y", "+y"), along="x")
    k.block("trophy_black", f, (-0.0015, 0.10, D), (0.0015, b0 - 0.03, D + 0.0008), step=0.3, skip=("-z",))   # the doors' gap
    for sx in (-1, 1):                                                                                    # brass pulls
        k.soft("trophy_brass", f, (sx * 0.035, b0 - 0.16, D + 0.006), (0.010, 0.12, 0.012), 0.004, n=1)
    # inside: a velvet floor and back
    k.block("case_velvet", f, (x0, b0, 0.0), (x1, b0 + 0.012, D), step=0.05, skip=("-y", "-z"))
    k.block("case_velvet", f, (x0 + 0.018, b0 + 0.012, 0.0), (x1 - 0.018, b1, 0.02), step=0.05, skip=("-z", "-y", "+y"))
    # the cap, its underside the case's ceiling, with an LED strip
    k.grain("trophy_walnut", f, (x0, b1, 0.0), (x1, b1 + cap, D + 0.005), step=0.08, skip=("-z",), along="x")
    y = b1 - 0.001
    k.quad("case_led", f, [(x0 + 0.05, y, D - 0.07), (x1 - 0.05, y, D - 0.07), (x1 - 0.05, y, D - 0.05), (x0 + 0.05, y, D - 0.05)])
    # the posts at its corners and rails along the front, and the glass
    p, y0 = 0.018, b0 + 0.012
    for px in (x0, x1 - p):
        for pz in (0.0, D - p):
            k.block("case_bronze", f, (px, y0, pz), (px + p, b1, pz + p), step=0.15, skip=("-y", "+y"))
    k.block("case_bronze", f, (x0 + p, y0, D - p), (x1 - p, y0 + 0.02, D), step=0.2, skip=("-y",))
    k.block("case_bronze", f, (x0 + p, b1 - 0.02, D - p), (x1 - p, b1, D), step=0.2, skip=("+y",))
    g = "case_glass"
    zg = D - p / 2
    k.quad(g, f, [(x0 + p, y0 + 0.02, zg), (x1 - p, y0 + 0.02, zg), (x1 - p, b1 - 0.02, zg), (x0 + p, b1 - 0.02, zg)])
    xa, xb = x0 + p / 2, x1 - p / 2
    k.quad(g, f, [(xa, y0, p), (xa, y0, D - p), (xa, b1, D - p), (xa, b1, p)])
    k.quad(g, f, [(xb, y0, D - p), (xb, y0, p), (xb, b1, p), (xb, b1, D - p)])
    LAMPS.append(dict(name=f"case_{name}", pos=f((0.0, b1 - 0.03, D * 0.55)), size=(W - 0.15, D - 0.15), watts=30.0,
                      aim=(0.0, -1.0, 0.0), colour=CASE_LIGHT))
    # and a small spot in the top front corner, aimed back down at what's inside, as museum cases have
    pos = f((0.0, b1 - 0.04, D - 0.06))
    aim = f((0.0, b0 + 0.50, 0.15))
    LAMPS.append(dict(name=f"case_{name}_spot", kind="spot", pos=pos, aim=tuple(np.subtract(aim, pos)), watts=10.0,
                      cone=75.0, colour=CASE_LIGHT))


# ---- the belt ----------------------------------------------------------------------------------
BELT = dict(a=0.245, b=0.145, z=0.22, h=0.19, ends=2.6)       # its ellipse's half-width and depth, middle, height


def _ellipse(theta, off=0.0):
    """A point round the belt (local x, z), `off` metres outward. theta 0 is its front."""
    a, b, zc = BELT["a"] + off, BELT["b"] + off, BELT["z"]
    return a * np.sin(theta), zc + b * np.cos(theta)


def _arc_to_theta():
    """Arc length round the belt's ellipse (from its front) to the angle there."""
    th = np.linspace(-math.pi, math.pi, 4001)
    x, z = _ellipse(th)
    seg = np.hypot(np.diff(x), np.diff(z))
    s = np.concatenate([[0.0], np.cumsum(seg)])
    s -= np.interp(0.0, th, s)
    return lambda arc: np.interp(arc, s, th)


def belt(k, f):
    """A championship belt, an original design, wrapped round a dark velvet form on the
    case's floor: a red leather strap edged in gold piping, a big octagonal centre plate
    (a gold rim, a dark blue enamel disc, a raised gold star, studs round its edge) and
    four smaller plates round the sides."""
    deck = CASE["base"] + 0.012
    yb = deck + 0.46                                     # the strap's middle height
    hh = BELT["h"] / 2
    # the form it's wrapped round, and a little brass plaque in front of it
    # (slim enough that its rounded corners stay a centimetre inside the strap all the way round:
    # where they poked through, the strap was buried and baked black)
    soft_fine(k, "case_velvet_dark", f, (0.0, deck + 0.33, BELT["z"]), (0.38, 0.66, 0.19), 0.07, div=6)
    k.soft("trophy_black", f, (0.0, deck + 0.025, 0.40), (0.16, 0.05, 0.05), 0.006, n=1, tilt=-30, pivot=(0.0, deck, 0.40))
    k.soft("trophy_brass", f, (0.0, deck + 0.030, 0.418), (0.13, 0.035, 0.004), 0.001, n=1, tilt=-30, pivot=(0.0, deck, 0.40))

    def P(theta, y, off):
        x, z = _ellipse(theta, off)
        return f((float(x), y, float(z)))

    # the strap: outside, inside and its edges, from one end round the front to the other
    axis = np.asarray(f((0.0, 0.0, BELT["z"])))

    def radial(c):
        return np.array((c[0] - axis[0], 0.0, c[2] - axis[2]))
    ends = BELT["ends"]
    ths = np.linspace(-ends, ends, 73)
    ys = np.linspace(yb - hh, yb + hh, 6)
    for off, sign in ((0.0, 1.0), (-0.006, -1.0)):
        verts = [P(t, y, off) for t in ths for y in ys]
        faces = []
        for i in range(len(ths) - 1):
            for j in range(len(ys) - 1):
                a, c = i * len(ys) + j, (i + 1) * len(ys) + j
                faces.append((a, a + 1, c + 1, c))
        k.b.mesh(G, "belt_leather", verts, facing(verts, faces, lambda c, s=sign: radial(c) * s), smooth=True)
    for y, up in ((yb + hh, 1.0), (yb - hh, -1.0)):
        verts = [P(t, y, off) for t in ths for off in (0.0, -0.006)]
        faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(ths) - 1)]
        k.b.mesh(G, "belt_leather", verts, facing(verts, faces, lambda c, u=up: np.array((0.0, u, 0.0))), smooth=False)
        # the gold piping along the edge
        k.sweep("trophy_gold", [P(t, y - 0.003 * up, 0.002) for t in ths], 0.0042, 8)

    to_theta = _arc_to_theta()

    def plate(mat, outline, s0, y0, off0, off1, rings=3):
        """A plate laid on the strap: `outline` (local x along the strap, y up, about
        its middle) at arc length s0, from off0 to off1 outward."""
        pts = np.asarray(outline, float)
        n = len(pts)

        def at(px, py, off):
            return P(float(to_theta(s0 + px)), y0 + py, off)
        verts = [at(0.0, 0.0, off1)]
        for r in range(1, rings + 1):
            for px, py in pts * (r / rings):
                verts.append(at(px, py, off1))
        faces = [(0, 1 + (i + 1) % n, 1 + i) for i in range(n)]
        for r in range(rings - 1):
            a0, a1 = 1 + r * n, 1 + (r + 1) * n
            faces += [(a0 + i, a0 + (i + 1) % n, a1 + (i + 1) % n, a1 + i) for i in range(n)]
        k.b.mesh(G, mat, verts, facing(verts, faces, radial), smooth=True)
        # its edge, down to the strap, facing out from the plate's middle
        mid = np.asarray(at(0.0, 0.0, (off0 + off1) / 2))
        rim = [at(px, py, off) for px, py in pts for off in (off1, off0)]
        rf = [(2 * i, 2 * ((i + 1) % n), 2 * ((i + 1) % n) + 1, 2 * i + 1) for i in range(n)]
        k.b.mesh(G, mat, rim, facing(rim, rf, lambda c: c - mid), smooth=False)

    def octagon(w, h, c, per=4):
        corners = [(-w / 2, -h / 2 + c), (-w / 2 + c, -h / 2), (w / 2 - c, -h / 2), (w / 2, -h / 2 + c),
                   (w / 2, h / 2 - c), (w / 2 - c, h / 2), (-w / 2 + c, h / 2), (-w / 2, h / 2 - c)]
        out = []
        for i in range(8):
            a, b_ = np.array(corners[i]), np.array(corners[(i + 1) % 8])
            out += [tuple(a + (b_ - a) * t) for t in np.linspace(0, 1, per, endpoint=False)]
        return out

    def circle(r, n=40):
        return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]

    def star(ro, ri, n=5):
        return [((ro if i % 2 == 0 else ri) * math.cos(math.pi / 2 + math.pi * i / n),
                 (ro if i % 2 == 0 else ri) * math.sin(math.pi / 2 + math.pi * i / n)) for i in range(2 * n)]

    # the centre plate
    plate("trophy_gold", octagon(0.31, 0.25, 0.055), 0.0, yb, 0.0, 0.009)
    plate("trophy_gold", circle(0.101), 0.0, yb, 0.009, 0.014)                 # a raised gold ring
    plate("belt_enamel", circle(0.086), 0.0, yb, 0.014, 0.0145)                # the enamel inside it
    plate("trophy_gold", star(0.064, 0.026), 0.0, yb, 0.0145, 0.019, rings=2)  # the star
    for px, py in octagon(0.265, 0.205, 0.045, per=1):                         # studs round the edge
        th = float(to_theta(px))
        x, z = _ellipse(th, 0.012)
        sphere(k, "trophy_gold", f((float(x), yb + py, float(z))), 0.0065, 10)
    # the side plates, two each side, following the strap round
    for s in (-0.36, -0.235, 0.235, 0.36):
        plate("trophy_gold", octagon(0.095, 0.155, 0.02, per=3), s, yb, 0.0, 0.007)
        plate("belt_enamel", circle(0.030, 28), s, yb, 0.007, 0.0075)
        plate("trophy_gold", circle(0.013, 20), s, yb, 0.0075, 0.010, rings=2)


# ---- medals -----------------------------------------------------------------------------------
def medal(k, f, c, metal, stripes, tilt=0.0, hang=None, r=0.038):
    """A medal facing local +z with its middle at c (in frame f): a flat disc with a raised
    rim and an embossed star (`coin`), a loop on top, and its ribbon. With `hang` it hangs from a brass pin that far
    above, the ribbon in a V; otherwise it stands on a small black easel, leaning back by
    `tilt` degrees, its ribbon folded behind it on the floor of the case."""
    T = rot(x=-tilt)
    c = np.asarray(c, float)

    def F(q):
        return f(tuple(c + T @ np.asarray(q, float)))
    coin(k, metal, F, r, 0.0045)
    ring = [F((0.0055 * math.sin(a), r + 0.0045 + 0.0055 * math.cos(a), 0.0)) for a in np.linspace(0, 2 * math.pi, 13)]
    k.sweep(metal, ring, 0.0013, 6, caps=False)
    top = c + T @ np.array((0.0, r + 0.010, -0.003))
    if hang:
        pin = np.array((c[0], c[1] + hang, 0.026))
        for sgn, dz in ((-1, 0.0), (1, 0.0012)):
            a = np.array((sgn * 0.020, pin[1], pin[2] + dz))
            b_ = np.array((sgn * 0.002, top[1], top[2] - 0.004 + dz))
            a[0] += c[0]
            b_[0] += c[0]
            path = [f(tuple(a + (b_ - a) * s)) for s in np.linspace(0, 1, 6)]
            # the leg's width runs across it, square to its length, in the wall's plane
            along = np.subtract(path[-1], path[0])
            normal = np.subtract(f((0, 0, 1)), f((0, 0, 0)))
            side = np.cross(along, normal)
            strip(k, path, side, 0.030, stripes)
        sphere(k, "trophy_brass", f(tuple(pin + (0, 0, 0.003))), 0.0045, 10)
    else:
        # the easel: a base, and a back leaning with the medal
        base = c + np.array((0.0, -r - 0.004, 0.0))
        k.soft("trophy_black", f, tuple(base + (0, -0.004, -0.004)), (0.075, 0.008, 0.05), 0.002, n=1)
        k.soft("trophy_black", f, tuple(c + T @ np.array((0.0, -0.01, -0.012))), (0.02, 0.07, 0.004), 0.001, n=1,
               tilt=-tilt, pivot=tuple(c + T @ np.array((0.0, -0.01, -0.012))))
        # the ribbon, from the loop back over the easel and down, folded flat behind
        floor = base[1] - 0.008
        p0 = top
        p1 = c + T @ np.array((0.0, r + 0.02, -0.03))
        p2 = np.array((c[0], floor + 0.02, c[2] - 0.08))
        p3 = np.array((c[0], floor + 0.0015, c[2] - 0.12))
        p4 = np.array((c[0], floor + 0.0015, c[2] - 0.20))
        path = [f(tuple(p)) for p in (p0, p1, p2, p3, p4)]
        side = np.subtract(f((1, 0, 0)), f((0, 0, 0)))
        strip(k, path, side, 0.032, stripes)


RIBBONS = {
    "red": [(0.66, 0.08, 0.08), (0.92, 0.90, 0.86), (0.66, 0.08, 0.08)],
    "navy": [(0.10, 0.14, 0.32), (0.92, 0.90, 0.86), (0.10, 0.14, 0.32)],
    "black": [(0.05, 0.05, 0.055), (0.84, 0.66, 0.30), (0.05, 0.05, 0.055)],
    "teal": [(0.06, 0.40, 0.42), (0.92, 0.90, 0.86), (0.06, 0.40, 0.42)],
    "blue": [(0.12, 0.30, 0.62), (0.84, 0.66, 0.30), (0.12, 0.30, 0.62)],
}


def boxing_medals(k, f):
    """Two medals hung either side of the belt, and one on a stand at each front corner."""
    deck = CASE["base"] + 0.012
    for x, y, metal, rib in ((-0.42, 2.03, "trophy_gold", "red"), (-0.42, 1.62, "trophy_silver", "navy"),
                             (0.42, 2.03, "trophy_gold", "red"), (0.42, 1.62, "trophy_bronze", "red")):
        medal(k, f, (x, y, 0.040), metal, RIBBONS[rib], hang=0.175)
    for x, metal, rib in ((-0.40, "trophy_gold", "navy"), (0.40, "trophy_silver", "red")):
        medal(k, f, (x, deck + 0.046, 0.37), metal, RIBBONS[rib], tilt=14.0)


def wins(k, f):
    """The coding and esports case: three medals on ribbons along the top, a glass shelf
    with a silver cup, a crystal award and a gold star trophy, and two medals on stands
    on the floor of the case with a crystal plaque between them."""
    W, D = CASE["w"], CASE["d"]
    deck = CASE["base"] + 0.012
    shelf = 1.62
    for x, metal, rib in ((-0.34, "trophy_gold", "teal"), (0.0, "trophy_gold", "blue"), (0.34, "trophy_silver", "black")):
        medal(k, f, (x, 2.05, 0.040), metal, RIBBONS[rib], hang=0.175)
    # the glass shelf on two small brass brackets
    k.box("case_glass", f, (-W / 2 + 0.03, shelf - 0.010, 0.025), (W / 2 - 0.03, shelf, D - 0.05))
    for x in (-0.40, 0.40):
        k.soft("trophy_brass", f, (x, shelf - 0.02, 0.04), (0.02, 0.02, 0.04), 0.004, n=1)
    # a silver cup on a black base
    g = Frame(f((-0.33, shelf, 0.24)), f.yaw)
    k.soft("trophy_black", g, (0.0, 0.0225, 0.0), (0.10, 0.045, 0.10), 0.004, n=1)
    k.lathe("trophy_silver", g, [(0.0, 0.045), (0.045, 0.045), (0.045, 0.052), (0.02, 0.065), (0.011, 0.10), (0.016, 0.11),
                                 (0.011, 0.12), (0.03, 0.14), (0.06, 0.18), (0.072, 0.23), (0.074, 0.245), (0.068, 0.245),
                                 (0.062, 0.22), (0.045, 0.17), (0.0, 0.155)], 32)
    for sx in (-1, 1):
        k.sweep("trophy_silver", [g((sx * x, y, 0.0)) for x, y in ((0.066, 0.22), (0.10, 0.225), (0.108, 0.19), (0.09, 0.165), (0.05, 0.16))],
                0.005, 8)
    # a crystal award: a slanted glass block on a black base
    g = Frame(f((0.0, shelf, 0.24)), f.yaw)
    k.soft("trophy_black", g, (0.0, 0.02, 0.0), (0.15, 0.04, 0.07), 0.004, n=1)
    verts = [(-0.05, 0.04, -0.022), (0.05, 0.04, -0.022), (0.05, 0.04, 0.022), (-0.05, 0.04, 0.022),
             (-0.05, 0.25, -0.022), (0.05, 0.30, -0.022), (0.05, 0.30, 0.022), (-0.05, 0.25, 0.022)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    k.mesh("crystal", g, verts, faces, smooth=False)
    # a gold star on a fluted column
    g = Frame(f((0.33, shelf, 0.24)), f.yaw)
    k.soft("trophy_black", g, (0.0, 0.025, 0.0), (0.09, 0.05, 0.09), 0.004, n=1)
    k.lathe("trophy_gold", g, [(0.0, 0.05), (0.03, 0.05), (0.03, 0.06), (0.016, 0.07), (0.014, 0.16), (0.022, 0.17), (0.0, 0.175)], 16)
    pts = [(math.cos(math.pi / 2 + math.pi * i / 5) * (0.06 if i % 2 == 0 else 0.025),
            math.sin(math.pi / 2 + math.pi * i / 5) * (0.06 if i % 2 == 0 else 0.025)) for i in range(10)]
    cy = 0.235
    front = [(0.0, cy, 0.008)] + [(x, cy + y, 0.004) for x, y in pts]
    back = [(0.0, cy, -0.008)] + [(x, cy + y, -0.004) for x, y in pts]
    verts = front + back
    faces = [(0, 1 + i, 1 + (i + 1) % 10) for i in range(10)] + [(11, 12 + (i + 1) % 10, 12 + i) for i in range(10)]
    faces += [(1 + i, 12 + i, 12 + (i + 1) % 10, 1 + (i + 1) % 10) for i in range(10)]
    k.mesh("trophy_gold", g, verts, faces, smooth=False)
    # on the floor of the case
    for x, metal, rib in ((-0.40, "trophy_gold", "teal"), (0.40, "trophy_bronze", "blue")):
        medal(k, f, (x, deck + 0.046, 0.37), metal, RIBBONS[rib], tilt=14.0)
    g = Frame(f((0.0, deck, 0.30)), f.yaw)
    k.soft("trophy_black", g, (0.0, 0.015, 0.0), (0.22, 0.03, 0.06), 0.004, n=1)
    k.box("crystal", g, (-0.09, 0.03, -0.012), (0.09, 0.15, 0.012))


# ---- the console, the cup and the photo -------------------------------------------------------
def wall_frame():
    return Frame((XE - LINING, F2, WALL_Z), -90.0)


def console(k):
    """A low walnut console under the photo: three doors with hairline gaps over a black
    recessed plinth; the cup in the middle, books and a brass sphere on one side, a small
    silver bowl on the other."""
    from .study import book_flat
    f = wall_frame()
    L, D, Hc = CONSOLE["L"], CONSOLE["D"], CONSOLE["H"]
    x0, x1 = -L / 2, L / 2
    k.block("trophy_black", f, (x0 + 0.05, 0.0, 0.0), (x1 - 0.05, 0.07, D - 0.05), step=0.3, skip=("-y", "-z", "+y"))
    k.grain("trophy_walnut", f, (x0, Hc - 0.03, 0.0), (x1, Hc, D), step=0.08, skip=("-z",), along="x")
    for x in (x0, x1 - 0.025):
        k.grain("trophy_walnut", f, (x, 0.07, 0.0), (x + 0.025, Hc - 0.03, D), step=0.08, skip=("-z", "-y"), along="y")
    k.grain("trophy_walnut", f, (x0 + 0.025, 0.07, 0.0), (x1 - 0.025, 0.09, D), step=0.1, skip=("-z", "-y"))
    n, gap = 3, 0.003
    w = (L - 0.05) / n
    for i in range(n):
        a = x0 + 0.025 + i * w
        k.grain("trophy_walnut", f, (a + gap / 2, 0.09 + gap, D - 0.02), (a + w - gap / 2, Hc - 0.03 - gap, D),
                step=0.07, skip=("-z",), along="y")
        k.soft("trophy_brass", f, (a + w / 2, Hc - 0.09, D + 0.006), (0.12, 0.010, 0.012), 0.004, n=1)
    k.block("trophy_black", f, (x0 + 0.025, 0.09, D - 0.03), (x1 - 0.025, Hc - 0.03, D - 0.02), step=0.3, skip=("-z",))
    # books and a sphere on the left, a small silver bowl on the right
    g = Frame(f((x0 + 0.34, Hc, D / 2)), f.yaw + 4)
    book_flat(k, g, (0.0, 0.0), (0.30, 0.035, 0.23), "book_navy")
    book_flat(k, Frame(g((0.0, 0.035, 0.0)), f.yaw - 5), (0.0, 0.0), (0.26, 0.026, 0.19), "book_cream")
    sphere(k, "trophy_brass", g((0.02, 0.061 + 0.055, 0.0)), 0.055, 24)
    k.lathe("trophy_silver", Frame(f((x1 - 0.32, Hc, D / 2))),
            [(0.0, 0.0), (0.05, 0.0), (0.10, 0.035), (0.125, 0.07), (0.118, 0.072), (0.092, 0.038), (0.0, 0.01)], 40)


def cup(k):
    """The cup: a gold two-handled trophy on a stepped black base, in the middle of the
    console under its own spot."""
    f = wall_frame()
    y0 = CONSOLE["H"]
    g = Frame(f((0.0, y0, CONSOLE["D"] / 2)), f.yaw)
    k.soft("trophy_black", g, (0.0, 0.04, 0.0), (0.24, 0.08, 0.24), 0.006, n=2)
    k.soft("trophy_black", g, (0.0, 0.105, 0.0), (0.19, 0.05, 0.19), 0.005, n=2)
    k.soft("trophy_brass", g, (0.0, 0.045, 0.121), (0.12, 0.035, 0.003), 0.001, n=1)
    base = 0.13
    prof = [(0.0, 0.0), (0.075, 0.0), (0.075, 0.012), (0.055, 0.022), (0.028, 0.05), (0.020, 0.10), (0.030, 0.118),
            (0.020, 0.135), (0.018, 0.17), (0.04, 0.19), (0.085, 0.225), (0.118, 0.275), (0.135, 0.33), (0.14, 0.37),
            (0.143, 0.388), (0.134, 0.388), (0.129, 0.36), (0.116, 0.30), (0.08, 0.255), (0.0, 0.24)]
    k.lathe("trophy_gold", Frame(g((0.0, base, 0.0))), [(r, h + 0.0) for r, h in prof], 48)
    for sx in (-1, 1):
        p0, p1, p2, p3 = (np.array(p) for p in ((0.128, 0.345), (0.27, 0.39), (0.255, 0.21), (0.096, 0.24)))
        path = []
        for t in np.linspace(0, 1, 18):
            q = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
            path.append(g((sx * q[0], base + q[1], 0.0)))
        k.sweep("trophy_gold", path, 0.0085, 10)
    spot = (TRACK_X, RY - 0.10, WALL_Z + 0.25)
    aim = g((0.0, base + 0.25, 0.0))
    LAMPS.append(dict(name="cup_spot", kind="spot", pos=spot, aim=tuple(np.subtract(aim, spot)), watts=26.0, cone=22.0))


def photo_frame(k):
    """The team photo's frame over the console: a black moulding round a wide white mat,
    with a plain linen board where the photo will go (material `team_photo`)."""
    f = wall_frame()
    w, h, yc = PHOTO["w"], PHOTO["h"], PHOTO["y"]
    x0, x1, y0, y1 = -w / 2, w / 2, yc - h / 2, yc + h / 2
    fr, d = PHOTO["fr"], 0.04
    for lo, hi in (((x0, y0, 0.004), (x0 + fr, y1, d)), ((x1 - fr, y0, 0.004), (x1, y1, d)),
                   ((x0 + fr, y0, 0.004), (x1 - fr, y0 + fr, d)), ((x0 + fr, y1 - fr, 0.004), (x1 - fr, y1, d))):
        k.block("trophy_black", f, lo, hi, step=0.08, skip=("-z",))
    a0, a1, b0, b1 = x0 + fr, x1 - fr, y0 + fr, y1 - fr
    m = PHOTO["mat"]
    p0, p1, q0, q1 = a0 + m, a1 - m, b0 + m, b1 - m
    z = d - 0.012
    for sa, sb, ta, tb in ((a0, a1, b0, q0), (a0, a1, q1, b1), (a0, p0, q0, q1), (p1, a1, q0, q1)):
        v, fc, _ = grid((sa, ta, z), (sb - sa, 0, 0), (0, tb - ta, 0), max(1, round((sb - sa) / 0.05)), max(1, round((tb - ta) / 0.05)))
        k.mesh("trophy_mat", f, v, fc, smooth=False)
    v, fc, uv = grid((p0, q0, z - 0.003), (p1 - p0, 0, 0), (0, q1 - q0, 0), max(2, round((p1 - p0) / 0.05)), max(2, round((q1 - q0) / 0.05)))
    k.mesh("team_photo", f, v, fc, smooth=False, uvs=uv)


# ---- the bench, the chess table, the fig ------------------------------------------------------
def bench(k):
    """A long gallery bench in cognac leather on two black steel frames, facing the display."""
    x, z, L, D, Hb = BENCH["x"], BENCH["z"], BENCH["L"], BENCH["D"], BENCH["H"]
    f = Frame((x, F2, z), -90.0)                   # its length along local x (world z)
    t = 0.10
    soft_fine(k, "trophy_leather", f, (0.0, Hb - t / 2, 0.0), (L, t, D), 0.035, div=10,
              shape=lambda vx, vy, vz: (vx, vy + (0.006 * (1 - (2 * vx / L) ** 2) if vy > 0 else 0.0), vz))
    for sx in (-1, 1):
        lx = sx * (L / 2 - 0.12)
        top = Hb - t - 0.005
        for sz in (-1, 1):
            k.rod("trophy_black", f((lx, 0.0, sz * (D / 2 - 0.04))), f((lx, top, sz * (D / 2 - 0.04))), 0.025)
        k.rod("trophy_black", f((lx, top, -(D / 2 - 0.04))), f((lx, top, D / 2 - 0.04)), 0.025)
    k.rod("trophy_black", f((-(L / 2 - 0.12), Hb - t - 0.02, 0.0)), f((L / 2 - 0.12, Hb - t - 0.02, 0.0)), 0.02)


def parse_fen(fen):
    out = {}
    for row, text in enumerate(fen.split()[0].split("/")):
        rank, file = 7 - row, 0
        for ch in text:
            if ch.isdigit():
                file += int(ch)
            else:
                out[(file, rank)] = ch
                file += 1
    return out


def chess_table(k):
    """A walnut chess table by the glass, its board inlaid in maple and walnut, a set
    standing ready (FEN), and a leather chair at each side: White on the east."""
    from .dining import PIECE_OBJECTS
    from .library import desk_chair
    from .props import load, place
    cx, cz, top, S = CHESS["x"], CHESS["z"], CHESS["top"], CHESS["size"]
    y = F2 + top
    half = S / 2
    world = Frame((0.0, 0.0, 0.0))
    border = 0.022
    bh = 4 * SQUARE + border                        # the board's half-width
    # the top: four walnut strips round the board (nothing lies over a face lit per vertex, gotcha 26)
    t = 0.035
    for lo, hi in (((cx - half, y - t, cz - half), (cx + half, y, cz - bh)), ((cx - half, y - t, cz + bh), (cx + half, y, cz + half)),
                   ((cx - half, y - t, cz - bh), (cx - bh, y, cz + bh)), ((cx + bh, y - t, cz - bh), (cx + half, y, cz + bh))):
        k.grain("trophy_walnut", world, lo, hi, step=0.06, along="x")
    # the board: squares painted per vertex, each its own points so the edges stay crisp
    k.block("trophy_walnut_v", world, (cx - bh, y - t, cz - bh), (cx + bh, y - 0.004, cz + bh), step=0.2, skip=("+y",))
    light, dark, edge = (srgb_to_linear(c) for c in ((0.80, 0.68, 0.50), (0.27, 0.16, 0.10), (0.18, 0.11, 0.07)))
    verts, faces, colors = [], [], []

    def square(xa, xb, za, zb, colour, n=2):
        base = len(verts)
        for i in range(n + 1):
            for j in range(n + 1):
                verts.append((xa + (xb - xa) * i / n, y + 0.0015, za + (zb - za) * j / n))
                colors.append(colour)
        for i in range(n):
            for j in range(n):
                a, c = base + i * (n + 1) + j, base + (i + 1) * (n + 1) + j
                faces.append((a, a + 1, c + 1, c))
    for xa, xb, za, zb in ((cx - bh, cx + bh, cz - bh, cz - bh + border), (cx - bh, cx + bh, cz + bh - border, cz + bh),
                           (cx - bh, cx - bh + border, cz - bh + border, cz + bh - border),
                           (cx + bh - border, cx + bh, cz - bh + border, cz + bh - border)):
        square(xa, xb, za, zb, edge, 3)
    # White sits on the east (+x): rank 1 at +x, the a-file on White's left (+z)
    for file in range(8):
        for rank in range(8):
            xc, zc = cx + (3.5 - rank) * SQUARE, cz + (3.5 - file) * SQUARE
            colour = dark if (file + rank) % 2 == 0 else light
            square(xc - SQUARE / 2, xc + SQUARE / 2, zc - SQUARE / 2, zc + SQUARE / 2, colour)
    k.b.mesh(G, "trophy_albedo", verts, faces, smooth=False, colors=colors)
    # the pedestal: a turned column on a crossed foot, an apron under the top
    k.block("trophy_walnut_v", world, (cx - 0.17, y - t - 0.05, cz - 0.17), (cx + 0.17, y - t, cz + 0.17), step=0.1, skip=("+y",))
    k.lathe("trophy_walnut_v", Frame((cx, F2, cz)), [(0.0, 0.05), (0.07, 0.05), (0.05, 0.10), (0.042, 0.20), (0.05, 0.45),
                                                    (0.042, 0.60), (0.06, 0.64), (0.06, top - t - 0.05), (0.0, top - t - 0.05)], 32)
    for yaw in (45.0, -45.0):
        k.soft("trophy_walnut_v", Frame((cx, F2, cz), yaw), (0.0, 0.03, 0.0), (0.62, 0.06, 0.07), 0.015, n=2)
    # the pieces (Poly Haven's chess set, in plain ivory and ebony)
    wanted = {name.format(colour) for name in PIECE_OBJECTS.values() for colour in ("white", "black")}
    pieces = load("chess_set", only=wanted, thin={n: (0.45 if "pawn" in n else 0.35) for n in wanted})
    rng = np.random.default_rng(6)
    for (file, rank), letter in parse_fen(FEN).items():
        colour = "white" if letter.isupper() else "black"
        piece = pieces[PIECE_OBJECTS[letter.lower()].format(colour)]
        x = cx + (3.5 - rank) * SQUARE + rng.uniform(-0.002, 0.002)
        z = cz + (3.5 - file) * SQUARE + rng.uniform(-0.002, 0.002)
        twist = rng.uniform(-0.15, 0.15) if letter.lower() == "n" else rng.uniform(-0.6, 0.6)
        # the set is modelled with White at -z; here White is at +x, so a quarter turn
        place(k.b, G, f"trophy_chess_{colour}", piece, (x, y + 0.0015, z), yaw=-math.pi / 2 + twist)
    for side in (-1, 1):
        f = Frame((cx + side * 0.66, F2, cz), 90.0 if side < 0 else -90.0)
        desk_chair(k, f, leather="trophy_leather", wood="trophy_walnut_v", brass="trophy_brass")
    spot = (cx, RY - 0.06, cz + 0.2)
    LAMPS.append(dict(name="chess_spot", kind="spot", pos=spot, aim=(0.0, -1.0, -0.08), watts=30.0, cone=50.0))


def fig(k):
    """A fig (Poly Haven's potted_plant_01, CC0) in a dark stone pot, in the corner by
    the library wall."""
    from .props import load, place
    x, z = FIG
    f = Frame((x, F2, z))
    h = 0.46
    k.lathe("trophy_planter", f, [(0.0, 0.0), (0.17, 0.0), (0.20, 0.05), (0.21, h), (0.195, h), (0.195, h - 0.04),
                                  (0.0, h - 0.04)], 40)
    plant = load("potted_plant_01", only={"potted_plant_01_leaves", "potted_plant_01_stem"},
                 thin={"potted_plant_01_leaves": 0.25})
    for name, piece in plant.items():
        mat = "trophy_fig_leaves" if name.endswith("leaves") else "trophy_fig_stems"
        place(k.b, G, mat, piece, (x, F2 + h - 0.04, z), yaw=2.2, scale=1.7, origin=(0.0, 0.5, 0.0))


# ---- the lights ----------------------------------------------------------------------------------
def track(k):
    """A slim black track along the ceiling in front of the display wall, with a spot for
    each case, the photo and the chess table (the cup has its own, in `cup`)."""
    y = RY - 0.03
    k.rod("trophy_black", (TRACK_X, y, -7.05), (TRACK_X, y, -0.85), 0.034)
    cf = {name: case_frame(z) for name, z in CASE_Z.items()}
    D = CASE["d"]
    targets = [("boxing", cf["boxing"]((0.0, 1.60, D)), CASE_Z["boxing"] + 0.35, 40.0, 30.0),
               ("wins", cf["wins"]((0.0, 1.60, D)), CASE_Z["wins"] - 0.35, 40.0, 30.0),
               ("photo", wall_frame()((0.0, PHOTO["y"], 0.0)), WALL_Z - 0.45, 30.0, 34.0),
               ("cup", None, WALL_Z + 0.25, 0.0, 0.0)]
    for name, aim, z, watts, cone in targets:
        head = np.array((TRACK_X, y - 0.10, z))
        if aim is None:
            aim = wall_frame()((0.0, CONSOLE["H"] + 0.38, CONSOLE["D"] / 2))
        d = np.subtract(aim, head)
        d /= np.linalg.norm(d)
        k.tube("trophy_black", (TRACK_X, y - 0.015, z), tuple(head), 0.006, segments=8)
        k.tube("trophy_black", tuple(head - d * 0.05), tuple(head + d * 0.07), 0.030, segments=16)
        k.tube("light_warm", tuple(head + d * 0.07), tuple(head + d * 0.072), 0.024, segments=16, step=0.002)
        if watts:
            pos = head + d * 0.09
            LAMPS.append(dict(name=f"track_{name}", kind="spot", pos=tuple(pos), aim=tuple(d), watts=watts, cone=cone))


# ---- medals' discs and the second belt -----------------------------------------------------------
def coin(k, mat, F, r, t, n=44, star=0.50):
    """A medal's disc, its face looking along local +z (F maps its own points to the world):
    flat back and face, a raised rim round the edge, a thin raised ring and an embossed star
    in the middle, and a smooth band round the edge. Flat faces stay flat when lit per vertex,
    where a rounded tube's caps came out looking like little balls."""
    z0, z1 = -t / 2, t / 2
    rim, ri = z1 + 0.0012, 0.84 * r
    a0 = np.asarray(F((0.0, 0.0, 0.0)), float)
    axis = np.asarray(F((0.0, 0.0, 1.0)), float) - a0

    def radial(c):
        v = np.asarray(c, float) - a0
        return v - axis * np.dot(v, axis)
    angles = [2 * math.pi * i / n for i in range(n)]

    def ring(rad, z):
        return [F((rad * math.cos(a), rad * math.sin(a), z)) for a in angles]

    def band(ra, za, rb, zb, want, smooth=False):
        verts = ring(ra, za) + ring(rb, zb)
        faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        k.b.mesh(G, mat, verts, facing(verts, faces, want), smooth=smooth)

    def disc(rad, z, want):
        verts = [F((0.0, 0.0, z))] + ring(rad, z)
        faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
        k.b.mesh(G, mat, verts, facing(verts, faces, want), smooth=False)
    band(r, z0, r, rim, radial, smooth=True)                       # the edge
    disc(r, z0, lambda c: -axis)                                   # the back
    band(ri, rim, r, rim, lambda c: axis)                          # the rim's top
    band(ri, z1, ri, rim, lambda c: -radial(c))                    # its inside wall
    disc(ri, z1, lambda c: axis)                                   # the face
    band(0.62 * ri, z1 + 0.0007, 0.70 * ri, z1 + 0.0007, lambda c: axis)   # a thin raised ring
    # the star, standing proud of the face
    ro, rn, e = star * ri, star * ri * 0.42, z1 + 0.0011
    pts = [((ro if i % 2 == 0 else rn) * math.cos(math.pi / 2 + math.pi * i / 5),
            (ro if i % 2 == 0 else rn) * math.sin(math.pi / 2 + math.pi * i / 5)) for i in range(10)]
    top = [F((0.0, 0.0, e))] + [F((x, y, e)) for x, y in pts]
    k.b.mesh(G, mat, top, facing(top, [(0, 1 + i, 1 + (i + 1) % 10) for i in range(10)], lambda c: axis), smooth=False)
    side = [F((x, y, zz)) for x, y in pts for zz in (z1, e)]
    sf = [(2 * i, 2 * ((i + 1) % 10), 2 * ((i + 1) % 10) + 1, 2 * i + 1) for i in range(10)]
    k.b.mesh(G, mat, side, facing(side, sf, radial), smooth=False)


def hung_belt(k, f):
    """A second belt hung flat on the velvet above the first, from a brass pin at each end,
    sagging a little in the middle: a black strap edged in gold, a round gold centre plate
    and a smaller plate each side."""
    xe, ytop, sag, w, z = 0.33, 2.17, 0.09, 0.13, 0.034
    xs = np.linspace(-xe, xe, 41)
    ys = ytop - sag * (1 - (xs / xe) ** 2)
    path = [f((float(x), float(y), z)) for x, y in zip(xs, ys)]
    along = np.subtract(path[-1], path[0])
    out = np.subtract(f((0, 0, 1)), f((0, 0, 0)))
    side = np.cross(along, out)
    # the strap, painted per vertex, edges kept square to its curve
    verts, faces, colors = [], [], []
    black = srgb_to_linear((0.07, 0.065, 0.065))
    for i, (x, y) in enumerate(zip(xs, ys)):
        slope = -sag * (-2 * x / xe ** 2)
        nx, ny = -slope, 1.0
        m = math.hypot(nx, ny)
        nx, ny = nx / m, ny / m
        for s in (-w / 2, w / 2):
            verts.append(f((float(x + nx * s), float(y + ny * s), z)))
            colors.append(black)
    for i in range(len(xs) - 1):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    k.b.mesh(G, "trophy_albedo", verts, facing(verts, faces, lambda c: out), smooth=False, colors=colors)
    for s in (-1, 1):
        edge = []
        for x, y in zip(xs, ys):
            slope = -sag * (-2 * x / xe ** 2)
            m = math.hypot(slope, 1.0)
            edge.append(f((float(x - slope / m * s * (w / 2 - 0.003)), float(y + 1 / m * s * (w / 2 - 0.003)), z + 0.002)))
        k.sweep("trophy_gold", edge, 0.0035, 8)
    for x in (-xe + 0.015, xe - 0.015):
        sphere(k, "trophy_brass", f((x, ytop + 0.005, z + 0.006)), 0.006, 10)
    # the plates
    for x, r in ((0.0, 0.088), (-0.19, 0.040), (0.19, 0.040)):
        y = ytop - sag * (1 - (x / xe) ** 2)

        def F(q, x=x, y=y):
            return f((x + q[0], y + q[1], z + 0.006 + q[2]))
        coin(k, "trophy_gold", F, r, 0.008, star=0.62)
