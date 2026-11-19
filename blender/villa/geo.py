"""Mesh building helpers.

The house is almost entirely flat rectangles, so instead of modelling by hand the
scripts describe it as boxes and quads and this module turns them into meshes.
It also does two jobs that would be tedious in Blender's UI:

  * throws away faces nobody can ever see (a wall end buried in another wall),
  * lays out the lightmap UVs, giving every face its own rectangle in an atlas.

Faces are grouped into "parts". A part becomes one Blender object, named
"<group>__<what>": the group is which bit of the house it shows and hides with
on the website (ground, upper, roof, out), and the second half says how it is
lit (a lightmap atlas name, "vtx" for per-vertex light, or "raw" for none).

Furniture is built inside `with b.room("dining"):`. Its parts are kept apart
from the house's ("dining__ground__vtx" and so on) because each furnished room
is exported as its own file, which the website loads after the first view.
"""
from collections import defaultdict
from contextlib import contextmanager
from math import ceil

import bpy
import numpy as np

from . import config as C
from .materials import MATS

FACES = ("+x", "-x", "+y", "-y", "+z", "-z")


def to_blender(p):
    """Site coordinates (y up, z toward the driveway) to Blender's (z up)."""
    return (p[0], -p[2], p[1])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dist(a, b):
    d = _sub(a, b)
    return (d[0] * d[0] + d[1] * d[1] + d[2] * d[2]) ** 0.5


class Part:
    def __init__(self, name, group, mode, atlas, room=None, attach=None):
        self.name, self.group, self.mode, self.atlas, self.room = name, group, mode, atlas, room
        self.attach = attach
        self.verts, self.faces, self.mats = [], [], []
        self.uv0, self.uv1, self.smooth = [], [], []
        self.colors = {}                 # vertex index -> linear colour, for surfaces painted per vertex
        self.dead = set()


