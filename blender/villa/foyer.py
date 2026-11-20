"""The foyer, furnished: an empty plinth waiting for the sculpture, a glass balustrade
and a brass rail up the stairs, and an oak console against the dark stone wall under
an original painting.

Plan, looking down, seen from the driveway (the dining room wall at the top, so +x is
on the right):

                                                    dining door           (z = 0)
     +=========== the stairs, rising to the right ==========+---[    ]----+
     |                     [resume door]                     |      (keep  |  d
   g |                                                              clear) |  a
   a |   (kept clear in front of the stairs, for the vault)               r  s
   r door                                                     [console] k  t
   a |                         [plinth]                                   o
   g |                                                          (fig)     n  e
   e |                                                                    e  w
     |                     ~~ runner ~~                         study door    a
     +-----[ glass ]--------[ front door ]------------[ glass ]-----------+  l
                                                                          (z = 8)

The plinth stands on the front door's axis, a pale stone block with a shadow gap at
its foot, lit by two spots from the ceiling already aimed where the sculpture will
stand. The strip in front of the stairs is left clear for the stairs down to the
vault.

Everything is lit per vertex, the walls, the stairs' side and the ceiling lined over
the house's own, so the room stays clean from a quick draft bake; it has no lightmap.
"""
import math

import numpy as np

from . import config as C
from .house import DOOR, H1, P
from .kit import Frame, Kit, grid, panel, wall
from .materials import srgb_to_linear
from .study import _smooth_noise, book_flat
from .textures import picture_path, save_png

ROOM, G = "foyer", "ground"
F2 = C.F2

# The room's inside faces.
XW = -5.0 + P / 2                 # the wall to the garage, its door from z 3.4 to 4.6 (-4.925)
XE = C.BLADE_X[0]                 # the dark stone wall, the door to the study from z 5.0 to 6.2 (1.0)
ZN = P / 2                        # the wall to the dining room (0.075)
ZF = C.HALF_D - C.WALL            # the front: glass, the front door from x -2.9 to -1.5 (7.7)
GARAGE_DOOR = (3.4, 4.6)
STUDY_DOOR = (5.0, 6.2)
SX0, SX1, (SZ0, SZ1) = C.STAIR_X0, C.STAIR_X1, C.STAIR_Z
RISE, TREAD = F2 / C.STAIR_RISERS, C.STAIR_TREAD
STEPS = C.STAIR_RISERS - 1


def step(i):
    """Step i of the flight, 0 the bottom: its x from the back of its tread to its nose
    (the flight climbs toward -x), and its top."""
    x1 = SX1 - i * TREAD
    return x1 - TREAD, x1, (i + 1) * RISE


def pitch(x):
    """The line through the steps' noses: its height over x."""
    return RISE * (1 + (SX1 - x) / TREAD)
RESUME_DOOR = (-2.79, -1.96, 1.34)          # the little door in the stairs' side, with its frame
LINING = 0.012

PLINTH = dict(x=-2.20, z=3.90, w=0.56, h=0.95)
CONSOLE = dict(z=3.25, L=1.60, D=0.38, H=0.80)      # on the dark stone wall
PAINTING = dict(w=0.95, h=1.20, y=1.98)
FIG = (0.52, 4.58)
RUNNER = dict(x=(-3.05, -1.35), z=(5.05, 7.35), t=0.010)
RAIL = 0.92                                  # the balustrade's height over the stairs' pitch line

CEILING_LIGHT = 0.45
LAMPS = []

# Review cameras. The first is also the room's view on the website: in the front corner by
# the stone wall, looking across to the stairs (climbing from the right to the left), the
# plinth to the left of the resume door, the console on the stone wall at the right.
FOYER_CAM = dict(pos=(0.40, 1.60, 7.00), target=(-2.60, 1.00, 1.00), fov=55.0)
CONSOLE_CAM = dict(pos=(-1.25, 1.55, 4.70), target=(1.0, 1.30, 3.10), fov=52.0)


def build_foyer(b):
    LAMPS.clear()
    paint_painting()
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    with b.room(ROOM):
        walls(k)
        stair_side(k)
        ceiling(Kit(b, "upper", None))
        balustrade(k)
        runner(k)
        plinth(k)
        vessel(k)
        console(k)
        painting(k)
        fig(k)


