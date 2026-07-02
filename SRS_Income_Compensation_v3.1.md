# Software Requirement Specification (SRS)

## ระบบประกันรายได้

**Version:** 3.1

---

# Document Information

| Item | Detail |
|------|--------|
| Document | Software Requirement Specification |
| System | ระบบประกันรายได้ |
| Version | 3.1 |
| Company | Gosoft (Thailand) Co., Ltd. |

---

# Revision History

| Version | Description |
|----------|-------------|
| 3.1 | Initial Version |

---

# Table of Contents

1. SRS Overview
2. Overall Description
    - Product Perspective
    - Product Functions
    - User Characteristics
    - Constraints
    - Assumptions
3. Functional Requirement
4. Non Functional Requirement
5. Appendix

---

# 1. SRS Overview

## Purpose

เอกสาร Software Requirement Specification (SRS)

ใช้สำหรับอธิบายความต้องการของระบบ **ประกันรายได้ (Income Compensation System)**

โดยอธิบายรายละเอียดของ

- Business Process
- Functional Requirement
- User Interface
- Business Rule
- Workflow
- Validation
- Report

เพื่อใช้เป็นเอกสารอ้างอิงสำหรับ

- Business
- Developer
- Tester
- Project Manager

---

# 2. Overall Description

## 2.1 Product Perspective

ระบบประกันรายได้ เป็นระบบสำหรับบริหารการชดเชยรายได้ของร้าน Franchise ที่ได้รับผลกระทบจากร้านเปิดใหม่

ระบบเชื่อมต่อกับระบบอื่น ดังนี้

- Store Chain Unit
- Finance & Account Unit
- Email Notification

---

## 2.2 Product Functions

ระบบประกอบด้วย Module ดังนี้

1. หน้ารอท่านดำเนินการ
2. เอกสารที่เกี่ยวข้องกับท่าน
3. ข้อมูลร้านถูกกระทบ
4. รายงาน
5. กำหนดผู้ปฏิบัติงาน
6. Master Data

---

## 2.3 User Characteristics

| Role | Description |
|------|-------------|
| Admin | ดูแลระบบ |
| HQ | ตรวจสอบข้อมูล |
| User Admin | จัดการผู้ใช้งาน |
| Report Admin | ดูรายงาน |
| Assign Job | แจกงาน |
| Report Admin Special | ดูเอกสารทั้งหมด |
| User Viewer | อ่านเอกสาร |

---

## 2.4 Constraints

- รับข้อมูลจาก Store Chain
- ใช้ฐานข้อมูล SQL Server
- Web Application
- ใช้งานผ่าน Browser

---

## 2.5 Assumptions

- มีการ Login
- มีสิทธิ์ก่อนใช้งาน
- มีข้อมูล Master พร้อม

---

# 3. Functional Requirement

## 3.1 สิทธิ์การเข้าถึง

### Purpose

กำหนดสิทธิ์ของผู้ใช้งานแต่ละ Role

### Actor

- Admin
- HQ
- User

### User Acceptance Criteria

- สามารถเห็นเมนูตามสิทธิ์
- ไม่สามารถเข้าถึงเมนูที่ไม่มีสิทธิ์

---

## 3.2 หน้ารอท่านดำเนินการ

### Purpose

แสดงเอกสารที่รอการดำเนินการ

### Search Condition

- เลขที่เอกสาร
- รหัสร้าน
- ชื่อร้าน
- ภาค
- สถานะ

### Result

| Column |
|----------|
| ครั้งที่ |
| เลขที่เอกสาร |
| รหัสร้านถูกกระทบ |
| ชื่อร้านถูกกระทบ |
| ภาค |
| จำนวนเงินชดเชย |
| สถานะ |
| รอดำเนินการ (วัน) |

---

## Business Rule

- เรียงตามวันที่สร้างล่าสุด
- เปิดเอกสารได้
- แสดงจำนวนวันที่ค้างดำเนินการ
- แสดงสถานะล่าสุด

---

## Validation

- หากยอดขายยังไม่ครบ 60 วัน
- ให้แสดงข้อความสีแดง

