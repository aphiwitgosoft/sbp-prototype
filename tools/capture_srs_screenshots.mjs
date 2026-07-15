#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const root = "/Users/bank_mac/gosoft/java/SBP/sbp-prototype";
const outDir = path.join(root, "output", "srs", "screenshots", "full");
fs.mkdirSync(outDir, { recursive: true });

const pages = [
  "index.html",
  "flow-fgi.html",
  "k2-flow.html",
  "plan-flow.html",
  "fgi-database.html",
  "k2-database.html",
  "plan-database.html",
  "job-batch.html",
  "k2-create.html",
  "k2-list-waiting.html",
  "k2-list-related.html",
  "k2-list-abnormal.html",
  "k2-document.html",
  "k2-report.html",
  "k2-operators.html",
  "k2-factors.html",
  "k2-permissions.html",
  "system-config.html",
  "plan-email.html",
  "plan-api.html",
];

class CDP {
  constructor(url) {
    this.nextId = 1;
    this.pending = new Map();
    this.waiters = new Map();
    this.ws = new WebSocket(url);
  }

  async open() {
    await new Promise((resolve, reject) => {
      this.ws.addEventListener("open", resolve, { once: true });
      this.ws.addEventListener("error", reject, { once: true });
    });
    this.ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      } else if (msg.method && this.waiters.has(msg.method)) {
        const waiters = this.waiters.get(msg.method);
        this.waiters.delete(msg.method);
        for (const resolve of waiters) resolve(msg.params);
      }
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }

  wait(method, timeoutMs = 15000) {
    return new Promise((resolve, reject) => {
      const list = this.waiters.get(method) || [];
      list.push(resolve);
      this.waiters.set(method, list);
      setTimeout(() => reject(new Error(`Timeout waiting for ${method}`)), timeoutMs);
    });
  }

  close() {
    this.ws.close();
  }
}

async function createTarget() {
  const response = await fetch("http://127.0.0.1:9222/json/new?about:blank", { method: "PUT" });
  if (!response.ok) throw new Error(`Cannot create Chrome target: ${response.status}`);
  return response.json();
}

async function closeTarget(id) {
  await fetch(`http://127.0.0.1:9222/json/close/${id}`);
}

async function capture(file) {
  const target = await createTarget();
  const cdp = new CDP(target.webSocketDebuggerUrl);
  await cdp.open();
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 1000,
    deviceScaleFactor: 1,
    mobile: false,
  });
  const loaded = cdp.wait("Page.loadEventFired");
  await cdp.send("Page.navigate", { url: `http://127.0.0.1:8000/${file}` });
  await loaded;
  await cdp.send("Runtime.evaluate", {
    expression: "document.fonts ? document.fonts.ready.then(() => true) : true",
    awaitPromise: true,
    returnByValue: true,
  });
  await cdp.send("Runtime.evaluate", {
    expression: `(() => {
      const style = document.createElement('style');
      style.textContent = 'header.app-header,#roleBar{position:static!important;top:auto!important} aside.sidebar{position:static!important;top:auto!important;align-self:stretch!important;min-height:100%!important}';
      document.head.appendChild(style);
      return true;
    })()`,
    returnByValue: true,
  });
  if (file === "job-batch.html") {
    await cdp.send("Runtime.evaluate", {
      expression: "document.querySelector('#tblJobs tbody tr[data-job=\"1\"]')?.click(); true",
      returnByValue: true,
    });
  }
  await new Promise((resolve) => setTimeout(resolve, 500));
  const metrics = await cdp.send("Page.getLayoutMetrics");
  const width = Math.ceil(metrics.cssContentSize.width);
  const height = Math.ceil(metrics.cssContentSize.height);
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await new Promise((resolve) => setTimeout(resolve, 250));
  const shot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
    clip: { x: 0, y: 0, width, height, scale: 1 },
  });
  const filename = file.replace(/\.html$/, ".png");
  fs.writeFileSync(path.join(outDir, filename), Buffer.from(shot.data, "base64"));
  cdp.close();
  await closeTarget(target.id);
  return { file, width, height, output: filename };
}

const results = [];
for (const file of pages) {
  results.push(await capture(file));
}
fs.writeFileSync(
  path.join(root, "output", "srs", "screenshots", "manifest.json"),
  JSON.stringify(results, null, 2),
  "utf8",
);
console.log(JSON.stringify(results, null, 2));
