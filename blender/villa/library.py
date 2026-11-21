"""The library (books, and my writing), furnished: floor-to-ceiling dark walnut shelves
on three sides, a leather reading chair by the window, and a desk at the glass with a
green banker's lamp, a laptop and the manuscript.

Plan, looking down, seen from the driveway (the front glass at the top, so +x is on
the right):

        front glass, onto the reflecting pool                        (z = 7.85)
     +-------------------------------------------------------------+
   b |                 [====== desk ======]          (lamp)[chair] |
   l |                        (o) chair                    (table) | s
   a |                                                             | h
   d landing door        [~~~~~~~~~~~ rug ~~~~~~~~~~~]              | e
   e |                                                             | l
     |                                                   titled  ->| v
   w |                                                   books     | e
   a |                                                   ladder  ->| s
   l | [=========== shelves ===========][ door ][==== shelves ====] |
   l +-------------------------------------------------------------+
            wall to the games and trophy rooms, shelves over the door  (z = 0)

The east wall is the main attraction: eight bays from floor to ceiling, a brass rail
and a rolling ladder. The books with real titles (data/library_books.txt) stand on
its two eye-level shelves in the middle bays, the Travis McGee spines printed in the
colour each title names and Heartiste in blackletter. Every other shelf is filled with
unmarked spines, a few lying flat, a few leaning, and some objects.

Everything is lit per vertex, so the room stays clean from a quick draft bake; it has
no lightmap. The unmarked books are one material painted per vertex (every book its
own colour); the titled spines share one picture painted here (`paint_spines`).
"""
import math
import random
import re

import numpy as np

from . import config as C
from .house import P
from .kit import Frame, Kit, grid
from .materials import srgb_to_linear
from .study import _smooth_noise, book_flat
from .textures import picture_path, save_png

ROOM, G = "library", "upper"
F2, RY = C.F2, C.ROOF_Y
BOOKS_FILE = C.ROOT / "data" / "library_books.txt"

# The room's inside faces (heights below are above the library's floor, F2).
XW = C.BLADE_X[1]                 # the dark stone wall, with the door from the landing (1.5)
XE = C.HALF_W - C.WALL            # the east wall (11.7)
Z0 = P / 2                        # the wall to the games and trophy rooms (0.075)
ZF = C.HALF_D - C.WALL            # the front glass's inside face (7.7)
TROPHY_DOOR = (7.0, 8.2)

# The shelving: board tops, from the floor up; the cornice reaches the ceiling.
DEP = 0.36                        # depth of the cases
UP = 0.03                         # uprights
BT = 0.028                        # board thickness
BOARDS = (0.12, 0.47, 0.81, 1.15, 1.49, 1.83, 2.17, 2.51)
CORNICE = (2.86, 2.985)
EYE_ROWS = (4, 3)                 # the boards the titled books stand on: 1.49 first, then 1.15
TITLE_BAYS = (3, 4, 2, 5)         # east wall bays for the titled books, in the order they fill
EAST_BAYS = 8
BRIDGE_Y = 2.33                   # the shelf over the door to the trophy room

RUG = dict(x=(4.55, 9.65), z=(2.15, 5.85), t=0.012)
DESK = dict(cx=6.90, z1=7.40, w=1.70, d=0.72, top=0.775)
CHAIR = dict(pos=(10.35, 6.30), yaw=-118.0)
LADDER_Z = 1.30

CEILING_LIGHT = 0.35
LAMPS = []

# Review cameras. The first is also the room's view on the website: from the landing
# door, across the room to the east wall's shelves, the desk and the chair on the right.
LIBRARY_CAM = dict(pos=(2.55, F2 + 1.50, 5.75), target=(11.0, F2 + 1.20, 3.05), fov=55.0)


def _bay_z(i):
    """The middle of east wall bay i, along the wall."""
    length = ZF - (Z0 + DEP)
    return Z0 + DEP + UP / 2 + (length - UP) * (i + 0.5) / EAST_BAYS


SPINES_CAM = dict(pos=(10.47, F2 + 1.45, _bay_z(3)), target=(11.34, F2 + 1.44, _bay_z(3)), fov=50.0)
SPINES_CAM_B = dict(pos=(10.47, F2 + 1.45, _bay_z(4)), target=(11.34, F2 + 1.44, _bay_z(4)), fov=50.0)
DESK_CAM = dict(pos=(6.10, F2 + 1.32, 5.80), target=(6.95, F2 + 0.80, 7.10), fov=52.0)


# ---- the book list ------------------------------------------------------------------------
# Spine styles: ground and ink colours (sRGB), typeface, height and thickness range (m),
# and whether the spine has gilt rules near its head and foot.
STYLES = {
    "oxblood cloth": dict(ground=(0.36, 0.08, 0.07), ink=(0.86, 0.69, 0.38), font="CrimsonText-SemiBold.ttf",
                          h=0.235, t=(0.040, 0.054), rules=True),
    "black serif": dict(ground=(0.07, 0.07, 0.075), ink=(0.90, 0.88, 0.82), font="CrimsonText-SemiBold.ttf",
                        h=0.205, t=(0.026, 0.033), rules=True),
    "navy": dict(ground=(0.10, 0.14, 0.28), ink=(0.92, 0.91, 0.88), font=None, h=0.215, t=(0.026, 0.032)),
    "cream": dict(ground=(0.86, 0.81, 0.69), ink=(0.10, 0.09, 0.09), font=None, h=0.210, t=(0.024, 0.032)),
    "white": dict(ground=(0.90, 0.89, 0.86), ink=(0.08, 0.08, 0.09), font=None, h=0.225, t=(0.026, 0.034)),
    "grey": dict(ground=(0.36, 0.38, 0.41), ink=(0.94, 0.93, 0.90), font=None, h=0.230, t=(0.026, 0.032)),
    "olive": dict(ground=(0.35, 0.36, 0.21), ink=(0.91, 0.88, 0.78), font=None, h=0.210, t=(0.024, 0.030)),
    "title colour": dict(ground=None, ink=None, font=None, h=0.178, t=(0.022, 0.026)),
    "blackletter": dict(ground=(0.05, 0.05, 0.055), ink=(0.90, 0.87, 0.80), font="UnifrakturMaguntia-Book.ttf",
                        h=0.215, t=(0.030, 0.034), size=1.3),
}

# The Travis McGee spines take the colour their title names: the first of these words in it.
COLOUR_WORDS = {
    "blue": (0.10, 0.25, 0.58), "pink": (0.92, 0.50, 0.64), "purple": (0.42, 0.18, 0.50),
    "red": (0.74, 0.11, 0.10), "gold": (0.82, 0.64, 0.22), "orange": (0.94, 0.49, 0.10),
    "amber": (0.86, 0.56, 0.12), "yellow": (0.96, 0.83, 0.20), "gray": (0.56, 0.57, 0.59),
    "grey": (0.56, 0.57, 0.59), "brown": (0.44, 0.29, 0.17), "indigo": (0.20, 0.16, 0.46),
    "lavender": (0.72, 0.63, 0.84), "tan": (0.79, 0.65, 0.47), "sandy": (0.87, 0.77, 0.57),
    "scarlet": (0.86, 0.18, 0.08), "turquoise": (0.14, 0.67, 0.66), "lemon": (0.98, 0.93, 0.38),
    "copper": (0.72, 0.42, 0.22), "green": (0.14, 0.45, 0.22), "crimson": (0.58, 0.05, 0.17),
    "cinnamon": (0.62, 0.34, 0.18), "silver": (0.76, 0.77, 0.79), "black": (0.07, 0.07, 0.07),
    "white": (0.92, 0.91, 0.88), "violet": (0.50, 0.26, 0.62), "cerise": (0.85, 0.20, 0.45),
}


