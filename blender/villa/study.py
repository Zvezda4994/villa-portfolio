"""The study (VAREK Systems), furnished: a student founder's study, not an
executive office. Warm, late evening.

Plan, looking down, seen from the driveway (the front glass at the top, so +x
is on the right):

        front glass, onto the reflecting pool                 (z = 7.85)
     +----------------------------------------------------+
   b |                 [====== desk ======]               |
   l |                        (o) chair            [cred- |
   a |  foyer door                                  enza] |
   d |                                                    |
   e |                                         gym door   |
     | [white-     [=========== Persian rug ==========]   |
   w |  board]        [glass table]    [ sofa, facing  ]  |
   a |                                 [ the board     ] (lamp)
   l |                                                    |
   l +----------------------------------------------------+
            back wall, door to the living room            (z = 0)

A Persian rug, a clean desk by the glass with an elegant brass lamp and an open
journal, a whiteboard on the dark stone wall with the call flow drawn on it by
hand, and a deep sofa facing the board across a glass coffee table. A low oak
credenza by the desk holds a few books and a succulent.

How it is lit: the rug, the desk and credenza tops and the whiteboard are big
flat surfaces on the room's own lightmap ("stu"); the sofa, chair, lamps and
small things are lit per vertex. The ceiling light is turned well down and the
desk lamp, a floor lamp and a picture light over the board do the rest.
"""
import math
import random

import numpy as np

from . import config as C
from .house import H1, P
from .kit import Frame, Kit, arc, rot
from .props import load, place
from .textures import picture_path, save_png

ROOM, G, ATLAS = "study", "ground", "stu"

# The room's inside faces.
X0 = C.BLADE_X[1]               # the dark stone wall (1.5)
X1 = 6.0 - P / 2                # the wall to the gym (5.925)
Z0 = P / 2                      # the wall to the living room (0.075)
GLASS_Z = C.HALF_D - C.WALL / 2 - 0.06    # just inside the glazing's frame

# The lounge: the whiteboard on the stone wall, the sofa facing it across the table.
LOUNGE_Z = 2.10
BOARD = dict(w=2.6, h=1.35, bottom=0.86, standoff=0.030)
SHELF_Z = (0.13, 0.67)          # a slim bookshelf on the stone wall, left of the board as you face it
PLANT = (1.88, 3.98)            # a tall fig in a dark pot on the other side
RUG_X, RUG_Z = (2.0, 5.0), (LOUNGE_Z - 1.2, LOUNGE_Z + 1.2)
RUG_T = 0.012
TABLE_X, TABLE_Z, TABLE_TOP = (2.72, 3.37), (LOUNGE_Z - 0.55, LOUNGE_Z + 0.55), 0.38
SOFA = dict(back_x=4.86, length=2.3, depth=0.95)
FLOOR_LAMP = (4.42, 0.36)

# The desk by the glass, and the credenza along the gym wall beside it.
DESK = dict(cx=3.70, z1=GLASS_Z - 0.34, w=1.6, d=0.72, top=0.75, t=0.032)
CREDENZA = dict(z=(4.90, 7.10), depth=0.42, h=0.58)

CEILING_LIGHT = 0.3

# Lamps for the bake (lighting.py adds them), filled in while building.
LAMPS = []

# Review cameras (lighting.PREVIEW_CAMERAS). The first is also the room's view on the
# website: from behind the sofa, looking over it at the whiteboard.
STUDY_CAM = dict(pos=(5.82, 1.55, 3.30), target=(1.50, 1.10, 2.08), fov=55.0)
DESK_CAM = dict(pos=(4.55, 1.38, 5.35), target=(3.62, 0.82, 7.15), fov=50.0)


def build_study(b):
    LAMPS.clear()
    paint_pictures()
    k = Kit(b, G, ATLAS)
    with b.room(ROOM):
        rug(b)
        whiteboard(k)
        bookshelf(k)
        tall_plant(k)
        coffee_table(k)
        sofa(k)
        floor_lamp(k)
        desk(k)
        desk_lamp(k)
        journal(k)
        cup(k)
        task_chair(k, Frame((DESK["cx"] - 0.05, RUG_T * 0, DESK["z1"] - DESK["d"] - 0.30), 8.0),
                   seat="chair_leather", shell="chair_shell", metal="aluminium")
        credenza(k)


# ---- the lounge -------------------------------------------------------------------------
def rug(b):
    full = [(0, 0), (1, 0), (1, 1), (0, 1)]
    b.box(G, "persian_rug", RUG_X, (0.0, RUG_T), RUG_Z, atlas=ATLAS, skip=("-y",), solid=False,
          over={"+y": dict(uv=full, density=0.9)})
    # fringes: the warp threads knotted off at both short ends, lying a little untidily
    rng = random.Random(12)
    verts, faces = [], []
    for side, x in ((-1, RUG_X[0]), (1, RUG_X[1])):
        z = RUG_Z[0] + 0.012
        while z < RUG_Z[1] - 0.012:
            length = rng.uniform(0.055, 0.075)
            a = rng.uniform(-0.25, 0.25)
            dx, dz = side * length * math.cos(a), length * math.sin(a)
            wd = 0.0035
            y = 0.003
            i = len(verts)
            verts += [(x, y, z - wd), (x, y, z + wd), (x + dx, y, z + dz + wd), (x + dx, y, z + dz - wd)]
            faces.append((i, i + 1, i + 2, i + 3) if side < 0 else (i, i + 3, i + 2, i + 1))
            z += rng.uniform(0.008, 0.012)
    b.mesh(G, "fringe", verts, faces, smooth=False)


