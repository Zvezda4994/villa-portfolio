"""The main bedroom (languages), furnished: soft and minimal. A low oak bed in white
linen against a wide upholstered headboard, the world map with two pins (Moscow
and Tokyo) over it, a nightstand with a lamp, a floor lamp, a pale wool rug and a
bench at the foot of the bed; on the wall to the lounge, a shelf of books over a
reading chair, and beside it, on the games room wall, a record player on a low console.

Plan, looking down, seen from the driveway (the lounge wall at the top, so +x is on
the right):

                       lounge door            shelf, over the chair         (z = 2)
     +------------------[      ]--------------[=====]------------------+
     |                                         (chair)(table) [records] |
   s |                                                        [stand]   | g
   i |                                                                  h a
   d glass                       ~~~~~~~~~~ rug ~~~~~~~~ [bench][ bed  ]| e m
   e |                                                      [          ]| a e
     |                                                         (lamp)   d s
     |                                                     map over the bed
     +------------[============== glass ==============]----------------+
                                                                        (z = -8)

The map is an original print made here from Natural Earth's public-domain coastlines
(1:110m), the pins are modelled. The books' spines are printed from
data/bedroom_books.txt.

Everything is lit per vertex, the walls and the ceiling lined over the house's own, so
the room stays clean from a quick draft bake; it has no lightmap.
"""
import json
import math

import numpy as np

from . import config as C
from .house import P
from .kit import Frame, Kit, cushion, grid, panel, rot, wall
from .materials import srgb_to_linear
from .study import _smooth_noise, book_flat, book_upright
from .textures import picture_path, save_png

ROOM, G = "bedroom", "upper"
F2, RY = C.F2, C.ROOF_Y
H = RY - F2
BOOKS_FILE = C.ROOT / "data" / "bedroom_books.txt"

# The room's inside faces (heights below are above the bedroom's floor, F2).
XW = -C.HALF_W + C.WALL           # the west wall, a window in it from z -6 to -2 (-11.7)
XE = -5.0 - P / 2                 # the wall to the games room, the headboard's wall (-5.075)
ZB = -C.HALF_D + C.WALL           # the back wall, glass from x -10.5 to -6.5 (-7.7)
ZN = 2.0 - P / 2                  # the wall to the lounge (1.925)
LOUNGE_DOOR = (-9.5, -7.5)
BACK_GLASS = (-10.5, -6.5)
SIDE_GLASS = (-6.0, -2.0)
LINING = 0.012

BED_Z = -3.60                     # the bed's middle along the headboard wall
HEADBOARD = dict(w=3.50, y=(0.22, 1.25), d=0.10, n=7)
MATTRESS = dict(w=1.93, l=2.03, h=0.25, z=0.17, y=0.30)      # z: its head end, out from the wall
FRAME = dict(w=2.05, z=(0.10, 2.24), y=(0.05, 0.30))
STAND = dict(x=1.405, w=0.55, d=0.45, h=0.52)               # the nightstand, in the bed's frame
FLOOR_LAMP = (-1.45, 0.32)
RUG = dict(x=(-8.80, -6.10), z=(-5.30, -1.90), t=0.012)
SHELF_X = -6.30                   # the shelf's middle along the lounge wall
MAP = dict(w=1.62, h=0.64, y=1.96, fr=0.028)  # over the headboard, on the bed's middle
LAT = (-58.0, 84.0)               # the map's latitude range (it's a plain equirectangular projection)
PINS = [("Russia", 55.76, 37.62), ("Japan", 35.68, 139.69)]     # at the capitals, Moscow and Tokyo
SHELF = dict(y=1.30, w=1.40, d=0.22, t=0.035)
CHAIR = dict(pos=(-6.72, 1.18), yaw=166.0)
SIDE_TABLE = (-5.86, 1.42)
BENCH = dict(z=(2.42, 2.84), w=1.50, h=0.45)       # in the bed's frame
# the low console with the record player, on the games room wall south of the reading chair's table
CONSOLE = dict(z=(-0.32, 0.80), d=0.40, h=0.48)

CEILING_LIGHT = 0.30
LAMPS = []

# Review cameras. The first is also the room's view on the website: from the corner by the
# glass, across the foot of the bed to the headboard and the map, the reading chair on the right.
BEDROOM_CAM = dict(pos=(-10.55, F2 + 1.55, -6.55), target=(-5.60, F2 + 1.05, -1.20), fov=55.0)
MAP_CAM = dict(pos=(XE - 2.20, F2 + 1.62, BED_Z + 0.30), target=(XE, F2 + 1.62, BED_Z), fov=50.0)
SHELF_CAM = dict(pos=(-6.25, F2 + 1.30, -0.55), target=(-6.30, F2 + 0.95, 1.925), fov=50.0)
RECORDS_CAM = dict(pos=(-6.65, F2 + 1.38, -0.70), target=(-5.30, F2 + 0.52, 0.30), fov=50.0)


def build_bedroom(b):
    LAMPS.clear()
    titled = read_books()
    cells = paint_spines(titled)
    paint_map()
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    with b.room(ROOM):
        walls(k)
        ceiling(Kit(b, "roof", None))
        rug(k)
        f = bed_frame()
        headboard(k, f)
        bed(k, f)
        nightstand(k, f)
        floor_lamp(k, f)
        bench(k, f)
        world_map(k, f)
        shelf(k, titled, cells)
        reading_chair(k)
        b.anchor("bedroom_record_player", record_console(k))


def read_books():
    out = []
    for raw in BOOKS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        title, _, colour = line.partition("|")
        rgb = tuple(float(v) for v in colour.split(",")) if colour.strip() else (0.84, 0.80, 0.70)
        if len(rgb) != 3:
            raise ValueError(f"data/bedroom_books.txt: '{line}' needs a colour as three numbers")
        out.append(dict(title=title.strip(), colour=rgb))
    return out


