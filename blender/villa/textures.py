"""Get the downloaded textures ready for use.

Photo textures often have a soft light-to-dark drift across them. On one wall
nobody notices; repeated across hundreds of metres of sand it turns into
stripes. So each source is evened out where needed and resized, then saved to
build/textures. Blender and the website both use these prepared copies, which
keeps the bake and the browser in step.
"""
import bpy
import numpy as np

from . import config as C

# size: pixels per side on the website. flatten: how many of the lowest
# frequencies to remove (0 = leave alone).
PREP = {
    "sandy_gravel_02":           dict(size=1024, flatten=6),
    "marble_01":                 dict(size=1024, flatten=0),
    "concrete_wall_007":         dict(size=512, flatten=3),
    "oak_veneer_01":             dict(size=512, flatten=0),
    "granite_tile":              dict(size=512, flatten=0),
    "laminate_floor_02":         dict(size=512, flatten=0),
    "asphalt_02":                dict(size=512, flatten=4),
    "rounded_square_tiled_wall": dict(size=512, flatten=0),
}
OUT = C.BUILD / "textures"


def to_linear(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def to_srgb(a):
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def load_pixels(path):
    """Read an image file as a float array (height, width, 4), bottom row first."""
    img = bpy.data.images.load(str(path))
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)


def save_png(path, rgb):
    h, w = rgb.shape[:2]
    img = bpy.data.images.new("tmp_save", w, h, alpha=False)
    rgba = np.concatenate([rgb, np.ones((h, w, 1), dtype=np.float32)], axis=2).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def halve(a):
    """Shrink to half size by averaging 2x2 blocks."""
    h, w = a.shape[:2]
    return a.reshape(h // 2, 2, w // 2, 2, -1).mean(axis=(1, 3))


def flatten(lin, cut):
    """Remove slow brightness drift, keeping the average colour and all fine detail.
    Done with a Fourier transform so the result still tiles seamlessly."""
    f = np.fft.fft2(lin, axes=(0, 1))
    h, w = lin.shape[:2]
    fy = np.abs(np.fft.fftfreq(h) * h)[:, None]
    fx = np.abs(np.fft.fftfreq(w) * w)[None, :]
    low = (np.maximum(fx, fy) <= cut) & ~((fx == 0) & (fy == 0))
    f[low] = 0
    return np.clip(np.fft.ifft2(f, axes=(0, 1)).real, 0.0, None)


def prepared(tex_id):
    return OUT / f"{tex_id}.png"


def prepare_all(ids):
    """Write the prepared copy of every texture in `ids`. Returns {id: linear float array}."""
    OUT.mkdir(parents=True, exist_ok=True)
    done = {}
    for tex_id in ids:
        spec = PREP[tex_id]
        src = C.SRC_TEX / f"{tex_id}_diff_1k.jpg"
        if not src.exists():
            raise FileNotFoundError(f"{src.name} is missing. Run blender/fetch_assets.py first.")
        lin = to_linear(load_pixels(src)[..., :3].astype(np.float64))
        if spec["flatten"]:
            lin = flatten(lin, spec["flatten"])
        while lin.shape[0] > spec["size"]:
            lin = halve(lin)
        save_png(prepared(tex_id), to_srgb(lin).astype(np.float32))
        done[tex_id] = lin
    return done
