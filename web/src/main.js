// The page itself: camera, the three views, labels, the side panel, the rooms
// menu, the resume and links like #dining. This is the navigation from the
// blockout prototype, kept as it was. The only real change is that the villa is
// now loaded from Blender's export (see world.js) instead of being built from boxes.

import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
import {ROOMS, FLOOR_NAME, NEIGHBOURS, HOTSPOTS} from "./rooms.js";
import {loadResume, resumeHTML, RESUME_PDF} from "./resume.js";
import {Still, STILL, cameraFov, stillFiles} from "./still.js";
import {loadWorld, TONE_MAPPING} from "./world.js";

performance.mark("ui");
const $ = id => document.getElementById(id);
const esc = t => String(t).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[c]);
const params = new URLSearchParams(location.search);
// review pictures and the stills tool want the 3D straight away, without the still
const reviewing = params.has("shot") || params.has("save") || params.has("capture") || params.get("ui") === "0";

/* ---------- The still ----------
   A picture of the landing shot shows at once (it's in index.html) while the 3D loads
   behind it. Until the 3D is ready: the labels sit on the still where they'll be in 3D,
   opening a room shows that room's own still, dragging pans the still a little and
   shows how far the loading has got. Then the 3D takes over from the same camera. */
let still = null;
if (reviewing) $("still").hidden = true;
else still = new Still($("still"), {onDrag: () => showProgress(true)});
let stillStop = null;                    // the stop whose still is showing (null: the landing shot)
let afterStill = null;                   // a floor view picked while the still showed, flown to after
let progressShown = 0, progressValue = 0, progressTimer = 0;
function showProgress(on) {
  if (!still || !still.on) return;
  const p = $("progress");
  if (p.classList.contains("failed")) return;     // the "couldn't load" note stays
  if (on) { p.hidden = false; progressShown = performance.now(); clearTimeout(progressTimer); progressTimer = setTimeout(() => showProgress(false), 1800); }
  else p.hidden = true;
}
function setProgress(f) {
  progressValue = f;
  $("progressBar").style.width = (f * 100).toFixed(1) + "%";
  $("progressText").textContent = `Loading the 3D house · ${Math.floor(f * 100)}%`;
}

/* ---------- Renderer, camera, controls ---------- */
const canvas = $("scene");
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: params.has("save") || params.has("capture")});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = TONE_MAPPING;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(STILL.fov, 1, 0.3, 4000);
scene.add(camera);                       // so things carried by the camera (the visitor's hand) are drawn
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.dampingFactor = 0.08; controls.maxPolarAngle = Math.PI / 2 - 0.04; controls.minDistance = 4; controls.maxDistance = 90;
// touch: one finger looks around, two pan and pinch to zoom (OrbitControls' own default, set here on purpose)
controls.touches = {ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN};
// Inside a room the camera may tip a little past level, to look up at a lamp or the top shelves; outside it
// stays above what it looks at. Review shots lift the limit altogether (reviewShot).
const POLAR = {out: Math.PI / 2 - 0.04, room: Math.PI / 2 + 0.12};
let reviewShot = false;

const HOME = {pos: [-19, 5.5, 30], target: [-2, 1.8, 8]};      // the landing shot (and its still)
camera.position.set(...HOME.pos); controls.target.set(...HOME.target);
if (still) controls.enabled = false;     // the still is dragged instead, until the 3D takes over

