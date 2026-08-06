#!/usr/bin/env node
/* จับภาพ modal / popup validation / แถบเลือกรายการ ของ prototype สำหรับใส่ในเอกสาร SRS
   ต้องมี  (1) python3 -m http.server 8000  ที่ root ของ repo
           (2) Chrome headless เปิดพอร์ต debug 9222
   ผลลัพธ์: output/srs/screenshots/modals/*.png  (crop เฉพาะกล่อง modal + ระยะขอบ) */

import fs from "node:fs";
import path from "node:path";

const root = "/Users/bank_mac/gosoft/java/SBP/sbp-prototype";
const outDir = path.join(root, "output", "srs", "screenshots", "modals");
fs.mkdirSync(outDir, { recursive: true });

/* แต่ละ shot: เปิดหน้า → รัน setup (async) → รอ → crop ตาม selector */
const shots = [
  {
    file: "k2-document.html",
    out: "modal-add-competitor.png",
    title: "Modal เพิ่มร้านคู่แข่งเปิดกระทบ",
    clip: "#modalOverlay .modal",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='opt-mgr'; s.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,250));
      document.querySelector('#sec-competitor [data-add-row]').click();`,
  },
  {
    file: "k2-document.html",
    out: "modal-edit-factor.png",
    title: "Modal แก้ไขปัจจัยอื่น ๆ",
    clip: "#modalOverlay .modal",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='opt-mgr'; s.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,250));
      document.querySelector('#sec-factor tbody .icon-edit').click();`,
  },
  {
    file: "k2-document.html",
    out: "modal-attach-file.png",
    title: "Modal แนบเอกสาร",
    clip: "#attachPop .modal",
    setup: `document.getElementById('btnAttachAll').click();`,
  },
  {
    file: "k2-document.html",
    out: "modal-attach-detail.png",
    title: "Modal รายละเอียดไฟล์แนบ + ปุ่มดาวน์โหลด",
    clip: "#attFilePop .modal",
    setup: `document.querySelector('#tbAttachBody tr').click();`,
  },
  {
    file: "k2-document.html",
    out: "modal-decision-history.png",
    title: "Modal รายละเอียดผลการพิจารณา (ประวัติ)",
    clip: "#decHistPop .modal",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='avp'; s.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,300));
      document.querySelector('#tbDecHistBody tr[data-idx]').click();`,
  },
  {
    file: "k2-document.html",
    out: "validate-percent-100.png",
    title: "Validation: %ชดเชยรวมไม่เท่ากับ 100%",
    clip: "#k2pop .k2pop",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='opt-mgr'; s.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,250));
      document.querySelectorAll('#tbldocument_new_stores .pct-input')[1].value='55.00';
      document.getElementById('btnNsCalc').click();`,
  },
  {
    file: "k2-document.html",
    out: "validate-no-decision.png",
    title: "Validation: ยังไม่เลือกผลการพิจารณา",
    clip: "#k2pop .k2pop",
    setup: `document.getElementById('btnDecSend').click();`,
  },
  {
    file: "k2-document.html",
    out: "validate-competitor-required.png",
    title: "Validation: ยังไม่เลือกร้านคู่แข่ง",
    clip: "#k2pop .k2pop",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='opt-mgr'; s.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,250));
      document.querySelector('#sec-competitor [data-add-row]').click();
      await new Promise(r=>setTimeout(r,350));
      const btns=[...document.querySelectorAll('#modalOverlay .modal-foot .btn')];
      btns[btns.length-1].click();`,
  },
  {
    file: "k2-document.html",
    out: "confirm-bulk-delete.png",
    title: "Popup ยืนยันลบรายการที่เลือก",
    clip: "#k2pop .k2pop",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='opt-mgr'; s.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,250));
      const all=document.querySelector('#tblCompetitor thead .cbx');
      all.checked=true; all.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,150));
      document.querySelector('#sec-competitor [data-bulk="del"]').click();`,
  },
  {
    file: "k2-document.html",
    out: "section-bulk-bar.png",
    title: "แถบดำเนินการกับรายการที่เลือก (ร้านคู่แข่งเปิดกระทบ)",
    clip: "#sec-competitor",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='opt-mgr'; s.dispatchEvent(new Event('change'));
      await new Promise(r=>setTimeout(r,250));
      const cb=document.querySelector('#tblCompetitor tbody .cbx');
      cb.checked=true; cb.dispatchEvent(new Event('change',{bubbles:true}));`,
  },
  {
    file: "k2-document.html",
    out: "section-calc-fs-iframe.png",
    title: "ส่วนคำนวณเงินชดเชย (iframe ของระบบ FS)",
    clip: "#sec-calc",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='sbpdsa-officer'; s.dispatchEvent(new Event('change'));`,
  },
  {
    file: "k2-document.html",
    out: "section-decision-panel.png",
    title: "แผงพิจารณา (ส่งดำเนินการ)",
    clip: "#sec-decision",
    setup: `
      const s=document.getElementById('roleSwitch'); s.value='opt-mgr'; s.dispatchEvent(new Event('change'));`,
  },
  {
    file: "k2-list-waiting.html",
    out: "list-quickbar.png",
    title: "แถบ Selected Filter + Quick Search",
    clip: ".quickbar",
    setup: `
      document.getElementById('qsText').value='RSU';
      document.getElementById('qsText').dispatchEvent(new Event('input'));`,
  },
  {
    file: "flow-srs.html",
    out: "flow-phase-1.png",
    title: "รูปที่ 1 ระยะที่ 1 — รับข้อมูลผลกระทบและคำนวณยอดขาย",
    clip: ".figwrap:nth-of-type(1)",
    setup: `true;`,
  },
  {
    file: "flow-srs.html",
    out: "flow-phase-2.png",
    title: "รูปที่ 2 ระยะที่ 2 — สร้างเอกสารและพิจารณาอนุมัติ",
    clip: ".figwrap:nth-of-type(2)",
    setup: `true;`,
  },
  {
    file: "flow-srs.html",
    out: "flow-phase-3.png",
    title: "รูปที่ 3 ระยะที่ 3 — ส่งผลชดเชยและกระทบยอดบัญชี",
    clip: ".figwrap:nth-of-type(3)",
    setup: `true;`,
  },
  {
    file: "k2-competitors.html",
    out: "modal-add-competitor-master.png",
    title: "Modal เพิ่มรายชื่อคู่แข่ง (master)",
    clip: "#modalOverlay .modal",
    setup: `document.querySelector('[data-add-row="tblCompetitorMaster"]').click();`,
  },
  {
    file: "k2-factors.html",
    out: "modal-add-factor-master.png",
    title: "Modal เพิ่มปัจจัยภายนอก (master)",
    clip: "#modalOverlay .modal",
    setup: `document.querySelector('[data-add-row="tblFactors"]').click();`,
  },
];

