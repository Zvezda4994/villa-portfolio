"""The house itself: slabs, walls, glazing, stairs and roof. No furniture.

Plan, looking down, front of the house (driveway) at the bottom:

    Ground floor                       Upstairs
    +---------+-------+-----------+    +---------+---------+---------+
    | kitchen | dining : living   |    | bedroom | games   | trophy  |=terrace
    +---------+-------+--+--------+    |         +----+----+---------+
    | garage  | foyer |st| gym    |    +---------+land|   library    |
    |         |       |ud|        |    | lounge  |ing |              |
    +---------+-------+--+--------+    +---------+----+--------------+

The dark stone "blade" wall runs between the foyer and the study, out through
the front of the house and up past the roof.
"""
import math
import random

from . import config as C

W, D, T, P = C.HALF_W, C.HALF_D, C.WALL, C.PART
H1, F2, RY = C.H1, C.F2, C.ROOF_Y
BX0, BX1 = C.BLADE_X
SX0, SX1 = C.STAIR_X0, C.STAIR_X1
SZ0, SZ1 = C.STAIR_Z
DOOR = 2.3            # head height of inside doorways

# The sheer curtains inside the upstairs glass are off everywhere (your choice, 21 Nov
# 2026, from the landing shot with and without them): the rooms read clearly from
# outside. SHEERS = True brings them back, except in NO_SHEERS (the games room has a
# blackout blind; the trophy room opens onto the terrace). Also the rooms whose ceiling
# downlights are switched off (the games room is lit by its screens, the gym by its
# hanging LED bars). Their fittings are still there, just not glowing.
SHEERS = False
NO_SHEERS = {"games", "trophy"}
LIGHTS_OFF = {"games", "gym"}

# Rooms: name -> (group, x range, z range, floor material). Also used to place lights.
ROOMS = {
    "garage":  ("ground", (-W, -5), (0, D), "floor_dark"),
    "foyer":   ("ground", (-5, BX0), (0, D), "floor_stone"),
    "study":   ("ground", (BX1, 6), (0, D), "floor_wood"),
    "gym":     ("ground", (6, W), (0, D), "floor_dark"),
    "kitchen": ("ground", (-W, -5), (-D, 0), "floor_stone"),
    "dining":  ("ground", (-5, 1), (-D, 0), "floor_wood"),
    "living":  ("ground", (1, W), (-D, 0), "floor_wood"),
    "bedroom": ("upper", (-W, -5), (-D, 2), "floor_wood"),
    "lounge":  ("upper", (-W, -5), (2, D), "floor_stone"),
    "landing": ("upper", (-5, BX0), (0, D), "floor_stone"),
    "library": ("upper", (BX1, W), (0, D), "floor_wood"),
    "games":   ("upper", (-5, 4), (-D, 0), "floor_dark"),
    "trophy":  ("upper", (4, W), (-D, 0), "floor_stone"),
}


# ---- helpers ---------------------------------------------------------------
def wall_run(b, group, along, a0, a1, t0, t1, y0, y1, openings=(), *, inside, outside=None,
             mat_in="plaster", mat_out="stone"):
    """A straight wall with openings cut in it.

    along      'x' or 'z', the direction the wall runs
    a0, a1     where it starts and ends in that direction
    t0, t1     its thickness, on the other axis
    openings   (start, end, sill height, head height), absolute coordinates
    inside     lightmap atlas for faces that look into the house
    outside    which face looks outdoors ("+z", "-x"...), or None for a partition
    """
    def piece(s0, s1, lo, hi, kind):
        if s1 - s0 < 1e-4 or hi - lo < 1e-4:
            return
        if outside:
            # stone wraps the outside face and the edges of openings
            over = {f: dict(mat=mat_out, atlas="ext") for f in ("+x", "-x", "+y", "-y", "+z", "-z")}
            inward = outside[0] == "+" and "-" + outside[1] or "+" + outside[1]
            over[inward] = dict(mat=mat_in, atlas=inside)
        else:
            over = {}
        skip = []
        if kind in ("full", "lintel"):
            over["+y"] = dict(mat="cut")       # top of the wall, seen when the roof is off
        if kind in ("full", "sill"):
            skip.append("-y")
        span = dict(x=(s0, s1), z=(t0, t1)) if along == "x" else dict(z=(s0, s1), x=(t0, t1))
        b.box(group, mat_in, y=(lo, hi), atlas=inside, skip=skip, over=over, **span)

    cur = a0
    for o0, o1, sill, head in sorted(openings):
        piece(cur, o0, y0, y1, "full")
        piece(o0, o1, y0, sill, "sill")
        piece(o0, o1, head, y1, "lintel")
        cur = o1
    piece(cur, a1, y0, y1, "full")


