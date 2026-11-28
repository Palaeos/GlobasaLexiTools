// SPDX-License-Identifier: GPL-3.0-or-later
// LitBank coreference for the browser eng->glb pipeline (the page's opt-in "LitBank mode").
//
// Model: compnet-renard/bert-base-cased-literary-coref-v2 (weights MIT, trained on LitBank,
// CC BY 4.0), an end-to-end span model after Lee et al. 2017. The inference below is a port of
// Tibert (github.com/CompNet/Tibert, GPL-3.0: bertcoref.py forward / coreference_documents,
// predict.py merge_coref_outputs), so this file is GPL; web/ as a whole is GPL-3.0-or-later.
// Exported by web/tagger/export_litbank_coref.py:
//   coref.bert.onnx     wordpiece ids (one 128-piece segment) -> last hidden states
//   coref.heads.onnx    word vectors [w, 768] -> 6 projections [w, 6 * 3000] (below)
//   coref.consts.f32    biases, output vectors, distance-bucket projections (layout in coref.json)
//   coref.vocab.txt     bert-base-cased wordpieces
//
// Same arithmetic as Tibert, without its pair tensor. Both scorers are a linear layer over a
// concatenation followed by ReLU and a dot product, and W[x; y; d] = W1 x + W2 y + W3 d. So
// each word is projected once (Ms/Me: start/end part of the mention scorer; A/B: start/end of
// the mention in the pair scorer; C/D: start/end of the antecedent) and a pair costs one
// add + ReLU + dot over 3000 values. Tibert builds m x 350 x 3092 floats per document.
// One difference: Tibert's top-350 antecedent list is padded with invalid spans (pruned spans,
// spans after the mention) when there are fewer real candidates, and those are scored too. Here
// only real candidates (kept mentions ending before the mention starts) are scored.
// web/test/coref_check.mjs counts what that changes against Tibert's own output.
//
// Long texts (handover docs/translation/browser_parser_handover.md §1d, memory plan):
//   - checkpoints: a heading (Chapter N, a Roman numeral alone, # line, a Title Case line) or a
//     scene break (* * *, ***, #) ends a coreference document; nothing crosses it;
//   - windows: inside a chapter, whole paragraphs up to the profile's wordpiece budget (a longer
//     paragraph is cut at a sentence end outside quotations), resolved one at a time and merged
//     with Tibert's hierarchical merging (Gupta, Hatzel & Biemann 2024). Between windows only
//     the chains are kept (mention spans and scores, per-chain sums of the projections);
//   - finished chapters are cached by their text.

const BLOCKS = 6;            // Ms, Me, A, B, C, D (export order)

// Window budgets in wordpieces (each window is one Tibert document with [CLS] and [SEP]).
// Mobile: whole tab under 1 GB; desktop: under 2 GB (user, 2026-11-27; measured by
// web/test/coref_memory.mjs).
export const PROFILES = {
  mobile: { window: 512, block: 64 },
  desktop: { window: 1024, block: 128 },
};

export function defaultProfile() {
  try {
    const nav = globalThis.navigator;
    if (nav && typeof nav.deviceMemory === "number" && nav.deviceMemory >= 8) return "desktop";
    if (nav && nav.userAgentData && nav.userAgentData.mobile === false && nav.deviceMemory === undefined) return "desktop";
  } catch (e) { /* no navigator: keep the safe profile */ }
  return "mobile";
}

