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

**Step 5, batch 1: the study and the games room** (approved 19 Nov 2026). Both are
furnished to the dining room's standard. Opening either room on the site drops the
camera inside it (`view` with `near` in `rooms.js`, like the dining room).

The study (VAREK), warm and late-evening (`blender/villa/study.py`):
- a 2.6 m whiteboard on the dark stone wall with "call comes in → AI agent answers
  → appointment booked" drawn in marker (Kalam), a tray of markers, a brass
  picture light; a tall fig on one side, a slim smoked-oak bookshelf on the other;
- a deep moss-green sofa facing the board across a glass and brass coffee table,
  on an original Persian-style rug, worn and faded, with fringes; a brass floor lamp;
- a smoked-oak desk at the front glass with a brass task lamp, an open journal
  (notes on the call flow), a pen and a cup, and a shaped, padded swivel chair;
- a low oak credenza with books, a brass sphere and a succulent.

The games room (CS2), black and white and lit by its screens (`blender/villa/games.py`):
- charcoal walls and ceiling laid over the house's own, a blackout blind over the
  window, the ceiling downlights off and the sheers gone;
- a white desk; a 32" OLED (black wallpaper) and a second monitor (win-probability
  chart, "Team Alpha" and "Team Bravo" as placeholders) on a white dual arm whose
  arms show under the screens; a light bar, a bias light and an LED wash behind the desk;
- a white keyboard and mouse on a black mat, a white showcase PC on a plinth (glass
  front and side, board, pump, RAM, graphics card, seven glowing fans), the white chair;
- a small white shelf with the five games, white spines and black titles: Yakuza 0,
  Hotline Miami, S.T.A.L.K.E.R., Titanfall 2, Metro Exodus;
- black slat acoustic panels lit from below, a large framed black and white print
  (an original dune landscape) under its own spot, a philodendron with an uplight,
  an off-white sofa with a low round black table across the room.

Previews: `previews/study.jpg`, `study_desk.jpg`, `games.jpg`, `games_desk.jpg`,
`games_shelf.jpg` and their `browser_*` pairs. Downloads: the
study 2.3 MB, the games room 1.1 MB (draft lightmaps; the full bake adds about 0.8 MB each).

**Step 5, batch 2: the kitchen and the gym** (approved 19 Nov 2026, the gym after a
second pass). Opening either room on the site drops the camera inside it.

The kitchen (tools and stack), bright and clean, white, pale oak and quartz
(`blender/villa/kitchen.py`):
- open oak shelves over white tiles on the garage wall, an LED strip under each, with
  23 jars, canisters and tins labelled in plain type with your tools. The labels
  are in `data/kitchen_labels.txt`, one per line; the shelves re-space themselves for
  any number, and long names shrink to fit their label;
- a counter under the shelves with an espresso machine, a crock of wooden spoons
  and a chopping board;
- a quartz island with waterfall ends, three oak stools, three opal pendants, a
  bowl of lemons and the visitor's coffee;
- counters under both windows (sink, tall tap, induction hob, ceiling extractor),
  tall white units with the fridge and two ovens, and a fig by the side window.

The gym (boxing), black mats under hard white light (`blender/villa/gym.py`):
- black rubber mats, kept clear but for the heavy bag (black, red bands, on chains);
  the speed bag on its wall platform; three bare linear LEDs hung from the ceiling,
  the house's downlights off;
- the gear wall, left of the living room door: an oak bench with an open duffel
  (shin and instep guards sticking up out of it), two rolled hand wraps (one partly
  unrolled) and a bottle; above it a rack with three pairs of gloves (black, red,
  black), and the worn brown lace-up sparring gloves hung from a hook by their laces;