# ---- the room ------------------------------------------------------------------------------------
def walls(k):
    """The dark stone wall lined in the same granite, lit per vertex (it stops round the
    painting, so nothing is buried behind it, gotcha 26), and plaster over the garage
    wall."""
    e = LINING
    world = Frame((0.0, 0.0, 0.0))
    pz0, pz1 = CONSOLE["z"] - PAINTING["w"] / 2 - 0.005, CONSOLE["z"] + PAINTING["w"] / 2 + 0.005
    py0, py1 = PAINTING["y"] - PAINTING["h"] / 2 - 0.005, PAINTING["y"] + PAINTING["h"] / 2 + 0.005
    s0, s1 = STUDY_DOOR
    for z0, z1, y0, y1 in ((ZN, pz0, 0.0, H1), (pz0, pz1, 0.0, py0), (pz0, pz1, py1, H1), (pz1, s0, 0.0, H1),
                           (s1, ZF, 0.0, H1), (s0, s1, DOOR, H1)):
        k.grain("foyer_stone", world, (XE - e - 0.002, y0, z0), (XE - e, y1, z1), step=0.15,
                skip=("+x", "+y", "-y", "+z", "-z"), along="z")
    # the garage wall (facing +x), round its door
    g0, g1 = GARAGE_DOOR
    wall(k, "plaster_v", (XW + e, 0.0, ZF), (0, 0, ZN - ZF), (0, H1, 0), step=0.15, holes=[(ZF - g1, ZF - g0, 0.0, DOOR)])
    # over the door to the dining room, beside the top of the stairs (facing +z)
    panel(k, "plaster_v", (SX1, DOOR, ZN + e), (XE - SX1, 0, 0), (0, H1 - DOOR, 0), step=0.15)


def stair_side(k):
    """The stairs' side, toward the foyer, lined in charcoal lit per vertex: a column per
    step up to the underside of its oak tread, round the little resume door, and the
    closed alcove under the top up to the ceiling. And the wall behind the stairs, in
    plaster, from each tread up to the ceiling."""
    for i in range(STEPS):
        x0, x1, y0 = step(i)
        if y0 < H1:
            panel(k, "plaster_v", (x0, y0, ZN + LINING), (x1 - x0, 0, 0), (0, H1 - y0, 0), step=0.14)
    z = SZ1 + LINING
    d0, d1, dh = RESUME_DOOR
    cap = 0.05                                   # the oak treads' thickness under each step's top
    for i in range(STEPS):
        x0, x1, top = step(i)
        top -= cap
        pieces = []
        if x1 <= d0 or x0 >= d1:
            pieces.append((x0, x1, 0.0, top))
        else:
            if x0 < d0:
                pieces.append((x0, d0, 0.0, top))
            if x1 > d1:
                pieces.append((d1, x1, 0.0, top))
            pieces.append((max(x0, d0), min(x1, d1), dh, top))
        for a, c, y0, y1 in pieces:
            if y1 - y0 > 1e-3 and c - a > 1e-3:
                panel(k, "stair_dark", (a, y0, z), (c - a, 0, 0), (0, y1 - y0, 0), step=0.14)
    panel(k, "stair_dark", (XW, 0.0, z), (SX0 - XW, 0, 0), (0, H1 - 0.014, 0), step=0.14)
    treads(k)


def treads(k):
    """Make the stairs read as oak treads floating off a dark wall: each step gets a thick
    oak slab over its top, its nose standing 3 cm proud of the riser and 4 cm past the
    side, and the risers and the side under them are lined in charcoal, so the slabs float.
    The landing's edge at the top gets the same oak nose."""
    world = Frame((0.0, 0.0, 0.0))
    for i in range(STEPS):
        x0, x1, top = step(i)
        k.grain("foyer_oak", world, (x0, top - 0.05, ZN + 0.004), (x1 + 0.03, top + 0.012, SZ1 + 0.04), step=0.07, along="z",
                skip=("-x",))
        lo = top - RISE + (0.012 if i else 0.0)
        panel(k, "stair_dark", (x1 + LINING, lo, SZ1), (0, 0, ZN + 0.004 - SZ1), (0, top - 0.05 - lo, 0), step=0.14)
    # the last rise, onto the landing: charcoal under an oak nose on the landing's edge
    lo = STEPS * RISE + 0.012
    panel(k, "stair_dark", (SX0 + LINING, lo, SZ1), (0, 0, ZN + 0.004 - SZ1), (0, F2 - 0.05 - lo, 0), step=0.1)
    k.grain("foyer_oak", world, (SX0 - 0.30, F2 - 0.05, ZN + 0.004), (SX0 + 0.03, F2 + 0.006, SZ1 + 0.04), step=0.07, along="z")


