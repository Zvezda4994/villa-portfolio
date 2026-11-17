# Villa portfolio

My portfolio as a modernist villa in the desert. Visitors look around the house,
and each room holds one part of my work. `BUILD_BRIEF.md` is the plan this
follows; `blockout.html` is the first prototype, kept for reference.

**Where it stands:** build step 1 (the house shell, grounds, sky and golden-hour
lighting) and step 3 (the dining room, fully furnished, with a game in progress
on the table) are done. The car (step 2) is on hold. The other rooms are still
empty. See `PROGRESS.md` for the decisions made so far and what to watch out for.

**The lighting is currently a quick draft bake**, so walls and rooms look a little
blotchy in the browser. The full-quality bake (`npm run bake`) will be run once
all the rooms are built.

## Look at it

```
python tools/serve.py
```

Then open http://localhost:5173. There is no build step for the site: the files
in `web/` are exactly what gets served.

The live site is https://zvezda4994.github.io/villa-portfolio/. Every push to
`main` runs the tests (`npm test`) and, if they pass, publishes `web/` to
GitHub Pages (`.github/workflows/pages.yml`).

## What is where

| Folder | What it holds |
|---|---|
| `web/` | The site. `index.html`, `styles.css`, and the code in `src/`. |
| `web/src/rooms.js` | **All the text** visitors read: one entry per room, plus the resume. Edit this to change copy. |
| `web/src/main.js` | Camera, the three views, labels, side panel, rooms menu, links. Carried over from the prototype. |
| `web/src/world.js` | Loads the model and decides how each material is drawn. Fetches furnished rooms after the first view. |
| `web/assets/` | What Blender exported: the model, textures, lightmaps, sky. Rebuilt by the scripts, not edited by hand. |
| `web/assets/rooms/` | One file per furnished room (so far `dining.glb`), loaded in the background. |
| `blender/` | Python scripts that build the whole scene in Blender from nothing. |
| `blender/villa/` | The scene itself, split by subject: `house.py`, `exterior.py`, `terrain.py`, `plants.py`, `lighting.py`, `materials.py`. Sizes, the sun position and the chess position are in `config.py`. |
| `blender/villa/dining.py` | The dining room's furniture, lamps and cameras. The template for furnishing the other rooms. |
| `blender/villa/props.py` | Brings in the downloaded Poly Haven models and places copies of them. |
| `previews/` | Review pictures for each build step. |
| `tools/` | Small helpers: a runner for the Blender scripts and the local preview server. |
| `tests/` | Checks run before every deploy: the exported files load, the downloads fit the budget, the rooms data is complete. |
| `build/`, `assets_src/` | Scratch output, and the downloaded textures and models. Not committed. |

## Rebuilding the 3D scene

You only need this if you change something in `blender/`.

Needs: Blender (written and tested against 5.3), Python 3, and Node for the
`npm run` shortcuts. If Blender is not in a standard place, set the `BLENDER`
environment variable to the full path of `blender.exe`.

```
npm run assets     # once: download the source textures and models (about 35 MB, all CC0)
npm run scene      # build the scene            -> build/villa.blend           (seconds)
npm run bake       # work out the lighting      -> web/assets/lightmaps        (minutes, uses the GPU)
npm run export     # write the model, textures, sky -> web/assets              (about a minute)
npm run previews   # render the review pictures -> previews/
npm run figure     # add, update or remove the dining room figure only     (seconds)
```

`npm run build` does scene, bake and export in one go. While experimenting,
`npm run bake:draft` and `npm run previews:draft` are fast, rough versions.

The scene is never edited by hand in Blender. Open `build/villa.blend` to look
around, but make changes in the scripts and rebuild, so the scene can always be
recreated.

## How the lighting works

The browser does not calculate any lighting. Blender (Cycles) works out how much
light lands on every surface once, at golden hour, and saves the answer:

- Big flat surfaces (walls, floors, paving, sand) get **lightmaps**: textures that
  store light instead of colour. There are four, each 2048 px: outside surfaces,
  ground floor, upstairs, and the sand.
- Small bumpy things (palms, shrubs, rocks, hills, window frames) store their
  light **per vertex**, which needs no texture at all.

In the browser each surface is its tiling colour texture multiplied by its baked
light, plus a reflection of the sky. That is why it runs on a laptop or phone.

Furnished rooms work the same way, with two additions:

