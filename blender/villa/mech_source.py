"""The aquarium mech's source model, prepared once for mech.py.

The model is a download (config.MECH_MODEL, under assets_src/, never committed): one
fused, very dense mesh with a single colour texture, standing, no rig. This reads it
straight from its glTF, welds the chunks it was split into, thins it to about TRIS
triangles with Blender's decimator (keeping its UVs), and keeps each remaining point's
colour from the texture (mech.py uses the colours only to find panels and trims; it
repaints everything).

The thinning loses the armour's crisp edges, so the full-detail mesh's look is baked
onto the thin one's UVs as a grey detail picture (DETAIL): its crevices (ambient
occlusion), its sharp edges (Cycles' pointiness, lighter on edges) and the panel lines
and shading painted into its own texture. The room's lighting is baked per vertex and
the site draws these surfaces unlit, so a normal map would show nothing; this picture,
multiplied over the per-vertex colour, is what carries the detail.

The results are cached in build/mech_source.npz and build/textures/mech_detail.png and
remade only when the source changes.

Coordinates are the glTF's own: y up, the model facing +z, about 1 unit tall.
"""
import json
import struct
from pathlib import Path

import numpy as np

from . import config as C

TRIS = 120000
DETAIL = "mech_detail"      # the baked detail picture (materials.py: "mech_body")
DETAIL_SIZE = 768
CACHE = C.BUILD / "mech_source.npz"
_TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
_SIZES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def source_path():
    return C.SRC_MODELS / C.MECH_MODEL["file"] if C.MECH_MODEL else None


def load():
    """(verts, faces, colours, face corner UVs) of the thinned model, or None when no
    model is set or it hasn't been downloaded. Also makes the detail picture."""
    src = source_path()
    if src is None or not src.exists():
        return None
    from .textures import picture_path
    if CACHE.exists() and CACHE.stat().st_mtime > src.stat().st_mtime and picture_path(DETAIL).exists():
        d = np.load(CACHE)
        if int(d["tris"]) == TRIS and str(d["src"]) == str(src) and "UV" in d:
            return d["V"], d["F"], d["C"], d["UV"]
    V, F, Cs, UV = _prepare(src)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, V=V, F=F, C=Cs, UV=UV, tris=TRIS, src=str(src))
    return V, F, Cs, UV


def _accessor(g, blob, i):
    a = g["accessors"][i]
    v = g["bufferViews"][a["bufferView"]]
    n = _SIZES[a["type"]]
    dt = np.dtype(_TYPES[a["componentType"]])
    start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = v.get("byteStride", 0) or dt.itemsize * n
    if stride == dt.itemsize * n:
        arr = np.frombuffer(blob, dt, a["count"] * n, start).reshape(a["count"], n)
    else:
        raw = np.frombuffer(blob, np.uint8, stride * (a["count"] - 1) + dt.itemsize * n, start)
        arr = np.lib.stride_tricks.as_strided(raw.view(dt), (a["count"], n), (stride, dt.itemsize)).copy()
    return arr