/* ---------- Views and fly-to ---------- */
let world = null;
let view = "out";
// The floor views lift off what's above that floor (the roof for upstairs, the
// upstairs and the roof for the ground floor) so it can be seen from above. Once
// the camera is inside the house and below that floor's ceiling, the lifted floors
// go back on, so a room has its ceiling at eye level. The switch happens as the
// camera passes down through the ceiling on the way in, where nothing pops. It
// stays on until the camera rises back through the ceiling of the floor it came in
// on, even if the view changes first (from the games room to the kitchen, say).
// Sizes from blender/villa/config.py: HALF_W, HALF_D, H1 and ROOF_Y.
const HOUSE = {halfW: 12, halfD: 8, ceiling: {g: 3.2, u: 6.5}};
const FLOOR_Y = {g: 0, u: 3.5};                  // each floor's level (config.F2 upstairs)
let lifted = "", inside = null;                  // inside: the floor whose room the camera is in
function fitFloors() {
  if (!world) return;
  const p = camera.position, inHouse = Math.abs(p.x) < HOUSE.halfW && Math.abs(p.z) < HOUSE.halfD;
  // out through the ceiling, or down through the floor (a flight between floors whose frames
  // happened to skip the part above the roof)
  if (inside && !(inHouse && p.y < HOUSE.ceiling[inside] && p.y > FLOOR_Y[inside] - 0.05)) inside = null;
  if (!inside && inHouse && p.y < HOUSE.ceiling[view]) inside = view;
  if (!reviewShot) controls.maxPolarAngle = inside ? POLAR.room : POLAR.out;
  const now = inside ? "out" : view;             // inside a room, the whole house shows
  if (now === lifted) return;
  lifted = now;
  world.setVisible("roof", now === "out");      // the roof lifts off for the floor views
  world.setVisible("upper", now !== "g");       // and the upstairs too, to see the ground floor
}
function setView(v, fly = true) {
  view = v;
  if (fly) here = null;                  // off to an overview: no room's hotspots any more
  fitFloors();
  controls.minDistance = 4;
  $("vOut").setAttribute("aria-pressed", v === "out"); $("vG").setAttribute("aria-pressed", v === "g"); $("vU").setAttribute("aria-pressed", v === "u");
  if (fly && still && still.on) {
    // before the 3D: back to the landing still, with that floor's labels on it; the
    // camera flies to the floor view once the 3D has taken over
    stillStop = null; still.show("landing"); afterStill = v === "out" ? null : v;
    showProgress(true);
    return;
  }
  if (fly) {
    if (v === "out") flyTo(HOME.pos, HOME.target);
    else if (v === "g") flyTo([0, 24, 20], [0, 0, 0]);
    else flyTo([0, 26, 18], [0, 3.4, -3]);
  }
}
let tween = null;
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
// `via`, if given, bends the camera's path through that point's neighbourhood
// (used to come down into a room from above instead of through a wall).
function flyTo(pos, target, ms = 1300, via = null) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  userMoved = false;                     // the stop's view is kept as authored until the visitor moves (keepClear)
  tween = {p0: camera.position.clone(), t0: controls.target.clone(), p1: new THREE.Vector3(...pos), t1: new THREE.Vector3(...target),
    via: via && new THREE.Vector3(...via), start: performance.now(), ms: reduce ? 1 : ms};
}
let current = null, opening = null;      // opening: the room's own loading (furniture, moodboard pictures)
let here = null;                         // the stop last opened, whose hotspots show while the camera is inside
function openRoom(id, fly = true) {
  const r = ROOMS.find(x => x.id === id); if (!r) return;
  current = r; here = r; hideTip();
  if (world) {
    opening = world.openRoom(r.room || r.id);
    world.prefetch((NEIGHBOURS[r.id] || []).map(id => { const x = ROOMS.find(s => s.id === id); return x ? x.room || x.id : id; }));
  }
  if (still && still.on) {
    // before the 3D: show the room's own still; the 3D appears at its camera when ready
    stillStop = r; afterStill = null; still.show(r.id); showProgress(true);
    view = r.floor;
    $("vOut").setAttribute("aria-pressed", view === "out"); $("vG").setAttribute("aria-pressed", view === "g"); $("vU").setAttribute("aria-pressed", view === "u");
    fly = false;
  }
  const otherFloor = r.floor !== view;
  if (otherFloor) setView(r.floor, false);
  // Rooms with a close-up (the chessboard) let the camera come in near and drop
  // in from above; the rest keep the normal fly-to. Between floors it bends higher,
  // so it leaves through the roof (6.5 m) instead of through the floor between them.
  controls.minDistance = r.near ?? 4;
  if (fly) {
    const [p, t] = r.view;
    flyTo(p, t, r.near ? 1700 : 1300, r.near ? [t[0], otherFloor ? 12 : 9, t[2] + 3] : null);
  }
  renderPanel(r); $("rooms").hidden = true; $("roomsBtn").setAttribute("aria-expanded", "false");
  $("hint").hidden = true;
  try { history.replaceState(null, "", "#" + r.id); } catch (e) {}
}
// a room the visitor may open next (a hovered label or menu entry): start loading it
const prefetch = id => { const r = ROOMS.find(x => x.id === id); if (r && world) world.prefetch([r.room || r.id]); };
function renderPanel(r) {
  const i = ROOMS.indexOf(r);
  let h = `<div class="eyebrow">${r.area} · ${FLOOR_NAME[r.floor]}</div><h2>${r.title}</h2>`;
  h += r.body.map(p => /^<(ul|ol|div|p)[\s>]/.test(p) ? p : `<p>${p}</p>`).join("");
  if (r.links) h += `<div class="links">${r.links.map(([t, u, internal, ghost]) => `<a href="${u}" ${internal ? `data-go="${u.slice(1)}"` : `target="_blank" rel="noopener"`} class="${ghost ? "ghost" : ""}">${t}</a>`).join("")}</div>`;
  // Credits for any figure seated in this room; they come and go with the figure itself.
  for (const f of Object.values(world?.manifest.figures || {})) {
    if (f.room === r.id) h += `<p class="credit">${esc(f.credit)} <a href="${encodeURI(f.link)}" target="_blank" rel="noopener">Model page</a></p>`;
  }
  // credits for models built into the room (the tank's mech), from the manifest
  for (const c of world?.manifest.credits || []) {
    if (c.room === r.id) h += `<p class="credit">${esc(c.credit)} <a href="${encodeURI(c.link)}" target="_blank" rel="noopener">Model page</a></p>`;
  }
  if (r.todo) h += `<p class="todo">To do: ${r.todo}</p>`;
  $("panelBody").innerHTML = h; $("panel").hidden = false; foldPanel(false);
  $("panelBody").querySelectorAll("[data-go]").forEach(a => a.onclick = e => { e.preventDefault(); const t = a.dataset.go; if (t === "resume") showResume(true); else openRoom(t); });
  $("prevRoom").onclick = () => openRoom(ROOMS[(i - 1 + ROOMS.length) % ROOMS.length].id);
  $("nextRoom").onclick = () => openRoom(ROOMS[(i + 1) % ROOMS.length].id);
  document.querySelectorAll(".pin").forEach(p => p.classList.toggle("on", p.dataset.id === r.id));
}
// On phones the panel is a sheet along the bottom; its handle folds it down to its title, so
// the room behind can be seen, and unfolds it again (as does tapping the folded title).
function foldPanel(on) { $("panel").classList.toggle("peek", on); $("panelGrab").setAttribute("aria-expanded", String(!on)); $("panelGrab").setAttribute("aria-label", on ? "Unfold the panel" : "Fold the panel down"); }
$("panelGrab").onclick = () => foldPanel(!$("panel").classList.contains("peek"));
$("panelBody").addEventListener("click", e => { if ($("panel").classList.contains("peek") && !e.target.closest("a")) { e.preventDefault(); foldPanel(false); } });
$("panelX").onclick = () => { $("panel").hidden = true; current = null; document.querySelectorAll(".pin").forEach(p => p.classList.remove("on")); };
$("vOut").onclick = () => setView("out"); $("vG").onclick = () => setView("g"); $("vU").onclick = () => setView("u");

/* Room list */
{
  let h = "";
  for (const f of ["out", "g", "u"]) { h += `<h3>${FLOOR_NAME[f]}</h3>`; ROOMS.filter(r => r.floor === f).forEach(r => h += `<button data-id="${r.id}">${r.title}<span>${r.area}</span></button>`); }
  $("rooms").innerHTML = h;
  $("rooms").querySelectorAll("button").forEach(b => { b.onclick = () => openRoom(b.dataset.id); b.onpointerenter = () => prefetch(b.dataset.id); });
}
$("roomsBtn").onclick = () => { const open = $("rooms").hidden; $("rooms").hidden = !open; $("roomsBtn").setAttribute("aria-expanded", open); };

