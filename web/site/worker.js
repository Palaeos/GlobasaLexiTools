// Translation worker: loads the wasm tools, Pyodide and a mode's files on demand, and
// runs the mode (src/pipeline.mjs) off the page's main thread.
// Pair files are kept in the Cache API under the bundle version, so a second visit
// loads them from disk; a rebuilt bundle has a new version and replaces the old cache.
import { Translator } from "./src/pipeline.mjs";
import { EnglishTagger } from "./src/tagger.mjs";
import { LitBankCoref, PROFILES } from "./src/coref.mjs";
import { loadPyodide } from "./pyodide/pyodide.mjs";

let index = null;
let translator = null;
let cache = null;

const post = (type, data = {}) => self.postMessage({ type, ...data });

async function bytes(url) {
  if (cache) {
    const hit = await cache.match(url);
    if (hit) return new Uint8Array(await hit.arrayBuffer());
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  if (cache) await cache.put(url, res.clone());
  return new Uint8Array(await res.arrayBuffer());
}

// models.json (web/models.json): a folder with a pinned Hugging Face revision loads from
// huggingface.co/<repo>/resolve/<revision>/, else from the bundle's own folder.
let models = {};
function modelBase(folder) {
  const m = models[folder];
  if (m && m.repo && m.revision) return `https://huggingface.co/${m.repo}/resolve/${m.revision}/`;
  return new URL(`${folder}/`, self.location.href).href;
}

async function init() {
  index = await (await fetch("pairs/index.json", { cache: "no-cache" })).json();
  try {
    const r = await fetch("models.json", { cache: "no-cache" });
    if (r.ok) models = await r.json();
  } catch { models = {}; }
  try {
    const name = `globasa-pairs-${index.version}`;
    for (const k of await caches.keys()) if (k.startsWith("globasa-pairs-") && k !== name) await caches.delete(k);
    cache = await caches.open(name);
  } catch { cache = null; /* private window: no Cache API, plain fetches */ }
  post("status", { text: "Loading the Apertium tools and Python…" });
  const [pyodide, icu, nfcn, runnerPy] = await Promise.all([
    loadPyodide({ indexURL: new URL("pyodide/", self.location.href).href }),
    bytes("wasm/icudt68l.dat"),
    bytes("wasm/nfcn.nrm"),
    fetch("py/runner.py").then((r) => r.text()),
  ]);
  translator = new Translator();
  await translator.init({
    wasm: await bytes("wasm/apertium.wasm"),
    mjs: new URL("wasm/apertium.mjs", self.location.href).href,
    icu, nfcn, pyodide, runnerPy,
  });
  // the LitBank mode is offered only when the bundle has the model (web/build.sh copies it if exported)
  let litbankBytes = 0;
  try {
    const r = await fetch(new URL("coref.json", modelBase("coref/en")).href, { cache: "no-cache" });
    if (r.ok) litbankBytes = Object.values((await r.json()).models).flat().reduce((n, p) => n + p.size, 0);
  } catch { litbankBytes = 0; }
  post("ready", { modes: index.modes, excluded: index.excluded, version: index.version, litbankBytes });
}

// Browser models that stand in for a pair's NLP service (build_modes.py BROWSER_NLP),
// loaded once, the first time a mode needs them. Without them the steps fall back.
const NLP = {
  eng: async () => {
    post("status", { text: "Loading the English tagger and parser…" });
    const ort = await import("./ort/ort.wasm.min.mjs");
    ort.env.wasm.wasmPaths = new URL("ort/", self.location.href).href;
    ort.env.wasm.numThreads = 1;          // threads need cross-origin isolation
    return new EnglishTagger().load(modelBase("tagger/en"), ort,
      (url) => bytes(url));
  },
};
const nlpLoading = {};

// LitBank mode (src/coref.mjs): an opt-in coreference model for eng->glb, ~120 MB, loaded the
// first time the page switches it on and then cached like the pair files.
let litbank = null, litbankLoading = null;
async function setLitbank(on, profile) {
  const tagger = translator.nlp.eng;
  if (!tagger) return;
  if (!on) { tagger.setCoref(null); return; }
  if (!litbankLoading) {
    litbankLoading = (async () => {
      post("status", { text: "Loading the LitBank coreference model…" });
      const ort = await import("./ort/ort.wasm.min.mjs");
      return new LitBankCoref().load(modelBase("coref/en"), ort, (url) => bytes(url),
        (done, total) => post("progress", { mode: "LitBank model", done, total }),
        async (url) => {
          const r = await fetch(url, { cache: "no-cache" });
          if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
          return new Uint8Array(await r.arrayBuffer());
        });
    })().then((m) => { litbank = m; return m; })
      .catch((err) => { litbankLoading = null;
        post("status", { text: `(fallback: LitBank model failed to load: ${err.message || err})` }); });
  }
  const m = await litbankLoading;
  if (!m) return;
  if (profile && PROFILES[profile]) m.profile = profile;
  tagger.setCoref(m);
}

async function load(mode) {
  if (translator.modes.has(mode)) return post("loaded", { mode });
  const manifest = await (await fetch(`pairs/${mode}.json`)).json();
  for (const lang of new Set(manifest.steps.filter((s) => s.browser_nlp).map((s) => s.browser_nlp.lang))) {
    if (NLP[lang] && !nlpLoading[lang]) {
      nlpLoading[lang] = NLP[lang]().then((a) => translator.setNlp(lang, a))
        .catch((err) => post("status", { text: `(fallback: ${lang} tagger failed to load: ${err.message || err})` }));
    }
    await nlpLoading[lang];
  }
  await translator.loadMode(manifest, (f) => bytes(`pairs/${f.url}`),
    (done, total) => post("progress", { mode, done, total }));
  post("loaded", { mode });
}

self.onmessage = async (e) => {
  const { type, id } = e.data;
  try {
    if (type === "init") await init();
    else if (type === "load") await load(e.data.mode);
    else if (type === "translate") {
      await load(e.data.mode);
      await setLitbank(Boolean(e.data.litbank), e.data.profile);
      const t0 = performance.now();
      const r = await translator.translate(e.data.mode, e.data.text, e.data.setvar || "");
      post("result", { id, ...r, ms: Math.round(performance.now() - t0) });
    }
  } catch (err) {
    post("error", { id, message: String(err && err.message || err), step: err && err.step });
  }
};
