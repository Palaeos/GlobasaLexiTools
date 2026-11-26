// End-to-end check in headless Chromium: serve web/dist, translate one sentence per given
// mode through the page itself, print output, notes and timings; a second page load in the
// same profile reports how many pair files came from the Cache API.
//   python3 web/test/capped.py node web/test/browser.mjs [mode ...]
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(here, "..", "dist");
const PORT = 8731, DBG = 9231;
const SAMPLES = {
  "eng-glb": "The old man saw that the strange thing was in the garden.",
  "glb-eng": "Mi le oko yu in jarden.",
  "fra-glb": "Le petit prince regardait les étoiles.",
  "epo-glb": "La junaj vulpoj, kiuj neniam vidis neĝon antaŭe, tuj volas ludi en ĝi.",
};
const modes = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(SAMPLES);

const server = spawn("python3", ["-m", "http.server", String(PORT), "-d", dist, "-b", "127.0.0.1"], { stdio: "ignore" });
const profile = mkdtempSync(path.join(tmpdir(), "glb-chrome-"));
const chrome = spawn("chromium", ["--headless=new", `--remote-debugging-port=${DBG}`, `--user-data-dir=${profile}`,
  "--no-first-run", "--disable-gpu", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function cdp() {
  for (let i = 0; i < 50; i++) {
    try {
      const tabs = await (await fetch(`http://127.0.0.1:${DBG}/json`)).json();
      const page = tabs.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* not up yet */ }
    await sleep(200);
  }
  throw new Error("chromium did not start");
}

const ws = new WebSocket(await cdp());
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let n = 0;
const pending = new Map();
const logs = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === "Runtime.consoleAPICalled") logs.push(m.params.args.map((a) => a.value).join(" "));
  if (m.method === "Runtime.exceptionThrown") logs.push("EXCEPTION " + m.params.exceptionDetails.text);
});
const send = (method, params = {}) => new Promise((r) => { const id = ++n; pending.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
async function until(expr, ms = 120000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { const v = await evaluate(expr); if (v) return v; await sleep(250); }
  throw new Error(`timeout waiting for ${expr}; status: ${await evaluate('document.getElementById("status").textContent')}`);
}

await send("Runtime.enable");
let code = 0;
try {
  for (const pass of [1, 2]) {
    const t0 = Date.now();
    await send("Page.navigate", { url: `http://127.0.0.1:${PORT}/` });
    await until('document.getElementById("status").textContent.startsWith("Ready")');
    console.log(`pass ${pass}: page ready in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
    for (const mode of (pass === 1 ? modes : modes.slice(0, 1))) {
      const t1 = Date.now();
      await evaluate(`(() => { const s = document.getElementById("mode"); s.value = ${JSON.stringify(mode)};
        s.dispatchEvent(new Event("change")); document.getElementById("src").value = ${JSON.stringify(SAMPLES[mode] || "Test.")};
        document.getElementById("out").textContent = ""; document.getElementById("go").click(); return true; })()`);
      await until('document.getElementById("status").textContent.startsWith("Translated") || document.getElementById("status").className.includes("err")');
      const st = await evaluate('document.getElementById("status").textContent');
      const out = await evaluate('document.getElementById("out").textContent');
      const notes = await evaluate('document.getElementById("notes").hidden ? "" : document.getElementById("notes").textContent');
      if (st.startsWith("Error")) code = 1;
      console.log(`  ${mode}: ${((Date.now() - t1) / 1000).toFixed(1)} s incl. loading — ${st}\n    → ${out}${notes ? `\n    notes: ${notes.slice(0, 300)}` : ""}`);
    }
    const cached = await evaluate(`(async () => { const ks = await caches.keys(); let n = 0;
      for (const k of ks) n += (await (await caches.open(k)).keys()).length; return ks.join(",") + " " + n + " files"; })()`);
    console.log(`  cache: ${cached}`);
  }
} catch (e) { console.log("FAIL", e.message); code = 1; }
if (logs.length) console.log("console:", logs.slice(0, 10).join("\n  "));
ws.close(); chrome.kill(); server.kill();
process.exit(code);
