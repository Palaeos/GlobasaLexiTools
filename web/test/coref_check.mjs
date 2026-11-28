// LitBank mode check: the JS port (src/coref.mjs, onnxruntime-web) against the exporter's own
// pipeline (onnxruntime, Python; coref.fixture.jsonl "chains") and against Tibert ("tibert"), on
// the documents of coref_inputs.mjs (same words, wordpieces and windows). Also checks that the
// JS windowing still gives the windows the fixture was made with.
//   python3 web/test/capped.py node web/test/coref_check.mjs [EXPORT_DIR [INPUTS.jsonl]]
import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import * as ort from "onnxruntime-web";
import { LitBankCoref } from "../src/coref.mjs";

ort.env.wasm.numThreads = 1;
const BASE = "/media/paleos/Warehouse2/Language/Claude/browser_coref";
const EXPORT = process.argv[2] || path.join(BASE, "export");
const INPUTS = process.argv[3] || path.join(BASE, "work", "inputs.jsonl");
const LIMIT = Number(process.env.CHECK_DOCS || 1e9);

const coref = await new LitBankCoref().load(pathToFileURL(EXPORT + "/").href, ort,
  async (url) => new Uint8Array(readFileSync(new URL(url))));
const lines = (f) => readFileSync(f, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
const inputs = lines(INPUTS).slice(0, LIMIT);
const fixture = new Map(lines(path.join(EXPORT, "coref.fixture.jsonl")).map((d) => [d.id, d]));

const canon = (chains) => chains.map((c) => c.mentions.map((m) => [m.start, m.end])
  .sort((a, b) => a[0] - b[0] || a[1] - b[1])).sort(cmp);
function cmp(a, b) {
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    const x = Array.isArray(a[i]) ? cmp(a[i], b[i]) : a[i] - b[i];
    if (x) return x;
  }
  return a.length - b.length;
}
const mentions = (chains) => new Set(chains.flatMap((c) => c.map((m) => JSON.stringify([m, c]))));
const diff = (a, b) => { const x = mentions(a), y = mentions(b); let n = 0;
  for (const m of x) if (!y.has(m)) n++; for (const m of y) if (!x.has(m)) n++; return n; };

let docs = 0, words = 0, ms = 0, piecesBad = 0;
const vsOnnx = [0, 0], vsTibert = [0, 0], examples = [];
for (const d of inputs) {
  const f = fixture.get(d.id);
  if (!f) continue;
  const pieces = d.words.map((w) => coref.tok.ids(w));
  piecesBad += pieces.filter((p, i) => JSON.stringify(p) !== JSON.stringify(d.pieces[i])).length;
  const t0 = performance.now();
  const wins = [];
  for (const [s, e] of d.windows) wins.push(await coref.resolveWindow(pieces.slice(s, e), s));
  const ours = canon(coref.merge(wins).chains);
  ms += performance.now() - t0;
  docs++; words += d.words.length;
  const a = diff(ours, f.chains), b = f.tibert ? diff(ours, f.tibert) : 0;   // null: no Tibert reference
  if (a) { vsOnnx[0]++; vsOnnx[1] += a; if (examples.length < 5) examples.push([d.id, ours, f.chains]); }
  if (b) { vsTibert[0]++; vsTibert[1] += b; }
}
console.log(`${docs} documents, ${words} words, ${(ms / words * 100).toFixed(0)} ms per 100 words (1 thread)`);
console.log(`wordpieces differing from the inputs: ${piecesBad}`);
console.log(`vs exported pipeline (Python onnxruntime): ${vsOnnx[0]} documents differ, ${vsOnnx[1]} mentions`);
console.log(`vs Tibert: ${vsTibert[0]} documents differ, ${vsTibert[1]} mentions`);
for (const [id, a, b] of examples) console.log("  ", id, JSON.stringify(a).slice(0, 300), "\n   expected", JSON.stringify(b).slice(0, 300));
process.exit(piecesBad || vsOnnx[0] ? 1 : 0);