def whiteboard(k):
    """A big whiteboard on the dark stone wall, framed in aluminium, with a tray of
    markers and an eraser, and a slim brass picture light over it."""
    w, h, y0 = BOARD["w"], BOARD["h"], BOARD["bottom"]
    f = Frame((X0, 0.0, LOUNGE_Z), 90.0)          # local +z out of the wall, +x to the viewer's right
    s = BOARD["standoff"]
    # The board's face is lit per vertex on a fine grid, not by the lightmap: the light
    # from the picture lamp falls off smoothly, and even a quick draft bake stays clean.
    k.box("aluminium", f, (-w / 2, y0, s - 0.016), (w / 2, y0 + h, s - 0.001), skip=("-z", "+z"))
    nx, ny = 22, 12
    verts = [(-w / 2 + w * i / nx, y0 + h * j / ny, s) for i in range(nx + 1) for j in range(ny + 1)]
    faces, uvs = [], []
    for i in range(nx):
        for j in range(ny):
            a, c = i * (ny + 1) + j, (i + 1) * (ny + 1) + j
            faces.append((a, c, c + 1, a + 1))
            uvs.append([(i / nx, j / ny), ((i + 1) / nx, j / ny), ((i + 1) / nx, (j + 1) / ny), (i / nx, (j + 1) / ny)])
    k.mesh("whiteboard", f, verts, faces, smooth=True, uvs=uvs)
    # the aluminium frame round it
    e, d = 0.022, 0.022
    for lo, hi in (((-w / 2 - e, y0 - e, s - 0.02), (w / 2 + e, y0, s + 0.006)),
                   ((-w / 2 - e, y0 + h, s - 0.02), (w / 2 + e, y0 + h + e, s + 0.006)),
                   ((-w / 2 - e, y0, s - 0.02), (-w / 2, y0 + h, s + 0.006)),
                   ((w / 2, y0, s - 0.02), (w / 2 + e, y0 + h, s + 0.006))):
        k.soft("aluminium", f, tuple((np.add(lo, hi)) / 2), tuple(np.subtract(hi, lo)), 0.004, n=1)
    # the tray along the bottom, and what's in it
    ty = y0 - e
    k.soft("aluminium", f, (0, ty - 0.012, s + 0.035), (w * 0.62, 0.006, 0.07), 0.002, n=1)
    k.soft("aluminium", f, (0, ty - 0.003, s + 0.068), (w * 0.62, 0.022, 0.006), 0.002, n=1)
    rng = random.Random(8)
    for i, (x, cap) in enumerate(((-0.42, "marker_black"), (-0.30, "marker_blue"), (0.16, "marker_black"))):
        a = math.radians(rng.uniform(-6, 6))
        half = 0.068
        p0 = f((x - half * math.cos(a), ty + 0.0, s + 0.035 - half * math.sin(a)))
        p1 = f((x + half * math.cos(a), ty + 0.0, s + 0.035 + half * math.sin(a)))
        p0 = (p0[0], p0[1] + 0.0, p0[2])
        mid = tuple(np.add(p0, np.subtract(p1, p0) * 0.72))
        k.tube("marker_body", p0, mid, 0.0085, segments=10)
        k.tube(cap, mid, p1, 0.0095, segments=10)
    # the eraser, felt down
    k.soft("eraser_felt", f, (0.42, ty - 0.004, s + 0.035), (0.15, 0.014, 0.05), 0.004, n=1, turn=4)
    k.soft("marker_black", f, (0.42, ty + 0.014, s + 0.035), (0.146, 0.022, 0.046), 0.008, n=2, turn=4)
    # the picture light: a brass bar on two short arms, glowing along its underside
    ly, out = y0 + h + 0.17, 0.20
    for x in (-0.55, 0.55):
        k.tube("brass", f((x, ly + 0.02, 0.004)), f((x, ly + 0.02, out - 0.02)), 0.006, segments=8)
        k.soft("brass", f, (x, ly + 0.02, 0.006), (0.05, 0.05, 0.012), 0.004, n=1)
    k.tube("brass", f((-0.75, ly, out)), f((0.75, ly, out)), 0.022, segments=16)
    k.quad("light_warm", f, [(-0.73, ly - 0.0225, out - 0.008), (0.73, ly - 0.0225, out - 0.008),
                             (0.73, ly - 0.0225, out + 0.008), (-0.73, ly - 0.0225, out + 0.008)])
    LAMPS.append(dict(name="board_light", pos=f((0.0, ly - 0.03, out)), size=(1.4, 0.06), watts=32.0,
                      aim=tuple(np.subtract(f((0, y0 + h * 0.4, 0)), f((0, ly, out))))))


def bookshelf(k):
    """A slim open bookshelf in smoked oak against the stone wall: five shelves of
    books, a few lying flat, and a couple of objects."""
    z0, z1 = SHELF_Z
    W, D, H, t = z1 - z0, 0.30, 2.10, 0.024
    f = Frame((X0, 0.0, (z0 + z1) / 2), 90.0)            # local +z into the room, +x toward -z
    for x in (-W / 2, W / 2 - t):
        k.box("study_oak", f, (x, 0.0, 0.0), (x + t, H, D), density=0.5)
    levels = [0.05, 0.47, 0.88, 1.27, 1.66, H - t]
    for y in levels:
        k.box("study_oak", f, (-W / 2 + t, y, 0.0), (W / 2 - t, y + t, D), over={"+y": dict(density=1.0)}, density=0.5)
    k.box("frame", f, (-W / 2 + t, 0.0, 0.02), (W / 2 - t, 0.05, D - 0.03))
    rng = random.Random(5)
    palette = ["book_navy", "book_cream", "book_rust", "book_olive", "book_charcoal", "book_cream", "book_navy"]
    inner = W - 2 * t
    for n, y in enumerate(levels[:-1]):
        y += t
        room = levels[n + 1] - y - 0.02
        x = -W / 2 + t + 0.01
        stop = W / 2 - t - (0.17 if n in (1, 3) else 0.01)
        while x < stop - 0.02:
            bw = rng.uniform(0.022, 0.045)
            if x + bw > stop:
                break
            bh = min(room, rng.uniform(0.21, 0.30))
            bd = rng.uniform(0.17, 0.23)
            book_upright(k, Frame(f((x + bw / 2, y, D - 0.02 - bd / 2)), f.yaw + rng.uniform(-1, 1)), (bw, bh, bd),
                         rng.choice(palette))
            x += bw + 0.001
        if n == 1:          # a short stack lying flat, with a brass sphere on it
            book_flat(k, Frame(f((W / 2 - t - 0.09, y, D / 2 + 0.02)), f.yaw + 90 + 3), (0.0, 0.0), (0.20, 0.04, 0.14), "book_charcoal")
            k.lathe("lamp_brass", Frame(f((W / 2 - t - 0.09, y + 0.04, D / 2 + 0.02))),
                    [(0.0, 0.0)] + [(0.038 * math.sin(math.pi * s), 0.038 - 0.038 * math.cos(math.pi * s)) for s in np.linspace(0.05, 1, 12)], 24)
        if n == 3:          # a small white vase
            k.lathe("ceramic_white", Frame(f((W / 2 - t - 0.085, y, D / 2))),
                    [(0.0, 0.0), (0.045, 0.0), (0.055, 0.04), (0.05, 0.11), (0.028, 0.16), (0.03, 0.18), (0.024, 0.18), (0.0, 0.17)], 28)


def tall_plant(k):
    """A fig tree (Poly Haven's potted_plant_01, CC0) in a tall dark ceramic pot."""
    x, z = PLANT
    f = Frame((x, 0.0, z))
    h = 0.52
    k.lathe("planter_dark", f, [(0.0, 0.0), (0.17, 0.0), (0.20, 0.06), (0.215, 0.30), (0.21, h), (0.195, h),
                                (0.195, h - 0.04), (0.0, h - 0.04)], 40)
    fig = load("potted_plant_01", only={"potted_plant_01_leaves", "potted_plant_01_stem"},
               thin={"potted_plant_01_leaves": 0.25})
    for name, piece in fig.items():
        mat = "study_fig_leaves" if name.endswith("leaves") else "study_fig_stems"
        place(k.b, G, mat, piece, (x, h - 0.04, z), yaw=-1.1, scale=1.75, origin=(0.0, 0.5, 0.0))