def title_colour(title):
    words = re.findall(r"[a-z]+", title.lower())
    for w in words:
        if w in COLOUR_WORDS:
            return COLOUR_WORDS[w]
    print(f"[library] no colour word in '{title}'; printing it on cream")
    return (0.86, 0.81, 0.69)


def read_books():
    """The titled books, in shelf order: dicts of title, author, style, colours, size."""
    groups, current = [], None
    for raw in BOOKS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()
        if low.startswith("author:"):
            current = dict(author=line.split(":", 1)[1].strip(), style="white", titles=[])
            groups.append(current)
        elif low.startswith("spine:"):
            style = line.split(":", 1)[1].strip().lower()
            if style not in STYLES:
                raise ValueError(f"data/library_books.txt: unknown spine style '{style}'. Use one of: {', '.join(STYLES)}")
            current["style"] = style
        elif current is None:
            raise ValueError("data/library_books.txt: a title comes before any 'author:' line")
        else:
            current["titles"].append(line)
    rng = random.Random(17)
    books = []
    for gi, g in enumerate(groups):
        st = STYLES[g["style"]]
        for title in g["titles"]:
            ground = st["ground"] or title_colour(title)
            if st["ink"]:
                ink = st["ink"]
            else:
                lum = 0.2126 * ground[0] + 0.7152 * ground[1] + 0.0722 * ground[2]
                ink = (0.06, 0.06, 0.07) if lum > 0.42 else (0.95, 0.94, 0.91)
            t = rng.uniform(*st["t"]) + (0.004 if len(title) > 24 else 0.0)
            books.append(dict(title=title, author=g["author"], style=g["style"], group=gi, ground=ground, ink=ink,
                              font=st["font"], rules=st.get("rules", False), size=st.get("size", 1.0),
                              h=st["h"] * rng.uniform(0.99, 1.01),
                              t=t, d=min(DEP - 0.05, st["h"] * 0.72)))
    return books


# ---- building ------------------------------------------------------------------------------
class Books:
    """Collects the books' faces so they go into the scene in a few large meshes."""

    def __init__(self, k):
        self.k = k
        self.v, self.f, self.c = [], [], []          # unmarked books, painted per vertex
        self.sv, self.sf, self.suv = [], [], []      # the titled spines, on the spine picture

    def add(self, fr, x, y, zs, t, h, d, cover, top, lean=0.0, spine_uv=None, rows=3):
        """One book standing on (x .. x+t, y), its spine at local z = zs facing +z, in
        the run frame fr. `lean` tips it to the left by that many degrees, about its
        bottom left edge. `spine_uv` (u0, v0, u1, v1) puts its spine on the spine picture."""
        def place(p):
            if lean:
                a = math.radians(lean)
                dx, dy = p[0] - x, p[1] - y
                p = (x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a), p[2])
            return fr(p)
        cover_l, top_l = srgb_to_linear(cover), srgb_to_linear(top)
        zb = zs - d

        def quad(pts, colour):
            base = len(self.v)
            self.v += [place(p) for p in pts]
            self.c += [colour] * 4
            self.f.append((base, base + 1, base + 2, base + 3))
        # the spine, divided top to bottom so the light falling down it is smooth
        ys = [y + h * j / rows for j in range(rows + 1)]
        if spine_uv:
            u0, v0, u1, v1 = spine_uv
            base = len(self.sv)
            for j, yy in enumerate(ys):
                self.sv += [place((x, yy, zs)), place((x + t, yy, zs))]
            for j in range(rows):
                a = base + 2 * j
                self.sf.append((a, a + 1, a + 3, a + 2))
                vv0, vv1 = v0 + (v1 - v0) * j / rows, v0 + (v1 - v0) * (j + 1) / rows
                self.suv.append([(u0, vv0), (u1, vv0), (u1, vv1), (u0, vv1)])
        else:
            base = len(self.v)
            for yy in ys:
                self.v += [place((x, yy, zs)), place((x + t, yy, zs))]
                self.c += [cover_l, cover_l]
            for j in range(rows):
                a = base + 2 * j
                self.f.append((a, a + 1, a + 3, a + 2))
        quad([(x, y + h, zs), (x + t, y + h, zs), (x + t, y + h, zb), (x, y + h, zb)], top_l)       # the top
        quad([(x, y, zb), (x, y, zs), (x, y + h, zs), (x, y + h, zb)], cover_l)                     # left side
        quad([(x + t, y, zs), (x + t, y, zb), (x + t, y + h, zb), (x + t, y + h, zs)], cover_l)     # right side

    def flush(self):
        if self.v:
            self.k.b.mesh(G, "library_albedo", self.v, self.f, smooth=False, colors=self.c)
        if self.sv:
            self.k.b.mesh(G, "library_spines", self.sv, self.sf, smooth=False, uvs=self.suv)


def build_library(b):
    LAMPS.clear()
    titled = read_books()
    cells = paint_spines(titled)
    paint_pictures()
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    rng = np.random.default_rng(3)
    with b.room(ROOM):
        books = Books(k)
        runs = shelving(k)
        stock(k, books, runs, titled, cells, rng)
        books.flush()
        rail_and_ladder(k)
        rug(k)
        desk(k)
        desk_chair(k, Frame((DESK["cx"] - 0.10, F2, DESK["z1"] - DESK["d"] - 0.22), 4.0))
        banker_lamp(k)
        laptop(k)
        # hotspot anchors: the eye-level shelf of real titles (between bays 3 and 4, at the
        # spines' middle height) and the laptop's screen
        b.anchor("library_real_books", (XE - DEP + 0.01, F2 + BOARDS[EYE_ROWS[0]] + BT + 0.12,
                                        (_bay_z(TITLE_BAYS[0]) + _bay_z(TITLE_BAYS[1])) / 2))
        b.anchor("library_laptop", laptop_screen())
        manuscript(k)
        reading_corner(k)
        shelf_lights()
        ceiling(Kit(b, "roof", None))


# ---- the shelving ---------------------------------------------------------------------------
def case(k, fr, L, n, bridge=False):
    """One run of shelving against a wall, `n` bays over length L in the run frame fr
    (origin at the wall at the run's left end, x along the wall, z out into the room).
    Returns the shelves' runs as (x0, x1, board index, board top, clear height)."""
    inner = (L - (n + 1) * UP) / n
    world_step = 0.12
    xs = [i * (inner + UP) for i in range(n + 1)]
    y0 = 0.0 if not bridge else BRIDGE_Y
    for x in xs if not bridge else ():                                     # uprights (the bridge shares its neighbours')
        k.grain("library_walnut", fr, (x, y0, 0.0), (x + UP, CORNICE[1], DEP), step=world_step, skip=("-z",), along="y")
    # the cornice, a little proud of the cases, up to the ceiling
    k.grain("library_walnut", fr, (0.0, CORNICE[0], 0.0), (L, CORNICE[1], DEP + 0.025), step=world_step, skip=("-z",))
    runs = []
    boards = BOARDS if not bridge else (BRIDGE_Y,)
    for i in range(n):
        a, c = xs[i] + UP, xs[i + 1]
        if not bridge:                                                     # the kick under the bottom board
            k.grain("library_walnut", fr, (a, 0.0, 0.0), (c, BOARDS[0] - BT, DEP - 0.035), step=world_step,
                    skip=("-z", "-y", "+y", "-x", "+x"))
        k.grain("library_walnut", fr, (a, y0 if bridge else BOARDS[0], 0.012), (c, CORNICE[0], 0.018),
                step=0.15, skip=("-z", "-x", "+x", "-y", "+y"))                 # the back panel
        for bi, top in enumerate(boards):
            k.grain("library_walnut", fr, (a, top - BT, 0.012), (c, top, DEP), step=world_step,
                    skip=("-z", "-x", "+x") + (("-y",) if bi == 0 and not bridge else ()))
            nxt = boards[bi + 1] - BT if bi + 1 < len(boards) else CORNICE[0]
            runs.append(dict(fr=fr, x0=a, x1=c, bay=i, board=bi, y=top, clear=nxt - top))
    return runs


