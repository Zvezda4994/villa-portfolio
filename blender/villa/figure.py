"""The figure at the dining table: a model you supply (config.FIGURE), seated
in the chair across the board from the visitor.

It is kept apart from everything else so it can come down in minutes:

  * it has its own file, web/assets/figures/opponent.glb, and its own pictures
    (textures/figure_*.ktx2), listed under "figures" in the manifest together
    with its credit, which the dining room panel shows;
  * it is lit per vertex after the room's bake and is left out of the room's
    lightmaps, so removing it leaves no shadow behind and needs no re-bake.

`export_figure` runs at the end of export_web.py and on its own as
`npm run figure`. With FIGURE = None it removes the figure and its credit.
The build never downloads a figure; the file has to be put in assets_src/ by hand.
"""
import json
import math

import numpy as np

from . import config as C
from .dining import OPPONENT_CHAIR, ROOM
from .geo import to_blender

NAME = "opponent"
MODEL = f"figures/{NAME}.glb"
PREFIX = "figure_"               # its materials and pictures are named figure_0, figure_1...
PICTURE_SIZE = 512
SEAT_BACK = -0.43                # the chair's back cushion, in the chair's own frame (it faces +z)


def remove(manifest):
    """Delete the figure's files and every mention of it in the manifest."""
    (C.ASSETS / MODEL).unlink(missing_ok=True)
    for old in (C.ASSETS / "textures").glob(f"{PREFIX}*.ktx2"):
        old.unlink()
    manifest.pop("figures", None)
    for key in [k for k in manifest["materials"] if k.startswith(PREFIX)]:
        del manifest["materials"][key]
    for key in [k for k in manifest["bytes"] if k.startswith("figure ")]:
        del manifest["bytes"][key]
    return manifest


def _check(spec):
    src = C.ROOT / "assets_src" / spec["file"]
    if not src.exists():
        raise SystemExit(f"config.FIGURE names {src}, which isn't there.")
    if not str(spec.get("credit", "")).strip():
        raise SystemExit("config.FIGURE needs a credit line: the figure is never shown without one.")
    if not str(spec.get("link", "")).startswith("https://"):
        raise SystemExit("config.FIGURE needs a link (https://...) to the model's page, for the credit.")
    return src


def _import(src, spec):
    """Import the file, pose it, thin it, and return (meshes, materials), where
    meshes are (points in site coordinates, faces, corner UVs, material index per
    face) and materials are Blender materials in index order."""
    import bpy

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(src))
    new = [o for o in bpy.data.objects if o not in before]
    scene = bpy.context.scene
    for ob in new:
        if ob.type == "ARMATURE" and ob.animation_data:
            # the file's own pose unless an animation is named
            ob.animation_data.action = bpy.data.actions.get(spec["action"]) if spec.get("action") else None
    scene.frame_set(int(spec.get("frame", 1)))

    meshes_in = [o for o in new if o.type == "MESH"]
    total = sum(len(p.vertices) - 2 for o in meshes_in for p in o.data.polygons)
    keep = min(1.0, spec.get("max_triangles", 60000) / max(total, 1))
    if keep < 1.0:
        for ob in meshes_in:
            mod = ob.modifiers.new("thin", "DECIMATE")       # after any armature, so it thins the posed shape
            mod.ratio = keep

    depsgraph = bpy.context.evaluated_depsgraph_get()
    mats, meshes = [], []
    for ob in meshes_in:
        ev = ob.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        verts = [(p.x, p.z, -p.y) for p in (mw @ v.co for v in me.vertices)]
        uv = me.uv_layers.active
        slots = []
        for slot in ob.material_slots:
            m = slot.material
            if m not in mats:
                mats.append(m)
            slots.append(mats.index(m))
        if not slots:
            if None not in mats:
                mats.append(None)
            slots.append(mats.index(None))
        faces, uvs, which = [], [], []
        for poly in me.polygons:
            faces.append(tuple(poly.vertices))
            uvs.append([tuple(uv.data[i].uv) for i in poly.loop_indices] if uv else [(0.0, 0.0)] * poly.loop_total)
            which.append(slots[min(poly.material_index, len(slots) - 1)])
        meshes.append((verts, faces, uvs, which))
        ev.to_mesh_clear()
    print(f"[figure] {total} triangles in the file, kept {keep:.0%}")
    return new, meshes, mats


def _base_colour(mat):
    """(image or None, linear colour) from a material's Principled BSDF."""
    if mat is None or not mat.node_tree:
        return None, (0.8, 0.8, 0.8)
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return None, (0.8, 0.8, 0.8)
    sock = bsdf.inputs["Base Color"]
    # follow the link back to the first picture (through mixes, tints and so on)
    todo, seen = [l.from_node for l in sock.links], set()
    while todo:
        node = todo.pop(0)
        if node in seen:
            continue
        seen.add(node)
        if node.type == "TEX_IMAGE" and node.image:
            return node.image, (1.0, 1.0, 1.0)
        for inp in node.inputs:
            todo += [l.from_node for l in inp.links]
    return None, tuple(sock.default_value[:3])