# ---- walls and ceiling ------------------------------------------------------------------------
def walls(k):
    """Plaster linings over the house's walls, lit per vertex on a grid, each wall one
    grid with holes behind the headboard, the map and the door (kit.wall)."""
    from .house import DOOR
    e, m = LINING, "plaster_v"
    hz0, hz1 = BED_Z - HEADBOARD["w"] / 2, BED_Z + HEADBOARD["w"] / 2
    hy0, hy1 = HEADBOARD["y"]
    # the headboard's wall (facing -x)
    mz0, mz1 = BED_Z - MAP["w"] / 2 - MAP["fr"], BED_Z + MAP["w"] / 2 + MAP["fr"]
    my0, my1 = MAP["y"] - MAP["h"] / 2 - MAP["fr"], MAP["y"] + MAP["h"] / 2 + MAP["fr"]
    cz0, cz1 = CONSOLE["z"]
    wall(k, m, (XE - e, F2, ZB), (0, 0, ZN - ZB), (0, H, 0), step=0.15,
         holes=[(hz0 - ZB, hz1 - ZB, hy0, hy1), (mz0 - ZB, mz1 - ZB, my0, my1), (cz0 - ZB, cz1 - ZB, 0.0, CONSOLE["h"])])
    # the lounge wall (facing -z), round its door
    d0, d1 = LOUNGE_DOOR
    wall(k, m, (XE, F2, ZN - e), (XW - XE, 0, 0), (0, H, 0), step=0.15, holes=[(XE - d1, XE - d0, 0.0, DOOR)])
    # the west wall's solid stretches either side of its window (facing +x)
    for z0, z1 in ((ZB, SIDE_GLASS[0]), (SIDE_GLASS[1], ZN)):
        panel(k, m, (XW + e, F2, z1), (0, 0, z0 - z1), (0, H, 0), step=0.15)
    # the back wall either side of the glass (facing +z)
    for x0, x1 in ((XW, BACK_GLASS[0]), (BACK_GLASS[1], XE)):
        panel(k, m, (x0, F2, ZB + e), (x1 - x0, 0, 0), (0, H, 0), step=0.15)


def ceiling(k):
    """The house's oak ceiling again, laid just under it and lit per vertex (as in the
    library), with its own downlight fittings. It lifts off with the roof."""
    from .house import downlight_spots
    y = RY - 0.014
    k.grain("bedroom_ceiling", Frame((0.0, 0.0, 0.0)), (XW, y - 0.012, ZB), (XE, y, ZN), step=0.3,
            skip=("+y", "+x", "-x", "+z", "-z"), along="z")
    s = 0.07
    for px, pz in downlight_spots(ROOM):
        k.b.quad("roof", "light_warm", [(px - s, y - 0.014, pz - s), (px + s, y - 0.014, pz - s),
                                        (px + s, y - 0.014, pz + s), (px - s, y - 0.014, pz + s)])


def rug(k):
    """A thick, pale wool rug under the lower part of the bed, oatmeal with a soft
    stripe in the weave and a darker band round its edge. Painted per vertex."""
    (x0, x1), (z0, z1), t = RUG["x"], RUG["z"], RUG["t"]
    rng = np.random.default_rng(44)
    step = 0.04
    nx, nz = round((x1 - x0) / step), round((z1 - z0) / step)
    mottle = _smooth_noise((nx + 1, nz + 1), 7, rng)
    field, band = np.array([0.80, 0.76, 0.69]), np.array([0.62, 0.57, 0.50])
    verts, colors = [], []
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = x0 + (x1 - x0) * i / nx, z0 + (z1 - z0) * j / nz
            verts.append((x, F2 + t, z))
            d = min(x - x0, x1 - x, z - z0, z1 - z)
            c = band if 0.10 < d < 0.18 else field * (1 + 0.035 * math.sin(x * 52.0) + 0.04 * mottle[i, j])
            colors.append(srgb_to_linear(tuple(np.clip(c, 0, 1))))
    faces = [(i * (nz + 1) + j, i * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j)
             for i in range(nx) for j in range(nz)]
    k.b.mesh(G, "bedroom_albedo", verts, faces, smooth=False, colors=colors)
    edge = srgb_to_linear(tuple(field * 0.85))
    for a, c in (((x1, z0), (x0, z0)), ((x0, z0), (x0, z1)), ((x0, z1), (x1, z1)), ((x1, z1), (x1, z0))):
        k.b.mesh(G, "bedroom_albedo", [(a[0], F2, a[1]), (c[0], F2, c[1]), (c[0], F2 + t, c[1]), (a[0], F2 + t, a[1])],
                 [(0, 1, 2, 3)], colors=[edge] * 4)


# ---- the bed ------------------------------------------------------------------------------------
def bed_frame():
    """The bed's frame: origin on the headboard wall's lining at the bed's middle, +z
    out toward the foot, +x to the right as you face the headboard (toward the lounge)."""
    return Frame((XE - LINING, F2, BED_Z), -90.0)


def fine(k, mat, f, centre, size, r, div=8, tilt=0.0, pivot=(0, 0, 0), turn=0.0, shape=None):
    """A rounded box with its flat sides divided (kit.cushion), optionally bent by
    `shape`, turned `turn` degrees about its vertical and tipped `tilt` about x."""
    verts, faces = cushion(size, r, n=3, div=div)
    if shape:
        verts = [shape(*v) for v in verts]
    T, R = rot(x=tilt), rot(y=turn)
    c, pv = np.asarray(centre, float), np.asarray(pivot, float)
    k.b.mesh(G, mat, [f(pv + T @ (c + R @ np.asarray(v, float) - pv)) for v in verts], faces)


def puffy(w, h, d, axis=2, keep=0.45):
    """Bend a box of size (w, h, d) into a pillow: thinnest at its edges along `axis`."""
    size = (w, h, d)
    a, b = [i for i in range(3) if i != axis]

    def shape(*v):
        v = list(v)
        s = (1 - (2 * v[a] / size[a]) ** 2) * (1 - (2 * v[b] / size[b]) ** 2)
        v[axis] *= keep + (1 - keep) * max(0.0, s) ** 0.6
        return tuple(v)
    return shape


def headboard(k, f):
    """A wide headboard in oatmeal linen, seven padded vertical channels from the
    nightstand to the floor lamp, on a slim oak rail."""
    w, (y0, y1), d, n = HEADBOARD["w"], HEADBOARD["y"], HEADBOARD["d"], HEADBOARD["n"]
    cw = w / n
    for i in range(n):
        x = -w / 2 + cw * (i + 0.5)
        fine(k, "bedroom_headboard", f, (x, (y0 + y1) / 2, d / 2), (cw - 0.006, y1 - y0, d), 0.035, div=8,
             shape=lambda vx, vy, vz, cw=cw: (vx, vy, vz + (0.012 * (1 - (2 * vx / cw) ** 2) if vz > 0 else 0.0)))
    k.grain("bedroom_oak", f, (-w / 2, y0 - 0.035, 0.0), (w / 2, y0, d + 0.01), step=0.08, skip=("-z",), along="x")