def shelving(k):
    """Cases on the east wall (eight bays), and on the back wall either side of the
    trophy room's door, with a shelf bridging over it."""
    runs = {}
    east = Frame((XE, F2, Z0 + DEP), -90.0)               # +x along the wall toward the front, +z into the room
    runs["east"] = case(k, east, ZF - (Z0 + DEP), EAST_BAYS)
    d0, d1 = TROPHY_DOOR
    left = Frame((XW, F2, Z0), 0.0)
    runs["left"] = case(k, left, d0 - 0.05 - XW, 6)
    right = Frame((d1 + 0.05, F2, Z0), 0.0)
    runs["right"] = case(k, right, XE - (d1 + 0.05), 4)
    bridge = Frame((d0 - 0.05 - UP, F2, Z0), 0.0)
    runs["bridge"] = case(k, bridge, (d1 + 0.05 + UP) - (d0 - 0.05 - UP), 1, bridge=True)
    return runs


# ---- the books -------------------------------------------------------------------------------
PALETTE = [(0.42, 0.10, 0.09), (0.10, 0.14, 0.27), (0.13, 0.26, 0.17), (0.07, 0.07, 0.07), (0.66, 0.52, 0.36),
           (0.84, 0.79, 0.67), (0.88, 0.87, 0.84), (0.42, 0.43, 0.44), (0.72, 0.56, 0.20), (0.33, 0.22, 0.14),
           (0.12, 0.33, 0.34), (0.70, 0.33, 0.15), (0.45, 0.55, 0.66), (0.40, 0.40, 0.22), (0.33, 0.08, 0.13),
           (0.55, 0.15, 0.12), (0.20, 0.20, 0.22)]
PAGES = (0.80, 0.76, 0.66)


def _jitter(c, rng, amount=0.12):
    s = 1.0 + rng.uniform(-amount, amount)
    return tuple(float(np.clip(v * s, 0, 1)) for v in c)


def unmarked_row(books, run, rng, x_start=None, x_end=None, fill=1.0):
    """Unmarked books standing along a shelf, in little sets that share a height and a
    colour family, as real shelves do. Returns where the row ended."""
    fr, y, clear = run["fr"], run["y"], run["clear"]
    x = run["x0"] + 0.004 if x_start is None else x_start
    end = run["x1"] - 0.004 if x_end is None else x_end
    end = x + (end - x) * fill
    last = None
    while True:
        n = int(rng.integers(2, 9))
        h0 = min(clear - 0.025, float(rng.choice([0.18, 0.20, 0.215, 0.235, 0.25, 0.28])))
        base = PALETTE[int(rng.integers(len(PALETTE)))]
        mu = float(rng.uniform(0.022, 0.042))
        placed = False
        for _ in range(n):
            t = float(np.clip(rng.normal(mu, 0.006), 0.014, 0.065))
            if x + t > end:
                break
            h = min(clear - 0.02, h0 * float(rng.uniform(0.97, 1.03)))
            d = min(DEP - 0.045, h * float(rng.uniform(0.66, 0.80)))
            cover = _jitter(base if rng.random() < 0.75 else PALETTE[int(rng.integers(len(PALETTE)))], rng)
            books.add(fr, x, y, DEP - 0.022 - float(rng.uniform(0, 0.012)), t, h, d, cover, _jitter(PAGES, rng, 0.06))
            last = (x, t, h)
            x += t + float(rng.uniform(0.0, 0.0015))
            placed = True
        if not placed:
            break
    return x, last


def lean_one(books, run, x, rng):
    """A book leaning against the end of a row, if there's room for one."""
    h = min(run["clear"] - 0.03, float(rng.uniform(0.19, 0.24)))
    t = float(rng.uniform(0.022, 0.035))
    a = float(rng.uniform(14, 24))
    xb = x + h * math.sin(math.radians(a)) + 0.002
    if xb + t * math.cos(math.radians(a)) > run["x1"] - 0.01:
        return
    books.add(run["fr"], xb, run["y"], DEP - 0.03, t, h, min(DEP - 0.05, h * 0.72),
              _jitter(PALETTE[int(rng.integers(len(PALETTE)))], rng), _jitter(PAGES, rng, 0.06), lean=a)


def flat_stack(books, run, x, rng, n=None):
    """A short stack of books lying flat, spines out. Returns its width and height."""
    n = n or int(rng.integers(3, 7))
    y = run["y"]
    widest = 0.0
    for i in range(n):
        L = float(rng.uniform(0.20, min(0.28, run["x1"] - x - 0.01)))
        t = float(rng.uniform(0.02, 0.04))
        if y + t > run["y"] + run["clear"] - 0.06:
            break
        dx = float(rng.uniform(-0.01, 0.01))
        books.add(run["fr"], x + dx, y, DEP - 0.025, L, t, min(DEP - 0.05, L * 0.75),
                  _jitter(PALETTE[int(rng.integers(len(PALETTE)))], rng), _jitter(PAGES, rng, 0.06), rows=1)
        y += t
        widest = max(widest, L + dx)
    return widest, y - run["y"]


def ornament(k, run, x, rng, kind=None, on=0.0):
    """Something that isn't a book: a vase, a brass sphere, an hourglass, a small walnut
    box. Returns how wide it is."""
    fr, y = run["fr"], run["y"] + on
    kind = kind or ["vase", "sphere", "hourglass", "box", "vase_dark"][int(rng.integers(5))]
    zc = DEP * 0.55
    if kind in ("vase", "vase_dark"):
        s = float(rng.uniform(0.85, 1.15))
        mat = "ceramic_white" if kind == "vase" else "library_ink"
        prof = [(0.0, 0.0), (0.045, 0.0), (0.06, 0.03), (0.062, 0.10), (0.04, 0.17), (0.026, 0.20), (0.03, 0.215),
                (0.024, 0.215), (0.0, 0.205)]
        k.lathe(mat, Frame(fr((x + 0.065 * s, y, zc))), [(r * s, h * s) for r, h in prof], 28)
        return 0.13 * s
    if kind == "sphere":
        r = float(rng.uniform(0.045, 0.06))
        k.lathe("library_brass", Frame(fr((x + r, y, zc))),
                [(0.0, 0.0)] + [(r * math.sin(math.pi * s), r - r * math.cos(math.pi * s)) for s in np.linspace(0.05, 1, 12)], 24)
        return 2 * r
    if kind == "hourglass":
        f = Frame(fr((x + 0.05, y, zc)))
        k.lathe("library_walnut_v", f, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.012), (0.0, 0.012)], 24)
        k.lathe("library_walnut_v", f, [(0.0, 0.168), (0.05, 0.168), (0.05, 0.18), (0.0, 0.18)], 24)
        for a in range(3):
            ang = 2 * math.pi * a / 3 + 0.4
            p = (x + 0.05 + 0.042 * math.cos(ang), y + 0.012, zc + 0.042 * math.sin(ang))
            k.tube("library_brass", fr(p), fr((p[0], y + 0.168, p[2])), 0.004, segments=6)
        k.lathe("hourglass_glass", f, [(0.0, 0.014), (0.03, 0.03), (0.034, 0.06), (0.006, 0.09), (0.034, 0.12),
                                       (0.03, 0.15), (0.0, 0.166)], 24)
        k.lathe("hourglass_sand", f, [(0.0, 0.016), (0.026, 0.03), (0.024, 0.045), (0.0, 0.052)], 20)
        return 0.10
    # a small walnut box
    w = float(rng.uniform(0.14, 0.20))
    k.soft("library_walnut_v", fr, (x + w / 2, y + 0.04, zc), (w, 0.08, 0.12), 0.006, n=2)
    return w


