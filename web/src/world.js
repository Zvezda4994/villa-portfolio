// Loads the villa that Blender exported and sets up how it is drawn.
//
// The lighting is not calculated here. Blender worked it out once and saved it:
// big flat surfaces carry a "lightmap" texture, and small things (plants, rocks,
// window frames) carry their light in their vertices. All this file does is
// multiply that baked light by each surface's colour, add reflections of the
// sky, and fade distant things into haze.

import * as THREE from "three";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";
import {KTX2Loader} from "three/addons/loaders/KTX2Loader.js";
import {RGBELoader} from "three/addons/loaders/RGBELoader.js";
import {MeshoptDecoder} from "three/addons/libs/meshopt_decoder.module.js";

const ASSETS = "assets/";
const TRANSCODER = "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/basis/";

// How strongly each lightmap's surfaces reflect the sky. Indoors the sky is
// mostly hidden by ceilings, so reflections there are turned well down
// (furnished rooms' own lightmaps count as indoors too).
const REFLECT = {ext: 1.0, terrain: 1.0, gnd: 0.3, upr: 0.3};
const INDOOR_REFLECT = 0.3;

// Distance haze, in metres: none closer than `near`, strongest at `far`.
const HAZE = {near: 120, far: 1100, max: 0.45};

// Tone mapping turns the scene's real brightness into screen colours. Blender's
// previews use "AgX" with its "Medium High Contrast" look. three.js has AgX but
// not the looks, so this adds that one step (a contrast change in AgX's log
// space) to keep the browser and the Blender renders looking the same.
const LOOK = {contrast: 1.2, pivot: 0.7};   // found by fitting this formula to Blender's output for a set of test colours
const STUB = /vec3 CustomToneMapping\s*\(\s*vec3 color\s*\)\s*\{[^}]*\}/;
const hasStub = STUB.test(THREE.ShaderChunk.tonemapping_pars_fragment);
if (hasStub) {
  THREE.ShaderChunk.tonemapping_pars_fragment = THREE.ShaderChunk.tonemapping_pars_fragment.replace(STUB, `
vec3 CustomToneMapping( vec3 color ) {
	const mat3 inset = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 ) );
	const mat3 outset = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 ) );
	const float minEv = - 12.47393;
	const float maxEv = 4.026069;
	color *= toneMappingExposure;
	color = inset * ( LINEAR_SRGB_TO_LINEAR_REC2020 * color );
	color = ( log2( max( color, 1e-10 ) ) - minEv ) / ( maxEv - minEv );
	color = clamp( ( color - ${LOOK.pivot.toFixed(3)} ) * ${LOOK.contrast.toFixed(3)} + ${LOOK.pivot.toFixed(3)}, 0.0, 1.0 );   // the look
	color = agxDefaultContrastApprox( color );
	color = outset * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	return clamp( color, 0.0, 1.0 );
}`);
} else {
  console.warn("three.js changed its tone mapping code; using plain AgX, which looks a little flatter.");
}
export const TONE_MAPPING = hasStub ? THREE.CustomToneMapping : THREE.AgXToneMapping;

const hazeColor = new THREE.Vector3();

// Fade the surface toward the haze colour (the sky at the horizon) before the
// image is tone mapped, so the far hills sit back into the sky.
function addHaze(shader) {
  shader.uniforms.uHaze = {value: hazeColor};
  shader.uniforms.uHazeMax = {value: HAZE.max};
  shader.fragmentShader = "uniform vec3 uHaze;\nuniform float uHazeMax;\n" + shader.fragmentShader
    .replace("#include <fog_fragment>", "")
    .replace("#include <tonemapping_fragment>",
      "#ifdef USE_FOG\n  gl_FragColor.rgb = mix(gl_FragColor.rgb, uHaze, smoothstep(fogNear, fogFar, vFogDepth) * uHazeMax);\n#endif\n#include <tonemapping_fragment>");
}

// The sky's soft light is already in the lightmaps, so the general-purpose sky
// lighting three.js would add on top is removed. Reflections are kept.
const SKY_LIGHT_LINE = "iblIrradiance += getIBLIrradiance( geometryNormal );";
const bakedLightChunk = THREE.ShaderChunk.lights_fragment_maps.replace(SKY_LIGHT_LINE, "");
if (bakedLightChunk === THREE.ShaderChunk.lights_fragment_maps) console.warn("three.js changed its lighting code; baked surfaces may look too bright.");

