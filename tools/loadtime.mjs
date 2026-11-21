// Measures a cold load of the site in headless Chrome on a throttled connection, the way
// DevTools' "Fast 4G" preset throttles it (9 Mbit/s down x 0.9, 1.5 up, 165 ms latency),
// with the cache off.
//
//   npm run loadtime                       the site in web/, served locally
//   npm run loadtime -- https://...        any other copy (the live site, say)
//   npm run loadtime -- --phone            as a 390 x 844 phone (3x) instead of a 1920 x 1080 desktop
//   npm run loadtime -- --runs 3           repeat and report each run
//
// It reports, from the start of navigation:
//   still   the landing still has loaded (the first picture of the house)
//   ui      the page's script is running: labels, panels and the Rooms menu work
//   world   the 3D house is built and drawing under the still
//   3d      the still starts to fade and the live 3D takes over
// and the megabytes downloaded by then. The page marks these itself (performance.mark);
// for an older copy without the marks, "3d" is when its loading screen went away.

import {launch, serveWeb, waitFor} from "./cdp.mjs";

const args = process.argv.slice(2);
const phone = args.includes("--phone");
const runs = Number(args[args.indexOf("--runs") + 1]) || 1;
const target = args.find(a => /^https?:\/\//.test(a));

const FAST_4G = {offline: false, latency: 60 * 2.75, downloadThroughput: 9e6 / 8 * 0.9, uploadThroughput: 1.5e6 / 8 * 0.9, connectionType: "cellular4g"};

const server = target ? null : await serveWeb();
const url = target || server.url;
console.log(`Loading ${url} on throttled Fast 4G, ${phone ? "phone 390x844 @3x" : "desktop 1920x1080"}, cache off`);

for (let run = 1; run <= runs; run++) {
  const page = await launch({width: phone ? 390 : 1920, height: phone ? 844 : 1080});
  await page.send("Network.enable");
  await page.send("Network.setCacheDisabled", {cacheDisabled: true});
  await page.send("Network.emulateNetworkConditions", FAST_4G);
  if (phone) {
    await page.send("Emulation.setDeviceMetricsOverride", {width: 390, height: 844, deviceScaleFactor: 3, mobile: true});
    await page.send("Emulation.setTouchEmulationEnabled", {enabled: true, maxTouchPoints: 5});
  }
  let bytes = 0;
  page.on("Network.loadingFinished", p => { bytes += p.encodedDataLength; });

  await page.send("Page.navigate", {url});
  const seen = {};
  const probe = `(() => {
    const m = {}; for (const e of performance.getEntriesByType("mark")) m[e.name] = e.startTime;
    return {m, ready: document.body && document.body.dataset.ready, now: performance.now()};
  })()`;
  const t0 = Date.now();
  for (;;) {
    let s = null;
    try { s = await page.evaluate(probe); } catch {}
    if (s) {
      for (const [k, v] of Object.entries(s.m)) if (!(k in seen)) seen[k] = {t: v, mb: bytes / 1e6};
      // an older copy of the site, without marks: its loading screen goes when ready is "yes"
      if (s.ready === "yes" && !("3d" in seen) && !("ui" in s.m)) seen["3d"] = {t: s.now, mb: bytes / 1e6, approx: true};
      if ("3d" in seen) break;
    }
    if (Date.now() - t0 > 240000) { console.log("  gave up after 240 s"); break; }
    await new Promise(r => setTimeout(r, 50));
  }
  const fmt = k => seen[k] ? `${(seen[k].t / 1000).toFixed(2)} s${seen[k].approx ? " (approx.)" : ""}, ${seen[k].mb.toFixed(1)} MB` : "-";
  console.log(`run ${run}:  still ${fmt("still")}   ui ${fmt("ui")}   world ${fmt("world")}   3d ${fmt("3d")}`);
  await page.close();
}
if (server) await server.close();