def stock(k, books, runs, titled, cells, rng):
    """Every shelf: the titled books on the east wall's eye-level shelves, unmarked
    books everywhere else, a few lying flat or leaning, and some objects."""
    east = runs["east"]
    by = {(r["bay"], r["board"]): r for r in east}
    slots = [by[(bay, board)] for board in EYE_ROWS for bay in TITLE_BAYS[:2]] + \
            [by[(bay, board)] for board in EYE_ROWS for bay in TITLE_BAYS[2:]]
    used = set()
    i, si = 0, 0
    x = None
    while i < len(titled) and si < len(slots):
        run = slots[si]
        if x is None:
            x = run["x0"] + 0.03
        # keep a group together if what's left of this shelf only takes a few of it
        group = [bk for bk in titled[i:] if bk["group"] == titled[i]["group"]]
        room = run["x1"] - 0.02 - x
        width = sum(bk["t"] for bk in group)
        if width > room and room < 0.07 and x > run["x0"] + 0.05:
            si, x = si + 1, None
            continue
        bk = titled[i]
        if x + bk["t"] > run["x1"] - 0.02:
            used.add(id(run))
            si, x = si + 1, None
            continue
        if i > 0 and titled[i - 1]["group"] != bk["group"] and x > run["x0"] + 0.05:
            x += 0.018                                       # a little space between authors
            if x + bk["t"] > run["x1"] - 0.02:
                continue
        books.add(run["fr"], x, run["y"], DEP - 0.02, bk["t"], bk["h"], bk["d"], bk["ground"], _jitter(PAGES, rng, 0.04),
                  spine_uv=cells[i], rows=4)
        used.add(id(run))
        x += bk["t"] + 0.0008
        i += 1
    if i < len(titled):
        print(f"[library] {len(titled) - i} titled books didn't fit on the eye-level shelves; add bays to TITLE_BAYS")
    # finish the last titled shelf with a brass bookend and an object
    if x is not None and si < len(slots):
        run = slots[si]
        k.soft("library_brass", run["fr"], (x + 0.004, run["y"] + 0.08, DEP * 0.55), (0.006, 0.16, 0.12), 0.002, n=1)
        k.soft("library_brass", run["fr"], (x + 0.05, run["y"] + 0.003, DEP * 0.55), (0.09, 0.006, 0.12), 0.002, n=1)
        x += 0.10
        if run["x1"] - x > 0.16:
            x += ornament(k, run, x, rng, "hourglass") + 0.03
        if run["x1"] - x > 0.12:
            unmarked_row(books, run, rng, x_start=x)
    # everything else
    for name in ("east", "left", "right", "bridge"):
        for run in runs[name]:
            if id(run) in used:
                continue
            r = rng.random()
            if r < 0.12 and run["clear"] > 0.24:                           # an object at one end
                if rng.random() < 0.5:
                    w = ornament(k, run, run["x0"] + 0.04, rng)
                    unmarked_row(books, run, rng, x_start=run["x0"] + 0.08 + w)
                else:
                    xe, _ = unmarked_row(books, run, rng, x_end=run["x1"] - 0.22)
                    ornament(k, run, xe + 0.04, rng)
            elif r < 0.22:                                                  # a stack lying flat, maybe with something on it
                w, h = flat_stack(books, run, run["x1"] - 0.30, rng)
                if rng.random() < 0.5 and run["clear"] - h > 0.12:
                    ornament(k, run, run["x1"] - 0.30 + w / 2 - 0.05, rng, "sphere", on=h)
                unmarked_row(books, run, rng, x_end=run["x1"] - 0.34)
            elif r < 0.32:                                                  # a short row, one leaning
                xe, _ = unmarked_row(books, run, rng, fill=float(rng.uniform(0.6, 0.85)))
                lean_one(books, run, xe, rng)
            else:
                unmarked_row(books, run, rng)


# ---- the rail and the ladder ------------------------------------------------------------------
def rail_and_ladder(k):
    """A brass rail along the east wall's cases, and a walnut library ladder hooked on it."""
    rx = XE - DEP - 0.075
    ry = F2 + 2.30
    z0, z1 = Z0 + DEP + 0.25, ZF - 0.25
    k.tube("library_brass", (rx, ry, z0), (rx, ry, z1), 0.014, segments=12, step=0.25)
    for z in np.linspace(z0 + 0.05, z1 - 0.05, 5):
        k.tube("library_brass", (XE - DEP, ry, z), (rx, ry, z), 0.009, segments=8)
    # the ladder: two stiles from the floor up to hooks over the rail, rungs between
    zl = LADDER_Z
    foot_x = rx - 0.78
    for side in (-0.21, 0.21):
        top = (rx - 0.01, ry + 0.04, zl + side)
        foot = (foot_x, F2 + 0.06, zl + side)
        k.rod("library_walnut_v", foot, top, 0.045)
        k.sweep("library_brass", [top, (rx + 0.005, ry + 0.05, zl + side), (rx + 0.03, ry + 0.02, zl + side)], 0.006, 8)
        k.lathe("library_brass", Frame((foot_x, F2, zl + side)), [(0.0, 0.0), (0.03, 0.0), (0.03, 0.06), (0.0, 0.06)], 16)
    for i in range(1, 8):
        t = i / 8.3
        p = (foot_x + (rx - 0.01 - foot_x) * t, F2 + 0.06 + (ry - F2 - 0.02) * t)
        k.rod("library_walnut_v", (p[0], p[1], zl - 0.19), (p[0], p[1], zl + 0.19), 0.03)


# ---- the rug, the desk, the chair ----------------------------------------------------------------
def rug(k):
    """A traditional rug, original: an oxblood field with a navy lozenge and border,
    fine cream lines, worn and mottled. Painted per vertex on a fine grid."""
    (x0, x1), (z0, z1), t = RUG["x"], RUG["z"], RUG["t"]
    rng = np.random.default_rng(12)
    step = 0.04
    nx, nz = round((x1 - x0) / step), round((z1 - z0) / step)
    mottle = _smooth_noise((nx + 1, nz + 1), 5, rng)
    field, navy, cream, rust = (np.array(c) for c in ((0.40, 0.10, 0.08), (0.10, 0.12, 0.22), (0.80, 0.72, 0.58), (0.58, 0.24, 0.12)))
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    verts, colors = [], []
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = x0 + (x1 - x0) * i / nx, z0 + (z1 - z0) * j / nz
            verts.append((x, F2 + t, z))
            d = min(x - x0, x1 - x, z - z0, z1 - z)
            lz = abs(x - cx) / ((x1 - x0) * 0.30) + abs(z - cz) / ((z1 - z0) * 0.30)     # the lozenge
            if d < 0.30:
                c = cream if (0.06 < d < 0.08 or 0.22 < d < 0.24) else navy
            elif lz < 0.42:
                c = rust if lz < 0.25 else navy
            elif abs(lz - 1.0) < 0.03:
                c = cream
            else:
                c = field
            c = c * (1 + 0.08 * mottle[i, j])
            colors.append(srgb_to_linear(tuple(np.clip(c, 0, 1))))
    faces = [(i * (nz + 1) + j, i * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j)
             for i in range(nx) for j in range(nz)]
    k.b.mesh(G, "library_albedo", verts, faces, smooth=False, colors=colors)
    edge = srgb_to_linear(tuple(navy * 0.8))
    for a, c in (((x1, z0), (x0, z0)), ((x0, z0), (x0, z1)), ((x0, z1), (x1, z1)), ((x1, z1), (x1, z0))):
        k.b.mesh(G, "library_albedo", [(a[0], F2, a[1]), (c[0], F2, c[1]), (c[0], F2 + t, c[1]), (a[0], F2 + t, a[1])],
                 [(0, 1, 2, 3)], colors=[edge] * 4)