/* Plain resume view: the fast path for anyone skimming. Built from web/resume.json
   (see src/resume.js); it doesn't wait for the 3D, so it works even if the villa can't load. */
{
  const actions = `<div class="rv-actions"><a class="pill brass" href="${RESUME_PDF}" download="Aditya-Singh-Resume.pdf">Download PDF</a>` +
    `<button class="pill" id="resumeBack">Back to the house</button></div>`;
  const back = () => { const b = $("resumeBack"); if (b) b.onclick = () => showResume(false); };
  $("resumeBody").innerHTML = `<header class="rv-head"><div><h1>Aditya Singh</h1></div>${actions}</header>`;
  back();
  loadResume().then(d => { $("resumeBody").innerHTML = resumeHTML(d, actions); back(); },
    e => { console.error(e); $("resumeBody").insertAdjacentHTML("beforeend", `<p>The resume could not be loaded. <a href="${RESUME_PDF}">Open the PDF</a> instead.</p>`); });
}
function showResume(on) {
  $("resume").hidden = !on;
  if (on) { $("panel").hidden = true; $("resume").scrollTop = 0; try { history.replaceState(null, "", "#resume"); } catch (e) {} }
  else if (location.hash === "#resume") { try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {} }
}
$("resumeBtn").onclick = () => showResume(true);

/* ---------- Pins (HTML labels that follow their 3D anchor) ---------- */
const pinEls = ROOMS.map(r => {
  const b = document.createElement("button"); b.className = "pin"; b.dataset.id = r.id; b.innerHTML = `<i></i>${r.title}`;
  b.onclick = () => openRoom(r.id); b.onpointerenter = () => prefetch(r.id);
  $("pins").appendChild(b); return b;
});
const tmp = new THREE.Vector3();
const tmpMoment = new THREE.Vector3();
let shotMoment = null;                   // set when a review picture is taken from a staged moment's camera
function updatePins() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  // on the still, the labels move with it when it's dragged; a room's still has none
  const onStill = still && still.on, dx = onStill ? still.x : 0, dy = onStill ? still.y : 0;
  ROOMS.forEach((r, i) => {
    const el = pinEls[i];
    // labels are for the Outside, Ground and Upstairs overviews only: inside a room none
    // show (the panel names the room, and the others would shine through the walls)
    const show = onStill ? !stillStop && (view === "out" ? r.floor === "out" : r.floor === view)
      : !inside && (view === "out" ? r.floor === "out" : r.floor === view);
    tmp.set(...r.at).project(camera);
    if (!show || tmp.z > 1 || tmp.x < -1.05 || tmp.x > 1.05 || tmp.y < -1.05 || tmp.y > 1.05) { el.hidden = true; return; }
    el.hidden = false;
    // kept whole on screen: a label whose point is near an edge slides in (on a phone held upright, say)
    const half = el.offsetWidth / 2, x = (tmp.x + 1) / 2 * w + dx, y = (1 - tmp.y) / 2 * h + dy;
    el.style.left = Math.min(Math.max(x, half + 6), w - half - 6) + "px";
    el.style.top = Math.max(y, el.offsetHeight + 6) + "px";
  });
}

/* ---------- On phones, the view centres in what the panel leaves uncovered ----------
   The bottom sheet (upright) or the side panel (held sideways) covers much of a phone's
   screen, so while it's open the 3D view (and the still) slides up or left by half of
   what it covers: the room's subject, the chessboard say, stays in sight. Larger screens
   keep the view as it is. */
const SHEET = matchMedia("(max-width: 640px)"), SIDE = matchMedia("(max-height: 500px) and (min-width: 641px)");
const shift = {x: 0, y: 0};
function shiftView() {
  let tx = 0, ty = 0;
  const p = $("panel");
  if (!p.hidden && !document.body.classList.contains("bare") && (SHEET.matches || SIDE.matches)) {
    const r = p.getBoundingClientRect();
    if (SHEET.matches) ty = r.height / 2; else tx = Math.max(0, canvas.clientWidth - r.left) / 2;
  }
  const k = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : 0.18;
  shift.x += (tx - shift.x) * k; shift.y += (ty - shift.y) * k;
  if (Math.abs(tx - shift.x) < 0.5) shift.x = tx;
  if (Math.abs(ty - shift.y) < 0.5) shift.y = ty;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (shift.x || shift.y) camera.setViewOffset(w, h, shift.x, shift.y, w, h);
  else if (camera.view && camera.view.enabled) camera.clearViewOffset();
  if (still && still.on) still.shiftTo(shift.x, shift.y);
}

/* ---------- Things in the scene that open a panel or the resume (the contact card at the pool,
   the door under the stairs) ---------- */
