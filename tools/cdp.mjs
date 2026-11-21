// A small driver for headless Chrome over the DevTools protocol, shared by the tools
// that need a real browser (tools/stills.mjs, tools/loadtime.mjs). No dependencies:
// Node's own fetch and WebSocket.
//
// Also a static server for web/, on a free port, for the tools that need the site
// served locally. It sends no caching headers, so each run is a cold load.

import {spawn} from "node:child_process";
import {createServer} from "node:http";
import {existsSync, mkdtempSync, readFileSync, rmSync, statSync} from "node:fs";
import {tmpdir} from "node:os";
import {dirname, extname, join, normalize} from "node:path";
import {fileURLToPath} from "node:url";

export const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
export const WEB = join(ROOT, "web");

export function findChrome() {
  const chrome = [
    process.env.CHROME,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
  ].filter(Boolean).find(p => existsSync(p));
  if (!chrome) throw new Error("Could not find Chrome. Set the CHROME environment variable to its full path.");
  return chrome;
}

const TYPES = {".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".css": "text/css",
  ".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf"};

// Serves web/ on 127.0.0.1. Returns {url, close}.
export async function serveWeb() {
  const server = createServer((req, res) => {
    const path = normalize(join(WEB, decodeURIComponent(new URL(req.url, "http://x").pathname)));
    const file = path.endsWith("\\") || path.endsWith("/") ? join(path, "index.html") : path;
    if (!file.startsWith(WEB) || !existsSync(file) || !statSync(file).isFile()) { res.writeHead(404).end(); return; }
    const body = readFileSync(file);
    res.writeHead(200, {"content-type": TYPES[extname(file)] || "application/octet-stream", "content-length": body.length, "cache-control": "no-store"}).end(body);
  });
  await new Promise(r => server.listen(0, "127.0.0.1", r));
  return {url: `http://127.0.0.1:${server.address().port}/`, close: () => new Promise(r => server.close(r))};
}

// Starts Chrome (headless, on the real GPU) with a fresh profile and connects to its
// first tab. Returns {send, on, evaluate, close}.
export async function launch({width = 1920, height = 1080, headless = true} = {}) {
  const profile = mkdtempSync(join(tmpdir(), "villa-chrome-"));
  const args = [`--user-data-dir=${profile}`, "--remote-debugging-port=0", "--no-first-run", "--no-default-browser-check",
    "--enable-gpu", "--use-angle=d3d11", "--ignore-gpu-blocklist", `--window-size=${width},${height}`, "--hide-scrollbars", "about:blank"];
  if (headless) args.unshift("--headless=new");
  const proc = spawn(findChrome(), args, {stdio: "ignore"});
  // Chrome writes the port it picked into the profile
  const portFile = join(profile, "DevToolsActivePort");
  let port = null;
  for (let i = 0; i < 200 && !port; i++) {
    if (existsSync(portFile)) port = Number(readFileSync(portFile, "utf8").split("\n")[0]) || null;
    if (!port) await new Promise(r => setTimeout(r, 50));
  }
  if (!port) { proc.kill(); throw new Error("Chrome did not start its debugging port"); }
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const tab = tabs.find(t => t.type === "page");
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = fail; });
  let id = 0;
  const waiting = new Map(), listeners = new Map();
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && waiting.has(msg.id)) {
      const {ok, fail} = waiting.get(msg.id); waiting.delete(msg.id);
      msg.error ? fail(new Error(msg.error.message)) : ok(msg.result);
    } else if (msg.method) for (const f of listeners.get(msg.method) || []) f(msg.params);
  };
  const send = (method, params = {}) => new Promise((ok, fail) => { const n = ++id; waiting.set(n, {ok, fail}); ws.send(JSON.stringify({id: n, method, params})); });
  const on = (method, f) => { if (!listeners.has(method)) listeners.set(method, []); listeners.get(method).push(f); };
  // runs an expression in the page (awaiting it if it's a promise) and returns its value
  const evaluate = async expression => {
    const r = await send("Runtime.evaluate", {expression, awaitPromise: true, returnByValue: true});
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  const close = async () => {
    try { await send("Browser.close"); } catch { proc.kill(); }
    await new Promise(r => setTimeout(r, 300));
    try { rmSync(profile, {recursive: true, force: true}); } catch {}
  };
  await send("Page.enable"); await send("Runtime.enable");
  return {send, on, evaluate, close};
}

// Waits until `expression` is truthy in the page, checking every `every` ms.
export async function waitFor(page, expression, {timeout = 120000, every = 100} = {}) {
  const t0 = Date.now();
  for (;;) {
    let v = null;
    try { v = await page.evaluate(expression); } catch {}
    if (v) return v;
    if (Date.now() - t0 > timeout) throw new Error(`timed out waiting for ${expression}`);
    await new Promise(r => setTimeout(r, every));
  }
}
