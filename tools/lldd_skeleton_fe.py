"""lldd_skeleton_fe.py — ตัวสร้างบล็อก "Skeleton Code" ฝั่ง Frontend สำหรับเอกสาร LLDD

entry point เดียว: ``fe_skeleton_blocks(topic, ctx)`` -> ``list[dict]``

โมดูลนี้ **ไม่ import อะไรจาก build_lldd_documents.py** (กัน circular import)
แต่ประกาศ helper p/h/bullets/table/code ของตัวเองที่คืน dict รูปแบบเดียวกับ renderer

โค้ดที่ผลิตออกมาอิง convention จริงของ portal `SBP/srm-sps-spsap-web-frontend` (build target `sbpm`):
  Next.js 16 App Router (`output: "export"`, ทุกหน้า `'use client'`) · TypeScript strict · alias `@/* -> src/*`
  PrimeReact 10 ห่อด้วย component กลาง (`@/components/Form`, `@/components/Table`)
  react-hook-form 7 + yup · Zustand 5 (`permissionStore`) · axios instance กลาง `@/lib/apiClient`
  @tanstack/react-query 5 · exceljs/file-saver สำหรับ Excel
  **ไม่มี chart library ในโปรเจกต์** — โมดูลนี้จึงไม่ผลิตโค้ดกราฟใด ๆ

ทุกอย่าง data-driven จาก Topic ที่รับเข้ามา (apis / fields / actions / scope)
เอกสารคนละฉบับจึงได้ skeleton คนละชุด
"""

from __future__ import annotations

import re
from typing import Any, Iterable

__all__ = ["fe_skeleton_blocks"]


# ---------------------------------------------------------------------------
# block helpers (รูปแบบเดียวกับ renderer ใน build_lldd_documents.py)
# ---------------------------------------------------------------------------


def p(text: str) -> dict[str, Any]:
    return {"type": "p", "text": text}


def h(level: int, text: str) -> dict[str, Any]:
    return {"type": f"h{level}", "text": text}


def bullets(items: Iterable[str]) -> dict[str, Any]:
    return {"type": "bullets", "items": list(items)}


def table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> dict[str, Any]:
    return {"type": "table", "headers": list(headers), "rows": [list(r) for r in rows]}


def code(text: str, lang: str = "ts") -> dict[str, Any]:
    return {"type": "code", "text": text.strip("\n"), "lang": lang}


# ---------------------------------------------------------------------------
# profile ต่อเอกสาร
# ---------------------------------------------------------------------------

ROUTE_BASE = "/sgi"

PROFILES: dict[str, dict[str, Any]] = {
    # domain = "integration" (ไม่ใช่ "common") เพื่อไม่ให้บล็อก types เขียนทับไฟล์ common.ts
    # ที่ประกาศไว้แล้วในบล็อก "types/helper กลาง" ของเอกสารฉบับเดียวกัน
    "Integration-Contracts": {"kind": "contracts", "domain": "integration", "routes": []},
    "Foundation": {"kind": "foundation", "domain": "lookup", "routes": []},
    # 2026-08-07: เอกสาร LLDD-FE-Overview ถูกลบออกจากชุดส่งมอบ (หน้า Dashboard ยกเลิก ·
    # งาน shell ที่เหลือซ้ำกับ FE-Foundation) จึงไม่มี profile "Overview" อีกต่อไป
    "Document-Lists": {
        "kind": "list",
        "domain": "document",
        "routes": [
            ("document/waiting", "หน้ารายการเอกสารรอดำเนินการ (GET /sgi/document/tasks)"),
            ("document/related", "หน้าเอกสารที่เกี่ยวข้อง (GET /sgi/document · ปี = required)"),
        ],
    },
    "Create-Document": {
        "kind": "create",
        "domain": "document",
        "routes": [("document/create", "หน้าสร้างเอกสาร: tab ทั่วไป + tab เอกสารจาก FS (hidden iframe)")],
    },
    "Document-Detail": {
        "kind": "detail",
        "domain": "document",
        "routes": [("document/[docNo]", "หน้ารายละเอียดเอกสาร + action panel ตาม role profile")],
    },
    "Report": {
        "kind": "report",
        "domain": "report",
        "routes": [("report/status-summary", "หน้ารายงานตรวจสอบประกันรายได้ (filter + ตารางผลลัพธ์ + Export Excel)")],
    },
    # 2026-08-05/06: หน้า "ผู้ปฏิบัติงาน" และ "สิทธิ์เมนู" ถูกตัดออกจากดีไซน์ถาวร
    # (ใช้ auth-backend ของระบบ SBP เดิมผ่านหน้า /setting/manage-user-rights และ
    #  prepared approver ของ @srm/glb-workflow) — จึงเหลือหน้า master เดียวคือปัจจัยภายนอก
    # 2026-08-07: เปลี่ยนชื่อเอกสาร LLDD-FE-Master-Config -> LLDD-FE-Master-Data
    # (ขอบเขตจริงคือ master 2 ตัวที่มีหน้าจอดูแลของตัวเอง: ปัจจัยภายนอก + รายชื่อคู่แข่ง)
    "Master-Data": {
        "kind": "master",
        "domain": "master",
        "routes": [
            ("master/factors", "ปัจจัยภายนอก (SCR-09)"),
            ("master/competitors", "รายชื่อร้านคู่แข่ง (master แบรนด์ 01-11)"),
        ],
    },
    "Testing-Delivery": {"kind": "testing", "domain": "common", "routes": []},
}

ROLE_PREFIX = "Document-Detail-Role-"
# create = iframe ของหน้า FS ล้วน ๆ (มติ 2026-08-06) จึงไม่มีฟอร์มฝั่ง SBP
NO_FORM_KINDS = {"contracts", "foundation", "testing", "create"}
FILTER_KINDS = {"list", "report", "master"}


