"""The living room's moodboard pictures: shrink whatever is in assets_src/moodboard/
into web/assets/moodboard/ and list them in moodboard.json, which the site picks
from at random each time the living room is opened.

    npm run moodboard        (every scene build does it too)

Each picture is scaled so its long side is at most LONG_SIDE pixels (never up) and
saved as a JPEG named after its contents, so a changed picture gets a new name and
no browser shows a stale copy. Pictures that have gone from the source folder are
removed from the site. Any common image format works; transparency is dropped.
Blender ignores a photo's EXIF rotation, so turn sideways phone photos upright
before adding them.
"""
import hashlib
import json

from . import config as C

OUT = C.ASSETS / "moodboard"
LIST = OUT / "moodboard.json"
LONG_SIDE = 768
QUALITY = 82
KINDS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def sources():
    if not C.SRC_MOODBOARD.exists():
        return []
    return sorted(p for p in C.SRC_MOODBOARD.iterdir() if p.is_file() and p.suffix.lower() in KINDS)


def process():
    """Write the site's copies and the list. Returns the list's entries."""
    import bpy
    OUT.mkdir(parents=True, exist_ok=True)
    images, keep = [], set()
    for src in sources():
        digest = hashlib.sha1(src.read_bytes() + f"{LONG_SIDE}/{QUALITY}".encode()).hexdigest()[:12]
        name = f"{digest}.jpg"
        out = OUT / name
        try:
            img = bpy.data.images.load(str(src))
            w, h = img.size
        except RuntimeError as e:
            print(f"[moodboard] skipped {src.name}: Blender can't read it ({e})")
            continue
        if not w or not h:
            print(f"[moodboard] skipped {src.name}: empty picture")
            bpy.data.images.remove(img)
            continue
        s = min(1.0, LONG_SIDE / max(w, h))
        nw, nh = max(1, round(w * s)), max(1, round(h * s))
        if not out.exists():
            if s < 1.0:
                img.scale(nw, nh)
            img.file_format = "JPEG"
            img.save(filepath=str(out), quality=QUALITY)
            print(f"[moodboard] {src.name} -> {name}  {nw}x{nh}  {out.stat().st_size / 1e3:.0f} KB")
        bpy.data.images.remove(img)
        images.append(dict(file=f"moodboard/{name}", w=nw, h=nh))
        keep.add(name)
    for old in OUT.glob("*.jpg"):
        if old.name not in keep:
            old.unlink()
            print(f"[moodboard] removed {old.name}")
    images.sort(key=lambda e: e["file"])
    LIST.write_text(json.dumps(dict(
        note="Written by blender/villa/moodboard.py from assets_src/moodboard/. Do not edit by hand.",
        images=images), indent=1))
    print(f"[moodboard] {len(images)} pictures listed")
    return images


def listed():
    """The pictures the site will pick from, as last written."""
    if not LIST.exists():
        return []
    return json.loads(LIST.read_text())["images"]