def desk_frame():
    """The desk's frame: origin on the floor at the middle of its front edge (the
    sitter's side), +z toward the glass, +x to the sitter's left."""
    return Frame((DESK["cx"], F2, DESK["z1"] - DESK["d"]), 0.0)


def desk(k):
    """A walnut writing desk: a slab top over a slim apron with a shallow drawer, on
    four square legs."""
    f = desk_frame()
    w, d, top = DESK["w"], DESK["d"], DESK["top"]
    t, leg, apron = 0.035, 0.055, 0.11
    k.grain("library_walnut", f, (-w / 2, top - t, 0.0), (w / 2, top, d), step=0.07)
    for x in (-w / 2 + 0.03, w / 2 - 0.03 - leg):
        for z in (0.03, d - 0.03 - leg):
            k.grain("library_walnut", f, (x, 0.0, z), (x + leg, top - t, z + leg), step=0.08, skip=("-y", "+y"), along="y")
    k.grain("library_walnut", f, (-w / 2 + 0.05, top - t - apron, 0.05), (w / 2 - 0.05, top - t, d - 0.05), step=0.09,
            skip=("+y",))
    k.block("library_ink", f, (-0.32, top - t - apron + 0.012, 0.045), (0.32, top - t - apron + 0.016, 0.052), step=0.3)
    k.block("library_ink", f, (-0.32, top - t - 0.016, 0.045), (0.32, top - t - 0.012, 0.052), step=0.3)
    k.soft("library_brass", f, (0.0, top - t - apron / 2, 0.042), (0.08, 0.012, 0.012), 0.004, n=1)


def desk_chair(k, f, leather="library_leather", wood="library_walnut_v", brass="library_brass"):
    """An upholstered desk chair in the reading chair's leather, facing the desk (+z):
    a deep seat, dished where you sit, its front edge rolled over; a padded back that
    wraps round the sitter, swells at the small of the back and leans back a little,
    with a raised welt round its edge; padded arms on curved walnut arms; and four
    tapered walnut legs, splayed slightly, with brass caps. (The trophy room's chess
    table has a pair, in its own materials.)"""
    from .kit import cushion, rot
    seat = 0.47

    def place(mat, verts, faces, centre, tilt=0.0, pivot=(0, 0, 0)):
        T = rot(x=tilt)
        pv, c = np.asarray(pivot, float), np.asarray(centre, float)
        k.b.mesh(k.g, mat, [f(pv + T @ (c + np.asarray(v) - pv)) for v in verts], faces)

    # the legs, tapering to brass caps, and a walnut rail under the seat
    for sx in (-1, 1):
        for sz in (-1, 1):
            top = (sx * 0.205, seat - 0.075, sz * 0.195)
            foot = (sx * 0.235, 0.022, sz * (0.225 if sz > 0 else 0.245))
            k.tube(wood, f(foot), f(top), 0.012, segments=12, r1=0.020)
            k.lathe(brass, Frame(f((foot[0], 0.0, foot[2]))), [(0.0, 0.0), (0.0125, 0.0), (0.0125, 0.024), (0.0, 0.024)], 14)
    k.soft(wood, f, (0.0, seat - 0.095, 0.0), (0.47, 0.055, 0.45), 0.014, n=2)

    # the seat: deep, dished in the middle, the front rolled down over the rail
    W, D, T = 0.52, 0.50, 0.105
    v, fc = cushion((W, T, D), 0.042, n=3, div=10)
    out = []
    for x, y, z in v:
        if y > 0:
            y -= 0.018 * max(0.0, 1 - (2 * x / W) ** 2) * max(0.0, 1 - (2 * (z + 0.03) / D) ** 2)
        fz = (z - (D / 2 - 0.10)) / 0.10
        if fz > 0:
            y -= 0.035 * fz ** 2
        out.append((x, y, z))
    place(leather, out, fc, (0.0, seat - 0.02, 0.015))

    # the back: wrapped round the sitter, a lumbar swell, a little wider at the shoulders
    H, lean, pivot = 0.50, -10.0, (0.0, seat, -0.22)

    def shape_back(verts, h, R=0.42, lumbar=0.028):
        res = []
        for x, y, z in verts:
            t = (y + h / 2) / h
            x *= 0.93 + 0.09 * math.sin(min(1.0, t * 1.3) * math.pi / 2)
            z += x * x / (2 * R) + lumbar * math.exp(-((t - 0.28) / 0.18) ** 2)
            res.append((x, y, z))
        return res
    centre = (0.0, seat + 0.07 + H / 2, -0.225)
    v, fc = cushion((0.48, H, 0.075), 0.034, n=3, div=10)
    place(leather, shape_back(v, H), fc, centre, lean, pivot)
    # its back shell, a size bigger, standing proud behind the cushion like a welted edge
    v, fc = cushion((0.50, H + 0.025, 0.03), 0.013, n=2, div=10)
    place(leather, shape_back(v, H + 0.025, lumbar=0.0), fc, (0.0, centre[1], centre[2] - 0.045), lean, pivot)
    # the back's two walnut stiles, from the back legs up behind its edges
    for sx in (-1, 1):
        Rb = rot(x=lean)
        top = np.asarray(pivot) + Rb @ (np.array((sx * 0.215, seat + 0.07 + H * 0.85, -0.25)) - np.asarray(pivot))
        k.tube(wood, f((sx * 0.205, seat - 0.075, -0.195)), f(tuple(top)), 0.013, segments=10)

    # the arms: walnut sweeps from the back to the front legs, with a padded leather rest
    for sx in (-1, 1):
        x = sx * 0.268
        path = [(sx * 0.215, seat + 0.17, -0.235), (x, seat + 0.215, -0.13), (x, seat + 0.225, 0.02),
                (x - sx * 0.01, seat + 0.19, 0.15), (sx * 0.215, seat - 0.07, 0.195)]
        smooth = []
        for a, c in zip(path, path[1:]):
            for t in np.linspace(0, 1, 5, endpoint=False):
                smooth.append(tuple(np.add(a, np.subtract(c, a) * t)))
        smooth.append(path[-1])
        k.sweep(wood, [f(p) for p in smooth], 0.012, 10)
        v, fc = cushion((0.065, 0.032, 0.28), 0.014, n=2, div=4)
        rest = [(vx, vy - 0.006 * (2 * vz / 0.28) ** 2, vz) for vx, vy, vz in v]          # a gentle crown along it
        place(leather, rest, fc, (x, seat + 0.245, -0.045))


