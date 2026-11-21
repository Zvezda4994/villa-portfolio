"""Download the source textures, models, fonts and map data the scene uses into assets_src/.

The textures and models are CC0 assets from Poly Haven; the fonts are from the
Google Fonts collection, under the SIL Open Font License; the coastlines for the
bedroom's world map are Natural Earth's, public domain; the paintings hung in the
rooms are public-domain works from Wikimedia Commons (see CREDITS.md). None
of them are kept in the repo, so run this once after cloning:

    python blender/fetch_assets.py

It only uses the standard library, so any Python 3 will do, including Blender's.
Files that are already there are skipped.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from villa.config import ARTWORKS, FONTS, SRC_ART, SRC_FONTS, SRC_GEO, SRC_MODELS, SRC_TEX, WORLD_LAND   # noqa: E402
from villa.materials import TEXTURE_IDS       # noqa: E402
from villa.props import MODEL_IDS             # noqa: E402

TEXTURE_URL = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/{id}/{id}_diff_1k.jpg"
FILES_API = "https://api.polyhaven.com/files/{id}"
HEADERS = {"User-Agent": "villa-build-script/1.0 (portfolio scene build)"}   # Wikimedia refuses a bare name


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as resp:
        return resp.read()


def fetch_textures():
    SRC_TEX.mkdir(parents=True, exist_ok=True)
    for tex_id in TEXTURE_IDS:
        dest = SRC_TEX / f"{tex_id}_diff_1k.jpg"
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"have     {dest.name}")
            continue
        data = get(TEXTURE_URL.format(id=tex_id))
        if data[:2] != b"\xff\xd8":
            raise SystemExit(f"{tex_id}: the download is not a JPEG, check the id")
        dest.write_bytes(data)
        print(f"fetched  {dest.name}  ({len(data) // 1024} KB)")


def fetch_models():
    """Each model as glTF with 1k textures: the .gltf, its .bin and the textures
    it names, kept in the same folder layout Poly Haven uses."""
    for model_id in MODEL_IDS:
        folder = SRC_MODELS / model_id
        gltf = folder / f"{model_id}_1k.gltf"
        if gltf.exists():
            print(f"have     {model_id}")
            continue
        files = json.loads(get(FILES_API.format(id=model_id)))
        entry = files["gltf"]["1k"]["gltf"]
        wanted = {gltf.name: entry["url"]}
        wanted.update({rel: f["url"] for rel, f in entry.get("include", {}).items()})
        total = 0
        for rel, url in wanted.items():
            dest = folder / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = get(url)
            dest.write_bytes(data)
            total += len(data)
        print(f"fetched  {model_id}  ({len(wanted)} files, {total // 1024} KB)")


def fetch_fonts():
    """Typefaces for hand lettering and printed labels (Blender's own Inter covers the rest)."""
    SRC_FONTS.mkdir(parents=True, exist_ok=True)
    for name, url in FONTS.items():
        dest = SRC_FONTS / name
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"have     {name}")
            continue
        data = get(url)
        if data[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
            raise SystemExit(f"{name}: the download is not a font file, check the link")
        dest.write_bytes(data)
        print(f"fetched  {name}  ({len(data) // 1024} KB)")


def fetch_geo():
    """Natural Earth's land outlines at 1:110m, for the bedroom's world map."""
    SRC_GEO.mkdir(parents=True, exist_ok=True)
    dest = SRC_GEO / WORLD_LAND["file"]
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"have     {dest.name}")
        return
    data = get(WORLD_LAND["url"])
    land = json.loads(data)
    if land.get("type") != "FeatureCollection" or not land.get("features"):
        raise SystemExit(f"{dest.name}: the download is not GeoJSON land outlines, check the link")
    dest.write_bytes(data)
    print(f"fetched  {dest.name}  ({len(data) // 1024} KB, {len(land['features'])} shapes)")


def fetch_art():
    """Public-domain paintings, as Wikimedia Commons' 1920 px copies."""
    SRC_ART.mkdir(parents=True, exist_ok=True)
    for name, url in ARTWORKS.items():
        dest = SRC_ART / name
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"have     {name}")
            continue
        data = get(url)
        if data[:2] != b"\xff\xd8":
            raise SystemExit(f"{name}: the download is not a JPEG, check the link")
        dest.write_bytes(data)
        print(f"fetched  {name}  ({len(data) // 1024} KB)")


def main():
    fetch_textures()
    fetch_models()
    fetch_fonts()
    fetch_geo()
    fetch_art()


if __name__ == "__main__":
    main()
