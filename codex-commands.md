# Codex commands quick reference

เอกสารนี้สรุปคำสั่งที่ใช้กับ Codex ใน 2 ระดับ:

1. Slash commands: พิมพ์ในช่องแชทของ Codex โดยขึ้นต้นด้วย `/`
2. CLI commands: รันใน shell ด้วยคำสั่ง `codex ...`

หมายเหตุ: รายการ slash commands อาจต่างกันตามเวอร์ชันและ surface ที่ใช้ เช่น CLI, Desktop app, หรือ IDE extension. เครื่องนี้ตรวจพบ `codex-cli 0.144.6`. วิธีเช็กที่แม่นสุดใน session ปัจจุบันคือพิมพ์ `/` เพื่อเปิด command popup และใช้ `Tab` เพื่อ autocomplete.

## Slash commands ที่ใช้บ่อย

| คำสั่ง | ใช้ทำอะไร | ใช้เมื่อไหร่ |
| --- | --- | --- |
| `/init` | สร้างไฟล์ `AGENTS.md` ใน directory ปัจจุบัน | เริ่ม repo ใหม่และอยากบันทึกกติกาถาวรให้ Codex อ่านในอนาคต |
| `/compact` | สรุปบทสนทนาเก่าเพื่อลด context/token ที่ใช้ | งานยาวมาก กลัว context เต็ม แต่ยังอยากให้ Codex จำประเด็นสำคัญ |
| `/new` | เริ่มแชทใหม่ใน session เดิม | เปลี่ยนไปทำงานคนละเรื่อง โดยยังไม่ต้องออกจาก Codex |
| `/clear` | ล้างหน้าจอและเริ่มแชทใหม่ | อยากเริ่มใหม่แบบเคลียร์บริบทในหน้าจอ |
| `/review` | ให้ Codex review current changes ใน git working tree | ก่อน commit หรือก่อนส่ง PR |
| `/diff` | แสดง git diff รวมไฟล์ untracked | ตรวจการแก้ไขที่ Codex หรือเราทำไว้ |
| `/status` | แสดง config/session/token usage | เช็ก model, permission, sandbox, และ usage |
| `/usage` | ดู account usage หรือ reset usage limit ถ้ามีให้ใช้ | เช็ก quota/usage ของบัญชีจากใน Codex |
| `/model` | เลือก model และ reasoning effort | เปลี่ยนรุ่น model ตามลักษณะงาน |
| `/permissions` | ตั้งค่าว่า Codex ทำอะไรได้โดยไม่ต้องถามก่อน | ปรับให้เข้มขึ้น/ผ่อนลงระหว่างทำงาน |
| `/skills` | ดูหรือเลือกใช้ skills | งานเฉพาะทาง เช่น PDF, spreadsheet, Figma, OpenAI docs |
| `/mcp` | ดู MCP tools ที่ตั้งค่าไว้ | เช็กว่า Codex ต่อกับเครื่องมือภายนอกอะไรได้บ้าง |
| `/mention` | แนบไฟล์หรือ path เข้า context | อยากบอกให้ Codex อ่านไฟล์เฉพาะ |
| `/copy` | copy คำตอบล่าสุดเป็น Markdown | เอาคำตอบล่าสุดไปวางที่อื่น |
| `/quit` หรือ `/exit` | ออกจาก Codex | จบ session |

## ตัวอย่าง `/init`

`/init` ใช้สร้างไฟล์ `AGENTS.md` สำหรับบันทึกคำสั่งถาวรของ repo เช่น:

- โครงสร้างโปรเจกต์
- คำสั่ง build/test
- coding style
- วิธี manual verification
- ข้อห้ามเฉพาะ repo

ตัวอย่างการใช้งาน:

```text
/init
```

หลังจากสร้างแล้วควรเปิด `AGENTS.md` ตรวจแก้ให้ตรงกับ repo จริง แล้ว commit ไว้ เพื่อให้ Codex session ถัดไปอ่านกติกานี้ได้ตั้งแต่ต้น.

