# Progress

Where the villa build has got to, what was decided along the way, the traps
found so far, and what comes next. `BUILD_BRIEF.md` is the plan; this is the log.

## Done

**Step 1: shell and exterior.** The house, grounds, sky and golden-hour light,
baked and running in the browser with the blockout's navigation (three views,
labels, side panel, rooms menu, Skip to resume, `#room` links).

**Fixes after reviewing step 1:**

- A smaller forecourt in mixed stone: a granite-sett court, pale slabs to the
  front door, dark granite bands between them, a long agave planter, a low wall,
  a reflecting pool in front of the study and gym, uplights and step lights.
- Soft edges everywhere paving meets sand: kerbs, gravel borders, rocks, shrubs
  and agaves.
- The drive is pale granite setts instead of asphalt.
- Palm trunks are ringed.
- Sheer curtains hang inside the upstairs glass.

**Step 3: the dining room, fully furnished.** It is the template for the other
rooms' level of detail. In it:
- a walnut table for eight on dark stone legs, with leather chairs on a wool rug;
- two low bronze pendants over the table;
- a walnut sideboard with a bronze horse's head and two vases on it;
- an original painting on the solid wall;
- a fig tree and a philodendron by the pool glass;
- a real game in progress.

Opening the room drops the camera into the visitor's seat over the board. The
furniture loads in the background after the landing view. Previews:
`previews/dining.jpg`, `chess.jpg` and their `browser_*` pairs.

**Step 4: the pool deck and the "Get in touch" moment.** The deck is furnished
to the dining room's standard. Opening the pool drops the camera onto the
visitor's lounger, looking out over the pool past my lounger and the side table,
with the visitor's hand holding a martini at the bottom of the frame. In it:
- two long teak loungers side by side at the pool's south-west corner, both
  facing the water, each turned 12° in toward the other, in the low sun, with a
  travertine side table between them and a cream cantilever parasol behind;
- the visitor's lounger with a folded towel at its foot;
- mine set as if I'd just stepped away: a navy beach towel left spread over it,
  my sunglasses, an isshobin of sake with an original label and a stoneware cup
  on the table, my loafers slipped off beside the head of my lounger;
- my contact card (placeholders) standing on the table, turned and tilted toward
  the visitor; on the site, clicking it opens the "Get in touch" panel;
- a fire-pit lounge of low sofas on the south side, in the evening shade;
- quiver trees (Poly Haven) and palms in big stone planters, lanterns and uplights.

My character is set aside until the end; see "The pool deck" below.

Previews: `previews/deck.jpg`, `pool_moment.jpg`, `pool.jpg` and their
`browser_*` pairs.

**Step 2, the car, is on hold** at your request. The researched options for the
model and the engine sound are in the conversation history; nothing was bought.

**Repo and hosting.** The code is on GitHub at Zvezda4994/villa-portfolio, and the
site is live at https://zvezda4994.github.io/villa-portfolio/. Every push to `main`
runs `npm test` and then publishes `web/` to GitHub Pages, the same setup as the
chess project.

