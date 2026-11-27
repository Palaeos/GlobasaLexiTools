// Translation worker: loads the wasm tools, Pyodide and a mode's files on demand, and
// runs the mode (src/pipeline.mjs) off the page's main thread.
// Pair files are kept in the Cache API under the bundle version, so a second visit
// loads them from disk; a rebuilt bundle has a new version and replaces the old cache.
import { Translator } from "./src/pipeline.mjs";
import { EnglishTagger } from "./src/tagger.mjs";
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

async function init() {
  index = await (await fetch("pairs/index.json", { cache: "no-cache" })).json();
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
  post("ready", { modes: index.modes, excluded: index.excluded, version: index.version });
}

// Browser models that stand in for a pair's NLP service (build_modes.py BROWSER_NLP),
// loaded once, the first time a mode needs them. Without them the steps fall back.
const NLP = {
  eng: async () => {
    post("status", { text: "Loading the English tagger and parser…" });
    const ort = await import("./ort/ort.wasm.min.mjs");
    ort.env.wasm.wasmPaths = new URL("ort/", self.location.href).href;
    ort.env.wasm.numThreads = 1;          // threads need cross-origin isolation
    return new EnglishTagger().load(new URL("tagger/en/", self.location.href).href, ort,
      (url) => bytes(url));
  },
};
const nlpLoading = {};

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
      const t0 = performance.now();
      const r = await translator.translate(e.data.mode, e.data.text, e.data.setvar || "");
      post("result", { id, ...r, ms: Math.round(performance.now() - t0) });
    }
  } catch (err) {
    post("error", { id, message: String(err && err.message || err), step: err && err.step });
  }
};
