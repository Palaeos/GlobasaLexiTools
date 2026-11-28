// Where the browser translator's time goes, to judge what a Rust port of the Python steps could
// win: one eng->glb translation of a Time Machine chapter, timed per step and split into
//   wasm tools (lt-proc, cg-proc, rtx-proc ...), Python steps in Pyodide (own work only),
//   the in-browser tagger + parser (ONNX) and the LitBank model, both awaited by the neural steps.
//   python3 web/test/capped.py node web/test/step_timing.mjs [off|mobile|desktop] [CHAPTER] [profile] [SAVE_DIR]
// profile: cProfile inside Pyodide, top functions by own time per Python step.
// SAVE_DIR: each Python step's final input (stream, args, env) for test/step_native.py, which
// runs the same steps under native CPython on the same streams.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ort from "onnxruntime-web";
import { loadPyodide } from "pyodide";
import { Translator } from "../src/pipeline.mjs";
import { EnglishTagger } from "../src/tagger.mjs";
import { LitBankCoref, PROFILES } from "../src/coref.mjs";

const [mode = "off", chapter = "VIII", profileArg = "", saveDir = ""] = process.argv.slice(2);
const profiling = profileArg === "profile";
const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, ".."), repo = path.join(web, ".."), dist = path.join(web, "dist");
ort.env.wasm.numThreads = 1;
const file = async (url) => new Uint8Array(readFileSync(new URL(url)));

const lines = readFileSync(path.join(repo, "time-machine/text/heinemann.txt"), "utf8").split("\n");
const start = lines.findIndex((l) => l.trim() === chapter);
let end = lines.findIndex((l, i) => i > start && /^[IVXL]+$/.test(l.trim()));
if (end < 0) end = lines.length;
const text = lines.slice(start, end).filter((l) => l.trim()).join("\n");
const words = text.split(/\s+/).length;

const t = new Translator();
const pyodide = await loadPyodide();
await t.init({
  wasm: path.join(dist, "wasm", "apertium.wasm"), mjs: path.join(dist, "wasm", "apertium.mjs"),
  icu: readFileSync(path.join(dist, "wasm", "icudt68l.dat")), nfcn: readFileSync(path.join(dist, "wasm", "nfcn.nrm")),
  pyodide, runnerPy: readFileSync(path.join(web, "py", "runner.py"), "utf8"),
});
const manifest = JSON.parse(readFileSync(path.join(dist, "pairs", "eng-glb.json"), "utf8"));
await t.loadMode(manifest, async (f) => readFileSync(path.join(dist, "pairs", f.url)));
const tagger = await new EnglishTagger().load(pathToFileURL(path.join(dist, "tagger", "en") + "/").href, ort, file);
t.setNlp("eng", tagger);
if (mode !== "off") {
  const coref = await new LitBankCoref().load(pathToFileURL(path.join(dist, "coref", "en") + "/").href, ort, file);
  coref.profile = mode;
  tagger.setCoref(coref);
}

// model time, measured where the neural steps wait for it
const model = { tagger: 0, coref: 0 };
const analyze = tagger.analyze.bind(tagger);
tagger.analyze = async (txt, opts) => { const t0 = performance.now(); const r = await analyze(txt, opts);
  model.tagger += performance.now() - t0; return r; };
if (tagger.coref) {
  const resolve = tagger.coref.resolve.bind(tagger.coref);
  tagger.coref.resolve = async (...a) => { const t0 = performance.now(); const r = await resolve(...a);
    model.coref += performance.now() - t0; return r; };
}

// Python steps: own time per call (the analysis requests in between are the model's time)
if (profiling) {
  pyodide.runPython(`
import cProfile, io, pstats, runner
_prof = {}
def run_step_prof(path, args, stream, env):
    p = _prof.setdefault(path + " " + " ".join(args), cProfile.Profile())
    p.enable()
    try:
        return runner.run_step(path, args, stream, env)
    finally:
        p.disable()
def prof_report(n=12):
    out = []
    for name, p in _prof.items():
        s = io.StringIO()
        pstats.Stats(p, stream=s).sort_stats("tottime").print_stats(n)
        body = "\\n".join(l for l in s.getvalue().splitlines() if l.strip())
        out.append("### " + name + "\\n" + body)
    return "\\n\\n".join(out)
`);
  t.runStep = pyodide.globals.get("run_step_prof");
}
const pyOwn = new Map(), saved = [];
const inner = t.runStep;
t.runStep = (p, args, stream, env) => {
  const t0 = performance.now();
  const res = inner(p, args, stream, env);
  const key = `${p.split("/").pop()} ${args.toJs().join(" ")}`.trim();
  pyOwn.set(key, (pyOwn.get(key) || 0) + performance.now() - t0);
  if (saveDir) saved.push({ key, path: p, args: args.toJs(), env: env.toJs({ dict_converter: Object.fromEntries }), stream });
  return res;
};

const t0 = performance.now();
const r = await t.translate("eng-glb", text);
const total = performance.now() - t0;

const pyTotal = [...pyOwn.values()].reduce((a, b) => a + b, 0);
const toolTotal = r.steps.filter((s) => !/\.py\b/.test(s.name)).reduce((a, s) => a + s.ms, 0);
const fmt = (ms) => `${(ms / 1000).toFixed(1).padStart(6)} s ${(100 * ms / total).toFixed(0).padStart(3)}%`;
console.log(`chapter ${chapter}, ${words} words, LitBank ${mode}${profiling ? " (cProfile on: Python times inflated)" : ""}`);
console.log(`total            ${fmt(total)}`);
console.log(`wasm tools       ${fmt(toolTotal)}`);
console.log(`Python (Pyodide) ${fmt(pyTotal)}`);
console.log(`tagger + parser  ${fmt(model.tagger - model.coref)}`);
console.log(`LitBank model    ${fmt(model.coref)}`);
console.log("\nper step (wall time; a neural step includes the model time it waited for):");
for (const s of [...r.steps].sort((a, b) => b.ms - a.ms).slice(0, 14)) {
  const own = pyOwn.get(s.name);
  console.log(`  ${fmt(s.ms)}  ${s.name}${own !== undefined ? `   (own Python ${(own / 1000).toFixed(1)} s)` : ""}`);
}
if (profiling) console.log("\n" + pyodide.globals.get("prof_report")(14));
if (saveDir) {
  mkdirSync(saveDir, { recursive: true });
  // the last call of each step is the one that ran to the end (earlier ones stopped for an analysis)
  const last = new Map();
  for (const s of saved) last.set(s.key, s);
  [...last.values()].forEach((s, k) => {
    writeFileSync(path.join(saveDir, `${String(k).padStart(2, "0")}.stream`), s.stream);
    writeFileSync(path.join(saveDir, `${String(k).padStart(2, "0")}.json`),
      JSON.stringify({ key: s.key, path: s.path, args: s.args, env: s.env, pyodide_ms: Math.round(pyOwn.get(s.key)) }));
  });
  console.log(`saved ${last.size} step inputs to ${saveDir}`);
}
