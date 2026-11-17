"""The list of materials, kept in one place for both Blender and the website.

kind:
  baked    lit by a lightmap. "tex" is a Poly Haven texture id, "tile" is how many
           metres one repeat of the texture covers, "tint" multiplies its colour.
           "blend" mixes in a second texture wherever a mask says so (the gravel
           borders on the sand).
  vertex   small things (window frames, plants, rocks) with light baked per vertex.
  sheer    see-through curtain fabric, lit per vertex like the above.
  glass / water / emissive / flat   handled specially on the website. Water
           reflects a panorama taken from where it sits ("probe").

Colours are sRGB values from 0 to 1. Tints are plain multipliers.
"""

MATS = {
    # --- house ---
    "stone":       dict(kind="baked", tex="marble_01", tile=2.4, tint=(1.0, 0.97, 0.92), rough=0.7),
    "concrete":    dict(kind="baked", tex="concrete_wall_007", tile=3.5, tint=(1.35, 1.33, 1.30), rough=0.8),
    "plaster":     dict(kind="baked", color=(0.92, 0.91, 0.88), rough=0.9),
    "oak":         dict(kind="baked", tex="oak_veneer_01", tile=1.8, tint=(1.0, 1.0, 1.0), rough=0.55),
    "dark_stone":  dict(kind="baked", tex="granite_tile", tile=2.3, tint=(0.30, 0.29, 0.30), rough=0.6),
    "floor_wood":  dict(kind="baked", tex="laminate_floor_02", tile=1.7, tint=(1.0, 1.0, 1.0), rough=0.5),
    "floor_stone": dict(kind="baked", tex="marble_01", tile=3.2, tint=(1.0, 0.98, 0.95), rough=0.55),
    "floor_dark":  dict(kind="baked", tex="granite_tile", tile=2.3, tint=(0.6, 0.6, 0.62), rough=0.45),
    # --- outside ---
    "paving":      dict(kind="baked", tex="marble_01", tile=3.2, tint=(0.90, 0.88, 0.86), rough=0.75),
    "slabs":       dict(kind="baked", tex="marble_01", tile=4.2, tint=(1.0, 0.96, 0.90), rough=0.7),      # the entrance, larger and paler
    "setts":       dict(kind="baked", tex="cobblestone_floor_08", tile=1.1, tint=(1.22, 1.10, 0.94), rough=0.85),
    "mulch":       dict(kind="baked", tex="floor_pebbles_01", tile=1.0, tint=(0.78, 0.72, 0.66), rough=1.0),
    "pool_tile":   dict(kind="baked", tex="rounded_square_tiled_wall", tile=2.0, tint=(0.45, 0.85, 0.9), rough=0.3),
    "sand":        dict(kind="baked", tex="sandy_gravel_02", tile=2.5, tint=(1.25, 1.17, 1.06), rough=1.0,
                        blend=dict(tex="floor_pebbles_01", tile=1.4, tint=(0.98, 0.95, 0.90), mask="terrain_mask")),
    # --- special ---
    "glass":       dict(kind="glass", color=(0.75, 0.85, 0.88), opacity=0.18),
    "glass_smoke": dict(kind="glass", color=(0.25, 0.27, 0.30), opacity=0.5),
    "water":       dict(kind="water", color=(0.15, 0.55, 0.60), probe="pool", ripple=0.15),
    "water_front": dict(kind="water", color=(0.10, 0.16, 0.17), probe="front", ripple=0.05),   # the still reflecting pool
    "light_warm":  dict(kind="emissive", color=(1.0, 0.72, 0.42), strength=12.0),
    "light_pool":  dict(kind="emissive", color=(0.70, 0.95, 1.0), strength=10.0),
    "cut":         dict(kind="flat", color=(0.07, 0.065, 0.06)),   # wall tops seen when the roof lifts off
    "sheer":       dict(kind="sheer", color=(0.93, 0.90, 0.84), opacity=0.62, double_sided=True),
    # --- small things lit per vertex ---
    "frame":       dict(kind="vertex", color=(0.06, 0.055, 0.05)),
    "brass":       dict(kind="vertex", color=(0.80, 0.60, 0.30)),
    "bark":        dict(kind="vertex", color=(0.42, 0.35, 0.27)),
    "palm_leaf":   dict(kind="vertex", color=(0.25, 0.33, 0.16), double_sided=True),
    "shrub":       dict(kind="vertex", color=(0.42, 0.42, 0.24), double_sided=True),
    "agave":       dict(kind="vertex", color=(0.40, 0.50, 0.45), double_sided=True),
    "rock":        dict(kind="vertex", color=(0.58, 0.47, 0.38)),
    "hill":        dict(kind="vertex", color=(0.50, 0.33, 0.24)),
}

