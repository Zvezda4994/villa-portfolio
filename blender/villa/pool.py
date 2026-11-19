"""The pool deck, furnished, and the "Get in touch" moment.

Plan, looking down (the house along the top, the pool in the middle):

        house  ------------------------------------------------  (z = -8)
        tree                                                 palm
                 dining glass        living glass      terrace above
           . . . . . . . . . walkway . . . . . . . . . . . . . .
                     +------------------ pool ------------------+
                     |                                          |
                     |                                          |
                     +------------------------------------------+
                       vis [t] mine     (both turned in toward the table)
                        (parasol)
        palm  tree           tree       [ sofas + fire pit ] tree    palm

(This plan is mirrored: standing on the deck facing the house, +x is on your left.)

Two long teak loungers stand side by side at the pool's south-west corner, a step
back from the water and facing it, each turned 12° in toward the other, with a
low travertine table between them and a cream cantilever parasol behind them.
That corner still has the low sun from the north-west; further east the house's
shadow covers the deck. The visitor's lounger has a folded towel at its foot.
Mine is set as if I'd just got up: a towel left spread over it, my sunglasses, an
isshobin of sake and a cup on the table, my contact card there turned toward the
visitor, my loafers on the deck between the two. On the south side, in the
house's evening shade, low sofas sit round a fire pit. Quiver trees and palms in
big stone planters stand at the corners, lanterns and small uplights glow, and the
pool keeps its own lights.

The camera moment: opening the room drops the camera onto the visitor's lounger
at eye level, looking out over the pool with my lounger and the table on the
left, and the visitor's own hand holding a martini at the bottom of the frame.
That hand moves with the camera on the website (it is exported tagged
attach=camera).

Big flat things (teak frames, the table, planters, rug, fire pit, the card) use
the room's own lightmap ("pol"); cushions, towels, plants and the small props are
lit per vertex. Everything here is exported to rooms/pool.glb.

The visitor's hand and the loafers were made with the scripted character code,
which is set aside for now; they are kept here as plain meshes in `frozen/`
(see PROGRESS.md, "Frozen meshes").
"""
import math
import random
from pathlib import Path

import numpy as np

from .dining import _lathe, _rounded_box

ROOM, G, ATLAS = "pool", "out", "pol"
FROZEN = Path(__file__).resolve().parent / "frozen"


def rot(x=0.0, y=0.0, z=0.0):
    """Rotation matrix, angles in degrees: first about z (roll), then x (pitch),
    then y (turn). Pitch about x tips +y toward +z; a turn about y swings +z toward +x."""
    x, y, z = math.radians(x), math.radians(y), math.radians(z)
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return ry @ rx @ rz


def axes(forward, up):
    """Rotation whose z axis points along `forward` and y axis as close to `up` as it can."""
    f = np.array(forward, float)
    f /= np.linalg.norm(f)
    x = np.cross(np.asarray(up, float), f)
    x /= np.linalg.norm(x)
    return np.stack([x, np.cross(f, x), f], axis=1)


# ---- layout ---------------------------------------------------------------------------
# The lounger pair is laid out in its own frame: X across (the visitor's lounger on
# -X, mine on +X), Z toward the water, both head ends on Z = 0. The frame sits square
# to the pool. Its front corners stop about 0.75 m short of the water.
PAIR_CENTRE = np.array([-0.30, 0.0, -18.40])
PAIR_YAW = 0.0
TOE_IN = 12.0                    # each lounger turned this far in toward the other
LOUNGER = dict(length=2.02, width=0.76, frame_top=0.29, seat=0.395, hinge=0.80, back=40.0)
# (head end in the pair frame, which way the lounger faces: 0 = straight at the water)
VISITOR_LOUNGER = dict(head=(-1.0, 0.0), turn=TOE_IN)
MY_LOUNGER = dict(head=(1.0, 0.0), turn=-TOE_IN)
TABLE = dict(at=(0.0, 1.05), half=0.21, top=0.40)     # between the two, beside the sitters' hips
# my loafers, slipped off beside the head of my lounger, between it and the table:
# (heel in the pair frame, turn, left shoe). Kept out of the camera moment's frame;
# the only spot in it, beside the table, is too tight for a shoe to show whole.
LOAFERS = [((0.22, 0.28), 12.0, False), ((0.37, 0.25), 2.0, True)]

# A cantilever parasol behind the pair: its mast stands behind the head ends and its
# arm holds the canopy over them. At 15° the sun passes under the canopy, so its
# shadow lands about 9 m away to the south-east, off the deck, and the loungers and
# the table stay in the sun. (mast foot and canopy centre in the pair frame, canopy
# side, height of its centre)
PARASOL = dict(mast=(0.0, -2.0), centre=(0.0, -0.35), size=2.7, top=2.55)

FIRE = dict(centre=(6.0, -19.35))
# Quiver trees (Poly Haven's quiver_tree_02, CC0) in the big planters: x, z, turn (degrees), scale
TREES = [(-3.05, -20.55, 35.0, 1.35), (2.45, -20.85, -60.0, 1.2), (9.55, -20.85, 160.0, 1.3),
         (-6.25, -9.05, 75.0, 1.25)]
PALMS = [(-6.15, -20.75, 3.9), (13.25, -15.20, 4.3)]
LANTERNS = [(-6.55, -15.05), (-2.95, -18.75), (2.75, -17.75), (9.25, -17.75), (-0.25, -9.35)]

# Lights for the bake, filled in while building (lighting.py adds them).
LAMPS = []


def pair_point(X, Z, y=0.0):
    """A point in the lounger pair's frame, in world coordinates."""
    return PAIR_CENTRE + rot(y=PAIR_YAW) @ np.array([X, y, Z])


class Frame:
    """A local frame for building one piece of furniture: `pos` is its origin in
    the world, `yaw` turns it about the vertical (degrees, +z toward +x)."""

    def __init__(self, pos, yaw=0.0):
        self.pos = np.asarray(pos, float)
        self.yaw = yaw
        self.R = rot(y=yaw)

    def __call__(self, p):
        return tuple(self.pos + self.R @ np.asarray(p, float))

    def many(self, pts):
        return [self(p) for p in pts]


def lounger_frame(spec):
    head = pair_point(*spec["head"])
    return Frame(head, PAIR_YAW + spec["turn"])


