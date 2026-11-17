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
// mostly hidden by ceilings, so reflections there are turned well down.
const REFLECT = {ext: 1.0, terrain: 1.0, gnd: 0.3, upr: 0.3};

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
function gravelShader(blend) {
  return shader => {
    bakedShader(shader);
    Object.assign(shader.uniforms, {
      uGravelMap: {value: blend.map}, uGravelMask: {value: blend.mask},
      uGravelScale: {value: blend.scale}, uGravelTint: {value: blend.tint},
    });
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

export async function loadWorld(renderer, scene, onProgress = () => {}) {
  const manifest = await (await fetch(ASSETS + "manifest.json")).json();
  const ktx2 = new KTX2Loader().setTranscoderPath(TRANSCODER).detectSupport(renderer);
  const gltfLoader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const hdr = new RGBELoader();
  const maxAniso = renderer.capabilities.getMaxAnisotropy();

  let done = 0, total = 0;
  const track = promise => { total++; return promise.then(v => { onProgress(++done, total); return v; }); };

  // ---- start every download needed for the first view at once ----
  const colourMaps = {};
  const want = file => { if (file && !colourMaps[file]) colourMaps[file] = track(ktx2.loadAsync(ASSETS + file)); };
  for (const m of Object.values(manifest.materials)) {
    want(m.map);
    if (m.blend) { want(m.blend.map); want(m.blend.mask); }
  }
  const smallLight = {};
  for (const [name, lm] of Object.entries(manifest.lightmaps)) smallLight[name] = track(ktx2.loadAsync(ASSETS + lm.small));
  // Panoramas taken from above each body of water, so it reflects what is really around it.
  const probeNames = Object.keys(manifest.sky).filter(k => k !== "background" && k !== "environment");
  const [gltf, skyTex, envTex, ...probeTex] = await Promise.all([
    track(gltfLoader.loadAsync(ASSETS + manifest.model)),
    track(hdr.loadAsync(ASSETS + manifest.sky.background)),
    track(hdr.loadAsync(ASSETS + manifest.sky.environment)),
    ...probeNames.map(k => track(hdr.loadAsync(ASSETS + manifest.sky[k]))),
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
  for (const [file, p] of Object.entries(colourMaps)) {
    const t = await p;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = Math.min(8, maxAniso);
    maps[file] = t;
  }
  for (const m of Object.values(manifest.materials)) {
    if (!m.blend) continue;
    const mask = maps[m.blend.mask];
    mask.wrapS = mask.wrapT = THREE.ClampToEdgeWrapping;
    mask.channel = 1;
  }

  const water = {ripples: rippleTexture()};
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
        envMap: reflections, envMapIntensity: REFLECT[atlas] ?? 1,
      });
      if (m.blend) {
        mat.onBeforeCompile = gravelShader({
          map: maps[m.blend.map], mask: maps[m.blend.mask], scale: m.tile / m.blend.tile,
          tint: new THREE.Vector3(...m.blend.color),
        });
        mat.customProgramCacheKey = () => "baked-gravel";
      } else {
        mat.onBeforeCompile = bakedShader;
        mat.customProgramCacheKey = () => "baked";
      }
      (bakedByAtlas[atlas] ||= []).push(mat);
    } else if (m.kind === "vertex") {
      mat = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setRGB(...m.color).multiplyScalar(lightScale), vertexColors: true,
        side: m.doubleSided ? THREE.DoubleSide : THREE.FrontSide,
      });
    } else if (m.kind === "sheer") {
      // Thin curtain fabric: lit from outside, with the room's light showing through.
      mat = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setRGB(...m.color).multiplyScalar(lightScale), vertexColors: true,
        transparent: true, opacity: m.opacity, depthWrite: false, side: THREE.DoubleSide,
      });
    } else if (m.kind === "glass" || m.kind === "water") {
      // Reflections are added at full strength while what is behind shows through dimmed, like real glass.
      mat = new THREE.MeshPhysicalMaterial({
        color: 0x000000, roughness: m.kind === "water" ? 0.06 : 0.02, metalness: 0, ior: m.kind === "water" ? 1.33 : 1.9,
        envMap: reflections, envMapIntensity: 1, transparent: true, opacity: m.opacity ?? 0.3, depthWrite: false,
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
  gltf.scene.traverse(o => {
    if (!o.isMesh) return;
    const {group, lightmap} = info(o);
    o.material = materialFor(o.material.name, lightmap);
    // The export leaves normals out to save space. Anything that reflects needs them back.
    if (!o.geometry.attributes.normal && !o.material.isMeshBasicMaterial) o.geometry.computeVertexNormals();
    // see-through things draw last, curtains before the glass in front of them
    if (o.material.transparent) o.renderOrder = o.material.name === "sheer" ? 1 : 2;
    (groups[group] || groups.out).push(o);
  });
  scene.add(gltf.scene);

  // ---- then fetch the sharp lightmaps in the background, outdoors first ----
  const sharp = (async () => {
    for (const name of ["ext", "terrain", "gnd", "upr"]) {
      const lm = manifest.lightmaps[name];
      if (!lm) continue;
      try {
        const tex = await ktx2.loadAsync(ASSETS + lm.file);
        tex.channel = 1;
        const old = lightmaps[name];
        for (const mat of bakedByAtlas[name] || []) mat.lightMap = tex;
        lightmaps[name] = tex;
        old.dispose();
      } catch (e) { console.warn("Could not load the sharp lightmap for", name, e); }
    }
    ktx2.dispose();
  })();

  return {
    manifest, groups, sharp,
    update(seconds) { water.ripples.offset.set(seconds * 0.012, seconds * 0.02); },
  };
}