def drape(width, v0, v1, top, th, r, drop, rng, foot=True, step=0.04, amp=0.012, wrinkle=0.006):
    """A cloth laid over a box (the duvet over the mattress, the throw over the duvet): a
    grid in the cloth's own flat layout, laid on the top between v0 and v1 across `width`,
    rounding over the edges with radius r and hanging `drop` metres down the sides (and the
    foot, at v1, if `foot`), with soft folds where it hangs. Returns points and faces in
    the bed's frame (x across, y up, z along)."""
    hw = width / 2
    arc = r * math.pi / 2
    reach = arc + drop
    us = np.arange(-hw - reach, hw + reach + 1e-9, step)
    vs = np.arange(v0, v1 + (reach if foot else 0.0) + 1e-9, step)
    noise = _smooth_noise((len(us), len(vs)), 5, rng)
    ph = rng.uniform(0, 2 * math.pi, 3)
    verts = []
    for i, u in enumerate(us):
        for j, v in enumerate(vs):
            ex = max(abs(u) - hw, 0.0)
            ez = max(v - v1, 0.0) if foot else 0.0
            d = math.hypot(ex, ez)
            eu = math.copysign(min(abs(u), hw), u)
            ev = min(v, v1)
            y = top + th + wrinkle * noise[i, j] * (1 if d < 1e-9 else 0.4)
            if d < 1e-9:
                verts.append((u, y, v))
                continue
            du, dv = math.copysign(ex, u) / d, ez / d
            if d < arc:
                a = d / r
                h, y = r * math.sin(a), top + th - r * (1 - math.cos(a))
            else:
                h, y = r, top + th - r - (d - arc)
            # folds where it hangs, growing toward the hem
            hang = min(1.0, max(0.0, (d - arc) / max(drop, 1e-6)))
            along = v if ex > ez else u
            h += amp * hang * (0.6 * math.sin(2 * math.pi * along / 0.31 + ph[0]) + 0.4 * math.sin(2 * math.pi * along / 0.17 + ph[1]))
            verts.append((eu + du * h, y, ev + dv * h))
    nv = len(vs)
    faces = [(i * nv + j, i * nv + j + 1, (i + 1) * nv + j + 1, (i + 1) * nv + j) for i in range(len(us) - 1) for j in range(nv - 1)]
    return verts, faces


def _up_faces(verts, faces, f, centre):
    """Turn the cloth's faces to face away from the inside of the bed."""
    c0 = np.asarray(centre, float)
    out = []
    for q in faces:
        p = [np.asarray(verts[i], float) for i in q]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        m = sum(p) / 4
        out.append(q if np.dot(n, m - c0) >= 0 else q[::-1])
    return out


def bed(k, f):
    """A low platform bed in pale oak on a black recessed plinth; a mattress in a white
    sheet; a white linen duvet turned back at the top, falling over the sides and the
    foot in soft folds; two big pillows against the headboard, two in front, a small
    terracotta cushion, and a terracotta throw across the foot."""
    rng = np.random.default_rng(12)
    fw, (fz0, fz1), (fy0, fy1) = FRAME["w"], FRAME["z"], FRAME["y"]
    k.block("bedroom_black", f, (-fw / 2 + 0.07, 0.0, fz0 + 0.07), (fw / 2 - 0.07, fy0, fz1 - 0.07), step=0.3, skip=("-y", "+y"))
    k.grain("bedroom_oak", f, (-fw / 2, fy0, fz0), (fw / 2, fy1, fz1), step=0.08, along="z", skip=("-y",))
    mw, ml, mh, mz, my = MATTRESS["w"], MATTRESS["l"], MATTRESS["h"], MATTRESS["z"], MATTRESS["y"]
    top = my + mh
    fine(k, "bed_sheet", f, (0.0, my + mh / 2, mz + ml / 2), (mw, mh, ml), 0.05, div=10)
    centre = f((0.0, my + mh / 2, mz + ml / 2))

    def put(mat, verts, faces):
        world = [f(v) for v in verts]
        k.b.mesh(G, mat, world, _up_faces(world, faces, f, centre), smooth=True)
    # the duvet, and its top turned back over itself
    fold = mz + 0.62
    v, fc = drape(mw, fold, mz + ml, top, 0.045, 0.07, 0.27, rng)
    put("bed_linen", v, fc)
    v, fc = drape(mw + 0.02, fold, fold + 0.34, top, 0.075, 0.085, 0.17, rng, foot=False, amp=0.008)
    put("bed_linen", v, fc)
    k.tube("bed_linen", f((-mw / 2 - 0.06, top + 0.05, fold + 0.012)), f((mw / 2 + 0.06, top + 0.05, fold + 0.012)), 0.03,
           segments=14, step=0.08)
    # the throw across the foot
    v, fc = drape(mw + 0.06, mz + ml - 0.62, mz + ml - 0.16, top, 0.10, 0.12, 0.20, rng, foot=False, amp=0.015, wrinkle=0.008)
    put("bed_throw", v, fc)
    # pillows: two big ones against the headboard, two in front, a small cushion
    for x, turn in ((-0.47, 3.0), (0.47, -4.0)):
        fine(k, "bed_pillow", f, (x, top + 0.29, mz + 0.10), (0.70, 0.56, 0.17), 0.06, div=8, tilt=-10,
             pivot=(x, top, mz + 0.10), turn=turn, shape=puffy(0.70, 0.56, 0.17, axis=2))
    for x, turn in ((-0.46, -3.0), (0.47, 5.0)):
        fine(k, "bed_linen", f, (x, top + 0.13, mz + 0.38), (0.70, 0.16, 0.48), 0.06, div=8, tilt=-28,
             pivot=(x, top + 0.04, mz + 0.38), turn=turn, shape=puffy(0.70, 0.16, 0.48, axis=1))
    fine(k, "bed_accent", f, (0.05, top + 0.18, mz + 0.62), (0.48, 0.28, 0.13), 0.05, div=6, tilt=-22,
         pivot=(0.05, top + 0.05, mz + 0.62), turn=2.0, shape=puffy(0.48, 0.28, 0.13, axis=2, keep=0.5))


