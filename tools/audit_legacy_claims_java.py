#!/usr/bin/env python3
"""ตรวจข้ออ้างในเอกสาร (LLDD + batchjob) ที่ชี้ไปโค้ด Java เดิมใน batchjob/fcsJar

    python3 tools/audit_legacy_claims_java.py

ตรวจว่า: ไฟล์ .java ที่อ้างมีจริง · เลขบรรทัดไม่เกินความยาวไฟล์ · คลาสที่อ้างมีอยู่
ไม่ต้องต่อฐานข้อมูล รันได้เสมอ"""
import re, glob, os, io
ROOT="/Users/bank_mac/gosoft/java/SBP/sbp-prototype"
SRC=os.path.join(ROOT,"batchjob/fcsJar/src")

java = {}
for p in glob.glob(SRC+"/**/*.java", recursive=True):
    java.setdefault(os.path.basename(p), []).append(p)

docs = sorted(glob.glob(ROOT+"/LLDD/md/**/*.md", recursive=True)) + sorted(glob.glob(ROOT+"/batchjob/*.md"))
REF = re.compile(r"([A-Za-z][A-Za-z0-9_]*\.java):(\d+)(?:-(\d+))?")
bad_file, bad_line, ok = [], [], 0
seen=set()
for d in docs:
    txt = io.open(d, encoding="utf-8").read()
    for m in REF.finditer(txt):
        name, a, b = m.group(1), int(m.group(2)), m.group(3)
        key=(os.path.relpath(d,ROOT), name, a, b)
        if key in seen: continue
        seen.add(key)
        paths = java.get(name)
        if not paths:
            bad_file.append(f"{os.path.relpath(d,ROOT)} → {name} (ไม่มีไฟล์นี้ใน fcsJar/src)")
            continue
        hi = int(b) if b else a
        # ชื่อไฟล์ซ้ำข้าม package ได้ — ผ่านถ้ามีไฟล์ใดไฟล์หนึ่งยาวพอ
        sizes = [sum(1 for _ in io.open(p, encoding="utf-8", errors="ignore")) for p in paths]
        if hi > max(sizes):
            bad_line.append(f"{os.path.relpath(d,ROOT)} → {name}:{a}{'-'+b if b else ''} "
                            f"แต่ไฟล์ยาวสุดมีแค่ {max(sizes)} บรรทัด")
        else:
            ok += 1

print(f"=== อ้างอิง Java file:line — ตรวจ {ok+len(bad_file)+len(bad_line)} จุด ===")
print(f"  ผ่าน {ok} · ไฟล์ไม่มี {len(bad_file)} · บรรทัดเกินไฟล์ {len(bad_line)}")
for x in bad_file: print("  ❌", x)
for x in bad_line: print("  ❌", x)

# คลาสที่อ้างถึงโดยไม่มีเลขบรรทัด
CLS = re.compile(r"\b([A-Z][A-Za-z0-9_]+)\.java\b")
missing=set()
for d in docs:
    for m in CLS.finditer(io.open(d, encoding="utf-8").read()):
        if m.group(1)+".java" not in java: missing.add((os.path.relpath(d,ROOT), m.group(1)))
print(f"\n=== คลาส .java ที่เอกสารอ้างแต่ไม่มีใน fcsJar/src: {len(missing)} ===")
for d,c in sorted(missing)[:20]: print(f"  ❌ {d} → {c}.java")
