# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, Thai-language, click-through HTML prototype of **ระบบประกันรายได้ (K2)** — an income-guarantee system that compensates 7-Eleven franchise "Store Partner (SP)" stores whose sales drop when a new 7-Eleven opens within an impact radius (1 km Bangkok/metro, 2 km provincial). "SBP" = Store Business Partner. "K2" refers to the BPM/workflow platform the real system runs on. The prototype implements every screen from the SRS **"RDM-SRS ประกันรายได้-K2 Version 3.1"** (PDF in repo root).

The repo has since grown around the prototype into the project's design/delivery hub. Four layers, from source to deliverable:

1. **The HTML prototype** (repo root + `assets/`) — no build/lint/test tooling; view with `open index.html` or `python3 -m http.server`. Only external dependency is Google Fonts (`assets/sbp.css` line 5); everything else works offline.
2. **Living design docs** — `database.md` / `workflow.md` / `api.md` mirrored by `plan-database.html` / `plan-flow.html` / `plan-api.html` (see "Living docs" below).
3. **Implementation specs** for building the real system — `plan-fe.md`, `plan-be.md`, `checklist-fe.md`, `checklist-be.md`, `REACT-TODO-CHECKLIST.md` — plus a working React port in `react-app/` (the only part with real build tooling).
4. **LLDD deliverables** — 40 low-level design documents in `LLDD/md/`, generated to PDF/DOCX by `tools/build_lldd_documents.py`.

Several filenames contain Thai characters — always quote paths in shell commands.

## Commands

The prototype itself has none (plain HTML/CSS/JS). The tooling that exists:

```sh
# React port (react-app/)
cd react-app
npm run dev:mock   # ★ dev server WITH MSW mock of /api/v1/* per api.md — use this; plain `npm run dev` shows errors on data pages
npm run build      # tsc --noEmit + vite build
npm run lint       # eslint

# Document generation (system python3 has the deps: python-docx, reportlab, PIL, lxml)
python3 tools/build_lldd_documents.py --formats md,docx,pdf   # LLDD/md → LLDD/pdf + LLDD/word + flow PNGs (manifest.json lists generated files)
python3 tools/build_integrated_srs.py                         # integrated SRS DOCX/PDF → output/srs/
node tools/capture_srs_screenshots.mjs                        # page screenshots → output/srs/screenshots/
```

`output/` and `tmp/` are generated/scratch — never edit by hand. In `LLDD/`, the markdown under `LLDD/md/` is the source; `LLDD/pdf/`, `LLDD/word/`, `LLDD/assets/flows/` are regenerated.

## Architecture (prototype)

Three moving parts: 20 HTML pages, one stylesheet (`assets/sbp.css`), one script (`assets/sbp.js`, ES5 IIFE, no dependencies). The header and sidebar do **not** exist in the HTML — `sbp.js` injects them at runtime on every page.

