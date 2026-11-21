"""Printed and hand-lettered pictures: the contact card and the sake label on the
pool deck, and the lettering in the furnished rooms (the study's whiteboard and
journal, the games room's screens and game cases).

Text is set with Blender's own text objects. Printed things use the Inter
typeface that ships with Blender (SIL Open Font License, the same face the
website uses); hand lettering uses the fonts in config.FONTS, which fetch_assets.py
downloads into assets_src/fonts. Each line of text is rendered flat, white on
black, as a mask, then laid over a background painted here, so no font file
needs to be in the repo.
"""
import math
import tempfile
from pathlib import Path

import numpy as np

from . import config as C
from .textures import load_pixels, picture_path, save_png

def _font(name=None):
    """Inter (Blender's own copy) by default, or one of config.FONTS by file name."""
    import bpy
    if name:
        path = C.SRC_FONTS / name
        if not path.exists():
            raise FileNotFoundError(f"{path} is missing. Run blender/fetch_assets.py first.")
        return bpy.data.fonts.load(str(path), check_existing=True)
    fonts = Path(bpy.utils.system_resource("DATAFILES", path="fonts"))
    for file in ("Inter.woff2", "Inter.ttf"):
        if (fonts / file).exists():
            try:
                return bpy.data.fonts.load(str(fonts / file), check_existing=True)
            except RuntimeError:
                pass
    return bpy.data.fonts.load("<builtin>")


