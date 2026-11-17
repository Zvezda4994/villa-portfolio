"""Step 3 of the pipeline: write everything the website loads into web/assets.

    blender --background --python blender/export_web.py

Needs build/villa_baked.blend from the bake step. Writes:
  villa.glb         the house and grounds: shapes and material names only, Meshopt-compressed
  rooms/*.glb       each furnished room's furniture, loaded after the first view is up
  textures/*.ktx2   the tiling colour textures and the furniture's pictures, with mipmaps
  sky/*.hdr         the sky as a background, as a reflection map that includes the desert,
                    and a reflection map seen from the pool (for the water)
  manifest.json     how the website should treat each material, plus sun, fog and file sizes
(The lightmaps in web/assets/lightmaps are written by the bake step.)
"""
import json
import math
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from villa import config as C  # noqa: E402
from villa.geo import to_blender  # noqa: E402
from villa.hdr import check_round_trip, write_hdr  # noqa: E402
from villa.ktx2 import write_ktx2  # noqa: E402
from villa.lighting import PREVIEW_CAMERAS, setup_render  # noqa: E402
from villa.materials import MATS, TEXTURE_IDS, srgb_to_linear  # noqa: E402
from villa.exterior import RPOOL_X, RPOOL_Z  # noqa: E402
from villa.textures import load_pixels, mask_path, picture_path, prepared  # noqa: E402

BAKED_BLEND = C.BUILD / "villa_baked.blend"
ENV_CLAMP = 40.0      # the sun is far brighter than this; unclamped it makes reflections sparkle


def _needs_uvs(ob):
    """Lightmapped surfaces, the water (for its ripples) and anything with a
    picture on it keep their UVs. On everything else they would be dead weight."""
    if ob.get("lit") == "lightmap":
        return True
    for m in ob.data.materials:
        spec = MATS.get(m.name, {}) if m is not None else {}
        if spec.get("kind") == "water" or "img" in spec:
            return True
    return False


def export_glb(objects, path):
    for ob in objects:
        if not _needs_uvs(ob):
            for layer in list(ob.data.uv_layers):
                ob.data.uv_layers.remove(layer)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True, export_yup=True,
        export_extras=True, export_cameras=False, export_lights=False, export_animations=False,
        # normals are left out to save space; the website works them out again on load
        export_image_format="NONE", export_materials="EXPORT", export_normals=False, export_tangents=False,
        export_vertex_color="ACTIVE", export_all_vertex_colors=False,
        export_meshopt_compression_enable=True)
    return path


def export_textures():
    out = C.ASSETS / "textures"
    sizes = {}
    for tex_id in TEXTURE_IDS:
        rgb = load_pixels(prepared(tex_id))[..., :3]
        sizes[tex_id] = write_ktx2(out / f"{tex_id}.ktx2", rgb, srgb=True)
    # Masks are data, not colour, so they are stored without the sRGB curve.
    for mask in sorted({m["blend"]["mask"] for m in MATS.values() if "blend" in m}):
        rgb = load_pixels(mask_path(mask))[..., :3]
        sizes[mask] = write_ktx2(out / f"{mask}.ktx2", rgb, srgb=False)
    # Furniture pictures: models' own colour maps, the rug, the painting, the chessboard.
    for name in sorted({m["img"] for m in MATS.values() if "img" in m}):
        rgb = load_pixels(picture_path(name))[..., :3]
        sizes[name] = write_ktx2(out / f"{name}.ktx2", rgb, srgb=True)
    # Drop textures nothing uses any more, so they don't get deployed.
    for old in out.glob("*.ktx2"):
        if old.stem not in sizes:
            old.unlink()
            print(f"[export] removed unused {old.name}")
    return sizes


# ---- sky panoramas ---------------------------------------------------------
# three.js reads an equirectangular image like this: a direction (x, y, z) sits
# at u = atan2(z, x) / 2pi + 0.5 across and v = asin(y) / pi + 0.5 up.
# Blender's panorama camera uses its own layout, so the render is rearranged
# to match. The layout is measured, not assumed (see _layout).

def _pano(name, world, objects, width, samples, eye, sharp=False, denoise=False):
    """Render an equirectangular panorama from `eye`. Bottom row first, linear light."""
    scene = bpy.data.scenes.new(name)
    scene.world = world
    scene.render.engine = "CYCLES"
    scene.cycles.device = bpy.context.scene.cycles.device
    scene.cycles.samples = samples
    scene.cycles.use_denoising = denoise
    if sharp:
        scene.cycles.filter_width = 0.01      # one ray through the exact centre of each pixel
    scene.render.resolution_x, scene.render.resolution_y = width, width // 2
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.view_settings.view_transform = "Raw"
    cam = bpy.data.cameras.new(name)
    cam.type = "PANO"
    cam.panorama_type = "EQUIRECTANGULAR"
    ob = bpy.data.objects.new(name, cam)
    ob.location = to_blender(eye)
    ob.rotation_euler = (math.pi / 2, 0.0, 0.0)          # level, looking along the horizon
    scene.collection.objects.link(ob)
    scene.camera = ob
    for o in objects:
        scene.collection.objects.link(o)
    with tempfile.TemporaryDirectory() as tmp:
        scene.render.filepath = str(Path(tmp) / "pano.exr")
        bpy.ops.render.render(write_still=True, scene=scene.name)
        px = load_pixels(Path(tmp) / "pano.exr")[..., :3].astype(np.float64)
    bpy.data.scenes.remove(scene)
    return px


