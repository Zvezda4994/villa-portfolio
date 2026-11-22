// Checks that run before every deploy (npm test). They don't need a browser:
// they read the files in web/ and make sure the site can actually load them.

import {test} from "node:test";
import assert from "node:assert/strict";
import {readFileSync, statSync, readdirSync} from "node:fs";
import {join, dirname} from "node:path";
import {fileURLToPath, pathToFileURL} from "node:url";

const WEB = join(dirname(fileURLToPath(import.meta.url)), "..", "web");
const ASSETS = join(WEB, "assets");
const manifest = JSON.parse(readFileSync(join(ASSETS, "manifest.json"), "utf8"));
const MB = 1e6;

const size = rel => statSync(join(ASSETS, rel)).size;

function allFiles(dir) {
  return readdirSync(dir, {withFileTypes: true}).flatMap(e => e.isDirectory() ? allFiles(join(dir, e.name)) : [join(dir, e.name)]);
}

// Every file needed before the landing view can show. Furniture (anything
// marked with a room) is fetched afterwards, so it doesn't count here, and the
// biggest pictures load as 512 px copies first (manifest "smallMaps").
function firstViewFiles() {
  const small = manifest.smallMaps || {};
  const files = [manifest.model, ...Object.values(manifest.sky)];
  for (const lm of Object.values(manifest.lightmaps)) if (!lm.room) files.push(lm.small);
  for (const m of Object.values(manifest.materials)) {
    if (m.room) continue;
    if (m.map) files.push(small[m.map] || m.map);
    if (m.blend) files.push(small[m.blend.map] || m.blend.map, m.blend.mask);
  }
  return [...new Set(files)];
}

// Everything the furnished rooms fetch once the first view is up.
function roomFiles() {
  const files = Object.values(manifest.rooms || {}).map(r => r.model);
  for (const f of Object.values(manifest.figures || {})) files.push(f.model);
  for (const lm of Object.values(manifest.lightmaps)) if (lm.room) files.push(lm.file);
  for (const m of Object.values(manifest.materials)) if (m.room && m.map) files.push(m.map);
  return [...new Set(files)];
}

test("every file the manifest names exists", () => {
  const files = [...firstViewFiles(), ...roomFiles(), ...Object.values(manifest.lightmaps).map(lm => lm.file), ...Object.keys(manifest.smallMaps || {})];
  for (const f of files) assert.ok(size(f) > 0, `${f} is empty or missing`);
});

