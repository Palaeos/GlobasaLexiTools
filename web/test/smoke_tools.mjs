// Smoke test: each wasm tool on a real compiled file, compared with the native tool.
//   node web/test/smoke_tools.mjs
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { readdirSync, existsSync } from "node:fs";
import { initTools, runTool, setIcuData } from "../src/tools.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(here, "..", "dist", "wasm");
await initTools(path.join(dist, "apertium.wasm"), path.join(dist, "apertium.mjs"));
// ICU_FULL=<dir of icupkg -x items>: mount every item and report the ones opened
const opened = new Set();
if (process.env.ICU_FULL) {
  const m = new Map();
  for (const n of readdirSync(process.env.ICU_FULL, { recursive: true })) {
    const p = path.join(process.env.ICU_FULL, n);
    if (!n.endsWith("/") && existsSync(p) && !readdirSync(path.dirname(p)).includes(n + "/")) {
      try { m.set(n, readFileSync(p)); } catch { /* directory */ }
    }
  }
  setIcuData(m, (p) => opened.add(p.replace("/icu/icudt68l/", "")));
} else if (existsSync(path.join(dist, "icudt68l.dat"))) {
  setIcuData(readFileSync(path.join(dist, "icudt68l.dat")));
}

const P = path.resolve(here, "../../GlobasaTranslation/apertium-glb-eng");
const files = new Map();
const f = (name) => { const p = path.join(P, name); files.set(p, readFileSync(p)); return p; };

let input = "The old man saw that the queer thing was in the garden.\n";
const steps = [
  ["lt-proc", ["-w", f("eng.automorf.bin")]],
  ["cg-proc", ["-w", f("eng-glb.rlx.bin")]],
  ["apertium-tagger", ["-g", f("eng-glb.prob")]],
  ["lsx-proc", [f("eng-glb.autoseq.bin")]],
  ["apertium-pretransfer", []],
  ["lt-proc", ["-b", f("eng-glb.autobil.bin")]],
  ["cg-proc", [f("eng-glb.biprefs.rlx.bin")]],
  ["lrx-proc", ["-m", f("eng-glb.autolex.bin")]],
  ["apertium-anaphora", [f("apertium-glb-eng.eng-glb.arx")]],
  ["rtx-proc", ["-a", f("eng-glb.rtx.bin")]],
  ["lsx-proc", [f("eng-glb.revautoseq.bin")]],
  ["lt-proc", ["-g", f("eng-glb.autogen.bin")]],
  ["lt-proc", ["-p", f("eng-glb.autopgen.bin")]],
];
let fail = 0;
for (const [tool, args] of steps) {
  const t0 = performance.now();
  const w = await runTool(tool, args, input, files);
  const ms = (performance.now() - t0).toFixed(0);
  const n = execFileSync(tool, args, { input, encoding: "utf8" });
  const ok = w.stdout === n;
  if (!ok) fail++;
  console.log(`${ok ? "ok  " : "DIFF"} ${tool} ${args[0] ?? ""} ${ms} ms${w.stderr ? "  stderr: " + w.stderr.slice(0, 200) : ""}`);
  if (!ok) { console.log("  wasm:  ", JSON.stringify(w.stdout.slice(0, 300))); console.log("  native:", JSON.stringify(n.slice(0, 300))); }
  input = n;      // keep following the native stream
}
console.log(fail ? `${fail} step(s) differ` : "all steps identical");
console.log("output:", input.trim());
if (opened.size) console.log("ICU items opened:", [...opened].sort().join(" "));
process.exit(fail ? 1 : 0);