Exception: `ประเด็นหารือ-preaccept-workflow.html` (discussion doc: pre-accept stores can't start workflow, Job 5 ↔ Job 8b) is a standalone self-styled page — plain `<body>`, no `sbp.js`, not in `MODULES`. Don't retrofit the page contract onto it or copy it as a template.

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

`data-page`/`data-module` equal the filename base; `data-crumb` is the breadcrumb leaf. Use `k2-document.html` as the template for new pages — `index.html` deviates (different title suffix, no `data-crumb`). Page-specific CSS goes in an inline `<style>` in that page's head; page-specific JS in an inline `<script>` **after** the `sbp.js` include (so `window.SBP.toast` exists). There are no per-page asset files.

**Adding a page = 2 steps**: (1) create the HTML file following the contract above, (2) add an entry to the `MODULES` array in `assets/sbp.js` (~line 52) — `{key, label, href, icon, group}`. `MODULES` is the single registry driving the sidebar and breadcrumb; sidebar groups render in first-appearance order (current groups: `ระบบประกันรายได้ (SBP Mall)`, `Flow`, `Database`, `Plan` — the `(SBP Mall)` suffix signals this is the SBP Mall web front per the SDD). `plan-email.html` (Email Template — 8 templates EM-01–08 with a self-contained WYSIWYG editor: toolbar, variable chips, tables, sticky save) lives in the SBP Mall group despite its `plan-` filename.

A module entry may instead carry `children: [{key, label, href}]` (no top-level `href`) to render a collapsible submenu — used by `เอกสาร` → รอดำเนินการ (`k2-list-waiting.html`) / ที่เกี่ยวข้อง (`k2-list-related.html`). A third child ข้อมูลผิดปกติ (`k2-list-abnormal.html`) is commented out in MODULES (and its index.html shortcuts, and its 2-endpoint API group in plan-api.html) pending a keep-or-drop decision — the page file still works. The two k2-list-waiting/related pages are near-identical copies differing only in a hardcoded `MODE` const, `<title>`, and body attrs — apply fixes to both. Active-child detection order: exact `file+query` match → `key` equals `data-page` → same file. `k2-document.html` is intentionally not in the sidebar (reached by clicking table rows).

Note: `sbp.js` also has a `data-nav="application"` sidebar mode and `switchStep()` navigation — legacy from deleted pages (`application*.html`, `recruitment.html`). Do not use or copy that mode.

### Behavior hooks (all in sbp.js, wired via one delegated click handler)

Interactivity is simulated by declaring attributes/classes in markup:

- `data-href` navigates; `data-toast`/`data-ack` (+ optional `data-kind="ok|del"`) fire a toast instead of a real action.
- `table.data` rows with `.icon-view` / `.icon-edit` / `.icon-del` buttons get auto-generated view/edit modals and confirm-delete. `[data-add-row="tableId"]` opens an add-row modal.
- The modal engine is driven by `data-entity` on the table, keyed to hand-written `SCHEMAS` in `sbp.js` (~line 424). Schema fields map to columns **by exact header text** — renaming a `<th>` silently breaks the modal round-trip. `data-entity="k2doc"` bypasses modals and populates the `#openedDoc` detail panel instead.
- Tabs: container `[data-tabs]` with child `.tab[data-tab=key]` toggles every `[data-tabpane]` **document-wide** whose key doesn't match.
- Charts: `<div data-chart="bar|donut|spark" data-values data-labels data-colors data-center>` renders inline SVG. All other diagrams (BPMN flowchart in k2-flow, ER diagram in k2-database, AllMap map in k2-document, per-endpoint flowcharts in plan-api) are hand-authored inline SVG — no chart/diagram libraries.
- Public API is only `window.SBP.toast(msg, kind)`.

### Styling

Design tokens live in `:root` of `sbp.css`. The app accent is `--primary` (#2f6fed blue) with teal secondary; the 7-Eleven brand colors (`--seven-*`) are for the header logo **only**. Status chips: `.pill` (status with dot) vs `.chip` (data labels) — not interchangeable. `table.data` needs a `.table-wrap` wrapper for horizontal scroll. Elements with class `reveal` are invisible until JS adds `.in`. Modals need both `display:flex` and `.show` to appear.

## Requirements documents (source-of-truth order)

1. `RDM-SRS ประกันรายได้-K2.pdf` — the SRS v3.1, ultimate requirements source. `SRS_Income_Compensation_v3.1.md` is its markdown conversion.
2. `RDM-SRS-ประกันรายได้-K2-รายการหน้าจอ.md` (455 lines) — detailed screen inventory: per-screen fields, validations, verbatim popup texts, role behavior table.
3. `ประกันรายได้-K2-รายการหน้าจอ.md` (160 lines) — condensed companion keyed to SRS section numbers, with section_codes and the 8 permission roles. **Not a duplicate** of #2 despite the similar name.
4. `PLAN-checklist-prototype.md` — implementation-status checklist mapping SRS sections 3.1.1–3.1.9 to HTML files. Internally inconsistent: some checkboxes are `[ ]` but the bottom summary says they were completed later — verify in the HTML before re-implementing anything.

Thai popup/validation strings in the docs are specified verbatim from the SRS and implemented to match exactly — do not paraphrase them when editing pages.

`FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0.pdf` (29 pages) describes the 11 backend batch entry points (Jobs 1–10 + 8b StartK2WorkFlow) that feed the K2 system; it is the sole requirements source for `job-batch.html` (batch-job console screen) and is not referenced by the K2 screen docs.

`08102025 SDD ปรับกระบวนการบัญชีประกันรายได้ เพื่อตรวจสอบ.pdf` (SDD v7.5) is the source of the accounting-process change (workflow steps 04/05 cut); `SDD-บัญชีประกันรายได้-gap-analysis.md` audits the prototype against it. `workflow_status_document.md` is the status × action × next-actor × email transition table.

**"SDD GI"** = `SDD ปรับปรุงการชดเชยรายได้ในระบบ SBP GI(2402026).pptx` (82 slides, 24/02/2026), converted to `SDD-GI-Compensation/SDD-ปรับปรุงการชดเชยรายได้-SBP-GI.md`. It is the newest requirements source and overrides earlier rules where they conflict: new approval limits (GM 50,000 / AVP 300,000 per item), self-service document reopening after หยุด/ไม่เห็นควรชดเชย (kills the ~20,000 THB/month SR cost), pending-work screen with auto-assign to the previous owner, section-01 rename to หน่วยงานส่งเสริมธุรกิจ SBP with senior-officer-level access, immediate flow-end on เห็นควรไม่ชดเชย at 01/02, zero-amount month 1–3/month-4 rule, and DSA all-store visibility. Acting (รักษาการ) positions cannot be approvers (positions come from HR Connect).

Current Batch Monitor decision: `LLDD/*/LLDD-FE-Batch-Monitor.*` is scoped to only two implementation tabs — `แบบฟอร์มพารามิเตอร์` and `ประวัติการรัน`. Flowchart/process details and database/table usage for batch jobs are reference material for developers only; do not treat them as FE deliverables, SRS requirements, or page-level API/DB sections for this document. `plan-api.html` must keep Batch Job Admin as endpoint reference only (no Batch flowchart tab, no Database + SQL tab for that group), and `plan-database.html` must present `job_configs` / `job_run_histories` as schema reference only, not as a Batch Monitor tab design.

Flow pages live in sidebar group `Flow`: `flow-fgi.html` = FGI/FCS batch pipeline, `k2-flow.html` = K2 approval workflow, and `plan-flow.html` = combined FGI/FCS + K2 target flow. Database pages live in sidebar group `Database`: `fgi-database.html` = FGI/FCS pipeline schema, `k2-database.html` = K2 documents/workflow schema, and `plan-database.html` = combined 29-table target schema (zones A = FGI/FCS, B = K2 documents/workflow, C = shared master/config). `plan-api.html` (sidebar group `Plan`) documents the 44-endpoint / 9-group REST API spec, including per-endpoint example SQL in `SQL_BY_PATH` (keyed `'METHOD path'`) and flowchart specs in `FLOWCHART_BY_PATH` for the 4 complex endpoints. Target database names use English `lower_snake_case` consistently; source tags — (FGI/FCS), (K2), or (ใหม่) — still tie each object back to the requirement documents and should be preserved.

## Living docs: database.md, workflow.md, and api.md (MUST read & keep in sync)

`database.md`, `workflow.md`, and `api.md` in the repo root are the canonical markdown summaries of the new-system design:

- `database.md` — the 29-table target schema, mirrors `plan-database.html` (data spine, zones A/B/C, cross-system keys, P0/P1 fixes).
- `workflow.md` — the end-to-end flow, mirrors `plan-flow.html` plus the sequence diagrams `old-flow.png` (legacy, 7 lanes incl. EAI and K2) and `new-flow.png` (target, 5 lanes).
- `api.md` — the 44-endpoint / 9-group REST spec, mirrors `plan-api.html` (per-endpoint modal structure, business rules bound to endpoints, the commented abnormal-stores group).

**2026-08-05 decision — reuse the existing SBP system for RBAC and operator assignment:** the current SBP production system (`SBP/` directory: `srm-sps-spsap-web-frontend` + `-sbp-bff` + `-store-backend`, see the three analysis `.md` files in `SBP/`) already provides menu permissions (auth-backend/ABS groups/menus/permissions per URL, managed via the existing `/setting/manage-user-rights` page) and operator/approver assignment (auth-backend groups + `@srm/glb-workflow` prepared approvers). SBPGI therefore does NOT build these: tables `roles`/`menus`/`menu_permissions`/`user_accounts`/`operator_assignments` and 18 API endpoints (Auth group + operators/roles/menus/menu-permissions/employees-search) were removed from the target design (34→29 tables, 62/10→44/9 endpoints/groups), and `k2-operators.html` + `k2-permissions.html` were removed from MODULES and index.html shortcuts (commented out; files kept for reference). SBPGI receives identity via BFF headers (`x-api-key`, `x-user-id`, `x-user-group-id`, `x-user-permissions`).

**Whenever a conversation touches the database, the flow/workflow, or the API, read the relevant .md file first.** When a design decision changes any of these topics, update the .md file **and** its HTML counterpart (`plan-database.html` / `plan-flow.html` / `plan-api.html`) in the same change so they never drift. The three are cross-coupled: an API change often touches a table (`database.md`) or a flow step (`workflow.md`) — update all affected pairs together. Design changes may also ripple into the LLDD markdown (`LLDD/md/`) and the implementation specs below.

Core architectural premise recorded there: the new system merges **EAI and K2 into SBPGI** — FGI/FCS batch jobs and the K2 document/workflow run in one system on one database. The internal `BPM06001O_/2O_/3O_` file exports through EAI (Jobs 7/8/9) and the K2 REST StartInstance call (Job 8b) are removed, replaced by direct DB writes (Document Service) and an internal Workflow Engine. External interfaces (QSSI, ALLMAP, IAS/MIS, STA, SMTP) keep their existing file/SFTP mechanisms.

## Implementation specs and the React port

The real system will be React (FE) and Node.js + Express + Prisma + PostgreSQL (BE). The spec set is cross-referenced — read in this order for build work:

- `plan-fe.md` / `plan-be.md` — complete build specs ("อ่านจบต้องสร้างได้โดยไม่ต้องถาม").
- `checklist-fe.md` / `checklist-be.md` — phased task lists with runnable acceptance criteria per phase; phases must not be skipped.
- `REACT-TODO-CHECKLIST.md` — per-page component breakdown of all 20 prototype pages.
- Shared FE↔BE contracts: `LLDD/md/FE/LLDD-FE-Integration-Contracts.md` + `LLDD/md/BE/LLDD-BE-API-Common-Contracts.md`.

`react-app/` is the working React + Vite + TypeScript + Tailwind port of the prototype (see its README for the port-status table). Key mappings from the prototype: `MODULES` → `src/data/modules.ts`, `window.SBP.toast` → `useToast`, sbp.js charts → `src/components/charts/`, `sbp.css` tokens → `tailwind.config.ts`. MSW mock handlers (`src/mocks/handlers.ts`) implement `/api/v1/*` per `api.md` — keep them in sync when the API spec changes.

`LLDD/` holds the 40 LLDD delivery documents (source markdown in `LLDD/md/{FE,BE,BE/Jobs}`, portal at `LLDD/index.html`, team/schedule in `LLDD/md/README.md` and `Main-Index-FE-BE-Job.csv`). Project planning docs at root: `estimate-sbpgi-project-hours.md`, `activity-plan-sbp-mall-fe-be.md`, `LLDD-Phase4-4.3-SBP-Operating-Management-Income-Guarantee.md`.

## Domain rules encoded in the prototype

- 5-step approval workflow by section_code (SDD v7.5 cut accounting steps 04/05): 06 (ฝ่าย SBP DSA) → 08 (เจ้าหน้าที่ SBP DSA) → 01 (หน่วยงานส่งเสริมธุรกิจฯ — renamed from ฝ่ายส่งเสริม and widened to senior officers per SDD GI) → 02 (GM) → 03 (AVP). **Approval limits per "SDD GI" (SDD ปรับปรุงการชดเชยรายได้ SBP GI, 24/02/2026, in `SDD-GI-Compensation/`): ≤ 50,000 THB ends at GM (02); 50,001–300,000 routes through AVP (03) then ends (> 300,000 unspecified — pending confirm); replaced the old single 100,000 threshold.** "เห็นควรไม่ชดเชย" at sections 01/02 now ends the flow immediately (no bounce-back). Reopening is allowed: a store+month whose document ended in หยุด/ไม่เห็นควรชดเชย can get a new document without an SR; ไม่เห็นควร (06) auto-queues next month to the same assignee; zero-compensation months 1–3 forward to 01, month 4 = หยุดชดเชย. Document statuses: 6 values (unchanged — status names still use "ฝ่ายส่งเสริม"). Accounting verifies via the SBP Mall report (Preview + Export CSV to Batch) outside the workflow.
- Document numbers: `YYYY/xxxxx` with Buddhist-era year (e.g. 2569/00123).
- Stores with < 60 days of sales data show as red `tr.flag-red` rows ("ผิดปกติ").
- %ชดเชย allocations across new stores must total exactly 100%.
- 8 permission role groups (00 Default … 10 UserViewer) — reference table in `k2-permissions.html` (page removed from sidebar 2026-08-05; roles are mapped to existing-system auth-backend groups).
- `k2-document.html` has a role-switcher dropdown demoing all 7 workflow views client-side via `data-editrole` / `data-roleonly` / `.edit-only` toggling.
- `k2-database.html` (ER diagram + 16-table schema) and the BPMN flowchart in `k2-flow.html` are additions **beyond the SRS**. The schema normalizes SRS/legacy naming into target BE/FE names such as `operator_assignments`, `external_factors`, and `audit_logs`; don't treat table names or added FK choices as SRS-mandated.