def ceiling(k):
    """The ceiling lined in plaster (it lifts off with the upstairs floor), round the
    open stairwell, with its own downlight fittings and the plinth's two spots."""
    from .house import downlight_spots
    y = H1 - 0.014
    panel(k, "plaster_v", (XW, y, SZ1), (XE - XW, 0, 0), (0, 0, ZF - SZ1), step=0.25)
    panel(k, "plaster_v", (SX1, y, ZN), (XE - SX1, 0, 0), (0, 0, SZ1 - ZN), step=0.25)
    s = 0.07
    for px, pz in downlight_spots(ROOM):
        k.b.quad("upper", "light_warm", [(px - s, y - 0.002, pz - s), (px + s, y - 0.002, pz - s),
                                         (px + s, y - 0.002, pz + s), (px - s, y - 0.002, pz + s)])
    # the plinth's spots, aimed at where the sculpture will stand, and the painting's
    px, pz = PLINTH["x"], PLINTH["z"]
    target = (px, PLINTH["h"] + 0.45, pz)
    for dx, dz in ((-0.85, 0.95), (0.85, 0.95)):
        pos = (px + dx, y - 0.03, pz + dz)
        can(k, (pos[0], y, pos[2]))
        LAMPS.append(dict(name=f"plinth_spot_{'l' if dx < 0 else 'r'}", kind="spot", pos=pos,
                          aim=tuple(np.subtract(target, pos)), watts=36.0, cone=30.0))
    pos = (XE - 1.15, y - 0.03, CONSOLE["z"])
    can(k, (pos[0], y, pos[2]))
    aim = (XE - 0.05, PAINTING["y"] - 0.1, CONSOLE["z"])
    LAMPS.append(dict(name="painting_spot", kind="spot", pos=pos, aim=tuple(np.subtract(aim, pos)), watts=30.0, cone=42.0))


def can(k, pos):
    """A small downlight set in the ceiling: a black rim round a glowing lens."""
    x, y, z = pos
    k.tube("foyer_black", (x, y + 0.004, z), (x, y - 0.006, z), 0.05, segments=20, step=0.01)
    k.disc("light_warm", Frame((x, y - 0.0065, z)), (0.0, 0.0, 0.0), 0.034, 20, down=True)


def balustrade(k):
    """Glass up the open side of the stairs, toward the foyer (two faces, 12 mm apart,
    green at its edges so it reads as glass), standing in a slim channel on each tread
    and rising to a line above the steps' noses, with a brass handrail along its top. It
    stops at the landing's floor, where the landing's own glass round the stairwell carries
    on above it."""
    z = SZ1 - 0.035
    world = Frame((0.0, 0.0, 0.0))
    top = F2 - 0.01                                   # no higher than the landing's floor

    def up(x):
        return min(pitch(x) + RAIL, top)
    for i in range(STEPS):
        x0, x1, y = step(i)
        k.b.quad(G, "foyer_glass", [(x0, y + 0.03, z), (x1, y + 0.03, z), (x1, up(x1), z), (x0, up(x0), z)])
        k.b.quad(G, "foyer_glass", [(x1, y + 0.03, z - 0.012), (x0, y + 0.03, z - 0.012), (x0, up(x0), z - 0.012),
                                    (x1, up(x1), z - 0.012)])
        k.block("foyer_black", world, (x0, y + 0.012, z - 0.025), (x1, y + 0.04, z + 0.013), step=0.3, skip=("-y",))
    # where the glass reaches the landing's floor, and the handrail runs into the landing's shoe
    x_meet = SX1 - ((top - RAIL) / RISE - 1) * TREAD
    # the glass's edges show green, as thick glass does: along its top and down its foot end
    edge = [(x, up(x) - 0.004, z - 0.006) for x in np.linspace(SX1, SX0, 40)]
    k.sweep("foyer_glass_edge", edge, 0.0065, 6)
    k.tube("foyer_glass_edge", (SX1, RISE + 0.03, z - 0.006), edge[0], 0.0065, segments=6)
    rail = [(x, pitch(x) + RAIL + 0.025, z) for x in np.linspace(SX1 - 0.02, x_meet, 30)]
    rail.append((x_meet - 0.10, F2 + 0.02, SZ1 - 0.01))
    k.sweep("foyer_brass", rail, 0.02, 14)
    k.tube("foyer_brass", (SX1 - 0.02, pitch(SX1) + RAIL - 0.08, z), rail[0], 0.02, segments=14)