**The lighting in the repo is mostly a draft bake.** It's quick to make but
blotchy. Two lightmaps have the full bake since step 4: `ext` (the house's
outside, the paving and the pool) and `pol` (the pool room's furniture), to
check the camera moment. The rest, and all the per-vertex light, wait for the
full bake once the rooms are done.

## Decisions

These came from the brief or were agreed while building. Most are expensive to
change later.

**Look and light**

- Sun 15° above the horizon, 58° round to the front left (`blender/villa/config.py`).
  Changing it means re-baking everything.
- Blender's own sky model makes the sky. The sun is split out of it and warmed
  up, which gives warm light with cool blue-grey shade.
- Colour is AgX with the "Medium High Contrast" look in Blender. three.js has
  AgX but no looks, so the site adds the look itself: a contrast of 1.2 around
  0.7 in AgX's log space, found by fitting the formula to Blender's output.
- Inside, the lamps are on in every room, warm white.

**Layout**

- Room positions follow the blockout.
- Upstairs is a full floor:
  - back row: main bedroom, games room, trophy room (opening onto the terrace over the pool);
  - front row: a lounge, the stair landing, the library.
- The dark stone wall runs from the foyer out through the front and up past the
  roof. It stays as it is.
- The foyer-to-dining doorway sits at the top end of the stairs.
- Space for the later "vault" is a lower level off the foyer, beside the stairs.
  Nothing blocks it.
- The car will park on the setts court, angled to face the landing camera.

**Furnishing a room** (the pattern the dining room sets)

- Build everything in `blender/villa/<room>.py` inside `with b.room("<room>"):`.
  Those parts are exported to `web/assets/rooms/<room>.glb`, not `villa.glb`, and
  the site fetches them after the first view, one room at a time.
- Big flat furniture (tables, rugs, pictures) uses the room's own lightmap, an
  entry in `config.ATLASES` with `room=`. Curved things and downloaded models are
  lit per vertex.
- Downloaded models keep their colour map ("img" + "src" in `materials.py`); the
  build thins dense meshes (`props.load(..., thin=...)`) and drops parts it
  replaces (pots, soil).
- Every material only the room uses gets `room="<room>"`, so its picture isn't
  part of the first-view download. The tests check this.
- A furnished room turns its general ceiling light down (`CEILING_LIGHT`) and
  adds its own lamps (`LAMPS`), which `lighting.py` picks up.
- Add its review cameras to `PREVIEW_CAMERAS`; they also work as `?shot=` in the site.
- **Budget: around 4 MB per room.** That means the room's own file, the pictures
  only it uses, and its lightmap (a seated figure is counted separately, since it
  can come and go). Prefer materials other rooms already load, keep pictures at
  512 px or less, and thin dense models. `npm test` checks it: new rooms fail
  above 4.5 MB.
- **The dining room is over, at 5.1 MB** (about 5.9 MB once its lightmap gets the
  full bake): `dining.glb` 1.85 MB, the chessboard picture 0.94 MB, the rest small.
  The test lets it through at up to 6.5 MB until step 6 brings it down.

**The dining room**

- The game: Ruy Lopez, Chigorin variation, after 16...Bd7, White to move
  (`config.CHESS_FEN`). The two pawns taken so far stand beside the board.
  Change the FEN to set up any other position.
- The visitor plays White, from the seat facing the pool glass. The room's
  camera is that seat looking down over the board (`dining.CHESS_CAM`).
- The figure across the board (your decision, recorded in `BUILD_BRIEF.md`): a
  credited fan-made model, supplied by you, in a slot built for quick removal.
  No figure is in the repo or on the site yet. The chair is set slightly back
  and turned so it looks right empty or occupied. How to add one and how to take
  it down are below, under "The figure at the table".
- The fish tank in the living room isn't built yet; nothing in the dining room
  blocks the living room's walls.

**The figure at the table**

Where it goes and what the build does with it (`blender/villa/figure.py`):

- **The file** goes in `assets_src/figures/` (git ignores `assets_src/`). It must be
  glTF or GLB, already in a seated pose. If it's rigged and comes with a sitting
  animation, name it in `action` instead. Most model sites offer a glTF download.
- **The setting** is `FIGURE` in `blender/villa/config.py`. The commented example
  there lists every field. `credit` and `link` are required; the build refuses
  to export a figure without them, and the tests fail too.
- **`npm run figure`** fits it into the opponent's chair: it scales it to `height`
  and sets its back against the cushion, facing the board. It thins anything over
  `max_triangles`, bakes its light, and writes `web/assets/figures/opponent.glb`,
  its pictures (`textures/figure_*.ktx2`) and its credit into the manifest. Use
  `turn` and `offset` to adjust the fit. Check it with `?shot=chess`.
- **The credit** shows in the dining room panel exactly as written, with a link
  to the model's page. Add the matching row to `CREDITS.md`.
- **The figure stays out of the room's lightmaps.** It casts no baked shadow, so
  taking it out leaves nothing behind and needs no re-bake. Its own lighting is
  baked into its vertices, so very low-poly models with long, thin faces light
  poorly; most character models are dense enough.

**Taking it down** (about two minutes in all):

1. In `blender/villa/config.py`, set `FIGURE = None`.
2. Run `npm run figure`. It deletes the figure's files and its credit from the
   manifest in a couple of seconds, and needs no Blender scene.
3. Delete its row from `CREDITS.md`, and its source file from `assets_src/figures/`.
4. `npm test`, commit, push. Pages redeploys in a minute or two.

The exported file stays in Git history after that. If a request covers the repo
itself, not just the site, the history has to be rewritten (for example with
`git filter-repo`) and force-pushed.

Tested with a plain stand-in mannequin: it sat in the chair, the credit
appeared, and taking it down took 1.7 s. The stand-in was deleted afterwards.

**The pool deck**

- **My character is set aside until the end** (your call, 17 Nov 2026). It will
  be redone from a proper base mesh, not built from primitives. The scripted
  version (`character.py`, `sdf.py`, `character_preview.py` and its review
  renders) is in `_shelved/`, which Git ignores; nothing in the build imports it.
  `_shelved/README.md` says what's there and what was learned making it.
- **Frozen meshes.** The visitor's hand and my loafers were made with that
  scripted code. They're kept as plain meshes in `blender/villa/frozen/`
  (`visitor_hand.npz`, `loafer.npz`), which `pool.py` loads, so the build needs
  none of the shelved code. The hand is stored in the camera's own frame, so it
  follows `MOMENT_CAM` if the camera moves. `_shelved/freeze_meshes.py` makes
  both again, but only on this machine. Replace them when the character is redone.
- **Layout** (`PAIR_CENTRE`, `TOE_IN` in `pool.py`): the pair sits square to the
  pool at its south-west corner, its front corners 0.75 m short of the water.
  That's the only stretch of the pool's edge still in the sun; further east
  the house's shadow covers the deck. Facing north, the loungers take the low
  sun from the front left, so the cushions, and whoever lies on them, are lit.
- **No pergola.** It covered the old spot only. At the water's edge it would
  crowd the pool, its posts would throw long shadows across both loungers at
  this sun angle, and at 15° its roof shades nothing near it anyway.
- **The parasol** (`PARASOL` in `pool.py`) stands behind the pair: its mast 2 m
  behind the head ends, its 2.7 m canopy held over them at 2.25 to 2.55 m. At 15°
  the sun passes under any canopy, so its shadow lands about 9 m to the south-east,
  off the deck, and the mast's shadow runs away behind it. Moving the canopy
  doesn't change that; moving the mast in front of the loungers would.
- **The canopy is tensioned fabric** (`canopy` and the `CANOPY_*` numbers in
  `pool.py`): eight panels, each stretched straight between two ribs and sagging
  about 2 cm at the middle of its edge, its free edge pulled in a little between
  the rib tips the way stretched cloth scallops. The ribs bow up slightly from a
  capped peak 36 cm above the edge. A raised seam a shade darker than the canvas
  runs along every rib, and a rolled hem about 1 cm thick wraps the edge.
  Underneath: the ribs, the hub and a cap on each rib's tip.
- **The loafers stay out of the moment's frame**, beside the head of my lounger.
  The only deck in the frame next to the table is too tight for a whole shoe:
  the table or the visitor's cushion always cut one off.
- **The deck is back to its old width on the west** (`DECK_X` from -7). The
  widening was for the pergola; the tree, palm and lantern on it moved in.
- **Trees: Poly Haven's Quiver Tree 02** (Aloidendron, from its Namaqualand
  set), in all four planters, turned and sized differently. Thinned from 82k
  triangles to 6.6k, its picture at 256 px. Quiver Tree 01 was tried too and
  dropped: tall and spindly, it read as a sickly palm in a planter.