const raycaster = new THREE.Raycaster();
const hitBox = new THREE.Box3(), tmpA = new THREE.Vector3(), tmpB = new THREE.Vector3(), tmpC = new THREE.Vector3();
const pointer = new THREE.Vector2();
const shown = o => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
// The stop whose panel the thing under the pointer opens, if any. It only counts if
// nothing solid in the scene is in front of it.
function stopUnder(e) {
  if (!world) return null;
  const rect = canvas.getBoundingClientRect();
  pointer.set((e.clientX - rect.left) / rect.width * 2 - 1, 1 - (e.clientY - rect.top) / rect.height * 2);
  raycaster.setFromCamera(pointer, camera);
  let solid;                             // the nearest solid thing under the pointer, found once if needed
  const blocked = d => {
    if (solid === undefined) solid = raycaster.intersectObjects(scene.children, true).find(h => shown(h.object) && !h.object.material.transparent) || null;
    return solid && solid.distance < d - 0.01;
  };
  for (const r of ROOMS) {
    if (r.click) {
      const hit = raycaster.intersectObjects(world.meshesWith(r.click).filter(shown), false)[0];
      if (hit && !blocked(hit.distance)) return r;
    }
    if (r.hit) {
      const at = raycaster.ray.intersectBox(hitBox.set(tmpA.set(...r.hit[0]), tmpB.set(...r.hit[1])), tmpC);
      if (at && !blocked(raycaster.ray.origin.distanceTo(at))) return r;
    }
  }
  return null;
}
let press = null, lastHover = 0;
canvas.addEventListener("pointerdown", e => { press = {x: e.clientX, y: e.clientY, t: performance.now()}; hideTip(); seenHint(); });
// On a phone, looking around folds the panel down to its title, so the room can be seen; tapping the
// title (or the handle) unfolds it again.
canvas.addEventListener("pointermove", e => {
  if (!press || press.folded || !(SHEET.matches || SIDE.matches) || $("panel").hidden) return;
  if (Math.hypot(e.clientX - press.x, e.clientY - press.y) > 12) { press.folded = true; foldPanel(true); }
});
canvas.addEventListener("pointerup", e => {
  const p = press; press = null;
  // a drag to look around isn't a click
  if (!p || Math.hypot(e.clientX - p.x, e.clientY - p.y) > 6 || performance.now() - p.t > 600) return;
  const r = stopUnder(e);
  if (r && r.opens === "resume") showResume(true);
  else if (r) { showResume(false); openRoom(r.id, camera.position.distanceTo(tmp.set(...r.view[0])) > 1.2); }
});
canvas.addEventListener("pointermove", e => {
  if (e.buttons || e.pointerType !== "mouse" || performance.now() - lastHover < 100) return;
  lastHover = performance.now();
  canvas.style.cursor = stopUnder(e) ? "pointer" : "";
});

/* ---------- Hotspots: small pulsing dots on things in the room you're in ----------
   One per entry in HOTSPOTS (rooms.js), on its anchor from the model. A dot shows only while the
   camera is inside the house and that stop is the one last opened, once its room's furniture is in,
   and only where nothing solid stands between it and the camera. */
const spots = HOTSPOTS.map(h => {
  const el = document.createElement("button");
  el.className = "spot"; el.hidden = true; el.setAttribute("aria-label", h.label);
  const s = {...h, el, ready: false, clear: true, at: null, x: 0, y: 0};
  el.onclick = () => useSpot(s);
  $("spots").appendChild(el);
  return s;
});
const tipEl = $("spotTip");
let tipFor = null, tipTimer = 0;
function hideTip() { if (!tipFor) return; tipFor = null; tipEl.hidden = true; clearTimeout(tipTimer); }
function useSpot(s) {
  seenHint();
  if (s.resume) showResume(true);
  else if (s.url) window.open(s.url, "_blank", "noopener");
  else if (s.view) { hideTip(); flyTo(...s.view, 1400); }
  else if (s.tip) {
    if (tipFor === s) { hideTip(); return; }
    tipFor = s; tipEl.textContent = s.tip; tipEl.hidden = false; placeTip(s);
    clearTimeout(tipTimer); tipTimer = setTimeout(hideTip, 6000);
  }
}
const spotRay = new THREE.Raycaster(), spotDir = new THREE.Vector3();
let lastSpotCheck = 0;
function updateSpots(t) {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const check = t - lastSpotCheck > 250;          // whether anything hides a dot: a few times a second is plenty
  if (check) lastSpotCheck = t;
  for (const s of spots) {
    let show = Boolean(world && inside && here && here.id === s.stop && s.ready && $("resume").hidden);
    if (show) {
      s.at ||= world.hotspot(s.anchor);
      show = Boolean(s.at);
    }
    if (show) {
      tmp.copy(s.at).project(camera);
      show = tmp.z < 1 && Math.abs(tmp.x) < 1 && Math.abs(tmp.y) < 1;
    }
    if (show && check) {
      // hidden if something solid is in front (the anchors sit on or just off their surfaces)
      const d = spotDir.copy(s.at).sub(camera.position).length();
      spotRay.set(camera.position, spotDir.normalize()); spotRay.far = d;
      const hit = spotRay.intersectObjects(scene.children, true).find(x => shown(x.object) && !x.object.material.transparent);
      s.clear = !hit || hit.distance > d - 0.15;
    }
    show = show && s.clear;
    s.el.hidden = !show;
    if (!show) { if (tipFor === s) hideTip(); continue; }
    s.x = (tmp.x + 1) / 2 * w; s.y = (1 - tmp.y) / 2 * h;
    s.el.style.transform = `translate(${s.x.toFixed(1)}px, ${s.y.toFixed(1)}px)`;
    if (tipFor === s) placeTip(s);
  }
}
// the note beside its dot, on whichever side has room
function placeTip(s) {
  const left = s.x + 18 + tipEl.offsetWidth > canvas.clientWidth - 8;
  tipEl.style.transform = `translate(${(left ? s.x - 18 - tipEl.offsetWidth : s.x + 18).toFixed(1)}px, ${(s.y - tipEl.offsetHeight / 2).toFixed(1)}px)`;
}

/* ---------- Keyboard: look around, move and zoom ----------
   Arrow keys orbit (left and right swing round, up and down tip the view), WASD pans across the
   floor in the direction the camera faces, Q and E (or - and +) zoom out and in. Speeds follow
   the distance to what the camera looks at, so it works the same in a room and over the house. */
