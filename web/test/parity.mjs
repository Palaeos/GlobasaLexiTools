// Parity: every mode in web/dist/pairs/index.json, run in wasm + Pyodide and natively
// (the apertium command: apertium -d <pair> <mode>), on the same text: the output must
// be identical.
// The native run gets the same switches the browser sets (GLB_NEURAL=0, ENG_GLB_NEURAL=0,
// FRA_GLB_NEURAL=0), so the comparison is of the rule-based pipelines.
//
//   node web/test/parity.mjs [mode ...]
//   PARITY_N=40          lines per mode (from parallel_gold_cache/<lang>/*.tsv)
//   PARITY_SETVAR=story  AP_SETVAR for both runs
//   PARITY_TEXT="..."    translate this text (lines) instead of the gold sample
//   PARITY_NATIVE_GB=4   address-space cap (ulimit -v) for each native pipeline run
//   Run the whole test through web/test/capped.py (npm test does): it caps the summed
//   memory of Node, wasm, Pyodide and the native tools at GLOBASA_MEM_GB.
//   ICU_FULL=<dir>       mount every ICU item (icupkg -x '*') and list the ones opened,
//                        to update web/wasm/icu_items.txt
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadPyodide } from "pyodide";
import { Translator } from "../src/pipeline.mjs";
import { setIcuData } from "../src/tools.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, "..");
const repo = path.join(web, "..");
const dist = path.join(web, "dist");
const N = Number(process.env.PARITY_N || 40);
const tmp = mkdtempSync(path.join(tmpdir(), "glb-parity-"));
const SETVAR = process.env.PARITY_SETVAR || "";
const NATIVE_KB = Math.round(Number(process.env.PARITY_NATIVE_GB || 4) * 1024 * 1024);
// every native pipeline runs under ulimit -v, so a blow-up (rtx-proc) fails, never swaps
const capped = (cmd) => `ulimit -v ${NATIVE_KB}; ${cmd}`;
const NEURAL_OFF = { GLB_NEURAL: "0", ENG_GLB_NEURAL: "0", FRA_GLB_NEURAL: "0" };

const index = JSON.parse(readFileSync(path.join(dist, "pairs", "index.json"), "utf8"));
const only = process.argv.slice(2);
const modes = index.modes.filter((m) => !only.length || only.includes(m.mode));

function sample(m) {
  if (process.env.PARITY_TEXT) return process.env.PARITY_TEXT.split("\n");
  const lang = m.src === "glb" ? m.tgt : m.src;
  const dir = path.join(repo, "parallel_gold_cache", lang);
  const lines = [];
  if (existsSync(dir)) {
    for (const f of readdirSync(dir).filter((f) => f.endsWith(".tsv")).sort()) {
      const col = f.startsWith(`${lang}-glb`) ? (m.src === "glb" ? 1 : 0) : (m.src === "glb" ? 0 : 1);
      for (const line of readFileSync(path.join(dir, f), "utf8").split("\n")) {
        if (!line || line.startsWith("#")) continue;
        const cell = (line.split("\t")[col] || "").trim();
        if (cell) lines.push(cell);
      }
    }
  }
  // spread over the files rather than the first N lines of one
  const step = Math.max(1, Math.floor(lines.length / N));
  return lines.filter((_, i) => i % step === 0).slice(0, N);
}

function nativeRun(m, text) {
  // the apertium command itself (plain text: destxt, wblank-mode pipeline, retxt)
  const pairDir = path.join(repo, "GlobasaTranslation", `apertium-${m.src === "glb" ? `glb-${m.tgt}` : `glb-${m.src}`}`);
  // input as a file: started from Node, the wrapper's stdin path is not readable and
  // apertium-destxt only prints its usage
  const inFile = path.join(tmp, "in.txt");
  writeFileSync(inFile, text + "\n");
  const out = execFileSync("bash", ["-c", capped(`apertium -d '${pairDir}' ${m.mode} '${inFile}'`)], {
    encoding: "utf8", maxBuffer: 1 << 28,
    env: { ...process.env, ...NEURAL_OFF, AP_SETVAR: SETVAR }, stdio: ["pipe", "pipe", "pipe"],
  });
  return out.trim();
}