---

## User Acceptance Criteria

- สามารถค้นหาเอกสารได้
- เปิดเอกสารได้
- แสดงข้อมูลถูกต้อง

---

## 3.3 เอกสารที่เกี่ยวข้องกับท่าน

### Purpose

แสดงเอกสารทั้งหมดที่ผู้ใช้งานเคยเกี่ยวข้อง

### Search Condition

- เลขที่เอกสาร
- รหัสร้าน
- สถานะ
- วันที่สร้าง

### Result

| Column |
|----------|
| เลขที่เอกสาร |
| รหัสร้าน |
| ชื่อร้าน |
| ภาค |
| ประเภทร้าน |
| จำนวนเงินชดเชย |
| สถานะ |
| ผู้ดำเนินการ |

---

Business Rule

- เปิดดูย้อนหลังได้
- อ่านข้อมูลได้
- ไม่มีสิทธิ์แก้ไขเอกสารที่เสร็จแล้ว

---

# End of Part 1

# Part 2

# 3.4 Flow การดำเนินงาน (Workflow)

## ภาพรวม Workflow

```text
สร้างเอกสาร
      │
      ▼
ฝ่าย SBP DSA (06)
      │
      ├──────────────► เห็นควรไม่ชดเชย
      │                    │
      │                    ▼
      │               จบเอกสาร
      │
      ├──────────────► หยุดชดเชย
      │                    │
      │                    ▼
      │               จบเอกสาร
      │
      └──────────────► เจ้าหน้าที่ SBP DSA (08)
                            │
                            ▼
                    คำนวณเงินชดเชย
                            │
                            ▼
                  ฝ่ายส่งเสริมธุรกิจ (01)
                            │
                            ▼
                  GM ส่งเสริมธุรกิจ (02)
                            │
                ┌───────────┴───────────┐
                │                       │
        >100,000 บาท             <=100,000 บาท
                │                       │
                ▼                       ▼
       ผู้บริหารสำนัก (03)      ฝ่ายบัญชี (04)
                │                       │
                └───────────┬───────────┘
                            ▼
                  บัญชีปฏิบัติการภาค (05)
                            │
                            ▼
                         Complete
```

---

# 3.5 สถานะเอกสาร

| State | ชื่อสถานะ |
|--------|-----------|
| 01 | รอฝ่ายส่งเสริมธุรกิจ SBP |
| 02 | รอ GM ส่งเสริมธุรกิจ SBP |
| 03 | รอผู้บริหารสำนักบริหาร SBP |
| 04 | รอฝ่ายบัญชี SBP |
| 05 | รอบัญชีปฏิบัติการภาค |
| 06 | รอฝ่าย SBP DSA |
| 08 | รอเจ้าหน้าที่ SBP DSA |

---

# 3.6 Workflow รายละเอียดแต่ละขั้น

## State 06

### ฝ่าย SBP DSA

หน้าจอเป็นแบบ Read / Write

สามารถดำเนินการได้ดังนี้

- เห็นควรไม่ชดเชย
- หยุดชดเชยประกันรายได้
- ส่งต่อฝ่ายส่งเสริมธุรกิจ SBP
- ส่งต่อฝ่ายบัญชี SBP
- ส่งต่อเจ้าหน้าที่ SBP DSA

---

### Validation

ก่อนกดส่งดำเนินการ

ระบบต้องตรวจสอบว่า

- เลือกผลการพิจารณาแล้ว
- กรณี "เห็นควรไม่ชดเชย"
  ต้องกรอกความคิดเห็น
- กรณี "ฝ่ายบัญชี SBP"
  ต้องกรอกความคิดเห็น

หากไม่ครบ

แสดงข้อความ

```
ท่านยังไม่เลือกผลการพิจารณา
กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ
```

---

## State 08

### เจ้าหน้าที่ SBP DSA

เพิ่มเติมจาก State 06

สามารถเข้าหน้าคำนวณเงินชดเชยได้

ข้อมูลอื่นทั้งหมดเป็น

Read Only

---

สามารถดำเนินการ