def glazing(b, group, along, a0, a1, t, y0, y1, *, mat="glass", every=1.9, bar=0.05, depth=0.11, rows=0):
    """A sheet of glass with a dark frame and evenly spaced mullions."""
    def frame(s0, s1, lo, hi):
        span = dict(x=(s0, s1), z=(t - depth / 2, t + depth / 2)) if along == "x" \
            else dict(z=(s0, s1), x=(t - depth / 2, t + depth / 2))
        b.box(group, "frame", y=(lo, hi), solid=False, cull=False, **span)

    if along == "x":
        b.quad(group, mat, [(a0, y0, t), (a1, y0, t), (a1, y1, t), (a0, y1, t)])
    else:
        b.quad(group, mat, [(t, y0, a1), (t, y0, a0), (t, y1, a0), (t, y1, a1)])
    frame(a0, a1, y0, y0 + bar)
    frame(a0, a1, y1 - bar, y1)
    panes = max(1, round((a1 - a0) / every))
    for i in range(panes + 1):
        s = a0 + (a1 - a0) * i / panes
        s = min(max(s, a0 + bar / 2), a1 - bar / 2)
        frame(s - bar / 2, s + bar / 2, y0 + bar, y1 - bar)
    for r in range(1, rows):
        yy = y0 + (y1 - y0) * r / rows
        frame(a0, a1, yy - bar / 2, yy + bar / 2)


def _runs(cells):
    """Merge neighbouring cells of the same kind in a row, to keep faces large."""
    out = []
    for kind, x0, x1 in cells:
        if out and out[-1][0] == kind and abs(out[-1][2] - x0) < 1e-6:
            out[-1][2] = x1
        else:
            out.append([kind, x0, x1])
    return out


# ---- the build -------------------------------------------------------------
def build_house(b):
    ground_floor(b)
    stairs(b)
    upper_slab(b)
    upper_floor(b)
    roof(b)
    blade_wall(b)
    downlights(b)


