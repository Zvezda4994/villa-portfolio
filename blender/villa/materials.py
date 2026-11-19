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
  reflect  (glass) how strongly it reflects the sky panorama; indoor glass that the
           sky can't really reach (a glass table) turns it down. Default 1.
  screen   a glowing picture (the games room's monitors): the picture times the
           colour times "strength", the same in Blender and on the website. Like
           the lampshade diffusers, it lights nothing in the bake; the room puts
           a lamp in front of it instead.

Colours are sRGB values from 0 to 1. Tints are plain multipliers.

Furniture adds three things:
  img      a picture laid over the object's own UVs instead of a tiling texture:
           either made by the build (the rug, the painting, the chessboard) or
           taken from a downloaded model ("src", relative to assets_src/models).
           Saved as build/textures/<img>.png and exported as textures/<img>.ktx2.
  room     the furnished room the material belongs to. The website fetches its
           picture with that room, after the first view is up, not before.
  albedo   the colour is painted per vertex (the visitor's skin on the pool deck).
           The bake multiplies it into the vertex light, so the website needs
           nothing extra.
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
    "light_off":   dict(kind="vertex", color=(0.80, 0.80, 0.78)),    # a ceiling downlight switched off
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

    # --- dining room (dining.py) ---
    # big flat pieces, lit by the room's own lightmap
    "walnut":      dict(kind="baked", room="dining", tex="walnut_veneer", tile=1.6, tint=(0.50, 0.42, 0.37), rough=0.4),
    "rug":         dict(kind="baked", room="dining", img="rug", color=(1, 1, 1), rough=1.0),
    "painting":    dict(kind="baked", room="dining", img="painting", color=(1, 1, 1), rough=0.9),
    "chessboard":  dict(kind="baked", room="dining", img="chessboard", color=(1, 1, 1), rough=0.25),
    # curved pieces, lit per vertex
    "leather":     dict(kind="vertex", room="dining", color=(0.33, 0.20, 0.13)),
    "walnut_dark": dict(kind="vertex", room="dining", color=(0.20, 0.13, 0.09)),
    "bronze":      dict(kind="vertex", room="dining", color=(0.27, 0.20, 0.14)),
    "canvas_edge": dict(kind="vertex", room="dining", color=(0.80, 0.76, 0.70)),
    # Poly Haven models, keeping their own colour pictures
    "chess_white": dict(kind="vertex", room="dining", img="chess_white", size=512,
                        src="chess_set/textures/chess_set_pieces_white_diff_1k.jpg", color=(1, 1, 1)),
    "chess_black": dict(kind="vertex", room="dining", img="chess_black", size=512,
                        src="chess_set/textures/chess_set_pieces_black_diff_1k.jpg", color=(1, 1, 1)),
    "cabinet":     dict(kind="vertex", room="dining", img="cabinet", size=512,
                        src="modern_wooden_cabinet/textures/modern_wooden_cabinet_diff_1k.jpg", color=(0.85, 0.80, 0.78)),
    "vase_round":  dict(kind="vertex", room="dining", img="vase_round", size=256,
                        src="ceramic_vase_02/textures/ceramic_vase_02_diff_1k.jpg", color=(1, 1, 1)),
    "vase_tall":   dict(kind="vertex", room="dining", img="vase_tall", size=256,
                        src="ceramic_vase_03/textures/ceramic_vase_03_diff_1k.jpg", color=(1, 1, 1)),
    "horse_head":  dict(kind="vertex", room="dining", img="horse_head", size=256,
                        src="horse_head/textures/horse_head_diff_1k.jpg", color=(1, 1, 1)),
    "fig_leaves":  dict(kind="vertex", room="dining", img="fig_leaves", size=256, double_sided=True,
                        src="potted_plant_01/textures/potted_plant_01_leaves_diff_1k.jpg", color=(1, 1, 1)),
    "fig_stems":   dict(kind="vertex", room="dining", img="fig_stems", size=256,
                        src="potted_plant_01/textures/potted_plant_01_pot_diff_1k.jpg", color=(1, 1, 1)),
    "philo_leaves": dict(kind="vertex", room="dining", img="philo_leaves", size=256, double_sided=True,
                         src="potted_plant_02/textures/potted_plant_02_leaves_diff_1k.jpg", color=(1, 1, 1)),

    # --- pool deck (pool.py) ---
    # teak and travertine reuse textures the house already loads, so they cost nothing extra
    "teak":        dict(kind="baked", tex="oak_veneer_01", tile=1.1, tint=(0.80, 0.60, 0.43), rough=0.6),
    "travertine":  dict(kind="baked", tex="marble_01", tile=0.9, tint=(1.0, 0.92, 0.80), rough=0.7),
    "rug_outdoor": dict(kind="baked", room="pool", color=(0.80, 0.76, 0.68), rough=1.0),
    "rug_border":  dict(kind="baked", room="pool", color=(0.45, 0.39, 0.32), rough=1.0),
    "card":        dict(kind="baked", room="pool", img="contact_card", color=(1, 1, 1), rough=0.8),
    "card_back":   dict(kind="baked", room="pool", color=(0.95, 0.935, 0.895), rough=0.8),
    "canvas":      dict(kind="vertex", room="pool", color=(0.88, 0.85, 0.78)),
    "canvas_sand": dict(kind="vertex", room="pool", color=(0.76, 0.70, 0.60)),
    "canvas_seam": dict(kind="vertex", room="pool", color=(0.80, 0.77, 0.69)),     # the parasol's seams
    "pillow_rust": dict(kind="vertex", room="pool", color=(0.62, 0.33, 0.21)),
    "pillow_olive": dict(kind="vertex", room="pool", color=(0.46, 0.46, 0.32)),
    "towel":       dict(kind="vertex", room="pool", color=(0.95, 0.94, 0.90)),
    "towel_stripe": dict(kind="vertex", room="pool", color=(0.72, 0.60, 0.44)),
    "towel_navy":  dict(kind="vertex", room="pool", color=(0.11, 0.16, 0.29)),
    "bronze_dark": dict(kind="vertex", room="pool", color=(0.11, 0.09, 0.075)),
    # the quiver trees, a Poly Haven model keeping its own colour picture
    "quiver_tree": dict(kind="vertex", room="pool", img="quiver_tree", size=256, double_sided=True,
                        src="quiver_tree_02/textures/quiver_tree_02_diff_1k.jpg", color=(1, 1, 1)),
    "fire_glass":  dict(kind="vertex", room="pool", color=(0.08, 0.07, 0.065)),
    "flame":       dict(kind="emissive", room="pool", color=(1.0, 0.55, 0.20), strength=14.0),
    "lantern_glow": dict(kind="emissive", room="pool", color=(1.0, 0.70, 0.42), strength=2.4),
    # the table setting
    "sake_bottle": dict(kind="vertex", room="pool", color=(0.07, 0.10, 0.08)),
    "sake_cap":    dict(kind="vertex", room="pool", color=(0.10, 0.09, 0.09)),
    "bottle_gloss": dict(kind="glass", room="pool", color=(0.30, 0.36, 0.32), opacity=0.10),
    "sake_label":  dict(kind="vertex", room="pool", img="sake_label", color=(1, 1, 1)),
    "stoneware":   dict(kind="vertex", room="pool", color=(0.80, 0.77, 0.70)),
    "sake":        dict(kind="vertex", room="pool", color=(0.78, 0.74, 0.58)),
    # what I left behind: sunglasses on the table, loafers on the deck
    "shades":      dict(kind="vertex", room="pool", color=(0.03, 0.028, 0.026)),
    "shades_lens": dict(kind="glass", room="pool", color=(0.05, 0.04, 0.035), opacity=0.85),
    "suede":       dict(kind="vertex", room="pool", color=(0.42, 0.28, 0.18)),
    "sole":        dict(kind="vertex", room="pool", color=(0.16, 0.10, 0.07)),
    # the visitor's hand and drink, carried with the camera (skin painted per vertex)
    "skin":        dict(kind="vertex", room="pool", albedo=True, color=(1, 1, 1)),
    "visitor_cuff": dict(kind="vertex", room="pool", color=(0.78, 0.82, 0.87)),
    "martini_glass": dict(kind="glass", room="pool", color=(0.86, 0.90, 0.90), opacity=0.16),
    "martini":     dict(kind="glass", room="pool", color=(0.85, 0.86, 0.76), opacity=0.32),
    "olive_fruit": dict(kind="vertex", room="pool", color=(0.34, 0.40, 0.14)),
    "pick":        dict(kind="vertex", room="pool", color=(0.12, 0.09, 0.07)),

    # --- shared by the furnished rooms (plain colours, nothing to download) ---
    "aluminium":   dict(kind="vertex", color=(0.70, 0.71, 0.72)),
    "caster":      dict(kind="vertex", color=(0.06, 0.06, 0.06)),
    "paper_edge":  dict(kind="vertex", color=(0.90, 0.87, 0.78)),
    "ceramic_white": dict(kind="vertex", color=(0.92, 0.91, 0.88)),
    "book_navy":   dict(kind="vertex", color=(0.13, 0.17, 0.29)),
    "book_cream":  dict(kind="vertex", color=(0.84, 0.79, 0.68)),
    "book_rust":   dict(kind="vertex", color=(0.55, 0.25, 0.15)),
    "book_olive":  dict(kind="vertex", color=(0.36, 0.37, 0.24)),
    "book_charcoal": dict(kind="vertex", color=(0.15, 0.15, 0.16)),
    # smoked oak: the house's oak picture, darker, so it costs nothing extra to load
    "study_oak":   dict(kind="baked", tex="oak_veneer_01", tile=1.4, tint=(0.62, 0.48, 0.37), rough=0.45),

    # --- study (study.py) ---
    "persian_rug": dict(kind="baked", room="study", img="persian_rug", color=(1, 1, 1), rough=1.0),
    "whiteboard":  dict(kind="vertex", room="study", img="whiteboard", color=(1, 1, 1)),
    "glass_table": dict(kind="glass", room="study", color=(0.78, 0.86, 0.84), opacity=0.22, reflect=0.2),
    "sofa_wool":   dict(kind="vertex", room="study", color=(0.27, 0.30, 0.20)),
    "cushion_rust": dict(kind="vertex", room="study", color=(0.63, 0.34, 0.19)),
    "cushion_cream": dict(kind="vertex", room="study", color=(0.86, 0.82, 0.73)),
    "throw":       dict(kind="vertex", room="study", color=(0.74, 0.68, 0.58)),
    "chair_leather": dict(kind="vertex", room="study", color=(0.47, 0.27, 0.15)),
    "chair_shell": dict(kind="vertex", room="study", color=(0.09, 0.085, 0.08)),
    "dark_bronze": dict(kind="vertex", room="study", color=(0.12, 0.10, 0.08)),
    # aged brass, less yellow than the house's; light, since the website shows only its diffuse light, not its shine
    "lamp_brass":  dict(kind="vertex", room="study", color=(0.82, 0.63, 0.37)),
    "black_marble": dict(kind="vertex", room="study", color=(0.06, 0.06, 0.065)),
    "shade_linen": dict(kind="emissive", room="study", color=(1.0, 0.80, 0.58), strength=1.6),
    "lamp_glow":   dict(kind="emissive", room="study", color=(1.0, 0.76, 0.48), strength=1.2),
    "fringe":      dict(kind="vertex", room="study", color=(0.80, 0.74, 0.62)),
    "planter_dark": dict(kind="vertex", room="study", color=(0.10, 0.095, 0.09)),
    # the fig tree again (Poly Haven's potted_plant_01), here beside the whiteboard
    "study_fig_leaves": dict(kind="vertex", room="study", img="fig_leaves", size=256, double_sided=True,
                             src="potted_plant_01/textures/potted_plant_01_leaves_diff_1k.jpg", color=(1, 1, 1)),
    "study_fig_stems": dict(kind="vertex", room="study", img="fig_stems", size=256,
                            src="potted_plant_01/textures/potted_plant_01_pot_diff_1k.jpg", color=(1, 1, 1)),
    "marker_body": dict(kind="vertex", room="study", color=(0.92, 0.92, 0.90)),
    "marker_black": dict(kind="vertex", room="study", color=(0.05, 0.05, 0.06)),
    "marker_blue": dict(kind="vertex", room="study", color=(0.12, 0.25, 0.60)),
    "eraser_felt": dict(kind="vertex", room="study", color=(0.55, 0.55, 0.55)),
    "journal_cover": dict(kind="vertex", room="study", color=(0.22, 0.13, 0.08)),
    "journal_pages": dict(kind="vertex", room="study", img="journal", color=(1, 1, 1)),
    "ribbon":      dict(kind="vertex", room="study", color=(0.50, 0.12, 0.10)),
    "pen_black":   dict(kind="vertex", room="study", color=(0.04, 0.04, 0.045)),
    "coffee":      dict(kind="vertex", room="study", color=(0.16, 0.09, 0.05)),
    # Poly Haven's potted_plant_04 (a haworthia in a white pot), keeping its own picture
    "succulent":   dict(kind="vertex", room="study", img="succulent", size=256,
                        src="potted_plant_04/textures/potted_plant_04_diff_1k.jpg", color=(1, 1, 1)),

    # --- games room (games.py): black and white, lit by the screens ---
    "desk_mat":    dict(kind="vertex", room="games", color=(0.035, 0.035, 0.038)),
    "rug_charcoal": dict(kind="baked", room="games", color=(0.10, 0.10, 0.105), rough=1.0),
    "rug_line":    dict(kind="baked", room="games", color=(0.80, 0.80, 0.78), rough=1.0),
    "white_v":     dict(kind="vertex", room="games", color=(0.88, 0.88, 0.87)),
    "keycap":      dict(kind="vertex", room="games", color=(0.93, 0.93, 0.92)),
    "monitor_black": dict(kind="vertex", room="games", color=(0.025, 0.025, 0.028)),
    "metal_black": dict(kind="vertex", room="games", color=(0.04, 0.04, 0.045)),
    "chair_white": dict(kind="vertex", room="games", color=(0.90, 0.90, 0.89)),
    "chair_white_shell": dict(kind="vertex", room="games", color=(0.80, 0.80, 0.80)),
    "board_white": dict(kind="vertex", room="games", color=(0.82, 0.82, 0.83)),
    "fan_blade":   dict(kind="vertex", room="games", color=(0.86, 0.86, 0.86), double_sided=True),
    "sofa_charcoal": dict(kind="vertex", room="games", color=(0.13, 0.13, 0.14)),
    "cushion_white": dict(kind="vertex", room="games", color=(0.86, 0.86, 0.84)),
    "cushion_black": dict(kind="vertex", room="games", color=(0.05, 0.05, 0.055)),
    "case_black":  dict(kind="vertex", room="games", color=(0.03, 0.03, 0.033)),
    "case_white":  dict(kind="vertex", room="games", color=(0.90, 0.90, 0.89)),
    "blind":       dict(kind="vertex", room="games", color=(0.07, 0.07, 0.075)),
    "blind_metal": dict(kind="vertex", room="games", color=(0.12, 0.12, 0.13)),
    "pc_glass":    dict(kind="glass", room="games", color=(0.30, 0.32, 0.34), opacity=0.14, reflect=0.15),
    "led_white":   dict(kind="emissive", room="games", color=(0.85, 0.90, 1.0), strength=2.2),
    "game_spines": dict(kind="vertex", room="games", img="game_spines", color=(1, 1, 1)),
    "wall_charcoal": dict(kind="vertex", room="games", color=(0.22, 0.22, 0.225)),
    "ceiling_charcoal": dict(kind="vertex", room="games", color=(0.17, 0.17, 0.175)),
    "felt_dark":   dict(kind="vertex", room="games", color=(0.30, 0.30, 0.30)),
    "slat_black":  dict(kind="vertex", room="games", color=(0.035, 0.035, 0.038)),
    "sofa_boucle": dict(kind="vertex", room="games", color=(0.80, 0.79, 0.76)),
    "games_print": dict(kind="vertex", room="games", img="games_print", color=(1, 1, 1)),
    # the philodendron (Poly Haven's potted_plant_02), as in the dining room
    "games_philo": dict(kind="vertex", room="games", img="philo_leaves", size=256, double_sided=True,
                        src="potted_plant_02/textures/potted_plant_02_leaves_diff_1k.jpg", color=(1, 1, 1)),
    "screen_main": dict(kind="screen", room="games", img="screen_main", color=(1, 1, 1), strength=1.4),
    "screen_chart": dict(kind="screen", room="games", img="screen_chart", color=(1, 1, 1), strength=1.4),
}

# Every Poly Haven texture the scene needs, without repeats. fetch_assets.py reads this.
TEXTURE_IDS = sorted({m["tex"] for m in MATS.values() if "tex" in m}
                     | {m["blend"]["tex"] for m in MATS.values() if "blend" in m})


def srgb_to_linear(c):
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def build_materials():
    """Make a Blender material for every entry above. Returns {name: material}."""
    import bpy
    from .textures import mask_path, picture_path, prepared

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
            elif "img" in m:
                # One picture over the object's own UVs, times a plain colour.
                node = new("ShaderNodeTexImage")
                node.image = image(picture_path(m["img"]))
                coords = new("ShaderNodeUVMap")
                coords.uv_map = "UVMap"
                link(coords.outputs["UV"], node.inputs["Vector"])
                mul = new("ShaderNodeVectorMath")
                mul.operation = "MULTIPLY"
                mul.inputs[1].default_value = srgb_to_linear(m.get("color", (1, 1, 1)))
                link(node.outputs["Color"], mul.inputs[0])
                link(mul.outputs[0], bsdf.inputs["Base Color"])
            elif m.get("albedo"):
                # colour painted per vertex (the character's skin), times a plain colour
                attr = new("ShaderNodeAttribute")
                attr.attribute_name = "Albedo"
                mul = new("ShaderNodeVectorMath")
                mul.operation = "MULTIPLY"
                mul.inputs[1].default_value = srgb_to_linear(m.get("color", (1, 1, 1)))
                link(attr.outputs["Color"], mul.inputs[0])
                link(mul.outputs[0], bsdf.inputs["Base Color"])
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

        elif kind == "screen":
            # a picture that glows: what's on a monitor
            node = new("ShaderNodeTexImage")
            node.image = image(picture_path(m["img"]))
            coords = new("ShaderNodeUVMap")
            coords.uv_map = "UVMap"
            link(coords.outputs["UV"], node.inputs["Vector"])
            mul = new("ShaderNodeVectorMath")
            mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = srgb_to_linear(m.get("color", (1, 1, 1)))
            link(node.outputs["Color"], mul.inputs[0])
            glow = new("ShaderNodeEmission")
            glow.inputs["Strength"].default_value = m["strength"]
            link(mul.outputs[0], glow.inputs["Color"])
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
