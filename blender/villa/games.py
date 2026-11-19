"""The games room (CS2 and the pick'em model), furnished: a strict black and
white setup in a dark room lit by its screens.

Plan, looking down, seen from the driveway (the window onto the pool at the
bottom, so +x is on the right):

         wall to the landing (z = 0), door  [  ]
     +-----------------------------------------------+
     |  [shelf]                                      |
   b |  [ ===    (o) chair                     sofa  | door to the
   e |  [desk]  ===mousepad===                facing | trophy room
   d |  [ ===    PC                           the    |
   r |                                        setup  |
     |                 [ blind over the window ]     |
     +-----------------------------------------------+

A white desk against the bedroom wall, kept clear: the 32" OLED and a second
monitor float on a white dual arm. A white keyboard and mouse on a black desk
mat, a minimal white PC with a glass side and no cables showing, a black task
chair on a charcoal rug, and a small white shelf with five game cases, titles
in plain type on plain black or white spines. The main screen shows a quiet
black wallpaper; the second shows a win-probability chart for two placeholder
teams. A blackout blind is down over the window, the ceiling lights are off,
and a charcoal sofa across the room faces the setup.

The rug and the desk's ends are on the room's own lightmap ("gam"); everything
else is lit per vertex, the desk top, shelf and mat on fine grids so the
screens' glow falls smoothly across them. Light comes from lamps set in front of the screens,
a bias light behind the main monitor and a glow inside the PC.
"""
import math

import numpy as np

from . import config as C
from .house import F2, P
from .kit import Frame, Kit
from .study import book_flat, sofa, task_chair
from .textures import picture_path, save_png

ROOM, G, ATLAS = "games", "upper", "gam"

XW = -5.0 + P / 2               # the wall to the bedroom (-4.925)
XE = 4.0 - P / 2                # the wall to the trophy room (3.925)
ZB = -C.HALF_D + C.WALL         # inside face of the back wall (-7.7)
SETUP_Z = -4.10                 # the middle of the desk, along the bedroom wall

DESK = dict(x=(-0.80, 1.00), depth=0.80, top=0.74, t=0.025)     # in the setup's frame
MAIN = dict(x=0.0, y=1.08, z=0.30, w=0.715, h=0.405)            # 32" 16:9
SIDE = dict(x=0.66, y=1.07, z=0.37, w=0.600, h=0.340, turn=-30.0)
SOFA_X = 0.20                    # the back of the sofa across the room, facing the setup
SHELF = dict(x=(-0.62, -0.24), y=1.56, depth=0.16)      # above the main screen, in its glow
GAMES = ["Yakuza 0", "Hotline Miami", "S.T.A.L.K.E.R.", "Titanfall 2", "Metro Exodus"]
SPINES = ["white"] * 5               # white spines, black titles, so all five read in the dark
TEAMS = ("Team Alpha", "Team Bravo")       # placeholders on the chart

CEILING_LIGHT = 0.45
CEILING_COLOUR = (0.85, 0.90, 1.0)     # a faint cool fill, so the whites stay white
SCREEN_LIGHT = (0.82, 0.88, 1.0)
LAMPS = []


def setup_frame():
    """The setup's own frame: origin on the bedroom wall at the desk's middle, +z into
    the room, +x to the sitter's right (toward the window)."""
    return Frame((XW, F2, SETUP_Z), 90.0)


def _cam(pos, target, fov):
    f = setup_frame()
    return dict(pos=tuple(round(float(v), 3) for v in f(pos)), target=tuple(round(float(v), 3) for v in f(target)), fov=fov)


# Review cameras. The first is also the room's view on the website: behind the chair,
# a little to the left, looking at the screens.
GAMES_CAM = _cam((-2.0, 1.62, 6.55), (0.55, 0.92, 0.60), 46.0)    # from behind the sofa, across the room
DESK_CAM = _cam((-1.35, 1.45, 2.95), (0.20, 1.10, 0.20), 55.0)     # closer, behind the chair
SHELF_CAM = _cam((-0.30, 1.48, 0.95), (-0.43, 1.60, 0.08), 36.0)


def build_games(b):
    LAMPS.clear()
    paint_pictures()
    k = Kit(b, G, ATLAS)
    f = setup_frame()
    with b.room(ROOM):
        rug(k, f)
        desk(k, f)
        monitors(k, f)
        desk_mat(k, f)
        keyboard(k, Frame(f((-0.04, DESK["top"] + 0.004, 0.56)), f.yaw + 1.5))
        mouse(k, Frame(f((0.40, DESK["top"] + 0.004, 0.57)), f.yaw - 6))
        pc(k, f)
        task_chair(k, Frame(f((0.22, 0.0, 1.15)), f.yaw + 180 + 32), seat="chair_white", shell="chair_white_shell",
                   metal="aluminium")
        shelf(k, f)
        led_glow(k, f)
        acoustic_panels(k, f)
        framed_print(k, f)
        plant(k, f)
        sofa(k, Frame((SOFA_X, F2, SETUP_Z + 0.05), -90.0), L=2.4, fabric="sofa_boucle",
             pillows=("cushion_black", "cushion_white"), throw=None)
        coffee_table(k)
        blind(k)
        walls(k, Kit(b, "roof", ATLAS))


