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
// marked with a room) is fetched afterwards, so it doesn't count here.
function firstViewFiles() {
  const files = [manifest.model, ...Object.values(manifest.sky)];
  for (const lm of Object.values(manifest.lightmaps)) if (!lm.room) files.push(lm.small);
  for (const m of Object.values(manifest.materials)) {
    if (m.room) continue;
    if (m.map) files.push(m.map);
    if (m.blend) files.push(m.blend.map, m.blend.mask);
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
  const files = [...firstViewFiles(), ...roomFiles(), ...Object.values(manifest.lightmaps).map(lm => lm.file)];
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

test("downloads stay inside the brief's budget", () => {
  const first = firstViewFiles().reduce((n, f) => n + size(f), 0);
  const total = allFiles(ASSETS).reduce((n, f) => n + statSync(f).size, 0);
  assert.ok(first < 15 * MB, `landing view needs ${(first / MB).toFixed(1)} MB, the limit is 15 MB`);
  assert.ok(total < 60 * MB, `all assets come to ${(total / MB).toFixed(1)} MB, the limit is 60 MB`);
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
  }
  for (const r of ROOMS) {
    for (const [label, url, internal] of r.links || []) {
      assert.ok(label, `${r.id}: a link has no label`);
      if (internal) assert.ok(url === "#resume" || ids.has(url.slice(1)), `${r.id}: "${label}" points to ${url}, which isn't a room`);
      else assert.match(url, /^https:\/\//, `${r.id}: "${label}" should be an https link`);
    }
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