class Builder:
    def __init__(self):
        self.parts = {}
        self.rects = defaultdict(list)   # atlas -> [(part, face, width m, height m, density factor)]
        self.solids = []                 # boxes that can hide other faces
        self._maybe_hidden = []          # (part, face, four corners)
        self.densities = {}
        self.atlas_rects = {}            # atlas -> [(x, y, w, h)] in texels, for the bake's hole filling
        self.current_room = None
        self.current_attach = None

    @contextmanager
    def attached(self, name):
        """Everything added inside this block is kept in its own objects, tagged
        attach=name. "camera" means the website carries it along with the camera
        (the visitor's hand at the pool)."""
        old, self.current_attach = self.current_attach, name
        try:
            yield self
        finally:
            self.current_attach = old

    @contextmanager
    def room(self, name):
        """Everything added inside this block belongs to that room's furniture."""
        old, self.current_room = self.current_room, name
        try:
            yield self
        finally:
            self.current_room = old

    # ---- adding geometry ---------------------------------------------------
    def part(self, group, mat, atlas=None):
        kind = MATS[mat]["kind"]
        if kind == "baked":
            if atlas is None:
                raise ValueError(f"'{mat}' is lit by a lightmap, so it needs an atlas")
            key, mode = f"{group}__{atlas}", "lightmap"
        elif kind in ("vertex", "sheer"):
            key, mode, atlas = f"{group}__vtx", "vertex", None
        else:
            key, mode, atlas = f"{group}__raw", "raw", None
        room = self.current_room
        if room:
            key = f"{room}__{key}"
            if atlas and C.ATLASES[atlas].get("room") != room:
                raise ValueError(f"{room} furniture should use its own lightmap, not '{atlas}'")
        elif atlas and C.ATLASES[atlas].get("room"):
            raise ValueError(f"lightmap '{atlas}' belongs to a room; build inside `with b.room(...)`")
        if self.current_attach:
            key = f"{key}__{self.current_attach}"
        if key not in self.parts:
            self.parts[key] = Part(key, group, mode, atlas, room, self.current_attach)
        return self.parts[key]

    def quad(self, group, mat, pts, atlas=None, density=1.0, rot=False, cull=False, uv=None):
        """One rectangle. `pts` are its four corners, anticlockwise seen from the front.
        `uv` gives the texture coordinates of the corners instead of tiling in metres
        (for pictures and rugs, where one image covers the whole face)."""
        part = self.part(group, mat, atlas)
        i = len(part.verts)
        part.verts.extend(pts)
        f = len(part.faces)
        part.faces.append((i, i + 1, i + 2, i + 3))
        part.mats.append(mat)
        part.smooth.append(False)
        part.uv0.append(list(uv) if uv else self._texture_uv(pts, mat, rot))
        part.uv1.append(None)
        if part.mode == "lightmap":
            self.rects[part.atlas].append((part, f, _dist(pts[0], pts[1]), _dist(pts[0], pts[3]), density))
        if cull:
            self._maybe_hidden.append((part, f, pts))
        return part, f

    @staticmethod
    def _texture_uv(pts, mat, rot):
        # Textures are laid flat against whichever axis the face looks along, in
        # world metres, so the pattern lines up across neighbouring faces.
        n = _cross(_sub(pts[1], pts[0]), _sub(pts[3], pts[0]))
        axis = max(range(3), key=lambda k: abs(n[k]))
        tile = MATS[mat].get("tile", 1.0)
        out = []
        for p in pts:
            u, v = ((p[2], p[1]), (p[0], p[2]), (p[0], p[1]))[axis]
            if rot:
                u, v = v, u
            out.append((u / tile, v / tile))
        return out

    def box(self, group, mat, x, y, z, atlas=None, skip=(), over=None, density=1.0,
            solid=True, cull=True, rot=False):
        """A box between two corners. `over` changes single faces, for example
        over={"+z": dict(mat="stone", atlas="ext")}. `skip` leaves faces out."""
        x0, x1 = sorted(x)
        y0, y1 = sorted(y)
        z0, z1 = sorted(z)
        corners = {
            "+x": [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
            "-x": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            "+y": [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
            "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            "-z": [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        }
        over = over or {}
        for name in FACES:
            if name in skip:
                continue
            o = dict(mat=mat, atlas=atlas, density=density, rot=rot, uv=None)
            o.update(over.get(name, {}))
            # "cut" faces are the wall tops you see when the roof lifts off, so
            # they must survive even though a slab normally sits on them.
            self.quad(group, o["mat"], corners[name], o["atlas"], o["density"], o["rot"],
                      cull=cull and o["mat"] != "cut", uv=o["uv"])
        if solid:
            self.solids.append((x0, x1, y0, y1, z0, z1))

    def floor(self, group, mat, atlas, x, z, y, density=1.0, rot=False):
        """A flat rectangle facing up."""
        (x0, x1), (z0, z1) = sorted(x), sorted(z)
        return self.quad(group, mat, [(x0, y, z1), (x1, y, z1), (x1, y, z0), (x0, y, z0)], atlas, density, rot)

    def ceiling(self, group, mat, atlas, x, z, y, density=1.0, rot=False):
        """A flat rectangle facing down."""
        (x0, x1), (z0, z1) = sorted(x), sorted(z)
        return self.quad(group, mat, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], atlas, density, rot)

    def mesh(self, group, mat, verts, faces, smooth=True, uvs=None, colors=None):
        """Any other shape (plants, rocks, furniture). Only for materials lit per
        vertex. `uvs`, if given, has one list of (u, v) per face, one pair per corner,
        for materials with a picture on them. `colors`, if given, is a colour per
        vertex (linear), painted onto surfaces whose material says "albedo"."""
        part = self.part(group, mat)
        if part.mode == "lightmap":
            raise ValueError("free-form meshes cannot use a lightmap material")
        i = len(part.verts)
        part.verts.extend(verts)
        if colors is not None:
            for n, c in enumerate(colors):
                part.colors[i + n] = tuple(c)
        for n, f in enumerate(faces):
            part.faces.append(tuple(i + k for k in f))
            part.mats.append(mat)
            part.smooth.append(smooth)
            part.uv0.append(list(uvs[n]) if uvs is not None else [(0.0, 0.0)] * len(f))
            part.uv1.append(None)

    # ---- finishing ---------------------------------------------------------
    def _drop_hidden_faces(self):
        """Remove faces that sit completely inside or against another solid box."""
        if not self._maybe_hidden or not self.solids:
            return 0
        solids = np.array(self.solids, dtype=np.float64)
        samples = []
        for _part, _f, pts in self._maybe_hidden:
            p = np.array(pts, dtype=np.float64)
            n = np.cross(p[1] - p[0], p[3] - p[0])
            n /= np.linalg.norm(n)
            centre = p.mean(axis=0)
            # the centre and a point near each corner, nudged 2 mm off the face
            samples.append(np.vstack([centre, centre + (p - centre) * 0.8]) + n * 0.002)
        pts = np.concatenate(samples)                      # (faces * 5, 3)
        eps = 1e-4
        hidden = np.zeros(len(pts), dtype=bool)
        for start in range(0, len(pts), 4000):
            q = pts[start:start + 4000, None, :]
            inside = ((q[..., 0] > solids[:, 0] + eps) & (q[..., 0] < solids[:, 1] - eps) &
                      (q[..., 1] > solids[:, 2] + eps) & (q[..., 1] < solids[:, 3] - eps) &
                      (q[..., 2] > solids[:, 4] + eps) & (q[..., 2] < solids[:, 5] - eps))
            hidden[start:start + 4000] = inside.any(axis=1)
        hidden = hidden.reshape(-1, 5).all(axis=1)
        for (part, f, _pts), h in zip(self._maybe_hidden, hidden):
            if h:
                part.dead.add(f)
        return int(hidden.sum())

    def _pack(self, atlas):
        """Give every lightmapped face a rectangle in the atlas. Returns texels per metre."""
        spec = C.ATLASES[atlas]
        size, pad = spec["size"], C.ATLAS_PADDING
        items = [r for r in self.rects[atlas] if r[1] not in r[0].dead]
        limit = size - 2 * pad
        density = spec["density"]
        while True:
            boxes = []
            for _part, _f, w, h, factor in items:
                pw = min(limit, max(4, ceil(w * density * factor)))
                ph = min(limit, max(4, ceil(h * density * factor)))
                boxes.append((ph, pw, True) if ph > pw else (pw, ph, False))   # lay tall ones on their side
            placed = _shelf_pack([(b[0], b[1]) for b in boxes], size, pad)
            if placed is not None:
                break
            density *= 0.97
        self.atlas_rects[atlas] = [(x, y, bw, bh) for (bw, bh, _t), (x, y) in zip(boxes, placed)]
        for (part, f, _w, _h, _factor), (bw, bh, turned), (x, y) in zip(items, boxes, placed):
            # Corners sit just outside the outermost texel centres: every texel in the
            # rectangle gets baked, and filtering never reaches the neighbours.
            u0, u1 = (x + 0.48) / size, (x + bw - 0.48) / size
            v0, v1 = (y + 0.48) / size, (y + bh - 0.48) / size
            part.uv1[f] = ([(u0, v0), (u0, v1), (u1, v1), (u1, v0)] if turned
                           else [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        return density

    def finalize(self, collection, materials):
        """Turn everything into Blender objects. `materials` maps names to bpy materials."""
        dropped = self._drop_hidden_faces()
        for atlas in self.rects:
            self.densities[atlas] = self._pack(atlas)
        objects = {}
        for part in self.parts.values():
            keep = [f for f in range(len(part.faces)) if f not in part.dead]
            if not keep:
                continue
            remap, verts, faces = {}, [], []
            for f in keep:
                face = []
                for v in part.faces[f]:
                    if v not in remap:
                        remap[v] = len(verts)
                        verts.append(to_blender(part.verts[v]))
                    face.append(remap[v])
                faces.append(face)
            me = bpy.data.meshes.new(part.name)
            me.from_pydata(verts, [], faces)

            names = sorted({part.mats[f] for f in keep})
            for n in names:
                me.materials.append(materials[n])
            me.polygons.foreach_set("material_index", [names.index(part.mats[f]) for f in keep])
            me.polygons.foreach_set("use_smooth", [part.smooth[f] for f in keep])

            uv = me.uv_layers.new(name="UVMap")
            uv.data.foreach_set("uv", [c for f in keep for pair in part.uv0[f] for c in pair])
            if part.mode == "lightmap":
                lm = me.uv_layers.new(name="Lightmap")
                lm.data.foreach_set("uv", [c for f in keep for pair in part.uv1[f] for c in pair])
                uv.active_render = True
            elif part.mode == "vertex":
                me.color_attributes.new(name="Light", type="FLOAT_COLOR", domain="POINT")
            if part.colors:
                # surface colour painted per vertex; the bake folds it into the light
                rgba = np.ones((len(verts), 4), dtype=np.float32)
                for old, new in remap.items():
                    if old in part.colors:
                        rgba[new, :3] = part.colors[old]
                albedo = me.color_attributes.new(name="Albedo", type="FLOAT_COLOR", domain="POINT")
                albedo.data.foreach_set("color", rgba.ravel())
                if part.mode == "vertex":
                    me.color_attributes.active_color = me.color_attributes["Light"]
            me.update()

            ob = bpy.data.objects.new(part.name, me)
            ob["group"] = part.group
            ob["lit"] = part.mode
            if part.atlas:
                ob["lightmap"] = part.atlas
            if part.room:
                ob["room"] = part.room
            if part.attach:
                ob["attach"] = part.attach
            collection.objects.link(ob)
            objects[part.name] = ob
        print(f"[geo] {len(objects)} objects, {dropped} hidden faces dropped, lightmap texels per metre: "
              + ", ".join(f"{a} {d:.1f}" for a, d in self.densities.items()))
        return objects


def _shelf_pack(boxes, size, pad):
    """Simple row packing: tallest first, left to right. Returns positions or None."""
    order = sorted(range(len(boxes)), key=lambda i: (-boxes[i][1], -boxes[i][0]))
    pos = [None] * len(boxes)
    x = y = pad
    row_h = 0
    for i in order:
        w, h = boxes[i]
        if x + w + pad > size:
            x, y, row_h = pad, y + row_h + pad, 0
        if y + h + pad > size:
            return None
        pos[i] = (x, y)
        x += w + pad
        row_h = max(row_h, h)
    return pos
