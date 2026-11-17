"""Render the review images from build/villa.blend into previews/.

    blender --background --python blender/render_previews.py -- [--draft] [camera names...]

With no names it renders every camera in lighting.PREVIEW_CAMERAS.
--draft renders at half size with few samples, for quick checks while working.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

from villa import config as C  # noqa: E402
from villa.lighting import PREVIEW_CAMERAS, setup_render  # noqa: E402


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    draft = "--draft" in args
    names = [a for a in args if not a.startswith("--")] or list(PREVIEW_CAMERAS)

    bpy.ops.wm.open_mainfile(filepath=str(C.BLEND_FILE))
    scene = setup_render(samples=48 if draft else 384)
    scene.render.resolution_percentage = 50 if draft else 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    out = C.BUILD / "draft" if draft else C.PREVIEWS
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        start = time.time()
        scene.camera = bpy.data.objects[f"cam_{name}"]
        scene.render.filepath = str(out / f"{name}.jpg")
        bpy.ops.render.render(write_still=True)
        print(f"[render] {name}.jpg  {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
