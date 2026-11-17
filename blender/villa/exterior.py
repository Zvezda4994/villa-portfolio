"""Everything built outside the house: forecourt, driveway, reflecting pool, pool and deck.

The front of the house from above, driveway coming in at the bottom:

      house front (z = 8)                          blade wall
   |======== dark granite threshold ==========|##| path ------------------|
   |                                 :        |##|  reflecting pool       |
   |low    granite setts (court)     : pale   |##|________________________|
   |wall                             : slabs  |
   |........ band ...........  ......:        |kerb
         |   drive (setts)   |  [======= planter ========]
         |                   |

Paving never meets the sand directly: kerbs, the low wall, the planter or the
pool coping finish each edge, and terrain.build_mask lays gravel along them.
"""
from . import config as C

W, D = C.HALF_W, C.HALF_D
G = C.GRADE
BASE = G - 0.12          # paving slabs go a little below the sand so no gap shows

DRIVE_X = (-11.2, -6.2)            # in line with the garage door
COURT_X = (-11.65, -3.4)           # granite setts, where cars pull up
ENTRY_X = (-3.4, C.BLADE_X[0])     # large pale slabs leading to the front door
FRONT_Z = 15.6                     # how far the forecourt reaches out from the house
BAND = 0.3                         # dark granite strips between the different stones
KERB = 0.2
KERB_TOP = 0.06
WALL = dict(x=(-W, COURT_X[0]), z=(D, 15.9), h=0.6)          # carries on the line of the house's west wall
PLANTERS = [dict(x=(-5.7, C.BLADE_X[0]), z=(14.4, FRONT_Z), h=0.5, soil=0.40)]
RPOOL_X = (C.BLADE_X[1], 11.8)     # reflecting pool, between the blade wall and the house corner
RPOOL_Z = (9.15, 11.0)
COPING = 0.25

# Filled in while building, read by lighting.py: small spotlights in the ground and walls.
GROUND_LIGHTS = []

# Holes cut in the sand where something sits lower than it (terrain.py reads this).
TERRAIN_HOLES = [(C.POOL_X, C.POOL_Z)]


def hard_surfaces():
    """Everything built on the ground, as (x0, x1, z0, z1) rectangles. Used to lay
    gravel around the edges and to keep plants and rocks off the paving."""
    return [
        (-W, W, -D, D),                                                # the house
        (WALL["x"][0], C.BLADE_X[0], D, WALL["z"][1]),                 # forecourt, wall and planter
        (C.BLADE_X[0], C.BLADE_X[0] + KERB, 11.0, FRONT_Z),            # kerb beside the entrance
        (C.BLADE_X[0], W + 0.2, D, RPOOL_Z[1] + COPING),               # reflecting pool and its path
        (DRIVE_X[0] - KERB, DRIVE_X[1] + KERB, FRONT_Z, 260.0),        # the drive and its kerbs
        (C.DECK_X[0], C.DECK_X[1], C.DECK_Z[0], C.DECK_Z[1]),          # pool deck at the back
    ]


def build_exterior(b):
    GROUND_LIGHTS.clear()
    forecourt(b)
    low_wall(b)
    for p in PLANTERS:
        planter(b, p)
    reflecting_pool(b)
    driveway(b)
    pool(b)


def uplight(b, x, z, aim, watts=30.0, y=0.0):
    """A small square fitting set into the ground, and a spotlight for the bake."""
    o = "out"
    s, r = 0.06, 0.09
    b.quad(o, "frame", [(x - r, y + 0.002, z + r), (x + r, y + 0.002, z + r), (x + r, y + 0.002, z - r), (x - r, y + 0.002, z - r)])
    b.quad(o, "light_warm", [(x - s, y + 0.004, z + s), (x + s, y + 0.004, z + s), (x + s, y + 0.004, z - s), (x - s, y + 0.004, z - s)])
    GROUND_LIGHTS.append(dict(pos=(x, y + 0.05, z), aim=aim, watts=watts, cone=55.0))


