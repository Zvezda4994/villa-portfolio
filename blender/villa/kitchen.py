"""The kitchen (tools and stack), furnished: bright and clean, white and pale oak,
with the open shelves of labelled jars and tins as the room's signature.

Plan, looking down, seen from the driveway (the window onto the pool at the
bottom, so +x is on the left here as on the site):

          wall to the garage (z = 0)      door
     +---------------------------------+  [  ]  +------------------+
     |  [ open shelves: jars and tins, labelled ]| tall units:      |
     |  [ counter, espresso machine        ]     | fridge, ovens    | west
  d  |                                                              | wall,
  i  |       (o)      (o)      (o)   pendants                       | window
  n  |     [========= island, quartz =========]                     |
  i  |       stool    stool    stool                         [fig]  |
  n  |                                                  [ counter,  |
  g  |                                                    hob ]     |
     |  [ counter, sink under the window                          ] |
     +--------------------------------------------------------------+
                         back wall, window onto the pool deck

The labels come from data/kitchen_labels.txt, one per line, and are painted into
one picture by `paint_labels`. The shelves re-space themselves for any number of
labels. The site's view sits on the right-hand stool, looking across the island at
the shelves.

How it is lit: everything in the site's view (the shelves, the tiles behind them,
the counter and the island) is lit per vertex on fine grids, so it stays clean
even with a quick draft bake. The back and side counters and the tall units are on
the room's own lightmap ("kit"). The ceiling light is left up, cool-neutral, with
three opal pendants over the island and an LED strip under each shelf.
"""
import math
import random

import numpy as np

from . import config as C
from .house import H1, P
from .kit import Frame, Kit, grid, panel
from .study import book_upright
from .textures import picture_path, save_png

ROOM, G, ATLAS = "kitchen", "ground", "kit"

# The room's inside faces.
XW = -C.HALF_W + C.WALL          # the west wall, with its window (-11.7)
XE = -5.0 - P / 2                # the wall to the dining room (-5.075)
ZB = -C.HALF_D + C.WALL          # the back wall, with the window onto the deck (-7.7)
ZN = -P / 2                      # the wall to the garage (-0.075)
GARAGE_DOOR = (-9.5, -8.3)

LABELS_FILE = C.ROOT / "data" / "kitchen_labels.txt"

# The shelf wall: a counter with open oak shelves above it, between the garage door
# and the dining room wall. Shelf heights are the tops of the boards.
RUN = (-8.15, XE)
COUNTER = dict(depth=0.62, top=0.90, t=0.03, door=0.018)
SHELF_Y = (2.22, 1.82, 1.42)     # top shelf first, the order the labels fill them
SHELF_T, SHELF_D = 0.04, 0.28
TILE_TOP = 2.62
TILE_Z = 0.014                   # the tiles' face, clear of the house wall's rounded positions (gotcha 22)
LINING = 0.012                   # the walls' plaster lining, likewise

ISLAND = dict(cx=-7.15, cz=-2.175, L=2.30, D=0.95, top=0.92, t=0.04, overhang=0.30)
STOOLS_X = (-7.85, -7.15, -6.45)
PENDANTS_X = (-7.90, -7.15, -6.40)

CEILING_LIGHT = 1.1
CEILING_COLOUR = (1.0, 0.90, 0.78)       # neutral, so the whites stay white
LED = (1.0, 0.90, 0.78)
LAMPS = []

# Review cameras. The first is also the room's view on the website: sitting on the
# right-hand stool at the island, looking across it at the shelves.
KITCHEN_CAM = dict(pos=(-6.45, 1.36, -3.02), target=(-6.62, 1.47, -0.075), fov=52.0)
SHELF_CAM = dict(pos=(-6.40, 1.66, -1.30), target=(-6.55, 1.78, -0.10), fov=50.0)
WIDE_CAM = dict(pos=(-5.55, 1.70, -7.05), target=(-9.40, 1.00, -2.10), fov=58.0)


def read_labels():
    lines = LABELS_FILE.read_text(encoding="utf-8").splitlines()
    return [s.strip() for s in lines if s.strip() and not s.strip().startswith("#")]


def build_kitchen(b):
    LAMPS.clear()
    labels = read_labels()
    cells = paint_labels(labels)
    paint_tiles()
    k = Kit(b, G, ATLAS)
    with b.room(ROOM):
        f = shelf_frame()
        shelf_counter(k, f)
        backsplash(k, f)
        shelves(k, f, labels, cells)
        counter_things(k, f)
        island(k)
        for i, x in enumerate(STOOLS_X):
            out = 0.20 if i == len(STOOLS_X) - 1 else 0.0           # the visitor's, pulled out
            stool(k, Frame((x, 0.0, ISLAND["cz"] - ISLAND["D"] / 2 - 0.08 - out), 180.0 + (6.0 if out else -3.0 + 4 * i)))
        pendants(k)
        island_things(k)
        back_run(k)
        west_run(k)
        tall_units(k)
        fig(k)
        walls(k)


def shelf_frame():
    """The shelf wall's own frame: origin on the garage wall at the middle of the run,
    +z out into the room, +x to the right as you face the shelves."""
    return Frame(((RUN[0] + RUN[1]) / 2, 0.0, ZN), 180.0)


def run_length():
    return RUN[1] - RUN[0]