def coffee_table(k):
    """A glass top on a slim brass frame, with two art books and a small brass dish."""
    x0, x1 = TABLE_X
    z0, z1 = TABLE_Z
    top, t = TABLE_TOP, 0.012
    world = Frame((0.0, 0.0, 0.0))
    k.box("glass_table", world, (x0, top - t, z0), (x1, top, z1))
    r, inset = 0.008, 0.03
    a0, a1, c0, c1 = x0 + inset, x1 - inset, z0 + inset, z1 - inset
    ty = top - t - r
    for p, q in (((a0, ty, c0), (a1, ty, c0)), ((a0, ty, c1), (a1, ty, c1)),
                 ((a0, ty, c0), (a0, ty, c1)), ((a1, ty, c0), (a1, ty, c1))):
        k.tube("brass", p, q, r, segments=8)
    for x in (a0, a1):
        for z in (c0, c1):
            k.tube("brass", (x, RUG_T, z), (x, ty, z), r, segments=8)
    ly = 0.07
    k.tube("brass", (a0, ly, (c0 + c1) / 2), (a1, ly, (c0 + c1) / 2), r * 0.8, segments=8)
    for x in (a0, a1):
        k.tube("brass", (x, ly, c0), (x, ly, c1), r * 0.8, segments=8)
    # on the glass: two books, the smaller one turned, and a little brass dish
    f = Frame(((x0 + x1) / 2 + 0.02, top, z0 + 0.30), -80.0)
    book_flat(k, f, (0.0, 0.0), (0.30, 0.025, 0.24), "book_navy")
    book_flat(k, Frame(f((0.0, 0.025, 0.0)), -70.0), (0.0, 0.0), (0.25, 0.02, 0.20), "book_cream")
    k.lathe("brass", Frame(((x0 + x1) / 2 - 0.02, top, z1 - 0.26)),
            [(0.0, 0.0), (0.05, 0.0), (0.075, 0.012), (0.085, 0.022), (0.083, 0.024), (0.07, 0.014), (0.0, 0.01)], 32)


def sofa(k, f=None, L=SOFA["length"], D=SOFA["depth"], fabric="sofa_wool",
         pillows=("cushion_rust", "cushion_cream", "cushion_cream"), throw="throw"):
    """A deep, low sofa, built facing +z with its back along z = 0. By default the
    study's, in moss green wool, facing the whiteboard; the games room has one too."""
    f = f or Frame((SOFA["back_x"], 0.0, LOUNGE_Z), -90.0)
    W = L / 2
    arm, seat_y, base_y = 0.19, 0.44, 0.11
    # short tapered dark legs
    for x in (-W + 0.07, 0.0, W - 0.07):
        for z in (0.07, D - 0.07):
            k.tube("frame", f((x, 0.0, z)), f((x, base_y + 0.01, z)), 0.013, segments=8, r1=0.019)
    k.soft(fabric, f, (0, base_y + 0.10, D / 2), (L, 0.20, D), 0.035)                       # the base
    for sx in (-1, 1):                                                                            # arms
        k.soft(fabric, f, (sx * (W - arm / 2), base_y + 0.255, D / 2 - 0.005), (arm, 0.51, D - 0.01), 0.06)
    k.soft(fabric, f, (0, base_y + 0.20 + 0.24, 0.11), (L - 0.02, 0.48, 0.22), 0.07)         # back
    inner = L - 2 * arm
    cw = inner / 2 - 0.006
    for sx in (-1, 1):
        cx = sx * (cw / 2 + 0.003)
        k.soft(fabric, f, (cx, seat_y - 0.065, 0.22 + (D - 0.235) / 2), (cw, 0.15, D - 0.24), 0.055)       # seat
        k.soft(fabric, f, (cx, seat_y + 0.21, 0.31), (cw - 0.01, 0.44, 0.19), 0.085, tilt=-11,
               pivot=(cx, seat_y, 0.31))                                                                      # back cushion
    # throw pillows, and a wool throw folded over the far arm
    k.soft(pillows[0], f, (-W + arm + 0.27, seat_y + 0.22, 0.47), (0.46, 0.44, 0.14), 0.07, tilt=-16,
           pivot=(-W + arm + 0.27, seat_y, 0.47), turn=14)
    k.soft(pillows[1], f, (W - arm - 0.28, seat_y + 0.21, 0.46), (0.44, 0.42, 0.14), 0.07, tilt=-18,
           pivot=(W - arm - 0.28, seat_y, 0.46), turn=-10)
    if len(pillows) > 2:
        k.soft(pillows[2], f, (W - arm - 0.52, seat_y + 0.17, 0.53), (0.38, 0.34, 0.12), 0.06, tilt=-22,
               pivot=(W - arm - 0.52, seat_y, 0.53), turn=-22)
    if not throw:
        return
    ax = W - arm / 2
    k.soft(throw, f, (ax, base_y + 0.515, 0.62), (arm + 0.05, 0.03, 0.42), 0.012)
    k.soft(throw, f, (ax + arm / 2 + 0.018, base_y + 0.36, 0.62), (0.03, 0.30, 0.42), 0.012)
    k.soft(throw, f, (ax - arm / 2 - 0.02, base_y + 0.47, 0.62), (0.03, 0.12, 0.42), 0.012)


def floor_lamp(k):
    """A slim brass floor lamp with a linen drum shade, beside the end of the sofa."""
    x, z = FLOOR_LAMP
    f = Frame((x, 0.0, z))
    k.lathe("dark_bronze", f, [(0.0, 0.0), (0.15, 0.0), (0.15, 0.012), (0.13, 0.024), (0.02, 0.03), (0.0, 0.03)], 40)
    k.tube("lamp_brass", (x, 0.025, z), (x, 1.36, z), 0.0095, segments=10)
    y0, y1, r = 1.18, 1.50, 0.215
    k.lathe("shade_linen", f, [(r, y0), (r, y1)], 48)
    k.lathe("shade_linen", f, [(r - 0.004, y1), (r - 0.004, y0)], 48)       # its inside
    k.disc("light_warm", f, (0.0, y0 + 0.06, 0.0), r - 0.03, 32, down=True)
    for a in range(3):                                                        # the spider holding the shade
        ang = 2 * math.pi * a / 3
        k.tube("lamp_brass", (x, 1.36, z), (x + (r - 0.005) * math.cos(ang), y1 - 0.01, z + (r - 0.005) * math.sin(ang)),
               0.003, segments=6)
    LAMPS.append(dict(name="floor_lamp_down", pos=(x, y0 + 0.04, z), size=(0.3, 0.3), watts=28.0, aim=(0.0, -1.0, 0.0)))
    LAMPS.append(dict(name="floor_lamp_up", pos=(x, y1 - 0.04, z), size=(0.3, 0.3), watts=14.0, aim=(0.0, 1.0, 0.0)))
    LAMPS.append(dict(name="floor_lamp_glow", kind="point", pos=(x, (y0 + y1) / 2, z), watts=6.0, radius=0.12))


# ---- the desk ---------------------------------------------------------------------------
def desk(k):
    """A smoked oak top on a slim black steel frame, nothing on it but the lamp,
    the journal and a cup."""
    cx, z1, w, d, top, t = DESK["cx"], DESK["z1"], DESK["w"], DESK["d"], DESK["top"], DESK["t"]
    x0, x1, z0 = cx - w / 2, cx + w / 2, z1 - d
    world = Frame((0.0, 0.0, 0.0))
    k.box("study_oak", world, (x0, top - t, z0), (x1, top, z1), over={"+y": dict(density=2.0)}, density=0.6)
    s, inset = 0.024, 0.05
    for x in (x0 + inset, x1 - inset):
        for z in (z0 + inset, z1 - inset):
            k.rod("frame", (x, 0.0, z), (x, top - t, z), s)
        k.rod("frame", (x, 0.11, z0 + inset), (x, 0.11, z1 - inset), s * 0.8)              # low stretcher
    for z in (z0 + inset, z1 - inset):
        k.rod("frame", (x0 + inset, top - t - 0.03, z), (x1 - inset, top - t - 0.03, z), s)  # apron rails
    for x in (x0 + inset, x1 - inset):
        k.rod("frame", (x, top - t - 0.03, z0 + inset), (x, top - t - 0.03, z1 - inset), s)


