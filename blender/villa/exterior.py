"""Everything built outside the house: forecourt, driveway, pool and deck."""
from . import config as C

W, D = C.HALF_W, C.HALF_D
G = C.GRADE
BASE = G - 0.12          # paving slabs go a little below the sand so no gap shows

DRIVE_X = (-11.5, -6.5)
FORECOURT_X = (-13.5, 4.0)
FORECOURT_Z = (D, 19.0)


def build_exterior(b):
    forecourt(b)
    driveway(b)
    pool(b)


def forecourt(b):
    """Pale stone paving in front of the garage and the entrance, where the car
    is parked, plus a strip along the study and gym windows."""
    o = "out"
    b.box(o, "paving", FORECOURT_X, (BASE, 0), FORECOURT_Z, atlas="ext", skip=("-y",), over={"+y": dict(density=1.0)}, density=0.5)
    b.box(o, "paving", (FORECOURT_X[1], 13.2), (BASE, 0), (D, 11.6), atlas="ext", skip=("-y",), density=0.6)


def driveway(b):
    """A straight drive running away from the forecourt, with a pale kerb and
    low lights down both sides. Far stretches get coarser lightmap texels."""
    o = "out"
    x0, x1 = DRIVE_X
    z0 = FORECOURT_Z[1]
    for a, c, dens in ((z0, 46, 0.6), (46, 92, 0.22), (92, 260, 0.06)):
        b.box(o, "drive", (x0, x1), (BASE, -0.03), (a, c), atlas="ext", skip=("-y", "+x", "-x"), density=dens)
        for k0, k1 in ((x0 - 0.25, x0), (x1, x1 + 0.25)):
            b.box(o, "concrete", (k0, k1), (BASE, 0.0), (a, c), atlas="ext", skip=("-y",), density=dens)
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
