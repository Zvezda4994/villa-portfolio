"""The upstairs landing, dressed: its walls and ceiling lined (lit per vertex, so they stay
clean from a draft bake), and one large original painting on the west wall.

Plan, looking down, seen from the driveway (the games room wall at the top, so +x is
on the right):

                       games room door                                     (z = 0)
     +===( stairwell, the flight arriving at its left end )====+---[    ]---+
     | ^ arrival   |                                           |            |  d
   l | (kept clear)+---------------------- glass and brass ----+            |  a
   o |                                                                      r  r
   u [ painting ]                                                           k  k
   n |                                                                         ,
   g |                                                                     [ library
   e door                                                                     door
     |                                                                      |
     +-----[ glass to the front, sheers ]-----------------------------------+  (z = 8)

The painting hangs on the wall to the lounge between the top of the stairs and the
lounge's door, so the way up from the stairs stays clear, under its own spot. Nothing
stands on the floor. The landing has no lightmap and no stop of its own on the site;
it loads in the background like the rooms (rooms/landing.glb).
"""
import numpy as np

from . import config as C
from .house import DOOR, P
from .kit import Frame, Kit, grid, panel, wall
from .study import _smooth_noise
from .textures import picture_path, save_png

ROOM, G = "landing", "upper"
F2, H1, RY = C.F2, C.H1, C.ROOF_Y

# The landing's inside faces.
XW = -5.0 + P / 2                 # the wall to the lounge, its door from z 5.0 to 6.2 (-4.925)
XE = C.BLADE_X[0]                 # the dark stone wall, the door to the library from z 4.0 to 5.2 (1.0)
ZN = P / 2                        # the wall to the games room, its door from x -0.15 to 0.85 (0.075)
ZF = C.HALF_D - C.WALL            # the front: glass from x -4.3 (7.7)
LOUNGE_DOOR = (5.0, 6.2)
LIBRARY_DOOR = (4.0, 5.2)
GAMES_DOOR = (-0.15, 0.85)
SX0, SX1, (SZ0, SZ1) = C.STAIR_X0, C.STAIR_X1, C.STAIR_Z
LINING = 0.012

# The painting: a gallery-wrapped canvas on the lounge wall, north of the stairs' arrival.
PAINTING = dict(z=3.35, w=2.10, h=1.30, y=F2 + 1.62, d=0.04)

CEILING_LIGHT = 0.6
LAMPS = []


def build_landing(b):
    LAMPS.clear()
    paint_painting()
    k = Kit(b, G, None)                  # no lightmap: everything here is lit per vertex
    with b.room(ROOM):
        walls(k)
        ceiling(Kit(b, "roof", None))
        painting(k)


def walls(k):
    """Plaster over the lounge wall (round its door and the painting) and the games room
    wall (round its door, and down the stairwell to the foyer's ceiling), and the dark
    stone wall lined in its own granite, round the library's door."""
    e = LINING
    # the lounge wall, facing +x: from the front back to the games room wall
    l0, l1 = LOUNGE_DOOR
    pz0, pz1 = PAINTING["z"] - PAINTING["w"] / 2 - 0.005, PAINTING["z"] + PAINTING["w"] / 2 + 0.005
    py0, py1 = PAINTING["y"] - PAINTING["h"] / 2 - 0.005 - F2, PAINTING["y"] + PAINTING["h"] / 2 + 0.005 - F2
    wall(k, "plaster_v", (XW + e, F2, ZF), (0, 0, ZN - ZF), (0, RY - F2, 0), step=0.15,
         holes=[(ZF - l1, ZF - l0, 0.0, DOOR), (ZF - pz1, ZF - pz0, py0, py1)])
    # the games room wall, facing +z: from the foyer's ceiling over the stairwell, from the
    # floor elsewhere (the slab fills the rest), round the door
    g0, g1 = GAMES_DOOR
    slab = F2 - H1
    wall(k, "plaster_v", (XW, H1, ZN + e), (XE - XW, 0, 0), (0, RY - H1, 0), step=0.15,
         holes=[(0.0, SX0 - XW, 0.0, slab), (SX1 - XW, XE - XW, 0.0, slab), (g0 - XW, g1 - XW, slab, slab + DOOR)])
    # the small stretch of front wall between the lounge wall and the glass, facing -z
    panel(k, "plaster_v", (-4.3, F2, ZF - e), (XW - (-4.3), 0, 0), (0, RY - F2, 0), step=0.15)
    # the dark stone wall, facing -x, in the same granite as the foyer's side of it
    world = Frame((0.0, 0.0, 0.0))
    d0, d1 = LIBRARY_DOOR
    for z0, z1, y0, y1 in ((ZN, d0, F2, RY), (d1, ZF, F2, RY), (d0, d1, F2 + DOOR, RY)):
        k.grain("landing_stone", world, (XE - e - 0.002, y0, z0), (XE - e, y1, z1), step=0.15,
                skip=("+x", "+y", "-y", "+z", "-z"), along="z")


