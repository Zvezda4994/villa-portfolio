"""Write KTX2 textures (the GPU-friendly format the website loads).

Blender ships a KTX2 encoder for its glTF exporter. It writes one image at one
size, with no mipmaps, and tiled textures shimmer badly without mipmaps. So
each smaller size is encoded separately and the pieces are stitched into one
file here. The format allows that because every mip level is stored on its own.
"""
import struct
import tempfile
from pathlib import Path

import numpy as np

_state = {}        # the encoder keeps its loaded library in here
MAGIC = b"\xabKTX 20\xbb\r\n\x1a\n"


def _encode_level(pixels, srgb):
    """Encode one image, return (level bytes, uncompressed size, header fields, dfd, kvd)."""
    from io_scene_gltf2.io.exp.ktx import KtxEncoder      # Blender's own; imported here so write_smaller works outside Blender

    h, w = pixels.shape[:2]
    rgba = np.concatenate([pixels[..., :3], np.ones((h, w, 1), dtype=np.float32)], axis=2).astype(np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "level.ktx2"
        # UASTC keeps smooth gradients clean; Zstandard on top makes the file smaller.
        code = KtxEncoder.encode_file(_state, path, rgba.ravel(), w, h, 4, quality=255,
                                      is_data=not srgb, use_uastc=True, compress=18)
        if code != 0:
            raise RuntimeError(f"KTX2 encoder failed with code {code}")
        data = path.read_bytes()
    if data[:12] != MAGIC:
        raise RuntimeError("encoder did not write a KTX2 file")
    head = struct.unpack_from("<9I", data, 12)                    # vkFormat ... supercompressionScheme
    dfd_off, dfd_len, kvd_off, kvd_len = struct.unpack_from("<4I", data, 48)
    sgd_len = struct.unpack_from("<Q", data, 72)[0]
    if head[7] != 1 or sgd_len != 0:
        raise RuntimeError("unexpected KTX2 layout from the encoder")
    off, length, raw = struct.unpack_from("<3Q", data, 80)
    return data[off:off + length], raw, head, data[dfd_off:dfd_off + dfd_len], data[kvd_off:kvd_off + kvd_len]


def _halve(a):
    h, w = a.shape[:2]
    return a.reshape(h // 2, 2, w // 2, 2, -1).mean(axis=(1, 3))


def write_ktx2(path, pixels, srgb=True, max_levels=99):
    """Save `pixels` (height, width, 3; values 0..1; bottom row first) as KTX2.

    If srgb is true the values are sRGB-encoded colour and mipmaps are averaged
    in linear light. Sizes must be multiples of 4, so the chain stops at 4 px.
    Returns the file size in bytes.
    """
    from .textures import to_linear, to_srgb

    level = np.asarray(pixels, dtype=np.float64)[..., :3]
    lin = to_linear(level) if srgb else level
    levels = []
    while len(levels) < max_levels:
        h, w = lin.shape[:2]
        img = (to_srgb(lin) if srgb else lin).astype(np.float32)
        levels.append(_encode_level(img, srgb))
        if h % 8 or w % 8:            # the next one down would not be a multiple of 4
            break
        lin = _halve(lin)

    _blob, _raw, head, dfd, kvd = levels[0]
    out = _assemble(head, dfd, kvd, [lv[:2] for lv in levels])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(out)
    return len(out)


def _assemble(head, dfd, kvd, levels):
    """One KTX2 file from its header fields, data format and key/value blocks, and its
    levels [(bytes, uncompressed size)], largest first."""
    count = len(levels)
    dfd_off = 80 + 24 * count
    kvd_off = dfd_off + len(dfd)
    pos = (kvd_off + len(kvd) + 7) // 8 * 8
    # Smallest level is stored first in the file, though the index lists the largest first.
    index = [None] * count
    body = bytearray()
    for i in range(count - 1, -1, -1):
        blob, raw = levels[i]
        pad = (-(pos + len(body))) % 8
        body += b"\0" * pad
        index[i] = (pos + len(body), len(blob), raw)
        body += blob

    out = bytearray(MAGIC)
    out += struct.pack("<9I", head[0], head[1], head[2], head[3], head[4], head[5], head[6], count, head[8])
    out += struct.pack("<4I", dfd_off, len(dfd), kvd_off if kvd else 0, len(kvd))
    out += struct.pack("<2Q", 0, 0)
    for entry in index:
        out += struct.pack("<3Q", *entry)
    out += dfd + kvd
    out += b"\0" * (pos - len(out))
    out += body
    return out


def write_smaller(src, dst, max_px):
    """Copy the KTX2 file `src` to `dst` without its mip levels wider or taller than
    max_px. The smaller levels are already in the file, so nothing is encoded again,
    and the result is exactly what encoding the picture at that size would give.
    Returns the new file's size, or None if `src` is no bigger than max_px."""
    data = Path(src).read_bytes()
    if data[:12] != MAGIC:
        raise ValueError(f"{src} is not a KTX2 file")
    head = list(struct.unpack_from("<9I", data, 12))
    dfd_off, dfd_len, kvd_off, kvd_len = struct.unpack_from("<4I", data, 48)
    sgd_len = struct.unpack_from("<Q", data, 72)[0]
    if sgd_len:
        raise ValueError(f"{src}: only Zstandard or uncompressed levels can be dropped")
    count = head[7]
    index = [struct.unpack_from("<3Q", data, 80 + 24 * i) for i in range(count)]
    drop = 0
    while drop < count - 1 and max(head[2] >> drop, head[3] >> drop) > max_px:
        drop += 1
    if drop == 0:
        return None
    head[2] >>= drop
    head[3] >>= drop
    levels = [(data[off:off + length], raw) for off, length, raw in index[drop:]]
    out = _assemble(head, data[dfd_off:dfd_off + dfd_len], data[kvd_off:kvd_off + kvd_len] if kvd_off else b"", levels)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(out)
    return len(out)
