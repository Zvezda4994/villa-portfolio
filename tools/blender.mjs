// Runs one of the Blender scripts in blender/ without opening Blender's window.
//
//   node tools/blender.mjs build_scene
//   node tools/blender.mjs render_previews --draft landing
//
// It looks for Blender in the BLENDER environment variable first, then in the
// usual install places. Anything after the script name is passed on to the script.

import {spawnSync} from "node:child_process";
import {existsSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const candidates = [
  process.env.BLENDER,
  "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe",
  "C:/Program Files/Blender Foundation/Blender/blender.exe",
  "/Applications/Blender.app/Contents/MacOS/Blender",
  "/usr/bin/blender",
].filter(Boolean);
const blender = candidates.find(p => existsSync(p));
if (!blender) {
  console.error("Could not find Blender. Set the BLENDER environment variable to the full path of blender.exe.");
  process.exit(1);
}

const [script, ...rest] = process.argv.slice(2);
if (!script) {
  console.error("Usage: node tools/blender.mjs <script name> [options]");
  process.exit(1);
}
const file = join(root, "blender", script.endsWith(".py") ? script : script + ".py");
const args = ["--background", "--factory-startup", "--python", file];
if (rest.length) args.push("--", ...rest);
const result = spawnSync(blender, args, {stdio: "inherit", cwd: root});
process.exit(result.status ?? 1);
