# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, Thai-language, click-through HTML prototype of **ระบบประกันรายได้ (K2)** — an income-guarantee system that compensates 7-Eleven franchise "Store Partner (SP)" stores whose sales drop when a new 7-Eleven opens within an impact radius (1 km Bangkok/metro, 2 km provincial). "SBP" = Store Business Partner. "K2" refers to the BPM/workflow platform the real system runs on. The prototype implements every screen from the SRS **"RDM-SRS ประกันรายได้-K2 Version 3.1"** (PDF in repo root).

No build, lint, test, or package tooling exists — it is plain HTML/CSS/JS. To view: `open index.html` or `python3 -m http.server`. The only external dependency is Google Fonts (Prompt + Sarabun), imported from `assets/sbp.css` line 5; everything else works offline.

Several filenames contain Thai characters — always quote paths in shell commands.

## Architecture

Three moving parts: 17 HTML pages, one stylesheet (`assets/sbp.css`), one script (`assets/sbp.js`, ES5 IIFE, no dependencies). The header and sidebar do **not** exist in the HTML — `sbp.js` injects them at runtime on every page.

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

**Adding a page = 2 steps**: (1) create the HTML file following the contract above, (2) add an entry to the `MODULES` array in `assets/sbp.js` (~line 50) — `{key, label, href, icon, group}`. `MODULES` is the single registry driving the sidebar and breadcrumb; sidebar groups render in first-appearance order (current groups: `ระบบประกันรายได้ (SBP Mall)`, `Flow`, `Database`, `Plan` — the former `ผู้ดูแลระบบ` and `Job` items were merged into `ระบบประกันรายได้ (SBP Mall)`; the `(SBP Mall)` suffix signals this is the SBP Mall web front per the SDD).

A module entry may instead carry `children: [{key, label, href}]` (no top-level `href`) to render a collapsible submenu — used by `เอกสาร` → รอดำเนินการ (`k2-list-waiting.html`) / ที่เกี่ยวข้อง (`k2-list-related.html`). A third child ข้อมูลผิดปกติ (`k2-list-abnormal.html`) is commented out in MODULES (and its index.html shortcuts) pending a keep-or-drop decision — the page file still works. The two k2-list-waiting/related pages are near-identical copies differing only in a hardcoded `MODE` const, `<title>`, and body attrs — apply fixes to both. Active-child detection order: exact `file+query` match → `key` equals `data-page` → same file. `k2-document.html` is intentionally not in the sidebar (reached by clicking table rows).

Note: `sbp.js` also has a `data-nav="application"` sidebar mode and `switchStep()` navigation — legacy from deleted pages (`application*.html`, `recruitment.html`). Do not use or copy that mode.

### Behavior hooks (all in sbp.js, wired via one delegated click handler)

Interactivity is simulated by declaring attributes/classes in markup:

- `data-href` navigates; `data-toast`/`data-ack` (+ optional `data-kind="ok|del"`) fire a toast instead of a real action.
- `table.data` rows with `.icon-view` / `.icon-edit` / `.icon-del` buttons get auto-generated view/edit modals and confirm-delete. `[data-add-row="tableId"]` opens an add-row modal.
- The modal engine is driven by `data-entity` on the table, keyed to hand-written `SCHEMAS` in `sbp.js` (~line 365). Schema fields map to columns **by exact header text** — renaming a `<th>` silently breaks the modal round-trip. `data-entity="k2doc"` bypasses modals and populates the `#openedDoc` detail panel instead.
- Tabs: container `[data-tabs]` with child `.tab[data-tab=key]` toggles every `[data-tabpane]` **document-wide** whose key doesn't match.
- Charts: `<div data-chart="bar|donut|spark" data-values data-labels data-colors data-center>` renders inline SVG. All other diagrams (BPMN flowchart in k2-flow, ER diagram in k2-database, AllMap map in k2-document) are hand-authored inline SVG — no chart/diagram libraries.
- Public API is only `window.SBP.toast(msg, kind)`.

### Styling

