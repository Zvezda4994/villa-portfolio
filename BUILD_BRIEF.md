# Villa portfolio: build brief

This is the plan for my portfolio site. It's a 3D villa in the desert that visitors can explore, and each room holds one part of my work or life. A working prototype already exists (`blockout.html`, a single three.js file made of plain boxes). The layout, navigation and room-to-section mapping in it are approved. The job now is to turn it into something that looks finished.

Read this whole file before starting. The sections near the top are the ones that are expensive to change later, so stick to them unless you check with me first.

## Who it's for

Recruiters and engineers looking at my resume. Many of them will spend under a minute on it. The house has to look impressive in the first five seconds, and everything important has to be reachable in two clicks. The "Skip to resume" button and the Rooms menu stay no matter what.

## Fixed decisions

**Look.** A modernist desert villa: long horizontal lines, cantilevered flat roof slabs, pale stone and concrete, floor-to-ceiling glass, warm timber and dark stone inside. Think of a Bond villa, not a mansion. Clean and expensive, never ornate.

**Setting.** Red-gold sand, low rocky hills on the horizon, a few date palms and desert shrubs. Not a specific country.

**Time of day.** Golden hour. The sun is low (about 12 to 18 degrees above the horizon), coming from the front left so the facade and the driveway are lit. Warm sun, cool blue-grey shadows, interior lights on and glowing softly. This drives the lighting bake, so it doesn't change once baking starts.

**Navigation.** Keep the prototype's system exactly: three views (Outside, Ground, Upstairs), the roof lifts off for the floor views, clickable labels, the camera flies to each room, a side panel with the content, previous and next, the Rooms menu, Skip to resume, and a link per room (`#dining` etc). No free first-person walking.

**Pipeline.**
- Blender (4.x) for layout, materials and lighting, driven by Python scripts kept in `blender/` in the repo so the scene can be rebuilt.
- Lighting baked in Cycles into lightmaps or baked textures, so the browser doesn't have to calculate realistic light.
- Exported as glTF (`.glb`), compressed with Meshopt or Draco, textures as KTX2.
- Shown in the browser with three.js, reusing the prototype's navigation and panel code rather than starting over.

**Performance budget.**
- Under 15 MB before the landing view is interactive, with the rest loaded room by room in the background. Under 60 MB in total.
- A smooth frame rate on a mid-range laptop and usable on a recent phone.
- If the landing shot isn't up within about 4 seconds on a normal connection, show a still image of it while the rest loads.

## Layout

Coordinates and sizes from the prototype are the starting point (the house is about 24 m by 16 m and faces +z toward the driveway). Proportions can be refined for looks, but rooms stay in the same relative positions.

**Outside**
- Driveway: replace the roundabout with a straight drive ending in a paved forecourt by the entrance. The car is parked at an angle there, facing where the landing camera sits.
- Pool deck behind the house, with loungers, and a view of the hills.

**Ground floor**

| Room | Section | Contents |
|---|---|---|
| Garage | Turo fleet | Two cars, clean and well lit, a key cabinet |
| Foyer and stairs | (entrance) | Stairs up, a sculpture on a plinth (original design, see below) |
| Under the stairs | Resume | Small door, opens the resume view |
| Study | VAREK Systems | Desk, monitor, shelving |
| Gym | Boxing | Heavy bag, mat, rack, gloves hanging up |
| Kitchen | Tools and stack | Island, counters |
| Dining room | Meruem Chess Coach | Long table with a real chessboard set up mid-game |
| Living room | Decoration | L-shaped sofa, and a floor-to-ceiling aquarium with a moss-covered mech resting on the bottom |

**Upstairs** (full floor of rooms, plus a modest terrace over the pool)

| Room | Section | Contents |
|---|---|---|
| Library | Books I rate, and my writing | Floor-to-ceiling shelves, reading chair, a desk with my manuscript |
| Trophy room | Wins in coding, boxing and esports | Display cases, belts or medals, a framed team photo spot. Opens onto the terrace |
| Games room | CS2 and the pick'em model | PC setup, monitors, sofa |
| Main bedroom | Languages (or whatever I decide later) | Bed, shelf |

Leave space in the plan for one more room later (probably a lower-level "vault" for older projects). It doesn't need to be built.

## Special moments

These are the places where the camera does something other than the standard fly-to.

1. **The car.** The latest Aston Martin Vanquish in black or dark grey. Clicking it turns the headlights on and plays an engine start. The sound only plays after a click, since browsers block audio before the visitor interacts. The recording must be licensed for this use.
2. **The pool ("Get in touch").** The camera drops to eye level as if the visitor is sitting on the lounger. Across from them is me, relaxed on a long chair, with a bottle of sake or soju beside me. The visitor's own hand holds a martini at the bottom of the frame. My contact details sit on a card on the side table.
3. **The chess table.** The camera tilts down over the board, which is set up in a real position, so it reads as an actual game.

## My character

A stylised-realistic figure that looks like me, built in Blender with open-source character tools (MPFB / MakeHuman or similar), using reference photos I'll provide. Posed reclining on the lounger. One pose is enough for version 1. It should match the scene's level of detail, not stand out from it. If that route doesn't look right, the fallback is a 3D phone scan of me, which I'll capture.

## Original designs only

No characters or designs owned by someone else. The sculpture in the foyer is an original figure (it's a nod to Meruem from Hunter x Hunter, but it must not be him). The mech in the aquarium is an original design. The drink bottle gets a made-up label. Real products like the car are fine as long as the model's license allows use on a public website.

## Assets

- Free first: Poly Haven (CC0 models, textures, HDRIs), ambientCG (CC0 materials), Quaternius (CC0 props).
- Paying is fine where it clearly lifts the result, mostly the car and one good furniture set. Check before buying anything over about $60.
- Every asset gets a line in `CREDITS.md`: name, source, author, license, link. Anything without a license that allows web use doesn't go in.

## Content

The prototype's panel text is a draft. I'll supply final copy per room. Keep content in one data file (like the prototype's `ROOMS` array) so text can change without touching the 3D code. Panels I still owe: VAREK and Turo numbers, the trophy list, the library list, the stack list, contact details.

## Build order

Work in this order and stop after each step with rendered previews (landing shot plus one or two angles) so I can review.

1. **Shell and exterior.** House structure, materials, driveway and forecourt, pool, terrain, sky, golden hour lighting, baked and running in the browser with the existing navigation. This proves the whole pipeline.
2. **The car**, including headlights and sound.
3. **Dining room, fully finished.** This is the template for the other rooms' level of detail.
4. **Pool scene with my character.**
5. **The remaining rooms**, one at a time, as I send each room's story.
6. **Polish.** Loading screen and still-image fallback, phone layout, link previews (an image for when the link is shared), performance pass.

## Repo and hosting

New GitHub repo, deployed with GitHub Pages and the same test-and-deploy workflow as my chess project. A custom domain comes later and shouldn't affect anything. Write the README and code comments in plain language, the way a person would.

## Not in version 1

First-person walking, multiple character poses, day and night switching, sound beyond the car.