export class LitBankCoref {
  // base: URL of the folder with the exported files; ort: onnxruntime-web; fetchBytes(url) (may
  // cache); fetchFresh(url): for the manifest, which must not come from a cache. Every other file
  // is fetched as name?v=<hash of the parts' sha256>, so a new export never meets a stale cache.
  async load(base, ort, fetchBytes, onProgress = () => {}, fetchFresh = fetchBytes) {
    const man = JSON.parse(new TextDecoder().decode(await fetchFresh(new URL("coref.json", base).href)));
    const version = (await sha256(new TextEncoder().encode(
      Object.values(man.models).flat().map((p) => p.sha256).join(",")))).slice(0, 12);
    const get = async (f) => {
      const u = new URL(f, base);
      if (u.protocol !== "file:") u.search = `v=${version}`;
      return fetchBytes(u.href);
    };
    this.man = man;
    this.cfg = man.config;
    const total = Object.values(man.models).flat().reduce((n, p) => n + p.size, 0);
    let done = 0;
    const model = async (parts) => {
      const bufs = [];
      for (const p of parts) {
        const b = await get(p.name);
        if (b.byteLength !== p.size || (await sha256(b)) !== p.sha256) throw new Error(`${p.name}: damaged download`);
        bufs.push(b);
        done += p.size;
        onProgress(done, total);
      }
      const all = new Uint8Array(parts.reduce((n, p) => n + p.size, 0));
      let o = 0;
      for (const b of bufs) { all.set(b, o); o += b.byteLength; }
      bufs.length = 0;
      return ort.InferenceSession.create(all);
    };
    this.bert = await model(man.models.bert);
    this.heads = await model(man.models.heads);
    const c = await get(man.consts.name);
    const f32 = new Float32Array(c.buffer.slice(c.byteOffset, c.byteOffset + c.byteLength));
    this.k = {};
    for (const [name, [off, len]] of Object.entries(man.consts.layout)) this.k[name] = f32.subarray(off, off + len);
    const vocab = new TextDecoder().decode(await get(man.vocab)).split("\n");
    if (vocab.at(-1) === "") vocab.pop();
    this.tok = new WordPiece(vocab);
    this.ort = ort;
    this.profile = defaultProfile();
    this.cache = new Map();          // chapter text -> chains (chapter word indices)
    this.stats = { chapters: 0, cached: 0, windows: 0 };
    return this;
  }

  // words: the tagger's words ({i, sent, start, end, text, head}); text: the analysed text.
  // -> [[{start, end, head}]] in word indices of the whole text, as eng-nlp-service.py answers.
  async resolve(text, words, onProgress = () => {}) {
    const chains = [];
    const chapters = chaptersOf(text, words);
    let done = 0;
    for (const ch of chapters) {
      const key = this.profile + "\u0001" + ch.words.map((w) => w.text).join(" ") + "\u0001" + ch.paras.join(",");
      let local = this.cache.get(key);
      if (local) this.stats.cached++;
      else {
        this.stats.chapters++;
        local = await this.resolveChapter(ch);
        this.cache.set(key, local);
        if (this.cache.size > 64) this.cache.delete(this.cache.keys().next().value);
      }
      for (const c of local) {
        chains.push(c.map(([s, e]) => {
          const start = ch.words[s].i, end = ch.words[e - 1].i + 1;
          const inside = (j) => j >= start && j < end;
          let head = start;
          for (let j = start; j < end; j++) if (!inside(words[j].head)) { head = j; break; }
          return { start, end, head };
        }));
      }
      done += ch.words.length;
      onProgress(done, words.length);
    }
    return chains;
  }

  // one chapter -> chains as [[start, end)] in chapter word indices
  async resolveChapter(ch) {
    const pieces = ch.words.map((w) => this.tok.ids(w.text));
    const windows = windowsOf(ch, pieces, PROFILES[this.profile].window);
    const docs = [];
    for (const [s, e] of windows) { this.stats.windows++; docs.push(await this.resolveWindow(pieces.slice(s, e), s)); }
    const merged = this.merge(docs);
    return merged.chains.map((c) => c.mentions.map((m) => [m.start, m.end]).sort((a, b) => a[0] - b[0] || a[1] - b[1]));
  }

  async encode(pieces) {
    const ids = [this.tok.cls], wid = [-1];
    pieces.forEach((p, w) => { for (const x of p) { ids.push(x); wid.push(w); } });
    ids.push(this.tok.sep); wid.push(-1);
    const W = pieces.length, H = this.cfg.hidden_size, S = this.cfg.segment_size;
    const vec = new Float32Array(W * H), count = new Float32Array(W);
    for (let s0 = 0; s0 < ids.length; s0 += S) {
      const seg = ids.slice(s0, s0 + S);
      const out = await this.bert.run({ input_ids: new this.ort.Tensor("int64", BigInt64Array.from(seg.map(BigInt)), [1, seg.length]) });
      const hs = out.hidden.data;
      for (let t = 0; t < seg.length; t++) {
        const w = wid[s0 + t];
        if (w < 0) continue;
        count[w]++;
        const o = w * H, q = t * H;
        for (let k = 0; k < H; k++) vec[o + k] += hs[q + k];
      }
      out.hidden.dispose?.();
    }
    for (let w = 0; w < W; w++) {
      const n = count[w] || 1, o = w * H;
      for (let k = 0; k < H; k++) vec[o + k] /= n;
    }
    const proj = await this.heads.run({ words: new this.ort.Tensor("float32", vec, [W, H]) });
    const data = proj.proj.data;     // [W, 6 * hid]; kept until the window is done
    return data;
  }

