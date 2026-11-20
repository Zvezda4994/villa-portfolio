"""The garage (Turo), furnished: a clean, bright showroom with two bays. The west bay has
a showroom light rig over it and a car under a fitted charcoal cover, standing in for the
real car until it arrives (`car_cover`: take it out then). By the door to the foyer, a tool
chest under a wall rack of tyres. On the back wall: a key cabinet with the four cars' key
fobs, each modelled on its car's real fob (no logos or badges), with a plain label under
each hook, and a wall screen with a simple booking calendar.

Plan, looking down, seen from the driveway (the kitchen wall at the top, so +x is on
the right):

             key cabinet    kitchen door          screen                 (z = 0)
     +-----------[==]---------[    ]------------[=======]----------------+
     |  EV charger                                                          |
     |     |   ======== wheel stop ==   |   ===== wheel stop =====    |    f
     |     |                            |                             |    o door
     |     |       the car's bay        |          the other bay      |    y
     |     |   (light rig over it)      |                             |    e
     |     |                            |                             |    r
     |                                                         (extinguisher)
     +----[============= garage door, smoked glass ===============]---------+
                                                                          (z = 8)

The fobs and their labels come from data/garage_keys.txt; the calendar's rows are plain
"Car 1" to "Car 4" (CALENDAR_ROWS). Everything is lit per vertex, the walls, the ceiling and the floor laid
over the house's own, so the room stays clean from a quick draft bake; it has no
lightmap.
"""
import math

import numpy as np

from . import config as C
from .house import H1, P
from .kit import Frame, Kit, grid, panel, wall
from .materials import srgb_to_linear
from .study import _smooth_noise
from .textures import picture_path, save_png

ROOM, G = "garage", "ground"
KEYS_FILE = C.ROOT / "data" / "garage_keys.txt"
CALENDAR_ROWS = ["Car 1", "Car 2", "Car 3", "Car 4"]

# The room's inside faces.
XW = -C.HALF_W + C.WALL           # the west wall (-11.7)
XE = -5.0 - P / 2                 # the wall to the foyer, its door from z 3.4 to 4.6 (-5.075)
ZN = P / 2                        # the wall to the kitchen, its door from x -9.5 to -8.3 (0.075)
ZF = C.HALF_D - C.WALL            # the front, the garage door from x -11.2 to -5.8 (7.7)
KITCHEN_DOOR = (-9.5, -8.3)
FOYER_DOOR = (3.4, 4.6)
GARAGE_DOOR = (-11.2, -5.8, 2.7)
LINING = 0.012

BAYS = [(-11.2, -8.5), (-8.5, -5.8)]
CAR_BAY = 0                       # the west bay: the light rig is over it, for the car to come
BAY_Z = (1.10, 7.45)              # how far the bays' lines run, back to front
FLOOR_Y = 0.012                   # the floor's coat, laid just over the house's floor
KEYS_X = -10.60                   # the key cabinet's middle, on the back wall left of the kitchen door
SCREEN_X = -6.69                  # the screen's middle, right of it
SCREEN = (1.43, 0.805, 1.62)      # 65", and the height of its middle
CABINET = dict(w=0.56, h=0.44, d=0.10, y=1.50)

CEILING_LIGHT = 0.45
CEILING_COLOUR = (0.93, 0.96, 1.0)     # a clean neutral white
LED_COLOUR = (0.94, 0.97, 1.0)
LAMPS = []

# Review cameras. The first is also the room's view on the website: just inside the garage
# door, between the bays, looking at the back wall with the key cabinet and the screen.
GARAGE_CAM = dict(pos=(-8.15, 1.60, 7.20), target=(-8.70, 1.12, 0.0), fov=55.0)
KEYS_CAM = dict(pos=(-10.52, 1.52, 1.00), target=(-10.60, 1.50, 0.075), fov=40.0)
SCREEN_CAM = dict(pos=(-6.69, 1.62, 2.15), target=(-6.69, 1.62, 0.075), fov=40.0)


def build_garage(b):
    LAMPS.clear()
    keys = read_keys()
    paint_labels([label for _, label in keys])
    paint_calendar(CALENDAR_ROWS)
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    with b.room(ROOM):
        walls(k)
        floor(k)
        ceiling(Kit(b, "upper", None))
        wheel_stops(k)
        drain(k)
        key_cabinet(k, keys)
        slats(k)
        screen(k)
        charger(k)
        extinguisher(k)
        car_cover(k)
        tool_chest(k)
        tyre_rack(k)


def read_keys():
    """The four keys, left to right: (fob shape, label lines)."""
    keys = []
    for ln in KEYS_FILE.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        shape, _, label = ln.partition(":")
        shape = shape.strip()
        if shape not in FOBS:
            raise ValueError(f"data/garage_keys.txt: unknown fob {shape!r}; the fobs are {', '.join(FOBS)}")
        keys.append((shape, [part.strip() for part in label.split("|")]))
    if len(keys) != 4:
        raise ValueError(f"data/garage_keys.txt should list four keys, not {len(keys)}")
    return keys


# ---- the room ------------------------------------------------------------------------------------
def walls(k):
    """White plaster linings over the house's walls, lit per vertex on a grid."""
    from .house import DOOR
    e, m = LINING, "plaster_v"
    # the kitchen wall (facing +z), round its door, the slats and the key cabinet (nothing
    # buried behind them: such points bake dark, gotcha 26)
    d0, d1 = KITCHEN_DOOR
    s0, s1 = SLATS["x"]
    cw, ch, cy = CABINET["w"], CABINET["h"], CABINET["y"]
    wall(k, m, (XW, 0.0, ZN + e), (XE - XW, 0, 0), (0, H1, 0), step=0.15,
         holes=[(d0 - XW, d1 - XW, 0.0, DOOR), (s0 - XW, s1 - XW, 0.0, H1),
                (KEYS_X - cw / 2 - XW, KEYS_X + cw / 2 - XW, cy - ch / 2, cy + ch / 2)])
    # the foyer wall (facing -x), round its door
    f0, f1 = FOYER_DOOR
    wall(k, m, (XE - e, 0.0, ZN), (0, 0, ZF - ZN), (0, H1, 0), step=0.15, holes=[(f0 - ZN, f1 - ZN, 0.0, DOOR)])
    # the west wall (facing +x)
    panel(k, m, (XW + e, 0.0, ZF), (0, 0, ZN - ZF), (0, H1, 0), step=0.15)
    # the front, round the garage door (facing -z)
    g0, g1, gh = GARAGE_DOOR
    wall(k, m, (XE, 0.0, ZF - e), (XW - XE, 0, 0), (0, H1, 0), step=0.15, holes=[(XE - g1, XE - g0, 0.0, gh)])


