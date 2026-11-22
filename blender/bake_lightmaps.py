"""Step 2 of the pipeline: bake the lighting.

    blender --background --python blender/bake_lightmaps.py -- [--draft] [atlas names...]

Opens build/villa.blend and works out, with Cycles on the GPU, how much light
lands on every surface. Flat surfaces get lightmap textures; plants, rocks,
hills and window frames get the light stored in their vertices.

Writes:
  build/bake/<atlas>.npy          the raw result, kept so textures can be re-made without re-baking
  web/assets/lightmaps/*.ktx2     what the website loads (full size and a small quick-loading copy)
  build/villa_baked.blend         the scene with vertex light filled in, ready for export

--draft bakes at a quarter of the size with few samples, to check the pipeline quickly.
--encode-only skips the baking and re-makes the .ktx2 files from the saved .npy results.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from villa import config as C  # noqa: E402
from villa.denoise import chart_ids, denoise  # noqa: E402
from villa.ktx2 import write_ktx2, write_smaller  # noqa: E402
from villa.lighting import setup_render  # noqa: E402
from villa.textures import to_srgb  # noqa: E402

BAKED_BLEND = C.BUILD / "villa_baked.blend"


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def fill_holes(rgb, mask):
    """Spread colour from baked texels into the empty gaps between them, so that
    filtering and mipmaps never pull in black."""
    rgb = rgb * mask[..., None]
    weight = mask.astype(np.float64)
    # a few rounds of growing by one texel, for a clean edge...
    for _ in range(4):
        acc = np.zeros_like(rgb)
        cnt = np.zeros_like(weight)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            acc += np.roll(rgb, (dy, dx), axis=(0, 1))
            cnt += np.roll(weight, (dy, dx), axis=(0, 1))
        grow = (weight == 0) & (cnt > 0)
        rgb[grow] = acc[grow] / cnt[grow][:, None]
        weight[grow] = 1.0
    # ...then fill whatever is left from smaller and smaller averages
    levels = [(rgb * weight[..., None], weight)]
    while levels[-1][1].shape[0] > 1:
        c, w = levels[-1]
        h, wd = w.shape
        levels.append((c.reshape(h // 2, 2, wd // 2, 2, 3).sum(axis=(1, 3)), w.reshape(h // 2, 2, wd // 2, 2).sum(axis=(1, 3))))
    cur = levels[-1][0] / np.maximum(levels[-1][1], 1e-9)[..., None]
    for c, w in reversed(levels[:-1]):
        up = cur.repeat(2, axis=0).repeat(2, axis=1)
        cur = np.where(w[..., None] > 0, c / np.maximum(w, 1e-9)[..., None], up)
    return cur


def encode(light, path, max_levels):
    """Light values (linear, any brightness) to an 8-bit KTX2, with a little noise
    added before rounding so smooth gradients do not show bands."""
    rng = np.random.default_rng(1)
    enc = to_srgb(np.clip(light / C.LIGHT_RANGE, 0.0, 1.0))
    enc = np.clip(enc + (rng.random(enc.shape) - 0.5) / 255.0, 0.0, 1.0)
    return write_ktx2(path, enc, srgb=True, max_levels=max_levels)


def shrink(a, size):
    while a.shape[0] > size:
        h, w = a.shape[:2]
        a = a.reshape(h // 2, 2, w // 2, 2, -1).mean(axis=(1, 3))
    return a


def bake_atlas(scene, model, atlas, size, rects):
    objects = [o for o in model.objects if o.get("lightmap") == atlas]
    if not objects:
        return None
    img = bpy.data.images.new(f"lm_{atlas}", size, size, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    for mat in bpy.data.materials:
        node = mat.node_tree.nodes.get("BAKE") if mat.node_tree else None
        if node:
            node.image = img
            mat.node_tree.nodes.active = node
    for ob in objects:
        ob.data.uv_layers.active = ob.data.uv_layers["Lightmap"]
    select_only(objects)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=2, margin_type="EXTEND",
                        use_clear=True, target="IMAGE_TEXTURES")
    px = np.empty(size * size * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    light = px.reshape(size, size, 4)[..., :3].astype(np.float64)

    if rects is None:
        mask = np.ones((size, size), dtype=bool)            # the sand covers its whole lightmap
    else:
        full = C.ATLASES[atlas]["size"]
        k = size / full
        mask = np.zeros((size, size), dtype=bool)
        for x, y, w, h in rects:
            mask[int(np.ceil(y * k)):int(np.floor((y + h) * k)), int(np.ceil(x * k)):int(np.floor((x + w) * k))] = True
    return fill_holes(light, mask)


def bake_vertices(model):
    """Light for the small bumpy things, stored per vertex instead of in a texture."""
    objects = [o for o in model.objects if o.get("lit") == "vertex"]
    for ob in objects:
        attrs = ob.data.color_attributes
        attrs.active_color = attrs["Light"]
        attrs.render_color_index = list(attrs).index(attrs["Light"])
    select_only(objects)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, target="VERTEX_COLORS")
    for ob in objects:
        attrs = ob.data.color_attributes
        data = attrs["Light"].data
        col = np.empty(len(data) * 4, dtype=np.float32)
        data.foreach_get("color", col)
        col = col.reshape(-1, 4)
        if "Albedo" in attrs:
            # surfaces painted per vertex: the colour goes into the light, and the
            # material on the website is plain white
            albedo = np.empty(len(data) * 4, dtype=np.float32)
            attrs["Albedo"].data.foreach_get("color", albedo)
            col[:, :3] *= albedo.reshape(-1, 4)[:, :3]
            attrs.remove(attrs["Albedo"])
            attrs.active_color = attrs["Light"]
        col[:, :3] = np.clip(col[:, :3] / C.LIGHT_RANGE, 0.0, 1.0)     # same scaling as the lightmaps
        col[:, 3] = 1.0
        data.foreach_set("color", col.ravel())
    return len(objects)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    draft = "--draft" in args
    encode_only = "--encode-only" in args
    only = [a for a in args if not a.startswith("--")]

    bpy.ops.wm.open_mainfile(filepath=str(C.BLEND_FILE))
    scene = setup_render(samples=48 if draft else 768)
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    model = bpy.data.collections["villa"]
    rects = json.loads((C.BUILD / "atlas_rects.json").read_text())
    C.BAKE_DIR.mkdir(parents=True, exist_ok=True)
    out = C.ASSETS / "lightmaps"
    out.mkdir(parents=True, exist_ok=True)
    report = {}

    for atlas, spec in C.ATLASES.items():
        if only and atlas not in only:
            continue
        start = time.time()
        size = spec["size"] // 4 if draft else spec["size"]
        if encode_only:
            light = np.load(C.BAKE_DIR / f"{atlas}.npy").astype(np.float64)
            size = light.shape[0]
        else:
            light = bake_atlas(scene, model, atlas, size, rects.get(atlas))
            if light is None:
                continue
            np.save(C.BAKE_DIR / f"{atlas}.npy", light.astype(np.float16))
        # the grain Cycles leaves in a bake, smoothed within each chart (villa/denoise.py);
        # the raw bake stays in the .npy, so --encode-only redoes this from it
        scale = size / spec["size"]
        light, grain, grain_after = denoise(light, rects.get(atlas), scale)
        light = fill_holes(light, chart_ids(light.shape[:2], rects.get(atlas), scale) >= 0)
        big = encode(light, out / f"{atlas}.ktx2", max_levels=4)
        # A room's lightmap can be baked sharper than it ships: `ship` keeps only the
        # mip levels up to that size (the dining room's, to stay under its 4.5 MB).
        if spec.get("ship"):
            tmp = out / f"{atlas}.ship.ktx2"
            n = write_smaller(out / f"{atlas}.ktx2", tmp, spec["ship"])
            if n:
                tmp.replace(out / f"{atlas}.ktx2")
                big, size = n, spec["ship"]
        # The house's lightmaps also get a small copy that loads first. A furnished
        # room's arrives after the first view anyway, so it only needs the full one.
        if spec.get("room"):
            (out / f"{atlas}_lo.ktx2").unlink(missing_ok=True)
            small = 0
        else:
            small = encode(shrink(light, min(size, C.LOW_RES)), out / f"{atlas}_lo.ktx2", max_levels=3)
        report[atlas] = dict(size=size, bytes=big, bytes_lo=small, grain=grain, grain_after=grain_after,
                             p50=float(np.percentile(light, 50)), p99=float(np.percentile(light, 99)),
                             p999=float(np.percentile(light, 99.9)), max=float(light.max()))
        print(f"[bake] {atlas}: {size}px  {big // 1024} KB (+{small // 1024} KB small)  "
              f"median {report[atlas]['p50']:.2f}  99% {report[atlas]['p99']:.2f}  max {report[atlas]['max']:.2f}  "
              f"grain {grain:.3f} -> {grain_after:.3f}  {time.time() - start:.0f}s")

    if not only and not encode_only:
        start = time.time()
        # Vertex light is cheap (seconds) and lives in the room files, not the lightmaps,
        # so even a draft gives it enough samples for dark rooms to come out clean.
        scene.cycles.samples = 256 if draft else 512
        n = bake_vertices(model)
        print(f"[bake] vertex light on {n} objects  {time.time() - start:.0f}s")
        bpy.ops.wm.save_as_mainfile(filepath=str(BAKED_BLEND))
    (C.BAKE_DIR / "report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
