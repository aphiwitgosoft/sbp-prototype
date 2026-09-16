# บัญชี credential ที่พบใน legacy snapshot

> **สร้างจาก** `python3 tools/scan_secrets.py batchjob/fcsJar` · **ตรวจเมื่อ 2026-09-12**
>
> 🔴 **เอกสารนี้ไม่คัดลอกค่าจริงของ credential ใด ๆ** — ระบุแค่ **ไฟล์ · บรรทัด · ชนิด**
> เปิดไฟล์ดูเองเมื่อต้องใช้ · **ห้ามคัดลอกค่าลงเอกสาร ticket หรือแชท**
>
> ⚠️ **การลบข้อความออกจากไฟล์ไม่ได้ทำให้ credential ปลอดภัยขึ้น** — ต้อง **rotate/revoke ที่ระบบต้นทาง**

---

## สรุปจำนวน

| ชนิด | จำนวนจุด |
|---|---|
| username ของฐานข้อมูล | 50 |
| password ใน .properties/.xml | 26 |
| JDBC URL ที่มี host จริง | 3 |
| credential รูปแบบ user:pass | 3 |
| AWS access key | 1 |
| **รวม** | **83 จุด ใน 22 ไฟล์** |

---

## จุดที่ต้องจัดการก่อน (ระบบในขอบเขต SGI)

| ไฟล์ | ระบบที่เกี่ยวข้อง | ต้องทำอะไร |
|---|---|---|
| `batchjob/fcsJar/jdbc.properties` | **ALLMAP (SQL Server `GSMALLMAP`)** · Oracle `FCS_FRN` | 🔴 **rotate ทั้ง prod และ QA** — ไฟล์สลับ environment ด้วยการ comment จึงมีค่าของหลาย env ปนกัน |
| `batchjob/fcsJar/src/th/co/gosoft/fgi/Constant/FgiConstant.java` | **K2 / BPM** (`K2USER` = domain user + รหัสผ่าน) | 🔴 **rotate** — ใช้กับ HTTP Basic Auth ของ Job 8b และ Job 12 |
| `batchjob/fcsJar/config.xml` | SFTP ของ EAI (STA · BPM · IAS) | 🔴 **rotate** |
| `batchjob/fcsJar/ApplicationResources.properties` | ⚠️ **มี AWS access key** | 🔴 **revoke ทันที** — key ที่หลุดใช้ได้จนกว่าจะถูกเพิกถอน |
| `batchjob/fcsJar/src/th/co/gosoft/fml/constant/CipherKey.java` | คีย์เข้ารหัสของระบบเดิม | 🔴 ประเมินว่ายังใช้กับข้อมูลจริงอยู่ไหม |

> 📌 **ไฟล์ที่เหลืออยู่นอกขอบเขต SGI** (`ad/` · `fmp/` · `fms/` · `fts/` — ระบบงานอื่นใน `fcsJar`)
> ยังต้องแจ้งเจ้าของระบบนั้น แต่ไม่ใช่งานของทีมประกันรายได้

---

## รายการเต็ม (ไฟล์ · จำนวนจุด · ชนิด)

