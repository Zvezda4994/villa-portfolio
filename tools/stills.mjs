// Makes the stills the site shows while its 3D loads (web/assets/stills/) and the link
// preview (web/og.jpg), by drawing them with the site's own renderer in headless Chrome.
// Run it after anything that changes how the house looks (a bake, an export):
//
//   npm run stills                 the landing shot, every stop and the link preview
//   npm run stills -- landing pool just those
//
// Drawn from the same cameras and the same code as the 3D, a still matches the 3D that
// fades in over it exactly. See web/src/still.js for its shape and sizes.

import {existsSync, mkdirSync, readFileSync, writeFileSync} from "node:fs";
import {join} from "node:path";
import {pathToFileURL} from "node:url";
import {WEB, launch, serveWeb, waitFor} from "./cdp.mjs";

const {ROOMS} = await import(pathToFileURL(join(WEB, "src", "rooms.js")).href);
const {SIZES} = await import(pathToFileURL(join(WEB, "src", "still.js")).href);

const asked = process.argv.slice(2).filter(a => !a.startsWith("--"));
const ids = asked.length ? asked : ["landing", ...ROOMS.map(r => r.id)];
const out = join(WEB, "assets", "stills");
mkdirSync(out, {recursive: true});

const server = await serveWeb();
const page = await launch({width: 1600, height: 900});
page.on("Runtime.consoleAPICalled", e => { if (e.type === "error" || e.type === "warning") console.log("  [page]", e.args.map(a => a.value ?? a.description).join(" ")); });
await page.send("Page.navigate", {url: server.url + "?capture=1"});
await waitFor(page, "typeof window.capture === 'function'", {timeout: 180000});

// tiny copies of every still, inlined in one file the page fetches as it starts
const thumbsFile = join(out, "thumbs.json");
const thumbs = existsSync(thumbsFile) ? JSON.parse(readFileSync(thumbsFile, "utf8")) : {};
let total = 0;
for (const id of ids) {
  const t0 = Date.now();
  const landing = id === "landing";
  const sizes = landing ? SIZES.landing : SIZES.room;
  // the largest wide still sets the drawing's height (it's drawn at twice that)
  const height = Math.round(Math.max(...sizes.wide) / 2.4);
  const files = await page.evaluate(`capture(${JSON.stringify(id)}, {height: ${height}, quality: ${landing ? 0.82 : 0.78}, og: ${landing}})`);
  const report = [];
  thumbs[id] = files.thumb; delete files.thumb;
  for (const [name, url] of Object.entries(files)) {
    const bytes = Buffer.from(url.slice(url.indexOf(",") + 1), "base64");
    writeFileSync(name === "og.jpg" ? join(WEB, "og.jpg") : join(out, name), bytes);
    report.push(`${name} ${(bytes.length / 1e3).toFixed(0)} KB`);
    total += bytes.length;
  }
  console.log(`[stills] ${id} (${((Date.now() - t0) / 1000).toFixed(1)} s): ${report.join(", ")}`);
}
writeFileSync(thumbsFile, JSON.stringify(thumbs));
console.log(`[stills] ${(total / 1e6).toFixed(1)} MB in all; thumbs.json ${(readFileSync(thumbsFile).length / 1e3).toFixed(0)} KB`);
await page.close();
await server.close();