ใน repo นี้มี `AGENTS.md` อยู่แล้ว และมีคำสั่งสำคัญ เช่น ให้อ่าน `CLAUDE.md` ก่อนเปลี่ยนงานใหญ่, quote path ภาษาไทยใน shell, และห้าม recreate sidebar/header ในแต่ละ HTML page.

## Context และ session

| คำสั่ง | ใช้ทำอะไร |
| --- | --- |
| `/compact` | สรุปบทสนทนาเดิมเพื่อคืนพื้นที่ context |
| `/new` | เปิดแชทใหม่ |
| `/resume` | กลับไป session ที่เคย save ไว้ |
| `/fork` | แตก branch จากแชทปัจจุบันเป็น thread ใหม่ |
| `/side` หรือ `/btw` | เปิด side conversation ชั่วคราว |
| `/rename` | เปลี่ยนชื่อ thread |
| `/archive` | archive session แล้วออก |
| `/delete` | ลบ session ถาวรแล้วออก |

## งานโค้ดและไฟล์

| คำสั่ง | ใช้ทำอะไร |
| --- | --- |
| `/review` | review changes ปัจจุบันแบบ code review |
| `/diff` | ดู git diff รวม untracked files |
| `/mention` | แนบไฟล์เข้า context |
| `/raw` | toggle raw scrollback mode เพื่อ copy จาก terminal ง่ายขึ้น |
| `!<command>` | รัน shell command จากใน Codex เช่น `!ls` |

## Model, permission, และ config

| คำสั่ง | ใช้ทำอะไร |
| --- | --- |
| `/model` | เลือก model และ reasoning effort |
| `/permissions` | ตั้งสิทธิ์/approval ว่า Codex ทำอะไรได้เอง |
| `/setup-default-sandbox` | ตั้งค่า elevated agent sandbox |
| `/sandbox-add-read-dir` | เพิ่ม read directory ให้ sandbox เฉพาะบางระบบ เช่น Windows |
| `/keymap` | ตั้ง keyboard shortcuts ของ TUI |
| `/vim` | เปิด/ปิด Vim mode ใน composer |
| `/personality` | เลือกสไตล์การตอบของ Codex |
| `/title` | ตั้งรายการที่แสดงใน terminal title |
| `/statusline` | ตั้งรายการที่แสดงใน status line |
| `/theme` | เลือก syntax highlighting theme |
| `/pets` หรือ `/pet` | เลือกหรือซ่อน terminal pet ถ้า surface รองรับ |

## Tools, skills, plugins, apps

| คำสั่ง | ใช้ทำอะไร |
| --- | --- |
| `/skills` | browse/use skills |
| `/mcp` | list MCP tools; ใช้ `/mcp verbose` เพื่อดูรายละเอียด |
| `/apps` | manage app connectors |
| `/plugins` | browse plugins |
| `/hooks` | ดูและจัดการ lifecycle hooks |
| `/ide` | ดึง context จาก IDE เช่น current selection/open files |
| `/import` | import setup/project/recent chats จาก Claude Code |

## Skills ที่ควรใช้กับโปรเจกต์นี้

| Skill/plugin | ใช้กับงานใน repo นี้ |
| --- | --- |
| Browser | เปิดและตรวจหน้า HTML prototype บน `localhost`, คลิก flow, ตรวจ modal/tab/table/sidebar, responsive, และ screenshot |
| PDF | อ่าน SRS/batch-job PDF, extract requirement, render/verify PDF output |
| Documents/Word | สร้างหรือแก้ `.docx` เช่น SRS/LLDD deliverables แล้ว render ตรวจหน้า |
| Spreadsheets | ทำ `.xlsx`, `.csv`, ตาราง export, สูตร, chart, หรือไฟล์ตรวจรายการ |
| OpenAI Docs | ตอบเรื่อง Codex, slash commands, model/API, config, MCP, skills จากเอกสารทางการ |
| Image generation | สร้าง bitmap assets เฉพาะเมื่อจำเป็น เช่นภาพประกอบหรือ mockup; งาน prototype ปกติให้ใช้ HTML/CSS/SVG เดิม |
| Figma | ใช้เมื่อมีคำสั่งเกี่ยวกับ Figma โดยตรง เช่น implement design, create screen, หรือสร้าง diagram ใน FigJam |