def desk_lamp(k):
    """An elegant brass task lamp: a black marble disc, a slim stem, a long arm
    curving out over the journal and a small dome shade."""
    cx, z1, w, top = DESK["cx"], DESK["z1"], DESK["w"], DESK["top"]
    bx, bz = cx + w / 2 - 0.26, z1 - 0.16                   # on the sitter's left (+x), toward the glass
    f = Frame((bx, top, bz))
    k.lathe("black_marble", f, [(0.0, 0.0), (0.085, 0.0), (0.086, 0.004), (0.083, 0.02), (0.075, 0.024), (0.0, 0.024)], 40)
    stem_top = top + 0.43
    k.tube("lamp_brass", (bx, top + 0.022, bz), (bx, stem_top, bz), 0.0065, segments=10)
    k.lathe("lamp_brass", Frame((bx, stem_top - 0.006, bz)), [(0.0, 0.0), (0.012, 0.0), (0.012, 0.018), (0.0, 0.018)], 16)
    # the arm: from the stem's top, a gentle curve out and down toward the page
    tip = (cx + 0.16, top + 0.40, z1 - 0.29)
    path = arc((bx, stem_top + 0.006, bz), tip, 0.06, n=18)
    k.sweep("lamp_brass", path, 0.0045, segments=8)
    # the shade: a small brass dome hanging at the tip, tipped a little toward the sitter
    hx, hy, hz = tip
    shade = Frame((hx, hy - 0.085, hz), 0.0)
    # (the inside glows rather than being a second solid skin a few millimetres in,
    # which would leave the outside's baked light nowhere to come from)
    k.lathe("lamp_brass", shade, [(0.0, 0.085), (0.02, 0.083), (0.05, 0.068), (0.068, 0.04), (0.076, 0.008), (0.078, 0.0)], 40)
    k.lathe("lamp_glow", shade, [(0.074, 0.0), (0.071, 0.008), (0.063, 0.038), (0.046, 0.064), (0.018, 0.078), (0.0, 0.08)], 40)
    k.disc("light_warm", shade, (0.0, 0.012, 0.0), 0.07, 32, down=True)
    LAMPS.append(dict(name="desk_lamp", kind="spot", pos=(hx, hy - 0.08, hz), aim=(0.0, -1.0, -0.12), watts=22.0, cone=95.0))
    LAMPS.append(dict(name="desk_lamp_glow", kind="point", pos=(hx, hy - 0.05, hz), watts=1.5, radius=0.04))


def journal(k, segments=26):
    """An open journal: two gently curved pages over a dark leather cover, and a pen."""
    cx, z1, top = DESK["cx"], DESK["z1"], DESK["top"]
    f = Frame((cx - 0.05, top, z1 - 0.33), 8.0)       # reader sits at -z, the top of the pages toward +z
    W, H = 0.150, 0.210                                 # one page
    cover_t = 0.003
    k.soft("journal_cover", f, (0.0, cover_t / 2, 0.0), (2 * W + 0.012, cover_t, H + 0.008), 0.0015, n=1)

    def lift(s):
        """Height of the page surface, s from the gutter (0) to the outer edge (1)."""
        return cover_t + 0.0025 + 0.0085 * (1 - math.exp(-7.0 * s)) - 0.0012 * s

    rows = 6
    verts, faces, uvs = [], [], []
    for page in (0, 1):                                 # 0: the left page (+x), 1: the right page
        base = len(verts)
        for i in range(segments + 1):
            s = i / segments
            x = (s if page == 0 else -s) * W
            for j in range(rows + 1):
                v = j / rows
                verts.append((x, lift(s), (v - 0.5) * H))
        for i in range(segments):
            for j in range(rows):
                a, c = base + i * (rows + 1) + j, base + (i + 1) * (rows + 1) + j
                s0, s1 = i / segments, (i + 1) / segments
                v0, v1 = j / rows, (j + 1) / rows
                u = (lambda s: 0.5 - s * 0.5) if page == 0 else (lambda s: 0.5 + s * 0.5)
                quad = (a, c, c + 1, a + 1)
                uv = [(u(s0), v0), (u(s1), v0), (u(s1), v1), (u(s0), v1)]
                if page == 0:                            # keep every face pointing up
                    quad = (a, a + 1, c + 1, c)
                    uv = [(u(s0), v0), (u(s0), v1), (u(s1), v1), (u(s1), v0)]
                faces.append(quad)
                uvs.append(uv)
    k.mesh("journal_pages", f, verts, faces, uvs=uvs)
    # the page block's outer edges
    for sx in (1, -1):
        h = lift(1.0)
        k.quad("paper_edge", f, [(sx * W, cover_t, -H / 2), (sx * W, cover_t, H / 2), (sx * W, h, H / 2), (sx * W, h, -H / 2)]
               if sx > 0 else [(sx * W, cover_t, H / 2), (sx * W, cover_t, -H / 2), (sx * W, h, -H / 2), (sx * W, h, H / 2)])
    # a ribbon marker trailing out at the bottom
    k.quad("ribbon", f, [(-0.004, cover_t + 0.0005, -H / 2 - 0.05), (0.004, cover_t + 0.0005, -H / 2 - 0.05),
                         (0.004, lift(0.0) + 0.0003, -H / 2 + 0.02), (-0.004, lift(0.0) + 0.0003, -H / 2 + 0.02)])
    # the pen, lying across the right-hand page
    p0 = f((-0.03, lift(0.25) + 0.0055, -0.07))
    p1 = f((-0.10, lift(0.65) + 0.0055, 0.06))
    mid = tuple(np.add(p0, np.subtract(p1, p0) * 0.62))
    k.tube("pen_black", p0, mid, 0.0052, segments=10)
    k.tube("brass", mid, p1, 0.0055, segments=10)
    k.tube("pen_black", p1, tuple(np.add(p1, np.subtract(p1, p0) * 0.05)), 0.0055, segments=10, r1=0.002)


def cup(k):
    """A white ceramic cup on its saucer, on the sitter's right."""
    cx, z1, w, top = DESK["cx"], DESK["z1"], DESK["w"], DESK["top"]
    f = Frame((cx - w / 2 + 0.24, top, z1 - 0.22))
    k.lathe("ceramic_white", f, [(0.0, 0.0), (0.055, 0.0), (0.072, 0.008), (0.074, 0.011), (0.06, 0.009), (0.0, 0.007)], 36)
    k.lathe("ceramic_white", f, [(0.0, 0.009), (0.026, 0.009), (0.036, 0.016), (0.043, 0.04), (0.046, 0.075),
                                 (0.043, 0.075), (0.040, 0.042), (0.033, 0.022), (0.0, 0.02)], 36)
    k.disc("coffee", f, (0.0, 0.064, 0.0), 0.041, 24)
    handle = [f((0.046 + 0.022 * math.sin(math.pi * t), 0.028 + 0.034 * t, 0.0)) for t in np.linspace(0, 1, 10)]
    k.sweep("ceramic_white", handle, 0.0045, segments=8)


