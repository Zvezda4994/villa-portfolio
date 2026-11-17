"""Download the source textures the scene uses into assets_src/textures.

They are all CC0 textures from Poly Haven (see CREDITS.md). They are not kept in
the repo, so run this once after cloning:

    python blender/fetch_assets.py

It only uses the standard library, so any Python 3 will do, including Blender's.
Files that are already there are skipped.
"""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from villa.config import SRC_TEX          # noqa: E402
from villa.materials import TEXTURE_IDS   # noqa: E402

URL = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/{id}/{id}_diff_1k.jpg"


def main():
    SRC_TEX.mkdir(parents=True, exist_ok=True)
    for tex_id in TEXTURE_IDS:
        dest = SRC_TEX / f"{tex_id}_diff_1k.jpg"
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"have     {dest.name}")
            continue
        req = urllib.request.Request(URL.format(id=tex_id), headers={"User-Agent": "villa-build-script"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if data[:2] != b"\xff\xd8":
            raise SystemExit(f"{tex_id}: the download is not a JPEG, check the id")
        dest.write_bytes(data)
        print(f"fetched  {dest.name}  ({len(data) // 1024} KB)")


if __name__ == "__main__":
    main()
