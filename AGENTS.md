# Repository Guidelines

## Project Structure & Module Organization

This repository is a static Thai-language HTML prototype for the SBP/K2 income-guarantee workflow. Source pages live in the repository root, for example `index.html`, `k2-document.html`, `job-batch.html`, and `plan-api.html`. Shared assets are limited to `assets/sbp.css` and `assets/sbp.js`.

Every K2 page should follow the existing page contract: a `<body>` with `data-page`, `data-nav`, `data-module`, and optional `data-crumb`; an empty `<aside id="sidebar"></aside>`; page content inside `<main class="content">`; and `assets/sbp.js` loaded at the end. Add new sidebar entries to the `MODULES` array in `assets/sbp.js`.

## Build, Test, and Development Commands

There is no build, package, lint, or test tooling. View locally with:

```sh
python3 -m http.server
```

Then open `http://localhost:8000/`. For a direct file preview on macOS, use:

```sh
open index.html
```

Use browser inspection for layout and interaction checks after edits.

## Coding Style & Naming Conventions

Use plain HTML, CSS, and dependency-free JavaScript. Keep shared styles in `assets/sbp.css`; put page-specific CSS in an inline `<style>` in that page head. Put page-specific JavaScript after the shared `assets/sbp.js` include so `window.SBP.toast()` is available.

Use filename-based keys: `k2-report.html` should use `data-page="k2-report"` and `data-module="k2-report"`. Preserve Thai labels, popup text, source tags such as `(FGI/FCS)`, `(K2)`, `(ใหม่)`, and document number formats exactly.

For target BE/FE database design, use English `lower_snake_case` for table and column names. Keep API payload examples in their existing camelCase style unless the API convention is changed explicitly.

## Testing Guidelines

No automated tests exist. Manually verify changed pages in a browser, including sidebar rendering, breadcrumbs, modals, tabs, tables, SVG charts, and responsive behavior. When editing table headers used by modal schemas, confirm view/edit/add/delete flows still work because schema mapping depends on exact header text.

## Commit & Pull Request Guidelines

Git history is minimal and uses short messages such as `update` and `Initial commit: SBP prototype HTML pages`. Prefer concise imperative commit messages, for example `Update K2 report filters`.

Pull requests should include a brief summary, changed pages/assets, manual verification steps, and screenshots for visual changes. Link the relevant requirement source when behavior comes from the SRS or batch-job documentation.

## Agent-Specific Instructions

Read `CLAUDE.md` before making substantial changes. Quote paths containing Thai characters in shell commands. Do not recreate the shared header or sidebar in individual pages; `assets/sbp.js` owns them.
