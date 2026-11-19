"""Shrink the moodboard pictures in assets_src/moodboard/ into the site.

    blender --background --python blender/moodboard.py      (or: npm run moodboard)

Needs no scene and no rebuild: the site reads web/assets/moodboard/moodboard.json
each time the living room opens. See villa/moodboard.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from villa.moodboard import process  # noqa: E402

if __name__ == "__main__":
    process()
