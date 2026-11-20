"""The list of materials, kept in one place for both Blender and the website.

kind:
  baked    lit by a lightmap. "tex" is a Poly Haven texture id, "tile" is how many
           metres one repeat of the texture covers, "tint" multiplies its colour.
           "blend" mixes in a second texture wherever a mask says so (the gravel
           borders on the sand).
  vertex   small things (window frames, plants, rocks) with light baked per vertex.
           With a "tex" it carries a tiling texture too, laid in metres like the
           house's (the walnut in the living room and the library, Kit.grain).
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
  moodboard  a frame on the living room's moodboard: the number is its picture's
           shape (width / height). The site lays one of the pictures in
           web/assets/moodboard/ over it, picked at random each time the room opens.
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

    # --- shared by the kitchen and the gym (plain colours) ---
    "oak_light":   dict(kind="vertex", color=(0.71, 0.60, 0.46)),          # pale oak: shelves, stools, the speed bag's board
    "steel_black": dict(kind="vertex", color=(0.05, 0.05, 0.055)),
    "steel_brushed": dict(kind="vertex", color=(0.66, 0.67, 0.68)),
    "plaster_v":   dict(kind="vertex", color=(0.92, 0.91, 0.88)),          # the house's plaster, lining a room's walls

    # --- kitchen (kitchen.py): white, pale oak and quartz ---
    "kitchen_white": dict(kind="baked", room="kitchen", color=(0.90, 0.90, 0.88), rough=0.6),
    "kitchen_plinth": dict(kind="baked", room="kitchen", color=(0.16, 0.16, 0.16), rough=0.8),
    "kitchen_white_v": dict(kind="vertex", room="kitchen", color=(0.90, 0.90, 0.88)),
    "kitchen_gap": dict(kind="vertex", room="kitchen", color=(0.16, 0.16, 0.16)),
    "kitchen_quartz": dict(kind="vertex", room="kitchen", color=(0.91, 0.90, 0.87)),
    "kitchen_tile": dict(kind="vertex", room="kitchen", img="kitchen_tile", color=(1, 1, 1)),
    "kitchen_labels": dict(kind="vertex", room="kitchen", img="kitchen_labels", color=(1, 1, 1)),
    "jar_glass":   dict(kind="glass", room="kitchen", color=(0.86, 0.91, 0.90), opacity=0.12, reflect=0.25),
    "jar_seal":    dict(kind="vertex", room="kitchen", color=(0.80, 0.78, 0.74)),
    "canister_white": dict(kind="vertex", room="kitchen", color=(0.93, 0.92, 0.89)),
    "tin_black":   dict(kind="vertex", room="kitchen", color=(0.07, 0.07, 0.075)),
    "tin_sage":    dict(kind="vertex", room="kitchen", color=(0.56, 0.61, 0.52)),
    "content_pasta": dict(kind="vertex", room="kitchen", color=(0.86, 0.70, 0.42)),
    "content_coffee": dict(kind="vertex", room="kitchen", color=(0.20, 0.12, 0.07)),
    "content_rice": dict(kind="vertex", room="kitchen", color=(0.93, 0.91, 0.86)),
    "content_lentils": dict(kind="vertex", room="kitchen", color=(0.78, 0.38, 0.18)),
    "content_oats": dict(kind="vertex", room="kitchen", color=(0.80, 0.71, 0.55)),
    "content_beans": dict(kind="vertex", room="kitchen", color=(0.13, 0.10, 0.10)),
    "glass_black": dict(kind="vertex", room="kitchen", color=(0.03, 0.03, 0.035)),
    "lemon":       dict(kind="vertex", room="kitchen", color=(0.88, 0.80, 0.08)),
    "kitchen_coffee": dict(kind="vertex", room="kitchen", color=(0.16, 0.09, 0.05)),
    "lamp_brass_k": dict(kind="vertex", room="kitchen", color=(0.82, 0.63, 0.37)),
    "kitchen_globe": dict(kind="emissive", room="kitchen", color=(1.0, 0.90, 0.78), strength=2.0),
    "kitchen_led": dict(kind="emissive", room="kitchen", color=(1.0, 0.92, 0.82), strength=3.0),
    # the haworthia (Poly Haven's potted_plant_04) and the fig (potted_plant_01), as in the study
    "kitchen_succulent": dict(kind="vertex", room="kitchen", img="succulent", size=256,
                              src="potted_plant_04/textures/potted_plant_04_diff_1k.jpg", color=(1, 1, 1)),
    "kitchen_fig_leaves": dict(kind="vertex", room="kitchen", img="fig_leaves", size=256, double_sided=True,
                               src="potted_plant_01/textures/potted_plant_01_leaves_diff_1k.jpg", color=(1, 1, 1)),
    "kitchen_fig_stems": dict(kind="vertex", room="kitchen", img="fig_stems", size=256,
                              src="potted_plant_01/textures/potted_plant_01_pot_diff_1k.jpg", color=(1, 1, 1)),

    # --- gym (gym.py): black mats, black and red leather, hard white light ---
    "gym_mat":     dict(kind="vertex", room="gym", color=(0.105, 0.105, 0.11)),
    "gym_mat_b":   dict(kind="vertex", room="gym", color=(0.125, 0.125, 0.13)),
    "leather_black": dict(kind="vertex", room="gym", color=(0.055, 0.052, 0.05)),
    "bag_band":    dict(kind="vertex", room="gym", color=(0.58, 0.06, 0.05)),
    "speedbag":    dict(kind="vertex", room="gym", color=(0.50, 0.29, 0.15)),
    "glove_red":   dict(kind="vertex", room="gym", color=(0.62, 0.05, 0.045)),
    "glove_white": dict(kind="vertex", room="gym", color=(0.90, 0.90, 0.88)),
    "glove_inside": dict(kind="vertex", room="gym", color=(0.03, 0.03, 0.03)),
    "duffel_black": dict(kind="vertex", room="gym", color=(0.065, 0.065, 0.07)),
    "duffel_inside": dict(kind="vertex", room="gym", color=(0.02, 0.02, 0.022)),
    "duffel_trim": dict(kind="vertex", room="gym", color=(0.30, 0.30, 0.31)),
    "duffel_zip":  dict(kind="vertex", room="gym", color=(0.55, 0.55, 0.56)),
    "shin_white":  dict(kind="vertex", room="gym", color=(0.90, 0.90, 0.88)),
    "shin_pad":    dict(kind="vertex", room="gym", color=(0.05, 0.05, 0.055)),
    "shin_black":  dict(kind="vertex", room="gym", color=(0.085, 0.085, 0.09)),
    "wrap_black":  dict(kind="vertex", room="gym", color=(0.07, 0.07, 0.075)),
    "wrap_layer":  dict(kind="vertex", room="gym", color=(0.15, 0.15, 0.16)),     # the turns seen at a roll's end
    "wrap_velcro": dict(kind="vertex", room="gym", color=(0.30, 0.30, 0.31)),
    # the worn brown lace-up pair: the leather's colour is painted per vertex (gym._wear)
    "glove_brown": dict(kind="vertex", room="gym", albedo=True, color=(1, 1, 1)),
    "glove_black": dict(kind="vertex", room="gym", color=(0.045, 0.045, 0.05)),
    "lace_tan":    dict(kind="vertex", room="gym", color=(0.80, 0.72, 0.58)),
    "gym_board":   dict(kind="vertex", room="gym", img="gym_board", color=(1, 1, 1)),
    "rope":        dict(kind="vertex", room="gym", color=(0.06, 0.06, 0.065)),
    "gym_led":     dict(kind="emissive", room="gym", color=(0.92, 0.96, 1.0), strength=4.0),
    "gym_timer":   dict(kind="screen", room="gym", img="gym_timer", color=(1, 1, 1), strength=1.6),

    # --- living room (living.py): oatmeal linen, walnut, the tank's glow ---
    # walnut lit per vertex, its grain from the dining table's texture (fetched with the room)
    "living_walnut": dict(kind="vertex", room="living", tex="walnut_veneer", tile=1.6, tint=(0.50, 0.42, 0.37)),
    # one material painted per vertex for the many small things: the rug, the tank's
    # sand, rocks, moss and fish
    "living_albedo": dict(kind="vertex", room="living", albedo=True, color=(1, 1, 1)),
    "living_sofa": dict(kind="vertex", room="living", color=(0.80, 0.76, 0.68)),
    "pillow_teal": dict(kind="vertex", room="living", color=(0.11, 0.27, 0.29)),
    "pillow_rust": dict(kind="vertex", room="living", color=(0.58, 0.32, 0.20)),
    "pillow_sand": dict(kind="vertex", room="living", color=(0.74, 0.66, 0.52)),
    "living_throw": dict(kind="vertex", room="living", color=(0.52, 0.40, 0.30)),
    "tv_black":    dict(kind="vertex", room="living", color=(0.025, 0.025, 0.028)),
    "tv_screen":   dict(kind="screen", room="living", img="living_tv", color=(1, 1, 1), strength=1.0),
    "living_brass": dict(kind="vertex", room="living", color=(0.82, 0.63, 0.37)),
    "living_shade": dict(kind="emissive", room="living", color=(1.0, 0.80, 0.58), strength=1.6),
    "mat_white":   dict(kind="vertex", room="living", color=(0.91, 0.90, 0.87)),
    # the tank: a glowing backdrop, glass, a dark plinth, plants and driftwood
    "tank_back":   dict(kind="screen", room="living", img="tank_back", color=(1, 1, 1), strength=0.8),
    "tank_glass":  dict(kind="glass", room="living", color=(0.74, 0.88, 0.88), opacity=0.12, reflect=0.35),
    "tank_black":  dict(kind="vertex", room="living", color=(0.025, 0.03, 0.035)),
    "tank_plinth": dict(kind="vertex", room="living", color=(0.11, 0.11, 0.115)),
    "aqua_grass":  dict(kind="vertex", room="living", color=(0.24, 0.47, 0.16), double_sided=True),
    "aqua_leaf":   dict(kind="vertex", room="living", color=(0.15, 0.36, 0.12), double_sided=True),
    "aqua_red":    dict(kind="vertex", room="living", color=(0.62, 0.22, 0.14), double_sided=True),
    "aqua_olive":  dict(kind="vertex", room="living", color=(0.40, 0.48, 0.16), double_sided=True),
    "driftwood":   dict(kind="vertex", room="living", color=(0.23, 0.16, 0.10)),
    # the moodboard's frames: plain colour fields in the file; the site lays one of the
    # pictures in web/assets/moodboard/ over each when the room opens. The number is
    # the picture's shape (width / height), for cropping.
    "moodboard_1": dict(kind="vertex", room="living", color=(0.66, 0.38, 0.26), moodboard=0.673),
    "moodboard_2": dict(kind="vertex", room="living", color=(0.33, 0.40, 0.50), moodboard=1.491),
    "moodboard_3": dict(kind="vertex", room="living", color=(0.78, 0.62, 0.30), moodboard=1.0),
    "moodboard_4": dict(kind="vertex", room="living", color=(0.56, 0.61, 0.52), moodboard=1.383),
    "moodboard_5": dict(kind="vertex", room="living", color=(0.85, 0.78, 0.66), moodboard=0.680),
    # the fig by the TV (Poly Haven's potted_plant_01), as in the kitchen
    "living_fig_leaves": dict(kind="vertex", room="living", img="fig_leaves", size=256, double_sided=True,
                              src="potted_plant_01/textures/potted_plant_01_leaves_diff_1k.jpg", color=(1, 1, 1)),
    "living_fig_stems": dict(kind="vertex", room="living", img="fig_stems", size=256,
                             src="potted_plant_01/textures/potted_plant_01_pot_diff_1k.jpg", color=(1, 1, 1)),

    # --- library (library.py): dark walnut shelves, books, a green banker's lamp ---
    "library_walnut": dict(kind="vertex", room="library", tex="walnut_veneer", tile=1.6, tint=(0.36, 0.28, 0.23)),
    # painted per vertex: every unmarked book its own colour, the rug, the titled books' sides
    "library_albedo": dict(kind="vertex", room="library", albedo=True, color=(1, 1, 1)),
    # the titled spines, all in one picture (data/library_books.txt, library.paint_spines)
    "library_spines": dict(kind="vertex", room="library", img="library_spines", color=(1, 1, 1)),
    "library_brass": dict(kind="vertex", room="library", color=(0.82, 0.63, 0.37)),
    "library_leather": dict(kind="vertex", room="library", color=(0.36, 0.19, 0.10)),
    # the banker's lamp's cased glass shade glows a little, lit from inside
    "banker_green": dict(kind="emissive", room="library", color=(0.10, 0.42, 0.20), strength=0.5),
    "banker_glow": dict(kind="emissive", room="library", color=(1.0, 0.84, 0.60), strength=1.8),
    "library_shade": dict(kind="emissive", room="library", color=(1.0, 0.80, 0.58), strength=1.5),
    "laptop_screen": dict(kind="screen", room="library", img="laptop_screen", color=(1, 1, 1), strength=0.9),
    "laptop_keys": dict(kind="vertex", room="library", color=(0.10, 0.10, 0.11)),
    "manuscript":  dict(kind="vertex", room="library", img="manuscript", color=(1, 1, 1)),
    "library_ink": dict(kind="vertex", room="library", color=(0.05, 0.05, 0.06)),
    # the house's oak ceiling, lit per vertex (library.ceiling)
    "library_ceiling": dict(kind="vertex", room="library", tex="oak_veneer_01", tile=1.8, tint=(1.0, 1.0, 1.0)),
    "library_walnut_v": dict(kind="vertex", room="library", color=(0.30, 0.20, 0.14)),     # small turned and slanted pieces
    "hourglass_glass": dict(kind="glass", room="library", color=(0.85, 0.88, 0.86), opacity=0.14, reflect=0.3),
    "hourglass_sand": dict(kind="vertex", room="library", color=(0.82, 0.70, 0.50)),
    "whisky":      dict(kind="vertex", room="library", color=(0.55, 0.30, 0.08)),

    # --- trophy room (trophy.py): slate walls, walnut, glass cases, gold ---
    "trophy_wall": dict(kind="vertex", room="trophy", color=(0.22, 0.24, 0.28)),
    "trophy_ceiling": dict(kind="vertex", room="trophy", tex="oak_veneer_01", tile=1.8, tint=(1.0, 1.0, 1.0)),
    "trophy_walnut": dict(kind="vertex", room="trophy", tex="walnut_veneer", tile=1.6, tint=(0.40, 0.32, 0.26)),
    "trophy_walnut_v": dict(kind="vertex", room="trophy", color=(0.30, 0.20, 0.14)),
    # painted per vertex: the rug, the chessboard's squares, the medals' ribbons
    "trophy_albedo": dict(kind="vertex", room="trophy", albedo=True, color=(1, 1, 1)),
    "trophy_black": dict(kind="vertex", room="trophy", color=(0.035, 0.035, 0.04)),
    "trophy_brass": dict(kind="vertex", room="trophy", color=(0.82, 0.63, 0.37)),
    # metals kept light: the site shows only diffuse light (see the study's lamp brass)
    "trophy_gold": dict(kind="vertex", room="trophy", color=(0.92, 0.72, 0.33)),
    "trophy_silver": dict(kind="vertex", room="trophy", color=(0.82, 0.83, 0.84)),
    "trophy_bronze": dict(kind="vertex", room="trophy", color=(0.70, 0.45, 0.26)),
    "case_velvet": dict(kind="vertex", room="trophy", color=(0.11, 0.14, 0.26)),
    "case_velvet_dark": dict(kind="vertex", room="trophy", color=(0.07, 0.08, 0.13)),
    "case_bronze": dict(kind="vertex", room="trophy", color=(0.24, 0.19, 0.14)),
    "case_glass":  dict(kind="glass", room="trophy", color=(0.86, 0.90, 0.90), opacity=0.10, reflect=0.25),
    "case_led":    dict(kind="emissive", room="trophy", color=(1.0, 0.90, 0.76), strength=3.0),
    "crystal":     dict(kind="glass", room="trophy", color=(0.86, 0.92, 0.95), opacity=0.25, reflect=0.5),
    "belt_leather": dict(kind="vertex", room="trophy", color=(0.80, 0.15, 0.12)),
    "belt_enamel": dict(kind="vertex", room="trophy", color=(0.07, 0.10, 0.25)),
    "trophy_leather": dict(kind="vertex", room="trophy", color=(0.48, 0.27, 0.14)),
    "trophy_mat":  dict(kind="vertex", room="trophy", color=(0.91, 0.90, 0.87)),
    "trophy_jersey": dict(kind="vertex", room="trophy", color=(0.15, 0.15, 0.165)),        # the framed team jersey
    "trophy_jersey_gold": dict(kind="vertex", room="trophy", color=(0.90, 0.68, 0.16)),
    "trophy_chess_white": dict(kind="vertex", room="trophy", color=(0.87, 0.83, 0.73)),
    "trophy_chess_black": dict(kind="vertex", room="trophy", color=(0.08, 0.07, 0.065)),
    "trophy_planter": dict(kind="vertex", room="trophy", color=(0.13, 0.125, 0.12)),
    # the fig in the corner (Poly Haven's potted_plant_01), as in the living room
    "trophy_fig_leaves": dict(kind="vertex", room="trophy", img="fig_leaves", size=256, double_sided=True,
                              src="potted_plant_01/textures/potted_plant_01_leaves_diff_1k.jpg", color=(1, 1, 1)),
    "trophy_fig_stems": dict(kind="vertex", room="trophy", img="fig_stems", size=256,
                             src="potted_plant_01/textures/potted_plant_01_pot_diff_1k.jpg", color=(1, 1, 1)),

    # --- main bedroom (bedroom.py): white linen, pale oak, oatmeal ---
    "bedroom_ceiling": dict(kind="vertex", room="bedroom", tex="oak_veneer_01", tile=1.8, tint=(1.0, 1.0, 1.0)),
    "bedroom_oak": dict(kind="vertex", room="bedroom", tex="oak_veneer_01", tile=1.4, tint=(0.95, 0.88, 0.80)),
    # painted per vertex: the rug and the titled books' covers
    "bedroom_albedo": dict(kind="vertex", room="bedroom", albedo=True, color=(1, 1, 1)),
    "bedroom_headboard": dict(kind="vertex", room="bedroom", color=(0.70, 0.65, 0.57)),
    "bedroom_chair": dict(kind="vertex", room="bedroom", color=(0.80, 0.77, 0.70)),
    "bedroom_black": dict(kind="vertex", room="bedroom", color=(0.05, 0.05, 0.055)),
    "bedroom_brass": dict(kind="vertex", room="bedroom", color=(0.82, 0.63, 0.37)),
    "bed_linen":   dict(kind="vertex", room="bedroom", color=(0.90, 0.88, 0.84)),
    "bed_sheet":   dict(kind="vertex", room="bedroom", color=(0.93, 0.92, 0.89)),
    "bed_pillow":  dict(kind="vertex", room="bedroom", color=(0.86, 0.83, 0.77)),
    "bed_accent":  dict(kind="vertex", room="bedroom", color=(0.62, 0.36, 0.24)),
    "bed_throw":   dict(kind="vertex", room="bedroom", color=(0.60, 0.37, 0.26)),
    "bed_ceramic": dict(kind="vertex", room="bedroom", color=(0.84, 0.81, 0.75)),
    "bed_shade":   dict(kind="emissive", room="bedroom", color=(1.0, 0.82, 0.62), strength=1.5),
    "bed_glass":   dict(kind="glass", room="bedroom", color=(0.86, 0.90, 0.90), opacity=0.14, reflect=0.3),
    "bed_water":   dict(kind="glass", room="bedroom", color=(0.80, 0.88, 0.90), opacity=0.25, reflect=0.3),
    "bed_pin":     dict(kind="vertex", room="bedroom", color=(0.80, 0.10, 0.08)),
    # the world map (bedroom.paint_map, from Natural Earth's coastlines) and the titled spines
    "bedroom_map": dict(kind="vertex", room="bedroom", img="world_map", color=(1, 1, 1)),
    "bedroom_spines": dict(kind="vertex", room="bedroom", img="bedroom_spines", color=(1, 1, 1)),

    # --- garage (garage.py): white walls, a pale resin floor, bright LED lines ---
    "garage_albedo": dict(kind="vertex", room="garage", albedo=True, color=(1, 1, 1)),
    "garage_white": dict(kind="vertex", room="garage", color=(0.91, 0.91, 0.90)),
    "garage_black": dict(kind="vertex", room="garage", color=(0.03, 0.03, 0.035)),
    "garage_rubber": dict(kind="vertex", room="garage", color=(0.10, 0.10, 0.105)),
    "garage_fob":  dict(kind="vertex", room="garage", color=(0.05, 0.05, 0.055)),
    "garage_fob_glass": dict(kind="vertex", room="garage", color=(0.11, 0.13, 0.15)),     # the Vanquish key's smoked glass
    "garage_red":  dict(kind="vertex", room="garage", color=(0.72, 0.08, 0.06)),
    "garage_green": dict(kind="emissive", room="garage", color=(0.35, 1.0, 0.55), strength=2.0),
    "garage_cable": dict(kind="vertex", room="garage", color=(0.06, 0.06, 0.065)),
    "garage_led":  dict(kind="emissive", room="garage", color=(0.94, 0.97, 1.0), strength=5.0),
    "garage_glass": dict(kind="glass", room="garage", color=(0.86, 0.90, 0.90), opacity=0.10, reflect=0.25),
    "garage_tags": dict(kind="vertex", room="garage", img="garage_tags", color=(1, 1, 1)),        # the hooks' labels
    "garage_screen": dict(kind="screen", room="garage", img="garage_calendar", color=(1, 1, 1), strength=1.1),
    # the covered car standing in for the real one, and the tool chest
    "car_cover":   dict(kind="vertex", room="garage", color=(0.19, 0.19, 0.20), double_sided=True),
    "garage_rim":  dict(kind="vertex", room="garage", color=(0.22, 0.22, 0.23)),
    "garage_chest": dict(kind="vertex", room="garage", color=(0.12, 0.12, 0.13)),
    "garage_bottle_blue": dict(kind="vertex", room="garage", color=(0.16, 0.36, 0.70)),
    "garage_towel": dict(kind="vertex", room="garage", color=(0.36, 0.46, 0.62)),

    # --- foyer (foyer.py): the dark stone wall, pale stone, oak and brass ---
    "foyer_stone": dict(kind="vertex", room="foyer", tex="granite_tile", tile=2.3, tint=(0.30, 0.29, 0.30)),
    "foyer_oak":   dict(kind="vertex", room="foyer", tex="oak_veneer_01", tile=1.4, tint=(0.95, 0.88, 0.80)),
    "foyer_albedo": dict(kind="vertex", room="foyer", albedo=True, color=(1, 1, 1)),
    # the plinth's pale stone, plain (the marble texture is a tiled floor's: it showed grout lines)
    "plinth_stone": dict(kind="vertex", room="foyer", color=(0.80, 0.76, 0.68)),
    "foyer_black": dict(kind="vertex", room="foyer", color=(0.04, 0.04, 0.045)),
    "foyer_brass": dict(kind="vertex", room="foyer", color=(0.82, 0.63, 0.37)),
    "foyer_glass": dict(kind="glass", room="foyer", color=(0.78, 0.88, 0.86), opacity=0.16, reflect=0.45),
    "foyer_glass_edge": dict(kind="vertex", room="foyer", color=(0.48, 0.64, 0.58)),
    "stair_dark":  dict(kind="vertex", room="foyer", color=(0.15, 0.145, 0.14)),
    "foyer_vessel": dict(kind="vertex", room="foyer", color=(0.11, 0.10, 0.095)),
    "foyer_ceramic": dict(kind="vertex", room="foyer", color=(0.80, 0.76, 0.68)),
    "foyer_ceramic_dark": dict(kind="vertex", room="foyer", color=(0.14, 0.13, 0.12)),
    "foyer_bowl":  dict(kind="vertex", room="foyer", color=(0.30, 0.27, 0.24)),
    "foyer_shade": dict(kind="emissive", room="foyer", color=(1.0, 0.82, 0.62), strength=1.5),
    "foyer_branch": dict(kind="vertex", room="foyer", color=(0.34, 0.25, 0.17)),
    "foyer_pot":   dict(kind="vertex", room="foyer", color=(0.84, 0.80, 0.72)),
    "foyer_canvas_edge": dict(kind="vertex", room="foyer", color=(0.80, 0.76, 0.70)),
    "foyer_painting": dict(kind="vertex", room="foyer", img="foyer_painting", color=(1, 1, 1)),
    # the fig by the study door (Poly Haven's potted_plant_01), as in the living room
    "foyer_fig_leaves": dict(kind="vertex", room="foyer", img="fig_leaves", size=256, double_sided=True,
                             src="potted_plant_01/textures/potted_plant_01_leaves_diff_1k.jpg", color=(1, 1, 1)),
    "foyer_fig_stems": dict(kind="vertex", room="foyer", img="fig_stems", size=256,
                            src="potted_plant_01/textures/potted_plant_01_pot_diff_1k.jpg", color=(1, 1, 1)),
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
            elif "img" in m or ("moodboard" in m and picture_path(name).exists()):
                # One picture over the object's own UVs, times a plain colour. (A moodboard
                # frame gets one of your pictures only in Blender's renders; on the site the
                # page picks them at random each time the room opens.)
                node = new("ShaderNodeTexImage")
                node.image = image(picture_path(m.get("img", name)))
                coords = new("ShaderNodeUVMap")
                coords.uv_map = "UVMap"
                link(coords.outputs["UV"], node.inputs["Vector"])
                mul = new("ShaderNodeVectorMath")
                mul.operation = "MULTIPLY"
                mul.inputs[1].default_value = (1, 1, 1) if "moodboard" in m else srgb_to_linear(m.get("color", (1, 1, 1)))
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