def ceiling(k):
    """The ceiling lined in plaster (it lifts off with the roof), with its own downlight
    fittings, and a spot on the painting."""
    from .house import downlight_spots
    y = RY - 0.014
    panel(k, "plaster_v", (XW, y, ZN), (XE - XW, 0, 0), (0, 0, ZF - ZN), step=0.25)
    s = 0.07
    for px, pz in downlight_spots(ROOM):
        k.b.quad("roof", "light_warm", [(px - s, y - 0.002, pz - s), (px + s, y - 0.002, pz - s),
                                        (px + s, y - 0.002, pz + s), (px - s, y - 0.002, pz + s)])
    pos = (XW + 1.3, y - 0.03, PAINTING["z"])
    can(k, (pos[0], y, pos[2]))
    aim = (XW + 0.05, PAINTING["y"] - 0.1, PAINTING["z"])
    LAMPS.append(dict(name="landing_painting_spot", kind="spot", pos=pos, aim=tuple(np.subtract(aim, pos)),
                      watts=40.0, cone=58.0))


def can(k, pos):
    """A small downlight set in the ceiling: a black rim round a glowing lens (as the foyer's)."""
    x, y, z = pos
    k.tube("landing_black", (x, y + 0.004, z), (x, y - 0.006, z), 0.05, segments=20, step=0.01)
    k.disc("light_warm", Frame((x, y - 0.0065, z)), (0.0, 0.0, 0.0), 0.034, 20, down=True)


def painting(k):
    """The painting (`paint_painting`), a deep gallery-wrapped canvas."""
    f = Frame((XW, 0.0, PAINTING["z"]), 90.0)      # its +z out of the wall into the room
    w, h, yc, d = PAINTING["w"], PAINTING["h"], PAINTING["y"], PAINTING["d"]
    x0, x1, y0, y1 = -w / 2, w / 2, yc - h / 2, yc + h / 2
    k.block("landing_canvas_edge", f, (x0, y0, 0.002), (x1, y1, d - 0.0005), step=0.1, skip=("-z", "+z"))
    v, fc, uv = grid((x0, y0, d), (w, 0, 0), (0, h, 0), 24, 16)
    k.mesh("landing_painting", f, v, fc, smooth=False, uvs=uv)


def paint_painting(w=512, h=316):
    """An original colour-field painting: three soft stacked fields, dusk blue over
    terracotta over a pale sand band, their edges feathered and scumbled, with a thin
    glowing seam where the blue meets the terracotta, in loose dry brushwork."""
    rng = np.random.default_rng(417)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    u, v = xx / w, yy / h                                     # v from the bottom
    ground = np.array((0.20, 0.17, 0.15))
    blue, terra, sand, seam = (np.array(c) for c in ((0.17, 0.22, 0.32), (0.62, 0.30, 0.19), (0.86, 0.78, 0.64),
                                                     (0.96, 0.70, 0.42)))
    soft = _smooth_noise((h, w), 24, rng)
    brush = _smooth_noise((h, w), 4, rng)
    img = np.broadcast_to(ground, (h, w, 3)).copy()

    def field(colour, b0, b1, inset=0.05, feather=0.025):
        """A soft-edged rectangle from height b0 to b1, set in from the sides."""
        wob = 0.008 * soft
        a = (np.clip((u - inset - wob) / feather, 0, 1) * np.clip((1 - inset - u + wob) / feather, 0, 1) *
             np.clip((v - b0 - wob) / feather, 0, 1) * np.clip((b1 - v + wob) / feather, 0, 1))
        a *= np.clip(0.9 + 0.12 * brush, 0, 1)               # dry brush: the ground shows through a little
        c = colour * (1 + 0.05 * soft + 0.03 * np.sin(u * 90 + 3 * brush))[..., None]
        return img * (1 - a[..., None]) + c * a[..., None]

    img = field(sand, 0.06, 0.24)
    img = field(terra, 0.28, 0.62)
    img = field(blue, 0.66, 0.94)
    # the seam: a narrow glow along the top of the terracotta, brightest in the middle
    glow = np.exp(-((v - 0.635) / 0.012) ** 2) * np.clip(1 - np.abs(u - 0.5) * 1.6, 0, 1) * (0.7 + 0.3 * brush)
    img = img * (1 - 0.8 * glow[..., None]) + seam * 0.8 * glow[..., None]
    save_png(picture_path("landing_painting"), np.clip(img, 0, 1).astype(np.float32))