  // One window (a Tibert document). offset: its first word in the chapter.
  // -> {chains: [{mentions: [{start, end, score}], P, Q}]} with chapter word indices;
  //    P / Q: summed mention / antecedent projections of the chain's mentions.
  async resolveWindow(pieces, offset) {
    const W = pieces.length, hid = this.cfg.mention_scorer_hidden_size, k = this.k;
    if (!W) return { chains: [] };
    const proj = await this.encode(pieces);
    const row = BLOCKS * hid;
    const at = (w, b) => w * row + b * hid;      // block b of word w
    // spans in spans_indexs order: by end, then by length
    const L = this.cfg.max_span_size, spans = [];
    for (let end = 1; end <= W; end++) for (let len = 1; len <= Math.min(L, end); len++) spans.push([end - len, end]);
    const P = spans.length, ms = new Float32Array(P);
    for (let p = 0; p < P; p++) {
      const [s, e] = spans[p], a = at(s, 0), b = at(e - 1, 1);
      let sum = 0;
      for (let j = 0; j < hid; j++) {
        const x = proj[a + j] + proj[b + j] + k.mention_b[j];
        if (x > 0) sum += x * k.mention_v[j];
      }
      ms[p] = sum + k.mention_c[0];
    }
    // pruning: best first, no crossing spans, floor(0.4 * words) of them
    const want = Math.max(Math.min(1, W), Math.floor(this.cfg.mentions_per_tokens * W));
    const order = [...spans.keys()].sort((x, y) => ms[y] - ms[x] || x - y);
    const top = [];
    for (const p of order) {
      if (top.length >= want) break;
      const [s1, e1] = spans[p];
      if (!top.some((q) => { const [s2, e2] = spans[q];
        return (s1 < s2 && e1 > s2 && e1 < e2) || (s1 > s2 && s1 < e2 && e1 > e2); })) top.push(p);
    }
    // mention-role (A, B) and antecedent-role (C, D) projection of a span
    const vec = (p, b1, b2) => {
      const [s, e] = spans[p], a = at(s, b1), b = at(e - 1, b2), out = new Float32Array(hid);
      for (let j = 0; j < hid; j++) out[j] = proj[a + j] + proj[b + j];
      return out;
    };
    // Antecedent candidates. Tibert takes the 350 closest spans by a topk over distances where
    // pruned spans and spans not before the mention are +Inf, so the list is padded with such
    // spans in torch's arbitrary tie order, and they are scored like the rest (it picks a later
    // mention now and then: cataphora). With <= 350 spans the list is every span: reproduced
    // exactly (padding: distance bucket "not before"). With more, the padding is an arbitrary
    // few of thousands of spans: only the real candidates are scored.
    const A = this.cfg.antecedents_nb, M = top.length, every = P <= A, B = this.cfg.dist_buckets;
    const Qc = new Map();
    const Q = (p) => { let v = Qc.get(p); if (!v) { v = vec(p, 4, 5); Qc.set(p, v); } return v; };
    const best = new Int32Array(M).fill(-1);    // a span index, -1 = the dummy
    for (let i = 0; i < M; i++) {
      const p = top[i], si = spans[p][0], Pi = vec(p, 2, 3);
      let cands;
      if (every) cands = spans.map((sp, q) => [q, si - sp[1] + 1]);
      else {
        cands = top.filter((q) => spans[q][1] <= si).map((q) => [q, si - spans[q][1] + 1])
          .sort((x, y) => x[1] - y[1] || x[0] - y[0]).slice(0, A);
      }
      let bestScore = 0;                     // the dummy antecedent scores 0
      for (const [q, dist] of cands) {
        const s = this.pairScore(Pi, 0, Q(q), 0, bucket(dist, B)) + ms[p] + ms[q];
        if (s > bestScore) { bestScore = s; best[i] = q; }
      }
    }
    // chains: Tibert's graph, components in the order their first node was added
    const nodeOf = new Map(), nodes = [], adj = [];
    const node = (p) => {
      if (!nodeOf.has(p)) { nodeOf.set(p, nodes.length); nodes.push(p); adj.push([]); }
      return nodeOf.get(p);
    };
    for (let i = 0; i < M; i++) {
      if (best[i] < 0) { if (ms[top[i]] > 0) node(top[i]); continue; }
      const a = node(best[i]), b = node(top[i]);
      adj[a].push(b); adj[b].push(a);
    }
    const seen = new Uint8Array(nodes.length), chains = [];
    for (let n0 = 0; n0 < nodes.length; n0++) {
      if (seen[n0]) continue;
      const comp = [], stack = [n0];
      seen[n0] = 1;
      while (stack.length) {
        const n = stack.pop(); comp.push(n);
        for (const x of adj[n]) if (!seen[x]) { seen[x] = 1; stack.push(x); }
      }
      const chain = { mentions: [], P: new Float32Array(hid), Q: new Float32Array(hid) };
      for (const n of comp) {
        const p = nodes[n], Pp = vec(p, 2, 3), Qp = Q(p);
        chain.mentions.push({ start: spans[p][0] + offset, end: spans[p][1] + offset, score: ms[p] });
        for (let j = 0; j < hid; j++) { chain.P[j] += Pp[j]; chain.Q[j] += Qp[j]; }
      }
      chains.push(chain);
    }
    return { chains };
  }