- right of the door, a small whiteboard with the round plan in marker ("12 x 3 min
  open sparring" boxed in red); the round timer at 3:00 over the door; a jump rope.

Previews: `previews/kitchen.jpg`, `kitchen_shelf.jpg`, `kitchen_wide.jpg`, `gym.jpg`,
`gym_gear.jpg`, `gym_board.jpg`, `gym_wide.jpg`, and the `browser_*` pairs of the
kitchen, kitchen_shelf, gym, gym_gear and gym_board. Downloads: the kitchen
2.3 MB (the label picture 0.65 MB of it), the gym 0.8 MB (no lightmap).

**The lighting in the repo is a draft bake, all of it.** Only draft lightmaps are
committed (your rule, 18 Nov 2026): `npm run bake:draft` before any commit that
touches `web/assets/lightmaps/`. The full bake is run once, at the end. The draft
looks blotchy on walls, floors and lightmapped furniture in the browser; the
Blender previews show the intended look.

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
- Newer rooms build with `blender/villa/kit.py`: `Kit(b, group, atlas)` gives boxes,
  rounded and shapeable cushions (`cushion`), lathes, tubes, swept arms and flat
  grids in a piece's own `Frame`. `study.task_chair`, `study.sofa`, `book_upright`
  and `book_flat` are reusable furniture. `Kit.block` is a box with every face a
  fine grid lit per vertex (cabinet fronts, the island, shelves seen from below);
  `kit.panel` lines a wall; `kit.sweep_geom` gives a tube's points without adding
  it, and `Kit.sweep(..., colors=)` paints one per vertex.
- A room's module also sets `ROOM` and `CEILING_LIGHT`, and may set `CEILING_COLOUR`;
  `lighting.furnished_rooms()` lists the room modules. Room lamps can be `"area"`
  (default), `"spot"` or `"point"`, each with an optional `colour`.
- **Things the draft bake makes blotchy, light per vertex on a grid instead**: a
  signature surface (the whiteboard, the games desk top, the print) looks bad
  mottled in the browser. `Kit.slab` and `kit.grid` make finely divided surfaces
  lit per vertex, which stay smooth at any bake quality.
- Lettering (labels, spines, screens, whiteboards) is painted by `labels.text_mask`
  with Inter, or a font from `config.FONTS` (downloaded by `fetch_assets.py`).
- Glowing pictures (monitors) use the `screen` material kind. Indoor glass can turn
  its sky reflection down with `reflect`.
- A room can drop its sheer curtains and switch its downlights off (`NO_SHEERS`,
  `LIGHTS_OFF` in `house.py`); it can line its walls (see `games.walls`).
- **Line the walls the room's view looks at** with plaster lit per vertex
  (`kit.panel` with `plaster_v`, as `kitchen.walls` and `gym.walls` do). The house's
  own walls are on the ground and upper lightmaps, which the draft leaves very
  blotchy close up. Lay linings 12 mm off the wall (gotcha 30), and start them at
  the top of any counter standing against them (gotcha 26).
- A room with nothing big and flat can do without a lightmap: the gym has none
  (`Kit(b, G, None)`).
- Worn or uneven colour on a small thing goes per vertex: an `albedo` material and
  `colors=` on its meshes (the brown gloves, `gym._wear`).
- Lists the user edits (labels, titles) go in `data/`, read by the room's script at
  build time; rebuild to reprint them.
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

**The study**

- Layout: the lounge faces the whiteboard on the dark stone wall (`LOUNGE_Z`); the
  desk faces the front glass; the credenza is on the gym wall by the desk. The
  site's view is `STUDY_CAM`, from behind the sofa.
- The rug is painted by `study.paint_rug` (an original medallion design, then
  knots, abrash, wear and fading). The whiteboard by `paint_whiteboard`, the
  journal by `paint_journal`. Change the text there and rebuild.
- Brass on lamps is pale (`lamp_brass`): the site shows only diffuse light, so a
  realistic brass reads as black in the dim corner by the glass.

**The games room**

- Strictly black and white: charcoal lining (`wall_charcoal` 0.22, ceiling 0.17),
  white furniture, cool-white light only (`CEILING_COLOUR`). The ceiling lining is in
  the "roof" group so it lifts off with the roof in the Upstairs view.
- The setup is built in `setup_frame()`: origin on the bedroom wall at the desk's
  middle, +z into the room, +x to the sitter's right. The site's view is
  `GAMES_CAM`, from beside the sofa; `DESK_CAM` (`games_desk`) is the close-up.
- Screen content: `paint_wallpaper` (main), `paint_chart` (team names in `TEAMS`),
  `paint_spines` (titles in `GAMES`). The print: `paint_print`.

**The kitchen**

- Layout: the labelled shelves and their counter on the garage wall, between the
  garage door and the dining room wall (`RUN`); the island in front of them, its
  stools on the window side; counters under the back and side windows; tall units
  between the west wall and the garage door.
- The site's view is `KITCHEN_CAM`, sitting on the right-hand stool, looking across
  the island at the shelves; `kitchen_shelf` is the close-up where every label reads.
- Labels: `data/kitchen_labels.txt`, top shelf first, left to right. `paint_labels`
  sets them in Inter in one picture (4 across, 256 x 144 px each) and fits each to
  its label (gotcha 32). Which container a label goes on (jar, canister, three kinds
  of tin) follows its position (`KINDS`, `container_spec`).
- The tiles stand 14 mm off the wall (`TILE_Z`, gotcha 30) and are laid in strips
  between the shelves (gotcha 26). The tile picture is painted by `paint_tiles`.

**The gym**

- Layout: the gear wall left of the living room door (`GEAR_BENCH`, `RACK`, `HOOK`),
  the whiteboard right of it (`BOARD`), the speed bag next to the east glass, the
  heavy bag on the mat (`HEAVY_BAG`), placed so the site's view sees past it.
- The site's view is `GYM_CAM`, standing on the mat behind the heavy bag, looking at
  the gear wall, the bag in the left foreground; `gym_gear` and `gym_board` are the
  close-ups, `gym_wide` the whole room. A bench by the front glass is left from the
  first pass.
- Gloves: `glove()` builds any of the kinds in `GLOVES` (lace-up brown, black, red);
  the brown leather's wear is painted by `_wear`. The round plan is `ROUND_PLAN`
  (Kalam, `paint_board`); the timer's face `paint_timer`.
- Shin and instep guards: black with a white stripe down the front. All white, they
  looked like legs sticking out of the bag.

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
    for a draft and 16 MB for a full bake. Commit draft lightmaps only.
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
24. **Browser review shots from a background tab.** With the preview pane in the
    background the page gets no animation frames, so the camera never turned to
    its target and `?save=` pictures looked straight down -z. `main.js` now aims
    the camera when a `?shot=` is set up and again just before saving.
25. **Per-vertex light needs vertices in the open.** A rod whose only rings sit
    inside what it's fixed to, or a shell 3 mm from a second shell, bakes black.
    `Kit.tube` adds a ring every 5 cm; make the inside of a lampshade glow
    (emissive) rather than a second solid skin.
26. **Don't lay a picture over a whole panel lit per vertex.** The panel's points
    under the picture bake dark and the visible border blends toward them and goes
    muddy brown. Build mats and borders as strips round the picture.
27. **Dark rooms need more vertex samples.** The draft's 64 were speckled in the
    games room; the draft now uses 256 for vertex light (seconds, and it lives in
    the room files, not the lightmaps). Lightmaps stay at the draft's 48.
28. **Warm light makes white look beige.** The house's lamp colour is warm; the
    games room's faint ceiling fill tinted every white surface until it was made
    cool (`CEILING_COLOUR`). Very dark walls (0.1) also swallow the LED glows;
    charcoal around 0.2 still reads as charcoal and lets them show.
29. **`_smooth_noise(shape, scale, rng)`: a bigger `scale` is smoother**, not rougher.
30. **The house wall shows through things laid 3 mm in front of it.** The house file
    keeps its positions at 12 bits (gotcha 22), a few millimetres out on the ground
    floor, so a stretch of the kitchen's own wall came forward through its tiles as
    a black strip, in the browser only. Tiles and wall linings now stand 12 to 14 mm
    off the wall.
31. **The export doesn't clear old lightmaps.** When a room drops its lightmap, delete
    its `web/assets/lightmaps/<name>.ktx2` by hand (the gym's was).
32. **Fitting text to a label: measure it small.** Set at full size, a long name
    spills into the next label and measures as no wider than its own. `paint_labels`
    sets every label at 0.4 first, measures, then sets each at the size that fits.

## Next

**Waiting on you**

- The figure for the dining table: put the model you choose in
  `assets_src/figures/`, fill in `FIGURE` with its credit and link, and run
  `npm run figure` (steps above).
- The car (step 2): pick a model and an engine sound from the options shown,
  whenever you want to pick it back up.
- Panel copy, which you're supplying separately (leave the panel text as it is
  until then): VAREK and Turo numbers, the trophy list, contact details. The
  contact details also go on the card on the pool deck's table (`CONTACT_CARD`).
- Images for the living room's gallery wall, in `assets_src/moodboard/` (batch 3).
- For later steps:
  - a choice of chess position for the dining table;
  - approval before buying anything over about $60, most likely the car model.

**Build order from here**

2. **The car (on hold).** A licensed model of the latest Vanquish in black or
   dark grey, parked on the setts court facing the landing camera. Headlights come
   on and a licensed engine start plays on click (sound only after a click). The
   model has to be shipped encrypted or in a non-standard format: CGTrader's
   royalty-free license allows web use only if visitors can't pull the model out.
5. **The remaining rooms (in progress). Next: batch 3, the living room and the library.**
   See "Step 5: the brief for the remaining rooms" below.
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
   - **A ceiling over the ground floor rooms** while the camera is inside one (see
     "Smaller things noted along the way").
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
   - **Games room, two things to consider** (your notes, 19 Nov 2026):
     - the room's label could open the desk view (`games_desk`) instead of the wide
       view (`GAMES_CAM`); or keep the wide view and fill its empty right-hand wall
       and floor;
     - the PC could come off its plinth and go on the desk's left end, or on the floor.
   - Then the full-quality bake.
7. **My character, at the end.** Redone from a proper base mesh (not generated
   from primitives), reclining on my lounger. Then the stepped-away setting
   comes off it: the sunglasses go back on, the towel and loafers stay or go as
   suits the pose, and the visitor's hand and loafers in `frozen/` are replaced
   to match. The reference photos are needed then.

**Smaller things noted along the way**

- **No ceiling over the ground floor rooms on the site.** Opening a ground floor room
  switches to the ground floor view, which hides the upper floor (`setView` in
  `main.js`), and the ceiling belongs to it, so sky shows overhead in the study, the
  dining room, the kitchen and the gym (and in their `browser_*` shots). The Blender
  renders have the ceiling. For step 6: keep the upper floor's underside, or a
  ceiling, showing while the camera is inside a ground floor room.

- The glass reflections could use a probe in front of the house, like the water.
- The far hills are hazier in the browser than in Blender, on purpose.
- Sand facing the sun lacks Cycles' faint sheen.

## Step 5: the brief for the remaining rooms

Your brief for step 5 (18 Nov 2026), kept here so each session can pick up the next
batch. The dining room is the template for the level of detail.

**How each batch runs.** One batch per session: build, `npm run bake:draft`, show
browser shots of each room (and the Blender renders of the same cameras), wait for
your OK, commit (draft lightmaps only), then update this file with what's done and
what's next. Use CC0 assets (Poly Haven, Quaternius, ambientCG) and credit them in
`CREDITS.md`, or model pieces yourself. Stay within the per-room budget. Leave
panel text as it is; you're supplying it separately. Any text on screens, spines or
labels is plain type: no real logos, cover art or screenshots, except the moodboard
images you supply.

**Batches:** (1) study and games room, done; (2) kitchen and gym, done;
**(3) living room and library, next**; (4) trophy room, bedroom, garage and foyer; (5) the
resume view.

**What you asked for in each room** (your words, lightly trimmed):

- **Kitchen (tools and stack).** Bright and clean. An island with stools and open
  shelving where jars and tins are labelled with my tools. Keep the labels in a data
  file so I can edit them. Labels: Python, Java, JavaScript, SQL, C, HTML/CSS, React,
  Node.js, Flask, Streamlit, pandas, NumPy, scikit-learn, PyTorch, SQLite, Git,
  Google Cloud, Apps Script, BeautifulSoup, three.js, Blender, Stockfish, ONNX. The
  labelled shelf is the room's signature.
- **Gym (boxing).** Floor mats, a heavy bag on the left, a speed bag on the right.
  Gear set out neatly: an open duffel bag with shin guards poking out, a pair of
  boxing gloves, hand wraps. Clean, harsh overhead light.
- **Living room.** L-shaped sofa, rug, coffee table, a large OLED TV on a wooden
  stand showing a dark, streaming-style paused screen with "Hunter × Hunter" in
  plain type (no logo or artwork). A gallery wall of 4–6 frames in mixed sizes that
  works as a moodboard: images go in `assets_src/moodboard/`. Write a script that
  resizes and compresses them into the site, with a manifest; each time the living
  room is opened the frames show a random selection. Frame images load only when
  the room opens and don't count toward the landing download. Until images are
  added, plain colour fields. Sparse and calm. The aquarium wall stays, with a
  moss-covered rock in place of the mech for now.
- **Library (books and my writing).** Floor-to-ceiling dark-wood shelves are the
  main attraction, plus a reading chair, a green banker's lamp, and a desk with a
  laptop and a manuscript stack. The book list goes in a data file. Real titles at
  eye level as plain spines (title, plus author where given); fill the rest with
  unmarked spines and a few objects, full but not cluttered. Each Travis McGee spine
  is printed in the colour from its title.
  - Dumas: The Three Musketeers, Twenty Years After, The Vicomte de Bragelonne,
    Louise de la Vallière, The Man in the Iron Mask, The Count of Monte Cristo,
    Queen Margot, La Dame de Monsoreau, The Forty-Five Guardsmen, The Black Tulip,
    Joseph Balsamo, The Queen's Necklace
  - Ian Fleming: Casino Royale, Live and Let Die, Moonraker, Diamonds Are Forever,
    From Russia with Love, Dr. No, Goldfinger, For Your Eyes Only, Thunderball, The
    Spy Who Loved Me, On Her Majesty's Secret Service, You Only Live Twice, The Man
    with the Golden Gun, Octopussy and The Living Daylights
  - John D. MacDonald (Travis McGee): The Deep Blue Good-by, Nightmare in Pink, A
    Purple Place for Dying, The Quick Red Fox, A Deadly Shade of Gold, Bright Orange
    for the Shroud, Darker Than Amber, One Fearful Yellow Eye, Pale Gray for Guilt,
    The Girl in the Plain Brown Wrapper, Dress Her in Indigo, The Long Lavender Look,
    A Tan and Sandy Silence, The Scarlet Ruse, The Turquoise Lament, The Dreadful
    Lemon Sky, The Empty Copper Sea, The Green Ripper, Free Fall in Crimson,
    Cinnamon Skin, The Lonely Silver Rain
  - Vadim Zeland: Reality Transurfing, volumes I–V
  - Maxwell Maltz: Psycho-Cybernetics
  - Randy Wayne White: The Man Who Invented Florida, The Heat Islands
  - Joseph Conrad: Heart of Darkness
  - Cormac McCarthy: Blood Meridian
  - Amor Towles: A Gentleman in Moscow
  - Objective: Secure
  - Whiskey Tango Foxtrot
  - Heartiste, set in a blackletter font (UnifrakturMaguntia, SIL Open Font
    License, credit it; add it to `config.FONTS`, its file is
    `ofl/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf` in the Google Fonts repo)
- **Trophy room.** Spotlit glass cases with medals and a belt, a trophy, a framed
  team-photo spot (empty frame for now), and a chessboard. Opens onto the terrace.
- **Main bedroom (languages).** Soft and minimal: bed in linen, a nightstand, a
  shelf with a few books, a world map with three pins (Morocco, Russia, Japan).
- **Garage (Turo).** A clean, bright showroom: two empty bays, a key cabinet with
  four labelled keys, a wall screen with a simple booking calendar.
- **Foyer.** An empty plinth (the sculpture comes later), the stairs, a console table.
- **Resume.** "Skip to resume" and the under-stairs door open the same resume view:
  a clean HTML page built from a data file (`resume.json`), plus a "Download PDF"
  button. The current resume is at `assets_src/resume.pdf`; use it for the content.
  On the web version, show email, LinkedIn and GitHub only (no phone number). The
  content is outdated and will be updated in the data file later, so keep the
  structure simple: education, experience, projects, skills.

**Room positions, for planning** (from `house.ROOMS`; the kitchen and gym are on the
ground floor): kitchen x -12 to -5, z -8 to 0 (window on the back wall at x -11 to -6,
side window on the west wall); gym x 6 to 12, z 0 to 8 (front glass, and glass on the
east wall at z 1 to 7; doors to the study at z 3.4 to 4.6 and to the living room at
x 8.4 to 9.6). Batch 1's lessons to reuse: light signature surfaces per vertex on a
grid, keep lamp metals light, give the site's view a seat-height camera inside the room.