def banker_lamp(k):
    """A green banker's lamp: a brass base and stem, a pull chain, and the cased green
    glass shade, its inside glowing."""
    f = desk_frame()
    top = DESK["top"]
    bx, bz = 0.52, DESK["d"] - 0.22
    base = Frame(f((bx, top, bz)), f.yaw)
    k.soft("library_brass", base, (0.0, 0.012, 0.0), (0.24, 0.024, 0.15), 0.01, n=2)
    stem = f((bx, top, bz - 0.03))
    k.tube("library_brass", (stem[0], stem[1] + 0.02, stem[2]), (stem[0], stem[1] + 0.33, stem[2]), 0.007, segments=10)
    k.tube("library_brass", (stem[0], stem[1] + 0.33, stem[2]), (stem[0], stem[1] + 0.36, stem[2] - 0.04), 0.006, segments=8)
    # the shade: half a cylinder, 30 cm long, opening down, tipped toward the sitter
    cx, cy, cz = stem[0], stem[1] + 0.37, stem[2] - 0.05
    L, R, n, m = 0.30, 0.075, 18, 6
    outer, inner = [], []
    T = np.array([[1, 0, 0], [0, math.cos(-0.22), -math.sin(-0.22)], [0, math.sin(-0.22), math.cos(-0.22)]])   # front edge down
    for i in range(m + 1):
        x = -L / 2 + L * i / m
        for j in range(n + 1):
            a = math.pi * j / n
            for lst, r in ((outer, R), (inner, R - 0.004)):
                p = T @ np.array((x, r * math.sin(a) * 0.85, -r * math.cos(a)))
                lst.append((cx + p[0], cy + p[1], cz + p[2]))
    faces_o = [(i * (n + 1) + j, (i + 1) * (n + 1) + j, (i + 1) * (n + 1) + j + 1, i * (n + 1) + j + 1)
               for i in range(m) for j in range(n)]
    k.b.mesh(G, "banker_green", outer, [f_[::-1] for f_ in faces_o], smooth=True)
    k.b.mesh(G, "banker_glow", inner, faces_o, smooth=True)
    for sx in (-1, 1):                                          # the shade's ends
        ring = [outer[(0 if sx < 0 else m) * (n + 1) + j] for j in range(n + 1)]
        c = np.mean(ring, axis=0)
        verts = [tuple(c)] + ring
        fc = [(0, j + 1, j + 2) if sx > 0 else (0, j + 2, j + 1) for j in range(n)]
        k.b.mesh(G, "banker_green", verts, fc, smooth=False)
    k.tube("library_brass", (cx + 0.05, cy - 0.03, cz), (cx + 0.05, cy - 0.20, cz), 0.0012, segments=4)
    k.lathe("library_brass", Frame((cx + 0.05, cy - 0.215, cz)), [(0.0, 0.0), (0.006, 0.004), (0.004, 0.016), (0.0, 0.018)], 10)
    LAMPS.append(dict(name="banker_lamp", kind="spot", pos=(cx, cy - 0.03, cz), aim=(-0.15, -1.0, -0.35), watts=26.0, cone=110.0))
    LAMPS.append(dict(name="banker_glow", kind="point", pos=(cx, cy + 0.02, cz), watts=1.2, radius=0.05, colour=(0.45, 0.9, 0.55)))


def laptop_frame():
    """The laptop's own frame on the desk: its front (+z) toward the sitter."""
    return Frame(desk_frame()((-0.08, DESK["top"], 0.36)), desk_frame().yaw + 180.0 - 6.0)


def laptop_screen():
    """The middle of the laptop's screen, in the world (the hotspot anchor)."""
    T, D, tilt = 0.014, 0.215, math.radians(-20.0)    # as in `laptop`: the lid tipped back about the hinge
    y = 0.10                                          # the screen's middle, up the lid from the hinge
    return laptop_frame()((0.0, T + y * math.cos(tilt), -D / 2 + y * math.sin(tilt)))


def laptop(k):
    """An open laptop, a little off centre, the draft on its screen."""
    g = laptop_frame()                                           # its front (+z) toward the sitter
    W, D, T = 0.31, 0.215, 0.014
    k.soft("aluminium", g, (0.0, T / 2, 0.0), (W, T, D), 0.004, n=2)
    k.quad("laptop_keys", g, [(-0.13, T + 0.0005, 0.005), (0.13, T + 0.0005, 0.005), (0.13, T + 0.0005, -0.095),
                              (-0.13, T + 0.0005, -0.095)])
    k.quad("library_ink", g, [(-0.05, T + 0.0004, 0.085), (0.05, T + 0.0004, 0.085), (0.05, T + 0.0004, 0.02),
                              (-0.05, T + 0.0004, 0.02)])
    # the lid, tipped back about 110 degrees from the base
    hinge = (0.0, T, -D / 2)
    tilt = -20.0
    k.soft("aluminium", g, (0.0, T + 0.10, -D / 2 - 0.003), (W, 0.205, 0.006), 0.003, n=1, tilt=tilt, pivot=hinge)
    k.soft("library_ink", g, (0.0, T + 0.10, -D / 2 + 0.0005), (W - 0.004, 0.201, 0.001), 0.0005, n=1, tilt=tilt, pivot=hinge)
    R = np.array([[1, 0, 0], [0, math.cos(math.radians(tilt)), -math.sin(math.radians(tilt))],
                  [0, math.sin(math.radians(tilt)), math.cos(math.radians(tilt))]])
    v, fc, uv = grid((-0.14, T + 0.012, -D / 2 + 0.0012), (0.28, 0, 0), (0, 0.175, 0), 8, 5)
    hv = np.array(hinge)
    v = [tuple(hv + R @ (np.array(p) - hv)) for p in v]
    k.mesh("laptop_screen", g, v, fc, smooth=False, uvs=uv)
    LAMPS.append(dict(name="laptop_glow", pos=g((0.0, T + 0.12, -D / 2 + 0.12)), size=(0.26, 0.16), watts=1.5,
                      aim=tuple(np.subtract(g((0, -0.3, 1)), g((0, 0, 0)))), colour=(0.85, 0.9, 1.0)))


def manuscript(k):
    """The manuscript: a stack of typed pages held with a black clip, a few loose pages
    fanned beside it, and a pen."""
    f = desk_frame()
    top = DESK["top"]
    g = Frame(f((-0.47, top, 0.32)), f.yaw + 180.0 + 4.0)
    W, D, T = 0.216, 0.279, 0.042
    k.box("paper_edge", g, (-W / 2, 0.0, -D / 2), (W / 2, T, D / 2), skip=("-y", "+y"))
    v, fc, uv = grid((-W / 2, T, D / 2), (W, 0, 0), (0, 0, -D), 6, 8)
    k.mesh("manuscript", g, v, fc, smooth=False, uvs=uv)
    # the clip at the top edge
    k.soft("library_ink", g, (0.0, T - 0.004, -D / 2 + 0.012), (0.05, 0.018, 0.028), 0.002, n=1)
    for sx in (-1, 1):
        k.tube("aluminium", g((sx * 0.018, T + 0.004, -D / 2 + 0.018)), g((sx * 0.018, T + 0.010, -D / 2 - 0.025)), 0.0012,
               segments=4)
    # loose pages, fanned, and a pen across them
    for i, (dx, dz, turn) in enumerate(((0.20, 0.03, -10.0), (0.22, 0.06, -20.0))):
        h = Frame(g((dx, 0.0006 * (i + 1), dz)), g.yaw + turn)
        v, fc, uv = grid((-W / 2, 0.0, D / 2), (W, 0, 0), (0, 0, -D), 3, 4)
        k.mesh("manuscript", h, v, fc, smooth=False, uvs=uv)
    p0, p1 = g((-0.03, T + 0.005, 0.05)), g((0.07, T + 0.005, -0.07))
    k.tube("library_ink", p0, p1, 0.0045, segments=8)
    k.tube("library_brass", p1, tuple(np.add(p1, np.subtract(p1, p0) * 0.05)), 0.0045, segments=8, r1=0.0015)
    # a coffee cup at the far corner
    c = Frame(f((0.25, top, 0.16)))
    k.lathe("ceramic_white", c, [(0.0, 0.0), (0.035, 0.0), (0.042, 0.01), (0.045, 0.09), (0.042, 0.09), (0.039, 0.012), (0.0, 0.01)], 28)
    k.disc("library_ink", c, (0.0, 0.075, 0.0), 0.039, 20)
    k.sweep("ceramic_white", [c((0.044 + 0.022 * math.sin(math.pi * s), 0.025 + 0.045 * s, 0.0)) for s in np.linspace(0, 1, 9)],
            0.005, 8)