# Every Poly Haven texture the scene needs, without repeats. fetch_assets.py reads this.
TEXTURE_IDS = sorted({m["tex"] for m in MATS.values() if "tex" in m}
                     | {m["blend"]["tex"] for m in MATS.values() if "blend" in m})


def srgb_to_linear(c):
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def build_materials():
    """Make a Blender material for every entry above. Returns {name: material}."""
    import bpy
    from .textures import mask_path, prepared

    def image(path, data=False):
        img = bpy.data.images.load(str(path), check_existing=True)
        if data:
            img.colorspace_settings.name = "Non-Color"
        return img

    out = {}
    for name, m in MATS.items():
        mat = bpy.data.materials.new(name)
        if mat.node_tree is None:
            mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        new, link = nt.nodes.new, nt.links.new
        output = new("ShaderNodeOutputMaterial")
        kind = m["kind"]

        def textured(tex_id, tint, scale=1.0):
            """Colour texture times tint. `scale` re-tiles it relative to the mesh's own UVs."""
            node = new("ShaderNodeTexImage")
            node.image = image(prepared(tex_id))
            if scale != 1.0:
                coords = new("ShaderNodeUVMap")
                coords.uv_map = "UVMap"
                grow = new("ShaderNodeVectorMath")
                grow.operation = "SCALE"
                grow.inputs["Scale"].default_value = scale
                link(coords.outputs["UV"], grow.inputs[0])
                link(grow.outputs[0], node.inputs["Vector"])
            mul = new("ShaderNodeVectorMath")
            mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = tint
            link(node.outputs["Color"], mul.inputs[0])
            return mul.outputs[0]

        if kind in ("baked", "vertex", "flat"):
            bsdf = new("ShaderNodeBsdfPrincipled")
            bsdf.inputs["Roughness"].default_value = m.get("rough", 0.85)
            bsdf.inputs["Metallic"].default_value = m.get("metal", 0.0)
            if "tex" in m:
                colour = textured(m["tex"], m.get("tint", (1, 1, 1)))
                if "blend" in m:
                    # Second texture wherever the mask (laid out in the lightmap's UVs) is white.
                    bl = m["blend"]
                    other = textured(bl["tex"], bl["tint"], scale=m["tile"] / bl["tile"])
                    mask = new("ShaderNodeTexImage")
                    mask.image = image(mask_path(bl["mask"]), data=True)
                    coords = new("ShaderNodeUVMap")
                    coords.uv_map = "Lightmap"
                    link(coords.outputs["UV"], mask.inputs["Vector"])
                    mix = new("ShaderNodeMix")
                    mix.data_type = "RGBA"
                    socket = {s.identifier: s for s in list(mix.inputs) + list(mix.outputs)}
                    link(mask.outputs["Color"], socket["Factor_Float"])
                    link(colour, socket["A_Color"])
                    link(other, socket["B_Color"])
                    colour = socket["Result_Color"]
                link(colour, bsdf.inputs["Base Color"])
            else:
                bsdf.inputs["Base Color"].default_value = (*srgb_to_linear(m["color"]), 1.0)
            link(bsdf.outputs[0], output.inputs["Surface"])
            if kind == "baked":
                # The lightmap bake writes into whichever image this node holds.
                target = new("ShaderNodeTexImage")
                target.name = "BAKE"

        elif kind == "sheer":
            # Thin fabric: part see-through, part lit from the front, part glowing
            # with the room light behind it.
            colour = (*srgb_to_linear(m["color"]), 1.0)
            front = new("ShaderNodeBsdfDiffuse")
            front.inputs["Color"].default_value = colour
            behind = new("ShaderNodeBsdfTranslucent")
            behind.inputs["Color"].default_value = colour
            cloth = new("ShaderNodeMixShader")
            cloth.inputs[0].default_value = 0.5
            link(front.outputs[0], cloth.inputs[1])
            link(behind.outputs[0], cloth.inputs[2])
            clear = new("ShaderNodeBsdfTransparent")
            final = new("ShaderNodeMixShader")
            final.inputs[0].default_value = m["opacity"]
            link(clear.outputs[0], final.inputs[1])
            link(cloth.outputs[0], final.inputs[2])
            link(final.outputs[0], output.inputs["Surface"])

        elif kind == "emissive":
            glow = new("ShaderNodeEmission")
            glow.inputs["Color"].default_value = (*srgb_to_linear(m["color"]), 1.0)
            glow.inputs["Strength"].default_value = m["strength"]
            link(glow.outputs[0], output.inputs["Surface"])

        elif kind in ("glass", "water"):
            # Flat sheets, not solid volumes: reflect like glass, and let light and
            # shadows straight through (tinted), so rooms and the pool floor get lit.
            colour = (*srgb_to_linear(m["color"]), 1.0)
            clear = new("ShaderNodeBsdfTransparent")
            # what passes through is much paler than the named colour, or two layers would go black
            clear.inputs["Color"].default_value = tuple(v ** (0.25 if kind == "water" else 0.15) for v in colour[:3]) + (1.0,)
            shine = new("ShaderNodeBsdfGlossy")
            shine.inputs["Roughness"].default_value = 0.02 if kind == "glass" else 0.06
            fresnel = new("ShaderNodeFresnel")
            fresnel.inputs["IOR"].default_value = 1.5 if kind == "glass" else 1.33
            boost = new("ShaderNodeMath")
            boost.operation = "MULTIPLY"
            boost.use_clamp = True
            boost.inputs[1].default_value = 1.8          # two surfaces per pane, so nearly double the reflection
            link(fresnel.outputs[0], boost.inputs[0])
            if kind == "water":
                ripples = new("ShaderNodeTexNoise")
                ripples.inputs["Scale"].default_value = 2.2
                ripples.inputs["Detail"].default_value = 3.0
                bump = new("ShaderNodeBump")
                bump.inputs["Strength"].default_value = 0.8 * m.get("ripple", 0.15)
                link(ripples.outputs[0], bump.inputs["Height"])
                link(bump.outputs[0], shine.inputs["Normal"])
                link(bump.outputs[0], fresnel.inputs["Normal"])
            seen = new("ShaderNodeMixShader")
            link(boost.outputs[0], seen.inputs[0])
            link(clear.outputs[0], seen.inputs[1])
            link(shine.outputs[0], seen.inputs[2])
            path = new("ShaderNodeLightPath")
            either = new("ShaderNodeMath")
            either.operation = "MAXIMUM"
            link(path.outputs["Is Shadow Ray"], either.inputs[0])
            link(path.outputs["Is Diffuse Ray"], either.inputs[1])
            final = new("ShaderNodeMixShader")
            link(either.outputs[0], final.inputs[0])
            link(seen.outputs[0], final.inputs[1])
            link(clear.outputs[0], final.inputs[2])
            link(final.outputs[0], output.inputs["Surface"])

        out[name] = mat
    return out