  // v'.relu(P_i + Q_j + Dist[bucket] + b') + c' (P/Q: rows of the given arrays, scaled by 1/n)
  pairScore(P, i, Q, j, b, nP = 1, nQ = 1) {
    const hid = this.cfg.mention_scorer_hidden_size, k = this.k, D = b * hid;
    let sum = 0;
    const oi = i * hid, oj = j * hid;
    for (let x = 0; x < hid; x++) {
      const v = P[oi + x] / nP + Q[oj + x] / nQ + k.dist[D + x] + k.pair_b[x];
      if (v > 0) sum += v * k.pair_v[x];
    }
    return sum + k.pair_c[0];
  }

  // Tibert merge_coref_outputs: binary tree over the windows, greedy chain matching
  merge(docs) {
    if (docs.length <= 1) return docs[0] || { chains: [] };
    const mid = Math.floor(docs.length / 2);
    const L = this.merge(docs.slice(0, mid)), R = this.merge(docs.slice(mid));
    if (!L.chains.length || !R.chains.length) return { chains: [...L.chains, ...R.chains] };
    const mean = (xs) => xs.reduce((a, m) => a + m.score, 0) / xs.length;
    const score = R.chains.map((r) => {
      const rStart = Math.min(...r.mentions.map((m) => m.start));
      return L.chains.map((l) => {
        const lEnd = Math.max(...l.mentions.map((m) => m.end));
        return this.pairScore(r.P, 0, l.Q, 0, bucket(rStart - lEnd + 1, this.cfg.dist_buckets),
          r.mentions.length, l.mentions.length) + mean(r.mentions) + mean(l.mentions);
      });
    });
    const taken = new Set(), out = [];
    L.chains.forEach((l, li) => {
      let bi = -1, bs = -Infinity;
      R.chains.forEach((_, ri) => { if (!taken.has(ri) && score[ri][li] > bs) { bs = score[ri][li]; bi = ri; } });
      if (bi < 0 || bs < 0) { out.push(l); return; }
      taken.add(bi);
      const r = R.chains[bi];
      const P = new Float32Array(l.P.length), Q = new Float32Array(l.Q.length);
      for (let x = 0; x < P.length; x++) { P[x] = l.P[x] + r.P[x]; Q[x] = l.Q[x] + r.Q[x]; }
      out.push({ mentions: [...l.mentions, ...r.mentions], P, Q });
    });
    R.chains.forEach((r, ri) => { if (!taken.has(ri)) out.push(r); });
    return { chains: out };
  }
}

