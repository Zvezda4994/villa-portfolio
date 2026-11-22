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
SRC_FONTS = ROOT / "assets_src" / "fonts"   # downloaded fonts for painted lettering
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

# Stairs: a straight flight along the back wall of the foyer. It starts on the foyer
# floor at its open east end (STAIR_X1, by the door to the dining room) and climbs west
# toward the garage wall; its last step is up onto the landing's floor, which reaches
# over the alcove at the top (west of STAIR_X0), and from there the landing opens to
# the north. The stairwell upstairs is the flight's length, STAIR_X0 to STAIR_X1.
STAIR_RISERS = 17                                          # 206 mm each
STAIR_TREAD = 0.245
STAIR_Z = (PART / 2, PART / 2 + 1.30)
STAIR_X1 = -0.23                                           # the bottom step's nose
STAIR_X0 = STAIR_X1 - STAIR_TREAD * (STAIR_RISERS - 1)     # the top, where it meets the landing (-4.15)

# Pool (water surface outline) and the deck around it.
POOL_X = (-1.5, 9.5)
POOL_Z = (-15.6, -11.0)
DECK_X = (-7.0, 14.0)
DECK_Z = (-21.6, -8.0)     # widened 2 m south for the fire-pit lounge

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
    "din": dict(size=1024, density=140.0, room="dining", ship=512),   # shipped at 512 px: no visible change, 0.8 MB less
    "pol": dict(size=1024, density=90.0, room="pool"),
    "stu": dict(size=1024, density=110.0, room="study"),
    "gam": dict(size=1024, density=110.0, room="games"),
    "kit": dict(size=1024, density=90.0, room="kitchen"),
    # (the living room and the library have none: everything in them is lit per vertex)
}

# The game on the dining table, in standard chess notation (FEN). Ruy Lopez,
# Chigorin variation, after 1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Be7 6.Re1 b5
# 7.Bb3 d6 8.c3 O-O 9.h3 Na5 10.Bc2 c5 11.d4 Qc7 12.Nbd2 cxd4 13.cxd4 Nc6 14.Nb3 a5
# 15.Be3 a4 16.Nbd2 Bd7, with White to move. Only the piece placement is used.
CHESS_FEN = "r4rk1/2qbbppp/2np1n2/1p2p3/p2PP3/4BN1P/PPBN1PP1/R2QR1K1 w - - 0 17"
# Pieces that have left the board, set down beside it: the c- and d-pawns.
CHESS_CAPTURED = "pP"

# ---- The figure at the dining table --------------------------------------------
# A model you supply, seated in the chair across the board from the visitor (see
# "Original designs only" in BUILD_BRIEF.md). The build never downloads one.
# None means no figure. To add one, put the file under assets_src/ (never
# committed) and fill this in, then run `npm run figure`:
#
# FIGURE = dict(
#     file="figures/opponent.glb",      # glTF or GLB under assets_src/, already in a seated pose
#     credit="… model by …, fan art; …", # shown word for word in the dining room panel
#     link="https://…",                  # the model's own page; the credit links to it
#     height=1.30,                       # seated: top of the head above the floor, in metres
#     turn=0,                            # extra turn in degrees, if it doesn't face the board
#     offset=(0.0, 0.0, 0.0),            # fine nudge in metres: sideways, up, toward the board
#     action=None, frame=1,              # or pose it with one of the file's own animations
#     max_triangles=60000,               # thinned to this if it's denser
# )
#
# To take it down: set FIGURE = None, run `npm run figure` (seconds, no re-bake),
# then commit and push. PROGRESS.md has the full checklist.
FIGURE = None

# ---- The mech in the living room's tank --------------------------------------------
# A downloaded model (fan art, your choice, 20 Nov 2026), posed, repainted and mossed by
# blender/villa/mech.py. The file lives under assets_src/models/ (never committed);
# mech_source.py thins it once into build/mech_source.npz. The credit is shown in the
# living room's panel (from the manifest) and listed in CREDITS.md.
# To take it down: set MECH_MODEL = None, rebuild (npm run scene, bake:draft, export),
# then commit and push. The tank keeps its stones and plants, with an empty corner.
MECH_MODEL = dict(
    file="nu_gundam/samurai_style_gundam_mecha/scene.gltf",
    credit='Mech based on "Samurai Style Gundam Mecha" by lawlietrecluze, CC BY 4.0; repainted, posed and weathered.',
    link="https://sketchfab.com/3d-models/samurai-style-gundam-mecha-298b529104e84c92a58a850c14d00525",
)

# ---- The contact card on the pool deck's side table --------------------------------
# Change these and rebuild the scene
# (npm run scene, then bake and export) to reprint the card.
CONTACT_CARD = dict(
    name="Aditya Singh",
    lines=["adityaviveksingh@icloud.com", "linkedin.com/in/aditya-singh", "github.com/Zvezda4994"],
)

# Extra typefaces for painted lettering, all SIL Open Font License, from the Google
# Fonts collection (credited in CREDITS.md): file name -> where fetch_assets.py gets it.
FONTS = {
    "Kalam-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/kalam/Kalam-Regular.ttf",
    "Kalam-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/kalam/Kalam-Bold.ttf",
    # the library's spines: a book-face serif for the cloth sets, blackletter for Heartiste
    "CrimsonText-SemiBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/crimsontext/CrimsonText-SemiBold.ttf",
    "UnifrakturMaguntia-Book.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf",
}

# Coastlines for the bedroom's world map: Natural Earth's 1:110m land, public domain
# (credited in CREDITS.md), downloaded by fetch_assets.py into assets_src/geo/.
SRC_GEO = ROOT / "assets_src" / "geo"
WORLD_LAND = dict(file="ne_110m_land.geojson",
                  url="https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson")

# Public-domain paintings hung in the rooms (credited in CREDITS.md), downloaded by
# fetch_assets.py into assets_src/art/: file name -> where it comes from.
SRC_ART = ROOT / "assets_src" / "art"
ARTWORKS = {
    # the study, over the sofa: J. M. W. Turner, The Fighting Temeraire (1839), National Gallery, London
    "fighting_temeraire.jpg": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/30/"
                              "The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg/"
                              "1920px-The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg",
}

# The living room's moodboard: your pictures go in assets_src/moodboard/ (never
# committed); `npm run moodboard` (and every scene build) shrinks them into
# web/assets/moodboard/ with a list the site picks from at random.
SRC_MOODBOARD = ROOT / "assets_src" / "moodboard"

ATLAS_PADDING = 8        # empty texels between islands
LOW_RES = 512            # size of the quick-loading preview copy of each lightmap

# Camera used for the landing shot. Matches the website's opening view.
LANDING_CAM = dict(pos=(-19.0, 5.5, 30.0), target=(-2.0, 1.8, 8.0), fov=45.0)