# ---- the shelf wall ------------------------------------------------------------------------
def shelf_counter(k, f):
    """White handleless drawers under a quartz top, on a dark recessed plinth."""
    L = run_length()
    d, top, t, door = COUNTER["depth"], COUNTER["top"], COUNTER["t"], COUNTER["door"]
    x0, x1 = -L / 2, L / 2
    k.block("kitchen_quartz", f, (x0, top - t, 0.0), (x1, top, d + door + 0.015), step=0.06, skip=("-z",))
    k.block("kitchen_gap", f, (x0, 0.0, 0.0), (x1, 0.10, d - 0.06), step=0.2, skip=("-z", "-y"))
    k.block("kitchen_gap", f, (x0, 0.10, d - 0.004), (x1, top - t, d), step=0.15, skip=("-z", "-y"))
    # five columns of drawers: a deep one at the bottom, two shallower above
    n = 5
    w = L / n
    rows = [(0.105, 0.48), (0.484, 0.68), (0.684, top - t - 0.004)]
    for i in range(n):
        for y0, y1 in rows:
            k.block("kitchen_white_v", f, (x0 + i * w + 0.0015, y0, d), (x0 + (i + 1) * w - 0.0015, y1 - 0.003, d + door),
                    step=0.07, skip=("-z",))


def tiled_panel(k, mat, f, x0, x1, y0, y1, z, tile, step=0.06):
    """A flat panel facing local +z, lit per vertex on a grid, with a picture that repeats
    every `tile` metres (fixed to the wall, so neighbouring panels line up)."""
    nu, nv = max(1, round((x1 - x0) / step)), max(1, round((y1 - y0) / step))
    verts, faces, uvs = grid((x0, y0, z), (x1 - x0, 0, 0), (0, y1 - y0, 0), nu, nv)
    uvs = [[((x0 + (x1 - x0) * u) / tile, (y0 + (y1 - y0) * v) / tile) for u, v in face] for face in uvs]
    k.mesh(mat, f, verts, faces, smooth=False, uvs=uvs)


def backsplash(k, f):
    """White handmade tiles from the counter to above the top shelf, laid in strips
    between the shelves so the light under each board doesn't muddy the next."""
    L = run_length()
    z = TILE_Z
    edges = [COUNTER["top"]]
    for y in sorted(SHELF_Y):
        edges += [y - SHELF_T - 0.002, y + 0.002]
    edges.append(TILE_TOP)
    for y0, y1 in zip(edges[::2], edges[1::2]):
        tiled_panel(k, "kitchen_tile", f, -L / 2, L / 2, y0, y1, z, 0.30)
    # a slim oak trim along the tiles' top edge
    k.block("oak_light", f, (-L / 2, TILE_TOP, 0.0), (L / 2, TILE_TOP + 0.012, TILE_Z + 0.012), step=0.2)