- **The camera moment** (`MOMENT_EYE` and `MOMENT_AIM` in `pool.py` give
  `MOMENT_CAM`; the "pool" entry in `rooms.js` repeats it): the visitor sits on
  their lounger, head up, eyes at 0.98 m, turned 35° toward my lounger and 8°
  down, so my lounger and the table take the left third and the pool and the
  house the rest. The eye can't go further back: the top of the lounger's raised
  back is right behind it and fills the frame. `npm test` fails if `rooms.js`
  and the exported camera drift apart.
- **The contact card** is 21 x 13 cm and leans back just enough to face the
  moment camera's eye. On the site it's clickable: the "pool" stop in `rooms.js`
  lists its materials under `click`, `world.js` hands back the meshes drawn with
  them, and `main.js` raycasts on click or tap. It opens the "Get in touch"
  panel, and flies to the lounger first if you're elsewhere. A hit only counts
  if nothing solid is in front of the card, and the mouse pointer turns into a
  hand over it.
- **The visitor's hand** is exported tagged `attach: camera` and re-hung on the
  camera by `world.js` while you are in the pool stop and within about a metre
  of the seat. It casts no shadow into the bake (the shadow would stay behind
  when the camera moves) and appears only in the `pool_moment` review render.
- **My towel is navy** with a cream band across each end; a white one vanished
  against the cream cushions. `draped_towel` lays it along the seat, up the back,
  over the top and down behind, its sides falling over the cushions' edges.
