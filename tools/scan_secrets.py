#!/usr/bin/env python3
"""ตรวจหา credential ที่ยังอยู่ใน working tree — แยกจาก tools/check_docs.py

ใช้ก่อน commit หรือก่อนแชร์ snapshot ของ batchjob/fcsJar
**ไม่พิมพ์ค่าจริงออกมา** — รายงานแค่ ไฟล์:บรรทัด และชนิดของ secret

    python3 tools/scan_secrets.py              # ตรวจทั้ง repo
    python3 tools/scan_secrets.py batchjob/    # ตรวจเฉพาะ path
"""
from __future__ import annotations
import os, re, sys

# ชนิด secret ที่ต้องจับ — เขียนเป็น (ชื่อ, regex, กลุ่มที่เป็นค่าจริง)
PATTERNS = [
    ("password ใน .properties/.xml", re.compile(r"(?i)\b(password|passwd|pwd)\s*[:=]\s*(\S+)"), 2),
    ("username ของฐานข้อมูล",         re.compile(r"(?i)\b(username|user)\s*[:=]\s*(\S{3,})"), 2),
    ("JDBC URL ที่มี host จริง",       re.compile(r"jdbc:[a-z]+://([^\s;]+)"), 1),
    ("HTTP Basic ใน source",          re.compile(r"(?i)\bbasic\s+[A-Za-z0-9+/=]{16,}"), 0),
    ("credential รูปแบบ user:pass",   re.compile(r"[A-Za-z0-9_\\\\]{3,}:[A-Za-z0-9!@#$%^&*]{6,}\""), 0),
    ("AWS access key",                re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"), 0),
    ("private key block",             re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), 0),
]
SKIP_DIRS = {".git", "node_modules", "LLDD/pdf", "LLDD/word", "output", "tmp", "__pycache__"}
SCAN_EXT = {".properties", ".xml", ".java", ".ts", ".js", ".json", ".yml", ".yaml",
            ".sh", ".env", ".conf", ".cfg", ".py", ".md"}
# ค่าที่เป็น placeholder ไม่ใช่ของจริง
PLACEHOLDER = re.compile(r"(?i)^(\$\{|<|\*+$|xxx|todo|changeme|your|example|secret/|arn:|env\.|process\.)")


def scan(root: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, ".")
        if any(rel == d or rel.startswith(d + os.sep) for d in SKIP_DIRS):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() not in SCAN_EXT:
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    for lno, line in enumerate(fh, 1):
                        if len(line) > 2000:
                            continue
                        for name, pat, grp in PATTERNS:
                            m = pat.search(line)
                            if not m:
                                continue
                            val = m.group(grp) if grp else m.group(0)
                            if PLACEHOLDER.match(val.strip().strip("'\"")):
                                continue
                            hits.append((os.path.relpath(path, "."), lno, name))
            except OSError:
                continue
    return hits


def main() -> int:
    roots = sys.argv[1:] or ["."]
    hits: list[tuple[str, int, str]] = []
    for r in roots:
        hits.extend(scan(r))
    if not hits:
        print("✅ ไม่พบ credential ที่ดูเป็นของจริง")
        return 0
    by_file: dict[str, list[tuple[int, str]]] = {}
    for path, lno, name in hits:
        by_file.setdefault(path, []).append((lno, name))
    print(f"🔴 พบ {len(hits)} จุดที่ต้องตรวจ ใน {len(by_file)} ไฟล์")
    print("   (ไม่แสดงค่าจริง — เปิดไฟล์ดูเองแล้ว rotate ที่ระบบต้นทาง)\n")
    for path in sorted(by_file):
        print(f"  {path}")
        for lno, name in sorted(by_file[path])[:12]:
            print(f"      บรรทัด {lno:<6} {name}")
        if len(by_file[path]) > 12:
            print(f"      … อีก {len(by_file[path]) - 12} จุด")
    print("\n⚠️ การลบข้อความออกจากไฟล์ไม่ได้ทำให้ credential ปลอดภัย — ต้อง rotate/revoke ที่ระบบต้นทาง")
    return 1


if __name__ == "__main__":
    sys.exit(main())