# ---- the setup ------------------------------------------------------------------------------
def rug(k, f):
    """A charcoal rug under the desk and chair, with a fine white line set in from its edge."""
    x0, x1, z0, z1 = -1.25, 1.45, 0.08, 2.45
    k.box("rug_charcoal", f, (x0, 0.0, z0), (x1, 0.010, z1), skip=("-y",), density=0.5)
    i = 0.09
    k.box("rug_line", f, (x0 + i, 0.010, z0 + i), (x1 - i, 0.0105, z1 - i), skip=("-y",), density=0.3)
    i += 0.012
    k.box("rug_charcoal", f, (x0 + i, 0.0105, z0 + i), (x1 - i, 0.011, z1 - i), skip=("-y",), density=0.5)


def desk(k, f):
    """A white desk: a thin top on two white slab ends and a modesty panel."""
    (x0, x1), d, top, t = DESK["x"], DESK["depth"], DESK["top"], DESK["t"]
    z0, z1 = 0.02, 0.02 + d
    k.slab("white_v", f, (x0, top - t, z0), (x1, top, z1), step=0.05)
    for x in (x0 + 0.03, x1 - 0.06):
        k.box("white_v", f, (x, 0.0, z0 + 0.04), (x + 0.03, top - t, z1 - 0.06), skip=("-y",))
    k.box("white_v", f, (x0 + 0.06, 0.30, z0 + 0.05), (x1 - 0.06, top - t, z0 + 0.065))