// PARITY_STEPS=1: on a difference, rerun the line step by step (each wasm step fed the
// native stream of the step before) and report the first step whose output differs.
async function firstDivergence(m, manifest, line) {
  let stream = line + "\n";
  for (let i = 0; i < manifest.steps.length; i++) {
    const step = manifest.steps[i];
    if (step.tool === "apertium-retxt") stream = stream.replace(/\[<STREAMCMD:[^\]]*>\]/g, "");
    const nat = execFileSync("bash", ["-c", capped(step.cmd)], { input: stream, encoding: "utf8",
      env: { ...process.env, ...NEURAL_OFF, AP_SETVAR: SETVAR }, stdio: ["pipe", "pipe", "pipe"] });
    t.modes.set("__step", { ...manifest, mode: "__step", steps: [step] });
    let w;
    try { w = (await t.translate("__step", stream.replace(/\n$/, ""), "")).output; } catch (e) { w = "ERROR " + e.message; }
    if (w !== nat.trim()) {
      console.log(`   first divergent step ${i}: ${step.cmd.slice(0, 160)}`);
      console.log(`     input:  ${stream.slice(0, 600)}`);
      console.log(`     wasm:   ${w.slice(0, 600)}`);
      console.log(`     native: ${nat.trim().slice(0, 600)}`);
      return;
    }
    stream = nat;
    if (step.tool === "apertium-destxt" && SETVAR) stream = `[<STREAMCMD:SETVAR:${SETVAR}>]` + stream;
  }
  console.log("   no single step diverges (difference comes from stream context)");
}

const pyodide = await loadPyodide();
const t = new Translator();
await t.init({
  wasm: path.join(dist, "wasm", "apertium.wasm"),
  mjs: path.join(dist, "wasm", "apertium.mjs"),
  icu: readFileSync(path.join(dist, "wasm", "icudt68l.dat")),
  nfcn: readFileSync(path.join(dist, "wasm", "nfcn.nrm")),
  pyodide,
  runnerPy: readFileSync(path.join(web, "py", "runner.py"), "utf8"),
});
const opened = new Set();
if (process.env.ICU_FULL) {
  const items = new Map();
  for (const n of readdirSync(process.env.ICU_FULL, { recursive: true })) {
    const p = path.join(process.env.ICU_FULL, n);
    try { items.set(n, readFileSync(p)); } catch { /* directory */ }
  }
  setIcuData(items, (name) => opened.add(name));
}

let failed = 0;
for (const m of modes) {
  const manifest = JSON.parse(readFileSync(path.join(dist, "pairs", `${m.mode}.json`), "utf8"));
  await t.loadMode(manifest, async (f) => readFileSync(path.join(dist, "pairs", f.url)));
  const lines = sample(m);
  if (!lines.length) { console.log(`skip ${m.mode}: no sample text`); continue; }
  const text = lines.join("\n");
  const t0 = performance.now();
  let w;
  try {
    w = await t.translate(m.mode, text, SETVAR);
  } catch (e) {
    failed++;
    console.log(`FAIL ${m.mode}: ${e.message}`);
    continue;
  }
  const ms = performance.now() - t0;
  let n;
  try {
    n = nativeRun(m, text);
  } catch (e) {
    failed++;
    console.log(`FAIL ${m.mode}: native run failed under the ${NATIVE_KB >> 20} GB cap `
      + `(${(e.stderr || e.message || "").toString().trim().split("\n").pop()}); wasm gave ${w.output.split("\n").length} lines`);
    continue;
  }
  const wl = w.output.split("\n"), nl = n.split("\n");
  const diff = wl.map((l, i) => [i, l, nl[i]]).filter(([, a, b]) => a !== b);
  if (diff.length || wl.length !== nl.length) failed++;
  const slow = [...w.steps].sort((a, b) => b.ms - a.ms).slice(0, 3).map((s) => `${s.name} ${s.ms}`).join(", ");
  console.log(`${diff.length || wl.length !== nl.length ? "DIFF" : "ok  "} ${m.mode.padEnd(14)} ${lines.length} lines `
    + `${(ms / 1000).toFixed(1)} s (slowest: ${slow})  notes: ${new Set(w.notes.map((x) => x.split(":")[0])).size}`);
  for (const [i, a, b] of diff.slice(0, 3)) {
    console.log(`   line ${i}\n     wasm:   ${a}\n     native: ${b}`);
  }
  if (diff.length && process.env.PARITY_STEPS) await firstDivergence(m, manifest, lines[diff[0][0]]);
}
if (opened.size) console.log("ICU items opened:", [...opened].sort().join(" "));
console.log(failed ? `${failed} mode(s) differ or fail` : "all modes identical");
process.exit(failed ? 1 : 0);
