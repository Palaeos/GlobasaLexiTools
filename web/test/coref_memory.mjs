// LitBank mode memory budget: a whole Time Machine chapter (VIII, the longest, ~4,200 words)
// through the full eng->glb pipeline (wasm tools, Pyodide, tagger + parser, LitBank model) with
// one window profile. Fails when the process's peak RSS passes the profile's budget (user,
// 2026-11-27: mobile 1 GB, desktop 2 GB for the whole tab). Node stands in for the tab here (no
// Chromium in this sandbox): its RSS includes V8, the wasm heaps and onnxruntime's arena.
//   python3 web/test/capped.py node web/test/coref_memory.mjs mobile|desktop [CHAPTER]
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ort from "onnxruntime-web";
import { loadPyodide } from "pyodide";
import { Translator } from "../src/pipeline.mjs";
import { EnglishTagger } from "../src/tagger.mjs";
import { LitBankCoref, PROFILES } from "../src/coref.mjs";

const BUDGET_GB = { mobile: 1, desktop: 2, off: 1 };
const profile = process.argv[2] || "mobile";     // off: the same run with the LitBank mode off (baseline)
const chapter = process.argv[3] || "VIII";
if (profile !== "off" && !PROFILES[profile]) throw new Error(`profile: ${Object.keys(PROFILES).join(" | ")}`);
const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, ".."), repo = path.join(web, ".."), dist = path.join(web, "dist");
ort.env.wasm.numThreads = 1;
const file = async (url) => new Uint8Array(readFileSync(new URL(url)));

const lines = readFileSync(path.join(repo, "time-machine/text/heinemann.txt"), "utf8").split("\n");
const start = lines.findIndex((l) => l.trim() === chapter);
let end = lines.findIndex((l, i) => i > start && /^[IVXL]+$/.test(l.trim()));
if (end < 0) end = lines.length;
const text = lines.slice(start, end).filter((l) => l.trim()).join("\n");

const rss = () => process.memoryUsage().rss / 1024 ** 3;
const t = new Translator();
await t.init({
  wasm: path.join(dist, "wasm", "apertium.wasm"), mjs: path.join(dist, "wasm", "apertium.mjs"),
  icu: readFileSync(path.join(dist, "wasm", "icudt68l.dat")), nfcn: readFileSync(path.join(dist, "wasm", "nfcn.nrm")),
  pyodide: await loadPyodide(), runnerPy: readFileSync(path.join(web, "py", "runner.py"), "utf8"),
});
const manifest = JSON.parse(readFileSync(path.join(dist, "pairs", "eng-glb.json"), "utf8"));
await t.loadMode(manifest, async (f) => readFileSync(path.join(dist, "pairs", f.url)));
const tagger = await new EnglishTagger().load(pathToFileURL(path.join(dist, "tagger", "en") + "/").href, ort, file);
t.setNlp("eng", tagger);
const before = rss();
if (profile !== "off") {
  const coref = await new LitBankCoref().load(pathToFileURL(path.join(dist, "coref", "en") + "/").href, ort, file);
  coref.profile = profile;
  tagger.setCoref(coref);
}
const loaded = rss();
let peak = loaded;
const timer = setInterval(() => { peak = Math.max(peak, rss()); }, 100);
const t0 = performance.now();
const r = await t.translate("eng-glb", text);
const secs = (performance.now() - t0) / 1000;
clearInterval(timer);
peak = Math.max(peak, rss(), process.resourceUsage().maxRSS / 1024 ** 2);
const words = text.split(/\s+/).length;
console.log(`chapter ${chapter}: ${words} words, profile ${profile}${PROFILES[profile] ? ` (window ${PROFILES[profile].window} pieces)` : ""}`);
console.log(`RSS: pipeline + tagger ${before.toFixed(2)} GB, + LitBank model ${loaded.toFixed(2)} GB, peak ${peak.toFixed(2)} GB`
  + ` (budget ${BUDGET_GB[profile]} GB)`);
console.log(`translate: ${secs.toFixed(0)} s (${(secs / words * 100).toFixed(2)} s per 100 words)`);
if (tagger.coref) console.log("LitBank:", JSON.stringify(tagger.coref.stats));
console.log("notes:", [...new Set(r.notes)].filter((n) => /coref|focus/.test(n)).join(" | "));
process.exit(peak > BUDGET_GB[profile] ? 1 : 0);