def ground_floor(b):
    g = "ground"
    # A plinth under the whole house, so the floor never looks like it is floating.
    b.box(g, "concrete", (-W, W), (-0.45, -0.002), (-D, D), atlas="ext", skip=("+y", "-y"), density=0.5)

    for name, (group, x, z, mat) in ROOMS.items():
        if group == g:
            b.floor(g, mat, "gnd", x, z, 0.0)
    b.floor(g, "floor_stone", "gnd", (BX0, BX1), (5.0, 6.2), 0.0)       # threshold through the stone wall

    # Outside walls
    front = [(-11.2, -5.8, 0, 2.7), (-4.3, BX0, 0, H1), (BX0, BX1, 0, H1), (BX1, 11.4, 0, H1)]
    wall_run(b, g, "x", -W, W, D - T, D, 0, H1, front, inside="gnd", outside="+z")
    back = [(-11.0, -6.0, 1.1, 2.3), (-4.4, 0.4, 0, H1), (1.2, 4.4, 0, H1), (10.5, 11.5, 0, H1)]
    wall_run(b, g, "x", -W, W, -D, -D + T, 0, H1, back, inside="gnd", outside="-z")
    wall_run(b, g, "z", -D + T, D - T, -W, -W + T, 0, H1, [(-6.5, -1.5, 1.1, 2.5)], inside="gnd", outside="-x")
    wall_run(b, g, "z", -D + T, D - T, W - T, W, 0, H1, [(1.0, 7.0, 0, H1)], inside="gnd", outside="+x")

    zf, zb = D - T / 2, -D + T / 2
    glazing(b, g, "x", -11.2, -5.8, zf, 0, 2.7, mat="glass_smoke", every=1.35, rows=5)   # garage door
    glazing(b, g, "x", -4.3, -2.9, zf, 0, H1, every=1.4)                                  # either side of the front door
    glazing(b, g, "x", -1.5, BX0, zf, 0, H1, every=1.25)
    glazing(b, g, "x", BX1, 11.4, zf, 0, H1, every=1.65)                                  # study and gym
    glazing(b, g, "x", -11.0, -6.0, zb, 1.1, 2.3, every=2.5)                              # kitchen
    glazing(b, g, "x", -4.4, 0.4, zb, 0, H1, every=1.6)                                   # dining, onto the pool deck
    glazing(b, g, "x", 1.2, 4.4, zb, 0, H1, every=1.6)                                    # living
    glazing(b, g, "x", 10.5, 11.5, zb, 0, H1)
    glazing(b, g, "z", -6.5, -1.5, -W + T / 2, 1.1, 2.5, every=2.5)                       # kitchen side window
    glazing(b, g, "z", 1.0, 7.0, W - T / 2, 0, H1, every=1.5)                             # gym

    # Front door: a tall oak pivot door with a brass pull.
    b.box(g, "oak", (-2.9, -1.5), (0, 3.0), (zf - 0.035, zf + 0.035), atlas="ext",
          over={"-z": dict(atlas="gnd")}, skip=("-y",), solid=False, cull=False, rot=True)
    b.box(g, "frame", (-2.9, -1.5), (3.0, H1), (zf - 0.055, zf + 0.055), solid=False, cull=False)
    b.box(g, "brass", (-1.74, -1.70), (0.85, 2.15), (zf + 0.035, zf + 0.10), solid=False, cull=False)

    # Inside partitions
    h = P / 2
    doors = lambda *spans: [(a, c, 0, DOOR) for a, c in spans]   # noqa: E731
    wall_run(b, g, "x", -W + T, W - T, -h, h, 0, H1,
             doors((-9.5, -8.3), (-0.2, 0.8), (3.0, 4.2), (8.4, 9.6)), inside="gnd")
    wall_run(b, g, "z", h, D - T, -5 - h, -5 + h, 0, H1, doors((3.4, 4.6)), inside="gnd")          # garage | foyer
    wall_run(b, g, "z", -D + T, -h, -5 - h, -5 + h, 0, H1, [(-5.5, -2.5, 0, 2.6)], inside="gnd")   # kitchen | dining
    wall_run(b, g, "z", h, D - T, 6 - h, 6 + h, 0, H1, doors((3.4, 4.6)), inside="gnd")            # study | gym


