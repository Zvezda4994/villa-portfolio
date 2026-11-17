"""Ready-made models from Poly Haven (all CC0), placed in the furnished rooms.

MODEL_IDS is read by fetch_assets.py, which downloads them into
assets_src/models. The build reads them from there with `load`, which hands
back plain lists of points and faces in site coordinates (y up), and `place`
adds a copy to the scene at a position, turn and scale. Their light is baked
per vertex, like the plants outside, so their own colour pictures are kept and
multiplied by it (see "img" in materials.py).
"""
import math

MODEL_IDS = [
    "chess_set",
    "modern_wooden_cabinet",
    "ceramic_vase_02",
    "ceramic_vase_03",
    "horse_head",
    "potted_plant_01",
    "potted_plant_02",
]


class Piece:
    """One mesh from a model: points (site coordinates, metres), faces, and the
    (u, v) of every face corner."""

    def __init__(self, name, verts, faces, uvs):
        self.name, self.verts, self.faces, self.uvs = name, verts, faces, uvs

    def bounds(self):
        xs, ys, zs = zip(*self.verts)
        return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

    def base(self):
        """The middle of its footprint, at its lowest point."""
        (x0, x1), (y0, _), (z0, z1) = self.bounds()
        return ((x0 + x1) / 2, y0, (z0 + z1) / 2)


def load(model_id, only=None, skip=(), thin=None):
    """Import assets_src/models/<id> and return {object name: Piece}.

    only / skip   object names to keep or leave out (pots, soil...)
    thin          {object name: fraction of triangles to keep}, for dense meshes
    """
    import bpy
    from . import config as C

    path = C.SRC_MODELS / model_id / f"{model_id}_1k.gltf"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing. Run blender/fetch_assets.py first.")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    out = {}
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for ob in new:
        if ob.type != "MESH" or ob.name in skip or (only and ob.name not in only):
            continue
        keep = (thin or {}).get(ob.name)
        if keep:
            mod = ob.modifiers.new("thin", "DECIMATE")
            mod.ratio = keep
            depsgraph.update()
        ev = ob.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ob.matrix_world
        verts = []
        for v in me.vertices:
            p = mw @ v.co
            verts.append((p.x, p.z, -p.y))                # Blender (z up) to site (y up)
        uv = me.uv_layers.get("UVMap") or me.uv_layers.active
        faces, uvs = [], []
        for poly in me.polygons:
            faces.append(tuple(poly.vertices))
            uvs.append([tuple(uv.data[i].uv) for i in poly.loop_indices] if uv else [(0.0, 0.0)] * poly.loop_total)
        out[ob.name] = Piece(ob.name, verts, faces, uvs)
        ev.to_mesh_clear()
    # Leave nothing of the import behind: the scene is built only from what `place` adds.
    for ob in new:
        data = ob.data
        bpy.data.objects.remove(ob)
        if data is not None and data.users == 0 and isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
    for coll in (bpy.data.materials, bpy.data.images):
        for item in list(coll):
            if item.users == 0:
                coll.remove(item)
    return out


def place(b, group, mat, piece, pos, yaw=0.0, scale=1.0, origin=None, tilt=0.0):
    """Add a copy of `piece` to the scene.

    origin   the point of the piece that lands on `pos` (default: its base)
    yaw      turn about the vertical, in radians; 0 keeps the model's own facing,
             and a turn of a moves its +z side toward (sin a, 0, cos a)
    tilt     lean toward +z, in radians, before the turn (for something set down at an angle)
    """
    ox, oy, oz = origin or piece.base()
    c, s = math.cos(yaw), math.sin(yaw)
    ct, st = math.cos(tilt), math.sin(tilt)
    px, py, pz = pos
    verts = []
    for x, y, z in piece.verts:
        x, y, z = (x - ox) * scale, (y - oy) * scale, (z - oz) * scale
        y, z = y * ct - z * st, y * st + z * ct
        verts.append((px + x * c + z * s, py + y, pz - x * s + z * c))
    b.mesh(group, mat, verts, piece.faces, smooth=True, uvs=piece.uvs)
