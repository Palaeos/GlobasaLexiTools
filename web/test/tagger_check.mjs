// The in-browser English tagger (src/tagger.mjs + onnxruntime-web) on UD EWT test with
// gold words: its Penn accuracy must match what web/tagger/export_stanza_pos.py reports
// for the exported files (combined 95.99, gum 92.98 with the top-100k int8 vectors).
// Then the tokenizer + both taggers on a probe sentence.
//   python3 web/test/capped.py node web/test/tagger_check.mjs [EXPORT_DIR] [MAX_SENTS]
import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import * as ort from "onnxruntime-web";
import { EnglishTagger } from "../src/tagger.mjs";

const dir = process.argv[2] || "/media/paleos/Warehouse2/Language/Claude/browser_tagger/export_100000";
const maxSents = Number(process.argv[3] || 100000);
const ud = "/media/paleos/Warehouse2/Language/Claude/browser_tagger/ud/en_ewt-ud-test.conllu";
ort.env.wasm.numThreads = 1;

const t = await new EnglishTagger().load(pathToFileURL(dir + "/").href, ort,
  async (url) => new Uint8Array(readFileSync(new URL(url))));

const sents = [];
let cur = [];
for (const line of readFileSync(ud, "utf8").split("\n")) {
  if (!line) { if (cur.length) sents.push(cur); cur = []; continue; }
  if (line.startsWith("#")) continue;
  const c = line.split("\t");
  if (!c[0].includes("-") && !c[0].includes(".")) cur.push([c[1], c[3], c[4]]);
}
const t0 = performance.now();
let n = 0;
const ok = { combined_nocharlm: 0, gum_nocharlm: 0 };
for (const s of sents.slice(0, maxSents)) {
  const words = s.map((w) => w[0]);
  for (const name of Object.keys(ok)) {
    const r = await t.tagSentence(name, words);
    r.xpos.forEach((x, i) => { if (x === s[i][2]) ok[name]++; });
  }
  n += s.length;
}
const secs = (performance.now() - t0) / 1000;
for (const [name, c] of Object.entries(ok)) console.log(`${name}: Penn ${(100 * c / n).toFixed(2)}% on ${n} EWT words`);
console.log(`${(n / secs).toFixed(0)} words/s (both taggers)`);

const probe = "Rule-based machine translation between Globasa and six languages, running entirely in your browser: the Apertium pairs are compiled to WebAssembly and loaded into memory, so nothing you type leaves this page. Don't panic, it's fine.";
const a = await t.analyze(probe);
console.log(a.words.map((w) => `${w.text}/${w.xpos}${w.xpos2 !== w.xpos ? "|" + w.xpos2 : ""}`).join(" "));
