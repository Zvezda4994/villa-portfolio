"""Sky, sun, indoor lamps, cameras and render settings.

Golden hour. The sun and sky both come from Blender's sky model, so the render,
the baked lightmaps and the sky image the website shows all agree.
"""
import math

import bpy
from mathutils import Vector

from . import config as C
from .geo import to_blender
from .house import ROOMS, H1, RY, SZ1

# Overall brightness of the sky model, chosen so a sunlit pale wall lands near 1.0.
SKY_STRENGTH = 0.07
# The sun disc on its own is fairly white at this height, so it is warmed up and
# lifted a little to get the golden-hour look: warm sun, cool blue-grey shadows.
SUN_TINT = (1.30, 0.98, 0.62)
SKY_TINT = (0.95, 0.98, 1.06)
SUN_SIZE_DEG = 1.3          # wider than the real sun, for softer shadow edges

LAMP_COLOUR = (1.0, 0.62, 0.32)     # warm white
ROOM_LAMP_WATTS = 7.0              # per square metre of floor
POOL_LAMP_WATTS = 140.0
SOFFIT_LAMP_WATTS = 22.0


def setup_render(samples=256):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == kind]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == kind
                scene.cycles.device = "GPU"
                break
        except Exception:
            continue
    else:
        scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.02
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.transparent_max_bounces = 16
    scene.cycles.sample_clamp_indirect = 8.0
    # sun glinting off the glass onto the ground is real, but it bakes as noisy speckles
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0
    return scene


def setup_world():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("GoldenHour")
    scene.world = world
    if world.node_tree is None:
        world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    new, link = nt.nodes.new, nt.links.new

    # Measured: with rotation 0 the sun sits toward Blender +Y, and turning it
    # positive swings it toward +X.
    sx, sy, _sz = to_blender(C.sun_direction())
    rotation = math.atan2(sx, sy)

    def sky(disc):
        n = new("ShaderNodeTexSky")
        n.sky_type = "MULTIPLE_SCATTERING"
        n.sun_elevation = math.radians(C.SUN_ELEVATION)
        n.sun_rotation = rotation
        n.sun_disc = disc
        n.sun_size = math.radians(SUN_SIZE_DEG)
        n.aerosol_density = 2.0          # a little desert haze
        return n

    dome, with_sun = sky(False), sky(True)
    # (sky with sun) minus (sky alone) leaves just the sun, which can then be tinted.
    only_sun = new("ShaderNodeVectorMath")
    only_sun.operation = "SUBTRACT"
    link(with_sun.outputs[0], only_sun.inputs[0])
    link(dome.outputs[0], only_sun.inputs[1])
    warm = new("ShaderNodeVectorMath")
    warm.operation = "MULTIPLY"
    warm.inputs[1].default_value = SUN_TINT
    link(only_sun.outputs[0], warm.inputs[0])
    cool = new("ShaderNodeVectorMath")
    cool.operation = "MULTIPLY"
    cool.inputs[1].default_value = SKY_TINT
    link(dome.outputs[0], cool.inputs[0])
    both = new("ShaderNodeVectorMath")
    both.operation = "ADD"
    link(warm.outputs[0], both.inputs[0])
    link(cool.outputs[0], both.inputs[1])
    bg = new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = SKY_STRENGTH
    link(both.outputs[0], bg.inputs["Color"])
    out = new("ShaderNodeOutputWorld")
    link(bg.outputs[0], out.inputs["Surface"])
    return world


def _lamp(collection, name, pos, size, watts, aim=(0.0, -1.0, 0.0), colour=LAMP_COLOUR):
    light = bpy.data.lights.new(name, "AREA")
    light.shape = "RECTANGLE"
    light.size, light.size_y = size
    light.energy = watts
    light.color = colour
    ob = bpy.data.objects.new(name, light)
    ob.location = to_blender(pos)
    ob.rotation_euler = Vector(to_blender(aim)).to_track_quat("-Z", "Y").to_euler()
    ob.visible_camera = False
    ob.visible_glossy = False
    collection.objects.link(ob)
    return ob


def _spot(collection, name, pos, aim, watts, cone, colour=LAMP_COLOUR):
    """A small spotlight: the uplights and step lights outside, a desk lamp."""
    light = bpy.data.lights.new(name, "SPOT")
    light.energy = watts
    light.color = colour
    light.spot_size = math.radians(cone)
    light.spot_blend = 0.6
    light.shadow_soft_size = 0.03
    ob = bpy.data.objects.new(name, light)
    ob.location = to_blender(pos)
    ob.rotation_euler = Vector(to_blender(aim)).normalized().to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(ob)
    return ob


