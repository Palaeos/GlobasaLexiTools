// Runs the Apertium processors of the multicall wasm binary (web/wasm/).
// One fresh module instance per call, from one compiled WebAssembly.Module:
// the tools keep getopt and static state, and exit() ends the runtime, so a
// reused instance would leak state from one pipeline step into the next.
// Calls are synchronous (WASM_ASYNC_COMPILATION=0 + Module.wasmModule, see
// build_wasm.sh), so Python steps can call the tools through subprocess.
// Works in a browser worker and in Node (web/test/).

let compiled = null;   // WebAssembly.Module
let factory = null;    // createApertium

export async function initTools(wasmUrl, mjsUrl) {
  factory = (await import(mjsUrl)).default;
  if (wasmUrl instanceof Uint8Array || wasmUrl instanceof ArrayBuffer) {
    compiled = await WebAssembly.compile(wasmUrl);
  } else if (typeof process !== "undefined" && process.versions?.node && !String(wasmUrl).startsWith("http")) {
    const { readFile } = await import("node:fs/promises");
    compiled = await WebAssembly.compile(await readFile(wasmUrl));
  } else {
    compiled = await WebAssembly.compileStreaming(fetch(wasmUrl));
  }
}

// ICU data. The Emscripten icu port is built with stub data, and ICU's formatted
// I/O (u_sscanf, u_fprintf with numbers: StringUtils::stoi, cg3 output) needs
// locale data, so the trimmed archive web/dist/wasm/icudt68l.dat is mounted at
// /icu and found through ICU_DATA. For tracing (web/wasm/icu_items.txt), a Map of
// item name -> bytes is mounted as loose files instead and every open is reported.
let icuData = null;          // Uint8Array (archive) or Map (loose items)
let icuTrace = null;         // fn(itemName) when tracing
let nfcn = null;             // nfcn.nrm for apertium-normalize, at /icu/nfcn.nrm
export function setIcuData(data, trace = null, nrm = null) { icuData = data; icuTrace = trace; if (nrm) nfcn = nrm; }

function mkdirs(FS, path) {
  const parts = path.split("/").slice(1, -1);
  let cur = "";
  for (const p of parts) {
    cur += "/" + p;
    try { FS.mkdir(cur); } catch { /* exists */ }
  }
}

function mountIcu(FS, ENV) {
  if (!icuData) return;
  FS.mkdir("/icu");
  if (icuData instanceof Map) {
    FS.mkdir("/icu/icudt68l");
    for (const [name, bytes] of icuData) {
      if (name.includes("/")) mkdirs(FS, "/icu/icudt68l/" + name);
      FS.writeFile("/icu/icudt68l/" + name, bytes);
    }
    const open = FS.open;
    FS.open = function (path, ...rest) {
      if (icuTrace && typeof path === "string" && path.startsWith("/icu/icudt68l/")) {
        icuTrace(path.slice("/icu/icudt68l/".length));
      }
      return open.call(this, path, ...rest);
    };
  } else {
    FS.writeFile("/icu/icudt68l.dat", icuData);
  }
  // apertium-normalize points ICU's data directory at its .nrm file's folder, so the
  // file sits next to the archive and the locale data stays reachable
  if (nfcn) FS.writeFile("/icu/nfcn.nrm", nfcn);
  ENV.ICU_DATA = "/icu";
}

// files: Map(path -> Uint8Array); the ones named in args are written into the
// instance's file system (the same /p/... paths the manifests use).
// Returns {stdout, stderr, status}.
export function runToolSync(tool, args, input, files) {
  if (!compiled) throw new Error("initTools() first");
  const err = [];
  const Module = {
    wasmModule: compiled,
    noInitialRun: true,
    print: () => {},
    printErr: (s) => err.push(s),
    // FS and ENV in preRun: libc copies the environment in a constructor that
    // runs before callMain, so ICU_DATA set afterwards would never be seen.
    preRun: [(M) => {
      mountIcu(M.FS, M.ENV);
      M.FS.mkdir("/io");
      M.FS.writeFile("/io/in", typeof input === "string" ? input : new Uint8Array(input));
      for (const a of args) {
        const data = files && files.get(a);
        if (data) { mkdirs(M.FS, a); M.FS.writeFile(a, data); }
      }
    }],
  };
  factory(Module);           // runs to completion synchronously (see header)
  if (!Module.callMain) throw new Error("wasm module did not initialise synchronously");
  let status = 0;
  try {
    status = Module.callMain([tool, ...args]) ?? 0;
  } catch (e) {
    if (e && e.name === "ExitStatus") status = e.status;
    else if (typeof e === "number") status = e;
    else if (typeof WebAssembly.Exception !== "undefined" && e instanceof WebAssembly.Exception
             && Module.getExceptionMessage) {
      err.push(`${tool}: uncaught C++ exception: ${Module.getExceptionMessage(e).filter(Boolean).join(": ")}`);
      status = 1;
    } else { err.push(`${tool}: ${e && e.stack || e}`); status = 1; }
  }
  let stdout = "";
  try { stdout = Module.FS.readFile("/io/out", { encoding: "utf8" }); } catch { /* no output */ }
  return { stdout, stderr: err.join("\n"), status };
}

export async function runTool(tool, args, input, files) {
  return runToolSync(tool, args, input, files);
}