const NAV_KEYS = new Set(["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "KeyW", "KeyA", "KeyS", "KeyD", "KeyQ", "KeyE", "Equal", "Minus", "NumpadAdd", "NumpadSubtract"]);
const held = new Set();
const navKey = e => NAV_KEYS.has(e.code) ? e.code : e.key === "+" ? "Equal" : e.key === "-" ? "Minus" : null;
window.addEventListener("keydown", e => {
  if (e.key === "Escape") hideTip();
  if (e.ctrlKey || e.metaKey || e.altKey || !controls.enabled || !$("resume").hidden) return;
  if (e.target.closest && e.target.closest("input, textarea, select, [contenteditable]")) return;
  const k = navKey(e); if (!k) return;
  e.preventDefault(); held.add(k); tween = null; userMoved = true; seenHint();
});
window.addEventListener("keyup", e => { const k = navKey(e); if (k) held.delete(k); });
window.addEventListener("blur", () => held.clear());
const orbit = new THREE.Spherical(), offset = new THREE.Vector3(), ahead = new THREE.Vector3(), aside = new THREE.Vector3();
function keyMove(dt) {
  if (!held.size || !controls.enabled) return;
  const on = (...ks) => ks.some(k => held.has(k)) ? 1 : 0;
  const yaw = on("ArrowLeft") - on("ArrowRight"), tilt = on("ArrowUp") - on("ArrowDown");
  const fwd = on("KeyW") - on("KeyS"), side = on("KeyD") - on("KeyA");
  const zoom = on("KeyE", "Equal", "NumpadAdd") - on("KeyQ", "Minus", "NumpadSubtract");
  offset.copy(camera.position).sub(controls.target);
  orbit.setFromVector3(offset);
  orbit.theta += yaw * 1.5 * dt;                         // about 85° a second
  orbit.phi = Math.min(Math.max(orbit.phi + tilt * 1.0 * dt, controls.minPolarAngle + 0.02), controls.maxPolarAngle);
  orbit.radius = Math.min(Math.max(orbit.radius * Math.exp(-zoom * 0.8 * dt), controls.minDistance), controls.maxDistance);
  offset.setFromSpherical(orbit);
  camera.getWorldDirection(ahead); ahead.y = 0;
  if (ahead.lengthSq() < 1e-6) ahead.set(-offset.x, 0, -offset.z);
  ahead.normalize(); aside.crossVectors(ahead, camera.up).normalize();
  const speed = Math.min(Math.max(orbit.radius * 0.45, 0.9), 15) * dt;      // about 1 m/s in a room
  controls.target.addScaledVector(ahead, fwd * speed).addScaledVector(aside, side * speed);
  camera.position.copy(controls.target).add(offset);
  // walking into something stops the walk (the point looked at stops too), rather than swinging round it
  const push = keepClear();
  if (push && (fwd || side)) controls.target.add(push);
}

/* ---------- Keeping the camera out of things ----------
   Once the visitor moves the camera themselves (keys, a drag, a pinch, the wheel), it stays at least
   CLEAR from every surface, furniture included: the near clipping plane is 0.3 m, so any closer and
   the camera would see into what it's touching. The exact distance to every triangle near the camera
   is measured (from either side, so nothing can be entered), and the camera is pushed straight away
   from the nearest until it's clear. The triangles are filed once, by the 0.5 m cells they touch, the
   first time the camera comes near their mesh (nothing in the house moves), so a check only looks at
   a few cells. Flights to a stop and the stops' own views are left exactly as authored (the pool's
   lounger has its back right behind the eye). */
const CLEAR = 0.35, CELL = 0.5;
const meshBox = new WeakMap();                     // each mesh's box, once
const boxOf = o => { let b = meshBox.get(o); if (!b) { b = new THREE.Box3().setFromObject(o); meshBox.set(o, b); } return b; };
const filedUpTo = new WeakMap(), cells = new Map();   // mesh -> how many of its triangles are filed; cell key -> triangle numbers
let triPos = new Float32Array(9 * 65536), triMesh = [], triCount = 0, triSeen = new Uint32Array(65536), stamp = 0;
const cellKey = (i, j, k) => (i + 512) * 1048576 + (j + 512) * 1024 + (k + 512);   // within 250 m of the middle (rooms are)
const fileV = new THREE.Vector3();
const isFiled = o => { const g = o.geometry; return filedUpTo.get(o) >= (g.index ? g.index.count : g.attributes.position.count); };
// Files a mesh's triangles, carrying on from where it stopped, until done or `until` (a performance.now() time).
function fileMesh(o, until = Infinity) {
  const g = o.geometry, pos = g.attributes.position, idx = g.index, n = idx ? idx.count : pos.count;
  if (!filedUpTo.has(o)) o.updateMatrixWorld(true);
  const m = o.matrixWorld;
  let t = filedUpTo.get(o) || 0;
  for (; t < n; t += 3) {
    if ((t & 255) === 0 && performance.now() > until) break;
    if (triCount * 9 + 9 > triPos.length) {        // grow the store
      const more = new Float32Array(triPos.length * 2); more.set(triPos); triPos = more;
      const seen = new Uint32Array(triSeen.length * 2); seen.set(triSeen); triSeen = seen;
    }
    const base = triCount * 9;
    for (let v = 0; v < 3; v++) {
      fileV.fromBufferAttribute(pos, idx ? idx.getX(t + v) : t + v).applyMatrix4(m);
      triPos[base + v * 3] = fileV.x; triPos[base + v * 3 + 1] = fileV.y; triPos[base + v * 3 + 2] = fileV.z;
    }
    triMesh.push(o);
    const x0 = Math.floor(Math.min(triPos[base], triPos[base + 3], triPos[base + 6]) / CELL), x1 = Math.floor(Math.max(triPos[base], triPos[base + 3], triPos[base + 6]) / CELL);
    const y0 = Math.floor(Math.min(triPos[base + 1], triPos[base + 4], triPos[base + 7]) / CELL), y1 = Math.floor(Math.max(triPos[base + 1], triPos[base + 4], triPos[base + 7]) / CELL);
    const z0 = Math.floor(Math.min(triPos[base + 2], triPos[base + 5], triPos[base + 8]) / CELL), z1 = Math.floor(Math.max(triPos[base + 2], triPos[base + 5], triPos[base + 8]) / CELL);
    // a huge triangle (the far hills, the open sand) would fill thousands of cells: those are left out;
    // the camera never gets near them in a room, and outside it stays above what it looks at anyway
    if ((x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1) <= 4096 && Math.min(x0, y0, z0) >= -500 && Math.max(x1, y1, z1) <= 500) {
      for (let i = x0; i <= x1; i++) for (let j = y0; j <= y1; j++) for (let k = z0; k <= z1; k++) {
        const key = cellKey(i, j, k);
        let list = cells.get(key); if (!list) cells.set(key, list = []);
        list.push(triCount);
      }
    }
    triCount++;
  }
  filedUpTo.set(o, t);
}
// Filing ahead, in the browser's idle moments: everything in and around the house, nearest the camera
// first, so the visitor's first move in a room doesn't stall while its triangles are filed.
const HOUSE_BOX = new THREE.Box3(new THREE.Vector3(-14, -1, -10), new THREE.Vector3(14, 8, 10));
const idle = window.requestIdleCallback || (f => setTimeout(() => f({timeRemaining: () => 8}), 50));
function fileAhead(deadline) {
  if (!world) return;
  const p = camera.position, todo = [];
  for (const list of Object.values(world.groups)) for (const o of list) if (!isFiled(o) && boxOf(o).intersectsBox(HOUSE_BOX)) todo.push(o);
  todo.sort((a, b) => boxOf(a).distanceToPoint(p) - boxOf(b).distanceToPoint(p));
  const until = performance.now() + Math.max(2, Math.min(deadline.timeRemaining(), 10));
  for (const o of todo) { fileMesh(o, until); if (performance.now() > until) break; }
  // rooms keep arriving for a while: look again later even when this pass finished everything
  setTimeout(() => idle(fileAhead), todo.length ? 0 : 3000);
}
const triA = new THREE.Vector3(), triB = new THREE.Vector3(), triC = new THREE.Vector3(), closest = new THREE.Vector3();
const tri = new THREE.Triangle(triA, triB, triC), pushed = new THREE.Vector3(), away = new THREE.Vector3();
let userMoved = false;                            // set by the visitor's own moves, cleared by a flight
controls.addEventListener("start", () => { userMoved = true; });
function keepClear() {
  if (!world || !userMoved || tween || reviewShot) return null;
  const p = camera.position;
  for (const list of Object.values(world.groups)) for (const o of list) {
    if (o.visible && !isFiled(o) && boxOf(o).distanceToPoint(p) < CLEAR + CELL) fileMesh(o);   // not filed ahead yet: now
  }
  pushed.set(0, 0, 0);
  const visible = new Map();                       // per mesh, for this check (a lifted roof doesn't count)
  for (let pass = 0; pass < 3; pass++) {           // a corner can take two or three pushes
    let gap = CLEAR; stamp++;
    const i0 = Math.floor((p.x - CLEAR) / CELL), i1 = Math.floor((p.x + CLEAR) / CELL);
    const j0 = Math.floor((p.y - CLEAR) / CELL), j1 = Math.floor((p.y + CLEAR) / CELL);
    const k0 = Math.floor((p.z - CLEAR) / CELL), k1 = Math.floor((p.z + CLEAR) / CELL);
    for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) for (let k = k0; k <= k1; k++) {
      for (const t of cells.get(cellKey(i, j, k)) || []) {
        if (triSeen[t] === stamp) continue;
        triSeen[t] = stamp;
        const o = triMesh[t];
        let vis = visible.get(o); if (vis === undefined) visible.set(o, vis = shown(o));
        if (!vis) continue;
        triA.fromArray(triPos, t * 9); triB.fromArray(triPos, t * 9 + 3); triC.fromArray(triPos, t * 9 + 6);
        tri.closestPointToPoint(p, closest);
        const d = closest.distanceTo(p);
        if (d >= gap) continue;
        gap = d;
        if (d > 1e-5) away.subVectors(p, closest).divideScalar(d); else tri.getNormal(away);
      }
    }
    if (gap >= CLEAR) break;
    const step = CLEAR - gap + 0.002;
    p.addScaledVector(away, step); pushed.addScaledVector(away, step);
  }
  return pushed.lengthSq() ? pushed : null;
}
// Inside a room the camera can tip past level (POLAR.room); this keeps it out of the floor.
// (Not during a flight, which may pass through floors on its way.)
function keepAboveFloor() {
  if (!inside || reviewShot || tween) return;
  const low = FLOOR_Y[inside] + 0.9;               // a little under a seated eye: never under the table
  if (camera.position.y < low) camera.position.y = low;
}

/* A small hint about the keys (or, on a touch screen, fingers), once: the first time a room is
   opened in the 3D. It goes after a few seconds, or as soon as the visitor moves. */
const TOUCH = matchMedia("(pointer: coarse)").matches && !matchMedia("(any-pointer: fine)").matches;
$("keysHint").innerHTML = TOUCH ? "One finger to look around · two to pan and zoom"
  : "<kbd>←</kbd><kbd>→</kbd><kbd>↑</kbd><kbd>↓</kbd> look around · <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> move · <kbd>Q</kbd><kbd>E</kbd> zoom";
let hintState = "new", hintTimer = 0;
try { if (localStorage.getItem("villa.keysHint")) hintState = "done"; } catch (e) {}
function maybeHint() {
  if (hintState !== "new" || !inside || !here || reviewing) return;
  hintState = "showing"; $("keysHint").hidden = false;
  try { localStorage.setItem("villa.keysHint", "1"); } catch (e) {}
  hintTimer = setTimeout(seenHint, 7000);
}
function seenHint() {
  if (hintState !== "showing") return;
  hintState = "done"; clearTimeout(hintTimer); $("keysHint").classList.add("going");
  setTimeout(() => { $("keysHint").hidden = true; }, 400);
}

/* ---------- Loop ---------- */
// The camera's field of view follows the window's shape (src/still.js, cameraFov): 45° tall
// on wider windows, a fixed sideways view on upright phones.
function fitCamera(aspect) { camera.aspect = aspect; camera.fov = cameraFov(aspect); camera.updateProjectionMatrix(); }
function resize() { const w = window.innerWidth, h = window.innerHeight; renderer.setSize(w, h, false); fitCamera(w / h); }
// The visitor's martini was modelled for a 16:9 frame. On an upright phone its spot is moved
// into the narrower, taller frame (the same for every phone, so the tall still matches it):
// across by how much narrower, down to near the bottom of a 19.5:9 phone's frame.
const T45 = Math.tan(STILL.fov / 2 * Math.PI / 180);
const UPRIGHT = {x: STILL.portrait.tanH / (T45 * 16 / 9), y: STILL.portrait.tanH / (9 / 19.5) / T45};
let uprightFrame = null;                 // set while the stills tool draws a tall still
const carryFrame = () => (uprightFrame ?? camera.aspect < STILL.portrait.below) ? UPRIGHT : null;
window.addEventListener("resize", resize); resize();
let lastFrame = 0;
renderer.setAnimationLoop(t => {
  const dt = Math.min(0.1, (t - (lastFrame || t)) / 1000); lastFrame = t;
  keyMove(dt);
  if (tween) {
    const k = Math.min(1, (t - tween.start) / tween.ms), e = ease(k);
    if (tween.via) {
      // quadratic curve: start, bend point, end
      const a = (1 - e) * (1 - e), b = 2 * e * (1 - e), c = e * e;
      camera.position.set(0, 0, 0).addScaledVector(tween.p0, a).addScaledVector(tween.via, b).addScaledVector(tween.p1, c);
    } else camera.position.lerpVectors(tween.p0, tween.p1, e);
    controls.target.lerpVectors(tween.t0, tween.t1, e); if (k >= 1) tween = null;
  }
  if (world) {
    fitFloors();
    world.update(t / 1000);
    // At the pool the visitor holds a martini at the bottom of the frame, once the
    // camera has settled on their lounger and while they stay near it.
    const stage = shotMoment || (current && current.moment && !$("panel").hidden ? current.moment : null);
    const r = stage && world.manifest.cameras[stage];
    world.carry(camera, Boolean(r && !tween && camera.position.distanceTo(tmpMoment.set(...r.pos)) < 1.2), carryFrame());
  }
  controls.update(); keepAboveFloor(); keepClear(); shiftView(); renderer.render(scene, camera); updatePins(); updateSpots(t);
  if (world && controls.enabled && !tween) maybeHint();
});

/* Deep links: #dining, #resume, ... */
function fromHash() { const h = location.hash.slice(1); if (h === "resume") showResume(true); else if (ROOMS.some(r => r.id === h)) { showResume(false); openRoom(h); } }
window.addEventListener("hashchange", fromHash);

/* Review pictures: ?save=name draws one 1920x1080 frame and hands it to the local
   preview server (tools/serve.py), which writes previews/browser_name.jpg.
   On the real site nothing is listening, so this does nothing there. */
function savePicture(name) {
  renderer.setPixelRatio(1); renderer.setSize(1920, 1080, false); fitCamera(16 / 9);
  controls.update();       // (as above) the camera may not have been aimed yet if the page is in the background
  fitFloors();             // and the floors may not have been fitted to where it is
  renderer.render(scene, camera);
  canvas.toBlob(blob => {
    fetch("/__shot?name=" + encodeURIComponent(name), {method: "POST", body: blob}).then(r => { document.body.dataset.saved = r.ok ? name : "failed"; }, () => {});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); resize();
  }, "image/jpeg", 0.92);
}

