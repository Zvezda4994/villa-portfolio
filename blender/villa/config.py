"""Shared numbers for the villa: paths, sizes, sun position, bake settings.

Everything in the build scripts is written in "site coordinates", the same ones
the website uses: x runs left to right along the front of the house, y is up,
and z points out of the front door toward the driveway. Units are metres.
`geo.to_blender` converts to Blender's z-up axes when meshes are made.
"""
import math
from pathlib import Path

# ---- Folders ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"                      # scratch output, not committed
BLEND_FILE = BUILD / "villa.blend"
BAKE_DIR = BUILD / "bake"                   # raw lightmaps before compression
SRC_TEX = ROOT / "assets_src" / "textures"  # downloaded source textures
SRC_MODELS = ROOT / "assets_src" / "models" # downloaded source models (glTF)
ASSETS = ROOT / "web" / "assets"            # what the website loads
PREVIEWS = ROOT / "previews"

# ---- House size ------------------------------------------------------------
HALF_W = 12.0        # the footprint is 24 m wide (x from -12 to 12)
HALF_D = 8.0         # and 16 m deep (z from -8 to 8)
WALL = 0.30          # outside wall thickness
PART = 0.15          # inside partition thickness
H1 = 3.2             # ground floor, floor to ceiling
SLAB = 0.30          # thickness of the slab between floors
F2 = H1 + SLAB       # upstairs floor level (3.5)
H2 = 3.0             # upstairs, floor to ceiling
ROOF_Y = F2 + H2     # underside of the roof slab (6.5)
ROOF_T = 0.35
GRADE = -0.12        # sand level around the house; paving and floors sit at 0

# The dark stone wall that runs from the foyer out through the front of the house.
BLADE_X = (1.0, 1.5)
BLADE_Z_END = 11.0
BLADE_TOP = 7.7

# Stairs: a straight flight along the back wall of the foyer, rising toward +x.
STAIR_X0 = -4.85
STAIR_RISERS = 18
STAIR_TREAD = 0.27
STAIR_Z = (PART / 2, PART / 2 + 1.30)
STAIR_X1 = STAIR_X0 + STAIR_TREAD * (STAIR_RISERS - 1)   # where it meets the upper floor

# Pool (water surface outline) and the deck around it.
POOL_X = (-1.5, 9.5)
POOL_Z = (-15.6, -11.0)
DECK_X = (-7.0, 14.0)
DECK_Z = (-19.5, -8.0)

# ---- Sun -------------------------------------------------------------------
# Golden hour. The sun sits low and to the front left of the house, so the
# facade and the driveway are lit. This drives the lighting bake: changing it
# means re-baking everything.
SUN_ELEVATION = 15.0         # degrees above the horizon
SUN_LEFT_OF_FRONT = 58.0     # degrees round from straight-in-front toward the left


def sun_direction():
    """Unit vector pointing from the ground toward the sun, in site coordinates."""
    e = math.radians(SUN_ELEVATION)
    a = math.radians(SUN_LEFT_OF_FRONT)
    return (-math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))


# ---- Baking ----------------------------------------------------------------
# Baked light is stored as ordinary 8-bit textures, so the values are divided by
# this number first and multiplied back in the browser. Sunlit walls come out
# around 2.5, so 4 leaves headroom without wasting much precision.
LIGHT_RANGE = 4.0

# One entry per lightmap. "density" is the target texels per metre; the packer
# lowers it if everything does not fit.
ATLASES = {
    "ext": dict(size=2048, density=52.0),      # facades, roof, paving, pool
    "gnd": dict(size=2048, density=56.0),      # ground floor interior
    "upr": dict(size=2048, density=52.0),      # upstairs interior
    "terrain": dict(size=2048, density=None),  # the sand (laid out separately)
    # Furnished rooms each get their own lightmap for the big furniture surfaces,
    # loaded together with the room after the first view is up.
    "din": dict(size=1024, density=140.0, room="dining"),
}

# The game on the dining table, in standard chess notation (FEN). Ruy Lopez,
# Chigorin variation, after 1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Be7 6.Re1 b5
# 7.Bb3 d6 8.c3 O-O 9.h3 Na5 10.Bc2 c5 11.d4 Qc7 12.Nbd2 cxd4 13.cxd4 Nc6 14.Nb3 a5
# 15.Be3 a4 16.Nbd2 Bd7, with White to move. Only the piece placement is used.
CHESS_FEN = "r4rk1/2qbbppp/2np1n2/1p2p3/p2PP3/4BN1P/PPBN1PP1/R2QR1K1 w - - 0 17"
# Pieces that have left the board, set down beside it: the c- and d-pawns.
CHESS_CAPTURED = "pP"
ATLAS_PADDING = 8        # empty texels between islands
LOW_RES = 512            # size of the quick-loading preview copy of each lightmap

# Camera used for the landing shot. Matches the website's opening view.
LANDING_CAM = dict(pos=(-19.0, 5.5, 30.0), target=(-2.0, 1.8, 8.0), fov=45.0)