def task_chair(k, f, seat, shell, metal, caster="caster"):
    """A swivel chair on a five-star base, built facing +z. The back is a padded
    cushion shaped like a real one: it wraps round the sitter, swells forward at the
    small of the back and widens toward the shoulders, on a moulded shell. The seat
    is dished, with a rolled front edge. Used in the games room too, in black."""
    from .kit import cushion
    hub = 0.10
    # base: five tapered spokes with twin-wheel casters
    for i in range(5):
        a = 2 * math.pi * i / 5 + math.pi / 10
        end = np.array((0.30 * math.cos(a), 0.07, 0.30 * math.sin(a)))
        k.tube(metal, f((0, hub, 0)), f(tuple(end)), 0.019, segments=10, r1=0.012)
        k.tube(metal, f(tuple(end)), f(tuple(end + (0, -0.02, 0))), 0.008, segments=8)
        side = np.array((-math.sin(a), 0, math.cos(a))) * 0.012
        for sgn in (-1, 1):
            c = end * np.array((1.0, 0.0, 1.0)) + (0, 0.026, 0) + sgn * side
            k.tube(caster, f(tuple(c - side * 0.45)), f(tuple(c + side * 0.45)), 0.024, segments=14)
    k.lathe(metal, f, [(0.0, hub - 0.025), (0.05, hub - 0.025), (0.055, hub - 0.005), (0.045, hub + 0.025), (0.0, hub + 0.025)], 20)
    k.tube(caster, f((0, hub + 0.02, 0)), f((0, 0.30, 0)), 0.028, segments=16)
    k.tube(metal, f((0, 0.30, 0)), f((0, 0.39, 0)), 0.017, segments=16)
    k.soft(shell, f, (0, 0.40, -0.01), (0.24, 0.045, 0.26), 0.012, n=2)

    def place_shape(mat, verts, faces, centre, tilt=0.0, pivot=(0, 0, 0)):
        T = rot(x=tilt)
        pv, c = np.asarray(pivot, float), np.asarray(centre, float)
        k.b.mesh(k.g, mat, [f(pv + T @ (c + np.asarray(v) - pv)) for v in verts], faces)

    # the seat: a moulded shell with a thick cushion, dished in the middle, the front rolled down
    def shape_seat(verts, w, d, dish, roll):
        out = []
        for x, y, z in verts:
            if y > 0:
                y -= dish * max(0.0, 1 - (2 * x / w) ** 2) * max(0.0, 1 - (2 * z / d) ** 2)
            fz = (z - (d / 2 - 0.09)) / 0.09
            if fz > 0:
                y -= roll * fz ** 2
            out.append((x, y, z))
        return out
    v, fc = cushion((0.50, 0.03, 0.48), 0.012, n=2, div=6)
    place_shape(shell, shape_seat(v, 0.50, 0.48, 0.0, 0.02), fc, (0, 0.435, -0.005))
    v, fc = cushion((0.48, 0.085, 0.47), 0.035, n=3, div=8)
    place_shape(seat, shape_seat(v, 0.48, 0.47, 0.014, 0.035), fc, (0, 0.49, 0.0))

    # the back: wrapped round the sitter, a lumbar swell, wider at the shoulders
    def shape_back(verts, h, R=0.42, lumbar=0.03):
        out = []
        for x, y, z in verts:
            t = (y + h / 2) / h
            x *= 0.86 + 0.16 * math.sin(min(1.0, t * 1.4) * math.pi / 2)
            z += x * x / (2 * R) + lumbar * math.exp(-((t - 0.25) / 0.18) ** 2)
            out.append((x, y, z))
        return out
    lean, pivot = -12, (0, 0.55, -0.27)
    H = 0.58
    v, fc = cushion((0.47, H, 0.075), 0.034, n=3, div=10)
    place_shape(seat, shape_back(v, H), fc, (0, 0.585 + H / 2, -0.255), lean, pivot)
    v, fc = cushion((0.49, H + 0.03, 0.026), 0.012, n=2, div=10)
    place_shape(shell, shape_back(v, H + 0.03, lumbar=0.025), fc, (0, 0.585 + H / 2, -0.305), lean, pivot)
    # the spine joining the back to the seat
    k.sweep(shell, [f((0, 0.43, -0.10)), f((0, 0.43, -0.22)), f((0, 0.48, -0.31)), f((0, 0.60, -0.335)), f((0, 0.70, -0.33))],
            [0.024, 0.026, 0.026, 0.022, 0.018], 12)
    # arms: a loop from under the seat up to a padded rest
    for sx in (-1, 1):
        x = sx * 0.27
        k.sweep(metal, [f((sx * 0.19, 0.42, -0.10)), f((x, 0.43, -0.10)), f((x + sx * 0.005, 0.55, -0.08)), f((x, 0.645, -0.04))],
                0.012, 10)
        v, fc = cushion((0.06, 0.03, 0.26), 0.013, n=2, div=4)
        place_shape(shell, v, fc, (x, 0.66, 0.0))


# ---- the credenza -----------------------------------------------------------------------
def credenza(k):
    """A low smoked oak cabinet along the gym wall, with books, a succulent and a
    small brass sculpture on top."""
    z0, z1 = CREDENZA["z"]
    dep, h = CREDENZA["depth"], CREDENZA["h"]
    f = Frame((X1, 0.0, (z0 + z1) / 2), -90.0)        # facing -x, into the room; local +x runs toward +z
    L = z1 - z0
    k.box("frame", f, (-L / 2 + 0.03, 0.0, 0.03), (L / 2 - 0.03, 0.07, dep - 0.04), skip=("-y",))     # recessed plinth
    k.box("study_oak", f, (-L / 2, 0.07, 0.0), (L / 2, h, dep), over={"+y": dict(density=1.6)}, density=0.6, skip=("-z",))
    # three door fronts, with dark shadow gaps between them
    for i in (1, 2):
        x = -L / 2 + L * i / 3
        k.quad("frame", f, [(x - 0.003, 0.09, dep + 0.001), (x + 0.003, 0.09, dep + 0.001),
                            (x + 0.003, h - 0.02, dep + 0.001), (x - 0.003, h - 0.02, dep + 0.001)])
    for i in range(3):
        x = -L / 2 + L * (i + 0.5) / 3 + (0.14 if i < 2 else -0.14)
        k.soft("brass", f, (x, h - 0.12, dep + 0.008), (0.012, 0.12, 0.012), 0.004, n=1)
    rng = random.Random(23)
    # a row of books standing between a brass bookend and the wall end
    x = -L / 2 + 0.12
    for i in range(9):
        bw = rng.uniform(0.022, 0.042)
        bh = rng.uniform(0.20, 0.26)
        bd = rng.uniform(0.15, 0.19)
        mat = rng.choice(["book_navy", "book_cream", "book_rust", "book_olive", "book_charcoal", "book_cream"])
        book_upright(k, Frame(f((x + bw / 2, h, 0.06 + bd / 2)), f.yaw + rng.uniform(-1.5, 1.5)), (bw, bh, bd), mat)
        x += bw + 0.002
    k.soft("brass", f, (x + 0.006, h + 0.075, 0.06 + 0.09), (0.008, 0.15, 0.12), 0.003, n=1)
    k.soft("brass", f, (x + 0.05, h + 0.004, 0.06 + 0.09), (0.09, 0.008, 0.12), 0.003, n=1)
    # a stack of two lying flat
    book_flat(k, Frame(f((0.05, h, 0.22)), f.yaw + 4), (0.0, 0.0), (0.28, 0.03, 0.22), "book_charcoal")
    book_flat(k, Frame(f((0.05, h + 0.03, 0.22)), f.yaw - 3), (0.0, 0.0), (0.24, 0.024, 0.18), "book_rust")
    # a small brass sphere on the stack
    k.lathe("brass", Frame(f((0.05, h + 0.054, 0.22))),
            [(0.0, 0.0)] + [(0.045 * math.sin(math.pi * t), 0.045 - 0.045 * math.cos(math.pi * t)) for t in np.linspace(0.05, 1, 12)], 24)
    # the succulent (Poly Haven's potted_plant_04, CC0), its pot as it comes
    parts = load("potted_plant_04", skip={"potted_plant_04_ground"}, thin={"potted_plant_04_plant": 0.6})
    spot = f((L / 2 - 0.25, h, dep / 2))
    for piece in parts.values():
        place(k.b, G, "succulent", piece, spot, yaw=0.6, scale=1.15, origin=(0.0, 0.0, 0.0))