def nightstand(k, f):
    """A pale oak nightstand with one drawer, in front of the headboard on the lounge
    side: a ceramic lamp with a linen shade, two books and a glass of water."""
    x0, w, d, h = STAND["x"], STAND["w"], STAND["d"], STAND["h"]
    g = Frame(f((x0, 0.0, HEADBOARD["d"] + 0.01)), f.yaw)
    k.block("bedroom_black", g, (-w / 2 + 0.03, 0.0, 0.02), (w / 2 - 0.03, 0.06, d - 0.04), step=0.3, skip=("-y", "+y"))
    k.grain("bedroom_oak", g, (-w / 2, 0.06, 0.0), (w / 2, h, d), step=0.07, skip=("-y",), along="x")
    k.block("bedroom_black", g, (-w / 2 + 0.02, h - 0.105, d), (w / 2 - 0.02, h - 0.10, d + 0.0008), step=0.3, skip=("-z",))
    k.block("bedroom_black", g, (-0.08, h - 0.075, d), (0.08, h - 0.067, d + 0.0008), step=0.3, skip=("-z",))
    # the lamp: a round ceramic base and a drum shade, glowing
    lf = Frame(g((0.10, h, d * 0.42)))
    k.lathe("bed_ceramic", lf, [(0.0, 0.0), (0.06, 0.0), (0.10, 0.04), (0.115, 0.11), (0.10, 0.18), (0.05, 0.24),
                                (0.02, 0.27), (0.02, 0.30), (0.0, 0.30)], 40)
    k.tube("bedroom_brass", lf((0.0, 0.30, 0.0)), lf((0.0, 0.40, 0.0)), 0.006, segments=8)
    y0, y1, r = 0.31, 0.49, 0.16
    k.lathe("bed_shade", lf, [(r, y0), (r * 0.94, y1)], 48)
    k.lathe("bed_shade", lf, [(r * 0.94 - 0.004, y1), (r - 0.004, y0)], 48)
    k.disc("light_warm", lf, (0.0, y0 + 0.05, 0.0), r - 0.03, 32, down=True)
    p = lf((0.0, 0.0, 0.0))
    LAMPS.append(dict(name="bedside_down", pos=(p[0], p[1] + y0 + 0.03, p[2]), size=(0.24, 0.24), watts=20.0, aim=(0.0, -1.0, 0.0)))
    LAMPS.append(dict(name="bedside_up", pos=(p[0], p[1] + y1 - 0.03, p[2]), size=(0.24, 0.24), watts=10.0, aim=(0.0, 1.0, 0.0)))
    LAMPS.append(dict(name="bedside_glow", kind="point", pos=(p[0], p[1] + (y0 + y1) / 2, p[2]), watts=5.0, radius=0.10))
    # two books, and a glass of water
    bf = Frame(g((-0.12, h, d * 0.55)), f.yaw + 8)
    book_flat(k, bf, (0.0, 0.0), (0.22, 0.028, 0.15), "book_olive")
    book_flat(k, Frame(bf((0.0, 0.028, 0.0)), f.yaw - 4), (0.0, 0.0), (0.20, 0.022, 0.14), "book_cream")
    gl = Frame(g((-0.17, h, d * 0.20)))
    k.lathe("bed_glass", gl, [(0.0, 0.0), (0.032, 0.0), (0.034, 0.11), (0.031, 0.11), (0.029, 0.006), (0.0, 0.006)], 24)
    k.disc("bed_water", gl, (0.0, 0.075, 0.0), 0.030, 20)


def floor_lamp(k, f):
    """A slim brass floor lamp with a linen drum shade, on the other side of the bed."""
    x, z = FLOOR_LAMP
    lf = Frame(f((x, 0.0, z)))
    p = lf((0.0, 0.0, 0.0))
    k.lathe("bedroom_black", lf, [(0.0, 0.0), (0.15, 0.0), (0.15, 0.012), (0.13, 0.024), (0.02, 0.03), (0.0, 0.03)], 40)
    k.tube("bedroom_brass", lf((0.0, 0.025, 0.0)), lf((0.0, 1.40, 0.0)), 0.009, segments=10)
    y0, y1, r = 1.22, 1.52, 0.21
    k.lathe("bed_shade", lf, [(r, y0), (r, y1)], 48)
    k.lathe("bed_shade", lf, [(r - 0.004, y1), (r - 0.004, y0)], 48)
    k.disc("light_warm", lf, (0.0, y0 + 0.06, 0.0), r - 0.03, 32, down=True)
    for a in range(3):
        ang = 2 * math.pi * a / 3
        k.tube("bedroom_brass", lf((0.0, 1.40, 0.0)), lf(((r - 0.005) * math.cos(ang), y1 - 0.01, (r - 0.005) * math.sin(ang))),
               0.003, segments=6)
    LAMPS.append(dict(name="bedroom_lamp_down", pos=(p[0], p[1] + y0 + 0.04, p[2]), size=(0.3, 0.3), watts=26.0, aim=(0.0, -1.0, 0.0)))
    LAMPS.append(dict(name="bedroom_lamp_up", pos=(p[0], p[1] + y1 - 0.04, p[2]), size=(0.3, 0.3), watts=14.0, aim=(0.0, 1.0, 0.0)))
    LAMPS.append(dict(name="bedroom_lamp_glow", kind="point", pos=(p[0], p[1] + (y0 + y1) / 2, p[2]), watts=5.0, radius=0.12))


# ---- the map and the shelf ----------------------------------------------------------------------
def shelf_frame():
    """The lounge wall's frame for the shelf: origin on the wall's lining at SHELF_X, +z
    out into the room, +x to the right as you face the wall."""
    return Frame((SHELF_X, F2, ZN - LINING), 180.0)


def map_point(lat, lon):
    """Where a place falls on the map, as a fraction across (0 at 180° W) and up."""
    return (lon + 180.0) / 360.0, (lat - LAT[0]) / (LAT[1] - LAT[0])


