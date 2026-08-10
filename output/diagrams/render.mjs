#!/usr/bin/env node
/* เรนเดอร์ไฟล์ HTML ในโฟลเดอร์นี้เป็น PNG ความละเอียด 2 เท่า
   ต้องมี (1) python3 -m http.server 8000 ที่ root ของ repo
          (2) Chrome headless เปิดพอร์ต debug 9222
   ใช้:  node output/diagrams/render.mjs <ชื่อไฟล์.html> <selector> <ชื่อไฟล์ออก.png> */

import fs from "node:fs";
import path from "node:path";

const root = "/Users/bank_mac/gosoft/java/SBP/sbp-prototype";
const [file, selector = "#sheet", out] = process.argv.slice(2);
if (!file || !out) {
  console.error("ใช้: node output/diagrams/render.mjs <file.html> <selector> <out.png>");
  process.exit(1);
}
const outDir = path.join(root, "output", "diagrams");

class CDP {
  constructor(url) { this.nextId = 1; this.pending = new Map(); this.ws = new WebSocket(url); }
  async open() {
    await new Promise((res, rej) => {
      this.ws.addEventListener("open", res, { once: true });
      this.ws.addEventListener("error", rej, { once: true });
    });
    this.ws.addEventListener("message", (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      }
    });
  }
  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
  close() { this.ws.close(); }
}

const target = await (await fetch("http://127.0.0.1:9222/json/new?about:blank", { method: "PUT" })).json();
const cdp = new CDP(target.webSocketDebuggerUrl);
await cdp.open();
await cdp.send("Page.enable");
await cdp.send("Runtime.enable");
await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1700, height: 1400, deviceScaleFactor: 2, mobile: false });
await cdp.send("Page.navigate", { url: `http://127.0.0.1:8000/output/diagrams/${file}?t=${Date.now()}` });
await new Promise((r) => setTimeout(r, 2200));
await cdp.send("Runtime.evaluate", {
  expression: "document.fonts ? document.fonts.ready.then(()=>true) : true",
  awaitPromise: true, returnByValue: true,
});
await new Promise((r) => setTimeout(r, 400));

const box = await cdp.send("Runtime.evaluate", {
  expression: `(() => { const e=document.querySelector(${JSON.stringify(selector)});
    if(!e) return null; const r=e.getBoundingClientRect();
    return {x:r.left+window.scrollX, y:r.top+window.scrollY, w:r.width, h:r.height}; })()`,
  returnByValue: true,
});
if (!box.result.value) throw new Error("ไม่พบ element " + selector);
const c = box.result.value;
const pad = 28;
const shot = await cdp.send("Page.captureScreenshot", {
  format: "png", fromSurface: true, captureBeyondViewport: true,
  clip: {
    x: Math.max(0, Math.round(c.x - pad)), y: Math.max(0, Math.round(c.y - pad)),
    width: Math.round(c.w + pad * 2), height: Math.round(c.h + pad * 2), scale: 2,
  },
});
fs.writeFileSync(path.join(outDir, out), Buffer.from(shot.data, "base64"));
cdp.close();
await fetch(`http://127.0.0.1:9222/json/close/${target.id}`);
console.log(`${out} · ${Math.round(c.w + pad * 2)}x${Math.round(c.h + pad * 2)} css px (PNG 2x)`);