function bakedShader(shader) {
  shader.fragmentShader = shader.fragmentShader.replace("#include <lights_fragment_maps>", bakedLightChunk);
  addHaze(shader);
}

// Sand with gravel borders: a second texture mixed in wherever a mask says so.
// The mask is laid out like the sand's lightmap, so it uses the same coordinates.
// `uniforms` is kept on the material so a sharper gravel picture can be swapped in later.
function gravelShader(blend, uniforms) {
  Object.assign(uniforms, {
    uGravelMap: {value: blend.map}, uGravelMask: {value: blend.mask},
    uGravelScale: {value: blend.scale}, uGravelTint: {value: blend.tint},
  });
  return shader => {
    bakedShader(shader);
    Object.assign(shader.uniforms, uniforms);
    shader.fragmentShader = "uniform sampler2D uGravelMap;\nuniform sampler2D uGravelMask;\nuniform float uGravelScale;\nuniform vec3 uGravelTint;\n" +
      shader.fragmentShader.replace("#include <map_fragment>", `#include <map_fragment>
  {
    vec3 gravel = texture2D(uGravelMap, vMapUv * uGravelScale).rgb * uGravelTint;
    diffuseColor.rgb = mix(diffuseColor.rgb, gravel, texture2D(uGravelMask, vLightMapUv).r);
  }`);
  };
}

// A small repeating pattern of ripples for the pool, made here so no image file is needed.
function rippleTexture(size = 128) {
  const h = (x, y) => {
    let v = 0;
    for (const [fx, fy, a, p] of [[1, 2, 1, 0.3], [3, 1, 0.6, 1.7], [2, 5, 0.35, 4.1], [5, 3, 0.3, 2.2], [7, 6, 0.15, 5.0]]) {
      v += a * Math.sin(2 * Math.PI * (fx * x + fy * y) / size + p);
    }
    return v;
  };
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const dx = (h(x + 1, y) - h(x - 1, y)) * 0.9, dy = (h(x, y + 1) - h(x, y - 1)) * 0.9;
    const n = new THREE.Vector3(-dx, -dy, 1).normalize();
    data.set([(n.x * 0.5 + 0.5) * 255, (n.y * 0.5 + 0.5) * 255, (n.z * 0.5 + 0.5) * 255, 255], (y * size + x) * 4);
  }
  const tex = new THREE.DataTexture(data, size, size);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.generateMipmaps = true;
  tex.repeat.set(0.6, 0.6);            // the water's UVs are in metres, so one tile covers about 1.7 m
  tex.needsUpdate = true;
  return tex;
}