- Each furnished room has its own lightmap for its big flat furniture (the
  dining room's is `din`: table, rug, painting, chessboard, planters).
- Downloaded models (chess pieces, sideboard, plants...) keep their own colour
  picture, multiplied by light baked into their vertices.

The sun position is fixed in `blender/villa/config.py`. Moving it means running
the bake again.

Each lightmap is saved twice: a small 512 px copy that loads straight away, and
the sharp full-size one that replaces it a moment later.

Reflections come from panoramas Blender renders at export time: one of the sky
and desert for glass and paving, and one taken from just above the pool for the
water (from there the house hides the bright sky around the sun, so the water
reflects the house instead). The sky files are written by `blender/villa/hdr.py`
rather than Blender's own .hdr saving, which in Blender 5.3 changes the values on
the way out and made the browser's sky look washed out.

## Download size

About 10.8 MB loads before the landing view appears (model, colour textures, the
small lightmaps, sky and water reflections). The sharp lightmaps follow in the
background, then each furnished room: the dining room is about 5 MB more
(furniture, its pictures, its lightmap). With the full-quality bake everything
together comes to about 31 MB.

The brief sets targets rather than a total limit: the landing view interactive
in about 10 MB, and each room's own download around 4 MB. The tests fail if the
landing view needs more than 11 MB, or a new room more than 4.5 MB (the dining
room is allowed 6.5 MB until the step 6 performance work).
`web/assets/manifest.json` lists every file's size after each export.

## Review pictures

`previews/landing.jpg`, `pool.jpg`, `entrance.jpg`, `dining.jpg` (the dining
room) and `chess.jpg` (the board, from the visitor's seat) are rendered by
Blender. The `browser_*.jpg` files next to them are the real site from the same
camera positions, so the two can be compared.

To see those camera positions in the site, add `?shot=landing&ui=0` to the
address (or `pool`, `entrance`, `dining`, `chess`). Adding `&save=landing` as
well, while `tools/serve.py` is running, saves the browser picture into
`previews/` once the furnished rooms have loaded.

Where the two still differ, on purpose or for now:

- The far hills are a little hazier in the browser. That haze is added on
  purpose for depth; Blender's render has none.
- Window glass in the browser reflects the open sky even where, in reality, the
  roof overhang would be reflected. From low angles the upstairs rooms look a
  touch paler through the glass than in Blender.
- Sand facing straight into the sun lacks the faint sheen Cycles gives it.

## Layout notes

The room positions follow the prototype. Three things were decided along the way:

- **Upstairs** is now a full floor, as the brief asks. Back row: main bedroom,
  games room, trophy room (opening onto the terrace over the pool). Front row:
  a lounge off the bedroom, the stair landing, and the library.
- **The dark stone wall** between the foyer and the study carries on out through
  the front of the house and up past the roof. It is the one tall element
  against all the long flat lines.
- **The doorway from the foyer to the dining room** moved to the right-hand end
  of that wall, because the stairs run along the rest of it.

Space for the later "vault" room: a lower level reached from the foyer, beside
the stairs. Nothing is built there yet and nothing blocks it.

The dining room (all in `blender/villa/dining.py`):

- A 3 m walnut table on two dark stone legs, with eight leather and walnut
  chairs on a wool rug. The table, sideboard and painting share one centre line.
- A pair of wide bronze pendants hang 80 cm over the table.
- A long walnut sideboard against the foyer wall holds a bronze horse's head and
  two white vases. An original abstract painting of the desert at dusk hangs above it.
- A fig tree and a philodendron stand in dark stone planters by the pool glass.
- A game is in progress at the living-room end of the table. The visitor's seat
  faces the glass. The chair across is pushed back and turned, as if the
  opponent has just stood up. Opening the dining room drops the camera into that
  seat, looking down over the board.
- The living room stays open to it and is still empty.
- The chair across the board can hold a figure you supply (`FIGURE` in
  `config.py`). It goes in and comes out with `npm run figure`, without a
  re-bake. See `PROGRESS.md` for the steps.

The forecourt, as reworked after step 1 (all in `blender/villa/exterior.py`):

- A smaller court of warm granite setts in front of the garage, framed by bands
  of the same dark granite as the stone wall, and large pale slabs leading to the
  front door. The car will be parked on the setts.
- A low stone wall continues the line of the house's west wall out to the drive.
  A long planter of agaves and grasses closes the front of the entrance.
- A shallow reflecting pool runs in front of the study and gym, with the dark
  stone wall rising out of its end.
- Uplights in the paving wash the stone piers and the dark wall; step lights sit
  in the low wall; the drive keeps its bollards.
- Every paved edge ends in a kerb, wall, planter or coping, with a gravel border
  (`terrain.build_mask`) and rocks, shrubs and agaves along it.
- The drive is pale granite setts with raised kerbs.
- Sheer curtains hang inside the upstairs glass until those rooms are furnished.

## Still to do (from the brief)

- Steps 2 to 6: the car, the dining room, the pool scene and character, the
  remaining rooms, and the polish pass (loading screen with a still image,
  phone layout, link previews, performance).
- Final copy for the panels (see the `todo` notes in `web/src/rooms.js`).

Assets and their licenses are listed in `CREDITS.md`.