def world_map(k, f):
    """The world map in a slim oak frame over the headboard, and red pins pushed into it
    (PINS)."""
    w, h, yc, fr = MAP["w"], MAP["h"], MAP["y"], MAP["fr"]
    x0, x1, y0, y1 = -w / 2 - fr, w / 2 + fr, yc - h / 2 - fr, yc + h / 2 + fr
    d = 0.035
    for lo, hi in (((x0, y0, 0.004), (x0 + fr, y1, d)), ((x1 - fr, y0, 0.004), (x1, y1, d)),
                   ((x0 + fr, y0, 0.004), (x1 - fr, y0 + fr, d)), ((x0 + fr, y1 - fr, 0.004), (x1 - fr, y1, d))):
        k.grain("bedroom_oak", f, lo, hi, step=0.06, skip=("-z",))
    zm = 0.014
    v, fc, uv = grid((-w / 2, yc - h / 2, zm), (w, 0, 0), (0, h, 0), 40, 16)
    k.mesh("bedroom_map", f, v, fc, smooth=False, uvs=uv)
    for name, lat, lon in PINS:
        u, t = map_point(lat, lon)
        px, py = -w / 2 + u * w, yc - h / 2 + t * h
        r = 0.0095
        k.tube("aluminium", f((px, py, zm - 0.004)), f((px, py, zm + 0.014)), 0.0009, segments=5, step=0.01)
        k.lathe("bed_pin", Frame(f((px, py, zm + 0.014 + r * 0.8))),
                [(0.0, -r)] + [(r * math.sin(math.pi * s), -r * math.cos(math.pi * s)) for s in np.linspace(0.12, 0.88, 7)] +
                [(0.0, r)], 16)
    spot = f((0.0, H - 0.06, 1.30))
    aim = f((0.0, yc - 0.15, 0.0))
    LAMPS.append(dict(name="map_spot", kind="spot", pos=spot, aim=tuple(np.subtract(aim, spot)), watts=34.0, cone=48.0))


def shelf(k, titled, cells):
    """A floating oak shelf over the reading chair: the titled books (data/bedroom_books.txt)
    between brass bookends, a few plain ones, one lying flat, and a small vase."""
    f = shelf_frame()
    w, d, t, y = SHELF["w"], SHELF["d"], SHELF["t"], SHELF["y"]
    k.grain("bedroom_oak", f, (-w / 2, y - t, 0.0), (w / 2, y, d), step=0.06, skip=("-z",), along="x")
    # the titled books, standing, spines out
    x = -0.30
    k.soft("bedroom_brass", f, (x - 0.006, y + 0.075, d * 0.5), (0.005, 0.15, 0.11), 0.002, n=1)
    k.soft("bedroom_brass", f, (x + 0.04, y + 0.003, d * 0.5), (0.09, 0.005, 0.11), 0.002, n=1)
    bh, bd = 0.235, 0.165
    for bk, cell in zip(titled, cells):
        bt = bk["thick"]
        book(k, f, x, y, bt, bh, bd, bk["colour"], cell)
        x += bt + 0.0015
    # three plain ones, and a brass bookend
    for colour, bt, hh in (("book_cream", 0.026, 0.215), ("book_charcoal", 0.032, 0.225), ("book_olive", 0.024, 0.205)):
        book_upright(k, Frame(f((x + bt / 2, y, d - 0.02 - bd / 2)), f.yaw), (bt, hh, bd), colour)
        x += bt + 0.0015
    k.soft("bedroom_brass", f, (x + 0.004, y + 0.075, d * 0.5), (0.005, 0.15, 0.11), 0.002, n=1)
    # one lying flat at the far end with a small vase on it, and a vase at the other end
    g = Frame(f((0.42, y, d * 0.5)), f.yaw + 6)
    book_flat(k, g, (0.0, 0.0), (0.24, 0.03, 0.17), "book_navy")
    k.lathe("bed_ceramic", Frame(g((0.0, 0.03, 0.0))), [(0.0, 0.0), (0.035, 0.0), (0.05, 0.04), (0.045, 0.08), (0.02, 0.12),
                                                       (0.016, 0.14), (0.02, 0.15), (0.0, 0.148)], 28)
    k.lathe("bedroom_black", Frame(f((-0.52, y, d * 0.5))), [(0.0, 0.0), (0.04, 0.0), (0.06, 0.05), (0.055, 0.13), (0.03, 0.18),
                                                            (0.026, 0.20), (0.0, 0.198)], 28)


def book(k, f, x, y, t, h, d, colour, cell):
    """A book standing on the shelf at x (its left side), spine facing out, its cover in
    `colour` (painted per vertex) and its spine on the spine picture."""
    zs = SHELF["d"] - 0.02
    zb = zs - d
    lin = srgb_to_linear(colour)
    pages = srgb_to_linear((0.90, 0.87, 0.80))
    verts, faces, colors = [], [], []

    def quad(pts, c):
        base = len(verts)
        verts.extend(f(p) for p in pts)
        colors.extend([c] * 4)
        faces.append((base, base + 1, base + 2, base + 3))
    quad([(x, y + h, zs), (x + t, y + h, zs), (x + t, y + h, zb), (x, y + h, zb)], pages)
    quad([(x, y, zb), (x, y, zs), (x, y + h, zs), (x, y + h, zb)], lin)
    quad([(x + t, y, zs), (x + t, y, zb), (x + t, y + h, zb), (x + t, y + h, zs)], lin)
    k.b.mesh(G, "bedroom_albedo", verts, faces, smooth=False, colors=colors)
    u0, v0, u1, v1 = cell
    n = 4
    sv, sf, suv = [], [], []
    for j in range(n + 1):
        yy = y + h * j / n
        sv += [f((x, yy, zs)), f((x + t, yy, zs))]
    for j in range(n):
        a = 2 * j
        sf.append((a, a + 1, a + 3, a + 2))
        suv.append([(u0, v0 + (v1 - v0) * j / n), (u1, v0 + (v1 - v0) * j / n), (u1, v0 + (v1 - v0) * (j + 1) / n),
                    (u0, v0 + (v1 - v0) * (j + 1) / n)])
    k.b.mesh(G, "bedroom_spines", sv, sf, smooth=False, uvs=suv)