def reading_corner(k):
    """A deep leather club chair by the window, an ottoman, a round side table with a
    book on it, and a brass floor lamp to read by."""
    (x, z), yaw = CHAIR["pos"], CHAIR["yaw"]
    f = Frame((x, F2, z), yaw)
    leather = "library_leather"
    W, D = 0.88, 0.86
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = f((sx * (W / 2 - 0.08), 0.0, sz * (D / 2 - 0.08)))
            k.tube("library_ink", p, (p[0], p[1] + 0.09, p[2]), 0.016, segments=8, r1=0.022)
    k.soft(leather, f, (0.0, 0.21, 0.0), (W, 0.24, D), 0.05)                                  # the base
    for sx in (-1, 1):                                                                         # rolled arms
        k.soft(leather, f, (sx * (W / 2 - 0.085), 0.40, 0.02), (0.17, 0.42, D - 0.04), 0.08)
    k.soft(leather, f, (0.0, 0.58, -D / 2 + 0.11), (W, 0.70, 0.22), 0.09, tilt=-8, pivot=(0, 0.2, -D / 2 + 0.11))     # back
    k.soft(leather, f, (0.0, 0.40, 0.06), (W - 0.34, 0.14, D - 0.26), 0.05)                     # seat cushion
    k.soft(leather, f, (0.0, 0.62, -D / 2 + 0.26), (W - 0.36, 0.40, 0.13), 0.06, tilt=-10, pivot=(0, 0.4, -D / 2 + 0.26))
    # the ottoman, in front
    o = Frame(f((0.0, 0.0, D / 2 + 0.42)), yaw + 4)
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = o((sx * 0.22, 0.0, sz * 0.17))
            k.tube("library_ink", p, (p[0], p[1] + 0.08, p[2]), 0.014, segments=8, r1=0.018)
    k.soft(leather, o, (0.0, 0.25, 0.0), (0.56, 0.34, 0.44), 0.06)
    # the side table, on the chair's left, with a book and a glass
    st = Frame(f((W / 2 + 0.34, 0.0, 0.10)))
    k.lathe("library_brass", st, [(0.0, 0.0), (0.16, 0.0), (0.16, 0.012), (0.02, 0.02), (0.016, 0.52), (0.0, 0.52)], 32)
    k.lathe("library_walnut_v", st, [(0.0, 0.52), (0.25, 0.52), (0.25, 0.55), (0.0, 0.55)], 48)
    book_flat(k, Frame(st((0.02, 0.55, 0.0)), yaw + 30), (0.0, 0.0), (0.22, 0.03, 0.15), "book_rust")
    k.lathe("hourglass_glass", Frame(st((-0.13, 0.55, 0.08))),
            [(0.0, 0.0), (0.036, 0.0), (0.038, 0.09), (0.034, 0.09), (0.032, 0.006), (0.0, 0.006)], 24)
    k.disc("whisky", Frame(st((-0.13, 0.55, 0.08))), (0.0, 0.03, 0.0), 0.032, 20)
    # the floor lamp, behind the chair's left shoulder
    lx, ly, lz = f((W / 2 + 0.10, 0.0, -D / 2 - 0.05))
    lf = Frame((lx, ly, lz))
    k.lathe("library_ink", lf, [(0.0, 0.0), (0.15, 0.0), (0.15, 0.012), (0.13, 0.024), (0.02, 0.03), (0.0, 0.03)], 40)
    k.tube("library_brass", (lx, ly + 0.025, lz), (lx, ly + 1.45, lz), 0.0095, segments=10)
    y0, y1, r = 1.28, 1.58, 0.20
    k.lathe("library_shade", lf, [(r, y0), (r, y1)], 48)
    k.lathe("library_shade", lf, [(r - 0.004, y1), (r - 0.004, y0)], 48)
    k.disc("light_warm", lf, (0.0, y0 + 0.06, 0.0), r - 0.03, 32, down=True)
    for a in range(3):
        ang = 2 * math.pi * a / 3
        k.tube("library_brass", (lx, ly + 1.45, lz), (lx + (r - 0.005) * math.cos(ang), ly + y1 - 0.01, lz + (r - 0.005) * math.sin(ang)),
               0.003, segments=6)
    LAMPS.append(dict(name="reading_lamp_down", pos=(lx, ly + y0 + 0.04, lz), size=(0.28, 0.28), watts=30.0, aim=(0.0, -1.0, 0.0)))
    LAMPS.append(dict(name="reading_lamp_up", pos=(lx, ly + y1 - 0.04, lz), size=(0.28, 0.28), watts=14.0, aim=(0.0, 1.0, 0.0)))
    LAMPS.append(dict(name="reading_lamp_glow", kind="point", pos=(lx, ly + (y0 + y1) / 2, lz), watts=6.0, radius=0.12))


def ceiling(k):
    """The house's oak ceiling again, laid just under it and lit per vertex, so it stays
    clean from a quick draft bake (the house's own is on the upstairs lightmap). It
    belongs to the roof's group, so it lifts off with the roof in the Upstairs view, and
    carries its own downlight fittings."""
    from .house import downlight_spots
    y = RY - 0.014
    # (it stops at the cornices' fronts: points buried in them would bake dark and smear)
    front = DEP + 0.03
    k.grain("library_ceiling", Frame((0.0, 0.0, 0.0)), (XW, y - 0.012, Z0 + front), (XE - front, y, ZF), step=0.3,
            skip=("+y", "+x", "-x", "+z", "-z"), along="z")
    s = 0.07
    for px, pz in downlight_spots(ROOM):
        k.b.quad("roof", "light_warm", [(px - s, y - 0.014, pz - s), (px + s, y - 0.014, pz - s),
                                        (px + s, y - 0.014, pz + s), (px - s, y - 0.014, pz + s)])


def shelf_lights():
    """Spots in the ceiling washing the shelves, so the spines read from across the room."""
    y = RY - 0.06
    for z in (1.40, 3.15, 4.90, 6.55):
        pos = (XE - 1.25, y, z)
        LAMPS.append(dict(name=f"shelf_spot_e{z:.0f}", kind="spot", pos=pos, aim=(1.25, -1.55, 0.0), watts=55.0, cone=70.0))
    for x in (3.0, 5.4, 9.95):
        pos = (x, y, Z0 + 1.25)
        LAMPS.append(dict(name=f"shelf_spot_b{x:.0f}", kind="spot", pos=pos, aim=(0.0, -1.55, -1.25), watts=45.0, cone=70.0))


# ---- pictures --------------------------------------------------------------------------------
SPINE_PX = 1800                    # pixels per metre on the spine picture
ATLAS_W = 1024


