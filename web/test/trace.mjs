// eng->glb through the browser pipeline (with the in-browser tagger), printing the stream
// after the named steps, to trace one sentence the way gap_dump.mjs translates it.
//   python3 web/test/capped.py node web/test/trace.mjs "sentence" [step-substring ...]
// Default steps: the tagger output, the rtx output and the final text.
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ort from "onnxruntime-web";
import { loadPyodide } from "pyodide";
import { Translator } from "../src/pipeline.mjs";
import { EnglishTagger } from "../src/tagger.mjs";
import { LitBankCoref } from "../src/coref.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, ".."), dist = path.join(web, "dist");
const [text, ...want] = process.argv.slice(2);
const picks = want.length ? want : ["eng-glb-neural.py pos", "rtx-proc", "glb-pregen.py"];
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

const full = t.modes.get("eng-glb");
const label = (s) => s.tool ? `${s.tool} ${s.args.join(" ")}` : `${s.py.split("/").pop()} ${s.args.join(" ")}`;
for (let k = 1; k <= full.steps.length; k++) {
  const name = label(full.steps[k - 1]);
  if (!picks.some((p) => name.includes(p))) continue;
  t.modes.set("trace", { ...full, steps: full.steps.slice(0, k) });
  const r = await t.translate("trace", text);
  console.log(`== after ${name.slice(0, 60)}\n${r.output}`);
}
const r = await t.translate("eng-glb", text);
console.log(`== output\n${r.output}`);