def stairs(b):
    """A solid block stair: white sides and risers, oak treads. It starts on the foyer floor
    at its east end and climbs west; the last step up is onto the landing's floor, which
    covers the alcove under the top. The alcove is closed off on the foyer side. The little
    door in the stair's side is the way into the resume."""
    g = "ground"
    rise = F2 / C.STAIR_RISERS
    T = C.STAIR_TREAD
    for i in range(C.STAIR_RISERS - 1):                 # i = 0 is the bottom step
        x1 = SX1 - i * T
        x0, top = x1 - T, (i + 1) * rise
        b.floor(g, "oak", "gnd", (x0, x1), (SZ0, SZ1), top, rot=True)
        b.quad(g, "plaster", [(x1, top - rise, SZ1), (x1, top - rise, SZ0), (x1, top, SZ0), (x1, top, SZ1)], "gnd")   # riser, facing east
        b.quad(g, "plaster", [(x0, 0, SZ1), (x1, 0, SZ1), (x1, top, SZ1), (x0, top, SZ1)], "gnd")                    # side
        b.solids.append((x0, x1, 0, top, SZ0, SZ1))
    # the alcove under the top, closed on the foyer side
    xw = -5 + P / 2
    b.quad(g, "plaster", [(xw, 0, SZ1), (SX0, 0, SZ1), (SX0, H1, SZ1), (xw, H1, SZ1)], "gnd")
    b.solids.append((xw, SX0, 0, H1, SZ0, SZ1))
    # the small door
    dx0, dx1, dh = -2.75, -2.0, 1.3
    b.box(g, "oak", (dx0, dx1), (0, dh), (SZ1, SZ1 + 0.03), atlas="gnd", skip=("-y", "-z"), solid=False, cull=False, rot=True)
    b.box(g, "frame", (dx0 - 0.04, dx1 + 0.04), (dh, dh + 0.04), (SZ1, SZ1 + 0.035), solid=False, cull=False)
    b.box(g, "frame", (dx0 - 0.04, dx0), (0, dh), (SZ1, SZ1 + 0.035), solid=False, cull=False)
    b.box(g, "frame", (dx1, dx1 + 0.04), (0, dh), (SZ1, SZ1 + 0.035), solid=False, cull=False)
    b.box(g, "brass", (dx1 - 0.14, dx1 - 0.09), (0.62, 0.67), (SZ1 + 0.03, SZ1 + 0.075), solid=False, cull=False)


def upper_slab(b):
    """The slab between the floors. Outside the walls it carries on as a thin
    ledge all round, and at the back right it becomes the terrace over the pool."""
    g = "upper"
    LX, LZF, LZB = 12.9, 9.4, -8.9       # how far the ledge reaches
    TX0, TZ = 3.5, -11.2                 # terrace
    xs = sorted({-LX, -W, SX0, SX1, TX0, W, LX})
    zs = sorted({TZ, LZB, -D, SZ0, SZ1, D, LZF})

    def kind_of(cx, cz):
        if SX0 < cx < SX1 and SZ0 < cz < SZ1:
            return None                                   # the stairwell
        if abs(cx) < W and abs(cz) < D:
            return "inside"
        if cz < LZB:
            return "terrace" if cx > TX0 else None
        if cz < -D and cx > TX0:
            return "terrace"
        return "ledge"

    for z0, z1 in zip(zs, zs[1:]):
        row = [(kind_of((x0 + x1) / 2, (z0 + z1) / 2), x0, x1) for x0, x1 in zip(xs, xs[1:])]
        for kind, x0, x1 in _runs(row):
            if kind is None:
                continue
            if kind == "inside":
                # underside is the ground floor ceiling; the top is covered by floor finishes
                b.box(g, "plaster", (x0, x1), (H1, F2), (z0, z1), atlas="upr", skip=("+y",),
                      over={"-y": dict(atlas="gnd")})
            else:
                top = "paving" if kind == "terrace" else "concrete"
                b.box(g, "concrete", (x0, x1), (H1, F2), (z0, z1), atlas="ext",
                      over={"+y": dict(mat=top, density=0.7), "-y": dict(mat="oak", rot=True)})

    # glass balustrades: round the stairwell (its long side and its east end; its west end is
    # where the stairs arrive) and round the terrace
    rail = F2 + 1.0
    b.quad(g, "glass", [(SX0, F2, SZ1), (SX1, F2, SZ1), (SX1, rail, SZ1), (SX0, rail, SZ1)])
    b.box(g, "brass", (SX0 - 0.02, SX1 + 0.02), (rail, rail + 0.03), (SZ1 - 0.02, SZ1 + 0.02), solid=False, cull=False)
    b.quad(g, "glass", [(SX1, F2, SZ1), (SX1, F2, SZ0), (SX1, rail, SZ0), (SX1, rail, SZ1)])
    b.box(g, "brass", (SX1 - 0.02, SX1 + 0.02), (rail, rail + 0.03), (SZ0, SZ1), solid=False, cull=False)
    for x in (SX0, SX1):                                     # posts at the corners, and a brass shoe along the glass
        b.box(g, "brass", (x - 0.02, x + 0.02), (F2, rail), (SZ1 - 0.02, SZ1 + 0.02), solid=False, cull=False)
    b.box(g, "frame", (SX0, SX1), (F2, F2 + 0.05), (SZ1 - 0.015, SZ1 + 0.015), solid=False, cull=False)
    b.box(g, "frame", (SX1 - 0.015, SX1 + 0.015), (F2, F2 + 0.05), (SZ0, SZ1), solid=False, cull=False)
    rail = F2 + 1.05
    x0, x1, z0 = TX0 + 0.06, LX - 0.06, TZ + 0.06
    b.quad(g, "glass", [(x1, F2, z0), (x0, F2, z0), (x0, rail, z0), (x1, rail, z0)])
    b.quad(g, "glass", [(x1, F2, -D), (x1, F2, z0), (x1, rail, z0), (x1, rail, -D)])
    b.quad(g, "glass", [(x0, F2, z0), (x0, F2, -D), (x0, rail, -D), (x0, rail, z0)])
    b.box(g, "brass", (x0, x1), (rail, rail + 0.03), (z0 - 0.02, z0 + 0.02), solid=False, cull=False)
    b.box(g, "brass", (x1 - 0.02, x1 + 0.02), (rail, rail + 0.03), (z0, -D), solid=False, cull=False)
    b.box(g, "brass", (x0 - 0.02, x0 + 0.02), (rail, rail + 0.03), (z0, -D), solid=False, cull=False)


