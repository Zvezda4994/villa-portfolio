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

**Step 2, the car, is on hold** at your request. The researched options for the
model and the engine sound are in the conversation history; nothing was bought.

**Repo and hosting.** The code is on GitHub at Zvezda4994/villa-portfolio, and the
site is live at https://zvezda4994.github.io/villa-portfolio/. Every push to `main`
runs `npm test` and then publishes `web/` to GitHub Pages, the same setup as the
chess project.

**The lighting in the repo is a draft bake.** It's quick to make but blotchy.
The full bake waits until the rooms are done.

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
    the browser. The Blender previews show the intended look; the full bake fixes the site.
18. **Importing a glTF leaves things behind.** `props.load` removes the imported
    objects, meshes and unused materials and images straight away, so the saved
    scene only holds what `place` added.
19. **`?view=` has to come before `?shot=`.** Switching views resets the camera's
    minimum distance, which pushed close-up review cameras back. `main.js` now
    applies the view first.

## Next

**Waiting on you**

- The figure for the dining table: put the model you choose in
  `assets_src/figures/`, fill in `FIGURE` with its credit and link, and run
  `npm run figure` (steps above).
- The car (step 2): pick a model and an engine sound from the options shown,
  whenever you want to pick it back up.
- Panel copy: VAREK and Turo numbers, the trophy list, the library list, the stack
  list, contact details.
- For later steps:
  - reference photos for the character;
  - a choice of chess position for the dining table;
  - approval before buying anything over about $60, most likely the car model.

**Build order from here**

2. **The car (on hold).** A licensed model of the latest Vanquish in black or
   dark grey, parked on the setts court facing the landing camera. Headlights come
   on and a licensed engine start plays on click (sound only after a click). The
   model has to be shipped encrypted or in a non-standard format: CGTrader's
   royalty-free license allows web use only if visitors can't pull the model out.
4. **Pool scene with the character.** The camera drops to lounger height; built
   with MPFB/MakeHuman from reference photos.
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
   - Phone layout and link previews.
   - Then the full-quality bake.

**Smaller things noted along the way**

- The glass reflections could use a probe in front of the house, like the water.
- The far hills are hazier in the browser than in Blender, on purpose.
- Sand facing the sun lacks Cycles' faint sheen.