# ---- pictures ------------------------------------------------------------------------------------
SPINE_PX = 1400                   # pixels per metre on the spine picture


def paint_spines(books, h=0.235):
    """The titled spines side by side in one picture, each its book's colour with the
    title in plain capitals reading top to bottom. Sets each book's thickness; returns
    each spine's (u0, v0, u1, v1)."""
    from .labels import text_mask
    rng = np.random.default_rng(3)
    for i, bk in enumerate(books):
        bk["thick"] = 0.034 + 0.004 * (i % 2)
    L = int(round(h * SPINE_PX))
    widths = [int(round(bk["thick"] * SPINE_PX)) for bk in books]
    W = int(math.ceil((sum(widths) + 4 * len(books)) / 4) * 4)
    Hh = int(math.ceil(L / 4) * 4)
    img = np.zeros((Hh, W, 3))
    # set the titles lying down, one band per book, then stand each band up
    bands_h = sum(wd + 4 for wd in widths)
    lines, y = [], 0
    for bk, wd in zip(books, widths):
        em = 0.42 * wd
        lines.append((bk["title"].upper(), 0.5, (y + (wd - 0.70 * em) / 2) / bands_h, em / bands_h, "CENTER", 1.25))
        y += wd + 4
    mask = text_mask((L, bands_h), lines)
    cells, x, y = [], 0, 0
    for bk, wd in zip(books, widths):
        band = mask[y:y + wd, :L]
        strip_mask = band.T[::-1, :]
        ground = np.array(bk["colour"]) * (1 + 0.03 * rng.standard_normal((L, wd)))[..., None]
        ground = ground * (1 - 0.10 * np.exp(-np.minimum(np.arange(wd), wd - 1 - np.arange(wd)) / 2.0))[None, :, None]
        lum = 0.2126 * bk["colour"][0] + 0.7152 * bk["colour"][1] + 0.0722 * bk["colour"][2]
        ink = np.array((0.08, 0.08, 0.09) if lum > 0.45 else (0.95, 0.94, 0.90))
        strip = ground * (1 - strip_mask[..., None]) + ink * strip_mask[..., None]
        img[0:L, x:x + wd] = strip
        cells.append(((x + 0.5) / W, 0.5 / Hh, (x + wd - 0.5) / W, (L - 0.5) / Hh))
        x += wd + 4
        y += wd + 4
    save_png(picture_path("bedroom_spines"), np.clip(img, 0, 1).astype(np.float32))
    return cells


def _fill(rings, w, h, to_px):
    """Rasterise polygons (even-odd, so holes stay holes): a (h, w) mask, bottom row first."""
    xs0, ys0, xs1, ys1 = [], [], [], []
    for ring in rings:
        pts = np.array([to_px(lon, lat) for lon, lat in ring])
        xs0.append(pts[:-1, 0])
        ys0.append(pts[:-1, 1])
        xs1.append(pts[1:, 0])
        ys1.append(pts[1:, 1])
    X0, Y0, X1, Y1 = (np.concatenate(a) for a in (xs0, ys0, xs1, ys1))
    mask = np.zeros((h, w), bool)
    for row in range(h):
        yc = row + 0.5
        hit = ((Y0 <= yc) & (Y1 > yc)) | ((Y1 <= yc) & (Y0 > yc))
        if not hit.any():
            continue
        xc = np.sort(X0[hit] + (yc - Y0[hit]) * (X1[hit] - X0[hit]) / (Y1[hit] - Y0[hit]))
        for a, b in zip(xc[0::2], xc[1::2]):
            i0, i1 = max(0, int(math.ceil(a - 0.5))), min(w - 1, int(math.floor(b - 0.5)))
            if i1 >= i0:
                mask[row, i0:i1 + 1] = True
    return mask


