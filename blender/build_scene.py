"""Step 1 of the pipeline: build the whole scene from nothing and save it.

    blender --background --python blender/build_scene.py

Writes build/villa.blend. Nothing here is edited by hand; change the scripts in
blender/villa and run this again.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

from villa import config as C  # noqa: E402
from villa.exterior import build_exterior  # noqa: E402
from villa.geo import Builder  # noqa: E402
from villa.house import build_house  # noqa: E402
from villa.lighting import setup_cameras, setup_lamps, setup_render, setup_world  # noqa: E402
from villa.materials import TEXTURE_IDS, build_materials  # noqa: E402
from villa.plants import build_plants  # noqa: E402
from villa.terrain import build_hills, build_mask, build_sand  # noqa: E402
from villa.textures import prepare_all  # noqa: E402


def main():
    start = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = setup_render()
    prepare_all(TEXTURE_IDS)
    build_mask()                      # where the sand turns to gravel; the sand material needs it
    materials = build_materials()

    model = bpy.data.collections.new("villa")      # everything that gets exported
    extras = bpy.data.collections.new("lights_and_cameras")
    scene.collection.children.link(model)
    scene.collection.children.link(extras)

    b = Builder()
    build_house(b)
    build_exterior(b)
    build_plants(b)
    b.finalize(model, materials)
    build_sand(model, materials)
    build_hills(model, materials)

    setup_world()
    setup_lamps(extras)
    setup_cameras(extras)

    C.BUILD.mkdir(parents=True, exist_ok=True)
    (C.BUILD / "atlas_rects.json").write_text(json.dumps(b.atlas_rects))
    bpy.ops.wm.save_as_mainfile(filepath=str(C.BLEND_FILE))
    tris = sum(len(p.vertices) - 2 for o in model.objects for p in o.data.polygons)
    print(f"[build] saved {C.BLEND_FILE.name}: {len(model.objects)} objects, {tris} triangles, {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