- คำนวณเงินชดเชยเรียบร้อย
- ส่งกลับฝ่าย SBP DSA

---

# 3.7 การคำนวณเงินชดเชย

Finance & Account Unit

เป็นผู้คำนวณ

ข้อมูลนี้แสดงเฉพาะผู้มีสิทธิ์

---

# 3.8 State 01

## ฝ่ายส่งเสริมธุรกิจ

สามารถแก้ไข

- ร้านเปิดใหม่
- ร้านคู่แข่ง
- ปัจจัยอื่น ๆ
- ความคิดเห็น

ข้อมูลอื่น

Read Only

---

ผลการดำเนินการ

- เห็นควรชดเชย
- เห็นควรไม่ชดเชย
- ส่งกลับ SBP DSA

---

# 3.9 State 02

## GM ส่งเสริมธุรกิจ

สามารถดำเนินการ

### เห็นควรชดเชย

กรณี

จำนวนเงิน > 100,000

ส่งต่อ

ผู้บริหารสำนักบริหาร

---

จำนวนเงิน <= 100,000

ส่งต่อ

ฝ่ายบัญชี

---

### เห็นควรไม่ชดเชย

จำนวนเงิน >100,000

ส่งต่อ

ผู้บริหารสำนักบริหาร

---

จำนวนเงิน <=100,000

ส่งกลับ SBP DSA

---

สามารถส่งกลับ

ฝ่ายส่งเสริมธุรกิจ

ได้เช่นกัน

---

# 3.10 State 03

## ผู้บริหารสำนักบริหาร

สามารถเลือก

- เห็นควรชดเชย
- เห็นควรไม่ชดเชย
- ส่งกลับ GM

---

# 3.11 State 04

## ฝ่ายบัญชี

สามารถเลือก

- ส่งบัญชีปฏิบัติการภาค
- ส่งกลับ SBP DSA

---

# 3.12 State 05

## บัญชีปฏิบัติการภาค

สามารถเลือก

- บัญชีภาคอนุมัติ
- ส่งกลับฝ่ายบัญชี

เมื่ออนุมัติแล้ว

Document Status

```
Completed
```

---

# User Acceptance Criteria

- Workflow เป็นไปตามลำดับ
- สิทธิ์แต่ละ Role ถูกต้อง
- Validation ครบถ้วน
- สามารถ Save Draft ได้ทุกขั้น
- สามารถส่งงานต่อได้ตาม Workflow

# Part 3

# 3.13 หน้าเอกสารข้อมูลร้านถูกกระทบ (Document Detail)

เมื่อผู้ใช้งานเปิดเอกสาร ระบบจะแสดงข้อมูลตามสิทธิ์ของแต่ละ Role

ประกอบด้วย Panel ดังนี้

1. ข้อมูลเอกสาร
2. ร้านเปิดใหม่
3. ประวัติการชดเชย
4. ผลการพิจารณา
5. ร้านคู่แข่งเปิดกระทบ
6. ปัจจัยอื่น ๆ
7. เอกสารแนบทั้งหมด
8. พิจารณา

---

# 3.13.1 ข้อมูลเอกสาร

| No | Field | Description |
|----|--------|-------------|
| 1 | เลขที่เอกสาร | Running Document No. |
| 2 | วันที่สร้าง | DD/MM/YYYY |
| 3 | ผู้สร้าง | ชื่อผู้สร้างเอกสาร |
| 4 | สถานะ | Current Status |
| 5 | ครั้งที่ | Running Compensation |
| 6 | เดือน/ปีที่ชดเชย | Compensation Period |
| 7 | วันที่โอนเป็นร้าน SP | Transfer Date |
| 8 | Period Statement | รอบ Statement |
| 9 | ยอดเงินชดเชย | Compensation Amount |
| 10 | หมายเหตุ | Additional Remark |

ข้อมูลทั้งหมดในส่วนนี้เป็น Read Only

---

# 3.13.2 ร้านเปิดใหม่

แสดงข้อมูลร้านที่เปิดใหม่ซึ่งส่งผลกระทบต่อร้าน Franchise