def _picture(image):
    """The image at no more than PICTURE_SIZE, both sides multiples of 4, as sRGB values."""
    w, h = image.size
    k = min(1.0, PICTURE_SIZE / max(w, h))
    nw, nh = max(4, int(w * k) // 4 * 4), max(4, int(h * k) // 4 * 4)
    copy = image.copy()
    copy.scale(nw, nh)
    px = np.empty(nw * nh * 4, dtype=np.float32)
    copy.pixels.foreach_get(px)
    import bpy
    bpy.data.images.remove(copy)
    rgb = px.reshape(nh, nw, 4)[..., :3]
    if image.is_float:                      # float images hold linear light; KTX2 wants sRGB values
        from .textures import to_srgb
        rgb = to_srgb(rgb).astype(np.float32)
    return rgb


def _place(meshes, spec):
    """Scale to the seated height and sit it in the opponent's chair."""
    pts = np.array([p for verts, *_ in meshes for p in verts])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    scale = spec.get("height", 1.30) / max(hi[1] - lo[1], 1e-6)
    anchor = np.array([(lo[0] + hi[0]) / 2, lo[1], lo[2]])       # bottom of its back, in the middle
    turn = math.radians(spec.get("turn", 0.0))
    ox, oy, oz = spec.get("offset", (0.0, 0.0, 0.0))
    yaw = OPPONENT_CHAIR["yaw"]
    cx, cy, cz = OPPONENT_CHAIR["pos"]
    out = []
    for verts, faces, uvs, which in meshes:
        p = (np.array(verts) - anchor) * scale
        # its own turn, then into the chair's frame (back against the cushion), then the chair's turn
        x = p[:, 0] * math.cos(turn) + p[:, 2] * math.sin(turn)
        z = -p[:, 0] * math.sin(turn) + p[:, 2] * math.cos(turn)
        x, y, z = x + ox, p[:, 1] + oy, z + SEAT_BACK + oz
        wx = cx + x * math.cos(yaw) + z * math.sin(yaw)
        wz = cz - x * math.sin(yaw) + z * math.cos(yaw)
        out.append((list(zip(wx, y + cy, wz)), faces, uvs, which))
    return out, scale


def _write_glb(ob, path):
    import bpy
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True, export_yup=True,
        export_extras=True, export_cameras=False, export_lights=False, export_animations=False,
        export_image_format="NONE", export_materials="EXPORT", export_normals=False, export_tangents=False,
        export_vertex_color="ACTIVE", export_all_vertex_colors=False,
        export_meshopt_compression_enable=True)


def export_figure(manifest_path, samples=128):
    """Add, update or remove the figure. Needs the baked scene open when adding."""
    import bpy
    from .ktx2 import write_ktx2

    manifest = remove(json.loads(manifest_path.read_text()))
    spec = C.FIGURE
    if not spec:
        manifest_path.write_text(json.dumps(manifest, indent=1))
        print("[figure] none set (config.FIGURE is None); any old figure and its credit are removed")
        return manifest
    src = _check(spec)

    imported, meshes, mats = _import(src, spec)
    placed, scale = _place(meshes, spec)

    # One mesh for the whole figure, in Blender's axes, with its own materials.
    verts, faces, uvs, which = [], [], [], []
    for v, f, u, w in placed:
        base = len(verts)
        verts += [to_blender(p) for p in v]
        faces += [tuple(base + i for i in face) for face in f]
        uvs += u
        which += w
    me = bpy.data.meshes.new(f"{ROOM}__ground__figure")
    me.from_pydata(verts, [], faces)
    entries, sizes = {}, {}
    for i, m in enumerate(mats):
        name = f"{PREFIX}{i}"
        image, colour = _base_colour(m)
        mat = bpy.data.materials.new(name)
        if mat.node_tree is None:
            mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
        entry = dict(kind="vertex", room=ROOM, color=list(colour), doubleSided=True)
        if image is not None:
            rgb = _picture(image)
            sizes[f"figure texture {i}"] = write_ktx2(C.ASSETS / "textures" / f"{name}.ktx2", rgb, srgb=True)
            entry["map"] = f"textures/{name}.ktx2"
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = image
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        else:
            bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
        me.materials.append(mat)
        entries[name] = entry
    me.polygons.foreach_set("material_index", which)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    layer = me.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", [c for corners in uvs for pair in corners for c in pair])
    me.color_attributes.new(name="Light", type="FLOAT_COLOR", domain="POINT")
    me.update()

    ob = bpy.data.objects.new(me.name, me)
    ob["group"], ob["lit"], ob["room"], ob["figure"] = "ground", "vertex", ROOM, NAME
    coll = bpy.data.collections.new("figure")
    bpy.context.scene.collection.children.link(coll)
    coll.objects.link(ob)
    for o in imported:
        bpy.data.objects.remove(o)

    # Its light, baked per vertex like the room's other curved things.
    scene = bpy.context.scene
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    attrs = me.color_attributes
    attrs.active_color = attrs["Light"]
    attrs.render_color_index = list(attrs).index(attrs["Light"])
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, target="VERTEX_COLORS")
    data = attrs["Light"].data
    col = np.empty(len(data) * 4, dtype=np.float32)
    data.foreach_get("color", col)
    col = col.reshape(-1, 4)
    col[:, :3] = np.clip(col[:, :3] / C.LIGHT_RANGE, 0.0, 1.0)
    col[:, 3] = 1.0
    data.foreach_set("color", col.ravel())

    _write_glb(ob, C.ASSETS / MODEL)
    sizes["figure model"] = (C.ASSETS / MODEL).stat().st_size
    manifest["materials"].update(entries)
    manifest["bytes"].update(sizes)
    manifest["figures"] = {NAME: dict(model=MODEL, room=ROOM, credit=spec["credit"].strip(), link=spec["link"])}
    manifest_path.write_text(json.dumps(manifest, indent=1))
    tris = sum(len(f) - 2 for f in faces)
    print(f"[figure] {src.name}: {tris} triangles, scaled x{scale:.3f}, {len(mats)} materials, "
          f"{sum(sizes.values()) / 1e6:.2f} MB, credit: {spec['credit'].strip()}")
    return manifest