def upper_floor(b):
    g = "upper"
    for name, (group, x, z, mat) in ROOMS.items():
        if group != g:
            continue
        if name == "landing":
            # leave the stairwell open
            b.floor(g, mat, "upr", (x[0], x[1]), (SZ1, z[1]), F2)
            b.floor(g, mat, "upr", (SX1, x[1]), (z[0], SZ1), F2)
            b.floor(g, mat, "upr", (x[0], SX0), (z[0], SZ1), F2)
        else:
            b.floor(g, mat, "upr", x, z, F2)
    b.floor(g, "floor_stone", "upr", (BX0, BX1), (4.0, 5.2), F2)

    front = [(-11.2, -5.8, F2, RY), (-4.3, BX0, F2, RY), (BX0, BX1, F2, RY), (2.2, 11.4, F2, RY)]
    wall_run(b, g, "x", -W, W, D - T, D, F2, RY, front, inside="upr", outside="+z")
    back = [(-10.5, -6.5, F2, RY), (-1.5, 1.5, F2, RY), (5.0, 11.0, F2, RY)]
    wall_run(b, g, "x", -W, W, -D, -D + T, F2, RY, back, inside="upr", outside="-z")
    wall_run(b, g, "z", -D + T, D - T, -W, -W + T, F2, RY, [(-6.0, -2.0, F2, RY)], inside="upr", outside="-x")
    wall_run(b, g, "z", -D + T, D - T, W - T, W, F2, RY, [], inside="upr", outside="+x")

    zf, zb = D - T / 2, -D + T / 2
    # (room, direction, start, end, glass line, which way is indoors, mullion spacing)
    runs = [
        ("lounge", "x", -11.2, -5.8, zf, -1, 1.8),
        ("landing", "x", -4.3, BX0, zf, -1, 1.75),
        ("library", "x", 2.2, 11.4, zf, -1, 1.85),
        ("bedroom", "x", -10.5, -6.5, zb, 1, 2.0),
        ("games", "x", -1.5, 1.5, zb, 1, 1.5),
        ("trophy", "x", 5.0, 11.0, zb, 1, 2.0),            # onto the terrace
        ("bedroom", "z", -6.0, -2.0, -W + T / 2, 1, 2.0),  # side window
    ]
    rng = random.Random(3)
    for room, along, a0, a1, t, indoors, every in runs:
        glazing(b, g, along, a0, a1, t, F2, RY, every=every)
        # Sheer curtains just inside, if SHEERS is on. (The random
        # numbers are drawn either way, so the other rooms' curtains don't move.)
        sheers(b, rng, along, a0, a1, t + indoors * (T / 2 + 0.16), indoors, keep=SHEERS and room not in NO_SHEERS)

    h = P / 2
    top = F2 + DOOR
    wall_run(b, g, "x", -5, W - T, -h, h, F2, RY, [(-0.15, 0.85, F2, top), (7.0, 8.2, F2, top)], inside="upr")
    wall_run(b, g, "x", -W + T, -5, 2 - h, 2 + h, F2, RY, [(-9.5, -7.5, F2, top)], inside="upr")       # bedroom | lounge
    wall_run(b, g, "z", -D + T, D - T, -5 - h, -5 + h, F2, RY, [(5.0, 6.2, F2, top)], inside="upr")    # left bay | middle
    wall_run(b, g, "z", -D + T, -h, 4 - h, 4 + h, F2, RY, [(-4.6, -3.4, F2, top)], inside="upr")       # games | trophy


