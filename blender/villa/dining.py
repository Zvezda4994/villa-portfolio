"""The dining room, fully furnished. It sets the level of detail for the other rooms.

Plan, looking down (the pool glass at the bottom, the foyer wall at the top):

        foyer wall:  [ painting ]          doorway
                     [ sideboard ]
    kitchen   +-------------------------+
    doorway   |  c    c    c    c(you)  |
              |  ====== table ==== [#]  |   rug under it all       living room
              |  c    c    c    c(away) |                          (open plan)
              +-------------------------+
       fig                                  philodendron
        ----------- glass onto the pool deck -----------

A walnut table for eight on two dark stone legs, leather chairs, a pair of low
bronze pendants, a long walnut sideboard with a few objects on it, a big wool
rug, a painting on the solid wall, and two large plants by the glass. A game is
in progress at the end of the table nearest the living room; the chair across
from the visitor's seat is pushed back, as if the opponent has just stood up.

How it is lit, like the house: the table, rug, painting, board and planters are
big flat surfaces and get the room's own lightmap ("din"); the chairs, lamps
and the ready-made models are curved and get their light baked per vertex.
Everything here is exported to its own file and loaded after the first view.
"""
import math
import random

import numpy as np

from . import config as C
from .house import H1, P
from .props import load, place
from .textures import load_pixels, picture_path, prepared, save_png

ROOM, G, ATLAS = "dining", "ground", "din"
WALL_Z = -P / 2                 # the dining side of the wall to the foyer
KITCHEN_X = -5 + P / 2          # the dining side of the kitchen wall
AXIS_X = -2.3                   # the table, sideboard and painting line up on this

# The table: walnut top on two dark stone legs, seats four a side.
TABLE_X = (AXIS_X - 1.5, AXIS_X + 1.5)
TABLE_Z = (-4.825, -3.775)
TABLE_TOP = 0.76
TABLE_THICK = 0.05
SEATS_X = [AXIS_X - 1.05, AXIS_X - 0.35, AXIS_X + 0.35, AXIS_X + 1.05]

RUG_X = (AXIS_X - 2.3, AXIS_X + 2.3)
RUG_Z = (-6.0, -2.6)
RUG_T = 0.012

# The game: on the table in front of the last seat on the foyer side.
SQUARE = 0.058                  # the chess set's own square size
BORDER = 0.04
BOARD_T = 0.022
BOARD = (SEATS_X[-1], (TABLE_Z[0] + TABLE_Z[1]) / 2)

PENDANT_X = [AXIS_X - 0.75, AXIS_X + 0.75]
PENDANT_LOW = 1.58              # bottom of the shades, about 80 cm over the table
PAINTING = dict(w=2.0, h=1.25, bottom=1.12)
SIDEBOARD_TOP = 0.68

# How bright the room's general ceiling light is compared with an empty room's.
CEILING_LIGHT = 0.4

# Lamps for the bake (lighting.py adds them): one inside each pendant shining
# down, and a soft wash over the painting.
LAMPS = [dict(name=f"pendant_{i}", pos=(x, PENDANT_LOW + 0.015, BOARD[1]), size=(0.42, 0.42), watts=16.0,
              aim=(0.0, -1.0, 0.0)) for i, x in enumerate(PENDANT_X)]
LAMPS.append(dict(name="painting_wash", pos=(AXIS_X, H1 - 0.2, WALL_Z - 0.7), size=(1.9, 0.15), watts=30.0,
                  aim=(0.0, -0.72, 0.69)))

# The visitor's seat and the view over the board (the room's camera on the website).
CHESS_CAM = dict(pos=(BOARD[0] + 0.02, 1.30, -3.52), target=(BOARD[0], 0.77, BOARD[1] - 0.05), fov=46.0)
ROOM_CAM = dict(pos=(3.4, 1.62, -5.6), target=(-2.6, 0.95, -2.6), fov=52.0)


def build_dining(b):
    paint_pictures()
    with b.room(ROOM):
        rug(b)
        table(b)
        chairs(b)
        pendants(b)
        painting(b)
        sideboard(b)
        chess(b)
        plants(b)


# ---- big flat pieces (lightmapped) -------------------------------------------
def rug(b):
    full = [(0, 0), (1, 0), (1, 1), (0, 1)]
    b.box(G, "rug", RUG_X, (0.0, RUG_T), RUG_Z, atlas=ATLAS, skip=("-y",), solid=False,
          over={"+y": dict(uv=full, density=0.8)})