| ไฟล์ | จุด | ชนิดที่พบ |
|---|---|---|
| `batchjob/fcsJar/ApplicationResources.properties` | 3 | username ของฐานข้อมูล ×2 · AWS access key ×1 |
| `batchjob/fcsJar/jdbc.properties` | 17 | username ของฐานข้อมูล ×7 · password ใน .properties/.xml ×7 · JDBC URL ที่มี host จริง ×3 |
| `batchjob/fcsJar/src/th/co/gosoft/ad/controller/SpsExportAdMgrToBudController.java` | 2 | username ของฐานข้อมูล ×1 · password ใน .properties/.xml ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/ad/jdbc/SendADJdbc.java` | 12 | username ของฐานข้อมูล ×10 · password ใน .properties/.xml ×2 |
| `batchjob/fcsJar/src/th/co/gosoft/ad/jdbc/SendLdapJdbc.java` | 1 | password ใน .properties/.xml ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/ad/main/QueryAD.java` | 5 | username ของฐานข้อมูล ×3 · password ใน .properties/.xml ×2 |
| `batchjob/fcsJar/src/th/co/gosoft/fcm/utils/Email.java` | 4 | username ของฐานข้อมูล ×2 · password ใน .properties/.xml ×2 |
| `batchjob/fcsJar/src/th/co/gosoft/fcs/controller/UpdateUserPositionLevelFromADController.java` | 1 | username ของฐานข้อมูล ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fcs/model/JdbcPropertiesBean.java` | 2 | username ของฐานข้อมูล ×1 · password ใน .properties/.xml ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fcs/model/table/BusinessUser.java` | 2 | username ของฐานข้อมูล ×1 · password ใน .properties/.xml ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fcs/utils/FtpUtils.java` | 2 | password ใน .properties/.xml ×2 |
| `batchjob/fcsJar/src/th/co/gosoft/fcs_fmp/model/table/BusinessUser.java` | 2 | username ของฐานข้อมูล ×1 · password ใน .properties/.xml ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fcs_fmp/model/table/MasSbpAd.java` | 1 | username ของฐานข้อมูล ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fes/utils/Email.java` | 4 | username ของฐานข้อมูล ×2 · password ใน .properties/.xml ×2 |
| `batchjob/fcsJar/src/th/co/gosoft/fgi/Constant/FgiConstant.java` | 1 | credential รูปแบบ user:pass ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fmp/dao/FmpJdbc.java` | 10 | username ของฐานข้อมูล ×10 |
| `batchjob/fcsJar/src/th/co/gosoft/fmp/main/SendMailReportEmployeeTrain.java` | 1 | username ของฐานข้อมูล ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fmp/model/FmpEmployeeTrain.java` | 1 | username ของฐานข้อมูล ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fms/dao/jdbc/OnlineAppReportJdbc.java` | 5 | username ของฐานข้อมูล ×3 · credential รูปแบบ user:pass ×2 |
| `batchjob/fcsJar/src/th/co/gosoft/fms/services/CMService.java` | 3 | password ใน .properties/.xml ×2 · username ของฐานข้อมูล ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fts/main/ImportTrain.java` | 2 | username ของฐานข้อมูล ×1 · password ใน .properties/.xml ×1 |
| `batchjob/fcsJar/src/th/co/gosoft/fts/model/JdbcPropertiesBean.java` | 2 | username ของฐานข้อมูล ×1 · password ใน .properties/.xml ×1 |

---

## ขั้นตอนที่ต้องทำ (ยังไม่ได้ทำ)

1. [ ] ระบุว่า credential แต่ละชุดเป็น **production / UAT / STQA** และใครเป็นเจ้าของระบบ
2. [ ] **rotate/revoke** ที่ระบบต้นทาง — ไม่ใช่แค่ลบข้อความในไฟล์
3. [ ] ย้ายค่า runtime ของระบบใหม่ไป **Secret Manager/Vault** ตามมาตรฐานองค์กร
4. [ ] สร้าง **sanitized snapshot** ของ `fcsJar` สำหรับใช้เป็นหลักฐานอ้างอิง
5. [ ] เพิ่ม `python3 tools/scan_secrets.py` เข้า **CI/pre-commit** ก่อนนำ `batchjob/` เข้า repo หลัก

> 🔴 **ข้อ 5 สำคัญเป็นพิเศษ** — ตอนนี้ `batchjob/` ยัง **untracked ทั้งโฟลเดอร์**
> ถ้า commit เข้าไปโดยไม่ตรวจก่อน credential ทั้งหมดจะเข้าไปอยู่ใน git history **ซึ่งลบยากกว่ามาก**

---

## อ่านต่อ

| เรื่อง | ที่ไหน |
|---|---|
| Checklist เต็ม | [CHECKLIST-JOB-02-JOB-12-REMEDIATION.md](CHECKLIST-JOB-02-JOB-12-REMEDIATION.md) ข้อ **P0-SEC-01** |
| มติที่บันทึกไว้ | `DECISIONS-รอตัดสินใจ.md` ข้อ **4.6** |
| ตัวสแกน | `tools/scan_secrets.py` |