/* ---------- The 3D takes over from the still ----------
   The 3D has been drawing under the still from the still's own camera. Once it's built
   (and the furniture of a room opened meanwhile is in), the camera is put at that
   stop's view, the still eases back from any drag and fades away. The sharp lightmaps
   and full-size pictures carry on loading afterwards, as they always have; after the
   full bake they're several megabytes, too many to keep the still up for. */
async function handOver(w) {
  for (;;) {                             // a room opened while waiting: wait for that one instead
    const stop = stillStop;
    if (stop) await w.roomReady(stop.room || stop.id);
    if (stop === stillStop) break;
  }
  const [pos, target] = stillStop ? stillStop.view : [HOME.pos, HOME.target];
  tween = null;
  camera.position.set(...pos); controls.target.set(...target);
  if (stillStop) { controls.minDistance = stillStop.near ?? 4; if (stillStop.floor !== view) setView(stillStop.floor, false); }
  controls.update(); fitFloors();
  performance.mark("3d");
  document.body.dataset.ready = "3d";
  $("progress").hidden = true;
  await still.fadeOut();
  controls.enabled = true;
  if (!stillStop && $("panel").hidden) $("hint").hidden = false;
  if (afterStill && !stillStop) setView(afterStill);
}

/* ---------- Stills: npm run stills (tools/stills.mjs) opens the page with ?capture=1 and
   calls capture() for the landing shot and each stop. The view is drawn in tiles at
   twice the size wanted, taller and wider than the screen as src/still.js describes,
   shrunk, and handed back as WebP (and the link preview as JPEG). ---------- */