สำหรับงาน HTML/CSS/JS ทั่วไป Codex แก้ไฟล์ได้ตรง ๆ ไม่ต้องมี skill แยก แต่หลังแก้ UI หรือ interaction ควรใช้ Browser ตรวจผลจริง.

## Long-running work

| คำสั่ง | ใช้ทำอะไร |
| --- | --- |
| `/plan` | เข้า Plan mode เพื่อวางแผนก่อนลงมือ |
| `/goal` | ตั้งหรือดู goal สำหรับงานยาว |
| `/agent` หรือ `/subagents` | สลับ active agent thread ถ้าเปิดใช้ multi-agent |
| `/ps` | ดู background terminals และ output ล่าสุด |
| `/stop` หรือ `/clean` | หยุด background terminals ทั้งหมด |
| `/approve` | อนุมัติ retry หนึ่งครั้งหลัง auto-review ปฏิเสธคำสั่ง |

## Account และ feedback

| คำสั่ง | ใช้ทำอะไร |
| --- | --- |
| `/usage` | ดู usage หรือ usage-limit reset ถ้า surface รองรับ |
| `/logout` | logout จาก Codex |
| `/feedback` | ส่ง logs ให้ maintainers เพื่อรายงานปัญหา |
| `/app` | เปิด/ต่อ session ใน Codex Desktop app ถ้ารองรับ |

## คำสั่ง debug/internal

คำสั่งเหล่านี้มีไว้สำหรับ debug หรือ development ของ Codex เอง จึงไม่ควรใช้ในงานปกติ:

| คำสั่ง | หมายเหตุ |
| --- | --- |
| `/debug-config` | ดู config layers และ requirement sources |
| `/rollout` | print rollout file path เฉพาะ debug build |
| `/test-approval` | ทดสอบ approval request เฉพาะ debug |
| `/debug-m-drop` | internal memory debug |
| `/debug-m-update` | internal memory debug |

## CLI commands นอกแชท

รันใน terminal ปกติ ไม่ใช่ในช่องแชท:

| คำสั่ง | ใช้ทำอะไร |
| --- | --- |
| `codex` | เปิด interactive Codex TUI |
| `codex "prompt"` | เปิด Codex พร้อม prompt เริ่มต้น |
| `codex exec "prompt"` | รัน Codex แบบ non-interactive |
| `codex review` | รัน code review แบบ non-interactive |
| `codex login` | login |
| `codex logout` | logout |
| `codex mcp ...` | จัดการ MCP servers |
| `codex plugin ...` | จัดการ plugins |
| `codex app` | เปิด Codex Desktop app |
| `codex completion ...` | generate shell completion |
| `codex update` | update Codex |
| `codex doctor` | diagnose installation/config/auth/runtime |
| `codex resume` | resume saved session |
| `codex fork` | fork saved/current session |
| `codex archive` | archive saved session |
| `codex delete` | delete saved session |
| `codex cloud` | browse/apply Codex Cloud tasks ถ้าเปิดใช้ |
| `codex --help` | ดู help ของ CLI |
| `codex --version` | ดู version |

ตัวอย่าง:

```sh
codex --version
codex doctor
codex resume
codex exec "review this repo and list risky files"
```

## คำแนะนำใช้งานใน repo นี้

- ก่อนให้ Codex ทำงานยาว ให้ระบุ scope ชัด เช่น "แก้เฉพาะ `k2-report.html` และ `assets/sbp.css`".
- ถ้าบทสนทนายาว ให้ใช้ `/compact` ก่อนสั่งงานต่อ เพื่อไม่ให้ context เต็ม.
- ถ้าต้องการให้ Codex จำกติกา repo ระยะยาว ให้แก้ `AGENTS.md` หรือ `CLAUDE.md` แทนการพิมพ์ซ้ำในแชท.
- ถ้าอยากให้ Codex อ่านไฟล์เฉพาะ ให้ใช้ `/mention path/to/file`.
- ก่อน commit ให้ใช้ `/diff` แล้วตามด้วย `/review`.