// The order things load in:
//   1. the landing set: the house, the skies, the small lightmaps and the colour pictures
//      (the biggest ones as 512 px copies). The 3D can draw once these are in.
//   2. then one queue, one or two downloads at a time, in this order of preference:
//      a room the visitor opened; the sharp lightmaps; rooms the visitor is likely to
//      open next (hovered
//      labels, the open room's neighbours); the full-size colour pictures; then every
//      other room, so the floor views show furnished rooms (skipped when the browser
//      asks to save data).
// onProgress(fraction) reports step 1, by bytes: the 3D takes over from the still at 100%.
export async function loadWorld(renderer, scene, onProgress = () => {}) {
  const manifest = await (await fetch(ASSETS + "manifest.json")).json();
  const ktx2 = new KTX2Loader().setTranscoderPath(TRANSCODER).detectSupport(renderer);
  const gltfLoader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const hdr = new RGBELoader();
  const maxAniso = renderer.capabilities.getMaxAnisotropy();

  // ---- progress, by bytes: each file's size from the manifest until the server says ----
  const bytesOf = file => {
    const b = manifest.bytes || {}, stem = file.split("/").pop().replace(/\.\w+$/, "");
    if (file === manifest.model) return b.model;
    for (const [k, v] of Object.entries(manifest.sky)) if (v === file) return b["sky " + k];
    for (const [k, lm] of Object.entries(manifest.lightmaps)) {
      if (lm.file === file) return b["lightmap " + k];
      if (lm.small === file) return b["lightmap " + k + " (small)"];
    }
    return b["texture " + stem] ?? b["texture " + stem.replace(/_lo$/, "") + " (small)"];
  };
  const counted = new Map();                   // file -> [loaded, total]
  const report = () => {
    let got = 0, all = 0;
    for (const [l, t] of counted.values()) { got += Math.min(l, t); all += t; }
    onProgress(all ? got / all : 0);
  };
  const count = file => { counted.set(file, [0, bytesOf(file) || 3e5]); };
  const progressFor = file => e => {
    const c = counted.get(file); if (!c) return;
    if (e.lengthComputable && e.total) c[1] = e.total;
    c[0] = e.loaded; report();
  };
  const fetchTracked = (loader, file) => {
    const p = loader.loadAsync(ASSETS + file, progressFor(file));
    return p.then(v => { const c = counted.get(file); if (c) { c[0] = c[1]; report(); } return v; });
  };

  // ---- start every download needed for the first view at once ----
  // (furniture is left for later: materials and lightmaps marked with a room
  // are fetched together with that room, once the first view is up)
  const smallMaps = manifest.smallMaps || {};  // full-size picture -> its 512 px copy, for the biggest ones
  const colourMaps = {};
  const want = file => {
    if (!file || colourMaps[file]) return;
    const first = smallMaps[file] || file;
    count(first);
    colourMaps[file] = fetchTracked(ktx2, first);
  };
  for (const m of Object.values(manifest.materials)) {
    if (m.room) continue;
    want(m.map);
    if (m.blend) { want(m.blend.map); want(m.blend.mask); }
  }
  const smallLight = {};
  for (const [name, lm] of Object.entries(manifest.lightmaps)) {
    if (!lm.room) { count(lm.small); smallLight[name] = fetchTracked(ktx2, lm.small); }
  }
  // Panoramas taken from above each body of water, so it reflects what is really around it.
  const probeNames = Object.keys(manifest.sky).filter(k => k !== "background" && k !== "environment");
  for (const f of [manifest.model, ...Object.values(manifest.sky)]) count(f);
  const [gltf, skyTex, envTex, ...probeTex] = await Promise.all([
    fetchTracked(gltfLoader, manifest.model),
    fetchTracked(hdr, manifest.sky.background),
    fetchTracked(hdr, manifest.sky.environment),
    ...probeNames.map(k => fetchTracked(hdr, manifest.sky[k])),
  ]);

  // ---- sky, reflections, haze ----
  skyTex.mapping = THREE.EquirectangularReflectionMapping;
  scene.background = skyTex;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const reflections = pmrem.fromEquirectangular(envTex).texture;
  envTex.dispose();
  const probes = {};
  probeNames.forEach((k, i) => { probes[k] = pmrem.fromEquirectangular(probeTex[i]).texture; probeTex[i].dispose(); });
  pmrem.dispose();
  hazeColor.fromArray(manifest.fog.color);
  scene.fog = new THREE.Fog(0xffffff, HAZE.near, HAZE.far);   // only switches the distance maths on; the colour comes from hazeColor
  renderer.toneMappingExposure = manifest.exposure;

  // ---- materials ----
  const lightScale = manifest.lightRange;      // baked light was divided by this to fit in 8 bits
  const lightmaps = {};
  for (const [name, p] of Object.entries(smallLight)) {
    lightmaps[name] = await p;
    lightmaps[name].channel = 1;               // lightmaps use the second set of UVs
  }
  const maps = {};
  const useMap = (file, t) => {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = Math.min(8, maxAniso);
    maps[file] = t;
  };
  for (const [file, p] of Object.entries(colourMaps)) useMap(file, await p);
  for (const m of Object.values(manifest.materials)) {
    if (!m.blend) continue;
    const mask = maps[m.blend.mask];
    mask.wrapS = mask.wrapT = THREE.ClampToEdgeWrapping;
    mask.channel = 1;
  }

  const water = {ripples: rippleTexture()};
  const flames = [];                           // the fire pit on the pool deck flickers a little
  const made = new Map();
  const bakedByAtlas = {};                     // atlas name -> materials, so the sharp lightmap can be swapped in later
  function materialFor(name, atlas) {
    const key = name + "|" + (atlas || "");
    if (made.has(key)) return made.get(key);
    const m = manifest.materials[name];
    let mat;
    if (!m) {
      mat = new THREE.MeshBasicMaterial({color: 0xff00ff});          // shows up loudly if a name is ever missing
    } else if (m.kind === "baked") {
      mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color().setRGB(...m.color), map: m.map ? maps[m.map] : null,
        roughness: m.rough ?? 0.85, metalness: m.metal ?? 0,
        lightMap: lightmaps[atlas], lightMapIntensity: lightScale * Math.PI,
        envMap: reflections, envMapIntensity: REFLECT[atlas] ?? (manifest.lightmaps[atlas]?.room ? INDOOR_REFLECT : 1),
      });
      if (m.blend) {
        mat.userData.uniforms = {};
        mat.onBeforeCompile = gravelShader({
          map: maps[m.blend.map], mask: maps[m.blend.mask], scale: m.tile / m.blend.tile,
          tint: new THREE.Vector3(...m.blend.color),
        }, mat.userData.uniforms);
        mat.customProgramCacheKey = () => "baked-gravel";
      } else {
        mat.onBeforeCompile = bakedShader;
        mat.customProgramCacheKey = () => "baked";
      }
      (bakedByAtlas[atlas] ||= []).push(mat);
    } else if (m.kind === "vertex") {
      // Light baked into the vertices, times a plain colour, times the model's
      // own picture if it has one (the furniture from Poly Haven does).
      mat = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setRGB(...m.color).multiplyScalar(lightScale), vertexColors: true,
        map: m.map ? maps[m.map] : null,
        side: m.doubleSided ? THREE.DoubleSide : THREE.FrontSide,
      });
    } else if (m.kind === "sheer") {
      // Thin curtain fabric: lit from outside, with the room's light showing through.
      mat = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setRGB(...m.color).multiplyScalar(lightScale), vertexColors: true,
        transparent: true, opacity: m.opacity, depthWrite: false, side: THREE.DoubleSide,
      });
    } else if (m.kind === "screen") {
      // A glowing picture (what's on a monitor), as bright as it is in Blender.
      mat = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setRGB(...m.color).multiplyScalar(m.strength ?? 1), map: m.map ? maps[m.map] : null,
      });
    } else if (m.kind === "glass" || m.kind === "water") {
      // Reflections are added at full strength while what is behind shows through dimmed, like real glass.
      mat = new THREE.MeshPhysicalMaterial({
        color: 0x000000, roughness: m.kind === "water" ? 0.06 : 0.02, metalness: 0, ior: m.kind === "water" ? 1.33 : 1.9,
        envMap: reflections, envMapIntensity: m.reflect ?? 1, transparent: true, opacity: m.opacity ?? 0.3, depthWrite: false,
        side: THREE.DoubleSide, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
      });
      if (m.kind === "water") {
        mat.envMap = probes[m.probe] ?? reflections;
        mat.normalMap = water.ripples;
        const r = m.ripple ?? 0.15;              // keep it gentle: stronger ripples tip the reflection up into the bright sky and sparkle
        mat.normalScale.set(r, r);
        mat.emissive.setRGB(...m.color).multiplyScalar(0.05);
        mat.opacity = 0.25;
      }
    } else if (m.kind === "emissive") {
      mat = new THREE.MeshBasicMaterial({color: new THREE.Color().setRGB(...m.color).multiplyScalar(m.strength * 0.4)});
      if (name === "flame") flames.push({mat, base: mat.color.clone()});
    } else {
      mat = new THREE.MeshBasicMaterial({color: new THREE.Color().setRGB(...m.color)});
    }
    if (!mat.onBeforeCompile || mat.onBeforeCompile === THREE.Material.prototype.onBeforeCompile) {
      mat.onBeforeCompile = addHaze;
      mat.customProgramCacheKey = () => "haze";
    }
    mat.name = name;
    made.set(key, mat);
    return mat;
  }

  // ---- sort the model's pieces into the groups the views switch on and off ----
  const groups = {ground: [], upper: [], roof: [], out: []};
  const info = o => { for (let p = o; p; p = p.parent) if (p.userData && p.userData.group) return p.userData; return {}; };
  const visibleNow = {};                       // filled in by the page, so late arrivals match the current view
  const carried = [];                          // things that travel with the camera (the visitor's hand at the pool)
  const byMaterial = new Map();                // material name -> meshes, for things you can click (the contact card)
  const hotspots = new Map();                  // anchor name -> its empty (blender/villa/geo.py, Builder.anchor), once its room is in
  function addModel(root) {
    root.traverse(o => {
      if (o.userData && o.userData.hotspot) hotspots.set(o.userData.hotspot, o);
      if (!o.isMesh) return;
      const {group, lightmap, attach} = info(o);
      o.material = materialFor(o.material.name, lightmap);
      if (!byMaterial.has(o.material.name)) byMaterial.set(o.material.name, []);
      byMaterial.get(o.material.name).push(o);
      // The export leaves normals out to save space. Anything that reflects needs them back.
      if (!o.geometry.attributes.normal && !o.material.isMeshBasicMaterial) o.geometry.computeVertexNormals();
      // see-through things draw last, curtains before the glass in front of them
      if (o.material.transparent) o.renderOrder = o.material.name === "sheer" ? 1 : 2;
      if (attach === "camera") { o.visible = false; carried.push(o); return; }
      const g = groups[group] ? group : "out";
      groups[g].push(o);
      if (g in visibleNow) o.visible = visibleNow[g];
    });
    scene.add(root);
  }

  // The visitor's hand and drink were modelled in place for the pool's camera
  // moment. To carry them with the camera, each is re-hung on the camera with its
  // position relative to that moment's camera, so it stays at the bottom of the
  // frame wherever the visitor looks.
  const moment = new THREE.PerspectiveCamera();
  let carriedReady = false;
  // frame (optional): {x, y} moves them across and up or down the view by those factors, for a
  // frame of another shape than the 16:9 they were modelled for (main.js, an upright phone)
  function carry(camera, on, frame = null) {
    if (on && !carriedReady && carried.length && manifest.cameras.pool_moment) {
      const c = manifest.cameras.pool_moment;
      moment.position.set(...c.pos);
      moment.lookAt(...c.target);
      moment.updateMatrixWorld(true);
      const toCamera = moment.matrixWorld.clone().invert();
      for (const o of carried) {
        o.updateMatrixWorld(true);
        const local = toCamera.clone().multiply(o.matrixWorld);
        camera.add(o);
        local.decompose(o.position, o.quaternion, o.scale);
        o.userData.home = o.position.clone();
        // where the object's middle sits in the camera's frame, which is what `frame` moves
        o.geometry.computeBoundingBox();
        o.userData.middle = o.geometry.boundingBox.getCenter(new THREE.Vector3()).applyMatrix4(local);
      }
      carriedReady = true;
    }
    for (const o of carried) {
      o.visible = on && carriedReady;
      if (carriedReady) {
        const {home, middle} = o.userData;
        o.position.set(home.x + middle.x * ((frame ? frame.x : 1) - 1), home.y + middle.y * ((frame ? frame.y : 1) - 1), home.z);
      }
    }
  }
  addModel(gltf.scene);

  // ---- the sharp lightmaps, all four at once ----
  async function loadSharpLight() {
    await Promise.all(Object.entries(manifest.lightmaps).filter(([, lm]) => !lm.room).map(async ([name, lm]) => {
      try {
        const tex = await fetchTracked(ktx2, lm.file);
        tex.channel = 1;
        const old = lightmaps[name];
        for (const mat of bakedByAtlas[name] || []) mat.lightMap = tex;
        lightmaps[name] = tex;
        old.dispose();
      } catch (e) { console.warn("Could not load the sharp lightmap for", name, e); }
    }));
  }
  // ---- the full-size copy of a picture that loaded small first ----
  async function loadSharpMap(file) {
    try {
      const tex = await ktx2.loadAsync(ASSETS + file);
      const old = maps[file];
      useMap(file, tex);
      for (const mat of made.values()) {
        if (mat.map === old) mat.map = tex;
        const u = mat.userData.uniforms;
        if (u && u.uGravelMap.value === old) u.uGravelMap.value = tex;
      }
      old.dispose();
    } catch (e) { console.warn("Could not load the full-size", file, e); }
  }

  // ---- the furnished rooms: pictures, lightmap, furniture ----
  async function loadRoom(name) {
    const room = manifest.rooms[name];
    const files = new Set(Object.values(manifest.materials).filter(m => m.room === name && m.map).map(m => m.map));
    const atlases = Object.entries(manifest.lightmaps).filter(([, lm]) => lm.room === name);
    // a figure seated in the room (see blender/villa/figure.py), if the manifest lists one
    const figures = Object.values(manifest.figures || {}).filter(f => f.room === name);
    const [roomGltf, pictures, light, figureGltfs] = await Promise.all([
      gltfLoader.loadAsync(ASSETS + room.model),
      Promise.all([...files].map(f => ktx2.loadAsync(ASSETS + f).then(t => [f, t]))),
      Promise.all(atlases.map(([a, lm]) => ktx2.loadAsync(ASSETS + lm.file).then(t => [a, t]))),
      Promise.all(figures.map(f => gltfLoader.loadAsync(ASSETS + f.model))),
    ]);
    for (const [f, t] of pictures) useMap(f, t);
    for (const [a, t] of light) { t.channel = 1; lightmaps[a] = t; }
    addModel(roomGltf.scene);
    for (const g of figureGltfs) addModel(g.scene);
  }
  // ---- the queue ----
  // One job per room, plus one for the sharp lightmaps and one for the full-size pictures.
  // Each settles once its files are in (or have failed to load). Two run at a time.
  const jobs = new Map();                       // key -> {run, done, promise, started}
  const job = (key, run) => {
    let done; const promise = new Promise(r => { done = r; });
    jobs.set(key, {run, done, promise, started: false});
    return promise;
  };
  const sharp = job("light", loadSharpLight);
  // one job per full-size picture, so none holds up a room the visitor opens for long
  const sharpMaps = Promise.all(Object.keys(smallMaps).filter(f => maps[f]).map(f => job("map:" + f, () => loadSharpMap(f))));
  const roomNames = Object.keys(manifest.rooms || {});
  const roomReady = {};
  for (const name of roomNames) roomReady[name] = job("room:" + name, () => loadRoom(name).catch(e => console.warn("Could not load the", name, "furniture", e)));
  let wanted = null, likely = [];                // the room opened, and rooms likely to be opened next
  const saveData = Boolean(navigator.connection && navigator.connection.saveData);
  const waiting = key => { const j = jobs.get(key); return j && !j.started ? key : null; };
  const mapJobs = [...jobs.keys()].filter(k => k.startsWith("map:"));
  function next() {
    // the room the visitor opened has the connection to itself: after the full bake the
    // sharp lightmaps are 12 MB, and sharing with them doubled a room's wait
    const open = wanted && jobs.get("room:" + wanted);
    if (open && open.started && !open.finished) return null;
    return (wanted && waiting("room:" + wanted)) || waiting("light") ||
      likely.map(n => waiting("room:" + n)).find(Boolean) || mapJobs.map(waiting).find(Boolean) ||
      (saveData ? null : roomNames.map(n => waiting("room:" + n)).find(Boolean));
  }
  const sleepers = [];
  async function worker() {
    for (;;) {
      const key = next();
      if (!key) {                                 // nothing to do now; a hover or an opened room may add some
        if ([...jobs.values()].every(j => j.started)) return;
        await new Promise(r => sleepers.push(r));
        continue;
      }
      const j = jobs.get(key); j.started = true;
      try { await j.run(); } catch (e) { console.warn("Could not load", key, e); } finally { j.finished = true; j.done(); poke(); }
    }
  }
  const poke = () => { for (const wake of sleepers.splice(0)) wake(); };
  // (started a moment later, so a room opened on the still is first in line)
  setTimeout(() => { worker(); worker(); }, 0);
  const rooms = Promise.all(Object.values(roomReady));
  Promise.all([rooms, sharp, sharpMaps]).then(() => ktx2.dispose());

  // ---- the living room's moodboard ----
  // Its frames (materials marked "moodboard" in the manifest, each with its picture's
  // shape) show pictures listed in assets/moodboard/moodboard.json (npm run moodboard),
  // a fresh random pick each time the room is opened. Nothing is fetched before that.
  // With no pictures listed, the frames stay the plain colour fields they were built with.
  const frames = Object.entries(manifest.materials).filter(([, m]) => m.moodboard)
    .map(([name, m]) => ({name, room: m.room, aspect: m.moodboard}));
  const imageLoader = new THREE.TextureLoader();
  const pictureTex = new Map();
  let pictureList = null, shuffles = 0;
  async function shuffleMoodboard(room) {
    const mine = frames.filter(f => f.room === room);
    if (!mine.length) return;
    const turn = ++shuffles;
    pictureList ||= fetch(ASSETS + "moodboard/moodboard.json")
      .then(r => (r.ok ? r.json() : {images: []}))
      .then(j => j.images || [], () => []);
    const [images] = await Promise.all([pictureList, roomReady[room]]);
    if (!images.length || turn !== shuffles) return;
    // shuffle the pictures, then give each frame (in random order) whichever of the
    // next few is closest to its shape, so few get cropped hard
    const pool = images.slice();
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]];
    }
    const misfit = (img, f) => Math.abs(Math.log(img.w / img.h / f.aspect));
    const picks = mine.map(f => [Math.random(), f]).sort((a, b) => a[0] - b[0]).map(([, f]) => {
      if (!pool.length) return [f, null];
      const best = pool.slice(0, 3).reduce((a, b) => (misfit(b, f) < misfit(a, f) ? b : a));
      pool.splice(pool.indexOf(best), 1);
      return [f, best];
    });
    await Promise.all(picks.map(async ([f, img]) => {
      const mat = (byMaterial.get(f.name) || [])[0]?.material;
      if (!mat) return;
      mat.userData.base ||= mat.color.clone();
      let tex = null;
      if (img) {
        if (!pictureTex.has(img.file)) {
          pictureTex.set(img.file, imageLoader.loadAsync(ASSETS + img.file).then(t => {
            t.colorSpace = THREE.SRGBColorSpace;
            t.flipY = false;                       // the frames' UVs come from glTF, which counts v from the top
            t.anisotropy = Math.min(8, maxAniso);
            return t;
          }, () => null));
        }
        tex = await pictureTex.get(img.file);
      }
      if (turn !== shuffles) return;             // opened again meanwhile; the newer pick wins
      if (!tex) {
        if (mat.map) { mat.map = null; mat.color.copy(mat.userData.base); mat.needsUpdate = true; }
        return;
      }
      // crop the picture to fill the frame, keeping its middle
      const a = img.w / img.h;
      if (a > f.aspect) { tex.repeat.set(f.aspect / a, 1); tex.offset.set((1 - f.aspect / a) / 2, 0); }
      else { tex.repeat.set(1, a / f.aspect); tex.offset.set(0, (1 - a / f.aspect) / 2); }
      if (!mat.map) mat.needsUpdate = true;
      mat.map = tex;
      mat.color.setScalar(lightScale);            // the picture's own colours, times the baked light
    }));
  }

  return {
    manifest, groups, sharp, sharpMaps, rooms,
    // The page says which groups are showing, so furniture that arrives later matches.
    setVisible(group, on) { visibleNow[group] = on; groups[group].forEach(o => { o.visible = on; }); },
    carry,
    hasCarried: () => carried.length > 0,
    // A hotspot anchor's world position (manifest.hotspots lists them all, loaded or not).
    hotspot(name) {
      const o = hotspots.get(name);
      if (o) return o.getWorldPosition(new THREE.Vector3());
      const h = manifest.hotspots && manifest.hotspots[name];
      return h ? new THREE.Vector3(...h.pos) : null;
    },
    // The visitor opened this room: load its furniture next, and pick its moodboard's pictures.
    openRoom(name) {
      if (roomReady[name]) { wanted = name; poke(); }
      return shuffleMoodboard(name);
    },
    // Rooms the visitor is likely to open next (a hovered label, the open room's neighbours):
    // they load before the rest. The newest hint goes first.
    prefetch(names) {
      const known = names.filter(n => roomReady[n]);
      if (!known.length) return;
      likely = [...known, ...likely.filter(n => !known.includes(n))].slice(0, 8);
      poke();
    },
    // settles once a room's furniture is in (at once for a name that isn't a furnished room)
    roomReady: name => roomReady[name] || Promise.resolve(),
    // every mesh drawn with any of these materials (empty until its room has loaded)
    meshesWith: names => names.flatMap(n => byMaterial.get(n) || []),
    update(seconds) {
      water.ripples.offset.set(seconds * 0.012, seconds * 0.02);
      const f = 0.86 + 0.08 * Math.sin(seconds * 9.1) + 0.06 * Math.sin(seconds * 23.7 + 1.3);
      for (const {mat, base} of flames) mat.color.copy(base).multiplyScalar(f);
    },
  };
}
