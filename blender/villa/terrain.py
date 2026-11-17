"""The desert: sand around the house and a ring of rocky hills on the horizon.

The sand is one big grid whose squares are small near the house and grow toward
the edges, so detail (and lightmap texels) go where the camera looks. The hills
are a separate ring further out.
"""
import bpy
import numpy as np

from . import config as C
from .exterior import TERRAIN_HOLES, hard_surfaces
from .materials import MATS

CORE = 55.0       # the grid is evenly spaced out to this distance from the centre...
U0 = 0.62         # ...using this share of the grid, and of the lightmap
EDGE = 430.0      # half-width of the whole sand mesh
N = 221           # grid points per side


# ---- noise (plain numpy, so the same functions work anywhere) --------------
def _hash(ix, iz, seed):
    n = (ix * 374761393 + iz * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def value_noise(x, z, seed=0):
    ix, iz = np.floor(x).astype(np.int64), np.floor(z).astype(np.int64)
    fx, fz = x - ix, z - iz
    # the smoother (quintic) blend: the simpler cubic leaves faint creases that low sun picks out
    u, v = fx ** 3 * (fx * (fx * 6 - 15) + 10), fz ** 3 * (fz * (fz * 6 - 15) + 10)
    a = _hash(ix, iz, seed) * (1 - u) + _hash(ix + 1, iz, seed) * u
    c = _hash(ix, iz + 1, seed) * (1 - u) + _hash(ix + 1, iz + 1, seed) * u
    return a * (1 - v) + c * v


def fbm(x, z, octaves=4, seed=0):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total = total + amp * value_noise(x * 2 ** o, z * 2 ** o, seed + o * 17)
        norm += amp
        amp *= 0.5
    return total / norm


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ---- sand ------------------------------------------------------------------
def warp(u):
    """Grid position (-1..1) to metres: even spacing in the middle, stretching outward."""
    a = np.abs(u)
    slope = CORE / U0
    t = np.clip((a - U0) / (1 - U0), 0.0, 1.0)
    outer = CORE + slope * (a - U0) + (EDGE - CORE - slope * (1 - U0)) * t ** 3
    return np.sign(u) * np.where(a < U0, slope * a, outer)


def height(x, z):
    """Ground height. Flat round the house and along the drive, dunes further out."""
    # distance from the flat area: the block round the house, forecourt and pool...
    dx = np.maximum(np.abs(x) - 17.0, 0.0)
    dz = np.maximum(np.maximum(z - 22.0, -24.0 - z), 0.0)
    d = np.hypot(dx, dz)
    # ...and a corridor along the drive
    along = np.where((z > 20.0) & (z < 275.0), np.maximum(np.abs(x + 9.0) - 6.0, 0.0), 1e6)
    d = np.minimum(d, along)

    amp = smoothstep(3.0, 70.0, d)
    swell = (fbm(x / 170.0, z / 170.0, 3, seed=1) - 0.5) * 12.0 * smoothstep(40.0, 200.0, d)
    crest = 1.0 - np.abs(2.0 * fbm((x * 0.85 + z * 0.5) / 46.0, (z * 0.85 - x * 0.5) / 90.0, 3, seed=2) - 1.0)
    dunes = crest ** 2 * 2.6
    small = (fbm(x / 9.0, z / 9.0, 2, seed=3) - 0.5) * 0.25
    return C.GRADE + amp * (swell + dunes + small)


def _grid_mesh(name, x, y, z, uv, uv2=None, wrap=False, keep=None):
    """Make a mesh from 2D arrays of site coordinates. Returns the object (not linked)."""
    rows, cols = x.shape
    idx = np.arange(rows * cols).reshape(rows, cols)
    if wrap:
        a, bq, c, d = idx[:-1, :], idx[1:, :], np.roll(idx, -1, axis=1)[1:, :], np.roll(idx, -1, axis=1)[:-1, :]
    else:
        a, bq, c, d = idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]
    faces = np.stack([a, bq, c, d], axis=-1).reshape(-1, 4)
    if keep is not None:
        faces = faces[keep.reshape(-1)]
    verts = np.stack([x, -z, y], axis=-1).reshape(-1, 3)          # Blender axes
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    if me.polygons[0].normal.z < 0:
        me.flip_normals()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    loops = np.empty(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", loops)
    layer = me.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", uv.reshape(-1, 2)[loops].ravel())
    if uv2 is not None:
        layer2 = me.uv_layers.new(name="Lightmap")
        layer2.data.foreach_set("uv", uv2.reshape(-1, 2)[loops].ravel())
        layer.active_render = True
    me.update()
    return bpy.data.objects.new(name, me)


def build_sand(collection, materials):
    u = np.linspace(-1.0, 1.0, N)
    gx, gz = np.meshgrid(warp(u), warp(u), indexing="ij")
    gy = height(gx, gz)
    tile = MATS["sand"]["tile"]
    uv = np.stack([gx, gz], axis=-1) / tile
    size = C.ATLASES["terrain"]["size"]
    lu = 0.5 / size + (u + 1.0) / 2.0 * (1.0 - 1.0 / size)
    lm = np.stack(np.meshgrid(lu, lu, indexing="ij"), axis=-1)

    # leave a hole where the pool goes, or sand would show inside it
    x0, x1 = gx[:-1, :-1], gx[1:, 1:]
    z0, z1 = gz[:-1, :-1], gz[1:, 1:]
    keep = np.ones(x0.shape, dtype=bool)
    for (px0, px1), (pz0, pz1) in TERRAIN_HOLES:
        keep &= ~((x1 > px0) & (x0 < px1) & (z1 > pz0) & (z0 < pz1))

    ob = _grid_mesh("out__terrain", gx, gy, gz, uv, lm, keep=keep)
    ob.data.materials.append(materials["sand"])
    ob["group"], ob["lit"], ob["lightmap"] = "out", "lightmap", "terrain"
    collection.objects.link(ob)
    return ob


# ---- gravel borders -----------------------------------------------------------
MASK_SIZE = 2048


def build_mask(size=MASK_SIZE):
    """Where the sand turns to gravel: a band along every paved edge, uneven in
    width, with a few stray patches beyond it so it doesn't make a new straight line.

    The mask is laid out like the sand's lightmap (its second UV set), so the
    website can look it up with the same coordinates. Saved for Blender as a PNG;
    export_web.py turns it into KTX2 for the site. Returns the mask, bottom row first.
    """
    from .textures import mask_path, save_png

    atlas = C.ATLASES["terrain"]["size"]
    t = (np.arange(size) + 0.5) / size                       # lightmap coordinate of each texel
    xs = warp(((t - 0.5 / atlas) / (1 - 1 / atlas)) * 2 - 1)   # back to metres (see build_sand)
    X, Z = np.meshgrid(xs, xs, indexing="xy")                # columns follow x, rows follow z

    d = edge_distance(X, Z)
    width = border_width(X, Z)
    band = 1.0 - smoothstep(width - 0.12, width + 0.12, d)
    patches = smoothstep(0.60, 0.70, fbm(X / 1.3, Z / 1.3, 3, seed=12)) * (1.0 - smoothstep(width, width + 1.8, d)) * 0.85
    mask = np.clip(np.maximum(band, patches), 0.0, 1.0)

    save_png(mask_path("terrain_mask"), np.repeat(mask[..., None], 3, axis=2).astype(np.float32))
    return mask


def edge_distance(X, Z):
    """Distance in metres to the nearest paved or built surface (0 on top of one)."""
    d = np.full(np.shape(X), np.inf)
    for x0, x1, z0, z1 in hard_surfaces():
        dx = np.maximum(np.maximum(x0 - X, X - x1), 0.0)
        dz = np.maximum(np.maximum(z0 - Z, Z - z1), 0.0)
        d = np.minimum(d, np.hypot(dx, dz))
    return d


def border_width(X, Z):
    """How far the gravel reaches from an edge: 0.7 to 1.9 m, fading out along the far drive."""
    return (0.7 + 1.2 * fbm(X / 4.0, Z / 4.0, 3, seed=11)) * (1.0 - smoothstep(40.0, 80.0, Z))


# ---- hills -----------------------------------------------------------------
def build_hills(collection, materials):
    r0, r1 = 250.0, 1000.0
    rings, around = 30, 288
    t = np.linspace(0.0, 1.0, rings)
    radius = r0 + (r1 - r0) * t
    angle = np.linspace(0.0, 2 * np.pi, around, endpoint=False)
    R, A = np.meshgrid(radius, angle, indexing="ij")
    T = np.meshgrid(t, angle, indexing="ij")[0]
    x, z = R * np.cos(A), R * np.sin(A)

    profile = smoothstep(0.06, 0.45, T) * (1.0 - 0.9 * smoothstep(0.7, 1.0, T))
    mass = fbm(x / 300.0, z / 300.0, 4, seed=7)
    ridge = 1.0 - np.abs(2.0 * fbm(x / 110.0, z / 110.0, 4, seed=8) - 1.0)
    crags = 1.0 - np.abs(2.0 * fbm(x / 38.0, z / 38.0, 3, seed=9) - 1.0)
    # tallest behind the house, lower toward the sun so the sky stays open there
    behind = 0.75 + 0.45 * (-z / R * 0.9 + x / R * 0.3)
    y = -5.0 + profile * behind * (12.0 + 120.0 * mass ** 1.6 * (0.35 + 0.5 * ridge ** 1.5 + 0.15 * crags))

    uv = np.stack([x, z], axis=-1) / 40.0
    ob = _grid_mesh("out__hills", x, y, z, uv, wrap=True)
    ob.data.materials.append(materials["hill"])
    ob.data.color_attributes.new(name="Light", type="FLOAT_COLOR", domain="POINT")
    ob["group"], ob["lit"] = "out", "vertex"
    collection.objects.link(ob)
    return ob
