// The page itself: camera, the three views, labels, the side panel, the rooms
// menu, the resume and links like #dining. This is the navigation from the
// blockout prototype, kept as it was. The only real change is that the villa is
// now loaded from Blender's export (see world.js) instead of being built from boxes.

import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
import {ROOMS, FLOOR_NAME, RESUME} from "./rooms.js";
import {loadWorld, TONE_MAPPING} from "./world.js";

const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);

/* ---------- Renderer, camera, controls ---------- */
const canvas = $("scene");
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: params.has("save")});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = TONE_MAPPING;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.3, 4000);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.dampingFactor = 0.08; controls.maxPolarAngle = Math.PI / 2 - 0.04; controls.minDistance = 4; controls.maxDistance = 90;

const HOME = {pos: [-19, 5.5, 30], target: [-2, 1.8, 8]};      // the landing shot
camera.position.set(...HOME.pos); controls.target.set(...HOME.target);

/* ---------- Views and fly-to ---------- */
let world = null;
let view = "out";
function setView(v, fly = true) {
  view = v;
  if (world) {
    world.groups.roof.forEach(o => { o.visible = v === "out"; });      // the roof lifts off for the floor views
    world.groups.upper.forEach(o => { o.visible = v !== "g"; });       // and the upstairs too, to see the ground floor
  }
  $("vOut").setAttribute("aria-pressed", v === "out"); $("vG").setAttribute("aria-pressed", v === "g"); $("vU").setAttribute("aria-pressed", v === "u");
  if (fly) {
    if (v === "out") flyTo(HOME.pos, HOME.target);
    else if (v === "g") flyTo([0, 24, 20], [0, 0, 0]);
    else flyTo([0, 26, 18], [0, 3.4, -3]);
  }
}
let tween = null;
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
function flyTo(pos, target, ms = 1300) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  tween = {p0: camera.position.clone(), t0: controls.target.clone(), p1: new THREE.Vector3(...pos), t1: new THREE.Vector3(...target), start: performance.now(), ms: reduce ? 1 : ms};
}
let current = null;
function openRoom(id, fly = true) {
  const r = ROOMS.find(x => x.id === id); if (!r) return;
  current = r;
  if (r.floor !== view) setView(r.floor, false);
  if (fly) flyTo(r.view[0], r.view[1]);
  renderPanel(r); $("rooms").hidden = true; $("roomsBtn").setAttribute("aria-expanded", "false");
  $("hint").hidden = true;
  try { history.replaceState(null, "", "#" + r.id); } catch (e) {}
}
function renderPanel(r) {
  const i = ROOMS.indexOf(r);
  let h = `<div class="eyebrow">${r.area} · ${FLOOR_NAME[r.floor]}</div><h2>${r.title}</h2>`;
  h += r.body.map(p => `<p>${p}</p>`).join("");
  if (r.links) h += `<div class="links">${r.links.map(([t, u, internal, ghost]) => `<a href="${u}" ${internal ? `data-go="${u.slice(1)}"` : `target="_blank" rel="noopener"`} class="${ghost ? "ghost" : ""}">${t}</a>`).join("")}</div>`;
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
function updatePins() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  ROOMS.forEach((r, i) => {
    const el = pinEls[i];
    const show = view === "out" ? r.floor === "out" : r.floor === view;
    tmp.set(...r.at).project(camera);
    if (!show || tmp.z > 1 || tmp.x < -1.05 || tmp.x > 1.05 || tmp.y < -1.05 || tmp.y > 1.05) { el.hidden = true; return; }
    el.hidden = false; el.style.left = ((tmp.x + 1) / 2 * w) + "px"; el.style.top = ((1 - tmp.y) / 2 * h) + "px";
  });
}

/* ---------- Loop ---------- */
function resize() { const w = window.innerWidth, h = window.innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
window.addEventListener("resize", resize); resize();
renderer.setAnimationLoop(t => {
  if (tween) {
    const k = Math.min(1, (t - tween.start) / tween.ms), e = ease(k);
    camera.position.lerpVectors(tween.p0, tween.p1, e); controls.target.lerpVectors(tween.t0, tween.t1, e); if (k >= 1) tween = null;
  }
  if (world) world.update(t / 1000);
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

  // For review pictures: ?shot=landing (or pool, entrance) puts the camera exactly
  // where Blender's preview camera is, and ?ui=0 hides the interface.
  const shot = w.manifest.cameras[params.get("shot")];
  if (shot) { camera.fov = shot.fov; camera.updateProjectionMatrix(); camera.position.set(...shot.pos); controls.target.set(...shot.target); controls.enableDamping = false; }
  if (params.get("ui") === "0") document.body.classList.add("bare");
  if (params.get("view")) setView(params.get("view"), !shot);

  if (params.has("debug")) window.villa = {THREE, scene, camera, controls, renderer, world: w};   // for poking around in the console
  $("loading").hidden = true;
  w.sharp.then(() => { document.body.dataset.ready = "sharp"; if (params.get("save")) setTimeout(() => savePicture(params.get("save")), 2500); });
  document.body.dataset.ready = "yes";
}).catch(err => {
  console.error(err);
  $("loading").innerHTML = `<div>The villa could not be loaded.<small>You can still read the resume with the button above.</small></div>`;
  $("loading").style.pointerEvents = "none"; $("loading").style.background = "transparent";
});
