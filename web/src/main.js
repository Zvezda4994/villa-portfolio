// The page itself: camera, the three views, labels, the side panel, the rooms
// menu, the resume and links like #dining. This is the navigation from the
// blockout prototype, kept as it was. The only real change is that the villa is
// now loaded from Blender's export (see world.js) instead of being built from boxes.

import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
import {ROOMS, FLOOR_NAME, RESUME} from "./rooms.js";
import {loadWorld, TONE_MAPPING} from "./world.js";

const $ = id => document.getElementById(id);
const esc = t => String(t).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[c]);
const params = new URLSearchParams(location.search);

/* ---------- Renderer, camera, controls ---------- */
const canvas = $("scene");
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: params.has("save")});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = TONE_MAPPING;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.3, 4000);
scene.add(camera);                       // so things carried by the camera (the visitor's hand) are drawn
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.dampingFactor = 0.08; controls.maxPolarAngle = Math.PI / 2 - 0.04; controls.minDistance = 4; controls.maxDistance = 90;

const HOME = {pos: [-19, 5.5, 30], target: [-2, 1.8, 8]};      // the landing shot
camera.position.set(...HOME.pos); controls.target.set(...HOME.target);

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
let lifted = "", inside = null;                  // inside: the floor whose room the camera is in
function fitFloors() {
  if (!world) return;
  const p = camera.position, inHouse = Math.abs(p.x) < HOUSE.halfW && Math.abs(p.z) < HOUSE.halfD;
  if (inside && !(inHouse && p.y < HOUSE.ceiling[inside])) inside = null;
  if (!inside && inHouse && p.y < HOUSE.ceiling[view]) inside = view;
  const now = inside ? "out" : view;             // inside a room, the whole house shows
  if (now === lifted) return;
  lifted = now;
  world.setVisible("roof", now === "out");      // the roof lifts off for the floor views
  world.setVisible("upper", now !== "g");       // and the upstairs too, to see the ground floor
}
function setView(v, fly = true) {
  view = v;
  fitFloors();
  controls.minDistance = 4;
  $("vOut").setAttribute("aria-pressed", v === "out"); $("vG").setAttribute("aria-pressed", v === "g"); $("vU").setAttribute("aria-pressed", v === "u");
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
  tween = {p0: camera.position.clone(), t0: controls.target.clone(), p1: new THREE.Vector3(...pos), t1: new THREE.Vector3(...target),
    via: via && new THREE.Vector3(...via), start: performance.now(), ms: reduce ? 1 : ms};
}
let current = null, opening = null;      // opening: the room's own loading (furniture, moodboard pictures)
let here = null;                         // the last room opened; its label stays while the camera is inside, panel closed or not
function openRoom(id, fly = true) {
  const r = ROOMS.find(x => x.id === id); if (!r) return;
  current = here = r;
  if (world) opening = world.openRoom(r.room || r.id);
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
function renderPanel(r) {
  const i = ROOMS.indexOf(r);
  let h = `<div class="eyebrow">${r.area} · ${FLOOR_NAME[r.floor]}</div><h2>${r.title}</h2>`;
  h += r.body.map(p => p.startsWith("<ul") ? p : `<p>${p}</p>`).join("");
  if (r.links) h += `<div class="links">${r.links.map(([t, u, internal, ghost]) => `<a href="${u}" ${internal ? `data-go="${u.slice(1)}"` : `target="_blank" rel="noopener"`} class="${ghost ? "ghost" : ""}">${t}</a>`).join("")}</div>`;
  // Credits for any figure seated in this room; they come and go with the figure itself.
  for (const f of Object.values(world?.manifest.figures || {})) {
    if (f.room === r.id) h += `<p class="credit">${esc(f.credit)} <a href="${encodeURI(f.link)}" target="_blank" rel="noopener">Model page</a></p>`;
  }
  if (r.todo) h += `<p class="todo">To do: ${r.todo}</p>`;
  $("panelBody").innerHTML = h; $("panel").hidden = false;
  $("panelBody").querySelectorAll("[data-go]").forEach(a => a.onclick = e => { e.preventDefault(); const t = a.dataset.go; if (t === "resume") showResume(true); else openRoom(t); });
  $("prevRoom").onclick = () => openRoom(ROOMS[(i - 1 + ROOMS.length) % ROOMS.length].id);
  $("nextRoom").onclick = () => openRoom(ROOMS[(i + 1) % ROOMS.length].id);
  document.querySelectorAll(".pin").forEach(p => p.classList.toggle("on", p.dataset.id === r.id));
}
$("panelX").onclick = () => { $("panel").hidden = true; current = null; document.querySelectorAll(".pin").forEach(p => p.classList.remove("on")); };
$("vOut").onclick = () => setView("out"); $("vG").onclick = () => setView("g"); $("vU").onclick = () => setView("u");

/* Room list */
{
  let h = "";
  for (const f of ["out", "g", "u"]) { h += `<h3>${FLOOR_NAME[f]}</h3>`; ROOMS.filter(r => r.floor === f).forEach(r => h += `<button data-id="${r.id}">${r.title}<span>${r.area}</span></button>`); }
  $("rooms").innerHTML = h; $("rooms").querySelectorAll("button").forEach(b => b.onclick = () => openRoom(b.dataset.id));
}
$("roomsBtn").onclick = () => { const open = $("rooms").hidden; $("rooms").hidden = !open; $("roomsBtn").setAttribute("aria-expanded", open); };

/* Plain resume view: the fast path for anyone skimming */
{
  let h = `<header><h1>${RESUME.name}</h1><button class="pill" id="resumeBack">Back to the house</button></header>`;
  for (const [k, items] of RESUME.sections) h += `<section><div class="k">${k}</div><div>${items.map(([t, d]) => `<h4>${t}</h4><p>${d}</p>`).join("")}</div></section>`;
  if (RESUME.todo) h += `<p class="todo">${RESUME.todo}</p>`;
  $("resumeBody").innerHTML = h; $("resumeBack").onclick = () => showResume(false);
}
function showResume(on) { $("resume").hidden = !on; if (on) { $("panel").hidden = true; try { history.replaceState(null, "", "#resume"); } catch (e) {} } }
$("resumeBtn").onclick = () => showResume(true);

/* ---------- Pins (HTML labels that follow their 3D anchor) ---------- */
const pinEls = ROOMS.map(r => { const b = document.createElement("button"); b.className = "pin"; b.dataset.id = r.id; b.innerHTML = `<i></i>${r.title}`; b.onclick = () => openRoom(r.id); $("pins").appendChild(b); return b; });
const tmp = new THREE.Vector3();
const tmpMoment = new THREE.Vector3();
let shotMoment = null;                   // set when a review picture is taken from a staged moment's camera
function updatePins() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  ROOMS.forEach((r, i) => {
    const el = pinEls[i];
    // inside a room only its own label shows, so none of the others shine through the walls;
    // the Outside, Ground and Upstairs overviews show their floor's labels as before
    const show = inside ? r === here : (view === "out" ? r.floor === "out" : r.floor === view);
    tmp.set(...r.at).project(camera);
    if (!show || tmp.z > 1 || tmp.x < -1.05 || tmp.x > 1.05 || tmp.y < -1.05 || tmp.y > 1.05) { el.hidden = true; return; }
    el.hidden = false; el.style.left = ((tmp.x + 1) / 2 * w) + "px"; el.style.top = ((1 - tmp.y) / 2 * h) + "px";
  });
}