def _read(src):
    g = json.loads(src.read_text(encoding="utf-8"))
    blob = (src.parent / g["buffers"][0]["uri"]).read_bytes()
    Vs, Fs, UVs, base = [], [], [], 0
    for mesh in g["meshes"]:
        for p in mesh["primitives"]:
            P = _accessor(g, blob, p["attributes"]["POSITION"]).astype(np.float64)
            UV = _accessor(g, blob, p["attributes"]["TEXCOORD_0"]).astype(np.float64)
            I = _accessor(g, blob, p["indices"]).astype(np.int64).reshape(-1, 3)
            Vs.append(P)
            UVs.append(UV)
            Fs.append(I + base)
            base += len(P)
    tex = g["images"][g["textures"][g["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]["uri"]
    return np.concatenate(Vs), np.concatenate(Fs), np.concatenate(UVs), src.parent / tex


def _texture(path, size=2048):
    import bpy
    img = bpy.data.images.load(str(path))
    img.scale(size, size)
    px = np.empty(size * size * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(size, size, 4)[:, :, :3]        # rows from the bottom, as glTF's v is flipped


def _prepare(src):
    import bmesh
    import bpy
    from mathutils.kdtree import KDTree

    V, F, UV, tex = _read(src)
    pix = _texture(tex)
    n = pix.shape[0]
    u = np.clip((UV[:, 0] % 1.0) * n, 0, n - 1).astype(int)
    v = np.clip((1.0 - UV[:, 1] % 1.0) * n, 0, n - 1).astype(int)
    col = pix[v, u]                                     # (the image's pixels are already sRGB values)
    # weld the chunks: points at the same place become one (UVs stay per face corner)
    key = np.round(V / 1e-5).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    W = V[first]
    Fw = inv[F]
    ok = (Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 0] != Fw[:, 2])
    Fw, corner_uv = Fw[ok], UV[F[ok]]
    print(f"[mech] source: {len(V)} points, {len(F)} triangles; welded to {len(W)}")

    scene = bpy.context.scene
    hi_me = _mesh("mech_hi", W, Fw, corner_uv)
    hi = bpy.data.objects.new("mech_hi", hi_me)
    scene.collection.objects.link(hi)
    mod = hi.modifiers.new("thin", "DECIMATE")
    mod.ratio = min(1.0, TRIS / len(Fw))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = hi.evaluated_get(dg)
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    hi.modifiers.remove(mod)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    lo_me = bpy.data.meshes.new("mech_lo")
    bm.to_mesh(lo_me)
    bm.free()
    lo = bpy.data.objects.new("mech_lo", lo_me)
    scene.collection.objects.link(lo)
    out_v = np.array([tuple(x.co) for x in lo_me.vertices])
    out_f = np.array([tuple(p.vertices) for p in lo_me.polygons])
    uvl = np.empty(len(lo_me.loops) * 2, np.float32)
    lo_me.uv_layers.active.data.foreach_get("uv", uvl)
    out_uv = uvl.reshape(-1, 3, 2)
    print(f"[mech] thinned to {len(out_v)} points, {len(out_f)} triangles")
    # each remaining point takes the colour of the nearest original point
    tree = KDTree(len(V))
    for i, p in enumerate(V):
        tree.insert(p, i)
    tree.balance()
    out_c = np.array([col[tree.find(p)[1]] for p in out_v])
    _bake_detail(hi, lo, tex)
    for ob, me in ((hi, hi_me), (lo, lo_me)):
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    return out_v, out_f, out_c, out_uv


def _mesh(name, V, F, corner_uv):
    import bpy
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.astype(np.int32).ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(0, F.size, 3, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(F), 3, np.int32))
    me.update(calc_edges=True)
    uv = me.uv_layers.new(name="UVMap")
    uv.data.foreach_set("uv", corner_uv.astype(np.float32).ravel())
    return me


def _bake_detail(hi, lo, tex):
    """Bake the full-detail mesh's crevices and edges onto the thin one's UVs, and fold in
    the shading and panel lines painted in the model's own texture. Saves DETAIL."""
    import bpy
    from .mech import classify
    from .textures import picture_path, save_png

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.device = "CPU"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("mech_world")
    scene.world.light_settings.distance = 0.03          # crevices, not whole limbs (model units)
    size = DETAIL_SIZE
    target = bpy.data.images.new("mech_detail_bake", size, size, alpha=False, float_buffer=True)
    target.colorspace_settings.name = "Non-Color"

    def material(name, emit_pointiness=False):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        if emit_pointiness:
            geo = nt.nodes.new("ShaderNodeNewGeometry")
            ramp = nt.nodes.new("ShaderNodeMapRange")       # pointiness sits close to 0.5; spread it
            ramp.inputs["From Min"].default_value = 0.40
            ramp.inputs["From Max"].default_value = 0.60
            em = nt.nodes.new("ShaderNodeEmission")
            nt.links.new(geo.outputs["Pointiness"], ramp.inputs["Value"])
            nt.links.new(ramp.outputs["Result"], em.inputs["Color"])
            nt.links.new(em.outputs[0], out.inputs["Surface"])
        else:
            bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
            nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
            node = nt.nodes.new("ShaderNodeTexImage")
            node.image = target
            nt.nodes.active = node
        return m

    hi.data.materials.clear()
    hi.data.materials.append(material("mech_hi_mat", emit_pointiness=True))
    lo.data.materials.clear()
    lo.data.materials.append(material("mech_lo_mat"))
    for ob in scene.objects:
        ob.select_set(False)
    hi.select_set(True)
    lo.select_set(True)
    bpy.context.view_layer.objects.active = lo

    def bake(kind):
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=0.004, max_ray_distance=0.02,
                            margin=6, margin_type="EXTEND")
        px = np.empty(size * size * 4, np.float32)
        target.pixels.foreach_get(px)
        return px.reshape(size, size, 4)[:, :, 0].copy()
    ao = bake("AO")
    edge = bake("EMIT")
    bpy.data.images.remove(target)
    # the model's own shading and panel lines, relative to each part's paint
    base = _texture(tex, size)
    _, shade = classify(base.reshape(-1, 3).astype(np.float64))
    shade = shade.reshape(size, size)
    detail = 0.80 * np.clip(ao, 0.2, 1.0) ** 0.6 * np.clip(shade, 0.55, 1.15) + 0.22 * np.clip((edge - 0.55) * 2.0, 0, 1)
    detail = np.clip(detail, 0.0, 1.0)
    detail[-8:, -8:] = 1.0                              # a white corner for the parts that have no picture
    srgb = np.where(detail <= 0.0031308, detail * 12.92, 1.055 * detail ** (1 / 2.4) - 0.055)
    save_png(picture_path(DETAIL), np.repeat(srgb[:, :, None], 3, axis=2).astype(np.float32))
    print(f"[mech] baked the detail picture: AO median {np.median(ao):.2f}, edges median {np.median(edge):.2f}")