Design tokens live in `:root` of `sbp.css`. The app accent is `--primary` (#2f6fed blue) with teal secondary; the 7-Eleven brand colors (`--seven-*`) are for the header logo **only**. Status chips: `.pill` (status with dot) vs `.chip` (data labels) — not interchangeable. `table.data` needs a `.table-wrap` wrapper for horizontal scroll. Elements with class `reveal` are invisible until JS adds `.in`. Modals need both `display:flex` and `.show` to appear.

## Requirements documents (source-of-truth order)

1. `RDM-SRS ประกันรายได้-K2.pdf` — the SRS v3.1, ultimate requirements source.
2. `RDM-SRS-ประกันรายได้-K2-รายการหน้าจอ.md` (455 lines) — detailed screen inventory: per-screen fields, validations, verbatim popup texts, role behavior table.
3. `ประกันรายได้-K2-รายการหน้าจอ.md` (160 lines) — condensed companion keyed to SRS section numbers, with section_codes and the 8 permission roles. **Not a duplicate** of #2 despite the similar name.
4. `PLAN-checklist-prototype.md` — implementation-status checklist mapping SRS sections 3.1.1–3.1.9 to HTML files. Internally inconsistent: some checkboxes are `[ ]` but the bottom summary says they were completed later — verify in the HTML before re-implementing anything.

Thai popup/validation strings in the docs are specified verbatim from the SRS and implemented to match exactly — do not paraphrase them when editing pages.

`FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0.pdf` (29 pages) describes the 11 backend batch entry points (Jobs 1–10 + 8b StartK2WorkFlow) that feed the K2 system; it is the sole requirements source for `job-batch.html` (batch-job console screen) and is not referenced by the K2 screen docs.

Flow pages live in sidebar group `Flow`: `flow-fgi.html` = FGI/FCS batch pipeline, `k2-flow.html` = K2 approval workflow, and `plan-flow.html` = combined FGI/FCS + K2 target flow. Database pages live in sidebar group `Database`: `fgi-database.html` = FGI/FCS pipeline schema, `k2-database.html` = K2 documents/workflow schema, and `plan-database.html` = combined 34-table target schema (zones A = FGI/FCS, B = K2 documents/workflow, C = shared master/config). `plan-api.html` (sidebar group `Plan`) documents the 61-endpoint / 10-group REST API spec (an abnormal-stores group of 2 endpoints is commented out pending the keep-or-drop decision). Target database names use English `lower_snake_case` consistently; source tags — (FGI/FCS), (K2), or (ใหม่) — still tie each object back to the requirement documents and should be preserved.

## Living docs: database.md, workflow.md, and api.md (MUST read & keep in sync)

`database.md`, `workflow.md`, and `api.md` in the repo root are the canonical markdown summaries of the new-system design:

- `database.md` — the 34-table target schema, mirrors `plan-database.html` (data spine, zones A/B/C, cross-system keys, P0/P1 fixes).
- `workflow.md` — the end-to-end flow, mirrors `plan-flow.html` plus the sequence diagrams `old-flow.png` (legacy, 7 lanes incl. EAI and K2) and `new-flow.png` (target, 5 lanes).
- `api.md` — the 61-endpoint / 10-group REST spec, mirrors `plan-api.html` (per-endpoint modal structure, business rules bound to endpoints, the commented abnormal-stores group).

**Whenever a conversation touches the database, the flow/workflow, or the API, read the relevant .md file first.** When a design decision changes any of these topics, update the .md file **and** its HTML counterpart (`plan-database.html` / `plan-flow.html` / `plan-api.html`) in the same change so they never drift. The three are cross-coupled: an API change often touches a table (`database.md`) or a flow step (`workflow.md`) — update all affected pairs together.

Core architectural premise recorded there: the new system merges **EAI and K2 into SBPGI** — FGI/FCS batch jobs and the K2 document/workflow run in one system on one database. The internal `BPM06001O_/2O_/3O_` file exports through EAI (Jobs 7/8/9) and the K2 REST StartInstance call (Job 8b) are removed, replaced by direct DB writes (Document Service) and an internal Workflow Engine. External interfaces (QSSI, ALLMAP, IAS/MIS, STA, SMTP) keep their existing file/SFTP mechanisms.

## Domain rules encoded in the prototype

- 5-step approval workflow by section_code (SDD v7.5 cut accounting steps 04/05): 06 (ฝ่าย SBP DSA) → 08 (เจ้าหน้าที่ SBP DSA) → 01 (ฝ่ายส่งเสริมธุรกิจฯ) → 02 (GM OPT) → 03 (AVP OPT). Compensation > 100,000 THB routes through AVP (03) then ends; ≤ 100,000 ends at GM (02). Document statuses: 6 values (5 "รอ…ดำเนินการ" + "เสร็จสิ้นดำเนินการ"). Accounting verifies via the SBP Mall report (Preview + Export CSV to Batch) outside the workflow.
- Document numbers: `YYYY/xxxxx` with Buddhist-era year (e.g. 2569/00123).
- Stores with < 60 days of sales data show as red `tr.flag-red` rows ("ผิดปกติ").
- %ชดเชย allocations across new stores must total exactly 100%.
- 8 permission role groups (00 Default … 10 UserViewer) — see `k2-permissions.html`.
- `k2-document.html` has a role-switcher dropdown demoing all 7 workflow views client-side via `data-editrole` / `data-roleonly` / `.edit-only` toggling.
- `k2-database.html` (ER diagram + 16-table schema) and the BPMN flowchart in `k2-flow.html` are additions **beyond the SRS**. The schema normalizes SRS/legacy naming into target BE/FE names such as `operator_assignments`, `external_factors`, and `audit_logs`; don't treat table names or added FK choices as SRS-mandated.