def forecourt(b):
    o = "out"
    x0, x1 = COURT_X[0], ENTRY_X[1]
    z0, z1 = D, FRONT_Z
    # The slab underneath: only its sides show, a hand's width above the sand.
    b.box(o, "concrete", (x0, x1), (BASE, -0.002), (z0, z1), atlas="ext", skip=("+y", "-y"), density=0.5)

    # Dark granite threshold along the house, then setts and slabs, with granite
    # bands wherever one stone meets another.
    b.floor(o, "dark_stone", "ext", (x0, x1), (z0, z0 + BAND), 0.0)
    b.floor(o, "dark_stone", "ext", (x0, x0 + BAND), (z0 + BAND, z1), 0.0)                       # along the low wall
    b.floor(o, "dark_stone", "ext", (x0 + BAND, ENTRY_X[0] - BAND), (z1 - BAND, z1), 0.0)         # across the mouth of the drive
    b.floor(o, "dark_stone", "ext", (ENTRY_X[0] - BAND, ENTRY_X[0]), (z0 + BAND, z1), 0.0)        # between setts and slabs
    b.floor(o, "setts", "ext", (x0 + BAND, ENTRY_X[0] - BAND), (z0 + BAND, z1 - BAND), 0.0, density=0.8)
    b.floor(o, "slabs", "ext", (ENTRY_X[0], x1), (z0 + BAND, z1), 0.0, density=0.9)
    # kerb on the open side of the entrance, beyond the end of the blade wall
    b.box(o, "concrete", (x1, x1 + KERB), (BASE, KERB_TOP), (11.0, z1), atlas="ext", skip=("-y",))

    # Uplights washing the stone piers and the dark wall.
    uplight(b, -11.45, D + 0.45, aim=(0.0, 1.0, -0.22), watts=35)
    uplight(b, -5.05, D + 0.45, aim=(0.0, 1.0, -0.22), watts=35)
    for z in (9.3, 10.6):
        uplight(b, C.BLADE_X[0] - 0.22, z, aim=(0.25, 1.0, 0.0), watts=35)
    # and two on the entrance side of the planter
    for x in (-2.4, -0.4):
        uplight(b, x, PLANTERS[0]["z"][0] - 0.3, aim=(0.0, 1.0, 0.35), watts=20)


def low_wall(b):
    """A low stone wall carrying the line of the house's west wall out to the drive."""
    o = "out"
    (x0, x1), (z0, z1), h = WALL["x"], WALL["z"], WALL["h"]
    b.box(o, "stone", (x0, x1), (BASE, h - 0.06), (z0, z1), atlas="ext", skip=("-y",))
    b.box(o, "concrete", (x0 - 0.03, x1 + 0.03), (h - 0.06, h), (z0, z1 + 0.03), atlas="ext", skip=("-y",), solid=False)
    # step lights in its inner face
    for z in (10.0, 12.6, 15.0):
        y, w, t = 0.2, 0.11, 0.025
        b.quad(o, "frame", [(x1 + 0.002, y - t - 0.02, z + w + 0.02), (x1 + 0.002, y - t - 0.02, z - w - 0.02),
                            (x1 + 0.002, y + t + 0.02, z - w - 0.02), (x1 + 0.002, y + t + 0.02, z + w + 0.02)])
        b.quad(o, "light_warm", [(x1 + 0.004, y - t, z + w), (x1 + 0.004, y - t, z - w),
                                 (x1 + 0.004, y + t, z - w), (x1 + 0.004, y + t, z + w)])
        GROUND_LIGHTS.append(dict(pos=(x1 + 0.05, y, z), aim=(1.0, -0.7, 0.0), watts=8.0, cone=110.0))


def planter(b, p):
    """A raised stone planter with a pebble mulch top. Plants go in from plants.py."""
    o = "out"
    (x0, x1), (z0, z1), h, soil = p["x"], p["z"], p["h"], p["soil"]
    rim = 0.18
    b.box(o, "stone", (x0, x1), (BASE, soil), (z0, z1), atlas="ext", skip=("-y",), over={"+y": dict(mat="mulch")})
    for bx, bz in (((x0, x1), (z0, z0 + rim)), ((x0, x1), (z1 - rim, z1)),
                   ((x0, x0 + rim), (z0 + rim, z1 - rim)), ((x1 - rim, x1), (z0 + rim, z1 - rim))):
        b.box(o, "stone", bx, (soil, h), bz, atlas="ext", skip=("-y",), over={"+y": dict(mat="concrete")}, density=0.8)
    for x in (x0 + 1.4, (x0 + x1) / 2, x1 - 1.4):
        uplight(b, x, (z0 + z1) / 2, aim=(0.0, 1.0, 0.0), watts=15, y=soil)


def reflecting_pool(b):
    """A shallow, dark, still pool in front of the study and gym, with the blade wall
    rising out of its end. A narrow path runs between it and the glass. It is only
    a few centimetres deep, like a real water mirror, so the sand stays below it."""
    o = "out"
    (rx0, rx1), (rz0, rz1) = RPOOL_X, RPOOL_Z
    floor_y, water_y, top = -0.08, -0.02, 0.04
    # path along the house
    b.box(o, "slabs", (rx0, W + 0.2), (BASE, 0.0), (D, rz0 - COPING), atlas="ext", skip=("-y", "-x"), density=0.9)
    # coping on the three open sides (the fourth is the blade wall); the basin lining covers their inner faces
    b.box(o, "dark_stone", (rx0, rx1 + COPING), (BASE, top), (rz0 - COPING, rz0), atlas="ext", skip=("-y", "+z"))
    b.box(o, "dark_stone", (C.BLADE_X[0], rx1 + COPING), (BASE, top), (rz1, rz1 + COPING), atlas="ext", skip=("-y", "-z"))
    b.box(o, "dark_stone", (rx1, rx1 + COPING), (BASE, top), (rz0, rz1), atlas="ext", skip=("-y", "-x"))
    # the basin, lined in the same dark stone, facing inward
    t = dict(atlas="ext", density=0.6)
    b.floor(o, "dark_stone", "ext", (rx0, rx1), (rz0, rz1), floor_y, density=0.6)
    b.quad(o, "dark_stone", [(rx0, floor_y, rz0), (rx1, floor_y, rz0), (rx1, top, rz0), (rx0, top, rz0)], **t)   # looks +z
    b.quad(o, "dark_stone", [(rx1, floor_y, rz1), (rx0, floor_y, rz1), (rx0, top, rz1), (rx1, top, rz1)], **t)   # looks -z
    b.quad(o, "dark_stone", [(rx1, floor_y, rz0), (rx1, floor_y, rz1), (rx1, top, rz1), (rx1, top, rz0)], **t)   # looks -x
    b.quad(o, "water_front", [(rx0, water_y, rz1), (rx1, water_y, rz1), (rx1, water_y, rz0), (rx0, water_y, rz0)])