// Tibert's distance buckets: <=1, 2, 3, 4, <=8, ..., <=128, further (or not before) = last
export function bucket(dist, buckets) {
  if (dist <= 0) return buckets.length;
  for (let i = 0; i < buckets.length; i++) if (dist <= buckets[i]) return i;
  return buckets.length;
}

// ── checkpoints and windows ──────────────────────────────────────────────
// The neural steps send the text with every line break as "\n\n" (eng-glb-neural.py to_text),
// so a block between blank lines is a paragraph, a heading or a scene break.
const TITLE_SMALL = new Set(["a", "an", "the", "of", "and", "or", "in", "on", "at", "to", "for", "with", "from", "by"]);
const HEADING_RE = /^(?:#{1,6}\s.*|(?:chapter|book|part)\s+(?:\d+|[ivxlcdm]+|[a-z]+)\b[^.!?]{0,60}|[ivxlcdm]+\.?)$/i;
const SCENE_RE = /^(?:[*#~•·]\s*){1,}$/;

export function isCheckpoint(block) {
  // apertium-destxt ends every line that has no final punctuation with "." ("Chapter One.",
  // "The Time Machine."): one final period is not evidence against a heading
  const t = block.trim().replace(/\s*\.$/, "");
  if (!t) return false;
  if (SCENE_RE.test(t) || HEADING_RE.test(t)) return true;
  // Title Case heading (as title_case() in eng-glb-neural.py), stricter: no other punctuation
  // or quotation marks at all (a comma: "Yes, Mr Smith."), at most 10 words
  if (/[.!?"“”:;,]/.test(t)) return false;
  const ws = t.split(/[\s,]+/).filter((w) => /^\p{L}/u.test(w));
  return ws.length >= 2 && ws.length <= 10 && ws.every((w) => /^\p{Lu}/u.test(w) || TITLE_SMALL.has(w.toLowerCase()));
}

// -> [{words: [...], paras: [first word index of each paragraph in the chapter]}]
export function chaptersOf(text, words) {
  const blocks = [];                  // [start, end) character ranges
  const re = /\n\s*\n/g;
  let pos = 0, m;
  while ((m = re.exec(text))) { blocks.push([pos, m.index]); pos = m.index + m[0].length; }
  blocks.push([pos, text.length]);
  const chapters = [];
  let cur = null, b = 0;
  const cut = new Set();
  for (const [s, e] of blocks) if (isCheckpoint(text.slice(s, e))) cut.add(s);
  let lastBlock = -1;
  for (const w of words) {
    while (b + 1 < blocks.length && w.start >= blocks[b + 1][0]) b++;
    if (cut.has(blocks[b][0])) { cur = null; continue; }            // headings take part in no chain
    if (!cur) { cur = { words: [], paras: [] }; chapters.push(cur); lastBlock = -1; }
    if (b !== lastBlock) { cur.paras.push(cur.words.length); lastBlock = b; }
    cur.words.push(w);
  }
  return chapters;
}

// Whole paragraphs up to budget wordpieces ([CLS] + [SEP] included); a longer paragraph is cut
// at sentence ends outside quotations (at any sentence end if there is none, and inside a
// sentence only when the sentence alone is longer than the budget).
export function windowsOf(ch, pieces, budget) {
  const n = ch.words.length, cost = pieces.map((p) => p.length), room = budget - 2;
  const paraEnds = [...ch.paras.slice(1), n];
  const units = [];                   // [start, end) pieces that must not be cut
  ch.paras.forEach((s, k) => {
    const e = paraEnds[k];
    if (sum(cost, s, e) <= room) { units.push([s, e]); return; }
    // sentence ends, marked whether they are outside quotations
    const ends = [];
    let depth = 0;
    for (let i = s; i < e; i++) {
      const t = ch.words[i].text;
      if (t === "“") depth++;
      else if (t === "”") depth = Math.max(0, depth - 1);
      else if (t === "\"") depth = depth ? 0 : 1;
      const next = i + 1 < e ? ch.words[i + 1] : null;
      if (!next || next.sent !== ch.words[i].sent) ends.push([i + 1, depth === 0]);
    }
    let start = s;
    while (start < e) {
      let cutAt = -1, any = -1;
      for (const [x, free] of ends) {
        if (x <= start) continue;
        if (sum(cost, start, x) > room) break;
        any = x;
        if (free) cutAt = x;
      }
      if (cutAt < 0) cutAt = any;
      if (cutAt < 0) {                // one sentence longer than the budget: cut at the budget
        cutAt = start + 1;
        while (cutAt < e && sum(cost, start, cutAt + 1) <= room) cutAt++;
      }
      units.push([start, cutAt]);
      start = cutAt;
    }
  });
  const out = [];
  for (const [s, e] of units) {
    const last = out.at(-1);
    if (last && sum(cost, last[0], e) <= room) last[1] = e;
    else out.push([s, e]);
  }
  return out;
}

function sum(cost, s, e) { let t = 0; for (let i = s; i < e; i++) t += cost[i]; return t; }

// ── bert-base-cased WordPiece (BertNormalizer: clean text, CJK split, no lowercase or accent
//    stripping; BertPreTokenizer: whitespace and punctuation; greedy longest match, "##") ──
export class WordPiece {
  constructor(vocab) {
    this.index = new Map(vocab.map((w, i) => [w, i]));
    this.unk = this.index.get("[UNK]");
    this.cls = this.index.get("[CLS]");
    this.sep = this.index.get("[SEP]");
    this.memo = new Map();
  }

  // one pre-split word -> its wordpiece ids (an empty word gets [UNK])
  ids(word) {
    if (this.memo.has(word)) return this.memo.get(word);
    const out = [];
    for (const part of preTokenize(normalize(word))) {
      const chars = [...part];
      if (chars.length > 100) { out.push(this.unk); continue; }
      const sub = [];
      let start = 0, bad = false;
      while (start < chars.length) {
        let end = chars.length, id;
        while (start < end) {
          const piece = (start ? "##" : "") + chars.slice(start, end).join("");
          id = this.index.get(piece);
          if (id !== undefined) break;
          end--;
        }
        if (start === end) { bad = true; break; }
        sub.push(id);
        start = end;
      }
      if (bad) out.push(this.unk); else out.push(...sub);
    }
    if (!out.length) out.push(this.unk);
    if (this.memo.size > 50000) this.memo.clear();
    this.memo.set(word, out);
    return out;
  }
}

function isControl(c) {
  if (c === "\t" || c === "\n" || c === "\r") return false;
  return /\p{Cc}|\p{Cf}|\p{Co}|\p{Cs}/u.test(c);
}
function isWhitespace(c) { return c === " " || c === "\t" || c === "\n" || c === "\r" || /\p{Zs}/u.test(c); }
function isCJK(cp) {
  return (cp >= 0x4E00 && cp <= 0x9FFF) || (cp >= 0x3400 && cp <= 0x4DBF) || (cp >= 0x20000 && cp <= 0x2A6DF)
    || (cp >= 0x2A700 && cp <= 0x2B73F) || (cp >= 0x2B740 && cp <= 0x2B81F) || (cp >= 0x2B820 && cp <= 0x2CEAF)
    || (cp >= 0xF900 && cp <= 0xFAFF) || (cp >= 0x2F800 && cp <= 0x2FA1F);
}
function isPunct(c) {
  const cp = c.codePointAt(0);
  if ((cp >= 33 && cp <= 47) || (cp >= 58 && cp <= 64) || (cp >= 91 && cp <= 96) || (cp >= 123 && cp <= 126)) return true;
  return /\p{P}/u.test(c);
}
function normalize(s) {
  let out = "";
  for (const c of s) {
    const cp = c.codePointAt(0);
    if (cp === 0 || cp === 0xFFFD || isControl(c)) continue;
    if (isWhitespace(c)) out += " ";
    else if (isCJK(cp)) out += ` ${c} `;
    else out += c;
  }
  return out;
}
function preTokenize(s) {
  const out = [];
  let cur = "";
  for (const c of s) {
    if (isWhitespace(c)) { if (cur) out.push(cur); cur = ""; }
    else if (isPunct(c)) { if (cur) out.push(cur); out.push(c); cur = ""; }
    else cur += c;
  }
  if (cur) out.push(cur);
  return out;
}

async function sha256(bytes) {
  const h = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