def setup_lamps(collection):
    """Lights are on in every room, plus a row of small ones under the overhangs.
    Furnished rooms turn their ceiling light down and add their own lamps."""
    FURNISHED_CEILING = {room.ROOM: room.CEILING_LIGHT for room in furnished_rooms()}
    # a room can also change its ceiling light's colour (the games room's is cool white)
    CEILING_COLOUR = {room.ROOM: getattr(room, "CEILING_COLOUR", LAMP_COLOUR) for room in furnished_rooms()}
    for name, (group, (x0, x1), (z0, z1), _mat) in ROOMS.items():
        ceiling = H1 if group == "ground" else RY
        w, d = x1 - x0, z1 - z0
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if name == "foyer":                      # keep clear of the stairwell
            cz, d = (SZ1 + z1) / 2, z1 - SZ1
        watts = ROOM_LAMP_WATTS * w * d * FURNISHED_CEILING.get(name, 1.0)
        _lamp(collection, f"lamp_{name}", (cx, ceiling - 0.25, cz), (w * 0.55, d * 0.55), watts,
              colour=CEILING_COLOUR.get(name, LAMP_COLOUR))
    for i in range(10):
        _lamp(collection, f"soffit_low_{i}", (-10.8 + i * 2.4, H1 - 0.03, 8.7), (0.14, 0.14), SOFFIT_LAMP_WATTS)
        _lamp(collection, f"soffit_high_{i}", (-11.7 + i * 2.6, RY - 0.03, 9.4), (0.14, 0.14), SOFFIT_LAMP_WATTS)
    # underwater lights along the house side of the pool, so it glows in the evening shade
    # uplights and step lights placed by exterior.py
    from .exterior import GROUND_LIGHTS
    for i, gl in enumerate(GROUND_LIGHTS):
        _spot(collection, f"ground_{i}", gl["pos"], gl["aim"], gl["watts"], gl["cone"])
    for i, x in enumerate(pool_light_positions()):
        _lamp(collection, f"pool_{i}", (x, -0.85, C.POOL_Z[1] - 0.06), (0.3, 0.3), POOL_LAMP_WATTS,
              aim=(0.0, -0.15, -1.0), colour=(0.75, 0.95, 1.0))
    # The furnished rooms' own lamps (pendants, picture lights, desk lamps, screens),
    # and the pool deck's lanterns, uplights and fire (filled in while building).
    # Each is a dict: "kind" is "area" (the default), "spot" or "point".
    for lamp in furnished_lamps():
        colour = lamp.get("colour", LAMP_COLOUR)
        kind = lamp.get("kind", "area")
        if kind == "spot":
            _spot(collection, lamp["name"], lamp["pos"], lamp["aim"], lamp["watts"], lamp["cone"], colour)
        elif kind == "point":
            _point(collection, lamp["name"], lamp["pos"], lamp["watts"], lamp.get("radius", 0.05), colour)
        else:
            _lamp(collection, lamp["name"], lamp["pos"], lamp["size"], lamp["watts"], aim=lamp["aim"], colour=colour)


def furnished_rooms():
    """The modules of the furnished rooms that have their own lamps and ceiling light."""
    from . import bedroom, dining, foyer, games, garage, gym, kitchen, library, living, study, trophy
    return [dining, study, games, kitchen, gym, living, library, trophy, bedroom, garage, foyer]


def furnished_lamps():
    from .pool import LAMPS as POOL_LAMPS
    lamps = [lamp for room in furnished_rooms() for lamp in room.LAMPS]
    return lamps + POOL_LAMPS


def _point(collection, name, pos, watts, radius, colour):
    """A small round light: a lantern's candle, the fire."""
    light = bpy.data.lights.new(name, "POINT")
    light.energy = watts
    light.color = colour
    light.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, light)
    ob.location = to_blender(pos)
    ob.visible_camera = False
    ob.visible_glossy = False
    collection.objects.link(ob)
    return ob


def pool_light_positions():
    x0, x1 = C.POOL_X
    return [x0 + (x1 - x0) * (i + 0.5) / 4 for i in range(4)]


def add_camera(collection, name, pos, target, fov=45.0):
    """A camera at `pos` looking at `target` (site coordinates). `fov` is the
    vertical angle, the same number three.js uses."""
    cam = bpy.data.cameras.new(name)
    cam.sensor_fit = "VERTICAL"
    cam.angle_y = math.radians(fov)
    cam.clip_start, cam.clip_end = 0.1, 3000.0
    ob = bpy.data.objects.new(name, cam)
    p, t = Vector(to_blender(pos)), Vector(to_blender(target))
    ob.location = p
    ob.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(ob)
    return ob


