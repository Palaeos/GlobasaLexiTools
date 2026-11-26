// Runs a Globasa mode from its manifest (web/build_modes.py): wasm tools and the
// pairs' own Python steps (in Pyodide), passing the stream as strings.
// Used by the page's worker (web/worker.js) and the Node tests (web/test/).
import { initTools, runToolSync, setIcuData } from "./tools.mjs";

const STREAMCMD_RE = /\[<STREAMCMD:[^\]]*>\]/g;
export const BROWSER_FALLBACK = "no neural service in browser";

export class Translator {
  // opts: {wasm, mjs, icu: Uint8Array, pyodide: loaded Pyodide instance, runnerPy: source text}
  async init(opts) {
    await initTools(opts.wasm, opts.mjs);
    setIcuData(opts.icu, null, opts.nfcn);
    this.py = opts.pyodide;
    this.files = new Map();           // /p/... -> Uint8Array (wasm tools)
    this.inPy = new Set();            // paths already written to Pyodide's FS
    globalThis.globasa_run_tool = (tool, args, input) => runToolSync(tool, [...args], input, this.files);
    this.py.FS.mkdirTree("/web");
    this.py.FS.writeFile("/web/runner.py", opts.runnerPy);
    this.py.runPython("import sys; sys.path.insert(0, '/web'); import runner");
    const runner = this.py.globals.get("runner");
    this.runStep = runner.run_step;
    this.addAnalysis = runner.add_analysis;
    this.needAnalysis = runner.NEED_ANALYSIS;
    this.modes = new Map();
    this.nlp = {};                    // lang -> {analyze(text) -> Promise<result>}
  }

  // A browser model standing in for a pipeline's NLP service (src/tagger.mjs for eng).
  setNlp(lang, analyzer) { this.nlp[lang] = analyzer; }

  // manifest: parsed <mode>.json; fetchFile(entry) -> Promise<Uint8Array>
  async loadMode(manifest, fetchFile, onProgress = () => {}) {
    let done = 0;
    const total = manifest.files.reduce((n, f) => n + f.size, 0);
    await Promise.all(manifest.files.map(async (f) => {
      if (!this.files.has(f.path)) {
        const bytes = await fetchFile(f);
        this.files.set(f.path, bytes);
      }
      if (!this.inPy.has(f.path)) {
        this.py.FS.mkdirTree(f.path.slice(0, f.path.lastIndexOf("/")));
        this.py.FS.writeFile(f.path, this.files.get(f.path));
        this.inPy.add(f.path);
      }
      done += f.size;
      onProgress(done, total);
    }));
    this.modes.set(manifest.mode, manifest);
  }

  // Returns {output, notes: [string], steps: [{name, ms}]}.
  // setvar: AP_SETVAR string ("story,eng_variety=US"), as the apertium wrapper uses it:
  // in the environment of the Python steps and as a stream command for the tools.
  async translate(mode, text, setvar = "") {
    const m = this.modes.get(mode);
    if (!m) throw new Error(`mode not loaded: ${mode}`);
    // As the apertium command: text (newline-terminated) -> apertium-destxt; the SETVAR
    // stream command goes in after destxt and is removed again before apertium-retxt.
    let stream = text + (text.endsWith("\n") ? "" : "\n");
    const notes = [], steps = [];
    for (const s of m.steps) {
      if (s.tool === "apertium-retxt") stream = stream.replace(STREAMCMD_RE, "");
      const t0 = performance.now();
      let name, r;
      if (s.tool) {
        name = `${s.tool} ${s.args.filter((a) => a.startsWith("-")).join(" ")}`.trim();
        r = runToolSync(s.tool, s.args, stream, this.files);
      } else {
        name = `${s.py.split("/").pop()} ${s.args.join(" ")}`.trim();
        const env = { AP_SETVAR: setvar };
        const browser = s.browser_nlp && this.nlp[s.browser_nlp.lang] ? s.browser_nlp : null;
        if (browser) {
          Object.assign(env, browser.env);
          notes.push(`${name}: ${browser.note} (fallback: no parser in browser)`);
        } else if (s.neural) {
          env[s.neural] = "0";
          notes.push(`${name}: (fallback: ${BROWSER_FALLBACK}; rule-based only)`);
        }
        // a browser-model request the page has no analysis for yet: analyse, run again
        for (;;) {
          const res = this.runStep(s.py, this.py.toPy(s.args), stream, this.py.toPy(env));
          const out = res.toJs();
          res.destroy();
          if (browser && out[0] === this.needAnalysis) {
            const [, url, req] = out;
            const analysis = await this.nlp[browser.lang].analyze(req);
            this.addAnalysis(url, req, JSON.stringify(analysis));
            continue;
          }
          const [status, stdout, stderr] = out;
          r = { status, stdout, stderr };
          break;
        }
      }
      steps.push({ name, ms: Math.round(performance.now() - t0) });
      for (const line of (r.stderr || "").split("\n")) {
        if (line.includes("fallback")) notes.push(line.trim());
      }
      if (r.status) {
        const e = new Error(`${name} failed (exit ${r.status}): ${(r.stderr || "").trim().split("\n").slice(-3).join(" | ")}`);
        e.step = name;
        throw e;
      }
      stream = r.stdout;
      if (s.tool === "apertium-destxt" && setvar) stream = `[<STREAMCMD:SETVAR:${setvar}>]` + stream;
    }
    return { output: stream.replace(STREAMCMD_RE, "").trim(), notes, steps };
  }
}