def _layout(eye, width=256):
    """Find out how Blender lays out its panorama, by rendering one whose colour
    is the direction each pixel looks in. Returns (sign, offset): the longitude
    of column c is offset + sign * (c + 0.5) * 360 / width, in degrees."""
    world = bpy.data.worlds.new("directions")
    if world.node_tree is None:
        world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    coords = nt.nodes.new("ShaderNodeTexCoord")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(coords.outputs["Generated"], bg.inputs["Color"])
    nt.links.new(bg.outputs[0], nt.nodes.new("ShaderNodeOutputWorld").inputs["Surface"])
    d = _pano("directions", world, [], width, 1, eye, sharp=True)
    bpy.data.worlds.remove(world)
    d /= np.linalg.norm(d, axis=2, keepdims=True)
    x, y, z = d[..., 0], d[..., 2], -d[..., 1]                     # Blender axes to site axes
    h = width // 2
    lat = np.degrees(np.arcsin(np.clip(y, -1, 1)))
    want = (np.arange(h) + 0.5) / h * 180 - 90
    if np.abs(lat[:, width // 3] - want).max() > 0.25 * 180 / h:
        raise RuntimeError("Blender's panorama rows are not plain latitude any more; check _layout")
    lon = np.degrees(np.arctan2(z, x))[h // 2]
    step = 360.0 / width
    for sign in (1, -1):
        offset = lon - sign * (np.arange(width) + 0.5) * step
        a = np.radians(offset)
        mean = float(np.degrees(np.arctan2(np.sin(a).mean(), np.cos(a).mean())))
        if np.abs((offset - mean + 180) % 360 - 180).max() < 0.25 * step:
            return sign, mean
    raise RuntimeError("Blender's panorama columns are not evenly spaced longitude; check _layout")


def _to_three(px, layout):
    """Rearrange a Blender panorama into the layout three.js expects."""
    sign, offset = layout
    w = px.shape[1]
    if sign < 0:
        px = px[:, ::-1]                       # now longitude increases with the column, from the same starting point
    # column c (Blender) holds longitude offset + (c + 0.5) * step; three.js wants
    # longitude -180 + (c + 0.5) * step there, so shift by (offset + 180) / step columns
    shift = (offset + 180.0) / (360.0 / w)
    k = int(round(shift))
    if abs(shift - k) > 0.05:
        raise RuntimeError(f"panorama shift of {shift:.2f} pixels is not a whole number; pick a width divisible by 4")
    return np.roll(px, k, axis=1)


def _check_sun(px, name):
    """The brightest pixel should be where three.js will look for the sun."""
    h, w = px.shape[:2]
    x, y, z = C.sun_direction()
    want_c = (math.atan2(z, x) / (2 * math.pi) + 0.5) * w
    want_r = (math.asin(y) / math.pi + 0.5) * h
    r, c = np.unravel_index(np.argmax(px.sum(axis=2)), (h, w))
    dc = abs((c + 0.5 - want_c + w / 2) % w - w / 2)
    if dc > 3 or abs(r + 0.5 - want_r) > 3:
        raise RuntimeError(f"{name}: the sun is at pixel ({c}, {r}) but should be near ({want_c:.0f}, {want_r:.0f})")


def export_sky(model):
    world = bpy.data.worlds["GoldenHour"]
    eye = (0.0, 2.5, 0.0)
    out = C.ASSETS / "sky"
    out.mkdir(parents=True, exist_ok=True)

    background = _to_three(_pano("sky", world, [], 1024, 16, eye), _layout(eye, 1024))
    _check_sun(background, "sky_bg")

    # Reflections should show sand and hills below the horizon, not a blank sky.
    land = [o for o in model.objects if o.name in ("out__terrain", "out__hills")]
    env = _to_three(_pano("env", world, land, 512, 96, eye), _layout(eye, 512))
    _check_sun(env, "sky_env")
    env = np.clip(env, 0.0, ENV_CLAMP)

    # Reflection probes for the two bodies of water: everything as seen from just
    # above each one. Reflecting open sky would be wrong there: from the back pool
    # the house hides the sun, and the reflecting pool mostly mirrors the house.
    lamps = [o for o in bpy.data.objects if o.type == "LIGHT"]
    probes = {}
    for name, (x0, x1), (z0, z1), height in (("pool", C.POOL_X, C.POOL_Z, 0.5), ("front", RPOOL_X, RPOOL_Z, 0.3)):
        spot = ((x0 + x1) / 2, height, (z0 + z1) / 2)
        px = _to_three(_pano(name, world, list(model.objects) + lamps, 512, 128, spot, denoise=True), _layout(spot, 512))
        probes[name] = np.clip(px, 0.0, ENV_CLAMP)

    h = background.shape[0]
    horizon = background[int(h * 0.505):int(h * 0.53)]
    # haze colour: the sky just above the horizon, away from the sun's glare
    fog = np.median(horizon.reshape(-1, 3), axis=0)
    background = np.clip(background, 0.0, 2000.0)
    sizes = {}
    files = {"background": ("sky_bg", background), "environment": ("sky_env", env)}
    files.update({name: (f"{name}_env", px) for name, px in probes.items()})
    sizes, paths = {}, {}
    for key, (stem, px) in files.items():
        path = out / f"{stem}.hdr"
        sizes[key] = write_hdr(path, px)
        check_round_trip(path, px)
        paths[key] = f"sky/{stem}.hdr"
    return fog.tolist(), sizes, paths


# ---- manifest ----------------------------------------------------------------
def write_manifest(fog, sizes, sky_paths, rooms):
    materials = {}
    for name, m in MATS.items():
        entry = dict(kind=m["kind"])
        if "tex" in m:
            entry["map"] = f"textures/{m['tex']}.ktx2"
            entry["tile"] = m["tile"]
            entry["color"] = list(m.get("tint", (1, 1, 1)))
        else:
            entry["color"] = list(srgb_to_linear(m["color"]))
            if "img" in m:
                entry["map"] = f"textures/{m['img']}.ktx2"
        if "room" in m:
            entry["room"] = m["room"]           # fetched with that room, not before the first view
        if "blend" in m:
            bl = m["blend"]
            entry["blend"] = dict(map=f"textures/{bl['tex']}.ktx2", tile=bl["tile"], color=list(bl["tint"]),
                                  mask=f"textures/{bl['mask']}.ktx2")
        for key in ("rough", "metal", "opacity", "strength", "probe", "ripple"):
            if key in m:
                entry[key] = m[key]
        if m.get("double_sided"):
            entry["doubleSided"] = True
        materials[name] = entry

    lightmaps = {}
    for atlas in C.ATLASES:
        full, small = C.ASSETS / "lightmaps" / f"{atlas}.ktx2", C.ASSETS / "lightmaps" / f"{atlas}_lo.ktx2"
        if full.exists():
            lightmaps[atlas] = dict(file=f"lightmaps/{atlas}.ktx2")
            sizes[f"lightmap {atlas}"] = full.stat().st_size
            if C.ATLASES[atlas].get("room"):
                lightmaps[atlas]["room"] = C.ATLASES[atlas]["room"]     # no small copy; fetched with the room
            else:
                lightmaps[atlas]["small"] = f"lightmaps/{atlas}_lo.ktx2"
                sizes[f"lightmap {atlas} (small)"] = small.stat().st_size

    scene = bpy.context.scene
    manifest = dict(
        note="Written by blender/export_web.py. Do not edit by hand.",
        lightRange=C.LIGHT_RANGE,
        exposure=2.0 ** scene.view_settings.exposure,
        sun=list(C.sun_direction()),
        fog=dict(color=fog),
        sky=sky_paths,
        model="villa.glb",
        rooms=rooms,
        lightmaps=lightmaps,
        materials=materials,
        cameras={k: dict(pos=list(v["pos"]), target=list(v["target"]), fov=v["fov"]) for k, v in PREVIEW_CAMERAS.items()},
        bytes=sizes,
    )
    (C.ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def main():
    start = time.time()
    if not BAKED_BLEND.exists():
        raise SystemExit("build/villa_baked.blend is missing. Run blender/bake_lightmaps.py first.")
    bpy.ops.wm.open_mainfile(filepath=str(BAKED_BLEND))
    setup_render(samples=64)
    model = bpy.data.collections["villa"]
    C.ASSETS.mkdir(parents=True, exist_ok=True)

    sizes = {}
    fog, sky_sizes, sky_paths = export_sky(model)          # before the GLB export, which strips UVs
    sizes.update({f"sky {k}": v for k, v in sky_sizes.items()})
    sizes.update({f"texture {k}": v for k, v in export_textures().items()})
    house = [ob for ob in model.objects if not ob.get("room")]
    sizes["model"] = export_glb(house, C.ASSETS / "villa.glb").stat().st_size
    # Each furnished room in a file of its own, in the order they are loaded
    rooms = {}
    for room in sorted({ob["room"] for ob in model.objects if ob.get("room")}):
        objects = [ob for ob in model.objects if ob.get("room") == room]
        rel = f"rooms/{room}.glb"
        sizes[f"room {room}"] = export_glb(objects, C.ASSETS / rel).stat().st_size
        rooms[room] = dict(model=rel)
    for old in (C.ASSETS / "rooms").glob("*.glb"):
        if old.stem not in rooms:
            old.unlink()
            print(f"[export] removed unused {old.name}")
    manifest = write_manifest(fog, sizes, sky_paths, rooms)

    total = sum(manifest["bytes"].values())
    for k, v in sorted(manifest["bytes"].items(), key=lambda kv: -kv[1]):
        print(f"[export] {v / 1e6:6.2f} MB  {k}")
    print(f"[export] {total / 1e6:6.2f} MB total, {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
