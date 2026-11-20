// Makes the site's Download PDF: prints web/resume.html (drawn from web/resume.json)
// to web/assets/resume.pdf with headless Chrome, so the PDF always matches the
// resume on the site, phone number left off.
//
//   npm run resume:pdf
//
// It serves web/ itself for the moment it takes, on a free port. Chrome is looked for
// in the CHROME environment variable first, then in the usual install places.

import {spawn} from "node:child_process";
import {createServer} from "node:http";
import {existsSync, readFileSync, statSync} from "node:fs";
import {dirname, extname, join, normalize} from "node:path";
import {fileURLToPath} from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const web = join(root, "web");
const out = join(web, "assets", "resume.pdf");

const chrome = [
  process.env.CHROME,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
].filter(Boolean).find(p => existsSync(p));
if (!chrome) {
  console.error("Could not find Chrome. Set the CHROME environment variable to its full path.");
  process.exit(1);
}

const types = {".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".css": "text/css"};
const server = createServer((req, res) => {
  const path = normalize(join(web, decodeURIComponent(new URL(req.url, "http://x").pathname)));
  if (!path.startsWith(web) || !existsSync(path) || !statSync(path).isFile()) { res.writeHead(404).end(); return; }
  res.writeHead(200, {"content-type": types[extname(path)] || "application/octet-stream"}).end(readFileSync(path));
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const url = `http://127.0.0.1:${server.address().port}/resume.html`;

const before = existsSync(out) ? statSync(out).mtimeMs : 0;
// (spawned, not run synchronously: this process has to keep serving while Chrome prints)
const code = await new Promise(r => {
  const p = spawn(chrome, ["--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
    `--user-data-dir=${join(root, "build", "chrome-pdf")}`, `--print-to-pdf=${out}`, url], {stdio: "ignore"});
  p.on("exit", r);
});
server.close();
if (code !== 0 || !existsSync(out) || statSync(out).mtimeMs === before) {
  console.error(`Chrome could not print the resume (exit ${code}).`);
  process.exit(1);
}
console.log(`[resume] ${out} (${(statSync(out).size / 1024).toFixed(0)} KB)`);