def paint_spines(books):
    """Every titled spine in one picture, each strip the shape of its spine at SPINE_PX:
    the title reading top to bottom near the head, the author near the foot, set in the
    book's own style and shrunk to fit. Returns each spine's (u0, v0, u1, v1)."""
    from .labels import text_mask
    rng = np.random.default_rng(9)
    sizes = [(max(8, int(round(bk["t"] * SPINE_PX))), int(round(bk["h"] * SPINE_PX))) for bk in books]
    # pack the strips in rows, tallest first
    order = sorted(range(len(books)), key=lambda i: -sizes[i][1])
    pos, x, y, row_h = {}, 0, 0, 0
    for i in order:
        w, h = sizes[i]
        if x + w > ATLAS_W:
            x, y, row_h = 0, y + row_h + 2, 0
        pos[i] = (x, y)
        x += w + 2
        row_h = max(row_h, h)
    H = int(math.ceil((y + row_h) / 4) * 4)
    img = np.zeros((H, ATLAS_W, 3))

    # The text is set lying down, one band per spine, then each band is turned upright.
    Lmax = max(h for _, h in sizes)
    band_y, bands_h = [], 0
    for w, _ in sizes:
        band_y.append(bands_h)
        bands_h += w + 4

    def layout(scale_t, scale_a, which):
        lines = {}
        for i, bk in enumerate(books):
            w, L = sizes[i]
            font = bk["font"]
            if which == "title":
                title = bk["title"].upper() if font is None else bk["title"]
                parts = scale_t[i][1]
                em = (0.50 if len(parts) == 1 else 0.36) * w * scale_t[i][0] * bk["size"]
                gap = 0.10 * w
                cap = 0.70 * em
                total = len(parts) * cap + (len(parts) - 1) * gap
                for n, text in enumerate(parts):
                    base = band_y[i] + (w - total) / 2 + (len(parts) - 1 - n) * (cap + gap)
                    lines.setdefault(font, []).append((text, 0.07 * L / Lmax, base / bands_h, em / bands_h, "LEFT", 1.04))
            elif bk["author"]:
                em = 0.34 * w * scale_a[i]
                base = band_y[i] + (w - 0.70 * em) / 2
                text = bk["author"].upper() if font is None else bk["author"]
                lines.setdefault(font, []).append((text, 0.94 * L / Lmax, base / bands_h, em / bands_h, "RIGHT", 1.04))
        return lines

    def render(lines):
        mask = np.zeros((bands_h, Lmax))
        for font, ls in lines.items():
            mask = np.maximum(mask, text_mask((Lmax, bands_h), ls, font))
        return mask

    def extent(mask, i):
        w, L = sizes[i]
        band = mask[band_y[i]:band_y[i] + w, :L]
        cols = np.nonzero(band.max(axis=0) > 0.3)[0]
        return (cols[0], cols[-1] + 1) if len(cols) else (0, 0)

    trial = 0.5
    one = [(trial, [bk["title"].upper() if bk["font"] is None else bk["title"]]) for bk in books]
    t_mask = render(layout(one, [trial] * len(books), "title"))
    a_mask = render(layout(one, [trial] * len(books), "author"))
    scale_t, scale_a = [], []
    for i, bk in enumerate(books):
        w, L = sizes[i]
        tw = (extent(t_mask, i)[1] - extent(t_mask, i)[0]) / trial / bk["size"]
        aw = (extent(a_mask, i)[1] - extent(a_mask, i)[0]) / trial
        a = min(1.0, 0.36 * L / aw) if aw else 1.0
        room = 0.87 * L - a * aw - (0.05 * L if aw else 0.0)
        s = min(1.0, room / tw) if tw else 1.0
        text = one[i][1][0]
        parts = [text]
        if s < 0.62 and " " in text and w >= 44:
            # a long title on a thick enough spine goes on two lines
            words = text.split(" ")
            best = min(range(1, len(words)), key=lambda c: abs(len(" ".join(words[:c])) - len(" ".join(words[c:]))))
            parts = [" ".join(words[:best]), " ".join(words[best:])]
            longest = max(len(p_) for p_ in parts) / len(text)
            s = min(1.0, room / (tw * longest * 0.36 / 0.50))
        scale_t.append((s, parts))
        scale_a.append(a)
    t_mask = render(layout(scale_t, scale_a, "title"))
    a_mask = render(layout(scale_t, scale_a, "author"))
    mask = np.maximum(t_mask, a_mask)

    cells = []
    for i, bk in enumerate(books):
        w, L = sizes[i]
        band = mask[band_y[i]:band_y[i] + w, :L]
        strip_mask = band.T[::-1, :]                                       # turned upright, reading downward
        ground = np.array(bk["ground"]) * (1 + 0.04 * rng.standard_normal((L, w)))[..., None]
        ground = ground * (1 - 0.10 * np.exp(-np.minimum(np.arange(w), w - 1 - np.arange(w)) / 2.0))[None, :, None]  # rounded spine edges
        strip = ground
        if bk["rules"]:
            ink = np.array(bk["ink"])
            for yy in (0.035, 0.05, 0.95, 0.965):
                r = int(L * yy)
                strip[r:r + 2, 2:w - 2] = ink * 0.9
        strip = strip * (1 - strip_mask[..., None]) + np.array(bk["ink"]) * strip_mask[..., None]
        x0, y0 = pos[i]
        img[y0:y0 + L, x0:x0 + w] = strip
        cells.append(((x0 + 0.5) / ATLAS_W, (y0 + 0.5) / H, (x0 + w - 0.5) / ATLAS_W, (y0 + L - 0.5) / H))
    save_png(picture_path("library_spines"), np.clip(img, 0, 1).astype(np.float32))
    print(f"[library] {len(books)} titled spines in a {ATLAS_W} x {H} picture")
    return cells


def paint_pictures():
    paint_manuscript()
    paint_laptop()


def _typed_lines(img, x0, x1, y_top, n, rng, line_h, ink, gap=1.9, indent_every=7, last_short=True):
    """Rows of grey bars standing in for typed text (no real words), top down."""
    h, w = img.shape[:2]
    y = y_top
    for i in range(n):
        start = x0 + (0.05 * (x1 - x0) if i % indent_every == 0 else 0.0)
        end = x1 - (rng.uniform(0.0, 0.08) * (x1 - x0))
        if last_short and i % indent_every == indent_every - 1:
            end = start + rng.uniform(0.3, 0.7) * (x1 - start)
        cx = start
        while cx < end:
            wl = rng.uniform(0.02, 0.07) * (x1 - x0)
            a, b = int(cx), int(min(end, cx + wl))
            r0, r1 = int(y - line_h), int(y)
            if 0 <= r0 < h and b > a:
                img[max(0, r0):r1, a:b] = img[max(0, r0):r1, a:b] * 0.25 + np.array(ink) * 0.75
            cx += wl + 0.012 * (x1 - x0)
        y -= line_h * gap
        if y < line_h * 3:
            break


def paint_manuscript(w=432, h=560):
    """The manuscript's top page: typed lines (shapes, not words), a chapter heading's
    worth of space, a page number, and a few edits in red pen."""
    from .labels import _paper
    rng = np.random.default_rng(14)
    img = _paper((h, w), np.array([0.94, 0.93, 0.89]), rng)
    _typed_lines(img, 0.12 * w, 0.88 * w, h * 0.70, 40, rng, h * 0.0115, (0.14, 0.14, 0.15), gap=2.0)
    # a heading block and a page number
    img[int(h * 0.80):int(h * 0.81), int(w * 0.40):int(w * 0.60)] = 0.25
    img[int(h * 0.045):int(h * 0.055), int(w * 0.49):int(w * 0.51)] = 0.25
    # red pen: a few strokes and a circled word
    red = np.array([0.72, 0.10, 0.08])
    for _ in range(5):
        y = int(h * rng.uniform(0.2, 0.68))
        x0, x1 = int(w * rng.uniform(0.15, 0.55)), 0
        x1 = x0 + int(w * rng.uniform(0.10, 0.25))
        img[y:y + 2, x0:x1] = red
    yy, xx = np.mgrid[0:h, 0:w]
    ring = np.abs(np.hypot((xx - w * 0.62) / 1.8, yy - h * 0.46) - h * 0.018) < 1.0
    img[ring] = red
    save_png(picture_path("manuscript"), np.clip(img, 0, 1).astype(np.float32))


def paint_laptop(w=512, h=320):
    """The laptop's screen: a writing app in dark mode, the page's lines as shapes."""
    rng = np.random.default_rng(15)
    img = np.ones((h, w, 3)) * np.array([0.11, 0.11, 0.12])
    img[int(h * 0.92):, :] = np.array([0.16, 0.16, 0.17])                   # the app's top bar
    _typed_lines(img, 0.22 * w, 0.78 * w, h * 0.80, 18, rng, h * 0.016, (0.72, 0.72, 0.70), gap=2.3)
    img[int(h * 0.30):int(h * 0.30) + 10, int(w * 0.50):int(w * 0.503)] = 0.85     # the cursor
    save_png(picture_path("laptop_screen"), np.clip(img, 0, 1).astype(np.float32))