# ---- books -------------------------------------------------------------------------------
def book_upright(k, f, size, cover, pages="paper_edge"):
    """A book standing on its tail with its spine toward local +z, its footprint
    centred on f's origin: size is (thickness, height, depth)."""
    w, h, d = size
    c = 0.0025
    k.box(cover, f, (-w / 2, 0.0, -d / 2), (-w / 2 + c, h, d / 2))                 # boards
    k.box(cover, f, (w / 2 - c, 0.0, -d / 2), (w / 2, h, d / 2))
    k.box(cover, f, (-w / 2, 0.0, d / 2 - c), (w / 2, h, d / 2))                   # spine, facing +z
    k.box(pages, f, (-w / 2 + c, 0.003, -d / 2 + 0.003), (w / 2 - c, h - 0.003, d / 2 - c), skip=("+z",))


def book_flat(k, f, at, size, cover, pages="paper_edge"):
    """A book lying flat: size is (length, thickness, width), spine toward local -x."""
    x, z = at
    L, t, W = size
    c = 0.0025
    k.box(cover, f, (x - L / 2, 0.0, z - W / 2), (x + L / 2, c, z + W / 2))
    k.box(cover, f, (x - L / 2, t - c, z - W / 2), (x + L / 2, t, z + W / 2))
    k.box(cover, f, (x - L / 2, 0.0, z - W / 2), (x - L / 2 + c, t, z + W / 2))
    k.box(pages, f, (x - L / 2 + c, c, z - W / 2 + 0.003), (x + L / 2 - 0.003, t - c, z + W / 2 - 0.003), skip=("-x",))


# ---- pictures the build paints ------------------------------------------------------------
def paint_pictures():
    paint_rug()
    paint_whiteboard()
    paint_journal()