test("a figure is never shown without its credit", () => {
  for (const [name, f] of Object.entries(manifest.figures || {})) {
    assert.ok(manifest.rooms[f.room], `figure ${name} sits in "${f.room}", which isn't a furnished room`);
    assert.ok(typeof f.credit === "string" && f.credit.trim().length > 10, `figure ${name} needs a credit line`);
    assert.match(f.link || "", /^https:\/\//, `figure ${name} needs an https link to the model's page`);
  }
});

test("furnished rooms only name lightmaps and pictures that belong to them", () => {
  for (const [name, lm] of Object.entries(manifest.lightmaps)) {
    if (lm.room) assert.ok(manifest.rooms[lm.room], `lightmap ${name} belongs to "${lm.room}", which isn't in the manifest's rooms`);
  }
  for (const [name, m] of Object.entries(manifest.materials)) {
    if (m.room) assert.ok(manifest.rooms[m.room], `material ${name} belongs to "${m.room}", which isn't in the manifest's rooms`);
  }
});

// The brief sets targets, not a total limit: the landing view interactive in about
// 10 MB, and each room's own download around 4 MB. These checks leave a little
// room over each target so a small change doesn't block a deploy.
const LANDING_LIMIT = 11 * MB;
const ROOM_LIMIT = 4.5 * MB;
// Rooms known to be over, and what they may use (none since step 6).
const ROOM_ALLOWANCE = {};

test("the landing view stays near its 10 MB target", () => {
  const first = firstViewFiles().reduce((n, f) => n + size(f), 0);
  assert.ok(first < LANDING_LIMIT, `landing view needs ${(first / MB).toFixed(1)} MB; the target is about 10 MB`);
});

test("each room's own download stays near its 4 MB target", () => {
  // the room's file, its lightmap and the pictures only it uses (a seated figure
  // can come and go, so it's counted on its own, not here)
  for (const [name, room] of Object.entries(manifest.rooms || {})) {
    const files = new Set([room.model]);
    for (const lm of Object.values(manifest.lightmaps)) if (lm.room === name) files.add(lm.file);
    for (const m of Object.values(manifest.materials)) if (m.room === name && m.map && !m.map.includes("/figure_")) files.add(m.map);
    const bytes = [...files].reduce((n, f) => n + size(f), 0);
    const limit = ROOM_ALLOWANCE[name] ?? ROOM_LIMIT;
    assert.ok(bytes < limit, `the ${name} room downloads ${(bytes / MB).toFixed(1)} MB; the target is about 4 MB`);
  }
});

test("the 512 px copies are the same pictures, smaller", () => {
  for (const [full, small] of Object.entries(manifest.smallMaps || {})) {
    const a = readFileSync(join(ASSETS, full)), b = readFileSync(join(ASSETS, small));
    assert.equal(b.readUInt32LE(20), 512, `${small} should be 512 px wide`);
    assert.ok(a.readUInt32LE(20) > 512, `${full} needs no small copy`);
    assert.equal(a.readUInt32LE(28 + 0), b.readUInt32LE(28 + 0));
  }
});

test("KTX2 textures are well formed", () => {
  const ktx = allFiles(ASSETS).filter(f => f.endsWith(".ktx2"));
  assert.ok(ktx.length > 0);
  for (const f of ktx) {
    const b = readFileSync(f);
    assert.deepEqual([...b.subarray(0, 12)], [0xab, 0x4b, 0x54, 0x58, 0x20, 0x32, 0x30, 0xbb, 0x0d, 0x0a, 0x1a, 0x0a], `${f}: not a KTX2 file`);
    const width = b.readUInt32LE(20), height = b.readUInt32LE(24), levels = b.readUInt32LE(40), scheme = b.readUInt32LE(44);
    assert.ok(width % 4 === 0 && height % 4 === 0, `${f}: ${width}x${height} is not a multiple of 4`);
    assert.ok(levels >= 1, `${f}: no mip levels`);
    assert.ok(scheme === 0 || scheme === 2, `${f}: compression scheme ${scheme} is not one three.js reads`);
    for (let i = 0; i < levels; i++) {
      const offset = Number(b.readBigUInt64LE(80 + 24 * i)), length = Number(b.readBigUInt64LE(88 + 24 * i));
      assert.ok(offset + length <= b.length, `${f}: mip level ${i} runs past the end of the file`);
    }
  }
});

test("sky files are run-length .hdr panoramas", () => {
  for (const rel of Object.values(manifest.sky)) {
    const head = readFileSync(join(ASSETS, rel)).subarray(0, 120).toString("latin1");
    assert.ok(head.startsWith("#?RADIANCE"), `${rel}: missing the Radiance header`);
    const m = head.match(/-Y (\d+) \+X (\d+)/);
    assert.ok(m, `${rel}: missing the size line`);
    assert.equal(Number(m[2]), 2 * Number(m[1]), `${rel}: a panorama should be twice as wide as it is tall`);
  }
});

test("the models only use extensions and materials the site understands", () => {
  const models = [[manifest.model, null], ...Object.entries(manifest.rooms || {}).map(([name, r]) => [r.model, name]),
    ...Object.values(manifest.figures || {}).map(f => [f.model, f.room])];
  for (const [file, room] of models) {
    const b = readFileSync(join(ASSETS, file));
    assert.equal(b.toString("latin1", 0, 4), "glTF", `${file} is not a binary glTF`);
    assert.equal(b.readUInt32LE(4), 2);
    const json = JSON.parse(b.toString("utf8", 20, 20 + b.readUInt32LE(12)));
    const supported = new Set(["EXT_meshopt_compression", "KHR_materials_emissive_strength", "KHR_texture_basisu"]);
    for (const ext of json.extensionsUsed || []) assert.ok(supported.has(ext), `${file} uses ${ext}, which the loader isn't set up for`);
    for (const mat of json.materials || []) {
      const m = manifest.materials[mat.name];
      assert.ok(m, `${file}: material "${mat.name}" has no entry in the manifest`);
      // the first view can't wait for a room's pictures, so the house must not use them
      if (!room) assert.ok(!m.room, `${file}: material "${mat.name}" belongs to the ${m.room} room`);
    }
    const groups = new Set(["ground", "upper", "roof", "out"]);
    for (const node of json.nodes.filter(n => n.mesh !== undefined)) {
      const extras = node.extras || {};
      assert.ok(groups.has(extras.group), `${file} ${node.name}: unknown group "${extras.group}"`);
      assert.equal(extras.room ?? null, room, `${file} ${node.name}: furniture should be in its room's file`);
      if (extras.lightmap) {
        assert.ok(manifest.lightmaps[extras.lightmap], `${file} ${node.name}: no lightmap called ${extras.lightmap}`);
        for (const p of json.meshes[node.mesh].primitives) assert.ok("TEXCOORD_1" in p.attributes, `${file} ${node.name}: lightmapped but has no second UV set`);
      }
      const pictured = json.meshes[node.mesh].primitives.some(p => p.material !== undefined && manifest.materials[json.materials[p.material].name].map);
      if (pictured) for (const p of json.meshes[node.mesh].primitives) assert.ok("TEXCOORD_0" in p.attributes, `${file} ${node.name}: has a picture but no UVs`);
    }
  }
});

// Hotspot anchors (blender/villa/geo.py, Builder.anchor): empties the site can hang a click
// target on. Each is listed in the manifest and is a plain node in its own room's file.
test("the hotspot anchors are in the manifest and in their rooms' files", () => {
  const wanted = ["living_couch_seat", "resume_door", "library_real_books", "library_laptop", "bedroom_record_player", "gym_gloves"];
  const spots = manifest.hotspots || {};
  for (const name of wanted) assert.ok(spots[name], `no hotspot anchor called ${name}`);
  for (const [name, h] of Object.entries(spots)) {
    assert.ok(manifest.rooms[h.room], `${name}: no room called ${h.room}`);
    assert.equal(h.pos.length, 3);
    const b = readFileSync(join(ASSETS, manifest.rooms[h.room].model));
    const json = JSON.parse(b.toString("utf8", 20, 20 + b.readUInt32LE(12)));
    const node = json.nodes.find(n => n.extras && n.extras.hotspot === name);
    assert.ok(node, `${name}: not in ${manifest.rooms[h.room].model}`);
    assert.equal(node.mesh, undefined, `${name}: an anchor has no geometry`);
    node.translation.forEach((v, i) => assert.ok(Math.abs(v - h.pos[i]) < 1e-3, `${name}: the manifest and the model disagree`));
  }
});

// The living room's moodboard: pictures shrunk by `npm run moodboard`, picked at random
// by the page each time the room opens. They are never part of the first view.
test("the moodboard's pictures and frames are in order", () => {
  const frames = Object.entries(manifest.materials).filter(([, m]) => m.moodboard !== undefined);
  assert.ok(frames.length >= 4 && frames.length <= 6, `the moodboard should have 4 to 6 frames, not ${frames.length}`);
  for (const [name, m] of frames) {
    assert.ok(Number.isFinite(m.moodboard) && m.moodboard > 0.2 && m.moodboard < 5, `${name}: its picture's shape should be width / height`);
    assert.ok(manifest.rooms[m.room], `${name} belongs to "${m.room}", which isn't a furnished room`);
    assert.ok(!m.map, `${name} should have no picture of its own; the page lays one over it`);
  }
  const list = join(ASSETS, "moodboard", "moodboard.json");
  let images = [];
  try { images = JSON.parse(readFileSync(list, "utf8")).images; } catch { return; }      // no pictures yet: plain colour fields
  assert.ok(Array.isArray(images), "moodboard.json should list its pictures under images");
  const first = new Set(firstViewFiles());
  for (const img of images) {
    assert.match(img.file, /^moodboard\/[\w-]+\.jpg$/, `${img.file}: expected moodboard/<name>.jpg`);
    assert.ok(Number.isInteger(img.w) && Number.isInteger(img.h) && img.w > 0 && img.h > 0, `${img.file}: needs its size`);
    assert.ok(Math.max(img.w, img.h) <= 1024, `${img.file}: ${img.w}x${img.h} is bigger than the site needs`);
    assert.ok(size(img.file) < 400e3, `${img.file} is ${(size(img.file) / 1e3).toFixed(0)} KB; run npm run moodboard`);
    assert.ok(!first.has(img.file), `${img.file} must not be part of the landing download`);
  }
  const listed = new Set(images.map(i => i.file.split("/")[1]));
  for (const f of readdirSync(join(ASSETS, "moodboard")).filter(f => f.endsWith(".jpg"))) {
    assert.ok(listed.has(f), `moodboard/${f} isn't listed in moodboard.json, so it would be deployed for nothing`);
  }
});

test("rooms data is complete and its links go somewhere", async () => {
  const {ROOMS, FLOOR_NAME} = await import(pathToFileURL(join(WEB, "src", "rooms.js")).href);
  const ids = new Set();
  const isPoint = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);
  for (const r of ROOMS) {
    assert.match(r.id, /^[a-z0-9-]+$/, `room id "${r.id}" won't work as a #link`);
    assert.ok(!ids.has(r.id), `room id "${r.id}" is used twice`);
    ids.add(r.id);
    assert.ok(r.floor in FLOOR_NAME, `${r.id}: unknown floor "${r.floor}"`);
    assert.ok(isPoint(r.at), `${r.id}: "at" should be [x, y, z]`);
    assert.ok(Array.isArray(r.view) && r.view.length === 2 && r.view.every(isPoint), `${r.id}: "view" should be [camera, target]`);
    assert.ok(r.title && r.area && Array.isArray(r.body) && r.body.length, `${r.id}: needs a title, area and body text`);
    if (r.near !== undefined) assert.ok(Number.isFinite(r.near) && r.near > 0, `${r.id}: "near" should be a distance in metres`);
    for (const name of r.click || []) {
      const m = manifest.materials[name];
      assert.ok(m && m.room === r.id, `${r.id}: "click" names "${name}", which isn't a material of the ${r.id} room`);
    }
    if (r.moment) {
      // things carried with the camera (the visitor's hand) were modelled for this exact camera
      const cam = manifest.cameras[r.moment];
      assert.ok(cam, `${r.id}: no camera called "${r.moment}" in the manifest`);
      const off = Math.max(...[...cam.pos, ...cam.target].map((v, i) => Math.abs(v - r.view.flat()[i])));
      assert.ok(off < 0.002, `${r.id}: "view" is ${off.toFixed(3)} m off the ${r.moment} camera; copy pos and target from the manifest`);
    }
  }
  for (const r of ROOMS) {
    for (const [label, url, internal] of r.links || []) {
      assert.ok(label, `${r.id}: a link has no label`);
      if (internal) assert.ok(url === "#resume" || ids.has(url.slice(1)), `${r.id}: "${label}" points to ${url}, which isn't a room`);
      else assert.match(url, /^https:\/\//, `${r.id}: "${label}" should be an https link`);
    }
  }
});

// The dots in the rooms (HOTSPOTS in rooms.js): each on an exported anchor in its stop's room,
// doing exactly one thing.
test("every hotspot sits on an anchor in its stop's room and does one thing", async () => {
  const {ROOMS, HOTSPOTS} = await import(pathToFileURL(join(WEB, "src", "rooms.js")).href);
  const isPoint = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);
  for (const s of HOTSPOTS) {
    const stop = ROOMS.find(r => r.id === s.stop);
    assert.ok(stop, `hotspot ${s.anchor}: no stop called ${s.stop}`);
    const h = (manifest.hotspots || {})[s.anchor];
    assert.ok(h, `hotspot ${s.anchor}: no anchor of that name in the manifest`);
    assert.equal(h.room, stop.room || stop.id, `hotspot ${s.anchor}: its anchor is in the ${h.room} room, not ${stop.room || stop.id}`);
    assert.ok(s.label, `hotspot ${s.anchor}: needs a label for screen readers`);
    const does = ["view", "resume", "url", "tip"].filter(k => s[k]);
    assert.equal(does.length, 1, `hotspot ${s.anchor}: should do one thing, not ${does.join(" and ") || "nothing"}`);
    if (s.view) assert.ok(s.view.length === 2 && s.view.every(isPoint), `hotspot ${s.anchor}: "view" should be [camera, target]`);
    if (s.url) assert.match(s.url, /^https:\/\//);
  }
});

test("three.js is pinned to one exact version everywhere", () => {
  const html = readFileSync(join(WEB, "index.html"), "utf8");
  const world = readFileSync(join(WEB, "src", "world.js"), "utf8");
  const versions = [...html.matchAll(/three@([\w.-]+)\//g), ...world.matchAll(/three@([\w.-]+)\//g)].map(m => m[1]);
  assert.ok(versions.length >= 3, "expected the import map and the texture transcoder to name a three.js version");
  for (const v of versions) assert.match(v, /^\d+\.\d+\.\d+$/, `three@${v} should be an exact version`);
  assert.equal(new Set(versions).size, 1, `three.js versions don't match: ${[...new Set(versions)].join(", ")}`);
  for (const ref of ["styles.css", "src/main.js"]) assert.ok(html.includes(ref) && statSync(join(WEB, ref)).size > 0, `index.html needs ${ref}`);
});

test("the resume data has its sections and no phone number", () => {
  const raw = readFileSync(join(WEB, "resume.json"), "utf8");
  const d = JSON.parse(raw);
  assert.ok(d.name, "resume.json needs a name");
  for (const k of ["education", "experience", "projects", "skills"]) assert.ok(Array.isArray(d[k]) && d[k].length, `resume.json needs ${k}`);
  for (const c of d.contact) assert.match(c.url, /^(https:\/\/|mailto:)/, `contact "${c.label}" needs an https or mailto link`);
  // the web version shows email, LinkedIn and GitHub only
  assert.doesNotMatch(raw, /\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b/, "resume.json looks like it holds a phone number");
});

test("the Download PDF exists and is one page", () => {
  const pdf = readFileSync(join(ASSETS, "resume.pdf"));
  assert.ok(pdf.subarray(0, 5).toString() === "%PDF-", "assets/resume.pdf isn't a PDF; run npm run resume:pdf");
  const pages = pdf.toString("latin1").match(/\/Type\s*\/Page[^s]/g) || [];
  assert.equal(pages.length, 1, `assets/resume.pdf has ${pages.length} pages; it should fit on one`);
});

// The stills shown while the 3D loads (npm run stills): the landing shot and one per stop,
// in every size src/still.js names, and the link preview.
test("every still and the link preview exist", async () => {
  const {ROOMS} = await import(pathToFileURL(join(WEB, "src", "rooms.js")).href);
  const {stillFiles, STILL} = await import(pathToFileURL(join(WEB, "src", "still.js")).href);
  for (const id of ["landing", ...ROOMS.map(r => r.id)]) {
    const f = stillFiles(id);
    for (const [kind, names] of [["wide", f.wide], ["square", f.square], ["tall", f.tall]]) {
      names.forEach((name, i) => {
        const b = readFileSync(join(ASSETS, "stills", name));
        assert.equal(b.toString("latin1", 0, 4) + b.toString("latin1", 8, 12), "RIFFWEBP", `${name} isn't a WebP`);
        const w = f.sizes[kind][i];
        assert.ok(b.length < (id === "landing" ? 450e3 : 400e3), `${name} is ${(b.length / 1e3).toFixed(0)} KB`);
        // VP8 (lossy) keeps its size 26 bytes in; check the shape matches what the page assumes
        if (b.toString("latin1", 12, 16) === "VP8 ") {
          const W = b.readUInt16LE(26) & 0x3fff, H = b.readUInt16LE(28) & 0x3fff;
          assert.equal(W, w, `${name} should be ${w} px wide`);
          assert.equal(H, kind === "wide" ? Math.round(w / STILL.aspect) : kind === "tall" ? Math.round(w / STILL.portrait.aspect) : w, `${name} has the wrong height`);
        }
      });
    }
  }
  const thumbs = JSON.parse(readFileSync(join(ASSETS, "stills", "thumbs.json"), "utf8"));
  for (const id of ["landing", ...ROOMS.map(r => r.id)]) assert.ok(thumbs[id]?.wide && thumbs[id]?.tall, `thumbs.json has no thumbnails for ${id}`);
  const html = readFileSync(join(WEB, "index.html"), "utf8");
  const l = stillFiles("landing");
  for (const name of [...l.wide, ...l.square, ...l.tall]) assert.ok(html.includes("assets/stills/" + name), `index.html should offer ${name}`);
  const og = readFileSync(join(WEB, "og.jpg"));
  assert.equal(og[0], 0xff); assert.equal(og[1], 0xd8);
  assert.ok(og.length < 400e3, `og.jpg is ${(og.length / 1e3).toFixed(0)} KB; link previews want it small`);
  for (const tag of ["og:title", "og:description", "og:image", "og:image:width", "og:image:height", "twitter:card"]) {
    assert.match(html, new RegExp(`(property|name)="${tag}"`), `index.html needs ${tag}`);
  }
  assert.match(html, /og:image" content="https:\/\/[^"]+\/og\.jpg"/, "og:image must be a full https address");
});