| No | Field | Description |
|----|-------|-------------|
| 1 | รหัสร้านถูกกระทบ | Store Code |
| 2 | ชื่อร้านถูกกระทบ | Store Name |
| 3 | ภาค | Region |
| 4 | ประเภทร้าน | FR Type |
| 5 | เจ้าของร้าน | Owner |
| 6 | นิติบุคคล | Company |
| 7 | วันที่เปิดร้าน | DD/MM/YYYY |
| 8 | ระยะห่างตามจริง | Distance |
| 9 | % ชดเชย | Compensation Percentage |

---

## ประเภทร้าน (FR Type)

- FR Type A
- FR Type B
- FR Type C
- FR Type พนักงาน
- บริษัท
- FR Type PTT
- FR Type BGC
- FR Type C R

---

## Validation ของ % ชดเชย

ระบบกำหนดค่าเริ่มต้นของ % ชดเชยให้โดยอัตโนมัติ

ผู้ใช้งานสามารถแก้ไขได้

เมื่อกดคำนวณ

ระบบต้องตรวจสอบว่า

```
ผลรวม % ชดเชย = 100%
```

หากไม่เท่ากับ 100%

แสดงข้อความ

```
โปรดตรวจสอบ %ชดเชย ของท่าน
รวมกันแล้วไม่เท่ากับ 100%
```

ผู้ใช้สามารถแก้ไขได้ทีละรายการเท่านั้น :contentReference[oaicite:0]{index=0}

---

# 3.13.3 ประวัติการชดเชย

ใช้แสดงประวัติการได้รับเงินชดเชยย้อนหลัง

| Column |
|---------|
| ครั้ง |
| เดือน/ปี |
| จำนวนเงิน |
| วันที่โอน |
| สถานะ |
| ผู้ดำเนินการ |

ข้อมูลทั้งหมดเป็น Read Only

---

# 3.13.4 ผลการพิจารณา

แสดงประวัติการพิจารณาของทุก Role

| No | Field | Description |
|----|-------|-------------|
| 1 | ผู้พิจารณา | ชื่อ-นามสกุล ภาษาอังกฤษ |
| 2 | ตำแหน่ง | ภาษาไทย |
| 3 | ผลการพิจารณา | Result |
| 4 | รายละเอียดการพิจารณา | Comment |
| 5 | วัน/เวลา | DD/MM/YYYY HH:mm:ss |

ตัวอย่าง

```
ผู้พิจารณา

John Smith

ตำแหน่ง

ฝ่าย OPT

ผลการพิจารณา

เห็นควรชดเชย

ความคิดเห็น

ร้านเปิดใหม่อยู่ใกล้มาก

วันที่

15/12/2016 11:45:09
```

รายละเอียดการแสดงผลตรงตามข้อกำหนดของเอกสาร :contentReference[oaicite:1]{index=1}

---

# 3.13.5 ร้านคู่แข่งเปิดกระทบ

ใช้บันทึกร้านคู่แข่งที่ส่งผลกระทบ

| No | Field | Description |
|----|-------|-------------|
| 1 | ร้านคู่แข่ง | Dropdown |
| 2 | วันที่เปิด | DD/MM/YYYY |
| 3 | รายละเอียดเพิ่มเติม | Text |

---

## กรณีข้อมูลมาจาก All Map

ระบบแสดงข้อความ

```
ข้อมูลจากระบบ All Map
```

ผู้ใช้งาน

```
ไม่สามารถแก้ไขข้อมูลได้
```

หากผู้ใช้เป็นผู้กรอกข้อมูลเอง

จะไม่แสดงข้อความดังกล่าว :contentReference[oaicite:2]{index=2}

---

## หน้าจอ Edit

มีปุ่ม

- เพิ่ม
- แก้ไข
- ลบ
- บันทึก

---

### Validation

Field ที่ต้องกรอก

- ร้านคู่แข่งเปิดกระทบ

หากไม่กรอก

```
กรุณาเลือกร้านคู่แข่งที่ท่านต้องการ
```

:contentReference[oaicite:3]{index=3}

---