def runner(k):
    """A runner rug inside the front door: warm grey wool with a charcoal border."""
    (x0, x1), (z0, z1), t = RUNNER["x"], RUNNER["z"], RUNNER["t"]
    rng = np.random.default_rng(15)
    step = 0.04
    nx, nz = round((x1 - x0) / step), round((z1 - z0) / step)
    mottle = _smooth_noise((nx + 1, nz + 1), 6, rng)
    field, border = np.array([0.56, 0.53, 0.49]), np.array([0.17, 0.16, 0.15])
    verts, colors = [], []
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = x0 + (x1 - x0) * i / nx, z0 + (z1 - z0) * j / nz
            verts.append((x, t, z))
            d = min(x - x0, x1 - x, z - z0, z1 - z)
            c = border if d < 0.09 else field * (1 + 0.05 * mottle[i, j])
            colors.append(srgb_to_linear(tuple(np.clip(c, 0, 1))))
    faces = [(i * (nz + 1) + j, i * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j)
             for i in range(nx) for j in range(nz)]
    k.b.mesh(G, "foyer_albedo", verts, faces, smooth=False, colors=colors)
    edge = srgb_to_linear(tuple(border))
    for a, c in (((x1, z0), (x0, z0)), ((x0, z0), (x0, z1)), ((x0, z1), (x1, z1)), ((x1, z1), (x1, z0))):
        k.b.mesh(G, "foyer_albedo", [(a[0], 0.0, a[1]), (c[0], 0.0, c[1]), (c[0], t, c[1]), (a[0], t, a[1])], [(0, 1, 2, 3)],
                 colors=[edge] * 4)


# ---- the plinth -------------------------------------------------------------------------------------
def plinth(k):
    """The plinth, empty for now: a block of pale stone on a black shadow gap. Its faces
    are fine grids, so the spots' pool of light on top comes out smooth."""
    x, z, w, h = PLINTH["x"], PLINTH["z"], PLINTH["w"], PLINTH["h"]
    world = Frame((0.0, 0.0, 0.0))
    g = 0.035
    k.block("foyer_black", world, (x - w / 2 + g, 0.0, z - w / 2 + g), (x + w / 2 - g, 0.045, z + w / 2 - g), step=0.2, skip=("-y", "+y"))
    k.block("plinth_stone", world, (x - w / 2, 0.045, z - w / 2), (x + w / 2, h, z + w / 2), step=0.05)


# ---- the console and the painting ------------------------------------------------------------------
def stone_frame(z):
    """A frame on the dark stone wall's lining: +z out into the foyer, +x to the right as
    you face the wall."""
    return Frame((XE - LINING - 0.002, 0.0, z), -90.0)