def sheers(b, rng, along, a0, a1, t, indoors, keep=True):
    """Two sheer curtains along one run of glass, drawn in from the ends with a gap
    of varying width between them, softly gathered into folds. With keep=False
    nothing is built, but the same random numbers are used up."""
    y0, y1 = F2 + 0.03, RY - 0.05
    span = a1 - a0
    left, right = rng.uniform(0.3, 0.55), rng.uniform(0.3, 0.55)
    if left + right > 0.9:
        left = right = 0.5                       # drawn all the way across
    rows = 4
    for p0, p1 in ((a0 + 0.02, a0 + left * span), (a1 - right * span, a1 - 0.02)):
        n = int((p1 - p0) / 0.05) + 2
        verts, faces = [], []
        phase = rng.uniform(0, 2 * math.pi)
        if not keep:
            continue
        for i in range(n):
            s = p0 + (p1 - p0) * i / (n - 1)
            # deeper folds near the outer end, where the fabric is stacked
            stack = 1.0 - min(abs(s - a0), abs(a1 - s)) / max(span * 0.5, 0.01)
            off = (0.03 + 0.03 * stack) * math.sin(2 * math.pi * (s - p0) / 0.24 + phase)
            for r in range(rows):
                y = y0 + (y1 - y0) * r / (rows - 1)
                d = t - indoors * off
                verts.append((s, y, d) if along == "x" else (d, y, s))
        # faces point at the glass, so they are lit from outside in the bake
        flip = (along == "x") == (indoors > 0)
        for i in range(n - 1):
            for r in range(rows - 1):
                a, c = i * rows + r, (i + 1) * rows + r
                faces.append((a, a + 1, c + 1, c) if flip else (a, c, c + 1, a + 1))
        b.mesh("upper", "sheer", verts, faces, smooth=True)


