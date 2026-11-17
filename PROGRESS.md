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

## Next

**Waiting on you**

- Panel copy: VAREK and Turo numbers, the trophy list, the library list, the stack
  list, contact details.
- For later steps:
  - reference photos for the character;
  - a choice of chess position for the dining table;
  - approval before buying anything over about $60, most likely the car model.

**Build order from here**

2. **The car.** A licensed model of the latest Vanquish in black or dark grey,
   parked on the setts court facing the landing camera. Headlights come on and
   a licensed engine start plays on click (sound only after a click).
3. **Dining room, fully finished.** It sets the level of detail for the other rooms.
4. **Pool scene with the character.** The camera drops to lounger height; built
   with MPFB/MakeHuman from reference photos.
5. **The remaining rooms,** one at a time as each room's story arrives. When a
   room is furnished, its curtains can go.
6. **Polish:**
   - loading screen with a still-image fallback. This matters: on a slow
     connection (about 150 KB/s in testing) the live site took about 90 seconds
     to show the landing view, because about 11 MB loads first. Showing a still
     straight away, and loading 512 px colour textures before the 1024 px ones,
     would fix most of it;
   - phone layout;
   - link previews;
   - performance pass;
   - then the full-quality bake.

**Smaller things noted along the way**

- The glass reflections could use a probe in front of the house, like the water.
- The far hills are hazier in the browser than in Blender, on purpose.
- Sand facing the sun lacks Cycles' faint sheen.