function shrink(src, sx, sy, sw, sh, w, h) {
  let c = src, x = sx, y = sy, cw = sw, ch = sh;
  while (cw / 2 >= w * 1.01) {           // halve in steps, so every pixel counts toward the result
    const n = document.createElement("canvas"); n.width = Math.round(cw / 2); n.height = Math.round(ch / 2);
    const g = n.getContext("2d"); g.imageSmoothingQuality = "high"; g.drawImage(c, x, y, cw, ch, 0, 0, n.width, n.height);
    c = n; x = 0; y = 0; cw = n.width; ch = n.height;
  }
  const out = document.createElement("canvas"); out.width = w; out.height = h;
  const g = out.getContext("2d"); g.imageSmoothingQuality = "high"; g.drawImage(c, x, y, cw, ch, 0, 0, w, h);
  return out;
}
async function capture(id, {height, quality = 0.8, og = false}) {
  const frames = n => new Promise(r => { const f = () => (--n ? requestAnimationFrame(f) : r()); requestAnimationFrame(f); });
  const r = ROOMS.find(x => x.id === id);
  if (r) openRoom(r.id, false);
  else { $("panel").hidden = true; current = null; setView("out", false); }
  const [pos, target] = r ? r.view : [HOME.pos, HOME.target];
  tween = null; camera.position.set(...pos); controls.target.set(...target); controls.update(); fitFloors();
  await world.sharp; await world.sharpMaps;
  if (r) { await world.roomReady(r.room || r.id); await opening; }
  await frames(30);                      // let the pool's martini settle on the camera, and the moodboard's pictures decode
  // draws the view at W x H with this vertical field of view, in tiles (big pictures are too big for one canvas)
  const draw = (W, H, fov) => {
    const big = document.createElement("canvas"); big.width = W; big.height = H;
    const g = big.getContext("2d");
    const nx = Math.ceil(W / 2048), ny = Math.ceil(H / 2048), tw = Math.ceil(W / nx), th = Math.ceil(H / ny);
    renderer.setPixelRatio(1); renderer.setSize(tw, th, false);
    camera.fov = fov; camera.aspect = W / H;
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      camera.setViewOffset(W, H, i * tw, j * th, tw, th); camera.updateProjectionMatrix();
      controls.update(); renderer.render(scene, camera);
      g.drawImage(canvas, 0, 0, tw, th, i * tw, j * th, tw, th);
    }
    camera.clearViewOffset(); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); resize();
    return big;
  };
  const files = stillFiles(r ? r.id : "landing"), out = {};
  // the wide still (and its square crop), drawn at 2 x the largest size wanted
  const H = height * 2, W = Math.round(H * STILL.aspect);
  const big = draw(W, H, STILL.renderFov);
  for (const [k, w] of files.sizes.wide.entries()) out[files.wide[k]] = shrink(big, 0, 0, W, H, w, Math.round(w / STILL.aspect)).toDataURL("image/webp", quality);
  for (const [k, w] of files.sizes.square.entries()) out[files.square[k]] = shrink(big, (W - H) / 2, 0, H, H, w, w).toDataURL("image/webp", quality);
  // the tall still, for upright phones, with the martini where an upright frame puts it
  uprightFrame = true; await frames(3);
  const TW = Math.max(...files.sizes.tall) * 2, TH = Math.round(TW / STILL.portrait.aspect);
  const tall = draw(TW, TH, STILL.portrait.renderFov);
  uprightFrame = null;
  for (const [k, w] of files.sizes.tall.entries()) out[files.tall[k]] = shrink(tall, 0, 0, TW, TH, w, Math.round(w / STILL.portrait.aspect)).toDataURL("image/webp", quality);
  // tiny copies, shown blurred the moment the stop is opened on the still, until its own still arrives
  out.thumb = {wide: shrink(big, 0, 0, W, H, 96, 40).toDataURL("image/webp", 0.5),
    tall: shrink(tall, 0, 0, TW, TH, 40, 95).toDataURL("image/webp", 0.5)};
  if (og) {
    // the link preview: exactly what a 1200 x 630 window shows of the landing shot
    const vh = H / STILL.margin, vw = vh * 1200 / 630;
    out["og.jpg"] = shrink(big, (W - vw) / 2, (H - vh) / 2, vw, vh, 1200, 630).toDataURL("image/jpeg", 0.88);
  }
  return out;
}

