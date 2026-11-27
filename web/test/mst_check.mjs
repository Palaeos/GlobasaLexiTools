// web/src/mst.mjs must return stanza's trees: the parser exporter
// (tagger/export_stanza_depparse.py) dumps the arc scores of the first UD EWT test sentences
// with the heads stanza's chuliu_edmonds_one_root found for them (mst_cases.json).
//   node web/test/mst_check.mjs [PATH/mst_cases.json]
import { readFileSync } from "node:fs";
import { chuliuEdmondsOneRoot } from "../src/mst.mjs";

const path = process.argv[2] ?? "/media/paleos/Warehouse2/Language/Claude/browser_tagger/export_parser/mst_cases.json";
// Python's json writes -Infinity, which JSON.parse does not read
const cases = JSON.parse(readFileSync(path, "utf8").replaceAll("-Infinity", "null"));
let bad = 0, words = 0;
for (const [k, c] of cases.entries()) {
  const n = c.arcs.length;
  const flat = new Float64Array(n * n);
  c.arcs.forEach((row, i) => row.forEach((x, j) => { flat[i * n + j] = x === null ? -Infinity : x; }));
  const got = [...chuliuEdmondsOneRoot(flat, n)];
  words += n - 1;
  if (got.join() !== c.heads.join()) {
    bad += 1;
    console.log(`case ${k}: stanza ${c.heads.join(" ")}\n        js     ${got.join(" ")}`);
  }
}
console.log(`mst.mjs vs stanza: ${cases.length - bad} of ${cases.length} trees identical (${words} words)`);
process.exit(bad ? 1 : 0);
