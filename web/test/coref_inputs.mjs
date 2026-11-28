// Inputs for the LitBank coreference checks: the browser tokenisation of the eng dev sentences
// (one document each, as gap_dump translates them) and of the first chapters of The Time
// Machine (checkpoints + windows + hierarchical merging), one JSON line per chapter:
//   {id, words: [text], windows: [[start, end)], budget}
// Read by web/tagger/export_litbank_coref.py, which adds Tibert's chains and its own.
//   node web/test/coref_inputs.mjs OUT.jsonl [VOCAB.txt]
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { tokenize } from "../src/tagger.mjs";
import { WordPiece, chaptersOf, windowsOf, PROFILES } from "../src/coref.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.join(here, "..", "..");
const VOCAB = process.argv[3] || "/media/paleos/Warehouse2/Language/Claude/browser_coref/hf/hub/"
  + "models--compnet-renard--bert-base-cased-literary-coref-v2/snapshots/d6f6693711f680099a59d9246bc8282dc9cc4af3/vocab.txt";
let vocabText;
try { vocabText = readFileSync(VOCAB, "utf8"); } catch (e) {
  vocabText = readFileSync(VOCAB.replace(/models--compnet[^/]+\/snapshots\/[^/]+/, "models--bert-base-cased/snapshots/cd5ef92a9fb2f889e972770a36d4ed042daf221e"), "utf8");
}
const vocab = vocabText.split("\n");
if (vocab.at(-1) === "") vocab.pop();
const tok = new WordPiece(vocab);

// words as the tagger gives them (i, sent, start, end, text)
function wordsOf(text) {
  const words = [];
  tokenize(text).forEach((toks, s) => toks.forEach((t) => words.push({ i: words.length, sent: s, ...t })));
  return words;
}

const out = [];
function add(id, text, budget) {
  const words = wordsOf(text);
  chaptersOf(text, words).forEach((ch, c) => {
    const pieces = ch.words.map((w) => tok.ids(w.text));
    out.push(JSON.stringify({ id: `${id}#${c}`, words: ch.words.map((w) => w.text),
      pieces, windows: windowsOf(ch, pieces, budget), budget }));
  });
}

for (const set of ["udhr", "pnc", "telltale", "thirty"]) {
  const lines = readFileSync(path.join(repo, `parallel_gold_cache/eng/eng-glb-${set}-dev.tsv`), "utf8").split("\n");
  lines.forEach((line, n) => {
    if (!line || line.startsWith("#")) return;
    const [src, gold] = line.split("\t");
    if (!src || !gold) return;
    add(`${set}:${n}`, src.trim(), PROFILES.desktop.window);
  });
}
// The Time Machine, title + chapters I-II, line breaks as the neural steps send them
const tm = readFileSync(path.join(repo, "time-machine/text/heinemann.txt"), "utf8").split("\n").slice(0, 172)
  .filter((l) => l.trim()).join("\n\n");
for (const [name, p] of Object.entries(PROFILES)) add(`timemachine-${name}`, tm, p.window);
// small: the same merge with a Tibert reference. Tibert's own path needs > 12 GB on a 450-word
// window (the exporter skips it above TIBERT_MAX_WORDS), and its merge builds a spans x spans
// matrix over the whole merged text, so: the opening ~700 words in 128-piece windows.
const paras = tm.split("\n\n");
let small = [], n = 0;
for (const p of paras) { if (n > 700) break; small.push(p); n += p.split(/\s+/).length; }
add("timemachine-small", small.join("\n\n"), 128);
writeFileSync(process.argv[2], out.join("\n") + "\n");
console.log(out.length, "documents");