# 3.13.6 ปัจจัยอื่น ๆ

ใช้เก็บเหตุผลภายนอกที่มีผลต่อยอดขาย

| No | Field |
|----|-------|
| 1 | ปัจจัยภายนอก |
| 2 | วันที่เริ่มต้น |
| 3 | วันที่สิ้นสุด |
| 4 | รายละเอียดเพิ่มเติม |

---

ปัจจัยภายนอก

เลือกจาก

```
Dropdown List
```

วันที่

ใช้รูปแบบ

```
DD/MM/YYYY
```

---

### Validation

ต้องกรอก

- ปัจจัยภายนอก
- วันที่เริ่มต้น
- รายละเอียดเพิ่มเติม

ถ้าไม่กรอก

```
กรุณาเลือกปัจจัยอื่น ๆ ที่ท่านต้องการ
```

ระบบตรวจสอบว่า

```
วันที่สิ้นสุด

>=

วันที่เริ่มต้น
```

หากไม่ถูกต้อง

```
แสดง Pop-up แจ้งเตือน
```

ตาม Business Rule ในเอกสาร :contentReference[oaicite:4]{index=4} :contentReference[oaicite:5]{index=5}

---

# 3.13.7 เอกสารแนบทั้งหมด

แสดงรายการไฟล์ที่แนบกับเอกสาร

| No | Field |
|----|-------|
| 1 | ไฟล์แนบ |
| 2 | ตำแหน่ง |
| 3 | ผู้แนบ |
| 4 | รายละเอียด |
| 5 | วันที่ |

---

เมื่อคลิก

```
File Link
```

ระบบเปิด

```
New Tab
```

รองรับไฟล์แนบหลากหลายประเภท เช่น

- PDF
- DOC / DOCX
- XLS / XLSX
- PPT / PPTX
- CSV
- JPG
- GIF
- TIFF
- ZIP
- MP3
- XML
- HTML

ขนาดไฟล์

```
ไม่เกิน 5 MB ต่อไฟล์
```

ตามข้อกำหนดของระบบ :contentReference[oaicite:6]{index=6}

---

# End of Part 3

# Part 4

(See Part 4 content generated in chat.)

# Part 5

# 3.14 หน้าพิจารณาเอกสาร (Document Approval)

หลังจากเอกสารถูกส่งตาม Workflow ระบบจะแสดงหน้าพิจารณาตาม Role ของผู้ใช้งาน

โดยข้อมูลหลักของเอกสารทั้งหมดจะแสดงเป็น

```
Read Only
```

ผู้ใช้งานสามารถแก้ไขได้เฉพาะส่วน **พิจารณา (Review Panel)** เท่านั้น :contentReference[oaicite:0]{index=0}

---

# 3.14.1 ผู้บริหารสำนักบริหาร SBP

## Role

AVP OPT

```
SectionCode = 03
```

Status

```
รอผู้บริหารสำนักบริหาร SBP ดำเนินการ
```

---

## Review Panel

### ผลการพิจารณา

เลือกได้ดังนี้

| Result | Next Status |
|---------|-------------|
| เห็นควรชดเชย | ส่งฝ่ายบัญชี SBP |
| เห็นควรไม่ชดเชย | ส่งฝ่าย SBP DSA |
| ส่งกลับ GM ส่งเสริมฯ | ส่ง GM ส่งเสริมธุรกิจ |

:contentReference[oaicite:1]{index=1}

---

### ความคิดเห็นเพิ่มเติม

รองรับ

- ภาษาไทย
- ภาษาอังกฤษ
- ตัวเลข

แสดงผล

```
Left Align
```

---

### แนบไฟล์

ผู้ใช้งานสามารถ

- เพิ่มไฟล์
- ลบไฟล์
- ดาวน์โหลดไฟล์

ประเภทไฟล์

```
pdf
doc
docx
xls
xlsx
ppt
pptx
csv
jpg
gif
tiff
zip
wav
mp3
xml
html
txt
```

ขนาด

```
5 MB / File
```

:contentReference[oaicite:2]{index=2}

---

### ปุ่ม

