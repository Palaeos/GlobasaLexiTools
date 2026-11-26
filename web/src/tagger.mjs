// In-browser English PoS tagging for the eng->glb pipeline: stanza's combined and gum
// taggers (non-transformer), exported to ONNX by web/tagger/export_stanza_pos.py, run with
// onnxruntime-web. analyze(text) answers like eng-nlp-service.py's /analyze, as far as a
// tagger can: upos/xpos/feats from the combined model, xpos2 from the gum model (the
// client prunes only where both agree, as on the desktop). No parser: head -1, deprel "".
//
// Mapping as stanza's data loader (checked against stanza by the exporter):
//   word id    lowercased form in the model's word vocabulary, else UNK (1)
//   pretrained lowercased form (spaces as no-break spaces) in the shared conll17 vectors
//              (top 100k words, int8 per row), else the UNK row
//   chars      each character in the model's character vocabulary (case-sensitive)

const UNK = 1;

export class EnglishTagger {
  // base: URL of the folder with the exported files; ort: the onnxruntime-web module
  async load(base, ort, fetchBytes) {
    const get = async (f) => fetchBytes(new URL(f, base).href);
    const text = async (f) => new TextDecoder().decode(await get(f));
    const [words, i8, scale] = await Promise.all([
      text("pretrain.words.txt"), get("pretrain.i8"), get("pretrain.scale")]);
    this.preIndex = new Map(words.split("\n").map((w, i) => [w, i]));
    this.preI8 = new Int8Array(i8.buffer, i8.byteOffset, i8.byteLength);
    this.preScale = new Float32Array(scale.buffer.slice(scale.byteOffset, scale.byteOffset + scale.byteLength));
    this.models = {};
    for (const name of ["combined_nocharlm", "gum_nocharlm"]) {
      const vocab = JSON.parse(await text(`${name}.vocab.json`));
      this.dim = vocab.pretrain_dim;
      this.models[name] = {
        vocab,
        wordIndex: new Map(vocab.word.map((w, i) => [w, i])),
        charIndex: new Map(vocab.char.map((c, i) => [c, i])),
        char: await ort.InferenceSession.create(await get(`${name}.char.onnx`)),
        sent: await ort.InferenceSession.create(await get(`${name}.sent.onnx`)),
      };
    }
    this.ort = ort;
    return this;
  }

  preVector(word, out, offset) {
    const key = word.toLowerCase().replaceAll(" ", "\u00a0");
    const row = this.preIndex.get(key) ?? UNK;
    const s = this.preScale[row], d = this.dim;
    for (let k = 0; k < d; k++) out[offset + k] = this.preI8[row * d + k] * s;
  }

  async tagSentence(name, words) {
    const m = this.models[name], ort = this.ort, T = words.length;
    const wordIds = BigInt64Array.from(words.map((w) => BigInt(m.wordIndex.get(w.toLowerCase()) ?? UNK)));
    const pre = new Float32Array(T * this.dim);
    words.forEach((w, i) => this.preVector(w, pre, i * this.dim));
    const reps = [];
    for (const w of words) {
      const chars = [...w].map((c) => BigInt(m.charIndex.get(c) ?? UNK));
      const r = await m.char.run({ chars: new ort.Tensor("int64", BigInt64Array.from(chars), [1, chars.length]) });
      reps.push(r.rep.data);
    }
    const D = reps[0].length, charsBuf = new Float32Array(T * D);
    reps.forEach((r, i) => charsBuf.set(r, i * D));
    const out = await m.sent.run({
      word: new ort.Tensor("int64", wordIds, [1, T]),
      pre: new ort.Tensor("float32", pre, [1, T, this.dim]),
      chars: new ort.Tensor("float32", charsBuf, [1, T, D]),
    });
    const v = m.vocab;
    const upos = [...out.upos.data].map((x) => v.upos[Number(x)]);
    const xpos = [...out.xpos.data].map((x) => v.xpos[Number(x)]);
    const F = v.feats.columns ? v.feats.columns.length : 0;
    const feats = words.map((_, i) => {
      const parts = [];
      for (let c = 0; c < F; c++) {
        const col = v.feats.columns[c];
        const val = v.feats.values[col][Number(out.feats.data[i * F + c])];
        if (val && val !== "_" && !val.startsWith("<")) parts.push(`${col}=${val}`);
      }
      return parts.sort().join("|") || "_";
    });
    return { upos, xpos, feats };
  }

  async analyze(text) {
    const sents = tokenize(text);
    const words = [];
    let i = 0;
    for (const [s, toks] of sents.entries()) {
      if (!toks.length) continue;
      const forms = toks.map((t) => t.text);
      const a = await this.tagSentence("combined_nocharlm", forms);
      const b = await this.tagSentence("gum_nocharlm", forms);
      toks.forEach((t, k) => words.push({
        i: i++, sent: s, start: t.start, end: t.end, text: t.text, lemma: t.text,
        upos: a.upos[k], xpos: a.xpos[k], xpos2: b.xpos[k], feats: a.feats[k],
        head: -1, deprel: "", mwt: false,
      }));
    }
    return { words, coref: [], entities: [] };
  }
}

// ── EWT-style tokenization ────────────────────────────────────────────────
// Words keep internal hyphens/apostrophes/periods; English clitics are split off as in
// UD EWT (do|n't, it|'s, ca|n't, wo|n't); runs of !, ? and . stay one token. A token that
// does not line up with an Apertium unit is simply not used by the client (no pruning).
const ABBREV = new Set(["mr.", "mrs.", "ms.", "dr.", "st.", "jr.", "sr.", "prof.", "vs.", "etc.", "e.g.", "i.e.",
  "u.s.", "u.k.", "inc.", "ltd.", "co.", "no.", "vol.", "fig.", "cf.", "a.m.", "p.m."]);
const TOKEN = /\d+(?:[.,:]\d+)*|[\p{L}\p{M}\p{N}]+(?:[-'’.][\p{L}\p{M}\p{N}]+)*\.?|\.{2,}|…|[!?]+|--+|[^\s]/gu;
const CLITIC = /^(.+?)(n['’]t|['’](?:s|re|ve|ll|d|m))$/i;

export function tokenize(text) {
  const sents = [[]];
  for (const m of text.matchAll(TOKEN)) {
    let tok = m[0], start = m.index;
    // a trailing period belongs to the word only for abbreviations
    if (tok.length > 1 && tok.endsWith(".") && /[\p{L}\p{N}]/u.test(tok) && !ABBREV.has(tok.toLowerCase())
        && !/^(?:[\p{L}]\.)+$/u.test(tok)) {
      push(sents, tok.slice(0, -1), start);
      push(sents, ".", start + tok.length - 1);
    } else {
      push(sents, tok, start);
    }
    // sentence end: . ! ? … followed by whitespace, or a blank line
    const after = text.slice(m.index + m[0].length, m.index + m[0].length + 3);
    const last = sents.at(-1).at(-1);
    if (last && /^(?:[.!?…]+)$/.test(last.text) && /^\s/.test(after)) sents.push([]);
    else if (/^\s*\n\s*\n/.test(after)) sents.push([]);
  }
  return sents.filter((s) => s.length);
}

function push(sents, tok, start) {
  const cur = sents.at(-1);
  const c = CLITIC.exec(tok);
  if (c && c[1].length) {
    const head = c[1], cl = c[2];                 // ca|n't, wo|n't as in EWT
    cur.push({ text: head, start, end: start + head.length });
    cur.push({ text: cl, start: start + head.length, end: start + tok.length });
    return;
  }
  cur.push({ text: tok, start, end: start + tok.length });
}