def text_mask(size, lines, font=None, bold=0.0):
    """White-on-black mask of some lines of text. `size` is (width, height) in
    pixels; each line is (text, x, y, height, align, spacing), with x a fraction
    of the picture's width and y and height fractions of its height, measured
    from the bottom left. `font` is a file name from config.FONTS (default Inter).
    `bold` thickens every stroke by that many pixels on each side (`embolden`), for a
    heavier face than the font has. (Blender's own text offset does this badly: it drops
    the tail of a Q and the bar of an A, and leaves stray lines through words.)"""
    import bpy
    w, h = size
    scene = bpy.data.scenes.new("label_mask")
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.single_color = (1.0, 1.0, 1.0)
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("label_black")
    scene.world.color = (0.0, 0.0, 0.0)
    scene.display.render_aa = "32"

    cam = bpy.data.cameras.new("label_cam")
    cam.type = "ORTHO"
    cam.ortho_scale = w / h                    # the frame is (w/h) wide and 1 tall
    if w < h:
        # (Blender's ortho scale spans the longer side, so a portrait picture needs it
        # pinned to the height; landscape ones are left exactly as they were)
        cam.sensor_fit = "VERTICAL"
        cam.ortho_scale = 1.0
    cam_ob = bpy.data.objects.new("label_cam", cam)
    cam_ob.location = (w / h / 2, 0.5, 5.0)
    scene.collection.objects.link(cam_ob)
    scene.camera = cam_ob

    font = _font(font)
    made = []
    for text, x, y, height, align, spacing in lines:
        curve = bpy.data.curves.new("label_text", "FONT")
        curve.body = text
        curve.font = font
        curve.size = height
        curve.align_x = align
        curve.space_character = spacing
        ob = bpy.data.objects.new("label_text", curve)
        ob.location = (x * w / h, y, 0.0)          # x is a fraction of the width
        scene.collection.objects.link(ob)
        made.append((ob, curve))
    with tempfile.TemporaryDirectory() as tmp:
        scene.render.filepath = str(Path(tmp) / "mask.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
        mask = load_pixels(Path(tmp) / "mask.png")[..., 0].astype(np.float64)
    for ob, curve in made:
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(curve)
    bpy.data.objects.remove(cam_ob)
    bpy.data.cameras.remove(cam)
    bpy.data.worlds.remove(scene.world)
    bpy.data.scenes.remove(scene)
    return embolden(mask, bold) if bold else mask      # bottom row first, like load_pixels


def embolden(mask, r):
    """Grow a text mask's strokes by r pixels all round (a round, anti-aliased dilation)."""
    out = mask.copy()
    n = int(r + 1)
    h, w = mask.shape
    for dy in range(-n, n + 1):
        for dx in range(-n, n + 1):
            d = (dx * dx + dy * dy) ** 0.5
            k = min(1.0, max(0.0, r + 0.5 - d))
            if k <= 0 or (dx == 0 and dy == 0):
                continue
            shifted = np.zeros_like(mask)
            shifted[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = \
                mask[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
            out = np.maximum(out, shifted * k)
    return out


def _paper(shape, base, rng, fibres=0.0):
    h, w = shape
    img = np.ones((h, w, 3)) * base
    grain = rng.standard_normal((h, w)) * 0.012
    img *= (1 + grain)[..., None]
    if fibres:
        for _ in range(int(fibres)):
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            a = rng.uniform(0, math.pi)
            length = rng.uniform(8, 40)
            for t in np.linspace(0, 1, int(length)):
                px, py = int(x + math.cos(a) * length * t), int(y + math.sin(a) * length * t)
                if 0 <= px < w and 0 <= py < h:
                    img[py, px] *= 0.93
    return img


def paint_card(size=(768, 480)):
    """The contact card: cream stock, a fine terracotta rule, the name, then the
    contact lines. The text comes from config.CONTACT_CARD."""
    rng = np.random.default_rng(5)
    w, h = size
    spec = C.CONTACT_CARD
    img = _paper((h, w), np.array([0.95, 0.935, 0.895]), rng)
    ink = np.array([0.13, 0.12, 0.11])
    rule = np.array([0.66, 0.38, 0.26])
    lines = [(spec["name"].upper(), 0.11, 0.62, 0.15, "LEFT", 1.25)]
    for i, line in enumerate(spec["lines"]):
        lines.append((line, 0.11, 0.37 - i * 0.105, 0.075, "LEFT", 1.05))
    mask = text_mask(size, lines)
    # the rule under the name
    y0 = int(h * 0.555)
    img[y0:y0 + 3, int(w * 0.07):int(w * 0.36)] = rule
    img = img * (1 - mask[..., None]) + ink * mask[..., None]
    save_png(picture_path("contact_card"), np.clip(img, 0, 1).astype(np.float32))


def paint_sake_label(size=(512, 384)):
    """An original sake label: washi paper, a brushed ensō circle in indigo ink,
    a small red seal, and a made-up brewery name."""
    rng = np.random.default_rng(12)
    w, h = size
    img = _paper((h, w), np.array([0.93, 0.90, 0.82]), rng, fibres=260)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    # the ensō: a ring of ink, thick where the brush lands, fading and dry where it lifts
    cx, cy, r = w * 0.5, h * 0.60, h * 0.25
    ang = np.arctan2(yy - cy, xx - cx)
    t = ((ang + math.pi * 0.62) % (2 * math.pi)) / (2 * math.pi)        # 0 where the stroke starts
    width = h * (0.050 * (1 - t) ** 0.6 + 0.008) * (t < 0.93)
    dist = np.abs(np.hypot(xx - cx, yy - cy) - r * (1 + 0.04 * np.sin(ang * 3 + 1)))
    dry = rng.random((h, w)) < (0.15 + 0.6 * t ** 2)
    ink = np.clip((width - dist) / 2.0, 0, 1) * ~dry
    indigo = np.array([0.10, 0.11, 0.18])
    img = img * (1 - ink[..., None]) + indigo * ink[..., None]
    # a small vermilion seal with an abstract mark cut into it
    sx0, sy0, s = int(w * 0.70), int(h * 0.30), int(h * 0.10)
    seal = np.zeros((h, w), bool)
    seal[sy0:sy0 + s, sx0:sx0 + s] = True
    inner = np.zeros_like(seal)
    m = s // 5
    inner[sy0 + m:sy0 + s - m, sx0 + 2 * m:sx0 + 2 * m + max(2, m // 2)] = True
    inner[sy0 + 2 * m:sy0 + 2 * m + max(2, m // 2), sx0 + m:sx0 + s - m] = True
    img[seal & ~inner] = np.array([0.72, 0.16, 0.10])
    # the name and the grade, in Latin letters
    mask = text_mask(size, [("SUNAKAZE", 0.5, 0.13, 0.13, "CENTER", 1.4),
                            ("JUNMAI DAIGINJO  ·  720 ml", 0.5, 0.045, 0.05, "CENTER", 1.15)])
    img = img * (1 - mask[..., None]) + np.array([0.11, 0.10, 0.10]) * mask[..., None]
    save_png(picture_path("sake_label"), np.clip(img, 0, 1).astype(np.float32))