/* ---------- Things in the scene that open a panel (the contact card at the pool) ---------- */
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const shown = o => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
// The stop whose panel the thing under the pointer opens, if any. It only counts if
// nothing solid in the scene is in front of it.
function stopUnder(e) {
  if (!world) return null;
  const rect = canvas.getBoundingClientRect();
  pointer.set((e.clientX - rect.left) / rect.width * 2 - 1, 1 - (e.clientY - rect.top) / rect.height * 2);
  raycaster.setFromCamera(pointer, camera);
  for (const r of ROOMS) {
    if (!r.click) continue;
    const hit = raycaster.intersectObjects(world.meshesWith(r.click).filter(shown), false)[0];
    if (!hit) continue;
    const first = raycaster.intersectObjects(scene.children, true).find(h => shown(h.object) && !h.object.material.transparent);
    if (first && first.distance < hit.distance - 0.01) continue;
    return r;
  }
  return null;
}
let press = null, lastHover = 0;
canvas.addEventListener("pointerdown", e => { press = {x: e.clientX, y: e.clientY, t: performance.now()}; });
canvas.addEventListener("pointerup", e => {
  const p = press; press = null;
  // a drag to look around isn't a click
  if (!p || Math.hypot(e.clientX - p.x, e.clientY - p.y) > 6 || performance.now() - p.t > 600) return;
  const r = stopUnder(e);
  if (r) { showResume(false); openRoom(r.id, camera.position.distanceTo(tmp.set(...r.view[0])) > 1.2); }
});
canvas.addEventListener("pointermove", e => {
  if (e.buttons || e.pointerType !== "mouse" || performance.now() - lastHover < 100) return;
  lastHover = performance.now();
  canvas.style.cursor = stopUnder(e) ? "pointer" : "";
});