def console(k):
    """A pale oak console: a thick top on two slab legs, a shelf low down with books on
    it. On top, a ceramic lamp, a wide bowl for keys (a set in it), and a vase of dried
    branches."""
    f = stone_frame(CONSOLE["z"])
    L, D, Hc = CONSOLE["L"], CONSOLE["D"], CONSOLE["H"]
    x0, x1 = -L / 2, L / 2
    t = 0.045
    k.grain("foyer_oak", f, (x0, Hc - t, 0.0), (x1, Hc, D), step=0.07, skip=("-z",), along="x")
    for xa in (x0 + 0.06, x1 - 0.06 - t):
        k.grain("foyer_oak", f, (xa, 0.0, 0.02), (xa + t, Hc - t, D - 0.02), step=0.07, skip=("-z", "-y", "+y"), along="y")
    k.grain("foyer_oak", f, (x0 + 0.06 + t, 0.14, 0.03), (x1 - 0.06 - t, 0.17, D - 0.03), step=0.07, skip=("-z",), along="x")
    # on the shelf: two stacks of books
    for xs, yaw, mats in ((-0.38, 3.0, ("book_charcoal", "book_cream", "book_olive")), (0.30, -4.0, ("book_navy", "book_rust"))):
        y = 0.17
        for j, mat in enumerate(mats):
            th = 0.03 + 0.008 * (j % 2)
            book_flat(k, Frame(f((xs, y, D / 2)), f.yaw + yaw + 5 * j), (0.0, 0.0), (0.30 - 0.03 * j, th, 0.22 - 0.02 * j), mat)
            y += th
    # the lamp, on the left
    lf = Frame(f((x0 + 0.30, Hc, D * 0.52)))
    k.lathe("foyer_ceramic", lf, [(0.0, 0.0), (0.05, 0.0), (0.09, 0.03), (0.105, 0.10), (0.095, 0.17), (0.05, 0.24),
                                  (0.022, 0.29), (0.022, 0.33), (0.0, 0.33)], 40)
    k.tube("foyer_brass", lf((0.0, 0.33, 0.0)), lf((0.0, 0.45, 0.0)), 0.006, segments=8)
    y0, y1, r = 0.35, 0.56, 0.17
    k.lathe("foyer_shade", lf, [(r, y0), (r * 0.93, y1)], 48)
    k.lathe("foyer_shade", lf, [(r * 0.93 - 0.004, y1), (r - 0.004, y0)], 48)
    k.disc("light_warm", lf, (0.0, y0 + 0.05, 0.0), r - 0.03, 32, down=True)
    p = lf((0.0, 0.0, 0.0))
    LAMPS.append(dict(name="console_lamp_down", pos=(p[0], p[1] + y0 + 0.03, p[2]), size=(0.24, 0.24), watts=18.0, aim=(0.0, -1.0, 0.0)))
    LAMPS.append(dict(name="console_lamp_up", pos=(p[0], p[1] + y1 - 0.03, p[2]), size=(0.24, 0.24), watts=10.0, aim=(0.0, 1.0, 0.0)))
    LAMPS.append(dict(name="console_lamp_glow", kind="point", pos=(p[0], p[1] + (y0 + y1) / 2, p[2]), watts=5.0, radius=0.10))
    # the bowl, with a set of keys in it
    bf = Frame(f((0.12, Hc, D * 0.50)))
    k.lathe("foyer_bowl", bf, [(0.0, 0.0), (0.06, 0.0), (0.15, 0.045), (0.175, 0.07), (0.168, 0.072), (0.142, 0.05),
                               (0.055, 0.012), (0.0, 0.010)], 44)
    kc = np.array(bf((0.03, 0.016, 0.01)))
    k.sweep("foyer_brass", [tuple(kc + (0.018 * math.cos(a), 0.0, 0.018 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 21)],
            0.0015, 6, caps=False)
    k.soft("foyer_black", Frame(tuple(kc + (0.045, 0.004, 0.012)), 30.0), (0.0, 0.0, 0.0), (0.055, 0.010, 0.030), 0.006, n=2)
    # a tall vase of dried branches on the right
    vf = Frame(f((x1 - 0.24, Hc, D * 0.48)))
    k.lathe("foyer_ceramic_dark", vf, [(0.0, 0.0), (0.06, 0.0), (0.085, 0.06), (0.09, 0.16), (0.06, 0.28), (0.035, 0.36),
                                       (0.04, 0.38), (0.034, 0.38), (0.0, 0.37)], 36)
    rng = np.random.default_rng(4)
    for _ in range(7):
        base = np.array(vf((rng.normal(0, 0.01), 0.36, rng.normal(0, 0.01))))
        d = np.array((rng.normal(0, 0.28), 1.0, rng.normal(0, 0.28)))
        d /= np.linalg.norm(d)
        pts, p_ = [tuple(base)], base.copy()
        length = rng.uniform(0.45, 0.75)
        for s in range(8):
            d = d + rng.normal(0, 0.12, 3) * (1, 0.3, 1)
            d /= np.linalg.norm(d)
            p_ = p_ + d * length / 8
            pts.append(tuple(p_))
        k.sweep("foyer_branch", pts, [0.004, 0.003, 0.0015], 6)
        for s in range(3, 8, 2):                     # short twigs
            q = np.array(pts[s])
            tip = q + np.array((rng.normal(0, 0.06), rng.uniform(0.04, 0.10), rng.normal(0, 0.06)))
            k.sweep("foyer_branch", [tuple(q), tuple(tip)], [0.0018, 0.0008], 5)


def painting(k):
    """An original painting on the stone wall over the console: a gallery-wrapped canvas
    (`paint_painting`), lit by a spot from the ceiling."""
    f = stone_frame(CONSOLE["z"])
    w, h, yc = PAINTING["w"], PAINTING["h"], PAINTING["y"]
    d = 0.035
    x0, x1, y0, y1 = -w / 2, w / 2, yc - h / 2, yc + h / 2
    k.block("foyer_canvas_edge", f, (x0, y0, 0.002), (x1, y1, d - 0.0005), step=0.1, skip=("-z", "+z"))
    v, fc, uv = grid((x0, y0, d), (w, 0, 0), (0, h, 0), 16, 20)
    k.mesh("foyer_painting", f, v, fc, smooth=False, uvs=uv)


def fig(k):
    """A fig (Poly Haven's potted_plant_01, CC0) in a pale stone pot, between the console
    and the door to the study."""
    from .props import load, place
    x, z = FIG
    f = Frame((x, 0.0, z))
    h = 0.48
    k.lathe("foyer_pot", f, [(0.0, 0.0), (0.16, 0.0), (0.19, 0.05), (0.205, h), (0.19, h), (0.19, h - 0.04), (0.0, h - 0.04)], 40)
    plant = load("potted_plant_01", only={"potted_plant_01_leaves", "potted_plant_01_stem"},
                 thin={"potted_plant_01_leaves": 0.25})
    for name, piece in plant.items():
        mat = "foyer_fig_leaves" if name.endswith("leaves") else "foyer_fig_stems"
        place(k.b, G, mat, piece, (x, h - 0.04, z), yaw=1.2, scale=1.8, origin=(0.0, 0.5, 0.0))


# ---- the painting's picture ---------------------------------------------------------------------
def paint_painting(w=384, h=480):
    """An original abstract: a warm sand ground, a low dark ochre band like a far ridge,
    a pale sun disc, and a single charcoal arc sweeping across, in loose brushed layers."""
    rng = np.random.default_rng(33)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    u, v = xx / w, yy / h                                     # v from the bottom
    sand, ochre, rust, pale, char = (np.array(c) for c in ((0.86, 0.79, 0.66), (0.68, 0.48, 0.28), (0.52, 0.28, 0.18),
                                                          (0.95, 0.92, 0.84), (0.15, 0.14, 0.13)))
    noise = _smooth_noise((h, w), 30, rng)
    img = sand * (1 + 0.04 * noise)[..., None]
    # brush texture: soft horizontal strokes
    strokes = _smooth_noise((h, w), 6, rng)
    img *= (1 + 0.02 * np.sin(v * 140 + 4 * strokes))[..., None]
    # the ridge: a band low down, its top edge wandering
    edge = 0.34 + 0.05 * np.sin(u * 5.5 + 1.0) + 0.02 * np.sin(u * 17) + 0.01 * noise
    ridge = np.clip((edge - v) * 40, 0, 1) * np.clip((v - 0.12) * 30, 0, 1)
    img = img * (1 - ridge[..., None]) + (ochre * (1 + 0.06 * strokes)[..., None]) * ridge[..., None]
    low = np.clip((0.12 - v) * 30, 0, 1)
    img = img * (1 - low[..., None]) + rust * low[..., None]
    # the sun
    sun = np.clip((0.11 - np.hypot((u - 0.66) * w / h, v - 0.66)) * 120, 0, 1)
    img = img * (1 - 0.85 * sun[..., None]) + pale * 0.85 * sun[..., None]
    # the arc: one dry charcoal stroke
    r = np.hypot((u - 0.15) * w / h, v - 0.05)
    width = 0.012 + 0.010 * np.clip(1 - u, 0, 1)
    # dry where the brush runs out: the ink thins in soft streaks along the stroke, more toward its end
    streaks = _smooth_noise((h, w), 2, rng)
    ink = np.clip(0.9 - 0.6 * np.clip(streaks, 0, 1) * (0.4 + u), 0, 1)
    arc = np.clip((width - np.abs(r - 0.72)) * 300, 0, 1) * np.clip((v - 0.30) * 40, 0, 1) * ink
    img = img * (1 - arc[..., None]) + char * arc[..., None]
    save_png(picture_path("foyer_painting"), np.clip(img, 0, 1).astype(np.float32))



def vessel(k):
    """A stand-in for the sculpture: a large dark-glazed ceramic vessel on the plinth, wide
    at the shoulder, narrowing to a small lip."""
    x, z, h = PLINTH["x"], PLINTH["z"], PLINTH["h"]
    prof = [(0.0, 0.0), (0.09, 0.0), (0.11, 0.01), (0.16, 0.08), (0.205, 0.22), (0.215, 0.30), (0.20, 0.40), (0.16, 0.50),
            (0.10, 0.57), (0.065, 0.61), (0.06, 0.64), (0.072, 0.655), (0.066, 0.66), (0.052, 0.645), (0.0, 0.60)]
    k.lathe("foyer_vessel", Frame((x, h, z)), prof, 56)