/* ---------- Load the villa, then start ---------- */
loadWorld(renderer, scene, f => setProgress(f)).then(w => {
  world = w;
  performance.mark("world");
  idle(fileAhead);                       // the camera's collision triangles (keepClear), a little at a time
  // a room's hotspots show once its furniture is in
  for (const s of spots) { const r = ROOMS.find(x => x.id === s.stop); w.roomReady(r.room || r.id).then(() => { s.ready = true; }); }
  if (still && still.on) {
    // the still is still up: the 3D draws underneath it, from its camera
    if (current) opening = w.openRoom(current.room || current.id);
    view = stillStop ? stillStop.floor : view;
    setView(view, false);
  } else {
    setView(view, false);
    if (location.hash) fromHash(); else setView("out", false);
  }

  // For review pictures: ?shot=landing (or pool, entrance, dining, chess) puts the
  // camera exactly where Blender's preview camera is, ?view=g picks which floors
  // show, and ?ui=0 hides the interface.
  const shot = w.manifest.cameras[params.get("shot")];
  if (params.get("view")) setView(params.get("view"), !shot);
  if (shot) {
    // the review cameras can sit below what they look at, which normal navigation forbids
    reviewShot = true; controls.maxPolarAngle = Math.PI; controls.minDistance = 0;
    camera.fov = shot.fov; camera.updateProjectionMatrix(); camera.position.set(...shot.pos); controls.target.set(...shot.target); controls.enableDamping = false;
    controls.update();      // aim it now: a page in a background tab gets no animation frames to do it
    if (params.get("shot").endsWith("_moment")) shotMoment = params.get("shot");
    opening = w.openRoom(params.get("shot").split("_")[0]);    // its room first, and its moodboard filled
  }
  if (params.get("ui") === "0" || params.has("capture")) document.body.classList.add("bare");
  if (params.has("capture")) window.capture = capture;

  if (params.has("debug")) window.villa = {THREE, scene, camera, controls, renderer, world: w, keepClear, moved: () => { userMoved = true; }};   // for poking around in the console
  w.rooms.then(() => opening).then(() => {
    document.body.dataset.ready = "rooms";
    if (current && !$("panel").hidden) renderPanel(current);      // picks up a figure's credit
    if (params.get("save")) setTimeout(() => savePicture(params.get("save")), 2500);
  });
  document.body.dataset.ready = "yes";
  if (still && still.on) handOver(w);
  else { performance.mark("3d"); if (!current && !reviewing) $("hint").hidden = false; }
}).catch(err => {
  console.error(err);
  // the still stays up, labels, panels and the resume still work
  const p = $("progress");
  p.hidden = false; p.classList.add("failed");
  $("progressText").textContent = "The 3D house couldn't load here. The labels, the Rooms menu and the resume still work.";
  if (still) still.on = true;
});

/* A link to a stop (#dining) opens its panel, on the still or in the 3D */
if (still && location.hash) fromHash();
