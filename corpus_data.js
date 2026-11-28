// Data access for the TMX and PoS viewers (tmx_viewer.html, pos_viewer.html).
//
// Server mode (Flask, Word Viewer.py): corpusFetch(url) is fetch(url).
// Static mode (<meta name="wv-mode" content="static">, the GitHub Pages build
// written by export_word_viewer_site.py): the same /api/... URLs are answered
// here from data/corpus/*.json, with the server's filter and pagination rules
// (api_tmx / api_pos: exact context match; q is a lowercase substring of the
// Globasa or the target text), so the page code does not change.
//
// Static files:
//   data/corpus/languages.json   [{lang, count}]
//   data/corpus/glb.json         [{glb_text, glb_morphs, mwes, glb_pos_tokens}]
//                                (each Globasa sentence once, shared by all languages)
//   data/corpus/<lang>.json      [[glb index, context, target_text], ...] in TMX order
//   data/corpus/pos_tags.json    [{tag, name}]

const CORPUS_STATIC = (document.querySelector('meta[name="wv-mode"]') || {}).content === "static";
const _corpusCache = {};

function _corpusJson(path) {
  if (!_corpusCache[path]) {
    _corpusCache[path] = fetch(path).then(r => {
      if (!r.ok) throw new Error(`${path}: ${r.status}`);
      return r.json();
    });
  }
  return _corpusCache[path];
}

function _corpusResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {status, headers: {"Content-Type": "application/json"}});
}

async function _corpusRows(lang) {
  const [glb, rows] = await Promise.all([
    _corpusJson("data/corpus/glb.json"),
    _corpusJson(`data/corpus/${encodeURIComponent(lang)}.json`),
  ]);
  return rows.map(([g, context, target_text], id) => ({id, context, target_text, g: glb[g]}));
}

async function _corpusPage(params, kind) {
  const lang = params.get("lang") || "en";
  const page = parseInt(params.get("page") || "1", 10);
  const perPage = parseInt(params.get("per_page") || "50", 10);
  const q = (params.get("q") || "").trim().toLowerCase();
  const context = (params.get("context") || "").trim();
  let rows = await _corpusRows(lang);
  if (context) rows = rows.filter(r => r.context === context);
  if (q) rows = rows.filter(r => r.g.glb_text.toLowerCase().includes(q) || r.target_text.toLowerCase().includes(q));
  const start = (page - 1) * perPage;
  const entries = rows.slice(start, start + perPage).map(r => kind === "tmx"
    ? {id: r.id, context: r.context, glb_text: r.g.glb_text, glb_morphs: r.g.glb_morphs,
       mwes: r.g.mwes, target_text: r.target_text}
    : {id: r.id, context: r.context, glb_text: r.g.glb_text, glb_pos_tokens: r.g.glb_pos_tokens,
       target_text: r.target_text});
  const out = {lang, total: rows.length, page, per_page: perPage, entries};
  if (kind === "tmx") Object.assign(out, {decompose: false, tokenizer_ok: true});
  return out;
}

async function corpusFetch(url) {
  if (!CORPUS_STATIC) return fetch(url);
  const u = new URL(url, "http://wv.invalid");
  const m = u.pathname.match(/^\/api\/(tmx|pos)(\/(languages|contexts|tags))?$/);
  if (!m) return _corpusResponse({error: "not in the static site"}, 404);
  const [, kind, , sub] = m;
  try {
    if (sub === "languages") return _corpusResponse(await _corpusJson("data/corpus/languages.json"));
    if (sub === "tags") return _corpusResponse(await _corpusJson("data/corpus/pos_tags.json"));
    if (sub === "contexts") {
      const counts = new Map();
      for (const r of await _corpusRows(u.searchParams.get("lang") || "en")) {
        if (r.context) counts.set(r.context, (counts.get(r.context) || 0) + 1);
      }
      // Same order as the server: most frequent first, ties in first-seen order.
      const out = [...counts].map(([context, count]) => ({context, count}));
      out.sort((a, b) => b.count - a.count);
      return _corpusResponse(out);
    }
    return _corpusResponse(await _corpusPage(u.searchParams, kind));
  } catch (e) {
    return _corpusResponse({error: String(e)}, 404);
  }
}

// Languages with full support in the dictionary (word-list columns) come first
// in the language <select>; the rest go under "Partial".
const CORPUS_FULL_LANGS = ["en", "es", "eo"];

function fillCorpusLangSelect(select, langs, names) {
  const groups = [["Full", langs.filter(l => CORPUS_FULL_LANGS.includes(l.lang))],
                  ["Partial", langs.filter(l => !CORPUS_FULL_LANGS.includes(l.lang))]];
  groups.forEach(([label, items]) => {
    if (!items.length) return;
    const og = document.createElement("optgroup");
    og.label = label;
    items.sort((a, b) => CORPUS_FULL_LANGS.indexOf(a.lang) - CORPUS_FULL_LANGS.indexOf(b.lang)
                         || (b.count || 0) - (a.count || 0));
    items.forEach(item => {
      const opt = document.createElement("option");
      opt.value = item.lang;
      const label = names[item.lang] || item.lang;
      opt.textContent = item.count == null ? label : `${label} (${item.count})`;
      og.appendChild(opt);
    });
    select.appendChild(og);
  });
}

// Static mode: drop local-only nav links, point TMX/PoS at their static pages.
function applyCorpusSiteMode() {
  if (!CORPUS_STATIC) return;
  document.querySelectorAll(".server-only").forEach(el => el.remove());
  document.querySelectorAll("[data-static-href]").forEach(a => { a.href = a.dataset.staticHref; });
}