def table(b):
    y0, y1 = TABLE_TOP - TABLE_THICK, TABLE_TOP
    b.box(G, "walnut", TABLE_X, (y0, y1), TABLE_Z, atlas=ATLAS, solid=False,
          over={"+y": dict(density=1.6), "-y": dict(density=0.35)})
    for cx in (TABLE_X[0] + 0.4, TABLE_X[1] - 0.4):
        b.box(G, "dark_stone", (cx - 0.04, cx + 0.04), (RUG_T, y0), (TABLE_Z[0] + 0.22, TABLE_Z[1] - 0.22),
              atlas=ATLAS, skip=("-y", "+y"), solid=False)


def painting(b):
    """A gallery-wrapped canvas hung a few millimetres off the wall."""
    w, h, y0 = PAINTING["w"], PAINTING["h"], PAINTING["bottom"]
    z1 = WALL_Z - 0.006
    face = [(0, 0), (1, 0), (1, 1), (0, 1)]          # seen from the room, +x is on the left
    b.box(G, "painting", (AXIS_X - w / 2, AXIS_X + w / 2), (y0, y0 + h), (z1 - 0.04, z1), atlas=ATLAS,
          skip=("+z",), solid=False, over={"-z": dict(uv=face, density=0.9)})


# ---- the chess game ------------------------------------------------------------
PIECE_OBJECTS = {
    "p": "piece_pawn_{}_01", "n": "piece_knight_{}_01", "b": "piece_bishop_{}_01",
    "r": "piece_rook_{}_01", "q": "piece_queen_{}", "k": "piece_king_{}",
}


def parse_fen(fen):
    """{(file 0-7, rank 0-7): letter} from the placement part of a FEN string."""
    out = {}
    for row, text in enumerate(fen.split()[0].split("/")):
        rank, f = 7 - row, 0
        for ch in text:
            if ch.isdigit():
                f += int(ch)
            else:
                out[(f, rank)] = ch
                f += 1
    return out