def _base_key(topic: Any) -> str:
    """`FE/LLDD-FE-Document-Lists` -> `Document-Lists`"""
    name = str(getattr(topic, "file", "") or "").split("/")[-1]
    for prefix in ("LLDD-FE-", "LLDD-"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return name or "Screen"


def _pascal(text: str) -> str:
    parts = [x for x in re.split(r"[^A-Za-z0-9]+", text) if x]
    return "".join(x[:1].upper() + x[1:] for x in parts) or "Sgi"


def _camel(text: str) -> str:
    pas = _pascal(text)
    return pas[:1].lower() + pas[1:]


def _profile(topic: Any) -> dict[str, Any]:
    key = _base_key(topic)
    if key.startswith(ROLE_PREFIX):
        rest = key[len(ROLE_PREFIX):]
        role_code = rest.split("-")[0]
        return {
            "kind": "role",
            "domain": "document",
            "role_code": role_code,
            "routes": [("document/[docNo]", f"ใช้ร่วมกับหน้า detail — view ของ workflow section {role_code}")],
            "key": key,
        }
    prof = dict(PROFILES.get(key) or {"kind": "list", "domain": _camel(key), "routes": [(key.lower(), getattr(topic, "title", key))]})
    prof["key"] = key
    return prof


# ---------------------------------------------------------------------------
# API helpers + naming (จุดเดียวที่ตั้งชื่อ เพื่อให้ service/types/hook/page ตรงกันเสมอ)
# ---------------------------------------------------------------------------

VERBS = {"GET": "get", "POST": "create", "PUT": "update", "PATCH": "patch", "DELETE": "remove"}

# ---------------------------------------------------------------------------
# endpoint ที่ถูก "ตัดออกจากดีไซน์" แล้ว (api.md — ตัดสินใจ 2026-08-05/06)
# 14 เส้น RBAC/ผู้ปฏิบัติงาน ใช้ auth-backend ของระบบ SBP เดิมแทน จึงห้าม generate
# service/hook/page ให้ endpoint กลุ่มนี้
# ---------------------------------------------------------------------------
CUT_PREFIXES: tuple[tuple[str, str], ...] = (
    ("/operators", "ใช้ group + scope ของ auth-backend (หน้า `/setting/manage-user-rights`)"),
    ("/employees/search", "ใช้ employee backend เดิมของระบบ SBP"),
    ("/roles", "ใช้ auth-backend groups"),
    ("/menus", "ใช้ auth-backend menus (`GET /menus` อ่านอย่างเดียว)"),
    ("/menu-permissions", "ใช้ auth-backend `/groups/{id}/permissions`"),
    ("/auth/", "ใช้ session/cookie ของ BFF (Cognito)"),
)


def _cut_reason(path: str) -> str:
    """คืนเหตุผลถ้า path นี้ถูกตัดจากดีไซน์ (คืน '' ถ้ายังใช้อยู่)"""
    clean = str(path or "").split(" (")[0].strip()
    if clean.startswith("/api/v1"):
        clean = clean[len("/api/v1"):] or "/"
    for prefix, reason in CUT_PREFIXES:
        # `/menus` ตัดเฉพาะ mutation — GET /menus ยังใช้อ่านเมนูอยู่
        if clean == prefix or clean.startswith(prefix.rstrip("/") + "/") or clean == prefix.rstrip("/"):
            return reason
    return ""


# ---------------------------------------------------------------------------
# ไฟล์ที่ "ใช้ร่วมกันหลายเอกสาร" — เอกสารแต่ละฉบับ generate เนื้อหาคนละส่วน
# ต้อง merge เข้าไฟล์เดิม ห้ามเขียนทับ (ประเด็นรีวิว 2026-08-07)
# ---------------------------------------------------------------------------
SHARED_DOMAINS = {"document", "common", "lookup"}


def _shared_note(domain: str, filename: str) -> str:
    if domain not in SHARED_DOMAINS:
        return ""
    return (
        f"⚠️ `{filename}` เป็น **ไฟล์ร่วมของโมดูล SGI** (เอกสาร FE หลายฉบับที่ใช้ domain "
        f"`{domain}` ประกาศไฟล์นี้เหมือนกัน) — เวลา implement ให้ **merge เพิ่ม** เข้าไฟล์เดิม "
        "ห้ามเขียนทับทั้งไฟล์ มิฉะนั้น type/function ของเอกสารฉบับก่อนหน้าจะหายไปเงียบ ๆ"
    )


def _clean_path(path: str) -> str:
    """ตัดหมายเหตุในวงเล็บ และตัด prefix /api/v1 (apiClient baseURL = bffUrl มี /api/v1 อยู่แล้ว)"""
    raw = str(path or "").split(" (")[0].strip()
    if raw.startswith("/api/v1"):
        raw = raw[len("/api/v1"):] or "/"
    return raw or "/"


def _is_concrete(api: Any) -> bool:
    method = str(getattr(api, "method", "") or "").upper()
    path = _clean_path(getattr(api, "path", ""))
    return method in VERBS and "*" not in path and path not in {"", "/"}


def _usable_apis(topic: Any, limit: int) -> list[Any]:
    keep = [
        a for a in (getattr(topic, "apis", None) or [])
        if _is_concrete(a) and not _cut_reason(getattr(a, "path", ""))
    ]
    return keep[:limit]


def _cut_apis(topic: Any) -> list[list[str]]:
    """เส้นที่อยู่ในตาราง API ของเอกสารแต่ถูกตัดออกจากดีไซน์แล้ว"""
    rows: list[list[str]] = []
    for a in getattr(topic, "apis", None) or []:
        reason = _cut_reason(getattr(a, "path", ""))
        if reason:
            rows.append([f"{str(a.method).upper()} {a.path}", str(getattr(a, "purpose", ""))[:70], reason])
    return rows


def _skipped_apis(topic: Any, shown: list[Any]) -> list[str]:
    """เส้นที่ยัง implement อยู่แต่ไม่ถูก generate เพราะเกิน max_apis"""
    shown_ids = {id(a) for a in shown}
    out: list[str] = []
    for a in getattr(topic, "apis", None) or []:
        if id(a) in shown_ids or not _is_concrete(a) or _cut_reason(getattr(a, "path", "")):
            continue
        out.append(f"{str(a.method).upper()} {_clean_path(a.path)}")
    return out


def _path_params(path: str) -> list[str]:
    return re.findall(r"\{([A-Za-z0-9_]+)\}", path)


def _ts_path(path: str) -> str:
    """`/sgi/document/{docNo}/actions` -> template literal ที่ encode path param แล้ว"""
    params = _path_params(path)
    if not params:
        return f"'{path}'"
    expr = path
    for name in params:
        expr = expr.replace("{%s}" % name, "${encodeURIComponent(%s)}" % name)
    return f"`{expr}`"


def _shape(api: Any) -> str:
    resp = getattr(api, "response", None)
    method = str(getattr(api, "method", "GET")).upper()
    path = _clean_path(getattr(api, "path", ""))
    req = getattr(api, "request", None)
    if isinstance(req, dict) and any(k.lower() in {"file", "files"} for k in req):
        return "upload"  # multipart/form-data
    if not isinstance(resp, dict) or not resp:
        return "object"
    if method == "GET" and (resp.get("contentType") or path.endswith("/export")):
        return "blob"
    items = resp.get("items")
    if isinstance(items, list):
        return "page" if ("page" in resp or "total" in resp) else "items"
    return "object"


def _api_names(apis: list[Any]) -> dict[int, dict[str, Any]]:
    """คืน mapping id(api) -> ชื่อ TS ทุกตัวที่ใช้ในเอกสาร (กันชื่อชนกันด้วย suffix)"""
    out: dict[int, dict[str, Any]] = {}
    used_fn: set[str] = set()
    used_key: set[str] = set()
    for api in apis:
        method = str(api.method).upper()
        path = _clean_path(api.path)
        words = [seg for seg in path.split("/") if seg and not seg.startswith("{")]
        base = _pascal("-".join(words))
        if method == "GET" and path.rstrip("/").endswith("}"):
            base += "Detail"
        verb = VERBS[method]
        shape = _shape(api)
        req = getattr(api, "request", None) or {}
        path_params = _path_params(path)
        body_keys = [k for k in req.keys() if k not in path_params] if isinstance(req, dict) else []

        fn = f"{verb}{base}"
        i = 2
        while fn in used_fn:
            fn = f"{verb}{base}{i}"
            i += 1
        used_fn.add(fn)

        key = _camel(base)
        i = 2
        while key in used_key:
            key = f"{_camel(base)}{i}"
            i += 1
        used_key.add(key)

        item_type = f"{base}Item"
        object_response = f"{base}Response" if method == "GET" else f"{_pascal(verb)}{base}Response"
        if shape == "page":
            response_type = f"PageResponse<T.{item_type}>"
        elif shape == "items":
            response_type = f"T.{base}Response"
        elif shape == "blob":
            response_type = "Blob"
        else:
            response_type = f"T.{object_response}"

        out[id(api)] = {
            "api": api,
            "method": method,
            "path": path,
            "raw_path": str(api.path),
            "base": base,
            "verb": verb,
            "shape": shape,
            "fn": fn,
            "key": key,
            "path_params": path_params,
            "body_keys": body_keys,
            "params_type": f"T.{base}Params",
            "request_type": f"T.{_pascal(verb)}{base}Request",
            "object_response": object_response,
            "item_type": f"T.{item_type}",
            "response_type": response_type,
            "query_hook": f"use{base}Query",
            "mutation_hook": f"use{_pascal(verb)}{base}Mutation",
            "download_hook": f"use{base}Download",
        }
    # เส้น /export ใช้ "filter ชุดเดียวกับการค้นหาล่าสุด" -> params type ต้องเป็นตัวเดียวกับ
    # endpoint ค้นหาแม่ (path เดียวกันแต่ไม่มี /export) มิฉะนั้น page.tsx ส่ง type ไม่ตรง hook
    by_path = {n["path"]: n for n in out.values() if n["method"] == "GET"}
    for n in out.values():
        if n["shape"] != "blob" or not n["path"].endswith("/export"):
            continue
        parent = by_path.get(n["path"][: -len("/export")])
        if parent and parent["body_keys"]:
            n["params_type"] = parent["params_type"]
            n["params_source"] = f"{parent['method']} {parent['path']}"
    return out


def _pick(names: dict[int, dict[str, Any]], method: str = "GET", contains: str = "", exclude: str = "", shape: str = "") -> dict[str, Any] | None:
    for n in names.values():
        if n["method"] != method:
            continue
        if contains and contains not in n["path"]:
            continue
        if exclude and exclude in n["path"]:
            continue
        if shape and n["shape"] != shape:
            continue
        return n
    return None


# ---------------------------------------------------------------------------
# TS type inference จากตัวอย่าง payload ใน ApiSpec
# ---------------------------------------------------------------------------


def _ts_scalar(key: str, value: Any) -> str:
    if key.lower() in {"file", "attachment"} and isinstance(value, str):
        return "File"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if value is None:
        return "string | null"
    if isinstance(value, str):
        return "string"
    return "unknown"


def _render_type(key: str, value: Any, indent: int, depth: int = 0) -> str:
    pad = "  " * indent
    if isinstance(value, dict):
        if not value or depth >= 2:
            return "Record<string, unknown>"
        inner = "\n".join(f"{pad}  {k}: {_render_type(k, v, indent + 1, depth + 1)};" for k, v in value.items())
        return "{\n" + inner + f"\n{pad}}}"
    if isinstance(value, list):
        if not value:
            return "unknown[]"
        first = value[0]
        if isinstance(first, dict):
            return _render_type(key, first, indent, depth) + "[]"
        return _ts_scalar(key, first) + "[]"
    return _ts_scalar(key, value)


def _interface(name: str, obj: dict[str, Any], comment: str = "", optional: bool = False, max_fields: int = 14) -> str:
    lines: list[str] = []
    if comment:
        lines.append(f"/** {comment} */")
    if not obj:
        lines.append(f"export type {name} = Record<string, unknown>; // TODO: ประกาศ field จริงตาม contract ของ BE")
        return "\n".join(lines)
    lines.append(f"export interface {name} {{")
    for i, (k, v) in enumerate(obj.items()):
        if i >= max_fields:
            lines.append("  // TODO: field ที่เหลือดูจากตาราง API ในเอกสารนี้")
            break
        mark = "?" if optional else ""
        lines.append(f"  {k}{mark}: {_render_type(k, v, 1)};")
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# fields -> ฟอร์ม / คอลัมน์
# ---------------------------------------------------------------------------

SKIP_VALIDATION_HINTS = ("display only", "readonly", "internal", "column ", "ไม่ใช่คอลัมน์")
TABLE_PREFIXES = ("table.", "resultTable.", "derived.")
SKIP_FIELD_NAMES = {"page", "size"}
ACTION_PRIORITY = ("result", "comment", "compensatePercent")


def _fields(topic: Any) -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for row in getattr(topic, "fields", None) or []:
        if isinstance(row, (list, tuple)) and len(row) >= 4:
            out.append((str(row[0]), str(row[1]), str(row[2]), str(row[3])))
    return out


def _form_fields(topic: Any, prof: dict[str, Any], apis: list[Any], limit: int = 6) -> list[tuple[str, str, str, str]]:
    candidates: list[tuple[str, str, str, str]] = []
    for name, fmt, validation, behavior in _fields(topic):
        if name.startswith(TABLE_PREFIXES) or name in SKIP_FIELD_NAMES:
            continue
        if any(hint in validation.lower() for hint in SKIP_VALIDATION_HINTS):
            continue
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
            continue  # ข้ามชื่อเชิงบรรยาย เช่น "Base URL", "PageResponse<T>"
        candidates.append((name, fmt, validation, behavior))

    if prof["kind"] in FILTER_KINDS:
        param_keys: set[str] = set()
        for api in apis:
            req = getattr(api, "request", None)
            if str(api.method).upper() == "GET" and isinstance(req, dict):
                param_keys |= set(req.keys())
        preferred = [
            f for f in candidates
            if f[0] in param_keys or any(k in f[2].lower() for k in ("search", "select", "picker", "filter"))
        ]
        candidates = preferred or candidates
    elif prof["kind"] in {"detail", "role"}:
        candidates.sort(key=lambda f: (f[0] not in ACTION_PRIORITY,))
    return candidates[:limit]


_ROW_NOISE_TOKENS = {"impacted", "impact", "new", "current"}


def _norm_tokens(name: str) -> frozenset[str]:
    parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", name or "")
    return frozenset(t.lower() for t in parts)


def _table_rows(topic: Any) -> list[tuple[str, str, str, str]]:
    """แถวในตารางฟิลด์ที่เป็นคอลัมน์ของตารางผลลัพธ์ -> (field, header, fmt, rawName)"""
    out: list[tuple[str, str, str, str]] = []
    for name, fmt, validation, behavior in _fields(topic):
        if not name.startswith(("table.", "resultTable.")):
            continue
        if any(hint in validation.lower() for hint in ("internal", "ไม่ใช่คอลัมน์")):
            continue
        field = name.split(".", 1)[1].split("/")[0]
        header = behavior.split(";")[0]
        header = re.sub(r"^คอลัมน์\s*\d+\s*", "", header).strip()
        out.append((field, (header or field)[:34], fmt, name))
    return out


def _item_keys(main: dict[str, Any] | None) -> list[str]:
    """คีย์จริงของ 1 แถวใน response ของ endpoint ค้นหาหลัก (source of truth ของ <Column field>)"""
    if not main:
        return []
    resp = getattr(main["api"], "response", None)
    if not isinstance(resp, dict):
        return []
    items = resp.get("items")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return [str(k) for k in items[0].keys()]
    return []


def _column_fields(topic: Any, limit: int = 10, main: dict[str, Any] | None = None) -> tuple[list[tuple[str, str, str]], list[str]]:
    """คืน (คอลัมน์ที่ generate, ชื่อคอลัมน์ในตารางฟิลด์ที่ยังไม่ได้ผูก)

    **field ของ `<Column>` มาจาก key ของ response item เสมอ** (ไม่ใช่ชื่อในตารางฟิลด์)
    เพื่อไม่ให้ผูกกับ field ที่ไม่มีอยู่จริงใน interface `*Item` ที่บล็อก types สร้าง
    ส่วน header ภาษาไทยดึงจากตารางฟิลด์ด้วยการจับคู่ 2 รอบ (exact -> token match)
    """
    rows = _table_rows(topic)
    keys = _item_keys(main)
    if not keys:
        # ไม่มี response schema -> ใช้ตารางฟิลด์ตามเดิม
        return [(f, hd, fm) for f, hd, fm, _r in rows[:limit]], [f for f, _h, _f2, _r in rows[limit:]]

    by_field = {r[0]: r for r in rows}
    used: set[str] = set()
    resolved: dict[str, tuple[str, str, str, str]] = {}
    # รอบ 1 — ชื่อตรงกันเป๊ะ
    for key in keys:
        row = by_field.get(key)
        if row and row[0] not in used:
            used.add(row[0])
            resolved[key] = row
    # รอบ 2 — จับคู่ด้วย token (ตัดคำนำหน้า impacted/new ทิ้งก่อนเทียบ)
    for key in keys:
        if key in resolved:
            continue
        kt = _norm_tokens(key) - _ROW_NOISE_TOKENS
        best: tuple[str, str, str, str] | None = None
        for row in rows:
            if row[0] in used:
                continue
            rt = _norm_tokens(row[0]) - _ROW_NOISE_TOKENS
            if kt and (kt == rt or kt <= rt):
                best = row
                break
        if best:
            used.add(best[0])
            resolved[key] = best

    cols: list[tuple[str, str, str]] = []
    for key in keys[:limit]:
        row = resolved.get(key)
        header = row[1] if row else key
        fmt = row[2] if row else ("number" if key.lower().endswith(("amount", "days", "no", "percent")) else "string")
        cols.append((key, header, fmt))
    missing = [r[0] for r in rows if r[0] not in used]
    return cols, missing


def _yup_rule(name: str, fmt: str, validation: str, behavior: str) -> str:
    fmt_l, val_l = fmt.lower(), validation.lower()
    required = "required" in val_l and "not required" not in val_l
    enum_values: list[str] = []
    if "|" in fmt and re.fullmatch(r"[A-Za-z0-9_| ]+", fmt.strip()):
        enum_values = [v.strip() for v in fmt.split("|") if v.strip()]

    if "array" in fmt_l:
        rule = "yup.array().of(yup.string().defined())"
    elif any(k in fmt_l for k in ("integer", "number", "decimal")):
        rule = "yup.number().typeError('กรุณาระบุเป็นตัวเลข')"
        if ">= 0" in validation or ">=0" in validation:
            rule += ".min(0, 'ต้องไม่ติดลบ')"
        if "0-100" in validation:
            rule += ".min(0).max(100)"
    elif "boolean" in fmt_l:
        rule = "yup.boolean()"
    elif "file" in fmt_l:
        rule = "yup.mixed<File>()"
        if "5 mb" in val_l or "5mb" in val_l:
            rule += ".test('size', 'ไฟล์ต้องไม่เกิน 5 MB', (f) => !f || f.size <= 5 * 1024 * 1024)"
    else:
        rule = "yup.string()"
        if enum_values:
            rule += ".oneOf([" + ", ".join(f"'{v}'" for v in enum_values) + "])"
        elif "5 digit" in fmt_l or "5 digits" in val_l:
            rule += ".matches(/^\\d{5}$/, 'รหัสร้านต้องเป็นตัวเลข 5 หลัก')"
        elif "yyyy-mm-dd" in fmt_l:
            rule += ".matches(/^\\d{4}-\\d{2}-\\d{2}$/, 'รูปแบบวันที่ต้องเป็น YYYY-MM-DD (ค.ศ.)')"
        elif "yyyy-mm" in fmt_l:
            rule += ".matches(/^\\d{4}-(0[1-9]|1[0-2])$/, 'รูปแบบเดือนต้องเป็น YYYY-MM (ค.ศ.)')"
        elif "yyyy/xxxxx" in fmt_l:
            rule += ".matches(/^\\d{4}\\/\\d{5}$/, 'เลขที่เอกสารต้องเป็น YYYY/xxxxx (ค.ศ.)')"
    if required:
        rule += f".required('กรุณาระบุ {name}')"
    note = behavior.split(";")[0].strip()
    return f"  {name}: {rule}," + (f" // {note[:70]}" if note else "")


def _ts_form_type(fmt: str) -> str:
    fmt_l = fmt.lower()
    if "array" in fmt_l:
        return "string[]"
    if any(k in fmt_l for k in ("integer", "number", "decimal")):
        return "number"
    if "boolean" in fmt_l:
        return "boolean"
    if "file" in fmt_l:
        return "File | null"
    if "|" in fmt and re.fullmatch(r"[A-Za-z0-9_| ]+", fmt.strip()):
        return " | ".join(f"'{v.strip()}'" for v in fmt.split("|") if v.strip())
    return "string"


def _visible_sections(apis: Iterable[Any]) -> list[str]:
    for api in apis:
        resp = getattr(api, "response", None) or {}
        value = resp.get("visibleSections") if isinstance(resp, dict) else None
        if isinstance(value, list) and value:
            return [str(v) for v in value]
    return []


def _editable_sections(apis: Iterable[Any]) -> list[str]:
    for api in apis:
        resp = getattr(api, "response", None) or {}
        value = resp.get("editableSections") if isinstance(resp, dict) else None
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _action_option_dicts(apis: Iterable[Any]) -> list[dict[str, Any]]:
    for api in apis:
        resp = getattr(api, "response", None) or {}
        value = resp.get("actionOptions") if isinstance(resp, dict) else None
        if isinstance(value, list) and value:
            return [o for o in value if isinstance(o, dict)]
    return []


def _action_options(apis: Iterable[Any]) -> list[str]:
    for api in apis:
        resp = getattr(api, "response", None) or {}
        value = resp.get("actionOptions") if isinstance(resp, dict) else None
        if isinstance(value, list) and value:
            out = []
            for opt in value:
                if isinstance(opt, dict):
                    need = "ต้องกรอกความคิดเห็น" if opt.get("requireComment") else "ไม่บังคับความคิดเห็น"
                    out.append(f"{opt.get('label', '')} ({need})")
            return out
    return []


# ---------------------------------------------------------------------------
# 1) ผังไฟล์
# ---------------------------------------------------------------------------


def _file_plan_blocks(nx: dict[str, Any], num: str) -> list[dict[str, Any]]:
    prof, apis = nx["prof"], nx["apis"]
    domain, kind = prof["domain"], prof["kind"]
    rows: list[list[str]] = [
        [f"src/app/(main)/sgi/{route}/page.tsx", f"route page — {purpose}"]
        for route, purpose in prof.get("routes", [])
    ]
    if kind == "role":
        rows += [
            [f"src/components/sgi/document-detail/RoleView{prof['role_code']}.tsx",
             f"component — view เฉพาะ workflow section {prof['role_code']} (อ่าน visibleSections/editableSections จาก API)"],
            [f"src/components/sgi/document-detail/ActionForm{prof['role_code']}.tsx",
             "component — ฟอร์มผลการพิจารณา (result + comment) ของ section นี้"],
            ["src/components/sgi/document-detail/DocumentSection.tsx",
             "component ร่วม — render 1 section ตาม sectionKey (ประกาศครั้งเดียวที่ LLDD-FE-Document-Detail)"],
            ["src/components/sgi/document-detail/ActionPanel.tsx",
             "component ร่วม — กล่อง action ของหน้า detail (ประกาศครั้งเดียวที่ LLDD-FE-Document-Detail)"],
        ]
    elif kind == "detail":
        rows += [
            ["src/components/sgi/document-detail/DocumentSection.tsx", "component — render 1 section ตาม sectionKey + editable"],
            ["src/components/sgi/document-detail/ActionPanel.tsx", "component — radio ผลการพิจารณา + comment + ปุ่มยืนยัน"],
        ]
    elif kind == "create":
        rows.append(["(ไม่มี component ฟอร์ม)",
                     "หน้านี้เป็น iframe ของหน้าสร้างเอกสารระบบ FS ล้วน ๆ (มติ 2026-08-06) — ไม่มีฟอร์ม/ตารางฝั่ง SBP"])
    elif kind == "contracts":
        rows += [
            ["src/types/sgi/common.ts", "types — ApiResponse / PageResponse / ApiError กลางของโมดูล"],
            ["src/lib/sgi/apiError.ts", "helper — แปลง AxiosError เป็นข้อความไทยจาก BE (ไม่ paraphrase)"],
            ["src/utils/sgi/format.ts", "helper — formatMonthThai / formatAmount / docNo (ค.ศ. ทั้งหมด · ไม่แปลง พ.ศ.)"],
        ]
    elif kind == "foundation":
        rows += [
            ["src/app/(main)/sgi/layout.tsx", "layout ของโมดูล + prefetch lookup (ไม่สร้าง QueryClient ใหม่)"],
            ["src/constants/sgi/routes.ts", "route registry ของโมดูล (ใช้ร่วมกับ url ที่มาจาก GET /menus)"],
        ]
    elif kind == "testing":
        rows += [
            ["src/app/(main)/sgi/_test/renderWithProviders.tsx", "test util — ครอบ QueryClientProvider + mock permissionStore"],
            ["src/app/(main)/sgi/**/__tests__/*.test.tsx", "jest + @testing-library/react ต่อหน้า"],
            ["src/services/sgi/__tests__/*.service.test.ts", "unit test ของ service ด้วย axios-mock-adapter"],
        ]
    else:
        comp = _pascal(prof["key"])
        folder = prof["key"].lower()
        # เฉพาะไฟล์ที่ page.tsx import จริงเท่านั้น — ตารางผลลัพธ์ render inline ด้วย <Table> กลาง
        rows.append([f"src/components/sgi/{folder}/{comp}Form.tsx",
                     "component — ฟอร์ม/ฟิลเตอร์ (react-hook-form + yup + FormInputControl)"])
    if apis and kind != "testing":
        methods = ", ".join(sorted({str(a.method).upper() for a in apis}))
        rows += [
            [f"src/services/sgi/{domain}.service.ts", f"service — เรียก BFF ผ่าน apiClient ({methods})"],
            [f"src/hooks/sgi/{domain}.query.ts", "hook — query key factory + useQuery/useMutation + invalidate"],
            [f"src/types/sgi/{domain}.ts", "types — request/response ตาม API contract ของเอกสารนี้"],
        ]
    return [
        h(3, f"{num} ผังไฟล์ที่ต้องสร้าง"),
        p("โครงไฟล์อิง portal เดิม (`srm-sps-spsap-web-frontend`, target `sbpm`) — โมดูล SGI อยู่ใต้ `src/app/(main)/sgi/*` และ import ผ่าน alias `@/*` ทุกจุด"),
        table(["Path ไฟล์", "หน้าที่"], rows),
    ]


# ---------------------------------------------------------------------------
# 2) page.tsx (คนละ template ตามชนิดหน้าจอ)
# ---------------------------------------------------------------------------


def _page_head(route: str, purpose: str, router: bool = False, table_extra: str = "") -> str:
    router_import = "\nimport { useRouter } from 'next/navigation';" if router else ""
    table_syms = ", ".join(sorted({"Column", "Table"} | ({table_extra} if table_extra else set())))
    return f"""'use client';
// {purpose}
// route: {ROUTE_BASE}/{route}  ·  ต้องมี record ใน GET /menus และสิทธิ์ใน GET /groups/current-user/permissions

import {{ useState }} from 'react';{router_import}
// Table/Column import จาก barrel `@/components/Table` เท่านั้น (table.tsx เป็น named export
// และ re-export `Column = PrimeColumn` ไว้แล้ว — ห้าม import จาก 'primereact/column')
import {{ {table_syms} }} from '@/components/Table';
import AccessDenied from '@/components/Permission/AccessDenied';
// permissionStore เป็น named export ของ Zustand store (ไม่มี symbol ชื่อ usePermissionStore ในโปรเจกต์)
import {{ permissionStore }} from '@/stores/permissionStore';"""


# ปุ่มของ portal เดิมเป็น <button className="btn ..."> ตรง ๆ (ดู report-sp-cooperation/page.tsx)
# ไม่มีโมดูล '@/components/Form/Button' — โฟลเดอร์นั้นมีแค่ text-button.tsx / dropdown-button.tsx
BTN_PRIMARY = 'className="btn btn-primary"'
BTN_SECONDARY = 'className="btn btn-secondary"'


def _permission_gate(page_url_const: str = "PAGE_URL", extra: str = "") -> str:
    """โค้ด 2 บรรทัดตาม convention จริง: รอ permission โหลดเสร็จก่อนแล้วค่อยตัดสิน AccessDenied"""
    lines = [
        "  // รอ permission โหลดเสร็จก่อน ไม่งั้นจะเห็น AccessDenied แว่บหนึ่งทุกครั้งที่เข้าหน้า",
        "  if (!isPermissionLoaded) return null;",
        f"  if (!hasPermission({page_url_const}, 'canView')) return <AccessDenied />;",
    ]
    if extra:
        lines.append(extra)
    return "\n".join(lines)


def _columns_jsx(cols: list[tuple[str, str, str]], indent: str = "        ", missing: list[str] | None = None) -> str:
    if not cols:
        return f"{indent}{{/* TODO: ใส่ <Column /> ตามคอลัมน์ในหัวข้อ \"รายละเอียดฟิลด์\" ของเอกสารนี้ */}}"
    out = []
    for field, header, fmt in cols:
        align = ' align="right"' if any(k in fmt.lower() for k in ("number", "decimal", "integer")) else ""
        out.append(f'{indent}<Column field="{field}" header="{header}" sortable{align} />')
    if missing:
        out.append(
            f"{indent}{{/* TODO: ยังขาดอีก {len(missing)} คอลัมน์ตามตารางฟิลด์ของเอกสารนี้: "
            + ", ".join(missing[:8]) + (" …" if len(missing) > 8 else "")
            + " — ต้องให้ BE เพิ่ม field เหล่านี้ใน response ก่อน */}"
        )
    return "\n".join(out)


def _list_page(nx: dict[str, Any]) -> str:
    topic, prof, names = nx["topic"], nx["prof"], nx["names"]
    route, purpose = prof["routes"][0]
    main = _pick(names, "GET", exclude="/store/") or _pick(names, "GET")
    cols, missing = _column_fields(topic, main=main)
    hook = main["query_hook"] if main else "useDocumentsQuery"
    item = main["item_type"].replace("T.", "") if main else "DocumentsItem"
    domain = prof["domain"]
    red_flag = any("salesDataDays" in f[0] for f in _fields(topic))
    row_class = (
        f"\n        rowClassName={{(row: {item}) => (row.salesDataDays < 60 ? 'flag-red' : '')}} // ยอดขายไม่ครบ 60 วัน = แถวผิดปกติ"
        if red_flag else ""
    )
    return f"""{_page_head(route, purpose, router=True)}
import {{ apiErrorMessage }} from '@/lib/sgi/apiError';
import {{ {hook} }} from '@/hooks/sgi/{domain}.query';
import type {{ {item} }} from '@/types/sgi/{domain}';

const PAGE_URL = '{ROUTE_BASE}/{route}';

export default function {_pascal(route)}Page() {{
  const router = useRouter();
  const {{ hasPermission, isPermissionLoaded }} = permissionStore();
  const [query, setQuery] = useState({{ page: 1, size: 20 }});
  // NOTE: เรียก hook ให้ครบก่อน แล้วค่อย early-return (rules of hooks)
  const {{ data, isLoading, isError, error }} = {hook}(query);

{_permission_gate()}

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold">{{/* TODO: หัวข้อหน้าจอตาม SRS */}}</h1>
      {{/* TODO: <{_pascal(prof['key'])}Form onSearch={{(v) => setQuery((q) => ({{ ...q, ...v, page: 1 }}))}} /> */}}
      <Table
        value={{data?.items ?? []}}
        loading={{isLoading}}
        lazy
        paginator
        rows={{query.size}}
        first={{(query.page - 1) * query.size}}
        totalRecords={{data?.total ?? 0}}
        onPage={{(e) => setQuery((q) => ({{ ...q, page: (e.page ?? 0) + 1, size: e.rows ?? q.size }}))}}
        onRowClick={{(e) => router.push(`{ROUTE_BASE}/document/${{encodeURIComponent((e.data as {item}).docNo)}}`)}}
        emptyMessage="ไม่พบข้อมูล"{row_class}
      >
{_columns_jsx(cols, missing=missing)}
      </Table>
      {{isError && <p className="text-red-600">{{apiErrorMessage(error)}}</p>}}
    </div>
  );
}}"""


def _report_page(nx: dict[str, Any]) -> str:
    topic, prof, names = nx["topic"], nx["prof"], nx["names"]
    route, purpose = prof["routes"][0]
    main = _pick(names, "GET", contains="report", exclude="/export") or _pick(names, "GET", exclude="/store/")
    export = _pick(names, "GET", shape="blob") or _pick(names, "GET", contains="/export")
    # หน้ารายงานต้องแสดงครบทุกคอลัมน์ที่ response ส่งมา (SDD สไลด์ 60 = 14 คอลัมน์)
    cols, missing = _column_fields(topic, limit=24, main=main)
    hook = main["query_hook"] if main else "useReportQuery"
    params_type = main["params_type"].replace("T.", "") if main else "ReportParams"
    item = main["item_type"].replace("T.", "") if main else "ReportItem"
    export_hook = export["download_hook"] if export else "useReportExportDownload"
    form_comp = _pascal(prof["key"]) + "Form"
    domain = prof["domain"]
    return f"""{_page_head(route, purpose)}
import {{ {hook}, {export_hook} }} from '@/hooks/sgi/{domain}.query';
import type {{ {params_type}, {item} }} from '@/types/sgi/{domain}';
import {form_comp} from '@/components/sgi/{prof['key'].lower()}/{form_comp}';

const PAGE_URL = '{ROUTE_BASE}/{route}';

export default function {_pascal(route)}Page() {{
  const {{ hasPermission, isPermissionLoaded }} = permissionStore();
  // ยิง API เฉพาะตอนกด "ค้นหาข้อมูล" -> ก่อนหน้านั้น submitted = null และ query ถูก disable
  const [submitted, setSubmitted] = useState<{params_type} | null>(null);
  const {{ data, isFetching }} = {hook}(submitted);
  const exportExcel = {export_hook}();

  const canExport = hasPermission(PAGE_URL, 'canExport');
{_permission_gate()}

  return (
    <div className="flex flex-col gap-4 p-4">
      {{/* "สถานะ" เป็น filter บังคับตัวเดียว — prop ชื่อ onSubmit ต้องตรงกับ component ในหัวข้อฟอร์ม */}}
      <{form_comp} onSubmit={{setSubmitted}} />
      <div className="flex justify-end gap-2">
        {{canExport && (
          <button
            type="button"
            {BTN_SECONDARY}
            disabled={{!submitted || exportExcel.isPending}}
            onClick={{() => submitted && exportExcel.mutate(submitted)}} // ใช้ filter ชุดเดียวกับการค้นหาล่าสุด
          >
            Export Excel
          </button>
        )}}
      </div>
      <Table value={{data?.items ?? []}} loading={{isFetching}} paginator rows={{20}} emptyMessage="ไม่พบข้อมูล">
{_columns_jsx(cols, missing=missing)}
      </Table>
      {{/* TODO: summary line (จำนวนรายการ/ยอดรวม) อ่านจาก data.summary */}}
    </div>
  );
}}"""


def _detail_page(nx: dict[str, Any]) -> str:
    prof, names, apis = nx["prof"], nx["names"], nx["apis"]
    route, purpose = prof["routes"][0]
    sections = _visible_sections(apis) or ["doc-header", "sec-action"]
    detail = _pick(names, "GET", contains="{") or _pick(names, "GET")
    action = _pick(names, "POST", contains="/actions") or _pick(names, "POST")
    detail_hook = detail["query_hook"] if detail else "useDocumentsDetailQuery"
    action_hook = action["mutation_hook"] if action else "useCreateDocumentsActionsMutation"
    domain = prof["domain"]
    section_jsx = "\n".join(
        f"      {{show('{s}') && <DocumentSection sectionKey=\"{s}\" doc={{doc}} editable={{editable('{s}')}} />}}"
        for s in sections[:8]
    )
    return f"""'use client';
// {purpose}
// route: {ROUTE_BASE}/{route}

import {{ useParams }} from 'next/navigation';
import AccessDenied from '@/components/Permission/AccessDenied';
import {{ permissionStore }} from '@/stores/permissionStore';
import DocumentSection from '@/components/sgi/document-detail/DocumentSection';
import ActionPanel from '@/components/sgi/document-detail/ActionPanel';
import {{ {detail_hook}, {action_hook} }} from '@/hooks/sgi/{domain}.query';

const PAGE_URL = '{ROUTE_BASE}/document';

export default function DocumentDetailPage() {{
  const params = useParams<{{ docNo: string }}>();
  const docNo = decodeURIComponent(params.docNo); // docNo = 'YYYY/xxxxx' จึงถูก encode ใน route param
  const {{ hasPermission, isPermissionLoaded }} = permissionStore();
  const {{ data: doc, isLoading }} = {detail_hook}(docNo);
  const submitAction = {action_hook}(docNo);

  // สิทธิ์แสดง/แก้ไขแต่ละ section มาจาก API เท่านั้น — FE ห้ามคำนวณจาก role เอง
  const show = (key: string) => !!doc?.visibleSections?.includes(key);
  const editable = (key: string) => !!doc?.editableSections?.includes(key);

  if (!isPermissionLoaded) return null;
  if (!hasPermission(PAGE_URL, 'canView')) return <AccessDenied />;
  if (isLoading || !doc) return null; // TODO: ใส่ skeleton loading ตาม design

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold">เอกสารเลขที่ {{doc.docNo}}</h1>
{section_jsx}
      {{doc.canAction && (
        <ActionPanel
          options={{doc.actionOptions}}  // render radio จาก actionOptions เท่านั้น ห้าม hardcode
          onSubmit={{(payload) => submitAction.mutate(payload)}} // payload = {{ result, comment }} เท่านั้น
          disabled={{submitAction.isPending}}
        />
      )}}
    </div>
  );
}}"""


def _role_component(nx: dict[str, Any]) -> str:
    prof, apis, names = nx["prof"], nx["apis"], nx["names"]
    code_no = prof["role_code"]
    sections = _visible_sections(apis) or ["doc-header", "sec-action"]
    editable = _editable_sections(apis)
    options = _action_options(apis)
    opt_lines = "\n".join(f"//   - {o}" for o in options) or "//   - (contract ของ role นี้ไม่ระบุ actionOptions)"
    sec_jsx = "\n".join(
        f"      {{show('{s}') && <DocumentSection sectionKey=\"{s}\" doc={{doc}} editable={{editable('{s}')}} />}}"
        for s in sections[:8]
    )
    return f"""'use client';
// RoleView{code_no} — view ของหน้า Document Detail สำหรับ workflow section {code_no}
// editableSections ตาม contract: {', '.join(editable) or '(อ่านอย่างเดียว)'}
// actionOptions ที่ API ส่งให้ role นี้ (ยัง render จาก doc.actionOptions ห้าม hardcode ใน component):
{opt_lines}

import DocumentSection from '@/components/sgi/document-detail/DocumentSection';
import ActionPanel from '@/components/sgi/document-detail/ActionPanel';
import type {{ DocumentsDetailResponse }} from '@/types/sgi/document';

interface Props {{
  doc: DocumentsDetailResponse;
  onSubmitAction: (payload: {{ result: string; comment: string }}) => void;
  submitting?: boolean;
}}

export default function RoleView{code_no}({{ doc, onSubmitAction, submitting }}: Props) {{
  const show = (key: string) => doc.visibleSections.includes(key);
  const editable = (key: string) => doc.editableSections.includes(key);

  return (
    <div className="flex flex-col gap-4">
{sec_jsx}
      {{doc.canAction && (
        <ActionPanel
          options={{doc.actionOptions}}
          onSubmit={{onSubmitAction}}   // TODO: บังคับกรอก comment เมื่อ option.requireComment = true
          disabled={{submitting}}
        />
      )}}
    </div>
  );
}}"""


def _create_page(nx: dict[str, Any]) -> str:
    topic, prof, names = nx["topic"], nx["prof"], nx["names"]
    route, purpose = prof["routes"][0]
    domain = prof["domain"]
    tabs = [str(s) for s in (getattr(topic, "scope", None) or []) if str(s).startswith("Tab")]
    tab_comment = "\n".join(f"//   {t}" for t in tabs) or "//   (scope ไม่ได้ระบุ tab)"
    return f"""'use client';
// {purpose}
{tab_comment}
//
// ⚠️ มติ 2026-08-06: หน้านี้ **ไม่มีฟอร์มฝั่ง SBP** — main card คือ iframe ของหน้าสร้างเอกสาร
//    ของระบบ FS ตรง ๆ (เหมือน k2-create.html) และ `POST /sgi/document` เป็น pipeline/service-token
//    endpoint (Job 8) ไม่ใช่ฟอร์มที่ FE ยิงเอง
// ⚠️ ห้ามอ่าน/เขียน DOM ข้าม iframe (`contentDocument`) — FS อยู่คนละ origin เบราว์เซอร์บล็อกทันที
//    ช่องทางสื่อสารเดียวที่ใช้ได้คือ `postMessage` และต้องตรวจ `event.origin` ทุกครั้ง

import {{ useEffect, useRef, useState }} from 'react';
import AccessDenied from '@/components/Permission/AccessDenied';
import {{ permissionStore }} from '@/stores/permissionStore';

const PAGE_URL = '{ROUTE_BASE}/{route}';
// TODO: ตั้งใน .env.sbpm.<env> — ต้องเป็น origin ของ FS ที่ยืนยันกับทีม FS แล้ว
const FS_IFRAME_URL = process.env.NEXT_PUBLIC_FS_CREATE_DOCUMENT_URL ?? '';
const FS_ORIGIN = process.env.NEXT_PUBLIC_FS_ORIGIN ?? '';

type FsMessage = {{ type: 'FS_DOC_CREATED' | 'FS_DOC_ERROR'; docNo?: string; message?: string }};

export default function CreateDocumentPage() {{
  const {{ hasPermission, isPermissionLoaded }} = permissionStore();
  const fsFrame = useRef<HTMLIFrameElement | null>(null);
  const [result, setResult] = useState<FsMessage | null>(null);

  // รับผลลัพธ์จากหน้า FS ผ่าน postMessage เท่านั้น
  useEffect(() => {{
    const onMessage = (event: MessageEvent<FsMessage>) => {{
      // TODO: ยืนยัน contract ของ message (type/field) กับทีม FS ก่อน UAT
      if (!FS_ORIGIN || event.origin !== FS_ORIGIN) return; // กัน message จาก origin อื่น
      if (event.data?.type === 'FS_DOC_CREATED' || event.data?.type === 'FS_DOC_ERROR') setResult(event.data);
    }};
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }}, []);

  if (!isPermissionLoaded) return null;
  if (!hasPermission(PAGE_URL, 'canManage')) return <AccessDenied />;

  return (
    <div className="flex flex-col gap-4 p-4">
      {{/* main card = iframe ของหน้า FS (สัดส่วนเดียวกับ .fs-frame ใน prototype) */}}
      <iframe
        ref={{fsFrame}}
        src={{FS_IFRAME_URL}}
        title="fs-create-document"
        className="w-full min-h-[720px] border rounded"
      />
      {{result?.type === 'FS_DOC_ERROR' && <p className="text-red-600">{{result.message}}</p>}}
      {{/* หมายเหตุ 4 ขั้นตอน (verbatim จากหน้าจอเดิม) อยู่นอกกรอบ iframe — ดูหัวข้อ Screen Design */}}
    </div>
  );
}}"""


def _master_page(nx: dict[str, Any]) -> str:
    topic, prof, names = nx["topic"], nx["prof"], nx["names"]
    route, purpose = prof["routes"][0]
    list_api = _pick(names, "GET", exclude="search") or _pick(names, "GET")
    save_api = _pick(names, "POST") or _pick(names, "PUT")
    cols, missing = _column_fields(topic, limit=8, main=list_api)
    list_hook = list_api["query_hook"] if list_api else "useFactorsQuery"
    item = list_api["item_type"].replace("T.", "") if list_api else "FactorsItem"
    save_hook = save_api["mutation_hook"] if save_api else "useCreateFactorsMutation"
    domain = prof["domain"]
    return f"""{_page_head(route, purpose, table_extra="TableActionButton")}
// ConfirmDialog เป็น named export (index.ts = `export * from './confirm-dialog'`) และ prop ยืนยัน
// ของ PrimeReact คือ accept/reject — ไม่มี onConfirm; helper confirmDialog() คือรูปแบบที่ทีมใช้จริง
import {{ ConfirmDialog, confirmDialog }} from '@/components/ConfirmDialog';
import {{ {list_hook}, {save_hook} }} from '@/hooks/sgi/{domain}.query';
import type {{ {item} }} from '@/types/sgi/{domain}';

const PAGE_URL = '{ROUTE_BASE}/{route}';

export default function {_pascal(route)}Page() {{
  const {{ hasPermission, isPermissionLoaded }} = permissionStore();
  const [query, setQuery] = useState({{ page: 1, size: 20 }});
  const [editing, setEditing] = useState<Partial<{item}> | null>(null);
  const {{ data, isLoading }} = {list_hook}(query);
  const save = {save_hook}();

  const canManage = hasPermission(PAGE_URL, 'canManage');
{_permission_gate()}

  // ทุก mutation ของ master ต้องแนบ `reason` เพื่อเขียน audit ในทรานแซกชันเดียวกัน
  const confirmSave = (values: Partial<{item}> & {{ reason: string }}) =>
    confirmDialog({{
      severity: 'question',
      header: 'ยืนยันการบันทึก',
      message: 'ต้องการบันทึกการเปลี่ยนแปลงข้อมูล master นี้หรือไม่',
      accept: () => save.mutate(values as never),
    }});

  return (
    <div className="flex flex-col gap-4 p-4">
      {{/* ต้องมี <ConfirmDialog /> อยู่ใน tree หนึ่งตัวเพื่อให้ confirmDialog() มีที่ render */}}
      <ConfirmDialog />
      <div className="flex justify-end">
        {{canManage && (
          <button type="button" {BTN_PRIMARY} onClick={{() => setEditing({{}})}}>
            เพิ่มข้อมูล
          </button>
        )}}
      </div>
      <Table value={{data?.items ?? []}} loading={{isLoading}} paginator rows={{query.size}} emptyMessage="ไม่พบข้อมูล">
{_columns_jsx(cols, missing=missing)}
        <Column
          header="จัดการ"
          body={{(row: {item}) =>
            canManage && (
              // TODO: ใส่ icon component ของทีม (เช่น Edit จาก @/components/Icons)
              <TableActionButton icon={{EditIcon}} severity="primary" tooltipMessage="แก้ไข" onClick={{() => setEditing(row)}} />
            )
          }}
        />
      </Table>
      {{/* TODO: modal ฟอร์มแก้ไข (ดูหัวข้อฟอร์ม) แล้วเรียก confirmSave({{ ...values, reason }}) ตอนกดบันทึก */}}
      {{editing && null}}
    </div>
  );
}}"""


def _foundation_module(nx: dict[str, Any]) -> str:
    names = nx["names"]
    status_api = _pick(names, "GET", contains="status")
    hook = status_api["query_hook"] if status_api else "useDocumentStatusesQuery"
    return f"""'use client';
// src/app/(main)/sgi/layout.tsx — โครง layout ของโมดูล SGI
// (main)/layout.tsx เดิมมี AppHeader / AppSider / LottieLoader / QueryClientProvider อยู่แล้ว
// โมดูลนี้จึง "ห้าม" สร้าง QueryClient ใหม่ และ "ห้าม" สร้าง axios instance ของตัวเอง

import {{ ReactNode }} from 'react';
import {{ {hook} }} from '@/hooks/sgi/lookup.query';

/** route registry ของโมดูล — ใช้ประกอบลิงก์ภายใน ส่วนเมนู/สิทธิ์ยังมาจาก GET /menus เท่านั้น */
export const SGI_ROUTES = {{
  waiting: '{ROUTE_BASE}/document/waiting',
  related: '{ROUTE_BASE}/document/related',
  create: '{ROUTE_BASE}/document/create',
  detail: (docNo: string) => `{ROUTE_BASE}/document/${{encodeURIComponent(docNo)}}`,
  report: '{ROUTE_BASE}/report/status-summary',
}} as const;

export default function SgiLayout({{ children }}: {{ children: ReactNode }}) {{
  // prefetch lookup ที่ทุกหน้าในโมดูลใช้ร่วมกัน (master -> staleTime ยาว)
  {hook}();

  // TODO: ใส่ ErrorBoundary ของโมดูล และ empty state เมื่อ permission ยังโหลดไม่เสร็จ
  return <div className="sgi-module">{{children}}</div>;
}}"""


def _contracts_module(nx: dict[str, Any]) -> str:
    return """// src/types/sgi/common.ts — สัญญากลางที่ทุกหน้าในโมดูล SGI ใช้ร่วมกัน
// envelope ต้องตรงกับ store-backend: { success, data } / { success:false, data:null, error:{code,message} }

export interface ApiError {
  code: string;    // เช่น VALIDATION, ACTION_RESULT_REQUIRED
  message: string; // ข้อความไทย verbatim จาก BE — ห้าม paraphrase ฝั่ง FE
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: ApiError | null;
}

export interface PageResponse<T> {
  page: number;  // >= 1
  size: number;  // <= 100
  total: number;
  items: T[];
}

/** payload ของทุก workflow action — FE ส่งได้แค่ 2 field นี้ ห้ามส่ง nextSection เอง */
export interface DocumentActionRequest {
  result: string;   // ต้องเป็นค่าจาก actionOptions ที่ API ส่งมาเท่านั้น
  comment: string;
}

export interface ActionResponse {
  statusCode: string;
  nextSection: string | null;
  message: string;
}

// ---------------------------------------------------------------------------
// src/lib/sgi/apiError.ts
// ---------------------------------------------------------------------------
import { AxiosError } from 'axios';

export function apiErrorMessage(error: unknown): string {
  const message = (error as AxiosError<{ error?: ApiError }>)?.response?.data?.error?.message;
  if (message) return message;                        // ใช้ข้อความจาก BE ตรง ๆ
  return 'ไม่สามารถเชื่อมต่อระบบได้ กรุณาลองใหม่อีกครั้ง'; // fallback เฉพาะ network/no-response
}

// ---------------------------------------------------------------------------
// src/utils/sgi/format.ts — formatter กลางจุดเดียว · ค.ศ. ทั้ง payload และ display (มติ 2026-08-06)
// ---------------------------------------------------------------------------
export const formatMonthThai = (isoMonth: string): string => {
  const [year, month] = isoMonth.split('-');
  return `${month}/${Number(year) + 543}`;
};

export const formatAmount = (value: number): string =>
  value.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// TODO: ยืนยันรูปแบบวันที่/เดือนกับ SRS ก่อนใช้จริง (บางหน้าจอแสดง ค.ศ. ตามระบบ SBP เดิม)"""


def _testing_module(nx: dict[str, Any]) -> str:
    topic = nx["topic"]
    tests = [str(t) for t in (getattr(topic, "tests", None) or [])][:4]
    cases = "\n".join(f"  it.todo('{t}');" for t in tests) or "  it.todo('เพิ่ม test case ตาม test list ของเอกสาร');"
    return f"""// src/app/(main)/sgi/_test/renderWithProviders.tsx
// jest 30 (next/jest, jsdom) + @testing-library/react + axios-mock-adapter ตาม setup เดิมของ portal

import {{ ReactElement, ReactNode }} from 'react';
import {{ render }} from '@testing-library/react';
import {{ QueryClient, QueryClientProvider }} from '@tanstack/react-query';
import {{ permissionStore }} from '@/stores/permissionStore';

export function renderWithProviders(ui: ReactElement, allowedUrls: string[] = []) {{
  // ปิด retry ในเทสต์ ไม่งั้น assertion ต้องรอ react-query retry
  const client = new QueryClient({{ defaultOptions: {{ queries: {{ retry: false }} }} }});
  // NOTE: เทสต์ของ portal เดิม mock ทั้ง module (`jest.mock('@/stores/permissionStore', ...)`)
  //       ที่นี่เซ็ต state ตรง ๆ ได้เพราะ permissionStore เป็น zustand store
  permissionStore.setState({{
    isPermissionLoaded: true,
    hasPermission: (url: string) => allowedUrls.includes(url),
  }} as never);
  const Wrapper = ({{ children }}: {{ children: ReactNode }}) => (
    <QueryClientProvider client={{client}}>{{children}}</QueryClientProvider>
  );
  return render(ui, {{ wrapper: Wrapper }});
}}

// ---------------------------------------------------------------------------
// ตัวอย่าง test ต่อหน้า (colocated `__tests__/*.test.tsx` ตาม convention เดิม)
// ---------------------------------------------------------------------------
import MockAdapter from 'axios-mock-adapter';
import apiClient from '@/lib/apiClient';

describe('SGI screen', () => {{
  const mock = new MockAdapter(apiClient);
  afterEach(() => mock.reset());

  it('แสดง AccessDenied เมื่อไม่มีสิทธิ์ canView', () => {{
    // TODO: renderWithProviders(<Page />, []) แล้ว expect ข้อความของ AccessDenied
  }});

  it('เรียก API แล้ว render ตารางเมื่อมีสิทธิ์', async () => {{
    mock.onGet(/\\/documents/).reply(200, {{ success: true, data: {{ page: 1, size: 20, total: 0, items: [] }} }});
    // TODO: expect ตารางแสดง emptyMessage
  }});

{cases}
}});"""


PAGE_BUILDERS = {
    "list": _list_page,
    "report": _report_page,
    "detail": _detail_page,
    "create": _create_page,
    "master": _master_page,
    "role": _role_component,
    "foundation": _foundation_module,
    "contracts": _contracts_module,
    "testing": _testing_module,
}

PAGE_TITLES = {
    "list": "page.tsx — หน้ารายการ (permission gate + react-query + Table กลาง)",
    "report": "page.tsx — หน้ารายงาน (filter ที่กดค้นหาแล้วค่อยยิง + Export Excel)",
    "detail": "page.tsx — หน้ารายละเอียดเอกสาร (section gating จาก API)",
    "create": "page.tsx — หน้าสร้างเอกสาร (iframe ของหน้า FS + postMessage)",
    "master": "page.tsx — หน้า master (ตาราง + modal CRUD + reason/audit)",
    "role": "RoleView component — view เฉพาะบทบาทของหน้า Document Detail",
    "foundation": "layout.tsx + route registry ของโมดูล SGI",
    "contracts": "types/helper กลาง (envelope, error message, formatter)",
    "testing": "test harness + ตัวอย่าง test ต่อหน้า",
}


def _page_blocks(nx: dict[str, Any], num: str) -> list[dict[str, Any]]:
    kind = nx["prof"]["kind"]
    builder = PAGE_BUILDERS.get(kind, _list_page)
    lang = "ts" if kind == "contracts" else "tsx"
    return [h(3, f"{num} {PAGE_TITLES.get(kind, 'page.tsx')}"), code(builder(nx), lang)]


# ---------------------------------------------------------------------------
# 3) service
# ---------------------------------------------------------------------------


def _service_blocks(nx: dict[str, Any], num: str) -> list[dict[str, Any]]:
    names, prof = nx["names"], nx["prof"]
    if not names:
        return []
    domain = prof["domain"]
    lines = [
        f"// src/services/sgi/{domain}.service.ts",
        "// apiClient = axios instance กลาง (baseURL = bffUrl ซึ่งรวม /api/v1 แล้ว, withCredentials, refresh-token interceptor, global loading)",
        "// ห้ามสร้าง axios instance ใหม่ และห้าม set Authorization header เอง — session อยู่ใน httpOnly cookie ของ BFF",
        "",
        "import apiClient from '@/lib/apiClient';",
        "__ENVELOPE_IMPORT__",
        f"import type * as T from '@/types/sgi/{domain}';",
        "",
    ]
    for n in names.values():
        method, path = n["method"], n["path"]
        args = [f"{name}: string" for name in n["path_params"]]
        if n["body_keys"]:
            args.append(f"params: {n['params_type']}" if method == "GET" else f"body: {n['request_type']}")
        lines.append(f"/** {method} {n['raw_path']} — {getattr(n['api'], 'purpose', '')} */")
        lines.append(f"export async function {n['fn']}({', '.join(args)}): Promise<{n['response_type']}> {{")
        if n["shape"] == "blob":
            opts = "{ params, responseType: 'blob' }" if n["body_keys"] else "{ responseType: 'blob' }"
            lines.append(f"  const {{ data }} = await apiClient.get<Blob>({_ts_path(path)}, {opts});")
            lines.append("  return data; // TODO: ตั้งชื่อไฟล์จาก content-disposition แล้วบันทึกด้วย file-saver")
        elif n["shape"] == "upload":
            lines.append("  const form = new FormData();")
            lines.append("  form.append('file', body.file); // TODO: ตรวจขนาด <= 5MB และนามสกุลที่อนุญาตก่อนเรียก")
            lines.append(
                f"  const {{ data }} = await apiClient.{method.lower()}<ApiResponse<{n['response_type']}>>({_ts_path(path)}, form, {{"
            )
            lines.append("    headers: { 'Content-Type': 'multipart/form-data' },")
            lines.append("  });")
            lines.append("  return data.data;")
        else:
            call = [_ts_path(path)]
            if method in {"POST", "PUT", "PATCH"}:
                call.append("body" if n["body_keys"] else "undefined")
            if method == "GET" and n["body_keys"]:
                call.append("{ params }")
            if method == "DELETE" and n["body_keys"]:
                call.append("{ data: body }")
            lines.append(f"  const {{ data }} = await apiClient.{method.lower()}<ApiResponse<{n['response_type']}>>({', '.join(call)});")
            lines.append("  return data.data;")
        lines.append("}")
        lines.append("")
    skipped = _skipped_apis(nx["topic"], nx["apis"])
    if skipped:
        lines.append(
            "// TODO: ยังขาดอีก %d เส้นที่ต้องเพิ่มในไฟล์นี้ด้วยรูปแบบเดียวกัน: %s"
            % (len(skipped), ", ".join(skipped))
        )
    cut = _cut_apis(nx["topic"])
    if cut:
        lines.append("// NOTE: เส้น %s ถูกตัดจากดีไซน์แล้ว (ใช้ระบบ SBP เดิม) — ห้ามสร้าง service ให้"
                     % ", ".join(row[0] for row in cut))
    lines.append("// TODO: ยืนยันกับทีม BFF ว่า unwrap envelope { success, data } ที่ชั้นไหน (BFF หรือ FE)")
    text = "\n".join(lines)
    imports = ["ApiResponse"] if "ApiResponse<" in text else []
    if "PageResponse<" in text:
        imports.append("PageResponse")
    envelope = (
        f"import type {{ {', '.join(imports)} }} from '@/types/sgi/common';" if imports else ""
    )
    text = text.replace("__ENVELOPE_IMPORT__\n", envelope + "\n" if envelope else "")
    blocks = [h(3, f"{num} service — `src/services/sgi/{domain}.service.ts`")]
    note = _shared_note(domain, f"src/services/sgi/{domain}.service.ts")
    if note:
        blocks.append(p(note))
    blocks.append(code(text, "ts"))
    return blocks


# ---------------------------------------------------------------------------
# 4) types
# ---------------------------------------------------------------------------


def _types_blocks(nx: dict[str, Any], num: str) -> list[dict[str, Any]]:
    names, prof = nx["names"], nx["prof"]
    if not names:
        return []
    domain = prof["domain"]
    lines = [
        f"// src/types/sgi/{domain}.ts — ตรงกับตาราง API ในเอกสารนี้",
        "// วันที่/เดือนเป็น ค.ศ. ทั้ง payload (ISO) และ display — ไม่แปลงเป็น พ.ศ. (มติ 2026-08-06)",
        "",
        "__ENVELOPE_IMPORT__",
        "",
    ]
    seen: set[str] = set()
    for n in list(names.values())[:3]:
        api = n["api"]
        base, method = n["base"], n["method"]
        req, resp = getattr(api, "request", None), getattr(api, "response", None)
        if isinstance(req, dict) and n["body_keys"]:
            body = {k: v for k, v in req.items() if k in n["body_keys"]}
            name = n["params_type"].replace("T.", "") if method == "GET" else f"{_pascal(n['verb'])}{base}Request"
            if name not in seen:
                seen.add(name)
                lines.append(_interface(name, body, f"{method} {n['raw_path']} — request", optional=(method == "GET")))
                lines.append("")
        if n["shape"] in {"page", "items"} and isinstance(resp, dict):
            items = resp.get("items") or []
            sample = items[0] if items and isinstance(items[0], dict) else {}
            item_name = f"{base}Item"
            if item_name not in seen:
                seen.add(item_name)
                lines.append(_interface(item_name, sample, f"{method} {n['raw_path']} — 1 แถวในตาราง"))
                if n["shape"] == "page":
                    lines.append(f"export type {base}ListResponse = PageResponse<{item_name}>;")
                else:
                    lines.append(f"export interface {base}Response {{ items: {item_name}[]; }}")
                lines.append("")
        elif n["shape"] in {"object", "upload"} and isinstance(resp, dict) and resp:
            name = n["object_response"]
            if name not in seen:
                seen.add(name)
                lines.append(_interface(name, resp, f"{method} {n['raw_path']} — response"))
                lines.append("")
    rest = list(names.values())[3:]
    if rest:
        lines.append("// endpoint ที่เหลือของเอกสารนี้ — TODO: แทน placeholder ด้วย interface เต็มรูปแบบเดียวกับข้างบน")
        for n in rest:
            placeholders: list[str] = []
            if n["body_keys"]:
                placeholders.append(n["params_type"].replace("T.", "") if n["method"] == "GET"
                                    else f"{_pascal(n['verb'])}{n['base']}Request")
            if n["shape"] in {"page", "items"}:
                placeholders.append(f"{n['base']}Item")
                if n["shape"] == "items":
                    placeholders.append(f"{n['base']}Response")
            elif n["shape"] != "blob":
                placeholders.append(n["object_response"])
            for name in placeholders:
                if name in seen:
                    continue
                seen.add(name)
                lines.append(f"export type {name} = Record<string, unknown>;")
    lines.append("// TODO: ใส่ nullable / required ให้ตรงกับ contract ฉบับล่าสุดของ BE")
    text = "\n".join(lines)
    envelope = "import type { PageResponse } from '@/types/sgi/common';" if "PageResponse<" in text else ""
    text = text.replace("__ENVELOPE_IMPORT__\n\n", envelope + "\n\n" if envelope else "")
    blocks = [h(3, f"{num} types — `src/types/sgi/{domain}.ts`")]
    note = _shared_note(domain, f"src/types/sgi/{domain}.ts")
    if note:
        blocks.append(p(note))
    blocks.append(code(text, "ts"))
    return blocks


# ---------------------------------------------------------------------------
# 5) react-query keys + hooks
# ---------------------------------------------------------------------------


def _query_blocks(nx: dict[str, Any], num: str) -> list[dict[str, Any]]:
    names, prof = nx["names"], nx["prof"]
    if not names:
        return []
    domain = prof["domain"]
    gets = [n for n in names.values() if n["method"] == "GET" and n["shape"] != "blob"][:3]
    downloads = [n for n in names.values() if n["shape"] == "blob"][:1]
    mutations = [n for n in names.values() if n["method"] != "GET"][:2]
    # import ตาม hook ที่ใช้จริงในไฟล์นี้เท่านั้น (portal เปิด no-unused-vars / noUnusedLocals)
    rq_imports = (["useMutation"] if (downloads or mutations) else []) + (["useQuery"] if gets else [])
    if mutations:
        rq_imports.append("useQueryClient")
    rq_imports = sorted(set(rq_imports))
    lines = [
        f"// src/hooks/sgi/{domain}.query.ts",
        "import { " + ", ".join(rq_imports) + " } from '@tanstack/react-query';",
    ]
    if downloads:
        lines.append("import { saveAs } from 'file-saver';")
    lines += [
        f"import * as api from '@/services/sgi/{domain}.service';",
        f"import type * as T from '@/types/sgi/{domain}';",
        "",
        f"export const {domain}Keys = {{",
        f"  all: ['sgi', '{domain}'] as const,",
    ]
    for n in gets:
        args = ", ".join(list(n["path_params"]) + (["params"] if n["body_keys"] else []))
        sig = ", ".join([f"{x}: string" for x in n["path_params"]] + ([f"params?: {n['params_type']} | null"] if n["body_keys"] else []))
        tail = (", " + args) if args else ""
        lines.append(f"  {n['key']}: ({sig}) => [...{domain}Keys.all, '{n['key']}'{tail}] as const,")
    lines.append("};")
    lines.append("")

    for n in gets:
        args = list(n["path_params"]) + (["params"] if n["body_keys"] else [])
        sig = ", ".join([f"{x}: string" for x in n["path_params"]] + ([f"params?: {n['params_type']} | null"] if n["body_keys"] else []))
        guards = [f"!!{x}" for x in n["path_params"]] + (["!!params"] if n["body_keys"] else [])
        lines.append(f"export function {n['query_hook']}({sig}) {{")
        lines.append("  return useQuery({")
        lines.append(f"    queryKey: {domain}Keys.{n['key']}({', '.join(args)}),")
        lines.append(f"    queryFn: () => api.{n['fn']}({', '.join(args[:-1] + ['params!'] if n['body_keys'] else args)}),")
        if guards:
            lines.append(f"    enabled: {' && '.join(guards)}, // ยังไม่ยิงจนกว่าจะมีพารามิเตอร์ครบ")
        lines.append("    staleTime: 30_000, // TODO: ปรับตามความถี่ของข้อมูลหน้านี้")
        lines.append("  });")
        lines.append("}")
        lines.append("")

    for n in downloads:
        # params_type ของเส้น /export ถูก align กับ endpoint ค้นหาแม่แล้วใน _api_names()
        lines.append(f"export function {n['download_hook']}() {{")
        lines.append("  return useMutation({")
        if n.get("params_source"):
            lines.append(f"    // filter ชุดเดียวกับการค้นหาล่าสุด -> input type = params ของ {n['params_source']}")
        lines.append(f"    mutationFn: (params: {n['params_type']}) => api.{n['fn']}(params),")
        lines.append("    onSuccess: (blob) => saveAs(blob, 'export.xlsx'), // TODO: อ่านชื่อไฟล์จาก content-disposition")
        lines.append("  });")
        lines.append("}")
        lines.append("")

    for n in mutations:
        sig = ", ".join(f"{x}: string" for x in n["path_params"])
        body_arg = "body" if n["body_keys"] else ""
        call_args = list(n["path_params"]) + ([body_arg] if body_arg else [])
        lines.append(f"export function {n['mutation_hook']}({sig}) {{")
        lines.append("  const qc = useQueryClient();")
        lines.append("  return useMutation({")
        lines.append(f"    mutationFn: ({(body_arg + ': ' + n['request_type']) if body_arg else ''}) => api.{n['fn']}({', '.join(call_args)}),")
        lines.append("    onSuccess: () => {")
        lines.append(f"      qc.invalidateQueries({{ queryKey: {domain}Keys.all }}); // reload list/detail/timeline")
        lines.append("    },")
        lines.append("    // TODO: onError -> แสดง apiErrorMessage(error) ผ่าน Toast กลาง")
        lines.append("  });")
        lines.append("}")
        lines.append("")
    if len(names) > len(gets) + len(mutations) + len(downloads):
        rest_names = [
            f"{n['method']} {n['path']}" for n in names.values()
            if n not in gets and n not in mutations and n not in downloads
        ]
        lines.append("// TODO: ยังขาดอีก %d เส้น เขียน hook ด้วยรูปแบบเดียวกัน: %s"
                     % (len(rest_names), ", ".join(rest_names)))
    blocks = [h(3, f"{num} react-query keys + hooks — `src/hooks/sgi/{domain}.query.ts`")]
    note = _shared_note(domain, f"src/hooks/sgi/{domain}.query.ts")
    if note:
        blocks.append(p(note))
    blocks.append(code("\n".join(lines), "ts"))
    return blocks


# ---------------------------------------------------------------------------
# 6) ฟอร์ม + validation
# ---------------------------------------------------------------------------


def _action_form(nx: dict[str, Any], comp: str) -> str:
    """ฟอร์มของหน้า Document Detail = ฟอร์ม "พิจารณา" (result + comment) ของ
    `POST /sgi/document/{docNo}/actions` เท่านั้น — ไม่ใช่ฟอร์มค้นหา และไม่ใช่ field ฝั่ง response
    """
    prof, apis = nx["prof"], nx["apis"]
    role_code = prof.get("role_code", "")
    options = _action_option_dicts(apis)
    editable = _editable_sections(apis)
    opt_rows = "\n".join(
        "//   - {label} (value='{value}', requireComment={rc})".format(
            label=o.get("label", ""), value=o.get("value", o.get("code", "")),
            rc=str(bool(o.get("requireComment"))).lower(),
        )
        for o in options
    ) or "//   - (contract ของ role นี้ไม่ระบุ actionOptions — render จาก doc.actionOptions ตอน runtime)"
    require_values = [str(o.get("value", o.get("code", ""))) for o in options if o.get("requireComment")]
    require_literal = ", ".join(f"'{v}'" for v in require_values if v) or "/* TODO: ค่าที่บังคับ comment */"
    return f"""'use client';
// {comp} — ฟอร์ม "ผลการพิจารณา" ของ workflow section {role_code}
// payload ที่ส่งจริงมีแค่ 2 field ตาม CreateDocumentsActionsRequest: {{ result, comment }}
// option ที่ role นี้เห็นตาม contract (render จาก doc.actionOptions ห้าม hardcode ใน JSX):
{opt_rows}
// editableSections ของ role นี้ (ใช้เป็น constant สำหรับ assertion/test เท่านั้น ไม่ใช่เพื่อ hardcode การ render):
export const EDITABLE_SECTIONS_{role_code or 'ROLE'} = [{', '.join(f"'{s}'" for s in editable)}] as const;

import {{ Controller, useForm }} from 'react-hook-form';
import {{ yupResolver }} from '@hookform/resolvers/yup';
import * as yup from 'yup';
import {{ RadioButtonGroup }} from '@/components/Form';
import {{ InputTextarea }} from '@/components/Form/InputText/inputtextArea';
import type {{ DocumentActionRequest }} from '@/types/sgi/common';

interface ActionOption {{ value: string; label: string; requireComment?: boolean }}

// ค่าที่ "บังคับกรอกความคิดเห็น" มาจาก contract ของ role นี้
const REQUIRE_COMMENT: string[] = [{require_literal}];

// ⚠️ ข้อความ validation ด้านล่างเป็น verbatim จาก SRS v3.1 — ห้าม paraphrase ห้ามย่อ
//    (SRS "รายการหน้าจอ" §10/§13 · ตรงกับที่ prototype k2-document.html ใช้)
const schema = yup.object({{
  result: yup.string().required('ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ'),
  // SRS บังคับให้ความคิดเห็นเป็น required เมื่อเลือกไม่ชดเชย แต่ไม่ได้ระบุข้อความ — ข้อความนี้เรากำหนดเอง
  comment: yup.string().when('result', {{
    is: (v: string) => REQUIRE_COMMENT.includes(v),
    then: (s) => s.required('กรุณาระบุความคิดเห็น'),
    otherwise: (s) => s.optional(),
  }}),
}});

export default function {comp}({{ options, onSubmit, onCancel, submitting }}: {{
  options: ActionOption[];          // = doc.actionOptions จาก API
  onSubmit: (payload: DocumentActionRequest) => void;
  onCancel?: () => void;
  submitting?: boolean;
}}) {{
  const {{ control, handleSubmit, watch, formState: {{ errors }} }} = useForm<DocumentActionRequest>({{
    resolver: yupResolver(schema) as never,
    defaultValues: {{ result: '', comment: '' }},
    mode: 'onSubmit',
  }});
  const mustComment = REQUIRE_COMMENT.includes(watch('result'));

  return (
    <form onSubmit={{handleSubmit(onSubmit)}} className="flex flex-col gap-3">
      <Controller
        name="result"
        control={{control}}
        render={{({{ field }}) => (
          <RadioButtonGroup
            options={{options.map((o) => ({{ label: o.label, value: o.value }}))}}
            value={{field.value}}
            onChange={{(e) => field.onChange(e.value)}}
            flex="col"
            gap="8px"
          />
        )}}
      />
      {{errors.result && <span className="text-red-600">{{errors.result.message}}</span>}}
      <Controller
        name="comment"
        control={{control}}
        render={{({{ field }}) => (
          <InputTextarea {{...field}} rows={{4}} placeholder={{mustComment ? 'ระบุความคิดเห็น (บังคับ)' : 'ความคิดเห็น'}} />
        )}}
      />
      {{errors.comment && <span className="text-red-600">{{errors.comment.message}}</span>}}
      <div className="flex justify-end gap-2">
        <button type="submit" {BTN_PRIMARY} disabled={{submitting}}>
          ยืนยัน
        </button>
        <button type="button" {BTN_SECONDARY} onClick={{onCancel}}>
          ยกเลิก
        </button>
      </div>
    </form>
  );
}}"""


def _search_form(nx: dict[str, Any], comp: str, fields: list[tuple[str, str, str, str]]) -> str:
    topic = nx["topic"]
    schema_lines = "\n".join(_yup_rule(name, fmt, validation, behavior) for name, fmt, validation, behavior in fields)
    type_lines = "\n".join(f"  {name}: {_ts_form_type(fmt)};" for name, fmt, _v, _b in fields)
    inputs = "\n".join(
        f'      <FormInputControl name="{name}" control={{control}} input={{InputText}} label="{name}" />'
        for name, _f, _v, _b in fields[:4]
    )
    rest = [f[0] for f in fields[4:]]
    rest_note = (
        "      {/* TODO: ฟิลด์ที่เหลือ (" + ", ".join(rest)
        + ") ใช้ Dropdown / DatePicker / MultiSelect จาก @/components/Form ผ่าน FormInputControl แบบเดียวกัน */}"
        if rest else
        "      {/* TODO: ปรับ input ให้ตรงชนิดข้อมูล (Dropdown / DatePicker / MultiSelect) ตามตารางฟิลด์ */}"
    )
    return f"""'use client';
// {comp} — ฟอร์มของ "{getattr(topic, 'title', '')}" (ฟิลด์/validation ตามตารางฟิลด์ในเอกสารนี้)
// ผูก react-hook-form ด้วย FormInputControl (components/Form/Layout/form-input-control.tsx)
// — InputText เองไม่รับ prop name/control/label/error (extends PrimeInputTextProps เท่านั้น)

import {{ useForm }} from 'react-hook-form';
import {{ yupResolver }} from '@hookform/resolvers/yup';
import * as yup from 'yup';
import {{ FormInputControl, InputText }} from '@/components/Form';

export interface {comp}Value {{
{type_lines}
}}

// TODO: แทนข้อความ validation ด้วยข้อความ verbatim จาก SRS ก่อน UAT
const schema = yup.object({{
{schema_lines}
}});

export default function {comp}({{ defaultValues, onSubmit }}: {{
  defaultValues?: Partial<{comp}Value>;
  onSubmit: (values: {comp}Value) => void;
}}) {{
  const {{ control, handleSubmit, reset }} = useForm<{comp}Value>({{
    resolver: yupResolver(schema) as never,
    defaultValues: defaultValues as {comp}Value,
    mode: 'onSubmit',
  }});

  return (
    <form onSubmit={{handleSubmit(onSubmit)}} className="grid grid-cols-1 gap-3 md:grid-cols-3">
{inputs}
{rest_note}
      <div className="col-span-full flex justify-end gap-2">
        <button type="submit" {BTN_PRIMARY}>
          ค้นหาข้อมูล
        </button>
        <button type="button" {BTN_SECONDARY} onClick={{() => reset()}}>
          เคลียร์ค่าเริ่มใหม่
        </button>
      </div>
    </form>
  );
}}"""


def _form_blocks(nx: dict[str, Any], num: str) -> list[dict[str, Any]]:
    topic, prof, apis = nx["topic"], nx["prof"], nx["apis"]
    if prof["kind"] in NO_FORM_KINDS:
        return []
    if prof["kind"] in {"role", "detail"}:
        comp = f"ActionForm{prof.get('role_code', '')}" if prof["kind"] == "role" else "ActionPanel"
        folder = "document-detail"
        return [
            h(3, f"{num} ฟอร์มพิจารณา + validation — `src/components/sgi/{folder}/{comp}.tsx`"),
            p("หน้านี้**ไม่มีการค้นหา** — ฟอร์มเดียวของหน้าคือฟอร์มผลการพิจารณาที่ยิง "
              "`POST /api/v1/sgi/document/{docNo}/actions` โดยส่งได้แค่ `result` + `comment`"),
            code(_action_form(nx, comp), "tsx"),
        ]
    fields = _form_fields(topic, prof, apis)
    if not fields:
        return []
    comp = _pascal(prof["key"]) + "Form"
    folder = prof["key"].lower()
    return [h(3, f"{num} ฟอร์ม + validation — `src/components/sgi/{folder}/{comp}.tsx`"),
            code(_search_form(nx, comp, fields), "tsx")]


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def fe_skeleton_blocks(topic: Any, ctx: Any = None) -> list[dict[str, Any]]:
    """สร้าง block ส่วน "Skeleton Code" ของเอกสาร LLDD ฝั่ง FE

    ``ctx`` (optional dict) รองรับคีย์:
      * ``section_prefix`` — เลขหัวข้อ เช่น ``"6"`` -> หัวข้อย่อยจะเป็น 6.1, 6.2, ...
      * ``max_apis``       — จำนวน endpoint สูงสุดที่ generate (default 5)
      * ``heading_level``  — ระดับหัวข้อหลัก (default 2)

    คืน ``[]`` เมื่อ topic ไม่ใช่ track FE
    """
    ctx = ctx if isinstance(ctx, dict) else {}
    if str(getattr(topic, "track", "FE")).upper() != "FE":
        return []

    prof = _profile(topic)
    try:
        max_apis = int(ctx.get("max_apis", 5) or 5)
    except (TypeError, ValueError):
        max_apis = 5
    apis = _usable_apis(topic, max_apis)
    names = _api_names(apis)
    nx = {"topic": topic, "prof": prof, "apis": apis, "names": names}

    prefix = str(ctx.get("section_prefix") or "").strip()
    try:
        level = int(ctx.get("heading_level", 2) or 2)
    except (TypeError, ValueError):
        level = 2

    counter = {"n": 0}

    def num() -> str:
        counter["n"] += 1
        return f"{prefix}.{counter['n']}" if prefix else f"({counter['n']})"

    blocks: list[dict[str, Any]] = [
        h(level, f"{prefix + ' ' if prefix else ''}Skeleton Code (โครงโค้ดตั้งต้นของหน้าจอนี้)"),
        p(
            "โค้ดชุดนี้อิง convention ของ portal เดิม `srm-sps-spsap-web-frontend` (build target `sbpm`): "
            "Next.js App Router + `'use client'`, PrimeReact ที่ห่อไว้แล้วใน `@/components/Form` และ `@/components/Table`, "
            "react-hook-form + yup, Zustand `permissionStore`, axios instance กลาง `@/lib/apiClient` และ react-query 5 — "
            "**โปรเจกต์ไม่มี chart library** จึงไม่มีโค้ดกราฟในเอกสารนี้ คัดลอกไปตั้งต้นได้ทันที แล้วเติมจุดที่กำกับ `TODO:`"
        ),
    ]
    cut = _cut_apis(topic)
    if cut:
        blocks.append(p(
            "เส้นที่อยู่ในตาราง API ของเอกสารนี้แต่ **ถูกตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06 — "
            "RBAC/ผู้ปฏิบัติงานใช้ auth-backend ของระบบ SBP เดิม) จึงไม่มี skeleton ให้:"
        ))
        blocks.append(table(["Endpoint", "จุดประสงค์เดิม", "ใช้ของระบบเดิมแทน"], cut))
    blocks += _file_plan_blocks(nx, num())
    blocks += _page_blocks(nx, num())
    blocks += _service_blocks(nx, num())
    blocks += _types_blocks(nx, num())
    blocks += _query_blocks(nx, num())
    blocks += _form_blocks(nx, num())
    blocks.append(
        bullets([
            "ทุกหน้าเช็คสิทธิ์ด้วย `permissionStore.hasPermission(url, 'canView'|'canManage'|'canExport'|'canOther')` แล้ว render `<AccessDenied />` เมื่อไม่มีสิทธิ์",
            "เมนู/สิทธิ์มาจาก `GET /menus` และ `GET /groups/current-user/permissions` — ห้าม hardcode role หรือรายการเมนูใน FE",
            "session อยู่ใน httpOnly cookie ของ BFF (`withCredentials: true`) — FE ไม่เก็บและไม่แนบ token เอง",
            "payload และการแสดงผลใช้วันที่ ค.ศ. เสมอ ผ่าน formatter กลางจุดเดียว — ไม่แปลงเป็น พ.ศ. (มติ 2026-08-06)",
            "ข้อความ error แสดงจาก `error.message` ของ BE ตรง ๆ (ห้าม paraphrase) — fallback ใช้เฉพาะกรณี network error",
        ])
    )
    return blocks
