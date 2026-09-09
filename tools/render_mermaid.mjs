#!/usr/bin/env node
/* render_mermaid.mjs — render ไฟล์ .mmd เป็น .svg + .png ด้วย mermaid ผ่าน Chrome headless
 *
 * ใช้เมื่อ: แก้ new-flow-improved.mmd แล้วต้องอัปเดตภาพให้ตรงกัน
 *
 *   1) python3 -c "import pathlib;m=pathlib.Path('new-flow-improved.mmd').read_text();\
 *        pathlib.Path('/tmp/m/mermaid-render.html').write_text(open('tools/mermaid-page.tpl').read().replace('__MMD__', m))"
 *      (หรือประกอบหน้า HTML ที่ฝัง .mmd ไว้ใน div.mermaid เองก็ได้)
 *   2) cd <dir ที่มีหน้า HTML> && python3 -m http.server 8788
 *   3) "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
 *        --remote-debugging-port=9223 --user-data-dir=/tmp/mmd-profile about:blank
 *   4) node tools/render_mermaid.mjs <out.svg> <out.png>
 *
 * หมายเหตุ: mermaid โหลดจาก cdnjs ตอน render เท่านั้น — ไฟล์ผลลัพธ์ไม่มี dependency ภายนอก
 *          และ prototype ยังทำงาน offline ตามเดิม
 */
import fs from "node:fs";
const HOST = "http://127.0.0.1:9223";
const nf = await fetch(`${HOST}/json/new?about:blank`, { method: "PUT" }).then(r => r.json());
class CDP {
  constructor(url){ this.id=1; this.p=new Map(); this.w=new Map(); this.ws=new WebSocket(url); }
  async open(){ await new Promise((res,rej)=>{this.ws.addEventListener("open",res,{once:true});this.ws.addEventListener("error",rej,{once:true});});
    this.ws.addEventListener("message",e=>{const m=JSON.parse(e.data);
      if(m.id&&this.p.has(m.id)){const{resolve,reject}=this.p.get(m.id);this.p.delete(m.id);m.error?reject(new Error(JSON.stringify(m.error))):resolve(m.result);}
      else if(m.method&&this.w.has(m.method)){const l=this.w.get(m.method);this.w.delete(m.method);l.forEach(r=>r(m.params));}});}
  send(method,params={}){const id=this.id++;this.ws.send(JSON.stringify({id,method,params}));return new Promise((resolve,reject)=>this.p.set(id,{resolve,reject}));}
  wait(m,t=30000){return new Promise((res,rej)=>{const l=this.w.get(m)||[];l.push(res);this.w.set(m,l);setTimeout(()=>rej(new Error("timeout "+m)),t);});}
}
const cdp = new CDP(nf.webSocketDebuggerUrl); await cdp.open();
await cdp.send("Page.enable"); await cdp.send("Runtime.enable");
await cdp.send("Emulation.setDeviceMetricsOverride",{width:1600,height:1200,deviceScaleFactor:2,mobile:false});
const loaded = cdp.wait("Page.loadEventFired");
await cdp.send("Page.navigate",{url:"http://127.0.0.1:8788/mermaid-render.html"});
await loaded;
for (let i=0;i<60;i++){
  const r = await cdp.send("Runtime.evaluate",{expression:"window.__done?'done':(window.__err||'wait')",returnByValue:true});
  if (r.result.value==="done") break;
  if (r.result.value!=="wait"){ console.error("MERMAID ERROR:", r.result.value); process.exit(1); }
  await new Promise(r=>setTimeout(r,500));
}
// ใส่ width/height จริงลง <svg> ก่อนบันทึก — mermaid ออก width="100%" ซึ่งทำให้ <img> หาขนาด intrinsic ไม่ได้
const fixExpr = "(()=>{const s=document.querySelector('#d svg');const v=s.getAttribute('viewBox').trim().split(' ').map(Number);" + "s.setAttribute('width',v[2]);s.setAttribute('height',v[3]);s.style.maxWidth='100%';s.style.height='auto';return s.outerHTML;})()";
const svg = await cdp.send("Runtime.evaluate",{expression: fixExpr, returnByValue:true});
fs.writeFileSync(process.argv[2], svg.result.value);
// ขนาดจริงของแผนภาพ = viewBox ของ svg (getLayoutMetrics คืนขนาด viewport ที่ override ไว้)
const box = await cdp.send("Runtime.evaluate",{expression: "(()=>{const s=document.querySelector('#d svg');const v=s.getAttribute('viewBox').trim().split(' ').map(Number);s.setAttribute('width',v[2]);s.setAttribute('height',v[3]);s.style.maxWidth='none';return JSON.stringify({w:Math.ceil(v[2])+48,h:Math.ceil(v[3])+48});})()", returnByValue:true});
const {w, h} = JSON.parse(box.result.value);
await cdp.send("Emulation.setDeviceMetricsOverride",{width:w,height:h,deviceScaleFactor:2,mobile:false});
await new Promise(r=>setTimeout(r,400));
const shot = await cdp.send("Page.captureScreenshot",{format:"png",fromSurface:true,captureBeyondViewport:false,clip:{x:0,y:0,width:w,height:h,scale:1}});
fs.writeFileSync(process.argv[3], Buffer.from(shot.data,"base64"));
console.log("svg+png ok", w+"x"+h);
await fetch(`${HOST}/json/close/${nf.id}`);