def paint_map(w=1024, ss=2):
    """An original world map print: Natural Earth's coastlines in a plain equirectangular
    projection (latitudes LAT), warm sand land with a darker coast on a pale blue-grey sea,
    a faint graticule every 30 degrees, on paper."""
    h = int(round(w * (LAT[1] - LAT[0]) / 360.0 / 4)) * 4
    path = C.SRC_GEO / C.WORLD_LAND["file"]
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing. Run blender/fetch_assets.py first.")
    land = json.loads(path.read_text(encoding="utf-8"))
    rings = []
    for feat in land["features"]:
        g = feat["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            rings += poly
    W, Hs = w * ss, h * ss

    def to_px(lon, lat):
        return (lon + 180.0) / 360.0 * W, (lat - LAT[0]) / (LAT[1] - LAT[0]) * Hs
    big = _fill(rings, W, Hs, to_px).astype(float)
    landm = big.reshape(h, ss, w, ss).mean(axis=(1, 3))
    # the coast: land pixels next to the sea
    pad = np.pad(big, 1, mode="edge")
    edge = big * (1 - np.minimum.reduce([pad[1:-1, :-2], pad[1:-1, 2:], pad[:-2, 1:-1], pad[2:, 1:-1]]))
    coast = edge.reshape(h, ss, w, ss).mean(axis=(1, 3))
    rng = np.random.default_rng(8)
    sea, ground, line = np.array([0.80, 0.85, 0.86]), np.array([0.83, 0.74, 0.58]), np.array([0.42, 0.36, 0.28])
    img = sea * (1 - landm[..., None]) + ground * landm[..., None]
    img *= (1 + 0.025 * _smooth_noise((h, w), 30, rng))[..., None]
    img = img * (1 - 0.9 * coast[..., None]) + line * 0.9 * coast[..., None]
    # the graticule
    for lon in range(-150, 180, 30):
        x = int(round((lon + 180.0) / 360.0 * w))
        img[:, x] = img[:, x] * 0.86
    for lat in range(-30, 90, 30):
        y = int(round((lat - LAT[0]) / (LAT[1] - LAT[0]) * h))
        if 0 <= y < h:
            img[y, :] = img[y, :] * (0.80 if lat == 0 else 0.86)
    img *= (1 + 0.012 * rng.standard_normal((h, w)))[..., None]
    save_png(picture_path("world_map"), np.clip(img, 0, 1).astype(np.float32))


# ---- the bench and the reading chair ------------------------------------------------------------
def bench(k, f):
    """A low bench at the foot of the bed: a pale oak frame and a linen cushion."""
    (z0, z1), w, h = BENCH["z"], BENCH["w"], BENCH["h"]
    t = 0.04
    for x in (-w / 2, w / 2 - t):
        k.grain("bedroom_oak", f, (x, 0.0, z0), (x + t, h - 0.07, z1), step=0.06, skip=("-y",), along="y")
    k.grain("bedroom_oak", f, (-w / 2, h - 0.10, z0), (w / 2, h - 0.07, z1), step=0.07, along="x")
    fine(k, "bedroom_headboard", f, (0.0, h - 0.035, (z0 + z1) / 2), (w - 0.02, 0.075, z1 - z0 - 0.01), 0.03, div=8,
         shape=lambda vx, vy, vz: (vx, vy + (0.006 * (1 - (2 * vx / w) ** 2) if vy > 0 else 0.0), vz))
    book_flat(k, Frame(f((0.42, h, (z0 + z1) / 2)), f.yaw + 12), (0.0, 0.0), (0.24, 0.03, 0.17), "book_rust")


def reading_chair(k):
    """A low lounge chair in off-white boucle under the shelf, on a pale oak frame with
    solid sides, a cushion for the small of the back, and a round side table with a book
    and a cup."""
    (x, z), yaw = CHAIR["pos"], CHAIR["yaw"]
    f = Frame((x, F2, z), yaw)
    W, D = 0.78, 0.80
    for sx in (-1, 1):
        a = sx * W / 2 - (0.05 if sx > 0 else 0.0)
        k.grain("bedroom_oak", f, (a, 0.0, -D / 2), (a + 0.05, 0.56, D / 2), step=0.06, along="z")
    k.grain("bedroom_oak", f, (-W / 2 + 0.05, 0.10, -D / 2), (W / 2 - 0.05, 0.14, D / 2), step=0.08, along="x", skip=("-y",))
    fine(k, "bedroom_chair", f, (0.0, 0.25, 0.03), (W - 0.11, 0.22, D - 0.08), 0.06, div=8,
         shape=lambda vx, vy, vz: (vx, vy - (0.012 * (1 - (2 * vx / W) ** 2) * (1 - (2 * vz / D) ** 2) if vy > 0 else 0.0), vz))
    fine(k, "bedroom_chair", f, (0.0, 0.62, -D / 2 + 0.12), (W - 0.11, 0.62, 0.18), 0.07, div=8, tilt=-14,
         pivot=(0.0, 0.36, -D / 2 + 0.12), shape=puffy(W - 0.11, 0.62, 0.18, axis=2, keep=0.6))
    fine(k, "bed_accent", f, (0.0, 0.52, -D / 2 + 0.28), (0.42, 0.26, 0.12), 0.05, div=6, tilt=-18,
         pivot=(0.0, 0.38, -D / 2 + 0.28), turn=-4.0, shape=puffy(0.42, 0.26, 0.12, axis=2, keep=0.5))
    tx, tz = SIDE_TABLE
    tf = Frame((tx, F2, tz))
    k.lathe("bedroom_black", tf, [(0.0, 0.0), (0.17, 0.0), (0.17, 0.012), (0.02, 0.02), (0.018, 0.48), (0.0, 0.48)], 32)
    k.lathe("bed_ceramic", tf, [(0.0, 0.48), (0.22, 0.48), (0.22, 0.51), (0.0, 0.51)], 48)
    book_flat(k, Frame(tf((-0.04, 0.51, 0.02)), 25.0), (0.0, 0.0), (0.20, 0.025, 0.14), "book_charcoal")
    c = Frame(tf((0.11, 0.51, -0.06)))
    k.lathe("bed_ceramic", c, [(0.0, 0.0), (0.033, 0.0), (0.04, 0.01), (0.042, 0.08), (0.039, 0.08), (0.036, 0.012), (0.0, 0.01)], 24)


# ---- the record player -------------------------------------------------------------------------
SLEEVES = [(0.62, 0.36, 0.24), (0.86, 0.82, 0.74), (0.20, 0.24, 0.30), (0.52, 0.55, 0.44), (0.12, 0.12, 0.13),
           (0.74, 0.60, 0.42), (0.34, 0.20, 0.18), (0.80, 0.77, 0.70), (0.42, 0.47, 0.52), (0.66, 0.50, 0.30),
           (0.18, 0.28, 0.24), (0.88, 0.86, 0.80), (0.48, 0.30, 0.22), (0.26, 0.26, 0.28)]


def record_console(k):
    """A low pale oak console against the games room wall beside the reading chair: a black
    recessed plinth, two doors on the left, an open bay of records standing on the right. On
    top, a record player (oak plinth, steel platter, a record on it with a terracotta label,
    a slim tonearm) at the chair's end, and a small stack of records lying flat beside it, in
    plain coloured sleeves. Returns the platter's middle (the hotspot anchor)."""
    from .kit import cushion
    z0, z1 = CONSOLE["z"]
    L, D, Hc = z1 - z0, CONSOLE["d"], CONSOLE["h"]
    f = Frame((XE - LINING, F2, (z0 + z1) / 2), -90.0)      # +z into the room, +x toward the chair (+z)
    x0, x1 = -L / 2, L / 2
    k.block("bedroom_black", f, (x0 + 0.04, 0.0, 0.0), (x1 - 0.04, 0.07, D - 0.04), step=0.3, skip=("-y", "-z", "+y"))
    k.grain("bedroom_oak", f, (x0, Hc - 0.028, 0.0), (x1, Hc, D), step=0.07, skip=("-z",), along="x")       # the top
    k.grain("bedroom_oak", f, (x0, 0.07, 0.0), (x1, 0.095, D), step=0.08, skip=("-z", "-y"), along="x")     # the bottom
    for xa in (x0, x1 - 0.025, -0.0125):                                                                    # ends, divider
        k.grain("bedroom_oak", f, (xa, 0.095, 0.0), (xa + 0.025, Hc - 0.028, D), step=0.07, skip=("-z", "-y", "+y"), along="y")
    # the left half's two doors, hairline gaps, a slim brass pull on each
    gap, w = 0.003, (L / 2 - 0.0375) / 2
    for i in range(2):
        a = x0 + 0.025 + i * w
        k.grain("bedroom_oak", f, (a + gap / 2, 0.095 + gap, D - 0.02), (a + w - gap / 2, Hc - 0.028 - gap, D),
                step=0.06, skip=("-z",), along="y")
        k.soft("bedroom_brass", f, (a + (w - 0.05 if i == 0 else 0.05), Hc - 0.15, D + 0.006), (0.010, 0.10, 0.012), 0.004, n=1)
    k.block("bedroom_black", f, (x0 + 0.025, 0.095, D - 0.03), (-0.0125, Hc - 0.028, D - 0.02), step=0.3, skip=("-z",))
    # the open bay: a dark back, and records standing in it
    k.block("bedroom_black", f, (0.0125, 0.095, 0.02), (x1 - 0.025, Hc - 0.028, 0.025), step=0.1, skip=("-z",))
    x = 0.03
    i = 0
    while x < x1 - 0.06:
        t = 0.0045
        lean = 0.0 if i < 34 else 7.0
        verts, faces = cushion((t, 0.315, 0.315), 0.0012, n=1, div=2)
        g = Frame(f((x + t / 2, 0.095 + 0.1575, 0.03 + 0.1575)), f.yaw)
        T = rot(z=-lean)
        c = srgb_to_linear(SLEEVES[i % len(SLEEVES)])
        k.b.mesh(k.g, "bedroom_albedo", [g(tuple(T @ np.array(v))) for v in verts], faces, colors=[c] * len(verts))
        x += t + 0.0012 + (0.014 if i == 33 else 0.0)
        i += 1
        if i > 38:
            break
    # the stack of records on top, lying flat, not quite square to each other
    top = Hc
    rng = np.random.default_rng(12)
    y = top
    for j, colour in enumerate((SLEEVES[0], SLEEVES[7], SLEEVES[4], SLEEVES[9], SLEEVES[2])):
        t = 0.005
        verts, faces = cushion((0.315, t, 0.315), 0.0012, n=1, div=2)
        g = Frame(f((-0.30 + rng.uniform(-0.008, 0.008), y + t / 2, D / 2 + rng.uniform(-0.008, 0.008))),
                  f.yaw + rng.uniform(-5, 5))
        c = srgb_to_linear(colour)
        k.b.mesh(k.g, "bedroom_albedo", [g(v) for v in verts], faces, colors=[c] * len(verts))
        y += t
    # the record player, at the chair's end
    tp = Frame(f((0.27, top, D / 2 - 0.005)), f.yaw)
    W, Dp, Hp = 0.44, 0.35, 0.075
    k.grain("bedroom_oak", tp, (-W / 2, 0.012, -Dp / 2), (W / 2, Hp, Dp / 2), step=0.05, along="x")
    for sx in (-1, 1):
        for sz in (-1, 1):
            k.lathe("bedroom_black", Frame(tp((sx * (W / 2 - 0.04), 0.0, sz * (Dp / 2 - 0.04)))),
                    [(0.0, 0.0), (0.022, 0.0), (0.024, 0.012), (0.0, 0.012)], 16)
    k.block("bedroom_black", tp, (-W / 2 + 0.008, Hp, -Dp / 2 + 0.008), (W / 2 - 0.008, Hp + 0.003, Dp / 2 - 0.008), step=0.05,
            skip=("-y",))
    pc = (-0.045, Hp + 0.003, 0.0)                             # the platter's middle
    k.lathe("bedroom_steel", Frame(tp(pc)), [(0.0, 0.0), (0.03, 0.0), (0.148, 0.004), (0.150, 0.010), (0.150, 0.018),
                                             (0.0, 0.018)], 64)
    k.lathe("bedroom_vinyl", Frame(tp((pc[0], pc[1] + 0.018, pc[2]))),
            [(0.0, 0.0), (0.1500, 0.0), (0.1500, 0.0022), (0.148, 0.0024), (0.0, 0.0024)], 72)
    k.lathe("bed_accent", Frame(tp((pc[0], pc[1] + 0.0205, pc[2]))), [(0.0, 0.0), (0.049, 0.0), (0.049, 0.0015), (0.0, 0.0015)], 40)
    k.tube("bedroom_steel", tp((pc[0], pc[1] + 0.02, pc[2])), tp((pc[0], pc[1] + 0.036, pc[2])), 0.0035, segments=8)
    # the tonearm: a post at the back right, the arm reaching in over the record's outer grooves
    pv = np.array((0.155, Hp + 0.003, -0.10))
    k.lathe("bedroom_steel", Frame(tp(tuple(pv))), [(0.0, 0.0), (0.03, 0.0), (0.03, 0.012), (0.012, 0.016), (0.012, 0.055),
                                                     (0.0, 0.055)], 24)
    head = np.array((pc[0] + 0.105, Hp + 0.003 + 0.032, pc[2] + 0.06))
    piv = pv + (0.0, 0.050, 0.0)
    k.sweep("bedroom_steel", [tp(tuple(piv)), tp(tuple(piv + (head - piv) * 0.55 + (0.006, 0.004, 0.0))), tp(tuple(head))],
            0.0042, segments=10)
    back = piv - (head - piv) / np.linalg.norm(head - piv) * 0.06
    k.tube("bedroom_steel", tp(tuple(piv)), tp(tuple(back)), 0.003, segments=8)
    k.tube("bedroom_black", tp(tuple(back)), tp(tuple(back - (head - piv) / np.linalg.norm(head - piv) * 0.028)), 0.014,
           segments=16)
    hs = Frame(tp(tuple(head)), f.yaw + 35.0)
    k.soft("bedroom_black", hs, (0.0, -0.004, 0.012), (0.018, 0.006, 0.040), 0.002, n=1)
    k.lathe("bedroom_steel", Frame(tp((0.175, Hp + 0.003, 0.07))), [(0.0, 0.0), (0.006, 0.0), (0.006, 0.042), (0.0, 0.042)], 12)
    for dx in (-0.19, -0.155):                                   # speed and start knobs at the front left
        k.lathe("bedroom_steel", Frame(tp((dx, Hp + 0.003, Dp / 2 - 0.035))),
                [(0.0, 0.0), (0.011, 0.0), (0.011, 0.012), (0.0, 0.012)], 16)
    return tp((pc[0], pc[1] + 0.025, pc[2]))
