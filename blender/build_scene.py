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
from villa.dining import build_dining  # noqa: E402
from villa.exterior import build_exterior  # noqa: E402
from villa.games import build_games  # noqa: E402
from villa.gym import build_gym  # noqa: E402
from villa.kitchen import build_kitchen  # noqa: E402
from villa.library import build_library  # noqa: E402
from villa.living import build_living  # noqa: E402
from villa.geo import Builder  # noqa: E402
from villa.house import build_house  # noqa: E402
from villa.lighting import setup_cameras, setup_lamps, setup_render, setup_world  # noqa: E402
from villa.materials import MATS, TEXTURE_IDS, build_materials  # noqa: E402
from villa.plants import build_plants  # noqa: E402
from villa.pool import build_pool, paint_pictures as paint_pool_pictures  # noqa: E402
from villa.study import build_study  # noqa: E402
from villa.terrain import build_hills, build_mask, build_sand  # noqa: E402
from villa.textures import prepare_all, prepare_pictures  # noqa: E402


def main():
    start = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = setup_render()
    prepare_all(TEXTURE_IDS)
    prepare_pictures(MATS)            # the downloaded models' colour maps
    build_mask()                      # where the sand turns to gravel; the sand material needs it
    b = Builder()
    build_dining(b)                   # paints the rug, painting and chessboard before materials load them
    build_study(b)                    # and the Persian rug, the whiteboard and the journal
    build_games(b)                    # and the screens and the game cases' spines
    build_kitchen(b)                  # and the jar labels (data/kitchen_labels.txt) and the tiles
    build_gym(b)                      # and the timer's face
    build_living(b)                   # and the TV's screen, the tank's backdrop, and the moodboard
    build_library(b)                  # and the titled spines (data/library_books.txt)
    paint_pool_pictures()             # the contact card and the sake label
    materials = build_materials()

    model = bpy.data.collections.new("villa")      # everything that gets exported
    extras = bpy.data.collections.new("lights_and_cameras")
    scene.collection.children.link(model)
    scene.collection.children.link(extras)

    build_house(b)
    build_exterior(b)
    build_plants(b)
    build_pool(b)
    objects = b.finalize(model, materials)
    # Glowing lampshade diffusers are drawn bright, but the light itself comes from
    # the lamps in lighting.py; letting the bake count them too only adds noise.
    for ob in objects.values():
        if ob.get("room") and ob.get("lit") == "raw":
            ob.visible_diffuse = ob.visible_shadow = False
        # Things carried with the camera (the visitor's hand at the pool) leave no baked
        # shadow behind when the camera moves on.
        if ob.get("attach"):
            ob.visible_diffuse = ob.visible_shadow = False
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