def roof(b):
    """One wide flat slab that overhangs the walls, with timber underneath."""
    g = "roof"
    RX, RZF, RZB = 14.0, 10.8, -10.0
    y0, y1 = RY, RY + C.ROOF_T
    xs, zs = [-RX, -W, W, RX], [RZB, -D, D, RZF]
    for z0, z1 in zip(zs, zs[1:]):
        for x0, x1 in zip(xs, xs[1:]):
            inside = abs((x0 + x1) / 2) < W and abs((z0 + z1) / 2) < D
            b.box(g, "concrete", (x0, x1), (y0, y1), (z0, z1), atlas="ext",
                  over={"+y": dict(density=0.3),
                        "-y": dict(mat="oak", atlas="upr" if inside else "ext", rot=True)})
    # a slim dark metal cap along the roof edge
    e, c = 0.03, 0.05
    b.box(g, "frame", (-RX - e, RX + e), (y1, y1 + c), (RZF - 0.25, RZF + e), solid=False, cull=False)
    b.box(g, "frame", (-RX - e, RX + e), (y1, y1 + c), (RZB - e, RZB + 0.25), solid=False, cull=False)
    b.box(g, "frame", (-RX - e, -RX + 0.25), (y1, y1 + c), (RZB + 0.25, RZF - 0.25), solid=False, cull=False)
    b.box(g, "frame", (RX - 0.25, RX + e), (y1, y1 + c), (RZB + 0.25, RZF - 0.25), solid=False, cull=False)


def blade_wall(b):
    """The dark stone wall. Built in pieces so each floor's part can be hidden
    with that floor, and so the two doorways through it stay open."""
    x = (BX0, BX1)
    zg, ze = D - T / 2, C.BLADE_Z_END      # where it passes through the front glazing, and where it ends
    cut = {"+y": dict(mat="cut")}

    def seg(group, atlas, z, y, over=cut, skip=("-y",)):
        b.box(group, "dark_stone", x, y, z, atlas=atlas, over=over, skip=skip)

    # ground floor: doorway to the study at z 5.0 to 6.2
    seg("ground", "gnd", (SZ0, 5.0), (0, H1))
    seg("ground", "gnd", (6.2, zg), (0, H1))
    seg("ground", "gnd", (5.0, 6.2), (DOOR, H1), skip=())
    seg("ground", "ext", (zg, ze), (-0.3, H1))
    # upstairs: doorway to the library at z 4.0 to 5.2
    seg("upper", "upr", (SZ0, 4.0), (F2, RY))
    seg("upper", "upr", (5.2, zg), (F2, RY))
    seg("upper", "upr", (4.0, 5.2), (F2 + DOOR, RY), skip=())
    seg("upper", "ext", (zg, ze), (H1, RY))
    # above the roof
    seg("roof", "ext", (SZ0, ze), (RY, C.BLADE_TOP), over={})


def downlight_spots(name):
    """Where a room's ceiling downlights sit, (x, z). A room that lines its ceiling
    (the living room, the library) puts fittings of its own under these."""
    _group, (x0, x1), (z0, z1), _mat = ROOMS[name]
    nx, nz = max(2, round((x1 - x0) / 2.6)), max(2, round((z1 - z0) / 2.8))
    out = []
    for i in range(nx):
        for j in range(nz):
            px, pz = x0 + (x1 - x0) * (i + 0.5) / nx, z0 + (z1 - z0) * (j + 0.5) / nz
            if name == "foyer" and SX0 - 0.2 < px < SX1 + 0.2 and pz < SZ1 + 0.2:
                continue                      # no ceiling there, it is the stairwell
            out.append((px, pz))
    return out


def downlights(b):
    """Small glowing discs in the ceilings and under the overhangs. The actual
    light comes from lamps added in lighting.py; these are just the visible fittings."""
    s = 0.07

    def spot(group, x, y, z, mat="light_warm"):
        b.quad(group, mat, [(x - s, y, z - s), (x + s, y, z - s), (x + s, y, z + s), (x - s, y, z + s)])

    for name, (group, _x, _z, _mat) in ROOMS.items():
        y, owner = (H1 - 0.004, "upper") if group == "ground" else (RY - 0.004, "roof")
        for px, pz in downlight_spots(name):
            spot(owner, px, y, pz, "light_off" if name in LIGHTS_OFF else "light_warm")
    # under the upstairs ledge along the front, and under the roof overhang
    for i in range(10):
        spot("upper", -10.8 + i * 2.4, H1 - 0.004, 8.7)
    for i in range(10):
        spot("roof", -11.7 + i * 2.6, RY - 0.004, 9.4)