#### ส่งดำเนินการ

Validation

```
ต้องเลือกผลการพิจารณา
```

หากไม่เลือก

```
ท่านยังไม่เลือกผลการพิจารณา
กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ
```

#### บันทึก

```
Save Draft
```

ไม่มี Validation

:contentReference[oaicite:3]{index=3}

---

# 3.14.2 ฝ่ายบัญชี SBP

## Role

Manager Account Franchise

```
SectionCode = 04
```

Status

```
รอฝ่ายบัญชีดำเนินการ
```

---

## ผลการพิจารณา

เลือกได้

| Result | Next Status |
|---------|-------------|
| บัญชีปฏิบัติการภาคดำเนินการ | ส่ง Operation Account |
| ฝ่าย SBP DSA ดำเนินการ | ส่งกลับ SBP DSA |

:contentReference[oaicite:4]{index=4}

---

## ความคิดเห็นเพิ่มเติม

รองรับข้อความทุกภาษา

---

## แนบไฟล์

เงื่อนไขเดียวกับ Role ก่อนหน้า

---

## Validation

ก่อนส่งดำเนินการ

```
ต้องเลือกผลการพิจารณา
```

ถ้าไม่เลือก

```
แสดง Pop-up
```

:contentReference[oaicite:5]{index=5}

---

# 3.14.3 บัญชีปฏิบัติการภาค

## Role

Operation Account

```
SectionCode = 05
```

Status

```
รอบัญชีปฏิบัติการภาคดำเนินการ
```

---

## ผลการพิจารณา

| Result | Next Status |
|---------|-------------|
| บัญชีภาคอนุมัติ | Completed |
| ฝ่ายบัญชี SBP ดำเนินการ | ส่งกลับฝ่ายบัญชี |

:contentReference[oaicite:6]{index=6}

---

## Validation

ก่อนส่งดำเนินการ

```
ต้องเลือกผลการพิจารณา
```

ถ้าไม่เลือก

```
ท่านยังไม่เลือกผลการพิจารณา
```

---

## Save

สามารถ

```
Save Draft
```

ได้ทุกครั้ง

:contentReference[oaicite:7]{index=7}

---

# User Acceptance Criteria

- สามารถดำเนินการสร้างเอกสารได้
- สามารถส่ง Workflow ได้
- Validation ถูกต้อง
- Save Draft ได้

:contentReference[oaicite:8]{index=8}

---

# 3.15 รายงานสรุปสถานะ (Summary Report)

## Purpose

ใช้สำหรับออกรายงานสรุปสถานะเอกสาร

Actor

- Admin
- HQ
- Report Admin

:contentReference[oaicite:9]{index=9}

---

# Search Criteria

| Field |
|--------|
| รหัสร้านที่ถูกกระทบ |
| ชื่อร้านที่ถูกกระทบ |
| เดือน / ปี |
| ถึง |
| ประเภทร้าน |
| ภาค |
| สถานะ |
| Period Statement From |
| Period Statement To |

---

## ประเภทร้าน

รองรับ

- FR Type A
- FR Type B
- FR Type C
- FR Type พนักงาน

สามารถเลือกได้

```
Multiple Select
```

:contentReference[oaicite:10]{index=10}

---

## ภาค

รองรับ

- BE
- BN
- BS
- BW
- RC
- RE
- RN
- RS

สามารถเลือกหลายค่าได้

:contentReference[oaicite:11]{index=11}

---

## ปุ่ม

### ค้นหา

เงื่อนไข

```
ต้องเลือกปี
```

จึงสามารถค้นหาได้

---

### เคลียร์ค่าเริ่มต้น

Reset Search Condition

---

### Export Excel

Export รายงานเป็น

```
Microsoft Excel
```

:contentReference[oaicite:12]{index=12}

---

# Search Result