def shelves(k, f, labels, cells):
    """Three floating oak shelves, each with an LED strip under its front edge, and the
    labelled jars, canisters and tins standing on them."""
    L = run_length()
    for y in SHELF_Y:
        k.block("oak_light", f, (-L / 2, y - SHELF_T, 0.0), (L / 2 - 0.004, y, SHELF_D), step=0.05)
        yl = y - SHELF_T - 0.0008
        k.quad("kitchen_led", f, [(-L / 2 + 0.03, yl, SHELF_D - 0.05), (L / 2 - 0.03, yl, SHELF_D - 0.05),
                                  (L / 2 - 0.03, yl, SHELF_D - 0.035), (-L / 2 + 0.03, yl, SHELF_D - 0.035)])
        LAMPS.append(dict(name=f"kitchen_shelf_{y:.2f}", pos=f((0.0, y - SHELF_T - 0.01, SHELF_D - 0.06)), size=(L - 0.1, 0.03),
                          watts=16.0, aim=tuple(np.subtract(f((0.0, -1.0, -0.22)), f((0, 0, 0)))), colour=LED))
    # the labels, top shelf first, left to right; each shelf ends with something unlabelled
    n = len(labels)
    per = [n // 3 + (1 if i < n % 3 else 0) for i in range(3)]
    extras = [("plant", 0.15, "right"), ("bowls", 0.17, "left"), ("books", 0.13, "right")]      # top, middle, bottom
    start = 0
    for s, (y, count) in enumerate(zip(SHELF_Y, per)):
        order = [(container_spec(start + i), start + i, container_spec(start + i)["r"] * 2) for i in range(count)]
        what, width, end = extras[s]
        order = order + [(what, None, width)] if end == "right" else [(what, None, width)] + order
        avail = L - 0.14
        gap = (avail - sum(w for *_, w in order)) / len(order)
        x = -L / 2 + 0.07 + gap / 2
        rng = random.Random(40 + s)
        for spec, idx, w in order:
            cx = x + w / 2
            if idx is None:
                extra_piece(k, f, spec, cx, y)
            else:
                at = Frame(f((cx, y, SHELF_D / 2 + 0.01)), f.yaw + rng.uniform(-7, 7))
                container(k, at, spec, labels[idx], cells[idx])
            x += w + gap
        start += count


# ---- jars, canisters and tins ------------------------------------------------------------------
KINDS = ["jar", "canister", "tin_black", "jar", "tin_steel", "canister", "jar", "tin_sage"]
CONTENTS = ["content_pasta", "content_coffee", "content_rice", "content_lentils", "content_oats", "content_beans"]


def container_spec(i):
    """What container label i goes on, and its size. The mix repeats along the shelves
    so neighbours differ."""
    kind = KINDS[(i * 5 + i // 8) % len(KINDS)]
    rng = random.Random(100 + i)
    if kind == "jar":
        tall = rng.random() < 0.4
        return dict(kind=kind, r=0.060 if tall else 0.066, h=0.235 if tall else 0.185, fill=rng.uniform(0.55, 0.85),
                    contents=CONTENTS[i % len(CONTENTS)])
    if kind == "canister":
        return dict(kind=kind, r=0.074, h=0.19 + rng.choice((0.0, 0.03)))
    return dict(kind=kind, r=0.058, h=0.165 + rng.choice((0.0, 0.02)))


LABEL_STYLE = {
    # ground colour, ink, paper grain and a fine border (sRGB)
    "jar":       ((0.95, 0.94, 0.90), (0.10, 0.10, 0.10), True),
    "canister":  ((0.93, 0.92, 0.89), (0.12, 0.12, 0.12), False),     # printed straight onto the glaze
    "tin_black": ((0.93, 0.90, 0.83), (0.08, 0.08, 0.08), True),
    "tin_steel": ((0.72, 0.58, 0.42), (0.11, 0.08, 0.06), True),       # kraft paper
    "tin_sage":  ((0.95, 0.94, 0.90), (0.12, 0.13, 0.11), True),
}
BODY = {"canister": "canister_white", "tin_black": "tin_black", "tin_steel": "steel_brushed", "tin_sage": "tin_sage"}


def container(k, f, spec, text, cell):
    kind, r, h = spec["kind"], spec["r"], spec["h"]
    lw = {"jar": 0.112, "canister": 0.128, "tin_black": 0.100, "tin_steel": 0.100, "tin_sage": 0.100}[kind]
    lh = lw / LABEL_ASPECT
    middle = {"jar": 0.45 * h, "canister": 0.52 * h}.get(kind, (h - 0.03) / 2)
    ly0 = middle - lh / 2
    label = ("kitchen_labels", lw / r, ly0, ly0 + lh, cell)
    if kind == "jar":
        ri = r - 0.004
        fill = 0.012 + (h - 0.03) * spec["fill"]
        k.lathe(spec["contents"], f, [(0.0, 0.008), (ri, 0.008), (ri, fill), (ri * 0.7, fill + 0.008), (0.0, fill + 0.011)], 28)
        labelled_wall(k, f, r, 0.0, h, "jar_glass", label)
        k.disc("jar_glass", f, (0.0, 0.004, 0.0), r - 0.002, 28)
        lid = [(0.0, h - 0.004), (r + 0.004, h - 0.004), (r + 0.005, h + 0.016), (r + 0.002, h + 0.022), (0.0, h + 0.024)]
        k.lathe("oak_light", f, lid, 32)
        k.lathe("jar_seal", f, [(r + 0.0005, h - 0.012), (r + 0.003, h - 0.012), (r + 0.003, h - 0.003), (r + 0.0005, h - 0.003)], 32)
    elif kind == "canister":
        body = BODY[kind]
        labelled_wall(k, f, r, 0.012, h, body, label)
        k.lathe(body, f, [(0.0, 0.0), (r - 0.012, 0.0), (r - 0.003, 0.003), (r, 0.012)], 32)
        lid = [(0.0, h - 0.002), (r + 0.002, h - 0.002), (r + 0.002, h + 0.024), (r - 0.004, h + 0.028), (0.025, h + 0.028),
               (0.022, h + 0.034), (0.024, h + 0.050), (0.016, h + 0.056), (0.0, h + 0.057)]
        k.lathe("oak_light", f, lid, 32)
    else:
        body = BODY[kind]
        labelled_wall(k, f, r, 0.0, h - 0.03, body, label)
        lid = [(0.0, h - 0.032), (r + 0.0025, h - 0.032), (r + 0.0025, h + 0.001), (r - 0.004, h + 0.004), (0.0, h + 0.004)]
        k.lathe(body, f, lid, 32)


def labelled_wall(k, f, r, y0, y1, body, label, n_label=12):
    """An upright cylinder's wall from y0 to y1 with a label wrapped round its front
    (local +z): `label` is (material, arc in radians, label bottom, label top, uv rect).
    The label's faces are part of the wall, not laid over it, so nothing underneath bakes
    dark and bleeds out round its edges."""
    mat, arc, ly0, ly1, (u0, v0, u1, v1) = label
    step = arc / n_label
    n_rest = max(8, round((2 * math.pi - arc) / step))
    thetas = [-arc / 2 + step * i for i in range(n_label + 1)]
    thetas += [arc / 2 + (2 * math.pi - arc) * i / n_rest for i in range(1, n_rest)]
    ys = sorted({y0, ly0, ly1, y1} | set(np.arange(y0, y1, 0.03).round(4)))
    ys = [y for y in ys if y0 <= y <= y1]
    ns = len(thetas)
    verts = [(r * math.sin(t), y, r * math.cos(t)) for t in thetas for y in ys]
    on, off, on_uv = [], [], []
    for i in range(ns):
        for j in range(len(ys) - 1):
            a, c = i * len(ys) + j, ((i + 1) % ns) * len(ys) + j
            face = (a, c, c + 1, a + 1)
            if i < n_label and ys[j] >= ly0 - 1e-6 and ys[j + 1] <= ly1 + 1e-6:
                on.append(face)
                ua, ub = u0 + (u1 - u0) * i / n_label, u0 + (u1 - u0) * (i + 1) / n_label
                va = v0 + (v1 - v0) * (ys[j] - ly0) / (ly1 - ly0)
                vb = v0 + (v1 - v0) * (ys[j + 1] - ly0) / (ly1 - ly0)
                on_uv.append([(ua, va), (ub, va), (ub, vb), (ua, vb)])
            else:
                off.append(face)
    for faces, m, uvs in ((on, mat, on_uv), (off, body, None)):
        used = sorted({v for fc in faces for v in fc})
        remap = {v: n for n, v in enumerate(used)}
        k.mesh(m, f, [verts[v] for v in used], [tuple(remap[v] for v in fc) for fc in faces], smooth=True, uvs=uvs)


def extra_piece(k, f, what, cx, y):
    """The unlabelled things at the end of each shelf."""
    from .props import load, place
    if what == "bowls":                     # a stack of three white bowls
        at = Frame(f((cx, y, SHELF_D / 2 + 0.01)))
        for i in range(3):
            yy = i * 0.028
            k.lathe("ceramic_white", Frame(at((0, yy, 0))), [(0.0, 0.0), (0.035, 0.0), (0.062, 0.022), (0.083, 0.055),
                                                             (0.079, 0.056), (0.058, 0.026), (0.0, 0.008)], 32)
    elif what == "books":                   # three cookbooks standing at the end
        x = cx - 0.065
        for w, h, d, cover in ((0.032, 0.25, 0.19, "book_cream"), (0.028, 0.235, 0.18, "book_olive"), (0.04, 0.26, 0.20, "book_charcoal")):
            book_upright(k, Frame(f((x + w / 2, y, SHELF_D / 2 + 0.005)), f.yaw), (w, h, d), cover)
            x += w + 0.002
    elif what == "plant":                   # a small haworthia in its white pot (Poly Haven's potted_plant_04)
        parts = load("potted_plant_04", skip={"potted_plant_04_ground"}, thin={"potted_plant_04_plant": 0.6})
        for piece in parts.values():
            place(k.b, G, "kitchen_succulent", piece, f((cx, y, SHELF_D / 2 + 0.01)), yaw=0.4, scale=1.0,
                  origin=(0.0, 0.0, 0.0))


def counter_things(k, f):
    """On the counter under the shelves: an espresso machine by the dining room wall,
    a crock of wooden spoons and a chopping board leaning on the tiles."""
    L = run_length()
    top = COUNTER["top"]
    # the espresso machine, brushed steel with a black drip tray and portafilter
    m = Frame(f((-L / 2 + 0.30, top, 0.30)), f.yaw)
    k.soft("steel_brushed", m, (0, 0.20, -0.02), (0.30, 0.38, 0.34), 0.02, n=2)
    k.soft("steel_black", m, (0, 0.012, 0.13), (0.28, 0.024, 0.13), 0.006, n=1)          # drip tray
    k.soft("steel_brushed", m, (0, 0.27, 0.16), (0.16, 0.05, 0.06), 0.012, n=2)            # group head
    k.tube("steel_brushed", m((0, 0.235, 0.18)), m((0, 0.245, 0.18)), 0.035, segments=20)
    k.tube("steel_black", m((0, 0.235, 0.20)), m((0, 0.225, 0.36)), 0.012, segments=10)   # portafilter handle
    k.soft("steel_black", m, (0.0, 0.31, 0.155), (0.12, 0.03, 0.004), 0.002, n=1)           # the control strip
    for x in (-0.06, 0.06):                                                                  # two cups warming on top
        k.lathe("ceramic_white", Frame(m((x, 0.39, -0.04))),
                [(0.0, 0.0), (0.022, 0.0), (0.03, 0.02), (0.032, 0.05), (0.029, 0.05), (0.026, 0.02), (0.0, 0.006)], 24)
    # a crock of wooden spoons
    c = Frame(f((0.30, top, 0.17)))
    k.lathe("ceramic_white", c, [(0.0, 0.0), (0.055, 0.0), (0.062, 0.02), (0.062, 0.15), (0.066, 0.16), (0.058, 0.16),
                                 (0.056, 0.03), (0.0, 0.025)], 32)
    for i, (dx, dz, lean) in enumerate(((-0.015, 0.0, -0.10), (0.018, 0.01, 0.12), (0.0, -0.02, 0.02))):
        p0 = np.array(c((dx, 0.03, dz)))
        p1 = np.array(c((dx + lean, 0.30 + 0.02 * i, dz + 0.03)))
        k.tube("oak_light", tuple(p0), tuple(p1), 0.007, segments=8)
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        k.tube("oak_light", tuple(p1 - d * 0.005), tuple(p1 + d * 0.065), 0.022, segments=12, r1=0.016)
    # an oak chopping board leaning against the tiles
    k.box("oak_light", f, (0.55, top, 0.015), (0.95, top + 0.30, 0.035), tilt=-12.0, pivot=(0, top, 0.035))


# ---- the island and stools ---------------------------------------------------------------------
def island(k):
    """A quartz top that falls to the floor at both ends, over white drawers facing the
    shelves; the stools tuck under the overhang on the window side."""
    I = ISLAND
    f = Frame((I["cx"], 0.0, I["cz"]))
    L, D, top, t = I["L"], I["D"], I["top"], I["t"]
    x0, x1, z0, z1 = -L / 2, L / 2, -D / 2, D / 2
    k.block("kitchen_quartz", f, (x0, top - t, z0), (x1, top, z1), step=0.06)
    for xa, xb in ((x0, x0 + t), (x1 - t, x1)):
        k.block("kitchen_quartz", f, (xa, 0.0, z0), (xb, top - t, z1), step=0.07, skip=("-y", "+y"))
    zb = z0 + I["overhang"]
    k.block("kitchen_white_v", f, (x0 + t, 0.10, zb), (x1 - t, top - t, z1 - 0.02), step=0.08, skip=("-y", "+y", "+z"))
    k.block("kitchen_gap", f, (x0 + t, 0.0, zb + 0.05), (x1 - t, 0.10, z1 - 0.07), step=0.2, skip=("-y",))
    n = 3
    w = (L - 2 * t) / n
    for i in range(n):
        for y0, y1 in ((0.105, 0.50), (0.504, top - t - 0.004)):
            k.block("kitchen_white_v", f, (x0 + t + i * w + 0.0015, y0, z1 - 0.02), (x0 + t + (i + 1) * w - 0.0015, y1 - 0.003, z1 - 0.002),
                    step=0.07, skip=("-z",))


def stool(k, f):
    """A counter stool: a dished round oak seat on four splayed black steel legs with a
    footring. Built facing +z."""
    seat = 0.66
    k.lathe("oak_light", f, [(0.0, seat - 0.035), (0.17, seat - 0.035), (0.182, seat - 0.02), (0.183, seat - 0.004),
                               (0.175, seat + 0.002), (0.12, seat - 0.004), (0.0, seat - 0.008)], 40)
    ring_y, r_top, r_foot = 0.27, 0.115, 0.205
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        top = (r_top * math.cos(a), seat - 0.035, r_top * math.sin(a))
        foot = (r_foot * math.cos(a), 0.0, r_foot * math.sin(a))
        k.tube("steel_black", f(top), f(foot), 0.011, segments=10)
    rr = r_foot + (r_top - r_foot) * ring_y / (seat - 0.035)            # the legs' spread at the footring
    k.sweep("steel_black", [f((rr * math.cos(a), ring_y, rr * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 49)],
            0.008, segments=8, caps=False)
    k.lathe("steel_black", Frame(f((0, seat - 0.05, 0))), [(0.0, 0.0), (0.13, 0.0), (0.13, 0.016), (0.0, 0.016)], 24)


def pendants(k):
    """Three opal glass globes on slim black stems over the island."""
    top = H1
    y = 2.00
    for x in PENDANTS_X:
        f = Frame((x, 0.0, ISLAND["cz"]))
        k.lathe("lamp_brass_k", Frame(f((0, top - 0.025, 0))), [(0.0, 0.0), (0.05, 0.0), (0.055, 0.02), (0.055, 0.025), (0.0, 0.025)], 24)
        k.tube("steel_black", f((0, top - 0.025, 0)), f((0, y + 0.13, 0)), 0.005, segments=8)
        k.lathe("lamp_brass_k", Frame(f((0, y + 0.095, 0))), [(0.0, 0.0), (0.032, 0.0), (0.034, 0.012), (0.03, 0.035), (0.0, 0.035)], 20)
        r = 0.115
        prof = [(r * math.sin(math.pi * s), y - r * math.cos(math.pi * s)) for s in np.linspace(0.0, 0.86, 16)]
        k.lathe("kitchen_globe", f, prof, 36)
        LAMPS.append(dict(name=f"kitchen_pendant_{x:.2f}", kind="point", pos=f((0, y, 0)), watts=22.0, radius=0.09,
                          colour=(1.0, 0.80, 0.58)))


def island_things(k):
    """A shallow oak bowl of lemons, and a cup of coffee by the visitor's seat."""
    I = ISLAND
    b = Frame((I["cx"] + 0.22, I["top"], I["cz"] + 0.12))
    k.lathe("oak_light", b, [(0.0, 0.0), (0.08, 0.0), (0.15, 0.03), (0.175, 0.07), (0.168, 0.071), (0.14, 0.036),
                               (0.075, 0.012), (0.0, 0.012)], 40)
    rng = random.Random(7)
    spots = [(0.0, 0.0), (0.075, 0.03), (-0.07, 0.045), (0.02, -0.075), (-0.05, -0.05), (0.06, -0.06), (0.0, 0.03)]
    for i, (dx, dz) in enumerate(spots):
        lift = 0.016 + 0.05 * math.hypot(dx, dz) + (0.045 if i == len(spots) - 1 else 0.0)
        r = rng.uniform(0.031, 0.036)
        k.lathe("lemon", Frame(b((dx, lift, dz))), [(0.0, 0.0)] + [(r * math.sin(math.pi * s) * (1.0 - 0.15 * abs(math.cos(math.pi * s)) ** 3),
                                                                    r * 1.15 * (1 - math.cos(math.pi * s))) for s in np.linspace(0.08, 1, 12)], 20)
    # the visitor's coffee, on a saucer, just in front of the right-hand stool
    c = Frame((STOOLS_X[-1] + 0.10, I["top"], I["cz"] - I["D"] / 2 + 0.17))
    k.lathe("ceramic_white", c, [(0.0, 0.0), (0.05, 0.0), (0.07, 0.008), (0.072, 0.012), (0.066, 0.011), (0.03, 0.004), (0.0, 0.004)], 32)
    k.lathe("ceramic_white", Frame(c((0, 0.004, 0))), [(0.0, 0.0), (0.024, 0.0), (0.036, 0.02), (0.04, 0.062), (0.037, 0.062),
                                                      (0.033, 0.022), (0.0, 0.01)], 28)
    k.disc("kitchen_coffee", c, (0.0, 0.05, 0.0), 0.035, 24)
    k.sweep("ceramic_white", [c((0.035 + 0.018 * math.sin(a), 0.035 + 0.018 * math.cos(a), 0.0)) for a in np.linspace(0.2, math.pi - 0.2, 10)],
            0.004, segments=8)


# ---- the rest of the room: lightmapped ---------------------------------------------------------
def cabinets(k, f, x0, x1, depth, top=0.90, rows=((0.105, 0.48), (0.484, 0.86))):
    """A run of white base cabinets on the room's lightmap, built against local z = 0
    with fronts facing +z, and a quartz top."""
    door = COUNTER["door"]
    k.box("kitchen_white", f, (x0, 0.10, depth - 0.004), (x1, top - 0.03, depth), skip=("-z",), density=0.6)
    k.box("kitchen_plinth", f, (x0, 0.0, 0.0), (x1, 0.10, depth - 0.06), skip=("-z", "-y"), density=0.4)
    n = max(1, round((x1 - x0) / 0.60))
    w = (x1 - x0) / n
    for i in range(n):
        for y0, y1 in rows:
            k.box("kitchen_white", f, (x0 + i * w + 0.0015, y0, depth), (x0 + (i + 1) * w - 0.0015, y1 - 0.003, depth + door),
                  skip=("-z",), density=0.6)


def back_run(k):
    """Counters under the window onto the deck, with an undermount sink and a tall tap."""
    f = Frame(((XW + XE) / 2, 0.0, ZB))          # +z into the room, +x toward the dining room
    L = XE - XW
    d, top, t = COUNTER["depth"], COUNTER["top"], COUNTER["t"]
    cabinets(k, f, -L / 2 + d, L / 2, d)
    sx = -8.5 - (XW + XE) / 2                     # the sink, centred on the window
    sw, s0, s1 = 0.36, 0.10, 0.52
    for lo, hi in (((-L / 2, top - t, 0.0), (sx - sw, top, d + 0.035)), ((sx + sw, top - t, 0.0), (L / 2, top, d + 0.035)),
                   ((sx - sw, top - t, 0.0), (sx + sw, top, s0)), ((sx - sw, top - t, s1), (sx + sw, top, d + 0.035))):
        k.slab("kitchen_quartz", f, lo, hi, step=0.06)
    bot = top - 0.21
    k.box("steel_brushed", f, (sx - sw + 0.01, bot, s0 + 0.01), (sx + sw - 0.01, bot + 0.002, s1 - 0.01), skip=("-y",))
    for lo, hi in (((sx - sw, bot, s0), (sx - sw + 0.01, top - t, s1)), ((sx + sw - 0.01, bot, s0), (sx + sw, top - t, s1)),
                   ((sx - sw, bot, s0), (sx + sw, top - t, s0 + 0.01)), ((sx - sw, bot, s1 - 0.01), (sx + sw, top - t, s1))):
        k.box("steel_brushed", f, lo, hi)
    # the tap: up from the back of the sink and over in an arc
    base = np.array(f((sx, top, 0.06)))
    k.lathe("steel_brushed", Frame(tuple(base)), [(0.0, 0.0), (0.028, 0.0), (0.028, 0.03), (0.0, 0.03)], 20)
    rise = [tuple(base + (0, h, 0)) for h in np.linspace(0.03, 0.30, 6)]
    arc_pts = [tuple(np.array(f((sx, top + 0.30 + 0.10 * math.sin(a), 0.06 + 0.10 * (1 - math.cos(a)))))) for a in np.linspace(0.1, math.pi, 12)]
    k.sweep("steel_brushed", rise + arc_pts, 0.011, segments=12)
    k.tube("steel_brushed", tuple(np.array(f((sx + 0.035, top + 0.18, 0.06)))), tuple(np.array(f((sx + 0.09, top + 0.18, 0.06)))), 0.006, segments=8)


def west_run(k):
    """Counters under the side window, with a flush black induction hob and a slim
    extractor set into the ceiling over it."""
    z1 = -3.60
    f = Frame((XW, 0.0, (ZB + COUNTER["depth"] + z1) / 2), 90.0)        # +z into the room (+x), +x toward the back wall
    L = z1 - (ZB + COUNTER["depth"])
    d, top, t = COUNTER["depth"], COUNTER["top"], COUNTER["t"]
    cabinets(k, f, -L / 2, L / 2, d)
    k.slab("kitchen_quartz", f, (-L / 2, top - t, 0.0), (L / 2 - 0.035, top, d + 0.035), step=0.06)   # the back run's top covers the corner
    hob = Frame((XW + 0.33, top + 0.0012, -5.30), 90.0)
    k.box("glass_black", hob, (-0.40, -0.0012, -0.26), (0.40, 0.0006, 0.26), skip=("-y",))
    k.box("steel_brushed", Frame((XW + 0.45, H1 - 0.012, -5.30), 90.0), (-0.45, 0.0, -0.25), (0.45, 0.012, 0.25), skip=("+y",))
    k.box("kitchen_gap", Frame((XW + 0.45, H1 - 0.0125, -5.30), 90.0), (-0.38, 0.0, -0.18), (0.38, 0.001, 0.18), skip=("+y",))


def tall_units(k):
    """A wall of tall white units between the west wall and the garage door: an
    integrated fridge, a column with two built-in ovens, and a pantry, up to a
    bulkhead under the ceiling."""
    x0, x1 = XW, GARAGE_DOOR[0] - 0.08
    f = Frame(((x0 + x1) / 2, 0.0, ZN), 180.0)
    L, d, door = x1 - x0, COUNTER["depth"], COUNTER["door"]
    h = 2.32
    k.box("kitchen_white", f, (-L / 2, h, 0.0), (L / 2, H1, d + door), skip=("+y", "-z"), density=0.5)        # bulkhead
    k.box("kitchen_plinth", f, (-L / 2, 0.0, 0.0), (L / 2, 0.10, d - 0.06), skip=("-z", "-y"), density=0.4)
    k.box("kitchen_plinth", f, (-L / 2, 0.10, d - 0.004), (L / 2, h, d), skip=("-z",), density=0.4)
    cols = [(-L / 2, -L / 2 + 0.62), (-L / 2 + 0.62, -L / 2 + 1.22), (-L / 2 + 1.22, L / 2)]
    fronts = {
        0: [(0.10, h)],                                                     # the pantry, left as you face it
        1: [(0.10, 0.50), (0.50, 0.84), (0.84, 1.45, "oven"), (1.45, 1.92, "oven"), (1.92, h)],
        2: [(0.10, 0.86), (0.86, h)],                                      # the fridge-freezer
    }
    for i, (a, c) in enumerate(cols):
        for spec in fronts[i]:
            y0, y1 = spec[0], spec[1]
            if len(spec) == 3:
                k.box("steel_brushed", f, (a + 0.002, y0 + 0.002, d), (c - 0.002, y1 - 0.004, d + door), skip=("-z",))
                k.box("glass_black", f, (a + 0.04, y0 + 0.06, d + door), (c - 0.04, y1 - 0.07, d + door + 0.002), skip=("-z",))
            else:
                k.box("kitchen_white", f, (a + 0.0015, y0 + 0.0015, d), (c - 0.0015, y1 - 0.003, d + door), skip=("-z",), density=0.6)


def fig(k):
    """A fig tree (Poly Haven's potted_plant_01) in a white pot in the corner by the side window."""
    from .props import load, place
    x, z = XW + 0.42, -2.55
    f = Frame((x, 0.0, z))
    h = 0.46
    k.lathe("ceramic_white", f, [(0.0, 0.0), (0.16, 0.0), (0.19, 0.05), (0.20, h), (0.185, h), (0.185, h - 0.04), (0.0, h - 0.04)], 40)
    plant = load("potted_plant_01", only={"potted_plant_01_leaves", "potted_plant_01_stem"},
                 thin={"potted_plant_01_leaves": 0.25})
    for name, piece in plant.items():
        mat = "kitchen_fig_leaves" if name.endswith("leaves") else "kitchen_fig_stems"
        place(k.b, G, mat, piece, (x, h - 0.04, z), yaw=2.3, scale=1.6, origin=(0.0, 0.5, 0.0))


def walls(k):
    """Plaster linings laid just over the house's walls, lit per vertex on a grid, so the
    walls stay smooth even from a quick draft bake (the house's own walls are on the
    ground floor's lightmap, which only the full bake makes clean)."""
    from .house import DOOR
    e, m = LINING, "plaster_v"
    top, d = COUNTER["top"], COUNTER["depth"] + 0.04
    # (where a counter stands against a wall the lining starts at its top: points buried
    # in the counter would bake dark and muddy the strip above it)
    # the dining room wall (facing -x), round its wide opening
    for z0, z1, y0 in ((ZB, ZB + d, top), (ZB + d, -5.5, 0.0), (-2.5, ZN - d, 0.0), (ZN - d, ZN, top), (-5.5, -2.5, 2.6)):
        panel(k, m, (XE - e, y0, z0), (0, 0, z1 - z0), (0, H1 - y0, 0))
    # the garage wall (facing -z): above the tiles, beside them, and over the door
    x_tiles = RUN[0]
    for x0, x1, y0, y1 in ((GARAGE_DOOR[1], XE, TILE_TOP + 0.012, H1), (GARAGE_DOOR[1], x_tiles, 0.0, TILE_TOP + 0.012),
                           (GARAGE_DOOR[0] - 0.08, GARAGE_DOOR[1], DOOR, H1)):
        panel(k, m, (x1, y0, ZN - e), (x0 - x1, 0, 0), (0, y1 - y0, 0))
    # the back wall (facing +z), round the window onto the deck
    for x0, x1, y0, y1 in ((XW, -11.0, top, H1), (-6.0, XE, top, H1), (-11.0, -6.0, top, 1.1), (-11.0, -6.0, 2.3, H1)):
        panel(k, m, (x0, y0, ZB + e), (x1 - x0, 0, 0), (0, y1 - y0, 0))
    # the west wall (facing +x), round the side window
    for z0, z1, y0, y1 in ((ZB, -6.5, top, H1), (-1.5, ZN, 0.0, H1), (-6.5, -3.6, top, 1.1), (-3.6, -1.5, 0.0, 1.1), (-6.5, -1.5, 2.5, H1)):
        panel(k, m, (XW + e, y0, z1), (0, 0, z0 - z1), (0, y1 - y0, 0))


# ---- pictures ----------------------------------------------------------------------------------
LABEL_COLS = 4
LABEL_CELL = (256, 144)
LABEL_ASPECT = LABEL_CELL[0] / LABEL_CELL[1]
LABEL_PAD = 6                      # pixels of the cell's ground colour round each label, against mipmap bleeding


def paint_labels(labels):
    """Every label in one picture, LABEL_COLS across: the name in Inter, fitted to the
    label, on paper (or straight on the glaze for the white canisters). Returns each
    label's uv rectangle (u0, v0, u1, v1)."""
    from .labels import _paper, text_mask
    n = len(labels)
    cw, ch = LABEL_CELL
    rows = max(1, math.ceil(n / LABEL_COLS))
    W, H = cw * LABEL_COLS, ch * rows
    rng = np.random.default_rng(31)
    img = np.ones((H, W, 3)) * 0.9
    cells, places = [], []
    for i, text in enumerate(labels):
        col, row = i % LABEL_COLS, rows - 1 - i // LABEL_COLS          # first label in the top row
        x0, y0 = col * cw, row * ch
        kind = container_spec(i)["kind"]
        ground, ink, paper = LABEL_STYLE[kind]
        cell = _paper((ch, cw), np.array(ground), rng) if paper else np.ones((ch, cw, 3)) * np.array(ground)
        if paper:                                              # a fine rule inset from the edge
            p = LABEL_PAD + 9
            line = np.array(ink) * 0.55 + np.array(ground) * 0.45
            cell[p:p + 2, p:cw - p] = line
            cell[ch - p - 2:ch - p, p:cw - p] = line
            cell[p:ch - p, p:p + 2] = line
            cell[p:ch - p, cw - p - 2:cw - p] = line
        img[y0:y0 + ch, x0:x0 + cw] = cell
        lines = text.split(" ", 1) if (" " in text and len(text) > 9) else [text]
        places.append((x0, y0, lines, ink))
        pad = LABEL_PAD / 2
        cells.append(((x0 + pad) / W, (y0 + pad) / H, (x0 + cw - pad) / W, (y0 + ch - pad) / H))

    def layout(scale):
        out = []
        for (x0, y0, lines, _), s in zip(places, scale):
            cap = (0.36 if len(lines) == 1 else 0.24) * ch * s            # cap height in pixels
            em = cap / 0.727
            if len(lines) == 1:
                base = [y0 + (ch - cap) / 2]
            else:
                gap = 0.62 * cap
                b0 = y0 + (ch - (2 * cap + gap)) / 2
                base = [b0 + cap + gap, b0]
            for text, by in zip(lines, base):
                out.append((text, (x0 + cw / 2) / W, by / H, em / H, "CENTER", 1.04))
        return out

    # set them small once (so none spills into its neighbour), measure how wide each
    # came out, and set them again at the size that fits
    trial = 0.4
    mask = text_mask((W, H), layout([trial] * n))
    limit = cw - 2 * (LABEL_PAD + 22)
    scale = []
    for x0, y0, _, _ in places:
        cols = np.nonzero(mask[y0:y0 + ch, x0:x0 + cw].max(axis=0) > 0.3)[0]
        width = (cols[-1] - cols[0] + 1) / trial if len(cols) else 0
        scale.append(min(1.0, limit / width) if width else 1.0)
    mask = text_mask((W, H), layout(scale))
    for x0, y0, _, ink in places:
        m = mask[y0:y0 + ch, x0:x0 + cw, None]
        img[y0:y0 + ch, x0:x0 + cw] = img[y0:y0 + ch, x0:x0 + cw] * (1 - m) + np.array(ink) * m
    save_png(picture_path("kitchen_labels"), np.clip(img, 0, 1).astype(np.float32))
    return cells


def paint_tiles(size=256):
    """Glazed white tiles, 15 x 7.5 cm in a brick bond, one repeat of 30 cm square: each
    tile a slightly different white, a little darker at its softened edges, in pale grout."""
    from .study import _smooth_noise
    rng = np.random.default_rng(19)
    rows, per = 4, 2
    th, tw = size // rows, size // per
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    img = np.zeros((size, size, 3))
    grout = np.array([0.80, 0.79, 0.76])
    for r in range(rows):
        shift = (tw // 2) * (r % 2)
        for c in range(per + 1):
            x0 = c * tw - shift
            tone = 0.93 + rng.normal(0, 0.012)
            tint = np.array([1.0, 1.0, 0.985]) * tone
            ys, xs = slice(r * th, (r + 1) * th), np.arange(x0, x0 + tw) % size
            ly = yy[ys][:, xs] - r * th
            lx = (xx[ys][:, xs] - x0) % size
            edge = np.minimum.reduce([lx, tw - 1 - lx, ly, th - 1 - ly])
            shade = 1.0 - 0.06 * np.exp(-edge / 2.5)
            block = tint[None, None, :] * shade[..., None]
            block[(edge < 1.5)] = grout
            img[ys, xs] = block
    img *= (1 + 0.015 * _smooth_noise((size, size), 30, rng))[..., None]
    save_png(picture_path("kitchen_tile"), np.clip(img, 0, 1).astype(np.float32))