def chess(b):
    bx, bz = BOARD
    half = 4 * SQUARE + BORDER
    top = TABLE_TOP + BOARD_T
    # The board: one picture over the whole top, so its shadows bake as one piece.
    # u runs toward +x (the a-file is on White's left), v from White's edge (+z) toward Black.
    b.box(G, "dark_stone", (bx - half, bx + half), (TABLE_TOP, top), (bz - half, bz + half), atlas=ATLAS,
          skip=("-y",), solid=False, over={"+y": dict(mat="chessboard", uv=[(0, 0), (1, 0), (1, 1), (0, 1)], density=3.5)})

    wanted = {name.format(colour) for name in PIECE_OBJECTS.values() for colour in ("white", "black")}
    thin = {n: (0.45 if "pawn" in n else 0.35) for n in wanted}
    pieces = load("chess_set", only=wanted, thin=thin)
    rng = random.Random(21)

    def put(letter, x, z, yaw, y=top):
        colour = "white" if letter.isupper() else "black"
        piece = pieces[PIECE_OBJECTS[letter.lower()].format(colour)]
        place(b, G, f"chess_{colour}", piece, (x, y, z), yaw=yaw)

    for (f, r), letter in parse_fen(C.CHESS_FEN).items():
        x = bx + (f - 3.5) * SQUARE + rng.uniform(-0.0025, 0.0025)
        z = bz + (3.5 - r) * SQUARE + rng.uniform(-0.0025, 0.0025)
        # The set is modelled with White at -z; here White sits at +z, so every
        # piece turns half round, plus the small twist real pieces always have.
        twist = rng.uniform(-0.18, 0.18) if letter.lower() == "n" else rng.uniform(-0.6, 0.6)
        put(letter, x, z, math.pi + twist)
    # Taken pieces stand on the table beside the board, on the side of whoever took them
    # (White's right is +x; Black's right is -x).
    for i, letter in enumerate(C.CHESS_CAPTURED):
        side = 1 if letter.islower() else -1
        x = bx + side * (half + 0.05 + 0.04 * (i // 2))
        z = bz + side * (half - 0.06)
        put(letter, x, z, rng.uniform(0, 2 * math.pi), y=TABLE_TOP)


# ---- curved pieces (lit per vertex) -----------------------------------------------
def _rounded_box(centre, size, r, n=3):
    """A box with rounded edges and corners, as quads. Shared points are merged."""
    cx, cy, cz = centre
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    ix, iy, iz = max(hx - r, 0), max(hy - r, 0), max(hz - r, 0)
    index, verts, faces = {}, [], []

    def vert(p):
        # push a point on the plain box out to the rounded surface
        q = (max(-ix, min(ix, p[0])), max(-iy, min(iy, p[1])), max(-iz, min(iz, p[2])))
        d = (p[0] - q[0], p[1] - q[1], p[2] - q[2])
        m = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
        out = (cx + q[0] + d[0] / m * r, cy + q[1] + d[1] / m * r, cz + q[2] + d[2] / m * r)
        key = tuple(round(v, 6) for v in out)
        if key not in index:
            index[key] = len(verts)
            verts.append(out)
        return index[key]

    # Each face is split so its flat middle and its rounded strips get their own rows.
    def steps(h, i):
        inner = [-i, i] if i > 1e-6 else [0.0]
        ramp = [-(i + (h - i) * k / n) for k in range(n, 0, -1)]
        return ramp + inner + [-v for v in reversed(ramp)]

    sx, sy, sz = steps(hx, ix), steps(hy, iy), steps(hz, iz)
    for axis, sign in ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)):
        a, c = [k for k in range(3) if k != axis]
        ua = (sx, sy, sz)[a]
        uc = (sx, sy, sz)[c]
        h = (hx, hy, hz)[axis] * sign
        grid = []
        for va in ua:
            row = []
            for vc in uc:
                p = [0.0, 0.0, 0.0]
                p[axis], p[a], p[c] = h, va, vc
                row.append(vert(p))
            grid.append(row)
        for i in range(len(ua) - 1):
            for j in range(len(uc) - 1):
                faces.append((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    return verts, _outward(verts, faces, centre)


def _outward(verts, faces, centre):
    """Flip any face whose normal points back toward the centre."""
    out = []
    for f in faces:
        p = [verts[i] for i in f]
        n = _normal(p)
        m = [sum(v[k] for v in p) / len(p) - centre[k] for k in range(3)]
        out.append(f if n[0] * m[0] + n[1] * m[1] + n[2] * m[2] >= 0 else tuple(reversed(f)))
    return out


def _normal(p):
    a = [p[1][k] - p[0][k] for k in range(3)]
    c = [p[-1][k] - p[0][k] for k in range(3)]
    return (a[1] * c[2] - a[2] * c[1], a[2] * c[0] - a[0] * c[2], a[0] * c[1] - a[1] * c[0])


def _prism(bottom, top, half_bottom, half_top):
    """A tapered square leg from `bottom` (x, y, z) to `top`."""
    verts = []
    for (x, y, z), (hx, hz) in ((bottom, half_bottom), (top, half_top)):
        verts += [(x - hx, y, z - hz), (x + hx, y, z - hz), (x + hx, y, z + hz), (x - hx, y, z + hz)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    centre = tuple((bottom[k] + top[k]) / 2 for k in range(3))
    return verts, _outward(verts, faces, centre)


def _lathe(profile, segments=36):
    """Spin a list of (radius, height) points round the vertical axis."""
    verts, faces = [], []
    for r, y in profile:
        for s in range(segments):
            a = 2 * math.pi * s / segments
            verts.append((r * math.cos(a), y, r * math.sin(a)))
    for i in range(len(profile) - 1):
        for s in range(segments):
            a, c = i * segments + s, i * segments + (s + 1) % segments
            faces.append((a, c, c + segments, a + segments))
    return verts, faces


def _move(verts, pos, yaw=0.0, tilt=0.0, pivot=(0.0, 0.0, 0.0)):
    """Lean (toward +z, about `pivot`), turn about the vertical, then move to `pos`."""
    c, s = math.cos(yaw), math.sin(yaw)
    ct, st = math.cos(tilt), math.sin(tilt)
    out = []
    for x, y, z in verts:
        y, z = y - pivot[1], z - pivot[2]
        y, z = y * ct - z * st, y * st + z * ct
        y, z = y + pivot[1], z + pivot[2]
        out.append((pos[0] + x * c + z * s, pos[1] + y, pos[2] - x * s + z * c))
    return out


def _add(b, mat, shape, pos, yaw=0.0, tilt=0.0, pivot=(0.0, 0.0, 0.0)):
    verts, faces = shape
    b.mesh(G, mat, _move(verts, pos, yaw, tilt, pivot), faces)


def chair(b, pos, yaw):
    """An upholstered dining chair: leather seat and back on a slim walnut frame.
    Built facing +z (the way the sitter looks) with its front edge at `pos`."""
    seat_y = 0.465
    _add(b, "leather", _rounded_box((0, seat_y - 0.045, -0.235), (0.48, 0.09, 0.47), 0.035), pos, yaw)
    _add(b, "walnut_dark", _rounded_box((0, seat_y - 0.105, -0.235), (0.45, 0.035, 0.43), 0.012, n=1), pos, yaw)
    # legs, splayed a little
    for sx in (-1, 1):
        for front in (True, False):
            z_top = -0.04 if front else -0.43
            z_bot = 0.0 if front else -0.47
            _add(b, "walnut_dark", _prism((sx * 0.215, 0.0, z_bot), (sx * 0.2, seat_y - 0.12, z_top),
                                          (0.012, 0.012), (0.018, 0.018)), pos, yaw)
    # the back: a curved-looking padded panel on two posts, leaning back 10 degrees
    lean = -math.radians(10)
    pivot = (0.0, seat_y, -0.45)
    _add(b, "leather", _rounded_box((0, seat_y + 0.27, -0.465), (0.46, 0.36, 0.065), 0.03), pos, yaw, lean, pivot)
    for sx in (-1, 1):
        _add(b, "walnut_dark", _prism((sx * 0.19, seat_y - 0.12, -0.465), (sx * 0.19, seat_y + 0.14, -0.465),
                                      (0.014, 0.014), (0.012, 0.012)), pos, yaw, lean, pivot)


def chairs(b):
    y = RUG_T
    near, far = TABLE_Z[1] + 0.05, TABLE_Z[0] - 0.05       # where the seat fronts sit, each side
    rng = random.Random(4)
    for i, x in enumerate(SEATS_X):
        # foyer side, facing the glass (and the pool); the last one is the visitor's
        out = 0.18 if i == 3 else rng.uniform(0.0, 0.03)
        chair(b, (x + rng.uniform(-0.01, 0.01), y, near + out), math.pi + rng.uniform(-0.02, 0.02))
        # glass side; across the board the chair is pushed back and turned, the player away
        if i == 3:
            chair(b, (x + 0.06, y, far - 0.32), math.radians(14))
        else:
            chair(b, (x + rng.uniform(-0.01, 0.01), y, far - rng.uniform(0.0, 0.03)), rng.uniform(-0.02, 0.02))


def pendants(b):
    """Two wide, shallow bronze shades hanging low over the table, each glowing
    through a warm diffuser underneath."""
    outer = [(0.03, 0.17), (0.09, 0.163), (0.17, 0.125), (0.235, 0.075), (0.272, 0.03), (0.285, 0.0)]
    inner = [(0.278, 0.004), (0.265, 0.032), (0.228, 0.074), (0.165, 0.118), (0.088, 0.152), (0.03, 0.158)]
    shade = _lathe(outer + inner, 48)
    z = BOARD[1]
    for x in PENDANT_X:
        base = (x, PENDANT_LOW, z)
        _add(b, "bronze", shade, base)
        # the glowing diffuser, a flat disc just inside the rim, facing down
        n = 48
        ring = [(0.262 * math.cos(2 * math.pi * k / n), 0.012, 0.262 * math.sin(2 * math.pi * k / n)) for k in range(n)]
        verts = _move([(0.0, 0.012, 0.0)] + ring, base)
        b.mesh(G, "light_warm", verts, [(0, k + 1, (k + 1) % n + 1) for k in range(n)], smooth=False)
        # the rod and the ceiling canopy (profiles run downward so the faces point outward)
        rod = _lathe([(0.006, H1 - PENDANT_LOW - 0.02), (0.006, 0.17)], 10)
        _add(b, "bronze", rod, base)
        canopy = _lathe([(0.072, 0.0), (0.072, -0.004), (0.07, -0.028), (0.012, -0.03)], 32)
        _add(b, "bronze", canopy, (x, H1, z))


def sideboard(b):
    """A long walnut cabinet against the foyer wall, with a bronze horse's head
    (a knight, given what is on the table) and two white vases on top."""
    parts = load("modern_wooden_cabinet", thin={"modern_wooden_cabinet_body": 0.5})
    cz = WALL_Z - 0.01 - 0.27                       # back of the cabinet 1 cm off the wall
    for piece in parts.values():
        place(b, G, "cabinet", piece, (AXIS_X, 0.0, cz), yaw=math.pi, origin=(0.0, 0.0, 0.0))
    top = SIDEBOARD_TOP
    horse = load("horse_head", thin={"horse_head": 0.5})["horse_head"]
    place(b, G, "horse_head", horse, (AXIS_X - 0.62, top, cz + 0.02), yaw=math.pi - 0.5)
    tall = load("ceramic_vase_03", thin={"ceramic_vase_03": 0.3})["ceramic_vase_03"]
    round_ = load("ceramic_vase_02", thin={"ceramic_vase_02": 0.3})["ceramic_vase_02"]
    place(b, G, "vase_tall", tall, (AXIS_X + 0.55, top, cz - 0.02))
    place(b, G, "vase_round", round_, (AXIS_X + 0.78, top, cz + 0.05), yaw=0.8)


def plants(b):
    """A fig tree and a big philodendron in dark stone planters by the glass."""
    spots = [("fig", -4.42, -7.15, 0.56, 0.62), ("philo", 0.64, -7.15, 0.72, 0.42)]
    for kind, x, z, w, h in spots:
        planter(b, x, z, w, h)
        soil = h - 0.04
        if kind == "fig":
            fig = load("potted_plant_01", only={"potted_plant_01_leaves", "potted_plant_01_stem"},
                       thin={"potted_plant_01_leaves": 0.25})
            k = 1.7
            for name, piece in fig.items():
                mat = "fig_leaves" if name.endswith("leaves") else "fig_stems"
                place(b, G, mat, piece, (x, soil, z), yaw=2.4, scale=k, origin=(0.0, 0.5, 0.0))
        else:
            philo = load("potted_plant_02", only={"potted_plant_02_leaves"})
            place(b, G, "philo_leaves", philo["potted_plant_02_leaves"], (x, soil, z), yaw=-0.7, scale=1.65,
                  origin=(0.0, 0.3, 0.0))


def planter(b, x, z, w, h):
    t = 0.035
    x0, x1, z0, z1 = x - w / 2, x + w / 2, z - w / 2, z + w / 2
    for xs, zs in (((x0, x1), (z0, z0 + t)), ((x0, x1), (z1 - t, z1)), ((x0, x0 + t), (z0 + t, z1 - t)),
                   ((x1 - t, x1), (z0 + t, z1 - t))):
        b.box(G, "dark_stone", xs, (0.0, h), zs, atlas=ATLAS, skip=("-y",), solid=False)
    b.floor(G, "mulch", ATLAS, (x0 + t, x1 - t), (z0 + t, z1 - t), h - 0.04)


# ---- pictures the build paints itself ------------------------------------------------
def _noise(shape, scale_y, scale_x, rng):
    """Smooth random field (mean 0, roughly -1..1) with features of about
    scale_y by scale_x pixels. Made in frequency space, so it tiles."""
    h, w = shape
    f = np.fft.fft2(rng.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * scale_y
    fx = np.fft.fftfreq(w)[None, :] * scale_x
    out = np.fft.ifft2(f * np.exp(-(fy ** 2 + fx ** 2) * 8)).real
    return out / (np.abs(out).max() + 1e-9)


def paint_pictures():
    paint_rug()
    paint_painting()
    paint_chessboard()


def paint_rug(w=512, h=384):
    """Undyed wool, oatmeal, with a darker band set in from the edge."""
    rng = np.random.default_rng(3)
    base = np.array([0.70, 0.63, 0.53])
    tone = 1.0 + 0.035 * _noise((h, w), 40, 40, rng) + 0.05 * rng.standard_normal((h, w)) * 0.5
    tone += 0.02 * _noise((h, w), 1, 3, rng)
    img = tone[..., None] * base
    px_per_m = w / (RUG_X[1] - RUG_X[0])
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / px_per_m   # metres from the edge
    band = (edge > 0.16) & (edge < 0.215)
    img[band] = img[band] * (np.array([0.42, 0.35, 0.29]) / base)
    img[edge < 0.025] *= 0.82                                                        # the bound edge
    save_png(picture_path("rug"), np.clip(img, 0, 1).astype(np.float32))


def paint_painting(w=768, h=480):
    """An original abstract: the desert at dusk as soft bands of colour, indigo
    sky over a rust glow, a thin gold horizon and ochre dunes, with visible brushwork."""
    rng = np.random.default_rng(17)
    x = np.linspace(0, 1, w)[None, :]
    y = np.linspace(0, 1, h)[:, None]                      # 0 at the bottom of the canvas
    # (colour, where this band's lower edge sits, how much it wanders, how soft it is)
    bands = [
        ((0.20, 0.11, 0.07), 0.00, 0.00, 0.02),            # umber ground
        ((0.62, 0.40, 0.20), 0.16, 0.035, 0.03),           # ochre dunes
        ((0.74, 0.50, 0.26), 0.37, 0.025, 0.02),           # lit crest
        ((0.88, 0.66, 0.33), 0.465, 0.006, 0.004),         # the gold horizon line
        ((0.58, 0.24, 0.12), 0.478, 0.01, 0.01),           # rust glow
        ((0.30, 0.17, 0.20), 0.63, 0.03, 0.05),            # dusk
        ((0.11, 0.12, 0.21), 0.78, 0.03, 0.07),            # indigo sky
    ]
    img = np.zeros((h, w, 3))
    for colour, at, wander, soft in bands:
        edge = at + wander * _noise((1, w), 1, 3.5, rng)[0][None, :] if wander else np.full((1, w), at)
        k = np.clip((y - edge) / max(soft, 1e-3) + 0.5, 0, 1)
        k = k * k * (3 - 2 * k)
        img = img * (1 - k[..., None]) + np.array(colour) * k[..., None]
    strokes = 0.06 * _noise((h, w), 1.5, 30, rng) + 0.03 * _noise((h, w), 3, 80, rng)
    img *= (1 + strokes)[..., None]
    weave = 0.015 * (np.sin(np.arange(w) * 2.1)[None, :] + np.sin(np.arange(h) * 2.3)[:, None])
    img *= (1 + weave)[..., None]
    save_png(picture_path("painting"), np.clip(img, 0, 1).astype(np.float32))


def paint_chessboard(size=1024):
    """Cream marble and dark granite squares in a granite border, with a thin
    brass line round the playing area. Rows start at White's edge, columns at the a-file."""
    rng = np.random.default_rng(9)
    marble = load_pixels(prepared("marble_01"))[..., :3]
    granite = load_pixels(prepared("granite_tile"))[..., :3]
    total = 8 * SQUARE + 2 * BORDER
    px = size / total
    img = np.zeros((size, size, 3))

    def fill(y0, y1, x0, x1, src, tint):
        hh, ww = y1 - y0, x1 - x0
        sy, sx = rng.integers(0, src.shape[0] - hh + 1), rng.integers(0, src.shape[1] - ww + 1)
        patch = src[sy:sy + hh, sx:sx + ww]
        if rng.random() < 0.5:
            patch = patch[::-1, ::-1]
        img[y0:y1, x0:x1] = patch * tint

    fill(0, size, 0, size, np.tile(granite, (2, 2, 1)), np.array([0.55, 0.53, 0.52]))
    edges = [round((BORDER + k * SQUARE) * px) for k in range(9)]
    for r in range(8):
        for f in range(8):
            light = (f + r) % 2 == 1
            src = marble if light else granite
            tint = np.array([1.02, 0.98, 0.90]) if light else np.array([0.42, 0.40, 0.40])
            fill(edges[r], edges[r + 1], edges[f], edges[f + 1], src, tint)
    a, c = edges[0], edges[8]
    brass = np.array([0.78, 0.60, 0.32])
    for t in range(-4, -1):
        img[a + t, a + t:c - t] = brass
        img[c - 1 - t, a + t:c - t] = brass
        img[a + t:c - t, a + t] = brass
        img[a + t:c - t, c - 1 - t] = brass
    save_png(picture_path("chessboard"), np.clip(img, 0, 1).astype(np.float32))