| Column |
|----------|
| รหัสร้านถูกกระทบ |
| ชื่อร้านถูกกระทบ |
| ภาค |
| ประเภทร้าน |
| เดือน/ปีที่ชดเชย |
| วันที่โอนเป็นร้าน SP |
| Period Statement |
| รหัสร้านเปิดใหม่ |
| ชื่อร้านเปิดใหม่ |
| ภาค |
| ประเภทร้าน |
| ยอดเงินชดเชย |
| สถานะ |
| ชื่อผู้ดำเนินการ |
| ผลการพิจารณา |
| รอดำเนินการ (วัน) |
| ครั้งที่ |
| วันที่สร้าง |
| เลขที่เอกสาร |

:contentReference[oaicite:13]{index=13}

---

# รายละเอียดแต่ละ Column

| Column | Description |
|----------|-------------|
| รหัสร้านถูกกระทบ | Store Code |
| ชื่อร้านถูกกระทบ | Store Name |
| ภาค | Region |
| ประเภทร้าน | Store Type |
| เดือนปีที่ถูกกระทบ | Compensation Month |
| วันที่โอนเป็นร้าน SP | Transfer Date |
| Period Statement | Statement Period |
| รหัสร้านเปิดใหม่ | New Store Code |
| ชื่อร้านเปิดใหม่ | New Store Name |
| ภาค | New Region |
| ประเภทร้าน | New Store Type |
| ยอดเงินชดเชย | Compensation Amount |
| สถานะ | Current Status |
| ผู้ดำเนินการ | Current Owner |
| ผลการพิจารณา | Review Result |
| รอดำเนินการ (วัน) | Waiting Days |
| ครั้งที่ | Compensation รอบที่ |
| วันที่สร้าง | Create Date |
| เลขที่เอกสาร | Document No |

:contentReference[oaicite:14]{index=14}

---

## Export Excel

เมื่อกด

```
Export Excel
```

ระบบส่งออกข้อมูลตามเงื่อนไขการค้นหา

รูปแบบไฟล์

```
.xlsx
```

---

## User Acceptance Criteria

- สามารถค้นหารายงานได้
- Export Excel ได้
- ข้อมูลถูกต้องครบถ้วน

:contentReference[oaicite:15]{index=15}

---

# End of Part 4

## Purpose

ใช้สำหรับกำหนดผู้ปฏิบัติงานในแต่ละตำแหน่ง
เพื่อให้ Workflow สามารถส่งงานไปยังผู้รับผิดชอบที่ถูกต้อง

---

## Actor

- Admin
- HQ
- User Admin

---

## Pre-condition

- ผู้ใช้งาน Login เข้าสู่ระบบเรียบร้อย
- มีสิทธิ์ User Admin หรือ Admin

---

# หน้าจอ

## Panel : สิทธิ์ผู้ปฏิบัติงานในแต่ละตำแหน่ง

### Field

| No | Field | Type | Required |
|----|-------|------|----------|
| 1 | ชื่อพนักงาน | Search Popup | ✓ |
| 2 | ชื่อตำแหน่ง | Dropdown | ✓ |
| 3 | ภาค | Dropdown | Conditional |

:contentReference[oaicite:1]{index=1}

---

## รายละเอียด Field

### ชื่อพนักงาน

กดปุ่มแว่นขยาย

ระบบเปิด

```
Employee Popup
```

เพื่อเลือกพนักงานจากฐานข้อมูล

---

### ชื่อตำแหน่ง

เลือกจาก

```
Drop Down List
```

ตัวอย่าง

- SBP DSA
- เจ้าหน้าที่ SBP DSA
- ฝ่ายส่งเสริมธุรกิจ
- GM ส่งเสริมธุรกิจ
- ผู้บริหารสำนัก
- ฝ่ายบัญชี
- บัญชีปฏิบัติการภาค

---

### ภาค

จะแสดงเฉพาะกรณี

```
ชื่อตำแหน่ง

=

ส่งเสริมธุรกิจพันธมิตร
```

ผู้ใช้สามารถเลือกจาก

```
Drop Down
```

เช่น

- BE
- BN
- BS
- BW
- RC
- RE
- RN
- RS

:contentReference[oaicite:2]{index=2}

---

# ปุ่มการทำงาน

## เพิ่มข้อมูล

เมื่อกด

```
เพิ่มข้อมูล
```

