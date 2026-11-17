# Villa portfolio

My portfolio as a modernist villa in the desert. Visitors look around the house,
and each room holds one part of my work. `BUILD_BRIEF.md` is the plan this
follows; `blockout.html` is the first prototype, kept for reference.

**Where it stands:** build step 1 of 6 is done (the house shell, grounds, sky and
golden-hour lighting, baked and running in the browser with the prototype's
navigation). The rooms are empty. The car comes next.

## Look at it

```
python tools/serve.py
```

Then open http://localhost:5173. There is no build step for the site: the files
in `web/` are exactly what gets served.

## What is where

| Folder | What it holds |
|---|---|
| `web/` | The site. `index.html`, `styles.css`, and the code in `src/`. |
| `web/src/rooms.js` | **All the text** visitors read: one entry per room, plus the resume. Edit this to change copy. |
| `web/src/main.js` | Camera, the three views, labels, side panel, rooms menu, links. Carried over from the prototype. |
| `web/src/world.js` | Loads the model and decides how each material is drawn. |
| `web/assets/` | What Blender exported: the model, textures, lightmaps, sky. Rebuilt by the scripts, not edited by hand. |
| `blender/` | Python scripts that build the whole scene in Blender from nothing. |
| `blender/villa/` | The scene itself, split by subject: `house.py`, `exterior.py`, `terrain.py`, `plants.py`, `lighting.py`, `materials.py`. Sizes and the sun position are in `config.py`. |
| `previews/` | Review pictures for each build step. |
| `tools/` | Small helpers: a runner for the Blender scripts and the local preview server. |
| `build/`, `assets_src/` | Scratch output and downloaded textures. Not committed. |

## Rebuilding the 3D scene

You only need this if you change something in `blender/`.

Needs: Blender (written and tested against 5.3), Python 3, and Node for the
`npm run` shortcuts. If Blender is not in a standard place, set the `BLENDER`
environment variable to the full path of `blender.exe`.

```
npm run assets     # once: download the source textures (about 10 MB, all CC0)
npm run scene      # build the scene            -> build/villa.blend           (seconds)
npm run bake       # work out the lighting      -> web/assets/lightmaps        (minutes, uses the GPU)
npm run export     # write the model, textures, sky -> web/assets              (about a minute)
npm run previews   # render the review pictures -> previews/
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

About 8.4 MB loads before the landing view appears (model, colour textures, the
small lightmaps, sky). The sharp lightmaps follow in the background. Everything
together is 24 MB. The brief's limits are 15 MB and 60 MB. `web/assets/manifest.json`
lists every file's size after each export.

## Review pictures

`previews/landing.jpg`, `pool.jpg` and `entrance.jpg` are rendered by Blender.
The `browser_*.jpg` files next to them are the real site from the same camera
positions, so the two can be compared.

To see those camera positions in the site, add `?shot=landing&ui=0` to the
address (or `pool`, or `entrance`). Adding `&save=landing` as well, while
`tools/serve.py` is running, saves the browser picture into `previews/`.

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

## Still to do (from the brief)

- Steps 2 to 6: the car, the dining room, the pool scene and character, the
  remaining rooms, and the polish pass (loading screen with a still image,
  phone layout, link previews, performance).
- GitHub repo and the Pages deploy workflow.
- Final copy for the panels (see the `todo` notes in `web/src/rooms.js`).

Assets and their licenses are listed in `CREDITS.md`.