/* ---------- Loop ---------- */
function resize() { const w = window.innerWidth, h = window.innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
window.addEventListener("resize", resize); resize();
renderer.setAnimationLoop(t => {
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
    world.carry(camera, Boolean(r && !tween && camera.position.distanceTo(tmpMoment.set(...r.pos)) < 1.2));
  }
  controls.update(); renderer.render(scene, camera); updatePins();
});

/* Deep links: #dining, #resume, ... */
function fromHash() { const h = location.hash.slice(1); if (h === "resume") showResume(true); else if (ROOMS.some(r => r.id === h)) { showResume(false); openRoom(h); } }
window.addEventListener("hashchange", fromHash);

/* Review pictures: ?save=name draws one 1920x1080 frame and hands it to the local
   preview server (tools/serve.py), which writes previews/browser_name.jpg.
   On the real site nothing is listening, so this does nothing there. */
function savePicture(name) {
  renderer.setPixelRatio(1); renderer.setSize(1920, 1080, false); camera.aspect = 16 / 9; camera.updateProjectionMatrix();
  controls.update();       // (as above) the camera may not have been aimed yet if the page is in the background
  fitFloors();             // and the floors may not have been fitted to where it is
  renderer.render(scene, camera);
  canvas.toBlob(blob => {
    fetch("/__shot?name=" + encodeURIComponent(name), {method: "POST", body: blob}).then(r => { document.body.dataset.saved = r.ok ? name : "failed"; }, () => {});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); resize();
  }, "image/jpeg", 0.92);
}

/* ---------- Load the villa, then start ---------- */
loadWorld(renderer, scene, (done, total) => { $("loadingNote").textContent = `${done} of ${total}`; }).then(w => {
  world = w;
  setView(view, false);
  if (location.hash) fromHash(); else setView("out", false);

  // For review pictures: ?shot=landing (or pool, entrance, dining, chess) puts the
  // camera exactly where Blender's preview camera is, ?view=g picks which floors
  // show, and ?ui=0 hides the interface.
  const shot = w.manifest.cameras[params.get("shot")];
  if (params.get("view")) setView(params.get("view"), !shot);
  if (shot) {
    // the review cameras can sit below what they look at, which normal navigation forbids
    controls.maxPolarAngle = Math.PI; controls.minDistance = 0;
    camera.fov = shot.fov; camera.updateProjectionMatrix(); camera.position.set(...shot.pos); controls.target.set(...shot.target); controls.enableDamping = false;
    controls.update();      // aim it now: a page in a background tab gets no animation frames to do it
    if (params.get("shot").endsWith("_moment")) shotMoment = params.get("shot");
    opening = w.openRoom(params.get("shot").split("_")[0]);    // its room first, and its moodboard filled
  }
  if (params.get("ui") === "0") document.body.classList.add("bare");

  if (params.has("debug")) window.villa = {THREE, scene, camera, controls, renderer, world: w};   // for poking around in the console
  $("loading").hidden = true;
  w.sharp.then(() => { document.body.dataset.ready = "sharp"; });
  w.rooms.then(() => opening).then(() => {
    document.body.dataset.ready = "rooms";
    if (current && !$("panel").hidden) renderPanel(current);      // picks up a figure's credit
    if (params.get("save")) setTimeout(() => savePicture(params.get("save")), 2500);
  });
  document.body.dataset.ready = "yes";
}).catch(err => {
  console.error(err);
  $("loading").innerHTML = `<div>The villa could not be loaded.<small>You can still read the resume with the button above.</small></div>`;
  $("loading").style.pointerEvents = "none"; $("loading").style.background = "transparent";
});