from .bedroom import BEDROOM_CAM, MAP_CAM as BEDROOM_MAP_CAM, SHELF_CAM as BEDROOM_SHELF_CAM  # noqa: E402
from .dining import CHESS_CAM, ROOM_CAM  # noqa: E402
from .foyer import CONSOLE_CAM as FOYER_CONSOLE_CAM, FOYER_CAM  # noqa: E402
from .games import DESK_CAM as GAMES_DESK_CAM, GAMES_CAM, SHELF_CAM  # noqa: E402
from .garage import GARAGE_CAM, KEYS_CAM as GARAGE_KEYS_CAM, SCREEN_CAM as GARAGE_SCREEN_CAM  # noqa: E402
from .gym import BOARD_CAM as GYM_BOARD_CAM, GEAR_CAM, GYM_CAM, WIDE_CAM as GYM_WIDE_CAM  # noqa: E402
from .kitchen import KITCHEN_CAM, SHELF_CAM as KITCHEN_SHELF_CAM, WIDE_CAM as KITCHEN_WIDE_CAM  # noqa: E402
from .library import DESK_CAM as LIBRARY_DESK_CAM, LIBRARY_CAM, SPINES_CAM, SPINES_CAM_B  # noqa: E402
from .living import LIVING_CAM, MOODBOARD_CAM, TANK_CAM, TV_CAM  # noqa: E402
from .pool import MOMENT_CAM  # noqa: E402
from .study import DESK_CAM, STUDY_CAM  # noqa: E402
from .trophy import BELT_CAM as TROPHY_BELT_CAM, CASES_CAM as TROPHY_CASES_CAM, CHESS_CAM as TROPHY_CHESS_CAM, TROPHY_CAM  # noqa: E402

# The views rendered for review after each build step. The website can jump to
# any of them with ?shot=name.
PREVIEW_CAMERAS = {
    "landing": dict(pos=C.LANDING_CAM["pos"], target=C.LANDING_CAM["target"], fov=C.LANDING_CAM["fov"]),
    "pool": dict(pos=(18.0, 7.0, -24.0), target=(4.0, 0.5, -12.0), fov=45.0),
    "entrance": dict(pos=(-9.5, 1.7, 20.5), target=(-1.0, 2.6, 8.0), fov=50.0),
    "dining": ROOM_CAM,
    "chess": CHESS_CAM,
    "deck": dict(pos=(-7.0, 4.2, -10.0), target=(2.0, 0.0, -17.8), fov=50.0),
    "pool_moment": MOMENT_CAM,
    "study": STUDY_CAM,
    "study_desk": DESK_CAM,
    "games": GAMES_CAM,
    "games_desk": GAMES_DESK_CAM,
    "games_shelf": SHELF_CAM,
    "kitchen": KITCHEN_CAM,
    "kitchen_shelf": KITCHEN_SHELF_CAM,
    "kitchen_wide": KITCHEN_WIDE_CAM,
    "gym": GYM_CAM,
    "gym_gear": GEAR_CAM,
    "gym_wide": GYM_WIDE_CAM,
    "gym_board": GYM_BOARD_CAM,
    "living": LIVING_CAM,
    "living_tv": TV_CAM,
    "living_moodboard": MOODBOARD_CAM,
    "living_tank": TANK_CAM,
    "library": LIBRARY_CAM,
    "library_spines": SPINES_CAM,
    "library_spines_b": SPINES_CAM_B,
    "library_desk": LIBRARY_DESK_CAM,
    "trophy": TROPHY_CAM,
    "trophy_cases": TROPHY_CASES_CAM,
    "trophy_belt": TROPHY_BELT_CAM,
    "trophy_chess": TROPHY_CHESS_CAM,
    "bedroom": BEDROOM_CAM,
    "bedroom_map": BEDROOM_MAP_CAM,
    "bedroom_shelf": BEDROOM_SHELF_CAM,
    "garage": GARAGE_CAM,
    "garage_keys": GARAGE_KEYS_CAM,
    "garage_screen": GARAGE_SCREEN_CAM,
    "foyer": FOYER_CAM,
    "foyer_console": FOYER_CONSOLE_CAM,
    # the upstairs landing: from by the library door, across to the stairwell's railing and
    # the top of the stairs at its far end
    "stairs_top": dict(pos=(0.30, C.F2 + 1.60, 5.40), target=(-3.70, C.F2 + 0.55, 0.90), fov=55.0),
}


def setup_cameras(collection):
    cams = {name: add_camera(collection, f"cam_{name}", **spec) for name, spec in PREVIEW_CAMERAS.items()}
    bpy.context.scene.camera = cams["landing"]
    return cams