class CDP {
  constructor(url) {
    this.nextId = 1;
    this.pending = new Map();
    this.ws = new WebSocket(url);
  }
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

async function newTarget() {
  const r = await fetch("http://127.0.0.1:9222/json/new?about:blank", { method: "PUT" });
  if (!r.ok) throw new Error("cannot create target: " + r.status);
  return r.json();
}
const closeTarget = (id) => fetch(`http://127.0.0.1:9222/json/close/${id}`);

async function capture(shot) {
  const target = await newTarget();
  const cdp = new CDP(target.webSocketDebuggerUrl);
  await cdp.open();
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1400, deviceScaleFactor: 2, mobile: false });
  await cdp.send("Page.navigate", { url: `http://127.0.0.1:8000/${shot.file}?srs=${Date.now()}` });
  await new Promise((r) => setTimeout(r, 1400));
  await cdp.send("Runtime.evaluate", {
    expression: "document.fonts ? document.fonts.ready.then(()=>true) : true",
    awaitPromise: true, returnByValue: true,
  });
  /* บังคับให้การ์ดที่ใช้ reveal แสดงผลทันที (ไม่ต้องรอ scroll) */
  await cdp.send("Runtime.evaluate", {
    expression: `document.querySelectorAll('.reveal').forEach(function(e){e.classList.add('in');}); true`,
    returnByValue: true,
  });
  const res = await cdp.send("Runtime.evaluate", {
    expression: `(async () => { ${shot.setup}\n await new Promise(r=>setTimeout(r,600)); return true; })()`,
    awaitPromise: true, returnByValue: true,
  });
  if (res.exceptionDetails) throw new Error(shot.out + " setup failed: " + JSON.stringify(res.exceptionDetails));
  await new Promise((r) => setTimeout(r, 350));

  const box = await cdp.send("Runtime.evaluate", {
    expression: `(() => { const e=document.querySelector(${JSON.stringify(shot.clip)});
      if(!e) return null; const r=e.getBoundingClientRect();
      return {x:Math.max(0,r.left-14), y:Math.max(0,r.top-14), w:r.width+28, h:r.height+28}; })()`,
    returnByValue: true,
  });
  if (!box.result.value) throw new Error(shot.out + ": ไม่พบ element " + shot.clip);
  const c = box.result.value;
  const shotData = await cdp.send("Page.captureScreenshot", {
    format: "png", fromSurface: true, captureBeyondViewport: true,
    clip: { x: Math.round(c.x), y: Math.round(c.y), width: Math.round(c.w), height: Math.round(c.h), scale: 2 },
  });
  fs.writeFileSync(path.join(outDir, shot.out), Buffer.from(shotData.data, "base64"));
  cdp.close();
  await closeTarget(target.id);
  return { out: shot.out, title: shot.title, w: Math.round(c.w), h: Math.round(c.h) };
}

const done = [];
for (const shot of shots) {
  try { done.push(await capture(shot)); }
  catch (e) { console.error("FAIL", shot.out, e.message); }
}
fs.writeFileSync(path.join(outDir, "manifest.json"), JSON.stringify(done, null, 2), "utf8");
console.log(JSON.stringify(done, null, 2));