def _smooth_noise(shape, scale, rng):
    h, w = shape
    f = np.fft.fft2(rng.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * scale
    fx = np.fft.fftfreq(w)[None, :] * scale
    out = np.fft.ifft2(f * np.exp(-(fy ** 2 + fx ** 2) * 8)).real
    return out / (np.abs(out).max() + 1e-9)


def paint_rug(w=760, h=608):
    """An original Persian-style medallion rug: a madder red field with an all-over
    lattice of small flowers, a scalloped indigo medallion with pendants, indigo
    corner pieces, and a wide indigo border with a running vine between guard
    stripes. Wool texture and a little abrash (the colour drift of hand-dyed yarn).
    Picture rows run along the rug's short side (z), columns along its length (x)."""
    rng = np.random.default_rng(31)
    Lx, Lz = RUG_X[1] - RUG_X[0], RUG_Z[1] - RUG_Z[0]
    xs = (np.arange(w) + 0.5) / w * Lx - Lx / 2
    zs = (np.arange(h) + 0.5) / h * Lz - Lz / 2
    X, Z = np.meshgrid(xs, zs)
    # hand-knotted: nothing is quite straight, so the whole design wanders a little
    X = X + 0.010 * _smooth_noise((h, w), 6, rng) + 0.003 * _smooth_noise((h, w), 30, rng)
    Z = Z + 0.010 * _smooth_noise((h, w), 6, rng) + 0.003 * _smooth_noise((h, w), 30, rng)
    red = np.array([0.50, 0.11, 0.09])
    madder = np.array([0.62, 0.20, 0.14])
    indigo = np.array([0.11, 0.14, 0.27])
    ivory = np.array([0.86, 0.80, 0.66])
    gold = np.array([0.80, 0.60, 0.30])
    brown = np.array([0.20, 0.11, 0.08])
    sky = np.array([0.42, 0.55, 0.62])
    img = np.zeros((h, w, 3)) + red

    def put(mask, colour):
        img[mask] = colour

    edge = np.minimum(Lx / 2 - np.abs(X), Lz / 2 - np.abs(Z))      # metres in from the nearest edge
    BORDER = (0.05, 0.25)
    field = edge > 0.29

    # -- the field: a lattice of diamonds with a small rosette in each, and sprigs between
    cell = 0.115
    u, v = X / cell, Z / (cell * 0.8)
    fu, fv = u - np.round(u), v - np.round(v)
    lattice = np.abs(np.abs(fu) + np.abs(fv) - 0.5) < 0.045
    put(field & lattice, madder * 0.9 + 0.1 * indigo)
    rr = np.hypot(fu, fv)
    ang = np.arctan2(fv, fu)
    petals = rr < 0.16 * (0.7 + 0.3 * np.cos(6 * ang))
    put(field & petals, ivory * 0.92)
    put(field & (rr < 0.06), indigo)
    gu, gv = u + 0.5 - np.round(u + 0.5), v + 0.5 - np.round(v + 0.5)
    sprig = (np.hypot(gu, gv * 1.6) < 0.09) & (np.abs(np.arctan2(gv, gu)) % (np.pi / 2) < 0.6)
    put(field & sprig, gold * 0.85)
    put(field & (np.hypot(gu, gv) < 0.035), sky * 0.8)

    # -- corner pieces: indigo quarter-ellipses with scalloped edges and an ivory rim
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (Lx / 2 - 0.29), sz * (Lz / 2 - 0.29)
            dx, dz = (X - cx) / 0.46, (Z - cz) / 0.34
            rc = np.hypot(dx, dz)
            a = np.arctan2(dz, dx)
            lim = 1 + 0.035 * np.cos(26 * a)
            inside = field & (rc < lim)
            put(inside & (rc > lim - 0.07), ivory)
            put(inside & (rc <= lim - 0.07), indigo)
            gx, gz = (X - cx) / 0.06, (Z - cz) / 0.06
            fx, fz = gx - np.round(gx), gz - np.round(gz)
            bud = inside & (rc < lim - 0.15) & (np.hypot(fx, fz) < 0.22 * (0.7 + 0.3 * np.cos(5 * np.arctan2(fz, fx))))
            put(bud, madder)
            put(inside & (rc < lim - 0.15) & (np.hypot(fx, fz) < 0.07), gold)

    # -- the medallion, with pendants along the long axis
    a_, b_ = 0.62, 0.46
    mx, mz = X / a_, Z / b_
    rm = np.hypot(mx, mz)
    am = np.arctan2(mz, mx)
    outline = 1 + 0.035 * np.cos(28 * am) + 0.10 * np.cos(4 * am) ** 8
    med = rm < outline
    put(med & (rm > outline - 0.045), ivory)
    put(med & (rm <= outline - 0.045), indigo)
    ring = med & (np.abs(rm - 0.80) < 0.06) & (np.cos(24 * am) > 0.2)
    put(ring, madder)
    put(med & (np.abs(rm - 0.80) < 0.022) & (np.cos(24 * am) > 0.6), ivory)
    starline = 0.56 * (1 + 0.16 * np.cos(16 * am))
    star = rm < starline
    put(med & star, madder)
    put(med & star & (rm > starline - 0.035), ivory)
    put(med & star & (np.abs(rm - 0.42) < 0.02) & (np.cos(16 * am) > 0), gold)
    put(rm < 0.30 * (1 + 0.1 * np.cos(12 * am)), indigo)
    put(rm < 0.20, ivory * 0.95)
    put(rm < 0.14 * (0.75 + 0.25 * np.cos(8 * am)), madder)
    put(rm < 0.05, gold)
    for sx in (-1, 1):
        px = sx * (a_ * 1.18 + 0.05)
        d = np.abs(X - px) / 0.10 + np.abs(Z) / 0.07
        put(d < 1.0, indigo)
        put((d < 1.0) & (d > 0.78), ivory)
        put(d < 0.35, madder)
        stem = (np.abs(Z) < 0.008) & (np.abs(X) > a_ * 1.05) & (np.abs(X) < np.abs(px)) & (np.sign(X) == sx)
        put(stem, ivory)

    # -- the border: guard stripes either side of a wide indigo band with a running vine
    put((edge < BORDER[1]) & (edge >= BORDER[0]), indigo)
    put((edge < 0.05) & (edge >= 0.012), ivory)
    put((edge < 0.05) & (edge >= 0.012) & (np.abs(np.sin((X + Z) * 90)) > 0.8), madder)
    put((edge >= 0.05) & (edge < 0.058), madder)
    put((edge >= 0.242) & (edge < 0.25), gold)
    put((edge >= 0.25) & (edge < 0.28), madder)
    put((edge >= 0.25) & (edge < 0.28) & (np.abs(np.sin((X - Z) * 70)) > 0.88), ivory)
    put((edge >= 0.28) & (edge < 0.29), indigo)
    put(edge < 0.012, brown)
    band = (edge >= BORDER[0] + 0.01) & (edge < BORDER[1] - 0.01)
    long_side = (Lx / 2 - np.abs(X)) > (Lz / 2 - np.abs(Z))
    s = np.where(long_side, X, Z)                                   # distance along the border
    t = (edge - BORDER[0]) / (BORDER[1] - BORDER[0])                # 0 at the outside, 1 at the inside
    period = 0.30
    wave = 0.5 + 0.30 * np.sin(2 * np.pi * s / period)
    vine = band & (np.abs(t - wave) * (BORDER[1] - BORDER[0]) < 0.0075)
    put(vine, ivory)
    for shift, colour in ((0.25, madder), (0.75, gold)):
        k = np.round(s / period - shift) + shift
        cs = k * period
        ct = 0.5 + 0.30 * np.sin(2 * np.pi * cs / period)
        dd = np.hypot(s - cs, (t - ct) * (BORDER[1] - BORDER[0]))
        aa = np.arctan2((t - ct), (s - cs))
        bloom = band & (dd < 0.045 * (0.72 + 0.28 * np.cos(6 * aa)))
        put(bloom, colour)
        put(band & (dd < 0.014), ivory)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (Lx / 2 - 0.15), sz * (Lz / 2 - 0.15)
            dd = np.abs(X - cx) + np.abs(Z - cz)
            put(dd < 0.085, madder)
            put(dd < 0.05, ivory)
            put(dd < 0.02, indigo)

    # -- wool. First soften the drawing a touch (knots blur an edge over a few millimetres)...
    k = np.ones(3) / 3
    for axis in (0, 1):
        img = np.apply_along_axis(lambda r: np.convolve(np.pad(r, 1, mode="edge"), k, "valid"), axis, img)
    # ...then build it from knots: about 3 mm each, every one a slightly different shade
    kn = 2
    cells = rng.normal(1.0, 0.06, (h // kn + 1, w // kn + 1))
    img = img * np.kron(cells, np.ones((kn, kn)))[:h, :w, None]
    # rows of knots and the weft between them show as faint lines across the pile
    rows = 1.0 - 0.06 * (np.arange(h) % 4 == 0)[:, None, None] - 0.03 * (np.arange(w) % 6 == 0)[None, :, None]
    img = img * rows
    # abrash: bands where a new batch of hand-dyed yarn began, running across the width
    abrash = 1.0 + 0.08 * _smooth_noise((1, w), 3.0, rng)[0][None, :, None]
    abrash = abrash * (1.0 + np.array([0.0, 0.03, 0.05]) * _smooth_noise((1, w), 5.0, rng)[0][None, :, None])
    mottle = 1.0 + 0.06 * _smooth_noise((h, w), 25, rng)[..., None]
    img = img * abrash * mottle
    # wear: the pile thinned to the pale foundation where feet go, most in the middle
    yy, xx = np.mgrid[0:h, 0:w]
    centre = np.exp(-(((xx - w / 2) / (w * 0.32)) ** 2 + ((yy - h / 2) / (h * 0.34)) ** 2))
    worn = np.clip(_smooth_noise((h, w), 14, rng) * 1.4 + centre * 0.55 - 0.45, 0, 1)
    worn = worn * (0.6 + 0.4 * (rng.random((h, w)) > 0.35))
    foundation = np.array([0.70, 0.62, 0.50])
    img = img * (1 - worn[..., None] * 0.55) + foundation * worn[..., None] * 0.55
    # an old rug's colours: faded toward grey, a little darker, warmed
    grey = img.mean(axis=2, keepdims=True)
    img = (img * 0.62 + grey * 0.38) * np.array([0.98, 0.93, 0.86]) * 0.92
    img = 0.08 + (img - 0.08) * 0.85                        # flatter contrast, like wool in soft light
    save_png(picture_path("persian_rug"), np.clip(img, 0, 1).astype(np.float32))


def _strokes(shape, polylines, width):
    """Coverage (0..1) of marker strokes: each polyline is a list of (x, y) pixels."""
    h, w = shape
    out = np.zeros((h, w))
    for line in polylines:
        pts = np.asarray(line, float)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            xa, xb = int(max(0, min(x0, x1) - width - 2)), int(min(w, max(x0, x1) + width + 3))
            ya, yb = int(max(0, min(y0, y1) - width - 2)), int(min(h, max(y0, y1) + width + 3))
            if xa >= xb or ya >= yb:
                continue
            yy, xx = np.mgrid[ya:yb, xa:xb] + 0.5
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy or 1e-9
            t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
            d = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
            out[ya:yb, xa:xb] = np.maximum(out[ya:yb, xa:xb], np.clip(width / 2 - d + 0.5, 0, 1))
    return out


def _wobbly(points, rng, amount, steps=8):
    """A hand-drawn version of a polyline: subdivided, with a slow wobble."""
    out = []
    pts = np.asarray(points, float)
    phase = rng.uniform(0, 6.28)
    for i, (a, c) in enumerate(zip(pts[:-1], pts[1:])):
        for s in range(steps):
            t = s / steps
            p = a + (c - a) * t
            n = np.array([-(c - a)[1], (c - a)[0]])
            n /= (np.linalg.norm(n) or 1)
            out.append(p + n * amount * math.sin(phase + (i + t) * 2.1))
    out.append(pts[-1] + np.array([rng.gauss(0, amount * 0.3), rng.gauss(0, amount * 0.3)]))
    return out


def _box_outline(cx, cy, bw, bh, rng, r=10):
    """A rounded rectangle drawn in one go by hand, overshooting where it closes."""
    pts = []
    for k in range(4):
        a0 = k * math.pi / 2
        corner = [(cx + (bw / 2 - r) * (1 if k in (0, 3) else -1), cy + (bh / 2 - r) * (1 if k in (0, 1) else -1))]
        for t in np.linspace(0, 1, 5):
            a = a0 + t * math.pi / 2
            pts.append((corner[0][0] + r * math.cos(a), corner[0][1] + r * math.sin(a)))
    pts.append(pts[0])
    pts.append((pts[1][0] + 6, pts[1][1] + 2))
    return _wobbly(pts, rng, 1.6, steps=6)


def paint_whiteboard(w=800, h=416):
    """The call flow, drawn by hand in marker: three boxes joined by arrows, with
    the faint ghosts of earlier sessions not quite wiped off."""
    from .labels import text_mask
    rng = np.random.default_rng(14)
    rnd = random.Random(14)
    img = np.ones((h, w, 3)) * np.array([0.93, 0.94, 0.94])
    # ghosting: soft grey smears where earlier drawings were wiped
    ghost = np.clip(_smooth_noise((h, w), 18, rng), 0, 1) * 0.05
    img -= ghost[..., None] * np.array([1.0, 1.0, 0.9])
    old = _strokes((h, w), [_wobbly([(60, 330), (260, 345), (420, 320)], rnd, 3),
                            _wobbly([(520, 80), (700, 95)], rnd, 3)], 5)
    img -= old[..., None] * 0.035
    ink = np.array([0.10, 0.12, 0.20])
    blue = np.array([0.13, 0.27, 0.60])
    green = np.array([0.12, 0.45, 0.24])
    # the three boxes (pixel rows count from the bottom, like the text mask)
    centres = [(0.155, 0.52), (0.50, 0.50), (0.845, 0.52)]
    bw, bh = 0.235 * w, 0.34 * h
    boxes = [_box_outline(cx * w, cy * h, bw * (1.02 if i == 1 else 1), bh, rnd) for i, (cx, cy) in enumerate(centres)]
    lines = _strokes((h, w), boxes, 4.6)
    # arrows between them, slightly bowed
    arrows = []
    for (ax, ay), (cx, cy) in zip(centres[:-1], centres[1:]):
        x0, x1 = ax * w + bw / 2 + 14, cx * w - bw / 2 - 16
        y = (ay + cy) / 2 * h + rnd.uniform(-4, 4)
        mid = [(x0 + (x1 - x0) * t, y + 7 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 12)]
        arrows.append(_wobbly(mid, rnd, 0.8, steps=2))
        arrows.append(_wobbly([(x1 - 15, y + 11), (x1, y + 1), (x1 - 16, y - 9)], rnd, 0.8, steps=3))
    arrow_ink = _strokes((h, w), arrows, 4.2)
    # a tick after "booked"
    tick = _strokes((h, w), [_wobbly([(0.845 * w + 40, 0.40 * h - 4), (0.845 * w + 50, 0.40 * h - 14), (0.845 * w + 70, 0.40 * h + 16)], rnd, 0.6, 3)], 4.4)
    words = [("call", 0.155, 0.555, 0.10), ("comes in", 0.155, 0.415, 0.10),
             ("AI agent", 0.50, 0.535, 0.10), ("answers", 0.50, 0.395, 0.10),
             ("appointment", 0.845, 0.555, 0.088), ("booked", 0.845, 0.415, 0.10)]
    text = text_mask((w, h), [(t, x, y, s, "CENTER", 1.0) for t, x, y, s in words], font="Kalam-Bold.ttf")
    # marker strokes aren't perfectly even
    streak = 1.0 - 0.18 * np.clip(_smooth_noise((h, w), 3, rng), 0, 1)
    for mask, colour in ((lines, ink), (text, ink), (arrow_ink, blue), (tick, green)):
        m = (mask * streak)[..., None]
        img = img * (1 - m) + colour * m
    save_png(picture_path("whiteboard"), np.clip(img, 0, 1).astype(np.float32))


def paint_journal(w=512, h=360):
    """The open journal: cream pages with faint rules, notes in blue ink on the
    left, a little sketch of the flow on the right, and the shadow of the gutter."""
    from .labels import text_mask
    rng = np.random.default_rng(6)
    rnd = random.Random(6)
    img = np.ones((h, w, 3)) * np.array([0.94, 0.91, 0.83])
    img *= (1 + 0.012 * rng.standard_normal((h, w)))[..., None]
    rows = np.arange(h)[:, None]
    ruled = (np.abs(((rows - 22) % 22) - 0) < 1) & (rows > 30) & (rows < h - 30)
    img[np.broadcast_to(ruled, (h, w))] *= np.array([0.86, 0.90, 0.97])
    ink = np.array([0.11, 0.15, 0.36])
    left = [("call flow v3", 0.07, 0.86, 0.065), ("- greet, ask what they need", 0.07, 0.74, 0.052),
            ("- check the calendar", 0.07, 0.62, 0.052), ("- book it, confirm by text", 0.07, 0.50, 0.052),
            ("- hand off if unsure", 0.07, 0.38, 0.052), ("test the after-hours path", 0.07, 0.20, 0.052)]
    text = text_mask((w, h), [(t, x, y, s, "LEFT", 1.0) for t, x, y, s in left], font="Kalam-Regular.ttf")
    right = [("call", 0.60, 0.70, 0.05), ("agent", 0.735, 0.70, 0.05), ("booked", 0.88, 0.70, 0.05),
             ("ship it", 0.62, 0.36, 0.06)]
    text = np.maximum(text, text_mask((w, h), [(t, x, y, s, "CENTER", 1.0) for t, x, y, s in right], font="Kalam-Regular.ttf"))
    sketch = [_wobbly([(0.60 * w - 28, 0.80 * h), (0.60 * w + 28, 0.80 * h), (0.60 * w + 28, 0.66 * h), (0.60 * w - 28, 0.66 * h), (0.60 * w - 28, 0.80 * h)], rnd, 0.7, 4),
              _wobbly([(0.735 * w - 28, 0.80 * h), (0.735 * w + 28, 0.80 * h), (0.735 * w + 28, 0.66 * h), (0.735 * w - 28, 0.66 * h), (0.735 * w - 28, 0.80 * h)], rnd, 0.7, 4),
              _wobbly([(0.88 * w - 30, 0.80 * h), (0.88 * w + 30, 0.80 * h), (0.88 * w + 30, 0.66 * h), (0.88 * w - 30, 0.66 * h), (0.88 * w - 30, 0.80 * h)], rnd, 0.7, 4),
              _wobbly([(0.60 * w + 32, 0.73 * h), (0.735 * w - 32, 0.73 * h)], rnd, 0.4, 3),
              _wobbly([(0.735 * w + 32, 0.73 * h), (0.88 * w - 34, 0.73 * h)], rnd, 0.4, 3),
              _wobbly([(0.62 * w - 40, 0.33 * h), (0.62 * w + 42, 0.33 * h)], rnd, 0.5, 4),
              _wobbly([(0.29 * w - 120, 0.835 * h), (0.29 * w - 8, 0.835 * h)], rnd, 0.5, 4)]
    lines = _strokes((h, w), sketch, 1.6)
    mask = np.maximum(text, lines)[..., None] * 0.92
    img = img * (1 - mask) + ink * mask
    # the gutter's shadow down the middle, and a slightly darker outer edge
    u = (np.arange(w) + 0.5) / w
    gutter = 1 - 0.28 * np.exp(-((u - 0.5) / 0.035) ** 2) - 0.06 * np.exp(-((u - 0.5) / 0.12) ** 2)
    img *= gutter[None, :, None]
    save_png(picture_path("journal"), np.clip(img, 0, 1).astype(np.float32))