ระบบจะ

- ตรวจสอบข้อมูล
- บันทึกข้อมูล
- เพิ่มรายการใหม่

ข้อมูลถูกจัดเก็บลง

```
MaintainMasterHistory
```

และ

```
CompenOrganizeProfile
```

:contentReference[oaicite:3]{index=3}

---

## Validation

ต้องกรอก

- ชื่อพนักงาน
- ชื่อตำแหน่ง

กรณีตำแหน่งต้องใช้ภาค

ต้องเลือก

```
ภาค
```

ด้วย

หากไม่ครบ

แสดง

```
กรุณาระบุข้อมูลให้ครบถ้วน
```

---

## ปุ่มเคลียร์

Reset ค่า

ทุก Field

กลับเป็นค่าเริ่มต้น

---

# รายชื่อผู้ปฏิบัติงาน

ระบบแสดงรายการทั้งหมด

| Column |
|----------|
| ชื่อพนักงาน |
| ตำแหน่ง |
| ภาค |
| วันที่สร้าง |
| ผู้สร้าง |

เมื่อคลิกที่รายการ

ระบบเปิด

```
Edit Mode
```

สามารถ

- แก้ไข
- บันทึก
- ยกเลิก

ได้ตามสิทธิ์

---

# Business Rules

## Rule 1

พนักงานหนึ่งคน

สามารถมีหลายตำแหน่ง

---

## Rule 2

ตำแหน่งที่กำหนดภาค

ต้องเลือกภาคทุกครั้ง

---

## Rule 3

ข้อมูลที่ถูกแก้ไข

ต้องเก็บประวัติ

```
History
```

ทุกครั้ง

---

## Rule 4

ไม่อนุญาตให้มีข้อมูลซ้ำ

```
Employee + Position + Region
```

---

# Database

## Table

MaintainMasterHistory

ใช้เก็บ

- Create
- Update
- Delete History

---

CompenOrganizeProfile

ใช้เก็บ

- Current Organization
- Workflow Mapping

---

# Security

เฉพาะ

```
Admin

HQ

User Admin
```

เท่านั้น

ที่สามารถ

```
Create

Update

Delete
```

ข้อมูลได้

---

Role อื่น

```
Read Only
```

---

# Audit Log

ทุกการแก้ไข

ต้องเก็บ

- User
- DateTime
- Action
- Before
- After

---

# Error Handling

กรณี

Employee ไม่มีในระบบ

```
ไม่สามารถบันทึกข้อมูลได้
```

---

กรณี

Duplicate Data

```
พบข้อมูลซ้ำในระบบ
```

---

กรณี

Database Error

```
ระบบไม่สามารถบันทึกข้อมูลได้
กรุณาติดต่อผู้ดูแลระบบ
```

---

# User Acceptance Criteria

- สามารถค้นหาพนักงานได้
- กำหนดตำแหน่งได้
- กำหนดภาคได้
- แก้ไขข้อมูลได้
- ลบข้อมูลได้ตามสิทธิ์
- เก็บ Audit Log ทุกครั้ง
- ตรวจสอบข้อมูลซ้ำก่อนบันทึก
- Workflow สามารถนำข้อมูลไปใช้งานได้

---

# Appendix A : Supported File Types

ระบบรองรับไฟล์แนบ

- PDF
- DOC
- DOCX
- XLS
- XLSX
- PPT
- PPTX
- CSV
- ZIP
- JPG
- JPEG
- GIF
- TIFF
- XML
- HTML
- TXT
- MP3
- WAV
- MOV
- MPG

---

# Appendix B : Workflow Summary

```text
Create
   │
   ▼
SBP DSA (06)
   │
   ▼
Officer SBP DSA (08)
   │
   ▼
Business Promotion (01)
   │
   ▼
GM (02)
   │
   ├──── Amount >100,000 ───► AVP (03)
   │                              │
   │                              ▼
   └──── Amount <=100,000 ─► Account (04)
                                  │
                                  ▼
                         Operation Account (05)
                                  │
                                  ▼
                              Completed
```

---

# End of Document