- **Skin colour is painted per vertex** (the visitor's hand) and multiplied into
  the baked light at bake time, so the site needs nothing new. Materials marked
  `albedo` in `materials.py` work this way.
- **The card's text** reads `CONTACT_CARD` in `config.py`. Change it and run
  `npm run build` (or scene, bake:draft, export) to reprint it.
- **The deck is 2 m wider to the south** (`DECK_Z`), for the fire-pit lounge.

**Pipeline**

- Everything is built by Python in `blender/`. Nothing is edited by hand in Blender.
  The order is `build_scene` → `bake_lightmaps` → `export_web`, or `npm run build` for all three.
- Lighting lives in four 2048 px lightmaps: outside, ground floor, upstairs and sand.
  Each also has a 512 px copy that loads first.
- Light is stored as 8-bit sRGB after dividing by 4 (`LIGHT_RANGE`), and the site
  multiplies it back.
- Small bumpy things (plants, rocks, frames, curtains, hills) keep their light in
  their vertices instead of a texture.
- Formats:
  - textures and lightmaps: KTX2 (UASTC with Zstandard), with mipmaps;
  - model: glTF with Meshopt compression, normals left out (the site rebuilds the ones it needs);
  - sky and reflections: Radiance `.hdr` panoramas.
- Water reflects a panorama taken from just above it (a "probe"), not the open
  sky. There are two: the pool at the back and the reflecting pool at the front.
  Glass reflects the open sky.
- The site has no build step. three.js 0.170.0 loads from jsDelivr, pinned to the
  same version everywhere (a test checks this).
- Textures are CC0 from Poly Haven, listed in `CREDITS.md`. Photo textures are
  evened out before tiling (`textures.py`) so the sand doesn't stripe.
- Quick draft bakes are for checking work. The full bake (768 samples, about 17
  minutes on this laptop's RTX 3070 Ti) happens once at the end.
- One lightmap can be baked at full quality on its own: `npm run bake -- ext pol`
  bakes only those two (5.3 minutes: `ext` 265 s at 2048 px, `pol` 47 s at
  1024 px). Run `npm run bake:draft` first after any change to the scene, since
  only a run over everything bakes the per-vertex light, then `npm run export`.
- CI runs on Node 22; the chess project uses 20, which is now out of support.

## Gotchas found

The traps hit so far, so they don't get rediscovered.

1. **Blender 5.3's .hdr saving changes the values.** Darks came out about 5×
   brighter and the sun 350× dimmer, which washed out the browser's sky.
   `villa/hdr.py` writes the files instead, and each one is read back and checked.
   Blender's .hdr loading isn't trusted either.
2. **Blender's panorama layout isn't three.js's.**
   - Rows are plain latitude.
   - Column 0 starts at 90° of longitude, so the image needs a quarter-turn shift.
   - `export_web._layout` measures this by rendering a panorama whose colour is
     each pixel's direction. The earlier approach, guessing from where a marker
     landed, happened to work but was fragile.
3. **Blender's bundled KTX2 encoder makes no mipmaps.** Without them, tiled
   textures shimmer. `villa/ktx2.py` encodes each size separately and stitches
   the levels into one file. Sizes must be multiples of 4.
4. **Water needs UVs for its ripples.** The export strips UVs from things without
   a lightmap. Without them the ripple normal map smears into bright streaks, so
   water keeps its UVs.
5. **Reflections from a sky panorama ignore what's in the way.** Water looked
   white because it reflected bright sky that the house actually hides; probes
   fixed it. Glass still has this problem, slightly: rooms look a bit pale
   through upstairs glass from low angles.
6. **OrbitControls moved low cameras.** Its "don't look up from below" limit
   raised any camera sitting below its target, so the browser review pictures
   were framed wrong. Review shots now lift the limit; normal navigation keeps it.
7. **Two three.js shader patches depend on the pinned version.**
   - The baked-light patch removes three.js's own sky lighting, which is already in the lightmaps.
   - The tone-mapping patch adds the AgX look.
   - Both find text inside three.js's shader code and log a warning if it has changed.
   - Check both whenever three.js is upgraded, along with the KTX2 transcoder
     path, which must use the same version.
8. **Cycles can't denoise a bake.** Draft bakes look blotchy for that reason. The
   full bake has enough samples that it doesn't matter.
9. **The sun in the sky model is nearly white at 15°.** It's tinted separately
   by subtracting a sun-less copy of the sky. Caustics are off, or glass throws
   speckles of sun into the bake.
10. **Windows line endings and binary files.** Git on Windows rewrites line
    endings, and an `.hdr` file starts with a text header, so Git could mistake
    it for text and corrupt it. `.gitattributes` marks every asset type as binary.
11. **Shallow basins and the sand.** The sand mesh is too coarse to cut neat
    holes in. The back pool gets a hole hidden under its wide deck. The
    reflecting pool is only a few centimetres deep, like a real water mirror,
    so its floor sits above the sand and needs no hole.
12. **Pages must be switched on once per repo.** The first deploy failed at
    "configure pages" because the repo had Pages off. The fix was Settings → Pages
    → Source: GitHub Actions. It's on now.
13. **Every bake commit adds its lightmaps to Git history.** That's about 2 MB
    for a draft and 16 MB for a full bake. Commit full bakes only at milestones.
    If history gets heavy, consider Git LFS (the Pages workflow would need
    `lfs: true` on checkout).
14. **Tools on this machine.** The GitHub CLI isn't installed; pushes use Git's
    saved credentials. Blender is the Steam copy at
    `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe`, which
    `tools/blender.mjs` finds by itself.
15. **The preview server's port.** Another session can hold port 5173. The
    `villa` entry in `.claude/launch.json` no longer passes a port, and
    `tools/serve.py` takes `$PORT` from the preview tool when it moves to another.
16. **Furniture pictures are big in UASTC.** A 1024 px picture is about 1 MB as
    KTX2, a 512 px one about 0.3 MB. The dining room uses 512 px or less except
    the chessboard (1024, it fills the close-up). That is most of why the dining
    room is over its 4 MB budget. Options for step 6: ETC1S for furniture pictures
    (far smaller, a little softer), a 512 px chessboard for phones, and fewer
    one-off pictures.
17. **Draft bakes look worst from inside a room.** At eye level the quarter-size,
    48-sample draft makes walls, ceilings and the rug look blocky and mottled in
    the browser. The Blender previews show the intended look; the full bake fixes
    the site. Checked on 18 Nov 2026: after a full bake of `ext` and `pol` the
    house wall, soffit, deck and table in the pool moment came out clean in the
    browser, with no blocks from texture compression and no visible lightmap
    texels at 2048 px. The rooms seen through the glass stayed mottled; they're
    in `gnd`, which still has the draft.
18. **Importing a glTF leaves things behind.** `props.load` removes the imported
    objects, meshes and unused materials and images straight away, so the saved
    scene only holds what `place` added.
19. **`?view=` has to come before `?shot=`.** Switching views resets the camera's
    minimum distance, which pushed close-up review cameras back. `main.js` now
    applies the view first.
20. **Blender's decimation keeps vertex-group weight 0 exactly as it is.** Weights
    are not a soft preference: 0 is locked, 1 is free. To thin a mesh but keep
    detail in some parts (a face, hands), thin it in passes, each with the
    others locked.
21. **Site coordinates are mirrored from a plan drawn with the house at the top.**
    Facing the house from the pool deck (looking toward +z), +x is on your left.
    Easy to get backwards when placing things beside a camera.
22. **Blender's glTF exporter loses position precision far from the origin.** With
    Meshopt compression on, it stores positions with a 12-bit mantissa per vertex
    (`EXP_FILTER_BITS` in its `meshopt` module), so they snap to a grid about 1 cm
    wide at the pool deck, 18 m out. The house didn't mind; the pool's sunglasses
    and the visitor's hand came out blocky, and my towel sank into its cushion.
    `export_web.py` now sets 16 bits for the room files (under 1 mm) and leaves
    the house at 12. It changes the exporter's own setting while it runs, so
    check it still exists after a Blender upgrade (the export warns if not). Blender's
    own renders never show the problem; only the exported file has it.
23. **`props.load` used to delete every unused material after an import.** The
    dining room loads its models before the scene's materials exist, so that was
    harmless; the pool loads its trees after, when none of the scene's own
    materials has a user yet, and the build fell over. It now removes only what
    the import brought in.

## Next

**Waiting on you**

- The figure for the dining table: put the model you choose in
  `assets_src/figures/`, fill in `FIGURE` with its credit and link, and run
  `npm run figure` (steps above).
- The car (step 2): pick a model and an engine sound from the options shown,
  whenever you want to pick it back up.
- Panel copy: VAREK and Turo numbers, the trophy list, the library list, the stack
  list, contact details. The contact details also go on the card on the pool
  deck's table (`CONTACT_CARD` in `config.py`).
- For later steps:
  - a choice of chess position for the dining table;
  - approval before buying anything over about $60, most likely the car model.

**Build order from here**

2. **The car (on hold).** A licensed model of the latest Vanquish in black or
   dark grey, parked on the setts court facing the landing camera. Headlights come
   on and a licensed engine start plays on click (sound only after a click). The
   model has to be shipped encrypted or in a non-standard format: CGTrader's
   royalty-free license allows web use only if visitors can't pull the model out.
5. **The remaining rooms,** one at a time as each room's story arrives. When a
   room is furnished, its curtains can go.
6. **Polish.** The brief's performance section now has targets and no hard
   total size limit. Step 6 builds them:
   - **A still of the landing shot within about 1 second.** It's a full-quality
     render from the exact landing camera; the live 3D fades in over it from the
     same camera. On a slow connection (about 150 KB/s in testing) the live site
     took about 90 seconds to show anything, so this matters most.
   - **The landing view interactive in about 10 MB or less** (10.8 MB now). Load
     512 px colour textures before the 1024 px ones, and look again at the
     cobblestone, sand and marble textures, the three largest.
   - **Each room's own download around 4 MB.**
     - Materials shared between rooms load once and are reused. Today a room
       material's picture is tied to one room; walnut veneer, for one, should
       become shared.
     - Repeated objects are instanced (the eight chairs, later the books and
       bottles). Their light is baked per vertex and differs per copy, so
       instancing needs that light kept per instance (or a shared average).
       Decide which in step 6.
     - Bring the dining room under budget (see "Furnishing a room").
   - **A still for every room**, rendered from its camera (`PREVIEW_CAMERAS`
     already has the dining one), shown while that room loads.
   - **Prefetching.** Start loading a room when the visitor hovers over its label,
     and the neighbouring rooms while they're in one. This needs a room-to-room
     neighbour list.
   - **Phones get lower-resolution textures** (a second, smaller set of pictures
     and lightmaps); desktops get the full set.
   - **While the still is showing and the 3D isn't ready:**
     - Labels sit on the still at their exact 3D positions, projected with the
       still's own camera.
     - Clicking a label opens its panel and swaps in that room's still. The 3D
       appears at that room's camera when it's ready.
     - The Rooms menu and Skip to resume work at once; they need no 3D.
     - Dragging pans the still slightly and shows the loading percentage. The
       drag isn't replayed when the 3D arrives.
   - Phone layout and link previews. On a phone held upright the pool moment's
     martini sits outside the narrow frame; place it from the screen's shape there.
   - The pool room's lightmap (`pol`) gets the full bake with everything else.
   - Then the full-quality bake.
7. **My character, at the end.** Redone from a proper base mesh (not generated
   from primitives), reclining on my lounger. Then the stepped-away setting
   comes off it: the sunglasses go back on, the towel and loafers stay or go as
   suits the pose, and the visitor's hand and loafers in `frozen/` are replaced
   to match. The reference photos are needed then.

**Smaller things noted along the way**

- The glass reflections could use a probe in front of the house, like the water.
- The far hills are hazier in the browser than in Blender, on purpose.
- Sand facing the sun lacks Cycles' faint sheen.
