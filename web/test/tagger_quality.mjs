// eng->glb in the browser pipeline, with and without the in-browser tagger (src/tagger.mjs):
// chrF (as test/score.py: character 1-6-grams, beta 2, best over " | " alternatives) and
// exact matches on the curated sentences and the eng dev sets, each line on its own.
//   python3 web/test/capped.py node web/test/tagger_quality.mjs [LINES_PER_FILE]
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ort from "onnxruntime-web";
import { loadPyodide } from "pyodide";
import { Translator } from "../src/pipeline.mjs";
import { EnglishTagger } from "../src/tagger.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, ".."), repo = path.join(web, ".."), dist = path.join(web, "dist");
const PER_FILE = Number(process.argv[2] || 60);
ort.env.wasm.numThreads = 1;

function ngrams(text, n) {
  text = text.split(/\s+/).filter(Boolean).join(" ");
  const c = new Map();
  for (let i = 0; i + n <= text.length; i++) { const g = text.slice(i, i + n); c.set(g, (c.get(g) || 0) + 1); }
  return c;
}
function chrf(hyp, ref) {
  const P = [], R = [];
  for (let n = 1; n <= 6; n++) {
    const h = ngrams(hyp, n), r = ngrams(ref, n);
    if (!h.size || !r.size) continue;
    let ov = 0, hs = 0, rs = 0;
    for (const [g, k] of h) { ov += Math.min(k, r.get(g) || 0); hs += k; }
    for (const k of r.values()) rs += k;
    P.push(ov / hs); R.push(ov / rs);
  }
  if (!P.length) return 0;
  const p = P.reduce((a, b) => a + b) / P.length, r = R.reduce((a, b) => a + b) / R.length;
  return p + r === 0 ? 0 : (5 * p * r) / (4 * p + r);
}
function gold(file, limit) {
  const rows = [];
  for (const line of readFileSync(file, "utf8").split("\n")) {
    if (!line || line.startsWith("#")) continue;
    const [src, ref] = line.split("\t");
    if (src && ref) rows.push([src.trim(), ref.trim()]);
  }
  const step = Math.max(1, Math.floor(rows.length / limit));
  return rows.filter((_, i) => i % step === 0).slice(0, limit);
}

const t = new Translator();
await t.init({
  wasm: path.join(dist, "wasm", "apertium.wasm"), mjs: path.join(dist, "wasm", "apertium.mjs"),
  icu: readFileSync(path.join(dist, "wasm", "icudt68l.dat")), nfcn: readFileSync(path.join(dist, "wasm", "nfcn.nrm")),
  pyodide: await loadPyodide(), runnerPy: readFileSync(path.join(web, "py", "runner.py"), "utf8"),
});
const manifest = JSON.parse(readFileSync(path.join(dist, "pairs", "eng-glb.json"), "utf8"));
await t.loadMode(manifest, async (f) => readFileSync(path.join(dist, "pairs", f.url)));
const tagger = await new EnglishTagger().load(pathToFileURL(path.join(dist, "tagger", "en") + "/").href, ort,
  async (url) => new Uint8Array(readFileSync(new URL(url))));

const sets = [["curated", path.join(repo, "GlobasaTranslation/apertium-glb-eng/test/eng-glb-curated.tsv"), 1000]];
for (const f of ["udhr", "pnc", "telltale", "thirty"]) {
  sets.push([f, path.join(repo, `parallel_gold_cache/eng/eng-glb-${f}-dev.tsv`), PER_FILE]);
}
for (const [name, file, limit] of sets) {
  const rows = gold(file, limit);
  const score = {};
  for (const withTagger of [false, true]) {
    t.nlp = withTagger ? { eng: tagger } : {};
    let sum = 0, exact = 0;
    const t0 = performance.now();
    for (const [src, ref] of rows) {
      const out = (await t.translate("eng-glb", src)).output;
      const refs = ref.split(" | ");
      sum += Math.max(...refs.map((r) => chrf(out, r)));
      if (refs.includes(out)) exact++;
      if (name === "curated") console.log(`   ${withTagger ? "tagger" : "rules "}: ${out}`);
    }
    score[withTagger] = { chrf: (100 * sum / rows.length).toFixed(1), exact, s: ((performance.now() - t0) / 1000).toFixed(0) };
  }
  console.log(`${name.padEnd(9)} ${rows.length} lines: rule-only chrF ${score[false].chrf} (exact ${score[false].exact}, ${score[false].s}s)`
    + `  →  browser tagger chrF ${score[true].chrf} (exact ${score[true].exact}, ${score[true].s}s)`);
}
