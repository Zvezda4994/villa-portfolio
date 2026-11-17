"""Read and write Radiance .hdr images (the sky files the website loads).

Blender can save .hdr itself, but in Blender 5.3 its writer changes the values
on the way out (dark parts come out several times brighter, the sun far
dimmer), so the sky looked washed out in the browser. This writes the format
directly instead. The format is simple: a short text header, then each pixel
as four bytes (red, green, blue mantissas sharing one exponent), with each row
run-length compressed.

Arrays are (height, width, 3) floats in linear light, bottom row first, the
same way Blender's image pixels are ordered.
"""
from pathlib import Path

import numpy as np


def _to_rgbe(rgb):
    """Floats to shared-exponent bytes, rounded so three.js's RGBELoader decodes
    them as closely as possible (it reads mantissa / 255 * 2^(exponent - 128))."""
    rgb = np.maximum(np.asarray(rgb, dtype=np.float64), 0.0)
    peak = rgb.max(axis=-1)
    out = np.zeros(rgb.shape[:-1] + (4,), dtype=np.uint8)
    lit = peak > 1e-30
    exp = np.ceil(np.log2(peak[lit]))
    scale = 255.0 / np.exp2(exp)
    mant = np.clip(np.rint(rgb[lit] * scale[:, None]), 0, 255)
    out[lit, :3] = mant.astype(np.uint8)
    out[lit, 3] = np.clip(exp + 128, 0, 255).astype(np.uint8)
    return out


def _from_rgbe(rgbe):
    rgbe = rgbe.astype(np.float64)
    scale = np.where(rgbe[..., 3] > 0, np.exp2(rgbe[..., 3] - 128.0) / 255.0, 0.0)
    return rgbe[..., :3] * scale[..., None]


def _encode_channel(row):
    """Run-length encode one channel of one row: runs of 3+ equal bytes become
    (128 + length, byte); everything else goes out as literal chunks of up to 128."""
    out = bytearray()
    n = len(row)
    starts = np.flatnonzero(np.diff(row, prepend=-1).astype(bool))      # where each run of equal bytes begins
    lengths = np.diff(np.append(starts, n))
    literal = bytearray()

    def flush():
        for k in range(0, len(literal), 128):
            chunk = literal[k:k + 128]
            out.append(len(chunk))
            out.extend(chunk)
        literal.clear()

    for s, length in zip(starts.tolist(), lengths.tolist()):
        if length >= 3:
            flush()
            value = int(row[s])
            while length > 0:
                take = min(length, 127)
                if take < 3:                 # a short tail is cheaper as a literal
                    literal += bytes([value]) * take
                else:
                    out += bytes((128 + take, value))
                length -= take
        else:
            literal += bytes(row[s:s + length].tolist())
    flush()
    return out


def write_hdr(path, rgb):
    """Save a linear float image as .hdr. Returns the file size in bytes."""
    rgb = np.asarray(rgb)
    h, w = rgb.shape[:2]
    if not 8 <= w < 32768:
        raise ValueError("width must be between 8 and 32767 for run-length rows")
    rgbe = _to_rgbe(rgb[::-1])                       # files store the top row first
    body = bytearray()
    for y in range(h):
        body += bytes((2, 2, w >> 8, w & 255))
        for c in range(4):
            body += _encode_channel(rgbe[y, :, c])
    head = f"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y {h} +X {w}\n".encode("ascii")
    Path(path).write_bytes(head + body)
    return len(head) + len(body)


def read_hdr(path):
    """Load a .hdr written by write_hdr (or any run-length .hdr). Bottom row first."""
    data = Path(path).read_bytes()
    end = data.index(b"\n\n") + 2
    size_line_end = data.index(b"\n", end)
    parts = data[end:size_line_end].split()
    if parts[0] != b"-Y" or parts[2] != b"+X":
        raise ValueError("only the standard top-to-bottom layout is supported")
    h, w = int(parts[1]), int(parts[3])
    pos = size_line_end + 1
    rgbe = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        if data[pos] != 2 or data[pos + 1] != 2:
            raise ValueError("expected run-length rows")
        pos += 4
        for c in range(4):
            x = 0
            while x < w:
                count = data[pos]
                pos += 1
                if count > 128:
                    count -= 128
                    rgbe[y, x:x + count, c] = data[pos]
                    pos += 1
                else:
                    rgbe[y, x:x + count, c] = np.frombuffer(data, np.uint8, count, pos)
                    pos += count
                x += count
    return _from_rgbe(rgbe)[::-1]


def check_round_trip(path, rgb):
    """Read the file back and make sure it holds what was meant. RGBE keeps about
    two and a half significant digits, so anything within 1% of the brightest
    channel of each pixel counts as a match."""
    back = read_hdr(path)
    want = np.maximum(np.asarray(rgb, dtype=np.float64), 0.0)
    peak = np.maximum(want.max(axis=-1, keepdims=True), 1e-6)
    worst = float((np.abs(back - want) / peak).max())
    if worst > 0.01:
        raise RuntimeError(f"{Path(path).name} did not read back correctly (worst error {worst:.1%})")
    return worst