def floor(k):
    """A pale grey resin floor laid over the house's dark one, very slightly mottled, with
    white lines marking the two bays. Painted per vertex."""
    rng = np.random.default_rng(17)
    x0, x1, z0, z1 = XW, XE, ZN, ZF
    step = 0.10
    nx, nz = round((x1 - x0) / step), round((z1 - z0) / step)
    mottle = _smooth_noise((nx + 1, nz + 1), 8, rng)
    base = np.array([0.62, 0.62, 0.61])
    verts, colors = [], []
    for i in range(nx + 1):
        for j in range(nz + 1):
            verts.append((x0 + (x1 - x0) * i / nx, FLOOR_Y, z0 + (z1 - z0) * j / nz))
            colors.append(srgb_to_linear(tuple(np.clip(base * (1 + 0.03 * mottle[i, j]), 0, 1))))
    faces = [(i * (nz + 1) + j, i * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j)
             for i in range(nx) for j in range(nz)]
    k.b.mesh(G, "garage_albedo", verts, faces, smooth=False, colors=colors)
    # the bays' lines: down each side, and across the back of each bay
    white = srgb_to_linear((0.93, 0.93, 0.91))
    w = 0.08
    lines = [(x - w / 2, x + w / 2, BAY_Z[0], BAY_Z[1]) for x in (BAYS[0][0], BAYS[0][1], BAYS[1][1])]
    lines += [(a + w / 2, c - w / 2, BAY_Z[0], BAY_Z[0] + w) for a, c in BAYS]
    for a, c, za, zb in lines:
        v, fc, _ = grid((a, FLOOR_Y + 0.001, zb), (c - a, 0, 0), (0, 0, za - zb), max(1, round((c - a) / 0.1)),
                        max(1, round((zb - za) / 0.1)))
        k.b.mesh(G, "garage_albedo", v, fc, smooth=False, colors=[white] * len(v))


def ceiling(k):
    """The ceiling lined in white plaster (it lifts off with the upstairs floor), with
    long LED lines along the bays: three over the car's bay, framed by a rectangle of LED
    channel and four spots aimed where its flanks will be; two over the other."""
    y = H1 - 0.014
    panel(k, "plaster_v", (XW, y, ZN), (XE - XW, 0, 0), (0, 0, ZF - ZN), step=0.25)
    z0, z1 = BAY_Z[0] + 0.3, BAY_Z[1] - 0.45
    for bi, (a, c) in enumerate(BAYS):
        cx = (a + c) / 2
        offsets = (-0.85, 0.0, 0.85) if bi == CAR_BAY else (-0.70, 0.70)
        for dx in offsets:
            led_line(k, (cx + dx, y, z0), (cx + dx, y, z1), name=f"bay{bi}_{dx:+.2f}", watts=52.0 if bi == CAR_BAY else 60.0)
        if bi == CAR_BAY:
            # the showroom rectangle round the car's bay, and four spots for the car
            hx, za, zb = 1.20, z0 - 0.35, z1 + 0.35
            for p0, p1 in (((cx - hx, za), (cx + hx, za)), ((cx + hx, za), (cx + hx, zb)), ((cx + hx, zb), (cx - hx, zb)),
                           ((cx - hx, zb), (cx - hx, za))):
                led_line(k, (p0[0], y, p0[1]), (p1[0], y, p1[1]), width=0.03, lamp=False)
            for sx in (-1, 1):
                for zz in (2.6, 5.9):
                    pos = (cx + sx * 1.55, y - 0.01, zz)
                    aim = (cx + sx * 0.75, 0.65, zz)
                    can(k, pos)
                    LAMPS.append(dict(name=f"car_spot_{sx:+d}_{zz:.0f}", kind="spot", pos=(pos[0], pos[1] - 0.06, pos[2]),
                                      aim=tuple(np.subtract(aim, pos)), watts=32.0, cone=46.0, colour=LED_COLOUR))


def led_line(k, p0, p1, name=None, watts=0.0, width=0.06, lamp=True):
    """A slim LED line set in the ceiling: a dark-edged channel with a glowing diffuser."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    d /= L
    s = np.array((-d[2], 0.0, d[0]))
    y = p0[1]
    for off, wd, mat, dy in ((0.0, width + 0.03, "steel_black", -0.001), (0.0, width, "garage_led", -0.002)):
        a, c = s * (wd / 2), d * L
        q = [p0 - a + (0, dy, 0), p0 + a + (0, dy, 0), p0 + a + c + (0, dy, 0), p0 - a + c + (0, dy, 0)]
        n = np.cross(q[1] - q[0], q[2] - q[1])
        if n[1] > 0:
            q = q[::-1]
        k.b.quad(k.g, mat, [tuple(v) for v in q])
    if lamp:
        mid = (p0 + p1) / 2
        LAMPS.append(dict(name=f"led_{name}", pos=(mid[0], y - 0.03, mid[2]),
                          size=(width + 0.06, L) if abs(d[2]) > abs(d[0]) else (L, width + 0.06),
                          watts=watts, aim=(0.0, -1.0, 0.0), colour=LED_COLOUR))


def can(k, pos):
    """A small black downlight can set in the ceiling, with its glowing lens."""
    x, y, z = pos
    k.tube("steel_black", (x, y + 0.005, z), (x, y - 0.035, z), 0.045, segments=20, step=0.02)
    k.disc("garage_led", Frame((x, y - 0.0355, z)), (0.0, 0.0, 0.0), 0.032, 20, down=True)


def wheel_stops(k):
    """A low black rubber wheel stop at the back of each bay, with two white bands."""
    world = Frame((0.0, 0.0, 0.0))
    z = BAY_Z[0] + 0.42
    for a, c in BAYS:
        cx = (a + c) / 2
        k.soft("garage_rubber", world, (cx, FLOOR_Y + 0.05, z), (1.70, 0.10, 0.15), 0.025, n=2)
        for sx in (-1, 1):
            k.soft("garage_white", world, (cx + sx * 0.55, FLOOR_Y + 0.05, z), (0.12, 0.102, 0.152), 0.025, n=2)


def drain(k):
    """A stainless slot drain across the front, just inside the garage door."""
    g0, g1, _ = GARAGE_DOOR
    world = Frame((0.0, 0.0, 0.0))
    z0, z1 = ZF - 0.32, ZF - 0.22
    k.block("steel_brushed", world, (g0 + 0.2, FLOOR_Y - 0.004, z0), (g1 - 0.2, FLOOR_Y + 0.002, z1), step=0.2, skip=("-y",))
    n = int((g1 - g0 - 0.4) / 0.045)
    for i in range(n):
        x = g0 + 0.2 + 0.03 + i * 0.045
        k.b.quad(G, "steel_black", [(x, FLOOR_Y + 0.0025, z1 - 0.02), (x + 0.012, FLOOR_Y + 0.0025, z1 - 0.02),
                                    (x + 0.012, FLOOR_Y + 0.0025, z0 + 0.02), (x, FLOOR_Y + 0.0025, z0 + 0.02)])


# ---- the keys ------------------------------------------------------------------------------------
def back_frame(x):
    """A frame on the kitchen wall's lining: +z out into the garage, +x to the right."""
    return Frame((x, 0.0, ZN + LINING), 0.0)


