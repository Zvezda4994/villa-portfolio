"""Add, update or remove the figure at the dining table, without a full export.

    node tools/blender.mjs export_figure        (or: npm run figure)

Reads config.FIGURE. With a figure set, it opens build/villa_baked.blend, sits
the model in the opponent's chair, bakes its light and writes
web/assets/figures/opponent.glb plus its credit in the manifest. With
FIGURE = None it deletes those files and the credit, and needs nothing else:
that is the takedown path, and it takes seconds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

from villa import config as C  # noqa: E402
from villa.figure import export_figure  # noqa: E402
from villa.lighting import setup_render  # noqa: E402


def main():
    if C.FIGURE:
        baked = C.BUILD / "villa_baked.blend"
        if not baked.exists():
            raise SystemExit("build/villa_baked.blend is missing. Run the bake first (npm run bake:draft).")
        bpy.ops.wm.open_mainfile(filepath=str(baked))
        setup_render()
    export_figure(C.ASSETS / "manifest.json")


if __name__ == "__main__":
    main()