# ---- the camera moment ------------------------------------------------------------------
# The visitor sits on the first lounger, head up off the cushion, looking out over the
# pool and the house, with my lounger and the table in the left third of the frame.
# (The eye can't go further back: the top of the lounger's raised back is just
# behind it.) MOMENT_CAM is worked out from these; rooms.js repeats it for the
# "pool" stop (the tests check the two agree).
MOMENT_EYE = (-0.12, 0.98, 0.32)      # in the visitor's lounger: across, height, from the head end
MOMENT_AIM = (0.65, 0.56, 2.77)       # what it looks at, in the pair frame (X, height, Z): the pool's
                                      # near edge, 35° round from the loungers' facing, 8° down
MOMENT_FOV = 48.0


def _moment_cam():
    eye = np.array(lounger_frame(VISITOR_LOUNGER)(MOMENT_EYE))
    X, y, Z = MOMENT_AIM
    target = pair_point(X, Z, y)
    return dict(pos=tuple(round(float(v), 3) for v in eye), target=tuple(round(float(v), 3) for v in target),
                fov=MOMENT_FOV)


MOMENT_CAM = _moment_cam()


def camera_axes(pos, target):
    """The camera's own axes as columns (right, up, back), the way three.js holds them."""
    pos, target = np.asarray(pos, float), np.asarray(target, float)
    fwd = (target - pos) / np.linalg.norm(target - pos)
    right = np.cross(fwd, (0.0, 1.0, 0.0))
    right /= np.linalg.norm(right)
    return np.stack([right, np.cross(right, fwd), -fwd], axis=1)


# ---- building blocks -----------------------------------------------------------------------
def obox(b, mat, f, lo, hi, tilt=0.0, pivot=(0, 0, 0), skip=(), density=1.0, atlas=ATLAS):
    """A box between local corners lo and hi in frame f, optionally tipped about
    the x axis by `tilt` degrees round `pivot`. Lightmapped like the house's boxes."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    corners = {
        "+x": [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
        "-x": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        "+y": [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
        "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "-z": [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
    }
    T = rot(x=tilt)
    pv = np.asarray(pivot, float)
    for name, pts in corners.items():
        if name in skip:
            continue
        world = [f(pv + T @ (np.asarray(p) - pv)) for p in pts]
        b.quad(G, mat, world, atlas, density)


def soft_box(b, mat, f, centre, size, r, tilt=0.0, pivot=(0, 0, 0), n=3):
    """A cushion: a box with rounded edges, lit per vertex."""
    verts, faces = _rounded_box(centre, size, r, n)
    T = rot(x=tilt)
    pv = np.asarray(pivot, float)
    b.mesh(G, mat, [f(pv + T @ (np.asarray(v) - pv)) for v in verts], faces)


def lathe(b, mat, f, profile, segments=32):
    """Spin a profile round the vertical. Profiles here are written from the bottom
    up; they are spun top-down, which is the way round that makes faces point out
    (and, for a hollow, into the hollow)."""
    verts, faces = _lathe(profile[::-1], segments)
    b.mesh(G, mat, f.many(verts), faces)


def rod(b, mat, p0, p1, thick, n=1):
    """A slim square-section bar with softened edges from p0 to p1 (world points), lit per vertex."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    length = float(np.linalg.norm(d))
    M = axes(d, (0.0, 1.0, 0.0) if abs(d[1]) < 0.9 * length else (1.0, 0.0, 0.0))
    V, F = _rounded_box((0, 0, 0), (thick, thick, length), thick * 0.3, n)
    b.mesh(G, mat, [tuple((p0 + p1) / 2 + M @ np.asarray(v)) for v in V], F)


def mesh_by_material(b, verts, faces, mats, smooth=True):
    """Hand each material its own faces, with only the vertices those faces use."""
    F = np.asarray(faces)
    mats = np.asarray(mats)
    for mat in dict.fromkeys(mats.tolist()):
        sub = F[mats == mat]
        used, inv = np.unique(sub, return_inverse=True)
        b.mesh(G, mat, [tuple(verts[i]) for i in used], [tuple(int(k) for k in row) for row in inv.reshape(sub.shape)],
               smooth=smooth)


# ---- the loungers -----------------------------------------------------------------------------
def lounger(b, f, towel="folded"):
    """A long teak lounger with a raised back, in its own frame: head end at z = 0,
    foot end at z = length, the sitter facing +z. `towel` is "folded" (a neat stack
    at the foot), "draped" (left spread over it) or None."""
    L, W = LOUNGER["length"], LOUNGER["width"] / 2
    top, seat, hinge, back = LOUNGER["frame_top"], LOUNGER["seat"], LOUNGER["hinge"], LOUNGER["back"]
    obox(b, "teak", f, (-W + 0.07, 0.0, 0.12), (W - 0.07, 0.20, L - 0.12), skip=("-y",), density=0.6)    # plinth
    obox(b, "teak", f, (-W, 0.20, 0.0), (W, top, L), skip=("-y",), density=0.8)                       # bed
    soft_box(b, "canvas", f, (0, (top + seat) / 2 + 0.003, (hinge + L) / 2 + 0.005), (2 * W - 0.04, seat - top + 0.006, L - hinge - 0.03), 0.03)
    # the back: a teak board hinged at the seat and propped up, with its cushion
    pivot = (0.0, top, hinge)
    obox(b, "teak", f, (-W + 0.02, top, hinge - 0.84), (W - 0.02, top + 0.03, hinge), tilt=back, pivot=pivot, density=0.7)
    soft_box(b, "canvas", f, (0, top + 0.03 + 0.045, hinge - 0.41), (2 * W - 0.06, 0.09, 0.80), 0.03, tilt=back, pivot=pivot)
    # a prop under the board
    obox(b, "teak", f, (-W + 0.10, top, 0.23), (W - 0.10, top + (hinge - 0.27) * math.tan(math.radians(back)) - 0.01, 0.27), density=0.5)
    if towel == "folded":
        folded_towel(b, f, (0.0, seat, L - 0.24))
    elif towel == "draped":
        draped_towel(b, f)


def folded_towel(b, f, base, yaw=0.0):
    """A thick white towel folded into a neat stack, with a sand stripe."""
    x, y, z = base
    g = Frame(f((x, 0, z)), f.yaw + yaw)
    for i, (w, d) in enumerate(((0.42, 0.30), (0.415, 0.295), (0.41, 0.29))):
        yy = y + 0.011 + i * 0.021
        soft_box(b, "towel", g, (0, yy, 0), (w, 0.021, d), 0.009, n=2)
    soft_box(b, "towel_stripe", g, (0, y + 0.064, 0.08), (0.412, 0.004, 0.045), 0.0015, n=1)


