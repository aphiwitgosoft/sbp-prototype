# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, Thai-language, click-through HTML prototype of **ระบบประกันรายได้ (K2)** — an income-guarantee system that compensates 7-Eleven franchise "Store Partner (SP)" stores whose sales drop when a new 7-Eleven opens within an impact radius (1 km Bangkok/metro, 2 km provincial). "SBP" = Store Business Partner. "K2" refers to the BPM/workflow platform the real system runs on. The prototype implements every screen from the SRS **"RDM-SRS ประกันรายได้-K2 Version 3.1"** (PDF in repo root).

The repo has since grown around the prototype into the project's design/delivery hub. Four layers, from source to deliverable:

1. **The HTML prototype** (repo root + `assets/`) — no build/lint/test tooling; view with `open index.html` or `python3 -m http.server` (both land on `k2-list-waiting.html`, the app's home page — `index.html` is just a redirect stub). Only external dependency is Google Fonts (`assets/sbp.css` line 5); everything else works offline.
2. **Living design docs** — `database.md` / `workflow.md` / `api.md` mirrored by `plan-database.html` / `plan-flow.html` / `plan-api.html` (see "Living docs" below).
3. **Implementation specs — ลบทั้งหมดเมื่อ 2026-08-11** (`plan-fe.md`, `plan-be.md`, `checklist-fe.md`, `checklist-be.md`, `REACT-TODO-CHECKLIST.md` · กู้จาก git ที่ `ebc09e7`): ตกยุคจนขัดกับการตัดสินใจปัจจุบัน ~250 จุด · **แหล่งความจริงสำหรับสร้างระบบคือ `workflow.md` / `api.md` / `database.md` และชุด LLDD ใน `LLDD/md/` เท่านั้น**
4. **LLDD deliverables** — 41 low-level design documents in `LLDD/md/` (38 topic documents + the two reference documents `LLDD-API` and `LLDD-Database`; the directory also holds `README.md` and the main index, so `find LLDD/md -name '*.md'` returns 42). History: 40 → 38 on 2026-08-06 (FE-Batch-Monitor + FE-Email-Template dropped), then 2026-08-07 dropped FE-Overview + BE-API-Dashboard-Summary and added four BE documents (BE-Database-Structure, BE-Data-Migration-Cutover, BE-Integration-SBP-Platform, BE-Workflow-Engine-Definition) → 38 topic / **41 documents**. The count is computed live by `tools/build_lldd_documents.py` (`len(all_topics) + len(reference_doc_links())`) and printed in `LLDD/md/README.md` + `LLDD/index.html` — those two are authoritative; generated to PDF/DOCX by the same script.

Several filenames contain Thai characters — always quote paths in shell commands.

## Commands

The prototype itself has none (plain HTML/CSS/JS). The tooling that exists:

```sh
# Real FE/BE work happens in the existing SBP codebases (see SBP/*.md analyses)
cd SBP/srm-sps-spsap-web-frontend && NEXT_PUBLIC_APP_TARGET=sbpm npm run dev   # FE portal (SBPGI = module under src/app/(main)/sbpgi)
cd SBP/srm-sps-spsap-store-backend && npm run start:dev                        # BE convention reference (NestJS + TypeORM)

# Document generation (system python3 has the deps: python-docx, reportlab, PIL, lxml)
python3 tools/build_lldd_documents.py --formats md,docx,pdf   # LLDD/md → LLDD/pdf + LLDD/word + flow PNGs (manifest.json lists generated files)
python3 tools/check_docs.py                                   # ชุดตรวจเอกสาร — จำนวนตาราง/FK/ลิงก์ + ตาราง+คอลัมน์ของ sps_store ที่อ้าง + ชื่อ function ของ engine (exit 1 เมื่อพบปัญหา)
python3 tools/build_worklist.py                              # worklist.html — หน้าจัดการงานสไตล์ Notion (งาน → API → DB) จากข้อมูลชุดเดียวกับ LLDD
# worklist.html มี Kanban Board (#/board) — สถานะงานเก็บ 3 ชั้น: localStorage (ทำงานประจำวัน) ·
#   และหน้าแผนงานรายสัปดาห์ (#/plan) — งานเป็นแถว สัปดาห์เป็นคอลัมน์ · จัดคิวจาก dependency + คิวเจ้าของงาน · แถวท้ายสรุปภาระงาน/สัปดาห์ (เพดาน 6 คน × 30 = 180 ชม.)
#   ลิงก์แชร์ ?b=<38 ตัวอักษร> (ส่งในแชท) · worklist-board.json (baseline ที่ commit ขึ้น git แล้วหน้าเว็บ fetch เป็นค่าตั้งต้น)
python3 tools/build_integrated_srs.py                         # integrated SRS DOCX/PDF → output/srs/
node tools/capture_srs_screenshots.mjs                        # page screenshots → output/srs/screenshots/
```

`output/` and `tmp/` are generated/scratch — never edit by hand. In `LLDD/`, the markdown under `LLDD/md/` is the source; `LLDD/pdf/`, `LLDD/word/`, `LLDD/assets/flows/` are regenerated.

## Architecture (prototype)

Three moving parts: **17 contract pages** (+ `index.html` redirect stub; two of the 17 are kept-for-reference but unlinked — the RBAC pair `k2-operators.html`/`k2-permissions.html`), one stylesheet (`assets/sbp.css`), one script (`assets/sbp.js`, ES5 IIFE, no dependencies). The header and sidebar do **not** exist in the HTML — `sbp.js` injects them at runtime on every page.

**Three standalone pages do NOT follow the page contract** (plain `<body>`, no `sbp.js`) — don't retrofit the contract onto them or copy them as templates:

- `ประเด็นหารือ-preaccept-workflow.html` — discussion doc (pre-accept stores can't start workflow, Job 5 ↔ Job 8b) · not in `MODULES`
- `flow-srs.html` — **figure generator**: renders the 3 sequence diagrams that `tools/capture_srs_modals.mjs` screenshots into the SRS deliverable · not in `MODULES`, not linked from any page — **do not delete, it looks orphaned but the SRS build depends on it**
- `worklist.html` — generated by `tools/build_worklist.py` (Notion-style work management: งาน → API → DB + Kanban `#/board` + แผนงานรายสัปดาห์ `#/plan`) · **is** in `MODULES` under group `Plan`, and carries its own `← กลับระบบประกันรายได้` link back to the app

### Page contract (how every page works)

Each page declares context via body attributes and provides an **empty** sidebar mount:

```html
<body data-page="k2-report" data-nav="modules" data-module="k2-report" data-crumb="รายงานสรุปสถานะ">
<div class="layout">
  <aside id="sidebar"></aside>          <!-- MUST stay empty; sbp.js fills it -->
  <main class="content">…page content…</main>
</div>
<div id="toast-stack"></div>
<script src="assets/sbp.js"></script>
```

`data-page`/`data-module` equal the filename base; `data-crumb` is the breadcrumb leaf. Use `k2-document.html` as the template for new pages (`index.html` no longer follows the contract at all — it is a bare redirect stub). Page-specific CSS goes in an inline `<style>` in that page's head; page-specific JS in an inline `<script>` **after** the `sbp.js` include (so `window.SBP.toast` exists). There are no per-page asset files.

**Adding a page = 2 steps**: (1) create the HTML file following the contract above, (2) add an entry to the `MODULES` array in `assets/sbp.js` (~line 52) — `{key, label, href, icon, group}`. `MODULES` is the single registry driving the sidebar and breadcrumb; sidebar groups render in first-appearance order (current groups: `ระบบประกันรายได้ (SBP Mall)`, `Flow` — Flow FGI/FCS · Flow K2 · Flow FGI/FCS + K2 · Flow Batch Job, `Database`, `Plan` — the `(SBP Mall)` suffix signals this is the SBP Mall web front per the SDD). **The `ผู้ดูแลระบบ (Admin)` group is gone (2026-08-06)**: `system-config.html` (Global Config) and `email-template.html` (Email Template) were **deleted outright** — central config and mail templates are administered in the existing SBP system (`mas_param` / `email_template`), and the BE only reads them; `job-batch.html` **moved to the `Flow` group as “Flow Batch Job”** and now shows only two tabs — `Flowchart การทำงาน` and `Database ที่ใช้`; the parameter form, run history, run/enable controls, stat cards, charts and audit card are gone. It is developer reference material, not a control screen: batch jobs still run, but their cron/parameters come from backend config.

A module entry may instead carry `children: [{key, label, href}]` (no top-level `href`) to render a collapsible submenu — used by `เอกสาร` → รอดำเนินการ (`k2-list-waiting.html`) / ที่เกี่ยวข้อง (`k2-list-related.html`). The two k2-list-waiting/related pages are near-identical copies differing only in a hardcoded `MODE` const, `<title>`, and body attrs — apply fixes to both. Active-child detection order: exact `file+query` match → `key` equals `data-page` → same file. `k2-document.html` is intentionally not in the sidebar (reached by clicking table rows).

**2026-08-06 decisions (landing page, dropped screens, create flow):**
- **The Overview/Dashboard page is gone.** `index.html` is now only a redirect stub to `k2-list-waiting.html`; the `home` MODULES entry is commented out, `เอกสาร` is the first sidebar group entry, and `HOME_KEY`/`HOME_HREF` at the top of `sbp.js` drive the brand logo link, the breadcrumb "Home" (rendered as plain text on the home page itself), and the filename fallback. **The landing page is เอกสาร → รอดำเนินการ.**
- **ข้อมูลผิดปกติ / แจกงาน is gone** — the `k2-list-abnormal.html` file was **deleted** from the repo (2026-08-06), along with its MODULES entry and its 2-endpoint group in `plan-api.html`/`api.md`. Abnormal data survives as a *row flag*: `salesDataDays < 60` renders `tr.flag-red` plus a "ยอดขายไม่ครบ 60 วัน" stat-card filter on the waiting/related pages.
- **`k2-create.html` has no form or tabs** — its main card is a **simulated `<iframe>` frame of the FS create-document page** (same `.fs-frame` styling as the calculation section on `k2-document.html`, shared from `sbp.css`), because the legacy K2 page embeds the FS form the same way. The 4-step explanation (verbatim from the legacy screen) sits **below it as a หมายเหตุ card**, outside the frame (moved 2026-08-06). `POST /documents` is therefore a pipeline/service-token endpoint, not an FE form; per-document key-in/adjustment happens in `k2-document.html`.
- The "ขั้นตอน Workflow ตามบทบาท" bar (`#roleBar`) on `k2-document.html` + both list twins has a close button (`#rbClose`) at its top-right and a restore chip (`#rbShow`) below it; the collapsed state persists across pages via `sessionStorage['sbp.roleBarHidden']`.

Note: `sbp.js` also has a `data-nav="application"` sidebar mode and `switchStep()` navigation — legacy from deleted pages (`application*.html`, `recruitment.html`). Do not use or copy that mode.

### Behavior hooks (all in sbp.js, wired via one delegated click handler)

Interactivity is simulated by declaring attributes/classes in markup:

- `data-href` navigates; `data-toast`/`data-ack` (+ optional `data-kind="ok|del"`) fire a toast instead of a real action.
- `table.data` rows with `.icon-view` / `.icon-edit` / `.icon-del` buttons get auto-generated view/edit modals and confirm-delete. `[data-add-row="tableId"]` opens an add-row modal.
- The modal engine is driven by `data-entity` on the table, keyed to hand-written `SCHEMAS` in `sbp.js` (~line 424). Schema fields map to columns **by exact header text** — renaming a `<th>` silently breaks the modal round-trip. `data-entity="k2doc"` bypasses modals and populates the `#openedDoc` detail panel instead.
- Tabs: container `[data-tabs]` with child `.tab[data-tab=key]` toggles every `[data-tabpane]` **document-wide** whose key doesn't match.
- Charts: `<div data-chart="bar|donut|spark" data-values data-labels data-colors data-center>` renders inline SVG. All other diagrams (BPMN flowchart in k2-flow, ER diagram in k2-database, AllMap map in k2-document, per-endpoint flowcharts in plan-api) are hand-authored inline SVG — no chart/diagram libraries.
- **2026-08-06 — charts and stat cards were stripped from the working screens:** `k2-document.html` lost its daily-sales and compensation-share charts (the AllMap map stays), `k2-report.html` lost both HBar charts, and both list twins lost the entire `#statGrid` stat-card row (their `renderWaitingStats`/`renderRelatedStats` are now no-ops, and the related page's **สถานะ** filter field was un-hidden since the donut that used to filter by status is gone). `GET /dashboard/summary` was deleted from the API design as a result (47 endpoints). Charts still live on the design/plan pages only.
- Public API is only `window.SBP.toast(msg, kind)`.

### Styling

Design tokens live in `:root` of `sbp.css`. The app accent is `--primary` (#2f6fed blue) with teal secondary; the 7-Eleven brand colors (`--seven-*`) are for the header logo **only**. Status chips: `.pill` (status with dot) vs `.chip` (data labels) — not interchangeable. `table.data` needs a `.table-wrap` wrapper for horizontal scroll. Elements with class `reveal` are invisible until JS adds `.in`. Modals need both `display:flex` and `.show` to appear.

## Requirements documents (source-of-truth order)

1. `RDM-SRS ประกันรายได้-K2.pdf` — the SRS v3.1, ultimate requirements source. `SRS_Income_Compensation_v3.1.md` is its markdown conversion.
2. `RDM-SRS-ประกันรายได้-K2-รายการหน้าจอ.md` (455 lines) — detailed screen inventory: per-screen fields, validations, verbatim popup texts, role behavior table.
3. `ประกันรายได้-K2-รายการหน้าจอ.md` (160 lines) — condensed companion keyed to SRS section numbers, with section_codes and the 8 permission roles. **Not a duplicate** of #2 despite the similar name.
4. `PLAN-checklist-prototype.md` — implementation-status checklist mapping SRS sections 3.1.1–3.1.9 to HTML files. Internally inconsistent: some checkboxes are `[ ]` but the bottom summary says they were completed later — verify in the HTML before re-implementing anything.

Thai popup/validation strings in the docs are specified verbatim from the SRS and implemented to match exactly — do not paraphrase them when editing pages.

`FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0.pdf` (29 pages) describes the 11 backend batch entry points (Jobs 1–10 + 8b StartK2WorkFlow) that feed the K2 system; it is the sole requirements source for `job-batch.html` (**“Flow Batch Job” in the `Flow` group since 2026-08-06** — flowchart + tables-used reference only, no parameter/run-history tabs) and is not referenced by the K2 screen docs.

**The only SDD in the repo is now "SDD GI"** — `SDD ปรับปรุงการชดเชยรายได้ในระบบ SBP GI(2402026).pptx` (see below). The older `08102025 SDD ปรับกระบวนการบัญชีประกันรายได้ เพื่อตรวจสอบ.pdf/.pptx` (**SDD v7.5**, 15/10/2025 — the accounting-process change that cut workflow steps 04/05) was **deleted from the repo on 2026-08-06**; its decisions are already folded into the current design (`workflow.md`, `workflow_status_document.md`, the prototype and the LLDD set), so the `(SDD v7.5)` tags that remain in those docs are provenance labels, not pointers to a file you can open. `SDD-บัญชีประกันรายได้-gap-analysis.md` audits the prototype against **both** SDDs (SDD GI wins on conflict). `workflow_status_document.md` is the status × action × next-actor × email transition table.

**"SDD GI"** = `SDD ปรับปรุงการชดเชยรายได้ในระบบ SBP GI(2402026).pptx` (82 slides, 24/02/2026), converted to `SDD-GI-Compensation/SDD-ปรับปรุงการชดเชยรายได้-SBP-GI.md`. It is the newest requirements source and overrides earlier rules where they conflict: new approval limits (เกณฑ์เดียว 100,000 per item), self-service document reopening after หยุด/ไม่เห็นควรชดเชย (kills the ~20,000 THB/month SR cost), pending-work screen with auto-assign to the previous owner, section-01 rename to หน่วยงานส่งเสริมธุรกิจ SBP — the rename applies **everywhere in the system including the document status name** ("รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ", decided 2026-08-06) — and a new **Senior Officer (เจ้าหน้าที่อาวุโส)** role that works section 01 alongside the existing manager/specialist level and can forward to GM, immediate flow-end on เห็นควรไม่ชดเชย at 01/02, zero-amount month 1–3/month-4 rule, and DSA all-store visibility. Acting (รักษาการ) positions cannot be approvers (positions come from HR Connect).

Current Batch Job decision (2026-08-06): the two **control** tabs are out of scope — `LLDD-FE-Batch-Monitor` was removed from the LLDD set, the Batch Job Admin API group (6 endpoints, `/jobs*`) was removed from `api.md`/`plan-api.html`, and `job_configs` / `job_run_histories` were removed from the target schema (24 → 22 tables at the time; 21 today). What survives is `job-batch.html` **as a Flow-group reference page with only `Flowchart การทำงาน` and `Database ที่ใช้`**. Batch jobs themselves (Jobs 1–10 + 8b) still run: cron and parameters come from **backend config** (config file/env), manual runs go through CLI/runbook, and run results go to the application log plus `interface_transactions`. If the control tabs return in a later phase, restore the tabs, the 6 endpoints, and the 2 tables together.

Flow pages live in sidebar group `Flow`: `flow-fgi.html` = FGI/FCS batch pipeline, `k2-flow.html` = K2 approval workflow, `plan-flow.html` = combined FGI/FCS + K2 target flow, and `job-batch.html` = **Flow Batch Job** (per-job flowchart + tables used, moved here 2026-08-06). Database pages live in sidebar group `Database`: `fgi-database.html` = FGI/FCS pipeline schema, `k2-database.html` = K2 documents/workflow schema, and `plan-database.html` = combined 19-table target schema (zones A = FGI/FCS, B = K2 documents/workflow, C = shared master/config). `plan-api.html` (sidebar group `Plan`) · **`worklist.html` (sidebar group `Plan` · เพิ่ม 2026-08-18)** = หน้าจัดการงานสไตล์ Notion เชื่อม งาน → API → DB สร้างด้วย `tools/build_worklist.py` จากข้อมูลชุดเดียวกับ LLDD — เป็นหน้า **standalone** (มี sidebar ของตัวเอง ไม่ใช้ page contract ของ `sbp.js`) จึงมีลิงก์ `← กลับระบบประกันรายได้` ในตัว documents the 29-endpoint / 6-group REST API spec, including per-endpoint example SQL in `SQL_BY_PATH` (keyed `'METHOD path'`) and flowchart specs in `FLOWCHART_BY_PATH` for the 4 complex endpoints. Target database names use English `lower_snake_case` consistently; source tags — (FGI/FCS), (K2), or (ใหม่) — still tie each object back to the requirement documents and should be preserved.

## Living docs: database.md, workflow.md, and api.md (MUST read & keep in sync)

`database.md`, `workflow.md`, and `api.md` in the repo root are the canonical markdown summaries of the new-system design:

- `database.md` — the 19-table target schema, mirrors `plan-database.html` (data spine, zones A/B/C, cross-system keys, P0/P1 fixes).
- `workflow.md` — the end-to-end flow, mirrors `plan-flow.html` plus the sequence diagrams `old-flow.png` (legacy, 7 lanes incl. EAI and K2) and `new-flow.png` (target, 5 lanes).
- `api.md` — the 29-endpoint / 6-group REST spec (Lookup 2 · Master Data 8 · เอกสาร 11 · รายงาน 2 · Workflow 3 · Interface 3), mirrors `plan-api.html` (per-endpoint modal structure, business rules bound to endpoints, and the removal records: abnormal-stores 2 endpoints, System Config + Email Template 10 endpoints, Batch Job Admin 6 endpoints).

**2026-08-06 decision (round 2) — reuse the existing SBP system's tables and APIs wherever they already exist:** auditing `SBP/README.md` + `srm-sps-spsap-store-backend` (79 TypeORM entities, 25 controllers, PostgreSQL) showed 10 target tables duplicated things the SBP system already runs, so they were cut (34 → 24 tables) and 3 endpoints dropped (47 → 44 endpoints). Cut tables → replacements: `workflow_instances`/`workflow_tasks`/`workflow_sections`/`document_statuses` → **`@srm/glb-workflow`** — **13 engine tables in schema `sps_store`** (`workflow` · `workflow_version` · `workflow_state` · `workflow_status` · `workflow_event` · `workflow_route` · `workflow_group` · `workflow_group_map` · `workflow_transaction` · `workflow_history` · `workflow_approver` · `workflow_part` · `workflow_part_display`); `sps_auth` has the same 13 table names but is auth-backend's separate, older copy (different column counts, ~55 transactions) — **do not point SBPGI at it**. SBPGI requests one new workflow version and calls the engine's initialize → add-prepared-approver → trigger-event sequence; **the function names are UNCONFIRMED — three conflicting sets exist** (A `eventWorkflow`/`addPreApprover`/`getPendingFlowByUser` from `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` sheet Detail · B `triggerEvent` from the Mermaid sequence in the same file · C `TriggerEventUseCase`/`AddPreparedApproverUseCase`/`GetPendingFlowUseCase` from `SBP/srm-sps-spsap-store-backend.md` §1.5) — see `api.md`; and **`referenceId` is undecided (DP-1)**, see `SBP/SBPGI-vs-existing-system.md` §4. Also note **`sps_store.workflow_transaction` has no PK and no index** on 19,283 rows (DP-2). `stores` → `store`/`mas_store`/`sevenshop`; `zones` → `mas_zone`; `branch_types` → `common_code`; `employees` → `business_user`; `email_templates` → `email_template` + `email_sent` + `@gosoft-sbp/email-lib`; `system_configs` → `mas_param`. Dropped endpoints: `/stores/search` → `GET /store/search`, `/zones` → `GET /store/all-regions`, `/branch-types` → `GET /common/common-code`. Also reuse: `GET /api/workflow/pending` (cross-system inbox), `POST /statement/upload-file-aws`/`download-file-aws` (S3). Approval limits (เกณฑ์เดียว 100,000) move to `common_code` (`code_type = SBPGI_APPROVE_LIMIT`). Kept because nothing equivalent exists: `consideration_logs` (engine history has no decision code/attachments), `document_attachments` (metadata only — files go through the existing S3 service), `interface_transactions` (record-level ACK; `integration_log` covers per-call payload logging and replaces the proposed `FGI_WS_LOG` table). `audit_logs` was kept in this round but **cut on 2026-08-07** (whether master-data audit comes back on the existing system's mechanism is DP-12). Response envelope must match store-backend: `{success, data}` / `{success:false, data:null, error:{code,message}}`.

**2026-08-06 decision (round 3) — the Admin screen group was removed entirely.** `system-config.html` (ตั้งค่าระบบ / Global Config) and `email-template.html` (Email Template) were **deleted**, together with their 10 endpoints (`/configs*` 5, `/email-templates*` 5), the `SCHEMAS.config` entry in `sbp.js`, and the LLDD document `LLDD-FE-Email-Template`. Both already wrote to the existing SBP system's tables (`mas_param`, `email_template`), which that system already administers; SBPGI now only **reads** them — status e-mails still go out through `@gosoft-sbp/email-lib` with a row in `email_sent`. Separately, `job-batch.html` was **cut down to a Flow-group reference page**: it moved from the Admin group to `Flow` as **“Flow Batch Job”** and keeps only the `Flowchart การทำงาน` and `Database ที่ใช้` tabs — the parameter form, run history, run/enable controls, stat cards, charts and audit card were deleted, along with the Batch Job Admin group (6 endpoints, `/jobs*`), the tables `job_configs` / `job_run_histories`, and the LLDD document `LLDD-FE-Batch-Monitor`. **The batch jobs themselves still run** — cron and parameters live in **backend config** (config file/env), manual runs go through CLI/runbook, and run results land in the application log plus `interface_transactions`. That round left 22 tables · 31 endpoints · 6 groups; the **2026-08-07 real-database comparison** (`SBP/db-schema-sps_store.md`, `SBP/SBPGI-vs-existing-system.md`) then cut `audit_logs` and one more endpoint. **Current state: 19 tables · 29 endpoints · 6 groups · 40 LLDD documents** (2026-08-10 · มติ DP-9 ย้าย `decisions` ไป `common_code` → ตัด 1 ตาราง + 1 endpoint).

**2026-08-05 decision — reuse the existing SBP system for RBAC and operator assignment:** the current SBP production system (`SBP/` directory: `srm-sps-spsap-web-frontend` + `-sbp-bff` + `-store-backend`, see the three analysis `.md` files in `SBP/`) already provides menu permissions (auth-backend/ABS groups/menus/permissions per URL, managed via the existing `/setting/manage-user-rights` page) and operator/approver assignment (auth-backend groups + `@srm/glb-workflow` prepared approvers). SBPGI therefore does NOT build these: tables `roles`/`menus`/`menu_permissions`/`user_accounts`/`operator_assignments` and 18 API endpoints (Auth group + operators/roles/menus/menu-permissions/employees-search) were removed from the target design (34→29 tables, 62/10→44/9 endpoints/groups; the 2026-08-06 legacy-DB comparison later added 5 tables and 3 lookup endpoints back → 34 tables / 47 endpoints; the same day's reuse round cut it to 24 tables, then deleting Global Config + Email Template and deferring Batch Job brought it to 22 tables / 31 endpoints / 6 groups, the 2026-08-07 real-database comparison brought it to 21 tables / 30 endpoints, and มติ DP-9 (2026-08-10) ย้าย `decisions` ไป `common_code` → **20 tables / 29 endpoints / 6 groups**), and `k2-operators.html` + `k2-permissions.html` were removed from MODULES and index.html shortcuts (commented out; files kept for reference). SBPGI receives identity via BFF headers (`x-api-key`, `x-user-id`, `x-user-group-id`, `x-user-permissions`).

**Whenever a conversation touches the database, the flow/workflow, or the API, read the relevant .md file first.** When a design decision changes any of these topics, update the .md file **and** its HTML counterpart (`plan-database.html` / `plan-flow.html` / `plan-api.html`) in the same change so they never drift. The three are cross-coupled: an API change often touches a table (`database.md`) or a flow step (`workflow.md`) — update all affected pairs together. Design changes may also ripple into the LLDD markdown (`LLDD/md/`) and the implementation specs below.

Core architectural premise recorded there: the new system merges **EAI and K2 into SBPGI** — FGI/FCS batch jobs and the K2 document/workflow run in one system on one database. The internal `BPM06001O_/2O_/3O_` file exports through EAI (Jobs 7/8/9) and the K2 REST StartInstance call (Job 8b) are removed, replaced by direct DB writes (Document Service) and an internal Workflow Engine. External interfaces (QSSI, ALLMAP, IAS/MIS, STA, SMTP) keep their existing file/SFTP mechanisms.

## Implementation specs and the React port

FE target = โมดูลใน Next.js portal เดิม (`SBP/srm-sps-spsap-web-frontend`, portal `sbpm`) · BE target = NestJS + TypeORM ตาม `SBP/srm-sps-spsap-store-backend` (ตัดสินใจ 2026-08-05). ชุด spec เดิม (`plan-fe.md` `plan-be.md` `checklist-fe.md` `checklist-be.md` `REACT-TODO-CHECKLIST.md`) **ถูกลบทิ้งเมื่อ 2026-08-11** เพราะตกยุคจนขัดกับการตัดสินใจปัจจุบัน ~250 จุด · แหล่งความจริงสำหรับสร้างระบบตอนนี้คือ:

- **`workflow.md` / `api.md` / `database.md`** — living docs (flow · 29 endpoint 6 กลุ่ม · 19 ตาราง) คู่กับ `plan-flow.html` / `plan-api.html` / `plan-database.html`
- **`LLDD/md/`** — เอกสารส่งมอบ 41 ฉบับ (สเปกระดับลงมือทำ พร้อม SQL/skeleton/flow ต่อหัวข้อ)
- Shared FE↔BE contracts: `LLDD/md/FE/LLDD-FE-Integration-Contracts.md` + `LLDD/md/BE/LLDD-BE-API-Common-Contracts.md`

**The `react-app/` React + Vite port was deleted on 2026-08-06** (recoverable from git history at commit `003b661`). It became dead weight once the FE target moved into the existing Next.js portal — do not resurrect it or write specs against it. `REACT-TODO-CHECKLIST.md` survives as a **per-screen component/field inventory** and is still useful when building the portal module.

`LLDD/` holds the 40 LLDD delivery documents (38 topic + LLDD-API + LLDD-Database + LLDD-To-Be; source markdown in `LLDD/md/{FE,BE,BE/Jobs}`, portal at `LLDD/index.html`, team/schedule in `LLDD/md/README.md` and `Main-Index-FE-BE-Job.csv`). Project planning docs at root: `estimate-sbpgi-project-hours.md`, `activity-plan-sbp-mall-fe-be.md`, `LLDD-Phase4-4.3-SBP-Operating-Management-Income-Guarantee.md`.

## Domain rules encoded in the prototype

- 5-step approval workflow by section_code (SDD v7.5 cut accounting steps 04/05): 06 (ฝ่าย SBP DSA) → 08 (เจ้าหน้าที่ SBP DSA) → 01 (หน่วยงานส่งเสริมธุรกิจฯ — renamed from หน่วยงานส่งเสริมธุรกิจ and widened to senior officers per SDD GI) → 02 (GM) → 03 (AVP). **Approval limit — single 100,000 threshold (meeting decision 2026-08-18, overrides SDD GI slide 55): amount < 100,000 ends at GM (02); amount ≥ 100,000 routes to AVP (03) then ends. This reverts the short-lived 50,000/300,000 two-tier rule back to the original single threshold, and removes the old "> 300,000 unspecified" open item.** "เห็นควรไม่ชดเชย" at sections 01/02 now ends the flow immediately (no bounce-back). Reopening is allowed: a store+month whose document ended in หยุด/ไม่เห็นควรชดเชย can get a new document without an SR; ไม่เห็นควร (06) auto-queues next month to the same assignee; zero-compensation months 1–3 forward to 01, month 4 = หยุดชดเชย. Document statuses: 6 values (unchanged — status names still use "หน่วยงานส่งเสริมธุรกิจ"). Accounting verifies via the SBP Mall report (ค้นหาข้อมูล + Export Excel) outside the workflow; that report screen was aligned to **SDD slide 60** on 2026-08-06 — 7 filters (สถานะ is the only required one) and 14 result columns.
- Document numbers: `YYYY/xxxxx` with **Christian-era (ค.ศ.) year** — e.g. `2026/00123`. Dates and document numbers are ค.ศ. system-wide (decided 2026-08-06, see `api.md`); the only exception is the STA/IAS interface files (`FRBC0001_*`, `AMS06001I_*`) which stay พ.ศ. + windows-874, converted only at file read/write.
- Stores with < 60 days of sales data show as red `tr.flag-red` rows ("ผิดปกติ").
- %ชดเชย allocations across new stores must total exactly 100%.
- `k2-competitors.html` (**added 2026-08-06**, sidebar entry right after กำหนดปัจจัยภายนอก) is the competitor **brand master** (11 rows, codes 01–11, Thai + English names) copied verbatim from the legacy K2 screen; it feeds the "ร้านคู่แข่ง (Master)" dropdown in the document page. Do not confuse it with `document_competitors`, which holds per-branch competitor rows imported from ALLMAP with their own alphanumeric ids.
- 8 permission role groups (00 Default … 10 UserViewer) — reference table in `k2-permissions.html` (page removed from sidebar 2026-08-05; roles are mapped to existing-system auth-backend groups).
- `k2-document.html` has a role-switcher dropdown demoing all **5** workflow views client-side via `data-editrole` / `data-roleonly` / `.edit-only` toggling (the two accounting roles were dropped with steps 04/05).
- `k2-database.html` (ER diagram + 16-table schema) and the BPMN flowchart in `k2-flow.html` are additions **beyond the SRS**. The schema normalizes SRS/legacy naming into target BE/FE names such as `operator_assignments`, `external_factors`, and `audit_logs`; don't treat table names or added FK choices as SRS-mandated.