def key_cabinet(k, keys):
    """A white lacquered key cabinet with a glass door in a thin black frame. Inside, on
    an oak back, four brass hooks, each with a ring and its car's fob, and a small white
    label under each hook naming the car."""
    f = back_frame(KEYS_X)
    W, Hc, D, yc = CABINET["w"], CABINET["h"], CABINET["d"], CABINET["y"]
    x0, x1, y0, y1 = -W / 2, W / 2, yc - Hc / 2, yc + Hc / 2
    t = 0.02
    # the box: sides, top, bottom, and an oak back inside
    for lo, hi in (((x0, y0, 0.0), (x0 + t, y1, D)), ((x1 - t, y0, 0.0), (x1, y1, D)),
                   ((x0 + t, y0, 0.0), (x1 - t, y0 + t, D)), ((x0 + t, y1 - t, 0.0), (x1 - t, y1, D))):
        k.block("garage_white", f, lo, hi, step=0.05, skip=("-z",))
    k.block("oak_light", f, (x0 + t, y0 + t, 0.0), (x1 - t, y1 - t, 0.012), step=0.04, skip=("-z", "-x", "+x", "-y", "+y"))
    # the door: glass in a thin black frame, closed
    fz = D + 0.002
    for lo, hi in (((x0, y0, D), (x0 + 0.012, y1, fz + 0.016)), ((x1 - 0.012, y0, D), (x1, y1, fz + 0.016)),
                   ((x0 + 0.012, y0, D), (x1 - 0.012, y0 + 0.012, fz + 0.016)), ((x0 + 0.012, y1 - 0.012, D), (x1 - 0.012, y1, fz + 0.016))):
        k.block("steel_black", f, lo, hi, step=0.1, skip=("-z",))
    k.quad("garage_glass", f, [(x0 + 0.012, y0 + 0.012, fz + 0.008), (x1 - 0.012, y0 + 0.012, fz + 0.008),
                               (x1 - 0.012, y1 - 0.012, fz + 0.008), (x0 + 0.012, y1 - 0.012, fz + 0.008)])
    k.soft("steel_black", f, (x1 - 0.035, yc, fz + 0.03), (0.010, 0.14, 0.012), 0.004, n=1)
    # a small brass plate over the hooks, and the oak rail they're on
    k.block("oak_light", f, (x0 + t, yc + 0.02, 0.012), (x1 - t, yc + 0.08, 0.03), step=0.05, skip=("-z",))
    rng = np.random.default_rng(9)
    for i, (shape, _) in enumerate(keys):
        hx = -0.195 + 0.13 * i
        hy = yc + 0.04
        # the hook: out from the rail, turned up at its tip
        k.sweep("brass", [f((hx, hy, 0.03)), f((hx, hy, 0.058)), f((hx, hy + 0.004, 0.064)), f((hx, hy + 0.016, 0.066))], 0.0028, 8)
        # the ring, hanging on it, parallel to the wall
        rr = 0.016
        rc = (hx, hy - rr + 0.002, 0.052)
        k.sweep("steel_brushed", [f((rc[0] + rr * math.sin(a), rc[1] + rr * math.cos(a), rc[2])) for a in np.linspace(0, 2 * math.pi, 25)],
                0.0016, 8, caps=False)
        bottom = rc[1] - rr
        # the fob, on a small steel loop through the ring, turned a little on it
        g = Frame(f((hx, bottom - 0.004, rc[2])), f.yaw + rng.uniform(-6, 6))
        k.sweep("steel_brushed", [g((0.0, 0.0035 + 0.0045 * math.cos(a), 0.0045 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 17)],
                0.0011, 6, caps=False)
        FOBS[shape](k, Frame(g((0.0, -0.0045, 0.0)), g.yaw))
        label(k, f, (hx, LABEL_Y - CABINET["y"] + yc, 0.012), i)
    # the cabinet's own little light, inside its top
    LAMPS.append(dict(name="key_cabinet_light", pos=f((0.0, y1 - t - 0.01, D * 0.6)), size=(W - 0.08, D - 0.03), watts=2.5,
                      aim=(0.0, -1.0, 0.0), colour=(1.0, 0.92, 0.82)))
    k.quad("garage_led", f, [(x0 + t + 0.02, y1 - t - 0.001, D * 0.75), (x1 - t - 0.02, y1 - t - 0.001, D * 0.75),
                             (x1 - t - 0.02, y1 - t - 0.001, D * 0.85), (x0 + t + 0.02, y1 - t - 0.001, D * 0.85)])


LABEL = (0.112, 0.028)            # a hook's label: width and height (the same shape as its picture)
LABEL_Y = 1.35                    # its middle's height, under the hanging fobs


def label(k, f, centre, i):
    """A small white label on the cabinet's oak back, its car printed on it (cell i of the
    labels' picture)."""
    w, h = LABEL
    x, y, z = centre
    k.soft("garage_white", f, (x, y, z + 0.0010), (w, h, 0.0020), 0.0006, n=1)
    # the printed face stands 1 mm proud of the plate: any closer and the two flicker
    v, fc, uv = grid((x - w / 2 + 0.002, y - h / 2 + 0.002, z + 0.0030), (w - 0.004, 0, 0), (0, h - 0.004, 0), 4, 2)
    u0, u1 = i / 4, (i + 1) / 4
    uv = [[(u0 + (u1 - u0) * a, b_) for a, b_ in face] for face in uv]
    k.mesh("garage_tags", f, v, fc, smooth=False, uvs=uv)


# ---- the fobs -------------------------------------------------------------------------------------
# Each is built in a frame whose origin is the top of the fob, hanging straight down (-y), its
# face out into the room (+z). Shapes after the cars' real fobs, with every logo and badge left
# off. Sizes in metres.
def _outline_rr(w, h, r, n=5):
    """A rounded rectangle's outline, its top edge at y = 0, anticlockwise from the front."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -h + r, -90), (w / 2 - r, -r, 0), (-w / 2 + r, -r, 90), (-w / 2 + r, -h + r, 180)):
        for j in range(n + 1):
            a = math.radians(a0 + 90 * j / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _outline_oval(w, h, e=2.6, n=36):
    """A rounded oval (a superellipse, exponent e), its top at y = 0, anticlockwise."""
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n - math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        pts.append((w / 2 * math.copysign(abs(c) ** (2 / e), c), -h / 2 + h / 2 * math.copysign(abs(s_) ** (2 / e), s_)))
    return pts


def _outline_shield(w, h, n=10):
    """A shield, anticlockwise: a straight top with softened corners, straight sides for
    the upper half, then curving in to a point at the bottom."""
    side = 0.52 * h                      # how far down the sides run straight
    r = 0.07 * w
    right = []                           # from the point up the right side
    for j in range(n + 1):
        t = 1 - j / n
        a, c, b = (w / 2, -side), (w / 2, -side - 0.40 * (h - side)), (0.0, -h)
        right.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
                      (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]))
    pts = right[:]
    for j in range(4):                   # the top right corner
        a = math.radians(0 + 90 * j / 3)
        pts.append((w / 2 - r + r * math.cos(a), -r + r * math.sin(a)))
    for j in range(4):                   # the top left corner
        a = math.radians(90 + 90 * j / 3)
        pts.append((-w / 2 + r + r * math.cos(a), -r + r * math.sin(a)))
    pts += [(-x, y) for x, y in reversed(right[1:])]
    return pts


def _slab(k, g, outline, rings, front, back):
    """Extrude an outline into a solid: `rings` are (scale about the outline's middle, z,
    material of the band from the previous ring to this one), back to front; the back and
    front faces are fans in their own materials. Faces are turned to point outward."""
    P = np.asarray(outline, float)
    mid = P.mean(axis=0)
    n = len(P)
    lay = [[(mid[0] + (x - mid[0]) * sc, mid[1] + (y - mid[1]) * sc, z) for x, y in P] for sc, z, _ in rings]
    zc = 0.5 * (rings[0][1] + rings[-1][1])
    centre = np.array([mid[0], mid[1], zc])

    def out(verts, faces):
        fixed = []
        for q in faces:
            p = [np.asarray(verts[i], float) for i in q]
            nrm = np.cross(p[1] - p[0], p[2] - p[0])
            if np.linalg.norm(nrm) < 1e-14 and len(p) > 3:
                nrm = np.cross(p[2] - p[0], p[3] - p[0])
            fixed.append(q if np.dot(nrm, sum(p) / len(p) - centre) >= 0 else q[::-1])
        return fixed
    for (sc, z, mat), a, b in zip(rings[1:], lay[:-1], lay[1:]):
        verts = a + b
        faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        k.mesh(mat, g, verts, out(verts, faces), smooth=True)
    # the back and the front: concentric rings in to a middle point, so the light baked at
    # the points shades across them evenly instead of in a fan
    for ring, mat in ((lay[0], back), (lay[-1], front)):
        z = ring[0][2]
        steps = [1.0, 0.72, 0.44, 0.18]
        verts = [(mid[0] + (x - mid[0]) * f_, mid[1] + (y - mid[1]) * f_, z) for f_ in steps for x, y, _ in ring]
        faces = [(a * n + i, a * n + (i + 1) % n, (a + 1) * n + (i + 1) % n, (a + 1) * n + i)
                 for a in range(len(steps) - 1) for i in range(n)]
        c = len(verts)
        verts.append((mid[0], mid[1], z))
        last = (len(steps) - 1) * n
        faces += [(last + i, last + (i + 1) % n, c) for i in range(n)]
        k.mesh(mat, g, verts, out(verts, faces), smooth=False)


def fob_bmw(k, g):
    """The M5's fob: a slim gloss-black slab with rounded corners, a polished band round
    its sides and three buttons down its face."""
    w, h, t = 0.038, 0.072, 0.0125
    o = _outline_rr(w, h, 0.011)
    _slab(k, g, o, [(0.93, -t / 2, None), (1.0, -t / 2 + 0.0015, "garage_fob"), (1.0, -0.0022, "garage_fob"),
                    (1.0, 0.0022, "steel_brushed"), (1.0, t / 2 - 0.0015, "garage_fob"), (0.93, t / 2, "garage_fob")],
          "garage_fob", "garage_fob")
    for y in (-0.024, -0.037, -0.050):
        k.soft("garage_rim", g, (0.0, y, t / 2 - 0.0002), (0.016, 0.0085, 0.0016), 0.0035, n=2)


def fob_aston(k, g):
    """The Vanquish's key: a long, slim block of dark glass held in a polished steel cage,
    with a steel cap at its top and two buttons on its right side."""
    w, h, t = 0.030, 0.082, 0.016
    o = _outline_rr(w, h, 0.006)
    _slab(k, g, o, [(0.94, -t / 2, None), (1.0, -t / 2 + 0.0018, "steel_brushed"), (1.0, t / 2 - 0.0028, "steel_brushed"),
                    (0.97, t / 2 - 0.0012, "garage_fob_glass"), (0.90, t / 2, "garage_fob_glass")],
          "garage_fob_glass", "steel_brushed")
    k.soft("steel_brushed", g, (0.0, -0.006, 0.0), (w + 0.0012, 0.012, t + 0.0012), 0.0035, n=2)
    for y in (-0.030, -0.044):
        k.soft("garage_rim", g, (w / 2 + 0.0004, y, 0.0), (0.0024, 0.009, 0.0065), 0.001, n=1)


def fob_porsche_gt(k, g):
    """The Carrera GT's key: a rounded black head with two buttons on its face, and a fixed
    steel blade below it."""
    w, h, t = 0.034, 0.046, 0.014
    o = _outline_oval(w, h)
    _slab(k, g, o, [(0.84, -t / 2, None), (1.0, -t / 2 + 0.0035, "garage_fob"), (1.0, t / 2 - 0.0035, "garage_fob"),
                    (0.84, t / 2, "garage_fob")], "garage_fob", "garage_fob")
    for y in (-0.017, -0.029):
        k.soft("garage_rim", g, (0.0, y, t / 2 + 0.0002), (0.010, 0.0075, 0.0016), 0.003, n=2)
    # the blade: a flat steel bar with an angled tip, out of a short collar
    k.soft("garage_fob", g, (0.0, -h - 0.002, 0.0), (0.014, 0.008, 0.0075), 0.0025, n=2)
    bw, bl, bt = 0.0085, 0.058, 0.0026
    blade = [(bw / 2, 0.0), (-bw / 2, 0.0), (-bw / 2, -bl + 0.004), (0.0, -bl), (bw / 2, -bl + 0.009)]
    b = Frame(g((0.0, -h - 0.005, 0.0)), g.yaw)
    _slab(k, b, blade, [(1.0, -bt / 2, None), (1.0, bt / 2, "steel_brushed")], "steel_brushed", "steel_brushed")
    k.soft("garage_rim", b, (0.0, -0.028, bt / 2), (0.0022, 0.040, 0.0006), 0.0003, n=1)


def fob_ferrari(k, g):
    """The 296 GTB's key, shaped like a shield: red, a polished bezel round its plain face."""
    w, h, t = 0.036, 0.050, 0.013
    o = _outline_shield(w, h)
    _slab(k, g, o, [(0.90, -t / 2, None), (1.0, -t / 2 + 0.0025, "garage_red"), (1.0, t / 2 - 0.0028, "garage_red"),
                    (0.97, t / 2 - 0.0010, "steel_brushed"), (0.90, t / 2, "steel_brushed")],
          "garage_red", "garage_red")


FOBS = {"bmw": fob_bmw, "aston": fob_aston, "porsche_gt": fob_porsche_gt, "ferrari": fob_ferrari}


# ---- the screen ----------------------------------------------------------------------------------
SLATS = dict(x=(-8.05, -5.33), depth=0.03, w=0.045, gap=0.022)


def slats(k):
    """A wall of vertical pale oak slats on a dark backing behind the screen, floor to
    ceiling: the one warm surface in the white room."""
    f = back_frame(0.0)
    (x0, x1), d, w, gap = SLATS["x"], SLATS["depth"], SLATS["w"], SLATS["gap"]
    k.block("garage_black", f, (x0, 0.0, 0.0), (x1, H1, 0.006), step=0.2, skip=("-z", "-y", "+y"))
    n = int((x1 - x0 + gap) / (w + gap))
    start = x0 + ((x1 - x0) - (n * w + (n - 1) * gap)) / 2
    for i in range(n):
        a = start + i * (w + gap)
        k.block("oak_light", f, (a, 0.0, 0.006), (a + w, H1 - 0.002, d), step=0.25, skip=("-z", "-y", "+y"))


def screen(k):
    """A 65-inch screen on the slats, a slim black bezel, the booking calendar on it."""
    f = Frame((SCREEN_X, 0.0, ZN + LINING + SLATS["depth"]), 0.0)
    sw, sh, yc = SCREEN
    k.soft("garage_black", f, (0.0, yc, 0.020), (sw + 0.016, sh + 0.016, 0.028), 0.004, n=2)
    v, fc, uv = grid((-sw / 2, yc - sh / 2, 0.0345), (sw, 0, 0), (0, sh, 0), 16, 9)
    k.mesh("garage_screen", f, v, fc, smooth=False, uvs=uv)
    LAMPS.append(dict(name="screen_glow", pos=f((0.0, yc, 0.30)), size=(sw * 0.9, sh * 0.9), watts=4.0,
                      aim=(0.0, 0.0, 1.0), colour=(0.80, 0.88, 1.0)))


# ---- the charger and the extinguisher -----------------------------------------------------------
def charger(k):
    """A wall charger for the car to come, on the west wall by its bay: a white box with a
    dark face and a green light, its cable coiled on a hook below and the plug in its holster."""
    f = Frame((XW + LINING, 0.0, 2.35), 90.0)          # +z out into the garage, +x toward the front
    k.soft("garage_white", f, (0.0, 1.30, 0.05), (0.24, 0.34, 0.10), 0.02, n=3)
    k.soft("garage_black", f, (0.0, 1.32, 0.10), (0.18, 0.24, 0.004), 0.01, n=2)
    k.soft("garage_green", f, (0.0, 1.41, 0.103), (0.08, 0.008, 0.003), 0.002, n=1)
    LAMPS.append(dict(name="charger_led", kind="point", pos=f((0.0, 1.41, 0.13)), watts=0.15, radius=0.01, colour=(0.4, 1.0, 0.55)))
    # the hook and the holster
    k.soft("garage_black", f, (0.0, 0.92, 0.05), (0.10, 0.03, 0.10), 0.008, n=2)
    k.soft("garage_black", f, (0.20, 1.02, 0.06), (0.07, 0.12, 0.09), 0.01, n=2)
    # the cable: down from the box, three loops over the hook, then up to the plug
    path = [f((0.0, 1.13, 0.06)), f((0.0, 1.05, 0.08))]
    for loop in range(3):
        r = 0.14 + 0.01 * loop
        for a in np.linspace(0, 2 * math.pi, 22, endpoint=False):
            path.append(f((r * math.sin(a) * 0.9, 0.93 - r + r * math.cos(a) - 0.0 * loop, 0.09 + 0.012 * loop + 0.004 * math.sin(a))))
    path += [f((0.10, 0.90, 0.13)), f((0.18, 0.95, 0.10)), f((0.20, 1.00, 0.08))]
    k.sweep("garage_cable", path, 0.0085, 8)


def extinguisher(k):
    """A red fire extinguisher on a bracket by the door to the foyer."""
    f = Frame((XE - LINING, 0.0, FOYER_DOOR[1] + 0.45), -90.0)
    g = Frame(f((0.0, 0.62, 0.10)))
    k.soft("steel_black", f, (0.0, 0.95, 0.012), (0.10, 0.12, 0.024), 0.004, n=1)
    k.lathe("garage_red", g, [(0.0, 0.0), (0.07, 0.0), (0.075, 0.02), (0.075, 0.40), (0.06, 0.46), (0.025, 0.49), (0.0, 0.49)], 32)
    k.lathe("steel_black", g, [(0.0, 0.49), (0.02, 0.49), (0.02, 0.56), (0.0, 0.56)], 12)
    k.soft("steel_black", Frame(g((0.0, 0.565, 0.0)), f.yaw), (0.03, 0.0, 0.0), (0.10, 0.012, 0.025), 0.004, n=1)
    k.sweep("steel_black", [g((0.02, 0.53, 0.0)), g((0.07, 0.50, 0.02)), g((0.09, 0.35, 0.04)), g((0.085, 0.20, 0.05))], 0.008, 8)


# ---- pictures -------------------------------------------------------------------------------------
def paint_labels(labels, cell=(512, 128)):
    """The four hooks' labels side by side: white, the car in plain black type, the make
    over the model when the line in data/garage_keys.txt splits them with "|"."""
    from .labels import text_mask
    cw, ch = cell
    w, h = cw * 4, ch
    img = np.ones((h, w, 3)) * np.array([0.95, 0.95, 0.94])
    lines = []
    for i, parts in enumerate(labels):
        rows = [(0.56, 0.37), (0.11, 0.37)] if len(parts) > 1 else [(0.30, 0.46)]
        for text, (y, size) in zip(parts[:2], rows):
            size = min(size, 0.92 * cw / (0.56 * ch * max(1, len(text))))     # fitted to the label
            lines.append((text, (i + 0.5) / 4, y, size, "CENTER", 1.05))
    mask = text_mask((w, h), lines)
    img = img * (1 - mask[..., None]) + np.array([0.06, 0.06, 0.07]) * mask[..., None]
    save_png(picture_path("garage_tags"), np.clip(img, 0, 1).astype(np.float32))


def paint_calendar(names, w=1024, h=576):
    """The booking calendar on the wall screen, dark: a header with the month, a row per
    car and a column per day for two weeks, bookings as rounded bars (booked in teal, a
    service in amber), today marked with a thin red line, and a small legend."""
    from .labels import text_mask
    rng = np.random.default_rng(26)
    bg, panel_c, grid_c = np.array([0.075, 0.08, 0.09]), np.array([0.105, 0.11, 0.125]), np.array([0.17, 0.18, 0.20])
    img = np.ones((h, w, 3)) * bg
    left, right, top, bottom = 0.20 * w, 0.965 * w, 0.775 * h, 0.17 * h       # the grid's edges (y from the bottom)
    days = 14
    first = 16                                       # the first day shown: Monday 16 November 2026
    dw = (right - left) / days
    rh = (top - bottom) / 4
    # the grid's panel, weekends a shade lighter, the column and row lines
    img[int(bottom):int(top), int(left):int(right)] = panel_c
    for d in range(days):
        if d % 7 in (5, 6):
            img[int(bottom):int(top), int(left + d * dw):int(left + (d + 1) * dw)] = panel_c * 1.18
    for d in range(days + 1):
        x = int(left + d * dw)
        img[int(bottom):int(top), x:x + 1] = grid_c
    for r in range(5):
        y = int(bottom + r * rh)
        img[y:y + 1, int(0.035 * w):int(right)] = grid_c
    # bookings: (row, first day index, length, kind)
    bookings = [(0, 0, 3, "b"), (0, 4, 5, "b"), (0, 10, 4, "b"), (1, 1, 2, "s"), (1, 4, 7, "b"), (2, 0, 6, "b"),
                (2, 7, 2, "b"), (2, 11, 3, "b"), (3, 2, 4, "b"), (3, 7, 1, "s"), (3, 9, 5, "b")]
    teal, amber = np.array([0.16, 0.62, 0.60]), np.array([0.90, 0.62, 0.20])
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    for row, d0, n, kind in bookings:
        rowi = 3 - row                                # the first car on the top row
        x0, x1 = left + d0 * dw + 4, left + (d0 + n) * dw - 4
        y0, y1 = bottom + rowi * rh + rh * 0.22, bottom + rowi * rh + rh * 0.78
        r = (y1 - y0) / 2
        cx = np.clip(xx, x0 + r, x1 - r)
        inside = np.hypot(xx - cx, yy - (y0 + y1) / 2) < r
        img[inside] = teal if kind == "b" else amber
    # today: Thursday the 19th
    tx = int(left + 3.5 * dw)
    img[int(bottom) - 4:int(top) + 6, tx - 1:tx + 2] = np.array([0.92, 0.25, 0.22])
    # the text: the title and the month, weekday letters over the day numbers, the cars' names
    white, grey = np.array([0.93, 0.93, 0.94]), np.array([0.58, 0.60, 0.64])
    lines_w = [("Bookings", 0.035, 0.885, 0.058, "LEFT", 1.0)]
    lines_g = [("November 2026", 0.965, 0.89, 0.040, "RIGHT", 1.0)]
    for d in range(days):
        cx = (left + (d + 0.5) * dw) / w
        lines_g.append(("MTWTFSS"[d % 7], cx, 0.835, 0.026, "CENTER", 1.0))
        lines_w.append((str(first + d), cx, 0.789, 0.032, "CENTER", 1.0))
    for r, name in enumerate(names):
        y = (bottom + (3 - r) * rh + rh * 0.36) / h
        lines_w.append((name, 0.035, y, 0.040, "LEFT", 1.0))
    lines_g.append(("Booked", 0.235, 0.060, 0.032, "LEFT", 1.0))
    lines_g.append(("Service", 0.385, 0.060, 0.032, "LEFT", 1.0))
    lines_g.append(("Today", 0.535, 0.060, 0.032, "LEFT", 1.0))
    mw = text_mask((w, h), lines_w)
    mg = text_mask((w, h), lines_g)
    img = img * (1 - mg[..., None]) + grey * mg[..., None]
    img = img * (1 - mw[..., None]) + white * mw[..., None]
    # the legend's swatches
    for x, c in ((0.20, teal), (0.35, amber)):
        x0, y0 = int(x * w), int(0.062 * h)
        img[y0:y0 + 14, x0:x0 + 26] = c
    lx, ly = int(0.50 * w), int(0.062 * h)
    img[ly - 2:ly + 18, lx + 12:lx + 15] = np.array([0.92, 0.25, 0.22])
    img *= (1 + 0.01 * rng.standard_normal((h, w)))[..., None]
    save_png(picture_path("garage_calendar"), np.clip(img, 0, 1).astype(np.float32))


# ---- the covered car, the tool chest, the tyres --------------------------------------------------
CAR = dict(x=-9.85, z=4.05, L=4.80, W=1.86, hem=0.30, wheelbase=2.84, track=1.60)


def _facing(verts, faces, want):
    out = []
    for q in faces:
        p = [np.asarray(verts[i], float) for i in q]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if len(p) > 3 and np.linalg.norm(n) < 1e-12:
            n = np.cross(p[2] - p[0], p[3] - p[0])
        c = sum(p) / len(p)
        out.append(q if np.dot(n, want(c)) >= 0 else q[::-1])
    return out


def tyre(k, centre, axis, r_out=0.33, width=0.225, r_in=0.22, rim=None, segments=40):
    """A tyre standing on its tread, its axle along the world vector `axis`: a rounded
    tread and sidewalls round a hole, with a dark rim filling the hole if `rim` names one."""
    c, ax = np.asarray(centre, float), np.asarray(axis, float)
    ax /= np.linalg.norm(ax)
    e1 = np.cross(ax, (0.0, 1.0, 0.0)) if abs(ax[1]) < 0.9 else np.cross(ax, (1.0, 0.0, 0.0))
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    hw, b = width / 2, 0.035
    prof = [(r_in, -hw + 0.01), (r_out - b, -hw), (r_out - 0.008, -hw + 0.012), (r_out, -hw + b), (r_out, hw - b),
            (r_out - 0.008, hw - 0.012), (r_out - b, hw), (r_in, hw - 0.01)]
    m = len(prof)
    verts = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        d = math.cos(a) * e1 + math.sin(a) * e2
        verts += [tuple(c + d * rad + ax * axl) for rad, axl in prof]
    faces = []
    for i in range(segments):
        for j in range(m):
            a, b_ = i * m + j, ((i + 1) % segments) * m + j
            faces.append((a, b_, ((i + 1) % segments) * m + (j + 1) % m, i * m + (j + 1) % m))
    rmid = (r_in + r_out) / 2

    def want(p):
        v = np.asarray(p) - c
        axl = np.dot(v, ax)
        rv = v - ax * axl
        rl = np.linalg.norm(rv) or 1.0
        return rv / rl * (rl - rmid) + ax * axl
    k.b.mesh(k.g, "garage_rubber", verts, _facing(verts, faces, want), smooth=True)
    if rim:
        for s in (-1, 1):
            ring = [tuple(c + (math.cos(a) * e1 + math.sin(a) * e2) * (r_in + 0.002) + ax * s * (hw - 0.03))
                    for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
            v = [tuple(c + ax * s * (hw - 0.045))] + ring
            fc = [(0, 1 + i, 1 + (i + 1) % 32) for i in range(32)]
            k.b.mesh(k.g, rim, v, _facing(v, fc, lambda p, s=s: ax * s), smooth=False)


def car_cover(k):
    """A sedan under a fitted cover in charcoal fabric, in the west bay, nose to the wall:
    lofted from cross-sections (a body with rounded shoulders, a cabin with a sloping
    windscreen and rear window), eased smooth like cloth pulled over it, hemmed a hand's
    width above the floor with soft folds, the tyres just showing underneath. A stand-in:
    the real car replaces it."""
    f = Frame((CAR["x"], FLOOR_Y, CAR["z"]), 180.0)          # local +z: the car's nose, toward the back wall
    L, B, hem = CAR["L"] / 2, CAR["W"] / 2, CAR["hem"]
    # the tyres first, just showing under the hem
    for sx in (-1, 1):
        for sz in (-1, 1):
            tyre(k, f((sx * (CAR["track"] / 2), 0.33, sz * CAR["wheelbase"] / 2)), np.subtract(f((1, 0, 0)), f((0, 0, 0))),
                 rim="garage_rim")

    def half_width(u):
        s = min(1.0, abs(u) / L)
        return B * max(0.0, 1 - s ** 5) ** (1 / 5)
    us_h = [-2.40, -2.15, -1.65, 0.90, 1.95, 2.40]
    hs_h = [0.74, 0.92, 0.97, 0.90, 0.82, 0.70]
    us_c = [-1.80, -1.62, -0.95, 0.10, 0.92, 1.10]
    hs_c = [0.96, 1.06, 1.40, 1.44, 1.02, 0.88]

    def section(u, M=64):
        b = half_width(u)
        h1 = float(np.interp(u, us_h, hs_h))
        h2 = float(np.interp(u, us_c, hs_c, left=0.0, right=0.0))
        rs = min(0.13, b * 0.9, max(h1 - hem, 0.01) * 0.5)
        # the left half, from the hem up over the shoulder (and the cabin) to the middle
        left = [(-b, hem)]
        for a in np.linspace(math.pi, math.pi / 2, 7):
            left.append((-b + rs + rs * math.cos(a), h1 - rs + rs * math.sin(a)))
        top = h1
        if h2 > h1 + 0.03 and b > 0.5:
            cb, cr, rr = min(0.74, b - 0.10), min(0.60, b - 0.22), 0.10
            left.append((-cb, h1))
            for a in np.linspace(math.pi, math.pi / 2, 6):
                left.append((-cr + rr + rr * math.cos(a), h2 - rr + rr * math.sin(a)))
            top = h2
        left.append((0.0, top))
        line = left + [(-x, y) for x, y in reversed(left[:-1])]
        # resample evenly along its length
        P = np.array(line, float)
        seg = np.hypot(*np.diff(P, axis=0).T)
        s = np.concatenate([[0.0], np.cumsum(seg)])
        if s[-1] < 1e-6:
            return np.column_stack([np.zeros(M), np.linspace(hem, h1, M)])
        t = np.linspace(0, s[-1], M)
        out = np.column_stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])])
        for _ in range(6):                                   # ease it, like cloth pulled over
            out[1:-1] = out[1:-1] * 0.5 + (out[:-2] + out[2:]) * 0.25
        out[0, 1] = out[-1, 1] = hem
        return out
    stations = [L * math.sin(math.pi / 2 * v) for v in np.linspace(-1, 1, 70)]
    rng = np.random.default_rng(7)
    ph = rng.uniform(0, 2 * math.pi, 2)
    M = 64
    secs = [section(u, M) for u in stations]
    verts = []
    for u, sec in zip(stations, secs):
        for j, (x, y) in enumerate(sec):
            # soft folds near the hem, more toward the bottom, and the hem drawn in a little
            low = max(0.0, 1 - (y - hem) / 0.35)
            along = u if abs(x) > 0.3 else x
            fold = 0.012 * low * math.sin(2 * math.pi * along / 0.23 + ph[0]) + 0.006 * low * math.sin(2 * math.pi * along / 0.11 + ph[1])
            sx = math.copysign(1.0, x) if abs(x) > 1e-6 else 0.0
            px = x + sx * fold - sx * 0.02 * low ** 3
            pu = u + (math.copysign(1.0, u) * (fold - 0.02 * low ** 3) if abs(u) > L - 0.25 else 0.0)
            verts.append(f((px, y, pu)))
    faces = [(i * M + j, i * M + j + 1, (i + 1) * M + j + 1, (i + 1) * M + j) for i in range(len(stations) - 1) for j in range(M - 1)]
    mid = np.asarray(f((0.0, 0.62, 0.0)))
    k.b.mesh(G, "car_cover", verts, _facing(verts, faces, lambda c: np.asarray(c) - mid), smooth=True)
    # the elastic hem
    # (at the nose and the tail the section is a vertical line, so its two hem points meet:
    # repeated points give the tube no direction there, and the export turned them into
    # a spike to the world's origin)
    loop = [verts[i * M] for i in range(len(stations))] + [verts[i * M + M - 1] for i in reversed(range(len(stations)))]
    loop.append(loop[0])
    hemline = [loop[0]]
    for p in loop[1:]:
        if np.linalg.norm(np.subtract(p, hemline[-1])) > 1e-4:
            hemline.append(p)
    k.sweep("car_cover", hemline, 0.009, 8, caps=False)


