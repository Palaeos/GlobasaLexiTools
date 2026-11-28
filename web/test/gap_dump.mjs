// eng->glb on every eng dev sentence through the browser pipeline with the in-browser tagger;
// one JSON line per sentence (set, source, gold, output, the tagger's [word, Penn, UPOS]).
// Input of gap_report.py (structure-gap analysis, docs/translation/rule_gaps_handover.md).
//   python3 web/test/capped.py node web/test/gap_dump.mjs OUT.jsonl
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ort from "onnxruntime-web";
import { loadPyodide } from "pyodide";
import { Translator } from "../src/pipeline.mjs";
import { EnglishTagger } from "../src/tagger.mjs";
import { LitBankCoref } from "../src/coref.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, ".."), repo = path.join(web, ".."), dist = path.join(web, "dist");
ort.env.wasm.numThreads = 1;
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
// LITBANK=1: the page's LitBank mode (dist/coref/en); LITBANK_PROFILE=mobile|desktop
if (process.env.LITBANK === "1") {
  const coref = await new LitBankCoref().load(pathToFileURL(path.join(dist, "coref", "en") + "/").href, ort,
    async (url) => new Uint8Array(readFileSync(new URL(url))));
  if (process.env.LITBANK_PROFILE) coref.profile = process.env.LITBANK_PROFILE;
  tagger.setCoref(coref);
}
t.setNlp("eng", tagger);

const out = [];
for (const set of ["udhr", "pnc", "telltale", "thirty"]) {
  for (const line of readFileSync(path.join(repo, `parallel_gold_cache/eng/eng-glb-${set}-dev.tsv`), "utf8").split("\n")) {
    if (!line || line.startsWith("#")) continue;
    const [src, gold] = line.split("\t");
    if (!src || !gold) continue;
    const r = await t.translate("eng-glb", src.trim());
    const a = await tagger.analyze(src.trim());
    out.push(JSON.stringify({ set, src: src.trim(), gold: gold.trim(), out: r.output,
      tags: a.words.map((w) => [w.text, w.xpos, w.upos]) }));
  }
  console.log(set, out.length);
}
writeFileSync(process.argv[2], out.join("\n") + "\n");
