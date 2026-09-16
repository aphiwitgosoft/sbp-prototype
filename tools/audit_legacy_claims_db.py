#!/usr/bin/env python3
"""ตรวจตัวเลขที่เอกสารอ้างว่ามาจากฐาน Oracle เดิม ว่ายังตรงกับของจริงไหม

    ORA_USER=... ORA_PASSWORD=... ORA_DSN=host:1521/service \\
      python3 tools/audit_legacy_claims_db.py

⚠️ SELECT ล้วน · credential อ่านจาก env เท่านั้น ห้ามใส่ลงไฟล์
รันซ้ำได้เมื่อสงสัยว่าตัวเลขในเอกสารตกยุค (ทุกข้ออ้างที่ปิด DECISIONS ไปแล้วอยู่ในนี้)"""
import os, oracledb
c = oracledb.connect(user=os.environ['ORA_USER'], password=os.environ['ORA_PASSWORD'],
                     dsn=os.environ['ORA_DSN'], tcp_connect_timeout=20)
FIS="FGI_IMPACT_STORE_BK_20250515"; OP="FGI_IMPACT_STORE_ON_PROCESS_BK_20250515"
SAL="FGI_IMPACT_STORE_SALES_BK_20250515"; CP="FGI_IMPACT_COMPETITOR_BK_20250515"
CHECKS=[
 ("Job2 · ปีในข้อมูลประวัติ 2016-2025",     f"SELECT MIN(year)||'-'||MAX(year) FROM {FIS}", "2016-2025"),
 ("Job2 · FGI_IMPACT_STORE_BK รวม 26,264",  f"SELECT COUNT(*) FROM {FIS}", 26264),
 ("Job2 · FLAG_VERIFY N=14,424",            f"SELECT COUNT(*) FROM {FIS} WHERE flag_verify='N'", 14424),
 ("Job2 · FLAG_VERIFY Y=8,556",             f"SELECT COUNT(*) FROM {FIS} WHERE flag_verify='Y'", 8556),
 ("Job2 · FLAG_VERIFY W=3,064",             f"SELECT COUNT(*) FROM {FIS} WHERE flag_verify='W'", 3064),
 ("Job2 · CREATE_BY ALM=23,126",            f"SELECT COUNT(*) FROM {FIS} WHERE create_by='ALM'", 23126),
 ("Job2 · UPDATE_BY ไม่ NULL = 0",          f"SELECT COUNT(*) FROM {FIS} WHERE update_by IS NOT NULL", 0),
 ("Job2 · หน่วย 'กิโลเมตร' = 23,127",       f"SELECT COUNT(*) FROM {FIS} WHERE distance_unit='กิโลเมตร'", 23127),
 ("Job2 · W ที่ไม่มีสัญญา = 2,684",         f"SELECT COUNT(*) FROM {FIS} WHERE flag_verify='W' AND sbp_start_date_i IS NULL", 2684),
 ("Job2 · W ที่เป็น FPT1 = 382",            f"SELECT COUNT(*) FROM {FIS} WHERE flag_verify='W' AND branchtype_i='FPT1'", 382),
 ("Job2 · รหัสร้านยาวเกิน 5 = 5 แถว",       f"SELECT COUNT(*) FROM {FIS} WHERE LENGTH(storecode_i)>5", 5),
 ("2.38 · แถวแม่ 7,548",                    f"SELECT COUNT(*) FROM {OP}", 7548),
 ("2.38 · แถวแม่ที่ต้องมี 24,783",          f"SELECT COUNT(*) FROM (SELECT DISTINCT storecode_i,year,month FROM {FIS})", 24783),
 ("2.38 · FLAG_ACTION N=7,545",             f"SELECT COUNT(*) FROM {OP} WHERE flag_action='N'", 7545),
 ("2.37 · sales FLAG_VERIFY Y=6,029",       f"SELECT COUNT(*) FROM {SAL} WHERE flag_verify='Y'", 6029),
 ("2.37 · sales FLAG_VERIFY N=2,549",       f"SELECT COUNT(*) FROM {SAL} WHERE flag_verify='N'", 2549),
 ("2.37 · sales FLAG_VERIFY P=151",         f"SELECT COUNT(*) FROM {SAL} WHERE flag_verify='P'", 151),
 ("Job3 · คู่แข่งรวม 228,116",              f"SELECT COUNT(*) FROM {CP}", 228116),
 ("Job3 · COMPET_ID ว่าง 14,565",           f"SELECT COUNT(*) FROM {CP} WHERE COMPET_ID IS NULL OR TRIM(COMPET_ID)=''", 14565),
 ("Job3 · ซ้ำตามคีย์ 2,982 กลุ่ม",          f"SELECT COUNT(*) FROM (SELECT storecode_i,year,month,COMPET_ID FROM {CP} GROUP BY storecode_i,year,month,COMPET_ID HAVING COUNT(*)>1)", 2982),
 ("Job3 · 88 งวด insert วันเดียวจบ",        f"SELECT COUNT(*) FROM (SELECT year,month FROM {CP} GROUP BY year,month HAVING COUNT(DISTINCT TRUNC(create_date))>1)", 0),
 ("mas_store 5 หลักเสมอ (ORA)",             "SELECT COUNT(*) FROM mas_store WHERE LENGTH(branch_id)<>5", 0),
 ("fr_store ร้านหลายสัญญา 1,056",           "SELECT COUNT(*) FROM (SELECT store_id FROM fr_store WHERE NVL(status,'-')<>'D' AND store_id<>'00000' AND cancel_type IS NOT NULL GROUP BY store_id HAVING COUNT(*)>1)", 1056),
]
bad=0
with c, c.cursor() as cur:
    for name, sql, want in CHECKS:
        try:
            cur.execute(sql); got = cur.fetchone()[0]
        except Exception as e:
            print(f"  ⚠️ {name:<42} ERROR {str(e).splitlines()[0][:50]}"); bad+=1; continue
        ok = str(got) == str(want)
        print(f"  {'✅' if ok else '❌'} {name:<42} เอกสาร {want} · จริง {got}")
        if not ok: bad+=1
print(f"\n{'✅ ตัวเลขในเอกสารตรงกับฐานจริงทั้งหมด' if bad==0 else f'❌ ไม่ตรง {bad} จุด'}")