def draped_towel(b, f, shift=-0.025, step=0.024):
    """A beach towel left spread over the lounger by someone who just got up: along
    the seat, up the raised back, over its top and hanging down behind, its sides
    falling over the cushions' edges, loosely creased. In the lounger's frame `f`;
    `shift` slides it across (negative toward the visitor). Navy, so it reads
    against the cream cushions, with a cream band across each end."""
    top, hinge = LOUNGER["frame_top"], LOUNGER["hinge"]
    c, s = math.cos(math.radians(LOUNGER["back"])), math.sin(math.radians(LOUNGER["back"]))
    t = 0.006                                   # thickness
    e = t / 2 + 0.003                           # how far the towel's middle sits off the cushions

    def on_back(a, d):
        """(y, z) of a point on the raised back: `a` off the board's underside, `d` along
        the board from the hinge (negative toward the head end)."""
        return (top + a * c - d * s, hinge + a * s + d * c)

    # The towel's middle line, from its end on the seat to its end hanging behind the
    # back, as (y, z, how much it lies on a cushion: 1 on one, 0 hanging free).
    seat_y = LOUNGER["seat"] + 0.006 + e
    key = [(seat_y, 1.62, 1.0), (seat_y, 1.10, 1.0), (seat_y + 0.003, 0.90, 1.0),
           (*on_back(0.12 + e, -0.07), 1.0), (*on_back(0.12 + e, -0.45), 1.0), (*on_back(0.12 + e, -0.76), 1.0)]
    r = 0.03 + e
    for k in range(1, 5):                       # over the cushion's rounded top corner
        phi = math.radians(22.5 * k)
        key.append((*on_back(0.09 + r * math.cos(phi), -0.78 - r * math.sin(phi)), 1.0 - 0.2 * k))
    key += [(*on_back(0.035 + e, -0.84 - e), 0.0), (*on_back(-e, -0.84 - e), 0.0)]    # over the board's end
    y0, z0 = key[-1][:2]
    key += [(y0 - 0.06, z0 - 0.004, 0.0), (y0 - 0.31, z0 - 0.008, 0.0)]                # hanging straight down
    P = np.array(key)
    for _ in range(2):                          # round off the corners
        Q = [P[0]]
        for p, q in zip(P[:-1], P[1:]):
            Q += [0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q]
        P = np.array(Q + [P[-1]])
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1))])
    S = np.linspace(0.0, arc[-1], int(arc[-1] / step) + 1)
    path = np.stack([np.interp(S, arc, P[:, k]) for k in range(3)], axis=1)
    T = np.gradient(path[:, :2], axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.stack([-T[:, 1], T[:, 0]], axis=1)  # (y, z), away from the lounger
    w = path[:, 2][:, None]
    s_free = S[np.argmax(path[:, 2] < 1e-6)]

    # Across: 0.82 m wide, a little wider than the cushions, laid slightly askew.
    half, flat = 0.41, 0.33                     # flat: where the seat cushion's top starts to round over
    u = np.concatenate([np.linspace(-half, -flat, 5), np.linspace(-flat, flat, 11)[1:-1], np.linspace(flat, half, 5)])
    Sg = S[:, None]
    x0 = u[None, :] + shift + 0.035 * (Sg / S[-1] - 0.5)
    ax = np.abs(x0)
    over = np.clip(ax - flat, 0.0, None)
    th = np.minimum(over / r, math.pi / 2)
    wrap_x = np.where(ax <= flat, ax, flat + r * np.sin(th))
    wrap_drop = r * (1 - np.cos(th)) + np.clip(over - r * math.pi / 2, 0.0, None)
    X = np.sign(x0) * (w * wrap_x + (1 - w) * ax)
    hang = np.clip(Sg - s_free, 0.0, None)
    off = (w * (0.0025 * (1 + np.sin(9.0 * Sg + 1.3) * np.cos(12.0 * u + 0.4)) + 0.0015 * (1 + np.sin(19.0 * Sg + 5.0 * u + 2.1)))
           + np.clip(hang / 0.15, 0, 1) * (0.012 * np.sin(2 * math.pi * u / 0.15 + 0.7) + 0.004 * np.sin(2 * math.pi * u / 0.055 + 2.0))
           - w * wrap_drop)
    Y = path[:, 0][:, None] + N[:, 0][:, None] * off
    Z = path[:, 1][:, None] + N[:, 1][:, None] * off
    top_ = np.stack([X, Y, Z], axis=2)
    n = np.cross(np.gradient(top_, axis=1), np.gradient(top_, axis=0))
    n /= np.linalg.norm(n, axis=2)[:, :, None]
    under = top_ - n * t

    rows, cols = X.shape
    V = np.concatenate([top_.reshape(-1, 3), under.reshape(-1, 3)])
    up = lambda i, j: i * cols + j                       # noqa: E731
    dn = lambda i, j: rows * cols + i * cols + j         # noqa: E731
    faces, mats = [], []
    ends = (0.06, 0.12)                                  # a cream band across each end
    for i in range(rows - 1):
        mid = (S[i] + S[i + 1]) / 2
        mat = "towel" if ends[0] < min(mid, S[-1] - mid) < ends[1] else "towel_navy"
        for j in range(cols - 1):
            faces += [(up(i, j), up(i, j + 1), up(i + 1, j + 1), up(i + 1, j)),
                      (dn(i + 1, j), dn(i + 1, j + 1), dn(i, j + 1), dn(i, j))]
            mats += [mat, mat]
        J = cols - 1
        faces += [(up(i, 0), up(i + 1, 0), dn(i + 1, 0), dn(i, 0)), (up(i + 1, J), up(i, J), dn(i, J), dn(i + 1, J))]
        mats += ["towel_navy", "towel_navy"]
    I = rows - 1
    for j in range(cols - 1):
        faces += [(up(0, j + 1), up(0, j), dn(0, j), dn(0, j + 1)), (up(I, j), up(I, j + 1), dn(I, j + 1), dn(I, j))]
        mats += ["towel_navy", "towel_navy"]
    mesh_by_material(b, f.many(V), faces, mats)


def side_table(b):
    f = Frame(pair_point(*TABLE["at"]), PAIR_YAW)
    h, top = TABLE["half"], TABLE["top"]
    obox(b, "travertine", f, (-h, 0.012, -h), (h, top, h), skip=("-y",), density=2.0)
    obox(b, "dark_stone", f, (-h + 0.02, 0.0, -h + 0.02), (h - 0.02, 0.012, h - 0.02), skip=("-y", "+y"), density=1.0)
    return f


# ---- the table setting --------------------------------------------------------------------
# Where things stand on the table, in its frame (x toward my lounger, z toward the
# water). The visitor sees it from behind and to the left, so the card is nearest
# them and the tall bottle is furthest away.
CARD_AT, GLASSES_AT, BOTTLE_AT, CUP_AT = (-0.07, -0.08), (-0.08, 0.12), (0.10, 0.10), (0.13, -0.11)
CARD = dict(width=0.21, height=0.13)        # the picture is 768 x 480, the same shape
# An isshobin, the tall 1.8 litre sake bottle: (radius, height) from the base up
SAKE_PROFILE = [(0.0, 0.0), (0.048, 0.0), (0.0515, 0.004), (0.0525, 0.014), (0.0525, 0.262), (0.0505, 0.282),
                (0.0440, 0.300), (0.0340, 0.316), (0.0240, 0.330), (0.0175, 0.345), (0.0158, 0.360),
                (0.0155, 0.380), (0.0168, 0.384), (0.0168, 0.390)]
SAKE_CAP = [(0.0171, 0.3875), (0.0178, 0.3885), (0.0178, 0.401), (0.0090, 0.404), (0.0, 0.404)]
SAKE_LABEL = dict(radius=0.0530, bottom=0.085, height=0.144, span=170.0)   # the 720 ml label, scaled up


def facing(spot, eye):
    """The turn (degrees) that points +z from `spot` toward `eye`."""
    return math.degrees(math.atan2(eye[0] - spot[0], eye[2] - spot[2]))


def sake_set(b, table, camera_pos):
    """An isshobin of sake with the Sunakaze label, and a small stoneware cup with a
    little sake in it."""
    top = TABLE["top"]
    spot = np.array(table((BOTTLE_AT[0], top, BOTTLE_AT[1])))
    f = Frame(spot, facing(spot, camera_pos) + 25.0)          # label turned mostly toward the visitor
    lathe(b, "sake_bottle", f, SAKE_PROFILE, 40)
    lathe(b, "sake_cap", f, SAKE_CAP, 24)
    lathe(b, "bottle_gloss", f, [(r * 1.004 + 0.0002, y) for r, y in SAKE_PROFILE[2:-1]], 40)
    # the label: a band round the front of the bottle, its picture laid flat over it
    n_a, n_h = 24, 2
    lab = SAKE_LABEL
    span = math.radians(lab["span"])
    verts, faces, uvs = [], [], []
    for j in range(n_h + 1):
        y = lab["bottom"] + lab["height"] * j / n_h
        for i in range(n_a + 1):
            a = -span / 2 + span * i / n_a
            verts.append(f((lab["radius"] * math.sin(a), y, lab["radius"] * math.cos(a))))
    for j in range(n_h):
        for i in range(n_a):
            k = j * (n_a + 1) + i
            faces.append((k, k + 1, k + n_a + 2, k + n_a + 1))
            uvs.append([(i / n_a, j / n_h), ((i + 1) / n_a, j / n_h), ((i + 1) / n_a, (j + 1) / n_h), (i / n_a, (j + 1) / n_h)])
    b.mesh(G, "sake_label", verts, faces, uvs=uvs)
    # the cup, on my side, with sake still in it
    cup = Frame(table((CUP_AT[0], top, CUP_AT[1])), 0.0)
    outer = [(0.0, 0.0), (0.019, 0.0), (0.021, 0.005), (0.0235, 0.008), (0.0300, 0.036), (0.0312, 0.040)]
    inner = [(0.0285, 0.040), (0.0272, 0.034), (0.021, 0.012), (0.0, 0.010)]
    lathe(b, "stoneware", cup, outer + inner, 32)
    lathe(b, "sake", cup, [(0.0262, 0.030), (0.0, 0.030)], 24)


def contact_card(b, table, camera_pos):
    """A folded card standing on the table, its front turned toward the visitor and
    leaning back just enough to face their eyes. On the website it opens the
    "Get in touch" panel when clicked (the "click" list in rooms.js)."""
    top = TABLE["top"]
    spot = np.array(table((CARD_AT[0], top, CARD_AT[1])))
    f = Frame(spot, facing(spot, camera_pos))
    w, h = CARD["width"], CARD["height"]
    rise = camera_pos[1] - (top + h / 2)
    lean = math.atan2(rise, math.hypot(camera_pos[0] - spot[0], camera_pos[2] - spot[2]))
    lean = min(max(lean, math.radians(15)), math.radians(40))
    dz, dy = h * math.sin(lean), h * math.cos(lean)
    front = [(-w / 2, 0, dz), (w / 2, 0, dz), (w / 2, dy, 0), (-w / 2, dy, 0)]
    back = [(w / 2, 0, -dz), (-w / 2, 0, -dz), (-w / 2, dy, 0), (w / 2, dy, 0)]
    b.quad(G, "card", f.many([(x, y + 0.0005, z) for x, y, z in front]), ATLAS, 3.0,
           uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    b.quad(G, "card_back", f.many(back), ATLAS, 1.0)
    # the inside faces, so the card isn't paper-thin from the side
    b.quad(G, "card_back", f.many([front[1], front[0], front[3], front[2]]), ATLAS, 0.5)
    b.quad(G, "card_back", f.many([back[1], back[0], back[3], back[2]]), ATLAS, 0.5)


def sunglasses(b, table, camera_pos, n=40):
    """Black sunglasses, folded and set down lenses up, turned toward the visitor.
    Built upright first (x across, y up, z out of the lenses), then laid down."""
    parts = {"shades": ([], []), "shades_lens": ([], [])}

    def add(mat, V, F):
        verts, faces = parts[mat]
        k = len(verts)
        verts.extend(np.asarray(v, float) for v in V)
        faces.extend(tuple(k + i for i in face) for face in F)

    def bar(p0, p1, height, thick):
        """A slim rounded bar from p0 to p1 (both on the same z), standing `height` tall."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        length = np.linalg.norm(p1 - p0)
        V, F = _rounded_box((0, 0, 0), (length, height, thick), min(height, thick) * 0.4, 1)
        dx = (p1 - p0) / length
        M = np.stack([dx, np.cross((0, 0, 1.0), dx), (0, 0, 1.0)], axis=1)
        add("shades", [(p0 + p1) / 2 + M @ np.asarray(v) for v in V], F)

    a, h, rim, d = 0.0262, 0.0205, 0.0045, 0.003      # lens half-width and half-height, rim width, half-depth
    x_out = 0.0
    for side in (1.0, -1.0):
        cx = 0.0335 * side
        loop = []
        for ang in np.linspace(0, 2 * math.pi, n, endpoint=False):
            ca, sa = math.cos(ang), math.sin(ang)
            x = a * math.copysign(abs(ca) ** 0.62, ca) * (1 + 0.07 * math.copysign(abs(sa) ** 0.62, sa))
            y = h * math.copysign(abs(sa) ** 0.62, sa)
            if x * side < 0 and y < 0:                 # drawn in at the bottom on the nose side
                x *= 1 - 0.22 * (-y / h)
            loop.append((cx + x, y))
        loop = np.array(loop)                          # anticlockwise seen from the front
        tang = np.roll(loop, -1, axis=0) - np.roll(loop, 1, axis=0)
        out = np.stack([tang[:, 1], -tang[:, 0]], axis=1)
        outer = loop + out / np.linalg.norm(out, axis=1)[:, None] * rim
        x_out = max(x_out, float(np.abs(outer[:, 0]).max()))
        V = ([(x, y, d) for x, y in loop] + [(x, y, d) for x, y in outer]
             + [(x, y, -d) for x, y in outer] + [(x, y, -d) for x, y in loop])
        F = []
        for k in range(n):
            k1 = (k + 1) % n
            F += [(k, n + k, n + k1, k1), (3 * n + k1, 2 * n + k1, 2 * n + k, 3 * n + k),     # front, back
                  (n + k, 2 * n + k, 2 * n + k1, n + k1), (k1, 3 * n + k1, 3 * n + k, k)]     # outside, inside
        add("shades", V, F)
        add("shades_lens", [(cx, 0.0, 0.0015)] + [(x, y, 0.0) for x, y in loop], [(0, 1 + k, 1 + (k + 1) % n) for k in range(n)])
        add("shades_lens", [(cx, 0.0, 0.0007)] + [(x, y, -0.0008) for x, y in loop], [(0, 1 + (k + 1) % n, 1 + k) for k in range(n)])
    bar((-0.0105, 0.0125, 0.0), (0.0105, 0.0125, 0.0), 0.0055, 0.0055)          # the bridge
    for side, z in ((1.0, -0.0065), (-1.0, -0.0105)):
        hinge = np.array([side * (x_out - 0.004), 0.011, z])
        bar((side * (x_out - 0.008), 0.011, -0.004), (side * x_out, 0.011, -0.004), 0.010, 0.006)
        # the arms folded flat behind the lenses, one over the other, tips bent down
        bend = hinge + (-side * 0.095, 0.0, 0.0)
        bar(hinge, bend, 0.0095, 0.0032)
        tip = bend + 0.032 * np.array([-side * math.cos(math.radians(25)), -math.sin(math.radians(25)), 0.0])
        bar(bend, tip, 0.0085, 0.0032)

    spot = np.array(table((GLASSES_AT[0], TABLE["top"], GLASSES_AT[1])))
    R = rot(y=facing(spot, camera_pos)) @ rot(x=-60.0)
    low = min((R @ v)[1] for verts, _ in parts.values() for v in verts)
    for mat, (verts, faces) in parts.items():
        b.mesh(G, mat, [tuple(spot + R @ v - (0, low - 0.0004, 0)) for v in verts], faces)


# ---- my loafers ---------------------------------------------------------------------------
def loafers(b):
    """Tobacco suede loafers on the deck between the loungers (frozen meshes: one
    shoe, heel at the origin and toe toward +z, mirrored for the other foot)."""
    layers, _ = frozen("loafer")
    for (X, Z), turn, left in LOAFERS:
        f = Frame(pair_point(X, Z), PAIR_YAW + turn)
        for mat, V, F, _ in layers:
            if left:
                V, F = V * (-1.0, 1.0, 1.0), F[:, ::-1]
            b.mesh(G, mat, f.many(V), [tuple(t) for t in F.tolist()])


# ---- the parasol ----------------------------------------------------------------------------------
def parasol(b):
    """A cantilever parasol behind the loungers: a square base of dark stone weights,
    a slim bronze mast, and an arm curving over to the canopy's peak."""
    P = PARASOL
    mast, hub = pair_point(*P["mast"]), pair_point(*P["centre"])
    half, top = P["size"] / 2, P["top"]
    R = rot(y=PAIR_YAW)
    mx, mz = mast[0], mast[2]
    b.box(G, "dark_stone", (mx - 0.42, mx + 0.42), (0.0, 0.07), (mz - 0.42, mz + 0.42), atlas=ATLAS, skip=("-y",),
          solid=False, density=1.0)
    rod(b, "bronze_dark", (mx, 0.07, mz), (mx, 0.17, mz), 0.14)                  # collar
    rod(b, "bronze_dark", (mx, 0.07, mz), (mx, top + 0.30, mz), 0.085)           # mast
    # the arm: a shallow arc from near the mast's top to above the canopy's centre, then a short drop
    a0, a2 = np.array([mx, top + 0.22, mz]), np.array([hub[0], top + 0.22, hub[2]])
    a1 = (a0 + a2) / 2 + (0.0, 0.16, 0.0)
    arc = [(1 - t) ** 2 * a0 + 2 * t * (1 - t) * a1 + t * t * a2 for t in np.linspace(0, 1, 7)]
    for q0, q1 in zip(arc[:-1], arc[1:]):
        rod(b, "bronze_dark", q0, q1, 0.06)
    rod(b, "bronze_dark", a2, (hub[0], top - 0.02, hub[2]), 0.05)

    canopy(b, hub, half, top, R)


# Canopy shape: the ribs drop this far from the peak to the edge, bowed up a little
# (CANOPY_BOW above 1), as ribs are under the fabric's pull; each panel sags this
# much at the middle of its edge and is pulled in this fraction of its reach there,
# as stretched fabric is between the rib tips.
CANOPY_DROP, CANOPY_BOW, CANOPY_SAG, CANOPY_PULL = 0.36, 1.1, 0.022, 0.035
FABRIC = 0.003                                  # canvas thickness


def canopy(b, hub, half, top, R, nt=14, ns=8):
    """A square canopy of cream canvas tensioned over eight ribs, to the corners and
    the middle of each side: eight panels, each stretched straight between its two
    ribs and sagging a little between them, a raised seam along every rib, a rolled
    hem round the edge, a cap on the peak, and the ribs and hub underneath."""
    hub = np.asarray(hub, float)
    up = np.array([0.0, 1.0, 0.0])
    dirs = [np.array([math.cos(math.radians(45 * k)), 0.0, math.sin(math.radians(45 * k))]) for k in range(8)]
    reach = [half / max(abs(d[0]), abs(d[2])) for d in dirs]      # corner ribs are longer

    def rib(k, t):
        """A point on rib k's line along the top of the fabric, t = 0 at the peak, 1 at the tip."""
        return hub + R @ (dirs[k] * reach[k] * t) + up * (top - CANOPY_DROP * t ** CANOPY_BOW)

    def fabric(k, t, s_):
        """A point on the panel between rib k and rib k + 1 (s_ from 0 to 1 across)."""
        a, c = rib(k, t), rib((k + 1) % 8, t)
        q = (1 - s_) * a + s_ * c
        across = 4 * s_ * (1 - s_)
        flat = q - hub
        flat[1] = 0.0
        q = q - flat * CANOPY_PULL * across * t ** 6                  # the free edge pulled in between the tips
        return q - up * CANOPY_SAG * across * t ** 1.2                # and sagging between the ribs

    verts, faces = [], []

    def face(idx, want):
        """Add a face, turned so it faces along `want`."""
        pts = [np.asarray(verts[i]) for i in idx]
        nrm = np.cross(pts[1] - pts[0], pts[-1] - pts[0])
        faces.append(tuple(idx) if nrm @ want >= 0 else tuple(reversed(idx)))

    ts = np.linspace(0.025, 1.0, nt + 1)                              # the finial covers the tiny hole at the peak
    ss = np.linspace(0.0, 1.0, ns + 1)
    for k in range(8):
        for skin, sign in ((0.0, 1.0), (-FABRIC, -1.0)):               # upper face, then the underside
            base = len(verts)
            for t in ts:
                for s_ in ss:
                    verts.append(tuple(fabric(k, t, s_) + up * skin))
            for i in range(nt):
                for j in range(ns):
                    a = base + i * (ns + 1) + j
                    quad = (a, a + 1, a + ns + 2, a + ns + 1)
                    # facing up (or down underneath), leaning out from the peak
                    mid = np.mean([verts[q] for q in quad], axis=0) - hub
                    mid[1] = 0.0
                    face(quad, sign * (up + 0.3 * mid / max(np.linalg.norm(mid), 1e-6)))
    b.mesh(G, "canvas", verts, faces)

    # the rolled hem: a flattened tube about 1 cm thick wrapping each panel's free edge
    verts, faces = [], []
    ring = 8
    for k in range(8):
        edge = [fabric(k, 1.0, s_) for s_ in np.linspace(0.0, 1.0, 13)]
        base = len(verts)
        centres = []
        for i, e in enumerate(edge):
            along = edge[min(i + 1, 12)] - edge[max(i - 1, 0)]
            out = np.cross(along, up)
            out[1] = 0.0
            out /= np.linalg.norm(out)
            if out @ (e - hub) < 0:
                out = -out
            centre = e - out * 0.008 - up * 0.004
            centres.append(centre)
            for m in range(ring):
                phi = 2 * math.pi * m / ring
                verts.append(tuple(centre + out * 0.011 * math.cos(phi) + up * 0.0055 * math.sin(phi)))
        for i in range(12):
            for m in range(ring):
                a, c = base + i * ring + m, base + i * ring + (m + 1) % ring
                quad = (a, c, c + ring, a + ring)
                face(quad, np.mean([verts[q] for q in quad], axis=0) - (centres[i] + centres[i + 1]) / 2)
    b.mesh(G, "canvas", verts, faces)

    # a raised seam along the top of every rib, a shade darker than the canvas
    verts, faces = [], []
    for k in range(8):
        side = R @ np.cross(up, dirs[k])
        base = len(verts)
        for t in ts[1:-1]:
            c = rib(k, t)
            verts += [tuple(c - side * 0.010 + up * 0.0015), tuple(c + up * 0.004), tuple(c + side * 0.010 + up * 0.0015)]
        for i in range(len(ts) - 3):
            for j in range(2):
                a = base + i * 3 + j
                face((a, a + 1, a + 4, a + 3), up)
    b.mesh(G, "canvas_seam", verts, faces)

    # the ribs and hub underneath, a cap on each rib's tip and one on the peak
    for k in range(8):
        pts = [rib(k, t) - up * (FABRIC + 0.011) for t in np.linspace(0.04, 0.985, 9)]
        for q0, q1 in zip(pts[:-1], pts[1:]):
            rod(b, "bronze_dark", q0, q1, 0.02)
        tip = rib(k, 1.0)
        out = R @ dirs[k]
        rod(b, "bronze_dark", tip - out * 0.03 - up * 0.006, tip + out * 0.012 - up * 0.006, 0.026)
    rod(b, "bronze_dark", hub + up * (top - 0.01), hub + up * (top - 0.13), 0.055)
    cap = Frame(hub + up * (top - 0.004), 0.0)
    lathe(b, "bronze_dark", cap, [(0.0, 0.0), (0.062, 0.0), (0.060, 0.010), (0.045, 0.024), (0.022, 0.034),
                                  (0.009, 0.050), (0.0, 0.056)], 24)


# ---- the fire-pit lounge -----------------------------------------------------------------------
def sofa(b, f, width, depth=0.92, pillows=()):
    """A low outdoor sofa, built facing +z with its back along z = 0."""
    W = width / 2
    obox(b, "teak", f, (-W + 0.06, 0.0, 0.06), (W - 0.06, 0.11, depth - 0.06), skip=("-y",), density=0.5)
    obox(b, "teak", f, (-W, 0.11, 0.0), (W, 0.20, depth), skip=("-y",), density=0.6)
    soft_box(b, "canvas_sand", f, (0, 0.285, depth / 2 + 0.09), (width - 0.04, 0.17, depth - 0.2), 0.04)
    soft_box(b, "canvas_sand", f, (0, 0.47, 0.11), (width - 0.04, 0.44, 0.18), 0.05, tilt=-10, pivot=(0, 0.2, 0.1))
    for x, mat, turn in pillows:
        g = Frame(f((x, 0.0, 0.0)), f.yaw + turn)
        soft_box(b, mat, g, (0, 0.55, 0.30), (0.46, 0.44, 0.13), 0.06, tilt=-18, pivot=(0, 0.37, 0.3))


def fire_lounge(b):
    cx, cz = FIRE["centre"]
    # an outdoor rug with a darker woven border
    b.box(G, "rug_border", (cx - 2.25, cx + 2.25), (0.0, 0.010), (cz - 1.85, cz + 1.65), atlas=ATLAS, skip=("-y",), solid=False, density=0.25)
    b.box(G, "rug_outdoor", (cx - 2.10, cx + 2.10), (0.010, 0.013), (cz - 1.70, cz + 1.50), atlas=ATLAS, skip=("-y",), solid=False, density=0.3)
    sofa(b, Frame((cx, 0.0, cz - 1.80), 0.0), 3.6, pillows=((-1.25, "pillow_rust", 8), (1.2, "pillow_olive", -6), (0.85, "pillow_rust", -14)))
    sofa(b, Frame((cx - 2.65, 0.0, cz - 0.10), 90.0), 2.2, pillows=((-0.6, "pillow_olive", 6),))
    sofa(b, Frame((cx + 2.65, 0.0, cz - 0.10), -90.0), 2.2, pillows=((0.55, "pillow_rust", -8),))
    # the fire pit: a long low trough of dark stone with a bed of dark glass and low flames
    hx, hz, h = 0.80, 0.36, 0.38
    world = Frame((0, 0, 0))
    for x, z in (((cx - hx, cx + hx), (cz - hz, cz - hz + 0.07)), ((cx - hx, cx + hx), (cz + hz - 0.07, cz + hz)),
                 ((cx - hx, cx - hx + 0.07), (cz - hz + 0.07, cz + hz - 0.07)), ((cx + hx - 0.07, cx + hx), (cz - hz + 0.07, cz + hz - 0.07))):
        b.box(G, "dark_stone", x, (0.013, h), z, atlas=ATLAS, skip=("-y",), solid=False, density=1.2)
    b.floor(G, "dark_stone", ATLAS, (cx - hx + 0.07, cx + hx - 0.07), (cz - hz + 0.07, cz + hz - 0.07), h - 0.06, density=0.8)
    burner(b, cx, h - 0.06, cz, 1.25)
    LAMPS.append(dict(name="fire", kind="point", pos=(cx, h + 0.22, cz), watts=110.0, colour=(1.0, 0.45, 0.16), radius=0.25))


def burner(b, cx, y, cz, length):
    """A bed of dark glass pebbles with a ribbon of low flames along it."""
    rng = random.Random(3)
    verts, faces = [], []
    for i in range(70):
        x = cx + rng.uniform(-length / 2, length / 2)
        z = cz + rng.uniform(-0.13, 0.13)
        r = rng.uniform(0.012, 0.024)
        j = len(verts)
        verts += [(x - r, y + 0.001, z), (x, y + 0.001, z - r), (x + r, y + 0.001, z), (x, y + 0.001, z + r), (x, y + r * 0.6, z)]
        faces += [(j, j + 4, j + 1), (j + 1, j + 4, j + 2), (j + 2, j + 4, j + 3), (j + 3, j + 4, j)]
    b.mesh(G, "fire_glass", verts, faces, smooth=False)
    # flames: two crossing ribbons with a ragged top, glowing
    verts, faces = [], []
    n = 40
    for side in (-1, 1):
        base = len(verts)
        for i in range(n + 1):
            t = i / n
            x = cx - length * 0.45 + length * 0.9 * t
            hgt = 0.06 + 0.11 * abs(math.sin(t * 19.0 + side)) * (0.5 + 0.5 * math.sin(t * 7.0)) ** 2 * math.sin(math.pi * t) ** 0.5
            verts += [(x, y + 0.005, cz + side * 0.02), (x, y + 0.005 + hgt, cz - side * 0.01)]
        for i in range(n):
            a = base + 2 * i
            faces.append((a, a + 2, a + 3, a + 1))
            faces.append((a + 1, a + 3, a + 2, a))           # both sides glow
    b.mesh(G, "flame", verts, faces, smooth=False)


# ---- planters, trees and palms -------------------------------------------------------------------
def planter(b, x, z, size, h):
    """A big square planter in pale stone, with pebbles on top and an uplight in them."""
    s, rim = size / 2, 0.06
    b.box(G, "stone", (x - s, x + s), (0.0, h), (z - s, z - s + rim), atlas=ATLAS, skip=("-y",), solid=False, density=0.7)
    b.box(G, "stone", (x - s, x + s), (0.0, h), (z + s - rim, z + s), atlas=ATLAS, skip=("-y",), solid=False, density=0.7)
    b.box(G, "stone", (x - s, x - s + rim), (0.0, h), (z - s + rim, z + s - rim), atlas=ATLAS, skip=("-y",), solid=False, density=0.7)
    b.box(G, "stone", (x + s - rim, x + s), (0.0, h), (z - s + rim, z + s - rim), atlas=ATLAS, skip=("-y",), solid=False, density=0.7)
    soil = h - 0.05
    b.floor(G, "mulch", ATLAS, (x - s + rim, x + s - rim), (z - s + rim, z + s - rim), soil, density=0.8)
    # a small round uplight set in the pebbles, washing the tree above
    lx, lz = x + s * 0.45, z + s * 0.45
    b.mesh(G, "light_warm", [(lx + 0.035 * math.cos(a), soil + 0.004, lz + 0.035 * math.sin(a))
                            for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)] + [(lx, soil + 0.004, lz)],
           [(12, (i + 1) % 12, i) for i in range(12)], smooth=False)
    LAMPS.append(dict(name=f"uplight_{len(LAMPS)}", kind="spot", pos=(lx, soil + 0.05, lz), aim=(-0.25, 1.0, -0.25),
                      watts=28.0, cone=60.0))
    return soil


def plants_in_planters(b):
    from .plants import palm
    from .props import load, place
    rng = random.Random(17)
    tree = load("quiver_tree_02", thin={"quiver_tree_02": 0.08})["quiver_tree_02"]     # 82k triangles to 6.6k
    # stand it on its trunk's foot, not the middle of its crown
    low = min(v[1] for v in tree.verts)
    foot = [v for v in tree.verts if v[1] < low + 0.05]
    origin = (sum(v[0] for v in foot) / len(foot), low + 0.04, sum(v[2] for v in foot) / len(foot))
    for x, z, turn, scale in TREES:
        soil = planter(b, x, z, 0.95, 0.68)
        place(b, G, "quiver_tree", tree, (x, soil, z), yaw=math.radians(turn), scale=scale, origin=origin)
    for x, z, h in PALMS:
        soil = planter(b, x, z, 1.15, 0.60)
        palm(b, rng, x, z, h, base=soil)


# ---- lanterns ---------------------------------------------------------------------------------------
def lantern(b, x, z, h=0.64, s=0.13):
    """A floor lantern: a slim dark bronze frame round frosted glass, glowing warm."""
    f = Frame((x, 0.0, z), 15.0)
    soft_box(b, "bronze_dark", f, (0, 0.016, 0), (2 * s + 0.03, 0.032, 2 * s + 0.03), 0.006, n=1)
    soft_box(b, "bronze_dark", f, (0, h - 0.02, 0), (2 * s + 0.04, 0.04, 2 * s + 0.04), 0.008, n=1)
    soft_box(b, "bronze_dark", f, (0, h + 0.012, 0), (2 * s - 0.06, 0.024, 2 * s - 0.06), 0.006, n=1)
    for cx in (-s, s):
        for cz in (-s, s):
            soft_box(b, "bronze_dark", f, (cx, h / 2, cz), (0.022, h - 0.04, 0.022), 0.004, n=1)
    y0, y1 = 0.035, h - 0.04
    i = s - 0.008
    for pts in ([(-i, y0, i), (i, y0, i), (i, y1, i), (-i, y1, i)], [(i, y0, -i), (-i, y0, -i), (-i, y1, -i), (i, y1, -i)],
                [(i, y0, i), (i, y0, -i), (i, y1, -i), (i, y1, i)], [(-i, y0, -i), (-i, y0, i), (-i, y1, i), (-i, y1, -i)]):
        b.mesh(G, "lantern_glow", f.many(pts), [(0, 1, 2, 3)], smooth=False)
    LAMPS.append(dict(name=f"lantern_{len(LAMPS)}", kind="point", pos=(x, h * 0.45, z), watts=14.0, radius=0.08))


# ---- frozen meshes and the visitor's hand ----------------------------------------------------
def frozen(name):
    """A mesh kept in `frozen/` (see PROGRESS.md, "Frozen meshes"): a list of
    (material, verts, faces, linear colours or None), and any extra arrays saved with it."""
    with np.load(FROZEN / f"{name}.npz") as z:
        layers = [(str(m), z[f"V_{m}"].astype(float), z[f"F_{m}"].astype(int),
                   z[f"C_{m}"].astype(float) if f"C_{m}" in z.files else None) for m in z["layers"]]
        extras = {k[2:]: z[k] for k in z.files if k.startswith("X_")}
    return layers, extras


def visitor_hand(b):
    """The visitor's right hand holding the glass by the stem low in the frame, with
    the rolled cuff of a pale linen shirt. It is stored in the camera's own frame, so
    it follows MOMENT_CAM. Returns the point where the fingers grip the stem."""
    layers, extras = frozen("visitor_hand")
    pos = np.asarray(MOMENT_CAM["pos"], float)
    R = camera_axes(MOMENT_CAM["pos"], MOMENT_CAM["target"])
    for mat, V, F, C in layers:
        b.mesh(G, mat, [tuple(v) for v in pos + V @ R.T], [tuple(t) for t in F.tolist()],
               colors=None if C is None else [tuple(c) for c in C.tolist()])
    return pos + R @ extras["grip"]


def martini(b, grip):
    """A martini glass held by the stem, with an olive on a pick."""
    f = Frame(np.asarray(grip) - [0.0, 0.050, 0.0], 30.0)
    glass = [(0.0, 0.0), (0.036, 0.0), (0.037, 0.002), (0.034, 0.004), (0.006, 0.007), (0.0034, 0.016), (0.0030, 0.092),
             (0.0060, 0.098), (0.0590, 0.168), (0.0600, 0.170), (0.0575, 0.170), (0.0040, 0.1015), (0.0, 0.1012)]
    lathe(b, "martini_glass", f, glass, 40)
    level = 0.150
    r = 0.004 + (0.0575 - 0.004) * (level - 0.1015) / (0.170 - 0.1015)
    lathe(b, "martini", f, [(r, level), (0.0, level)], 32)
    lathe(b, "martini", f, [(0.0, 0.103), (0.0035, 0.1035), (r - 0.0008, level - 0.0005)], 32)
    # the olive on its pick, leaning against the rim
    pick = np.array([[0.004, 0.118, -0.004], [0.052, 0.198, 0.010]])
    d = pick[1] - pick[0]
    Rp = axes(d, (0.0, 0.0, 1.0))
    olive_c = pick[0] + d * 0.25
    verts, faces = _lathe([(0.0, 0.011), (0.006, 0.0095), (0.0095, 0.005), (0.0105, 0.0), (0.0095, -0.005),
                           (0.006, -0.0095), (0.0, -0.011)], 16)
    b.mesh(G, "olive_fruit", [f(olive_c + Rp @ np.array([v[0], -v[2], v[1]])) for v in verts], faces)
    rod, rf = _lathe([(0.0012, float(np.linalg.norm(d))), (0.0012, 0.0)], 6)
    b.mesh(G, "pick", [f(pick[0] + Rp @ np.array([v[0], -v[2], v[1]])) for v in rod], rf)


def build_pool(b):
    """Furnish the deck."""
    LAMPS.clear()
    eye = np.array(MOMENT_CAM["pos"])
    with b.room(ROOM):
        lounger(b, lounger_frame(VISITOR_LOUNGER), towel="folded")
        lounger(b, lounger_frame(MY_LOUNGER), towel="draped")
        table = side_table(b)
        sake_set(b, table, eye)
        contact_card(b, table, eye)
        sunglasses(b, table, eye)
        loafers(b)
        parasol(b)
        fire_lounge(b)
        plants_in_planters(b)
        for x, z in LANTERNS:
            lantern(b, x, z)
        with b.attached("camera"):
            martini(b, visitor_hand(b))


def paint_pictures():
    from .labels import paint_card, paint_sake_label
    paint_card()
    paint_sake_label()