def east_frame(z):
    """A frame on the foyer wall's lining: +z out into the garage, +x toward the front."""
    return Frame((XE - LINING, 0.0, z), -90.0)


CHEST_Z = 1.30


def tool_chest(k):
    """A rolling tool chest in charcoal steel: six drawers with long brushed pulls on
    casters, a top box with four more under a lid; two detailing sprays and a folded
    microfibre towel on top."""
    f = east_frame(CHEST_Z)
    W, D = 1.10, 0.46
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = f((sx * (W / 2 - 0.06), 0.045, 0.06 + (sz + 1) / 2 * (D - 0.12)))
            k.tube("garage_black", (c[0], c[1] + 0.045, c[2]), (c[0], c[1] + 0.065, c[2]), 0.02, segments=10, step=0.02)
            k.tube("garage_black", (c[0], 0.045, c[2] - 0.02), (c[0], 0.045, c[2] + 0.02), 0.035, segments=14, step=0.02)
    k.block("garage_chest", f, (-W / 2, 0.11, 0.0), (W / 2, 0.95, D), step=0.08, skip=("-z",))
    k.block("garage_chest", f, (-W / 2 + 0.01, 0.97, 0.03), (W / 2 - 0.01, 1.38, D - 0.02), step=0.08, skip=("-z",))
    k.block("garage_chest", f, (-W / 2, 1.38, 0.02), (W / 2, 1.42, D - 0.01), step=0.08)
    def drawers(y0, y1, heights, front):
        y = y1
        for h in heights:
            ya = y - h
            k.block("garage_black", f, (-W / 2 + 0.02, ya + 0.001, front), (W / 2 - 0.02, ya + 0.004, front + 0.0015), step=0.3, skip=("-z",))
            k.tube("steel_brushed", f((-W / 2 + 0.08, y - 0.03, front + 0.018)), f((W / 2 - 0.08, y - 0.03, front + 0.018)), 0.006,
                   segments=8, step=0.2)
            for x in (-W / 2 + 0.09, W / 2 - 0.09):
                k.tube("steel_brushed", f((x, y - 0.03, front)), f((x, y - 0.03, front + 0.018)), 0.004, segments=6)
            y = ya
    drawers(0.11, 0.95, (0.08, 0.08, 0.10, 0.12, 0.16, 0.30), D)
    drawers(0.97, 1.30, (0.07, 0.07, 0.08, 0.11), D - 0.02)
    # on top: two sprays and a folded towel
    for x, col in ((-0.36, "garage_bottle_blue"), (-0.25, "garage_white")):
        g = Frame(f((x, 1.42, D / 2)))
        k.lathe(col, g, [(0.0, 0.0), (0.04, 0.0), (0.042, 0.02), (0.042, 0.18), (0.03, 0.21), (0.014, 0.23), (0.014, 0.25),
                         (0.0, 0.25)], 24)
        k.soft("garage_black", Frame(g((0.0, 0.27, 0.0)), f.yaw + 20), (0.01, 0.0, 0.0), (0.06, 0.04, 0.025), 0.006, n=2)
    k.soft("garage_towel", Frame(f((0.25, 1.42, D / 2)), f.yaw + 6), (0.0, 0.025, 0.0), (0.32, 0.05, 0.22), 0.015, n=3)


def tyre_rack(k):
    """A steel rack on the wall over the tool chest, four spare tyres standing on its two
    rails."""
    f = east_frame(CHEST_Z)
    y = 2.05
    k.tube("steel_black", f((-0.84, y, 0.12)), f((0.84, y, 0.12)), 0.016, segments=10, step=0.2)
    k.tube("steel_black", f((-0.84, y, 0.40)), f((0.84, y, 0.40)), 0.016, segments=10, step=0.2)
    for x in (-0.80, 0.0, 0.80):
        k.rod("steel_black", f((x, y - 0.02, 0.0)), f((x, y - 0.02, 0.44)), 0.03)
        k.rod("steel_black", f((x, y - 0.32, 0.0)), f((x, y - 0.03, 0.36)), 0.025)
        k.soft("steel_black", f, (x, y - 0.17, 0.004), (0.06, 0.40, 0.008), 0.003, n=1)
    r = 0.33
    cy = y + math.sqrt(r ** 2 - 0.14 ** 2) + 0.016
    for x in (-0.60, -0.20, 0.20, 0.60):                   # a hand's width between them
        tyre(k, f((x, cy, 0.26)), np.subtract(f((1, 0, 0)), f((0, 0, 0))), r_out=r)