def driveway(b):
    """A straight drive of granite setts with raised kerbs and low lights down both
    sides. Far stretches get coarser lightmap texels."""
    o = "out"
    x0, x1 = DRIVE_X
    z0 = FRONT_Z
    for a, c, dens in ((z0, 46, 0.6), (46, 92, 0.22), (92, 260, 0.06)):
        b.box(o, "setts", (x0, x1), (BASE, 0.0), (a, c), atlas="ext", skip=("-y", "+x", "-x"), density=dens)
        for k0, k1 in ((x0 - KERB, x0), (x1, x1 + KERB)):
            b.box(o, "concrete", (k0, k1), (BASE, KERB_TOP), (a, c), atlas="ext", skip=("-y",), density=dens)
    for i in range(9):
        z = z0 + 3.0 + i * 8.0
        for x in (x0 - 0.75, x1 + 0.75):
            bollard(b, x, z)


def bollard(b, x, z):
    o = "out"
    b.box(o, "frame", (x - 0.05, x + 0.05), (G - 0.05, 0.42), (z - 0.05, z + 0.05), solid=False, cull=False)
    b.box(o, "light_warm", (x - 0.055, x + 0.055), (0.42, 0.50), (z - 0.055, z + 0.055), solid=False, cull=False, skip=("-y",))
    b.box(o, "frame", (x - 0.065, x + 0.065), (0.50, 0.53), (z - 0.065, z + 0.065), solid=False, cull=False)


def pool(b):
    o = "out"
    px0, px1 = C.POOL_X
    pz0, pz1 = C.POOL_Z
    dx0, dx1 = C.DECK_X
    dz0, dz1 = C.DECK_Z
    depth = -1.45

    # the deck, in four pieces round the pool
    for x, z in (((dx0, px0), (dz0, dz1)), ((px1, dx1), (dz0, dz1)), ((px0, px1), (dz0, pz0)), ((px0, px1), (pz1, dz1))):
        b.box(o, "paving", x, (BASE, 0), z, atlas="ext", skip=("-y",), density=0.9)

    # the basin, tiled, facing inward
    t = dict(atlas="ext", density=0.8)
    b.floor(o, "pool_tile", "ext", (px0, px1), (pz0, pz1), depth, density=0.8)
    b.quad(o, "pool_tile", [(px0, depth, pz0), (px1, depth, pz0), (px1, BASE, pz0), (px0, BASE, pz0)], **t)   # looks +z
    b.quad(o, "pool_tile", [(px1, depth, pz1), (px0, depth, pz1), (px0, BASE, pz1), (px1, BASE, pz1)], **t)   # looks -z
    b.quad(o, "pool_tile", [(px0, depth, pz1), (px0, depth, pz0), (px0, BASE, pz0), (px0, BASE, pz1)], **t)   # looks +x
    b.quad(o, "pool_tile", [(px1, depth, pz0), (px1, depth, pz1), (px1, BASE, pz1), (px1, BASE, pz0)], **t)   # looks -x
    # wide steps down at the left end
    for k, (run, top) in enumerate(((1.35, -1.10), (0.90, -0.75), (0.45, -0.40))):
        b.box(o, "pool_tile", (px0, px0 + run), (depth, top), (pz0, pz1), atlas="ext", density=0.8,
              skip=("-x", "-y", "+z", "-z"), solid=False, cull=False)

    # underwater light fittings on the house side (the lamps themselves are in lighting.py)
    for i in range(4):
        x = px0 + (px1 - px0) * (i + 0.5) / 4
        b.quad(o, "light_pool", [(x + 0.12, -0.97, pz1 - 0.01), (x - 0.12, -0.97, pz1 - 0.01),
                                 (x - 0.12, -0.73, pz1 - 0.01), (x + 0.12, -0.73, pz1 - 0.01)])

    # the water surface
    y = -0.08
    b.quad(o, "water", [(px0, y, pz1), (px1, y, pz1), (px1, y, pz0), (px0, y, pz0)])