def monitors(k, f):
    """The 32" OLED in the middle and a second monitor turned in on the right, both on
    one white dual arm clamped to the back of the desk."""
    top = DESK["top"]
    pole = (0.30, top, 0.08)
    arm_y = top + 0.125                                  # the arms run just under the screens' bottom edges
    k.soft("white_v", f, (pole[0], top + 0.012, pole[2]), (0.075, 0.024, 0.10), 0.006, n=1)          # clamp
    k.tube("white_v", f((pole[0], top, pole[2])), f((pole[0], arm_y + 0.03, pole[2])), 0.018, segments=16)
    k.lathe("white_v", Frame(f((pole[0], arm_y + 0.03, pole[2]))), [(0.0, 0.0), (0.02, 0.0), (0.02, 0.012), (0.0, 0.012)], 16)
    main = Frame(f((MAIN["x"], MAIN["y"], MAIN["z"])), f.yaw)
    side = Frame(f((SIDE["x"], SIDE["y"], SIDE["z"])), f.yaw + SIDE["turn"])
    for m, spec, picture in ((main, MAIN, "screen_main"), (side, SIDE, "screen_chart")):
        w, h = spec["w"], spec["h"]
        k.soft("monitor_black", m, (0, 0, -0.0035), (w, h, 0.007), 0.002, n=1)            # the panel
        k.soft("monitor_black", m, (0, -0.02, -0.025), (w * 0.62, h * 0.55, 0.036), 0.012, n=2)   # its back
        k.soft("white_v", m, (0, -0.02, -0.048), (0.11, 0.11, 0.012), 0.003, n=1)          # the arm's plate
        a = 0.004
        k.quad(picture, m, [(-w / 2 + a, -h / 2 + a + 0.006, 0.0005), (w / 2 - a, -h / 2 + a + 0.006, 0.0005),
                            (w / 2 - a, h / 2 - a, 0.0005), (-w / 2 + a, h / 2 - a, 0.0005)],
               uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # each arm: two white segments with round joints, out from the pole under its screen,
    # then a short riser up behind the screen to its plate
    hub = np.array(f((pole[0], arm_y, pole[2])))
    for m, bend in ((main, (0.12, 0.17)), (side, (0.52, 0.12))):
        plate = np.array(m((0, -0.02, -0.056)))
        foot = np.array(m((0, -0.02, -0.07)))
        foot[1] = hub[1]                                 # world height of arm_y (hub is already in world space)
        elbow = np.array(f((bend[0], arm_y, bend[1])))
        for a, c in ((hub, elbow), (elbow, foot)):
            k.tube("white_v", tuple(a), tuple(c), 0.016, segments=14)
        for j in (elbow, foot):
            k.lathe("white_v", Frame(tuple(j + (0, -0.022, 0))), [(0.0, 0.0), (0.021, 0.0), (0.021, 0.044), (0.0, 0.044)], 16)
        k.tube("white_v", tuple(foot), tuple(plate + (0, -0.03, 0)), 0.013, segments=12)
        k.tube("white_v", tuple(plate + (0, -0.03, 0)), tuple(plate), 0.013, segments=12)
    # a slim light bar clipped to the top of the main screen, washing the desk
    bh = MAIN["h"] / 2
    k.tube("metal_black", main((-0.24, bh + 0.016, 0.035)), main((0.24, bh + 0.016, 0.035)), 0.012, segments=14)
    k.soft("metal_black", main, (0, bh + 0.008, -0.012), (0.05, 0.03, 0.05), 0.006, n=1)
    k.quad("led_white", main, [(-0.23, bh + 0.0045, 0.045), (0.23, bh + 0.0045, 0.045), (0.23, bh + 0.0045, 0.03),
                               (-0.23, bh + 0.0045, 0.03)])
    LAMPS.append(dict(name="light_bar", pos=main((0, bh, 0.05)), size=(0.44, 0.02), watts=7.0,
                      aim=tuple(np.subtract(main((0, -0.75, 0.6)), main((0, 0, 0)))), colour=SCREEN_LIGHT))
    # light from the screens, and the bias light glowing on the wall behind the main one
    for m, spec, watts in ((main, MAIN, 11.0), (side, SIDE, 6.0)):
        LAMPS.append(dict(name=f"screen_{len(LAMPS)}", pos=m((0, 0, 0.012)), size=(spec["w"] * 0.95, spec["h"] * 0.95),
                          watts=watts, aim=tuple(np.subtract(m((0, 0, 1)), m((0, 0, 0)))), colour=SCREEN_LIGHT))
    LAMPS.append(dict(name="bias_light", pos=main((0, -0.02, -0.05)), size=(0.42, 0.20), watts=18.0,
                      aim=tuple(np.subtract(f((0, 0, -1)), f((0, 0, 0)))), colour=(0.86, 0.90, 1.0)))


def desk_mat(k, f):
    top = DESK["top"]
    k.slab("desk_mat", f, (-0.36, top, 0.38), (0.58, top + 0.004, 0.78), step=0.05, skip=("-y",))


def keyboard(k, f):
    """A white 75% keyboard: an aluminium-look case and blank white keycaps."""
    u = 0.0190
    rows = [[1] * 16, [1] * 14 + [2], [1.5] + [1] * 13 + [1.5], [1.75] + [1] * 12 + [2.25],
            [2.25] + [1] * 10 + [1.75, 1], [1.25, 1.25, 1.25, 6.25, 1, 1, 1, 1, 1]]
    width = 16 * u
    depth = len(rows) * u
    k.soft("white_v", f, (0, 0.011, 0), (width + 0.016, 0.022, depth + 0.016), 0.005, n=2)
    for r, row in enumerate(rows):
        z = -depth / 2 + (r + 0.5) * u                    # the top row furthest from the sitter (-z here is the far side)
        x = -width / 2
        for w in row:
            k.soft("keycap", f, (x + w * u / 2, 0.026, z), (w * u - 0.0026, 0.009, u - 0.0026), 0.0025, n=1)
            x += w * u


def mouse(k, f):
    k.soft("white_v", f, (0, 0.019, 0), (0.062, 0.038, 0.12), 0.026, n=3)
    k.soft("keycap", f, (0, 0.035, -0.035), (0.003, 0.006, 0.05), 0.001, n=1)


def fan(k, centre, axis, r=0.06, glow=True):
    """A 120 mm case fan: a white frame ring, seven swept blades round a hub, and a
    soft white glow ring inside the frame. `axis` is the way the air goes."""
    from .kit import axes
    c = np.asarray(centre, float)
    M = axes(axis, (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0))
    w = lambda p: tuple(c + M @ np.asarray(p, float))                                  # noqa: E731
    seg = 28
    # the frame: a square plate with a round opening, as a ring of quads
    verts, faces = [], []
    for i in range(seg):
        a0, a1 = 2 * np.pi * i / seg, 2 * np.pi * (i + 1) / seg
        for zz, flip in ((0.0125, False), (-0.0125, True)):
            inner = [(r * 0.92 * np.cos(a), r * 0.92 * np.sin(a), zz) for a in (a0, a1)]
            outer = []
            for a in (a0, a1):
                d = max(abs(np.cos(a)), abs(np.sin(a)))
                outer.append((r * np.cos(a) / d, r * np.sin(a) / d, zz))
            q = [inner[0], inner[1], outer[1], outer[0]]
            n = len(verts)
            verts += [w(v) for v in q]
            faces.append((n, n + 3, n + 2, n + 1) if not flip else (n, n + 1, n + 2, n + 3))
        # the opening's wall
        n = len(verts)
        verts += [w((r * 0.92 * np.cos(a), r * 0.92 * np.sin(a), zz)) for a in (a0, a1) for zz in (-0.0125, 0.0125)]
        faces.append((n, n + 1, n + 3, n + 2))
    k.b.mesh(k.g, "white_v", verts, faces, smooth=False)
    # hub and blades
    k.tube("white_v", w((0, 0, -0.012)), w((0, 0, 0.012)), r * 0.30, segments=20)
    verts, faces = [], []
    for b in range(7):
        a = 2 * np.pi * b / 7
        n = len(verts)
        for rr in (r * 0.30, r * 0.88):
            sweep = 0.35 * (rr / r)
            for side in (-1, 1):
                aa = a + side * 0.22 + sweep
                verts.append(w((rr * np.cos(aa), rr * np.sin(aa), side * 0.006)))
        faces.append((n, n + 1, n + 3, n + 2))
        faces.append((n, n + 2, n + 3, n + 1))
    k.b.mesh(k.g, "fan_blade", verts, faces, smooth=False)
    if glow:
        verts, faces = [], []
        for i in range(seg):
            a0, a1 = 2 * np.pi * i / seg, 2 * np.pi * (i + 1) / seg
            n = len(verts)
            verts += [w((rr * np.cos(a), rr * np.sin(a), 0.0126)) for a in (a0, a1) for rr in (r * 0.89, r * 0.93)]
            faces.append((n, n + 1, n + 3, n + 2))
            faces.append((n, n + 2, n + 3, n + 1))
        k.b.mesh(k.g, "led_white", verts, faces, smooth=False)


def pc(k, f):
    """A white showcase PC on a low white plinth beside the desk: glass front and
    glass side meeting at a pillarless corner, a white board with its pump, RAM and
    heatsinks, a long white graphics card, three fans glowing on the floor of the
    case, three more under the roof on the radiator, and one at the back. No cables."""
    # local x along the case's depth (front at -x), +z its glass side, y up
    c = Frame(f((DESK["x"][0] - 0.45, 0.0, 0.42)), f.yaw + 40)
    L, H, Wd, t = 0.46, 0.50, 0.30, 0.012
    base = 0.22
    k.box("white_v", c, (-L / 2 - 0.05, 0.0, -Wd / 2 - 0.05), (L / 2 + 0.05, base, Wd / 2 + 0.05))      # the plinth
    y0, y1 = base + 0.015, base + 0.015 + H
    for x in (-L / 2 + 0.04, L / 2 - 0.04):
        for z in (-Wd / 2 + 0.03, Wd / 2 - 0.03):
            k.soft("metal_black", c, (x, base + 0.0075, z), (0.05, 0.015, 0.04), 0.004, n=1)
    zb, zg = -Wd / 2, Wd / 2                       # back (board side) and glass side
    xf, xr = -L / 2, L / 2                         # front (glass) and rear
    k.box("white_v", c, (xf, y0, zb), (xr, y1, zb + t))                       # motherboard tray
    k.box("white_v", c, (xf, y0, zb), (xr, y0 + t, zg))                       # floor
    k.box("white_v", c, (xf, y1 - t, zb), (xr, y1, zg))                       # roof
    k.box("white_v", c, (xr - t, y0, zb), (xr, y1, zg))                       # rear panel
    k.box("white_v", c, (xf, y1 - 0.03, zg - 0.012), (xr, y1, zg))            # the top rail the glass hangs from
    inner = zb + t
    # the board: a white cover with darker details
    k.box("board_white", c, (-0.10, y0 + 0.10, inner), (0.20, y1 - 0.05, inner + 0.006))
    for (x0_, y0_, x1_, y1_) in ((0.12, y1 - 0.13, 0.19, y1 - 0.06), (-0.08, y1 - 0.12, -0.01, y1 - 0.06), (0.10, y0 + 0.13, 0.19, y0 + 0.17)):
        k.box("metal_black", c, (x0_, y0_, inner + 0.006), (x1_, y1_, inner + 0.02))          # heatsinks
    for i in range(4):                                                                         # RAM
        x = 0.085 + i * 0.011
        k.soft("white_v", c, (x, y1 - 0.20, inner + 0.03), (0.007, 0.13, 0.04), 0.002, n=1)
        k.quad("led_white", c, [(x - 0.0035, y1 - 0.135, inner + 0.01), (x + 0.0035, y1 - 0.135, inner + 0.01),
                                (x + 0.0035, y1 - 0.135, inner + 0.05), (x - 0.0035, y1 - 0.135, inner + 0.05)][::-1])
    # the CPU pump: a white cylinder with a glowing ring on its face
    pump = (0.02, y1 - 0.19, inner + 0.006)
    k.tube("white_v", c(pump), c((pump[0], pump[1], pump[2] + 0.04)), 0.036, segments=28)
    ring = Frame(c((pump[0], pump[1], pump[2] + 0.0405)), c.yaw)
    k.quad("led_white", ring, [(-0.026, -0.026, 0), (0.026, -0.026, 0), (0.026, 0.026, 0), (-0.026, 0.026, 0)])
    k.tube("white_v", c((pump[0] + 0.03, pump[1] + 0.02, pump[2] + 0.02)), c((0.12, y1 - 0.045, inner + 0.10)), 0.008, segments=10)
    k.tube("white_v", c((pump[0] + 0.03, pump[1] - 0.02, pump[2] + 0.02)), c((0.16, y1 - 0.045, inner + 0.10)), 0.008, segments=10)
    # the graphics card: a long white shroud with a black stripe and a light along its edge
    gy = y0 + 0.17
    k.soft("white_v", c, (-0.03, gy, inner + 0.075), (0.31, 0.06, 0.14), 0.008, n=2)
    k.soft("metal_black", c, (-0.03, gy - 0.031, inner + 0.075), (0.30, 0.004, 0.13), 0.001, n=1)
    k.quad("led_white", c, [(-0.18, gy - 0.006, inner + 0.1455), (0.12, gy - 0.006, inner + 0.1455),
                            (0.12, gy + 0.006, inner + 0.1455), (-0.18, gy + 0.006, inner + 0.1455)])
    # fans: three on the floor blowing up, three on the radiator under the roof, one at the back
    for i in range(3):
        x = -L / 2 + 0.08 + i * 0.125
        fan(k, c((x, y0 + t + 0.0125, 0.03)), np.subtract(c((0, 1, 0)), c((0, 0, 0))), r=0.058)
        fan(k, c((x, y1 - 0.045, 0.02)), np.subtract(c((0, 1, 0)), c((0, 0, 0))), r=0.058)
    k.box("white_v", c, (-L / 2 + 0.02, y1 - 0.033, -0.05), (L / 2 - 0.08, y1 - 0.031, 0.09))   # radiator edge
    fan(k, c((xr - t - 0.0125, y1 - 0.15, -0.02)), np.subtract(c((1, 0, 0)), c((0, 0, 0))), r=0.058)
    # the glass front and the glass side
    k.quad("pc_glass", c, [(xf, y0, zg), (xf, y0, zb), (xf, y1, zb), (xf, y1, zg)])
    k.quad("pc_glass", c, [(xf, y0, zg), (xr, y0, zg), (xr, y1, zg), (xf, y1, zg)])
    LAMPS.append(dict(name="pc_glow", kind="point", pos=c((0.0, y0 + 0.28, 0.02)), watts=6.0, radius=0.10,
                      colour=(0.9, 0.93, 1.0)))


def shelf(k, f):
    """A small white floating shelf with the five game cases, spines out, between a
    black sphere and a black bookend."""
    (x0, x1), y, d = SHELF["x"], SHELF["y"], SHELF["depth"]
    k.slab("white_v", f, (x0, y - 0.03, 0.0), (x1, y, d), step=0.04)
    t, H, D = 0.014, 0.170, 0.135
    x = x0 + 0.105
    n = len(GAMES)
    for i, colour in enumerate(SPINES):
        strip = [(i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 1), (i / n, 1)]
        k.box(f"case_{colour}", f, (x + 0.0006, y, d - 0.008 - D), (x + t - 0.0006, y + H, d - 0.008),
              over={"+z": dict(mat="game_spines", uv=strip)})
        x += t
    k.soft("metal_black", f, (x + 0.003, y + 0.07, d - 0.008 - D / 2), (0.006, 0.14, 0.11), 0.002, n=1)
    k.soft("metal_black", f, (x + 0.035, y + 0.003, d - 0.008 - D / 2), (0.07, 0.006, 0.11), 0.002, n=1)
    k.lathe("metal_black", Frame(f((x0 + 0.045, y, d / 2))),
            [(0.0, 0.0)] + [(0.035 * math.sin(math.pi * s), 0.035 - 0.035 * math.cos(math.pi * s)) for s in np.linspace(0.06, 1, 12)], 24)


def coffee_table(k):
    """A low round table in black stone in front of the sofa, with two books and a
    white controller-shaped tray left on it."""
    x, z = SOFA_X - 0.95 - 0.55, SETUP_Z + 0.05
    t = Frame((x, F2, z))
    k.lathe("metal_black", t, [(0.0, 0.0), (0.18, 0.0), (0.18, 0.012), (0.12, 0.02), (0.12, 0.30), (0.40, 0.30),
                               (0.42, 0.32), (0.42, 0.345), (0.40, 0.36), (0.0, 0.36)], 48)
    book_flat(k, Frame((x + 0.08, F2 + 0.36, z - 0.10), -100.0), (0.0, 0.0), (0.30, 0.03, 0.23), "case_white")
    book_flat(k, Frame((x + 0.08, F2 + 0.39, z - 0.10), -88.0), (0.0, 0.0), (0.26, 0.025, 0.19), "case_black")
    k.lathe("ceramic_white", Frame((x - 0.17, F2 + 0.36, z + 0.15)),
            [(0.0, 0.0), (0.07, 0.0), (0.09, 0.02), (0.095, 0.035), (0.088, 0.035), (0.075, 0.012), (0.0, 0.01)], 32)


def blind(k):
    """A blackout roller blind pulled all the way down over the window."""
    x0, x1 = -1.58, 1.58
    from .house import RY
    world = Frame((0.0, 0.0, 0.0))
    z = ZB + 0.07
    k.box("blind", world, (x0, F2 + 0.04, z - 0.002), (x1, RY - 0.13, z + 0.002))
    k.box("blind_metal", world, (x0 - 0.02, RY - 0.14, ZB + 0.005), (x1 + 0.02, RY - 0.02, ZB + 0.11))
    k.box("blind_metal", world, (x0, F2 + 0.025, z - 0.009), (x1, F2 + 0.05, z + 0.009))


def led_glow(k, f):
    """A soft white LED strip along the back of the desk, washing the wall behind it."""
    top = DESK["top"]
    x0, x1 = DESK["x"]
    k.quad("led_white", f, [(x1 - 0.08, top - 0.03, 0.025), (x0 + 0.08, top - 0.03, 0.025),
                            (x0 + 0.08, top - 0.015, 0.025), (x1 - 0.08, top - 0.015, 0.025)])
    LAMPS.append(dict(name="desk_glow", pos=f((0.1, top - 0.03, 0.05)), size=(1.6, 0.03), watts=42.0,
                      aim=tuple(np.subtract(f((0, -0.25, -1)), f((0, 0, 0)))), colour=(0.86, 0.90, 1.0)))


def acoustic_panels(k, f):
    """Three tall acoustic panels to the right of the setup: black slats on grey felt,
    lit from below."""
    for i in range(3):
        x0 = 1.30 + i * 0.37
        k.box("felt_dark", f, (x0, 0.20, 0.004), (x0 + 0.33, 2.62, 0.016))
        x = x0 + 0.012
        while x < x0 + 0.33 - 0.02:
            k.box("slat_black", f, (x, 0.20, 0.016), (x + 0.02, 2.62, 0.036))
            x += 0.034
    # a hidden LED strip along their foot, grazing up the slats
    k.box("metal_black", f, (1.28, 0.0, 0.06), (2.43, 0.05, 0.11))
    LAMPS.append(dict(name="slat_wash", pos=f((1.855, 0.06, 0.10)), size=(1.1, 0.03), watts=80.0,
                      aim=tuple(np.subtract(f((0, 1, -0.32)), f((0, 0, 0)))), colour=(0.88, 0.92, 1.0)))


def framed_print(k, f):
    """A large black and white print in a thin black frame with a white mat, to the
    left of the setup, lit by a small spot from the ceiling."""
    from .kit import grid
    from .house import RY
    x0, x1, y0, y1 = -2.00, -0.90, 1.02, 1.82
    fr, mat_w, d = 0.022, 0.08, 0.03
    k.box("metal_black", f, (x0, y0, 0.004), (x0 + fr, y1, d))
    k.box("metal_black", f, (x1 - fr, y0, 0.004), (x1, y1, d))
    k.box("metal_black", f, (x0 + fr, y0, 0.004), (x1 - fr, y0 + fr, d))
    k.box("metal_black", f, (x0 + fr, y1 - fr, 0.004), (x1 - fr, y1, d))
    a0, a1, b0, b1 = x0 + fr, x1 - fr, y0 + fr, y1 - fr
    p0, p1, q0, q1 = a0 + mat_w, a1 - mat_w, b0 + mat_w, b1 - mat_w
    # the mat: four strips round the picture (a whole sheet behind it would leave its
    # baked light in the dark under the picture, and the visible border would go muddy)
    for (sa, sb, ta, tb) in ((a0, a1, b0, q0), (a0, a1, q1, b1), (a0, p0, q0, q1), (p1, a1, q0, q1)):
        v, fc, _ = grid((sa, ta, d - 0.005), (sb - sa, 0, 0), (0, tb - ta, 0), max(1, round((sb - sa) / 0.06)), max(1, round((tb - ta) / 0.06)))
        k.mesh("white_v", f, v, fc, smooth=False)
    v, fc, uv = grid((p0, q0, d - 0.005), (p1 - p0, 0, 0), (0, q1 - q0, 0), 14, 10)
    k.mesh("games_print", f, v, fc, smooth=False, uvs=uv)
    spot = f(((x0 + x1) / 2, RY - F2 - 0.06, 1.1))
    LAMPS.append(dict(name="print_spot", kind="spot", pos=spot,
                      aim=tuple(np.subtract(f(((x0 + x1) / 2, (y0 + y1) / 2, 0)), spot)),
                      watts=45.0, cone=52.0, colour=(0.95, 0.96, 1.0)))


def plant(k, f):
    """A big philodendron (Poly Haven's potted_plant_02, CC0) in a black pot, in front
    of the acoustic panels."""
    from .props import load, place
    x, z = 1.86, 0.48
    pot = Frame(f((x, 0.0, z)))
    h = 0.46
    k.lathe("metal_black", pot, [(0.0, 0.0), (0.20, 0.0), (0.21, 0.02), (0.21, h), (0.195, h), (0.195, h - 0.04), (0.0, h - 0.04)], 40)
    philo = load("potted_plant_02", only={"potted_plant_02_leaves"})
    place(k.b, G, "games_philo", philo["potted_plant_02_leaves"], f((x, h - 0.04, z)), yaw=0.9, scale=1.75,
          origin=(0.0, 0.3, 0.0))
    # an uplight on the floor behind the pot, throwing the leaves' shadows up the slats
    up = f((x + 0.05, 0.05, z - 0.30))
    LAMPS.append(dict(name="plant_uplight", kind="spot", pos=up, aim=tuple(np.subtract(f((x - 0.05, 2.6, 0.05)), up)),
                      watts=55.0, cone=75.0, colour=(0.92, 0.95, 1.0)))


def walls(k, ceiling):
    """Charcoal walls and ceiling, laid just over the house's own plaster and oak. They
    are lit per vertex on a fine grid, so the glow from the screens and the LEDs falls
    smoothly across them. The ceiling belongs to the roof, so it lifts off with it."""
    from .kit import grid
    from .house import RY, DOOR
    H, e, step = RY - F2, 0.004, 0.22
    top = F2 + H

    def panel(kit, mat, origin, u, v):
        nu = max(1, int(round(np.linalg.norm(u) / step)))
        nv = max(1, int(round(np.linalg.norm(v) / step)))
        verts, faces, _ = grid(origin, u, v, nu, nv)
        kit.b.mesh(kit.g, mat, verts, faces, smooth=False)

    zf = -P / 2 - e
    # the bedroom wall, behind the setup (facing +x)
    panel(k, "wall_charcoal", (XW + e, F2, -P / 2), (0, 0, ZB + P / 2), (0, H, 0))
    # the trophy room wall (facing -x), round its door
    for z0, z1, y0 in ((ZB, -4.6, F2), (-3.4, -P / 2, F2), (-4.6, -3.4, F2 + DOOR)):
        panel(k, "wall_charcoal", (XE - e, y0, z0), (0, 0, z1 - z0), (0, top - y0, 0))
    # the back wall (facing +z), either side of the window
    for x0, x1 in ((XW, -1.5), (1.5, XE)):
        panel(k, "wall_charcoal", (x0, F2, ZB + e), (x1 - x0, 0, 0), (0, H, 0))
    # the landing wall (facing -z), round its door
    for x0, x1, y0 in ((-0.15, XW, F2), (XE, 0.85, F2), (0.85, -0.15, F2 + DOOR)):
        panel(k, "wall_charcoal", (x0, y0, zf), (x1 - x0, 0, 0), (0, top - y0, 0))
    # the ceiling, facing down
    panel(ceiling, "ceiling_charcoal", (XW, RY - 0.006, ZB), (XE - XW, 0, 0), (0, 0, -P / 2 - ZB))


# ---- pictures ------------------------------------------------------------------------------------
def paint_pictures():
    paint_print()
    paint_wallpaper()
    paint_chart()
    paint_spines()


def paint_print(w=640, h=416):
    """The framed print: an original black and white landscape, layered dunes fading
    into haze under a pale evening sky, with a fine grain as if shot on film."""
    from .study import _smooth_noise
    rng = np.random.default_rng(41)
    v = (np.arange(h)[:, None] + 0.5) / h          # 0 at the bottom of the picture
    u = (np.arange(w)[None, :] + 0.5) / w
    img = 0.86 - 0.42 * np.clip((v - 0.42) / 0.58, 0, 1) ** 0.7                       # sky: bright at the horizon, darker above
    img = np.broadcast_to(img, (h, w)).copy()
    # layers of dunes, far to near: each a smooth crest line, a little darker and sharper than the last
    layers = [(0.46, 0.035, 0.70, 0.010), (0.38, 0.06, 0.52, 0.006), (0.27, 0.09, 0.30, 0.004), (0.12, 0.12, 0.08, 0.003)]
    for i, (base, amp, tone, soft) in enumerate(layers):
        crest = base + amp * (0.6 * np.sin(u * (2.2 + i) * np.pi + i * 1.7) + 0.4 * _smooth_noise((1, w), 80 - 10 * i, rng)[0][None, :])
        k = np.clip((crest - v) / soft + 0.5, 0, 1)
        lean = np.tanh(np.gradient(crest[0]) * w * 0.25)[None, :]                       # which way the slope faces
        shade = tone + 0.12 * lean * np.clip((crest - v) / 0.07, 0, 1)                  # lit and shaded flanks
        img = img * (1 - k) + np.clip(shade, 0, 1) * k
    img = img + 0.03 * _smooth_noise((h, w), 60, rng) + rng.normal(0, 0.014, (h, w))
    img = np.clip(img, 0, 1)[..., None] * np.ones(3)
    save_png(picture_path("games_print"), img.astype(np.float32))


def paint_wallpaper(w=512, h=288):
    """The main screen: a quiet OLED wallpaper, true black with one soft band of
    white light sweeping across it."""
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = xx / w, yy / h
    d = (v - (0.25 + 0.55 * u)) / 0.09
    band = np.exp(-d ** 2) * (0.35 + 0.65 * np.exp(-((u - 0.62) / 0.35) ** 2))
    thin = np.exp(-((v - (0.18 + 0.55 * u)) / 0.006) ** 2) * 0.5 * np.exp(-((u - 0.5) / 0.3) ** 2)
    img = np.clip(band * 0.55 + thin, 0, 1)[..., None] * np.array([0.92, 0.94, 1.0])
    save_png(picture_path("screen_main"), np.clip(img, 0, 1).astype(np.float32))


def paint_chart(w=512, h=288):
    """The second screen: a win-probability chart over the rounds of a map, in white
    and greys on near-black, for two placeholder teams."""
    from .labels import text_mask
    from .study import _strokes
    rng = np.random.default_rng(27)
    img = np.ones((h, w, 3)) * 0.035
    left, right, bottom, top = 0.17 * w, 0.93 * w, 0.17 * h, 0.80 * h
    mid = (bottom + top) / 2

    def y_of(p):
        return bottom + p * (top - bottom)

    rounds = 24
    p = [0.5]
    for _ in range(rounds - 1):
        p.append(float(np.clip(p[-1] + rng.normal(0.012, 0.075), 0.12, 0.9)))
    p[-1] = 0.68
    xs = [left + (right - left) * i / (rounds - 1) for i in range(rounds)]
    pts = [(x, y_of(q)) for x, q in zip(xs, p)]
    # shaded area between the line and 50 %
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    line_y = np.interp(xx[0], xs, [y for _, y in pts])[None, :]
    inside = (xx >= left) & (xx <= right) & (((yy > mid) & (yy < line_y)) | ((yy < mid) & (yy > line_y)))
    img[inside] = np.where((yy > mid)[inside][:, None], 0.16, 0.10)
    grid = _strokes((h, w), [[(left, y_of(g)), (right, y_of(g))] for g in (0.0, 0.25, 0.75, 1.0)], 1.0) * 0.10
    dashes = _strokes((h, w), [[(x, mid), (min(x + 8, right), mid)] for x in np.arange(left, right, 14)], 1.4) * 0.45
    axes = _strokes((h, w), [[(left, bottom), (left, top)], [(left, bottom), (right, bottom)]], 1.4) * 0.55
    line = _strokes((h, w), [pts], 2.6)
    dot = (np.hypot(xx - pts[-1][0], yy - pts[-1][1]) < 4.5).astype(float)
    labels = text_mask((w, h), [
        ("WIN PROBABILITY", 0.17, 0.885, 0.055, "LEFT", 1.15),
        (TEAMS[0].upper(), 0.155, y_of(0.88) / h - 0.012, 0.042, "RIGHT", 1.05),
        (TEAMS[1].upper(), 0.155, y_of(0.10) / h - 0.012, 0.042, "RIGHT", 1.05),
        ("50%", 0.155, mid / h - 0.012, 0.038, "RIGHT", 1.0),
        ("ROUND 1", 0.17, 0.085, 0.036, "LEFT", 1.05),
        (f"ROUND {rounds}", 0.93, 0.085, 0.036, "RIGHT", 1.05),
        (f"{TEAMS[0].upper()}  68%", 0.93, 0.885, 0.055, "RIGHT", 1.1),
    ])
    for mask, level in ((grid, 1.0), (dashes, 1.0), (axes, 1.0), (labels, 0.82), (line, 1.0), (dot, 1.0)):
        m = np.clip(mask, 0, 1)[..., None]
        img = img * (1 - m) + level * m
    img = img * np.array([0.97, 0.98, 1.0])
    save_png(picture_path("screen_chart"), np.clip(img, 0, 1).astype(np.float32))


def paint_spines(strip_w=64, strip_h=512):
    """Five game-case spines side by side, each a plain black or white strip with its
    title in Inter, reading top to bottom."""
    from .labels import text_mask
    strips = []
    for title, colour in zip(GAMES, SPINES):
        mask = text_mask((strip_h, strip_w), [(title.upper(), 0.5, 0.33, 0.40, "CENTER", 1.12)])   # (64, 512)
        mask = mask.T[::-1, :]                                                          # turned to read downward
        ground, ink = (0.04, 0.93) if colour == "black" else (0.90, 0.05)
        strip = ground + (ink - ground) * mask
        strip[:, :2] *= 0.85
        strip[:, -2:] *= 0.85
        strips.append(strip)
    img = np.concatenate(strips, axis=1)[..., None] * np.ones(3)
    save_png(picture_path("game_spines"), np.clip(img, 0, 1).astype(np.float32))
