# LLDD FE - Status Summary Report

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Overview

| รายการ | รายละเอียด |
| --- | --- |
| Track | FE |
| Estimate | 30 ชั่วโมง |
| Owner | Peerakorn <Pete> Sakunkaewphithak |
| Objective | สร้างรายงานตรวจสอบประกันรายได้ตาม SDD สไลด์ 60 (7 ตัวกรอง / 14 คอลัมน์) พร้อมค้นหาข้อมูลและ Export Excel |

Common contract reference: ทุกหัวข้อ API/FE ต้องยึด LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts สำหรับ error/auth/format/pagination/action/RBAC ก่อนลงรายละเอียดเฉพาะหน้าหรือเฉพาะ endpoint

## 2. Screen / Functional Scope

- Report filters (SDD slide 60 · 2026-08-06: สถานะ*|รหัสร้านถูกกระทบ · รหัสร้านเปิดกระทบ|ประเภทร้าน A/B/C/E · Period Statement From-To (date, ค.ศ.) เต็มแถว · ภาคเต็มแถว · ผลการพิจารณาเต็มแถว)
- Summary table (sortable 14 columns)
- Export Excel action
- Sample data verification

## 3. Screenshot Reference

![รูปที่ 1: Screenshot: k2-report-01.png](../../../output/srs/screenshots/slices/k2-report-01.png)

_รูปที่ 1: Screenshot: k2-report-01.png_

![รูปที่ 2: Screenshot: k2-report-02.png](../../../output/srs/screenshots/slices/k2-report-02.png)

_รูปที่ 2: Screenshot: k2-report-02.png_

## 4. Implementation Flow Diagram (Reference)

![รูปที่ 3: Implementation flow reference: LLDD FE - Status Summary Report](../../assets/flows/FE-LLDD-FE-Report.png)

_รูปที่ 3: Implementation flow reference: LLDD FE - Status Summary Report_

## 5. Field, Format, and Validation

| Field / UI | Format | Validation | Behavior |
| --- | --- | --- | --- |
| impactedStoreCode | string 5 digits | optional; numeric only when input | คง leading zero; ปุ่มแว่นขยายเรียก popup เลือกร้านที่ถูกกระทบ |
| impactedStoreName | string | readonly | แสดงอัตโนมัติหลังเลือกรหัสร้าน; ไม่ส่งเป็น filter หลักถ้ามี storeCode |
| newStoreCode | string 5 digits | optional; numeric only when input | รหัสร้านเปิดกระทบ/ร้านเปิดใหม่; คง leading zero |
| impactMonthFrom | YYYY-MM | optional; month picker | ส่งเป็น ค.ศ. เช่น 2026-05; FE แสดงเดือน/ปี พ.ศ. ในตาราง |
| impactMonthTo | YYYY-MM | optional; month picker; must be >= from | ถ้า from > to ให้แสดง validation ก่อน call API |
| storeTypes | array enum A\|B\|C\|D | optional multi select | checkbox เลือกได้มากกว่า 1; ส่งเป็น comma/query array |
| status | statusCode string | required single select | บังคับเลือก 1 สถานะก่อน Preview/Export; options ตรงกับ document_statuses |
| resultCategory | APPROVE\|REJECT | required radio | APPROVE=ประกันรายได้, REJECT=ไม่ประกันรายได้ |
| regions | array enum | optional multi select | รองรับ BE, BS, NEU, REU, RSU, BG, BW, RC, RN, BN, NEL, REL, RSL และภาคใหม่จาก API |
| statementPeriodFrom | YYYY-MM | optional month picker | Period Statement From; ส่ง ค.ศ. format YYYY-MM |
| statementPeriodTo | YYYY-MM | optional month picker; must be >= from | Period Statement To; validate range ก่อน call API |
| page | integer | default 1; >=1 | pagination ของ preview table |
| size | integer | default 20; max 100 | BE จำกัด page size เพื่อกัน query หนัก |
| resultTable.storeCode | string 5 digits | display only | คอลัมน์ 1 รหัสร้านถูกกระทบ |
| resultTable.storeName | string | display only | คอลัมน์ 2 ชื่อร้านถูกกระทบ |
| resultTable.region | string | display only | คอลัมน์ 3 ภาค |
| resultTable.storeType | string | display only | คอลัมน์ 4 ประเภทร้าน |
| resultTable.impactMonth | MM/YYYY พ.ศ. | display only | คอลัมน์ 5 เดือนปีที่ถูกกระทบ |
| resultTable.transferToSpDate | DD/MM/YYYY พ.ศ. | nullable | คอลัมน์ 6 วันที่โอนเป็นร้าน SP |
| resultTable.statementPeriod | MM/YYYY พ.ศ. | nullable | คอลัมน์ 7 Period Statement |
| resultTable.newStoreCode | string 5 digits or '-' | display only | คอลัมน์ 8 รหัสร้านเปิดใหม่ |
| resultTable.newStoreName | string or '-' | display only | คอลัมน์ 9 ชื่อร้านเปิดใหม่ |
| resultTable.newStoreRegion | string or '-' | display only | คอลัมน์ 10 ภาค (ร้านใหม่) |
| resultTable.newStoreType | string or '-' | display only | คอลัมน์ 11 ประเภทร้าน (ร้านใหม่) |
| resultTable.compensationAmount | number #,##0.00 | >=0 | คอลัมน์ 12 ยอดเงินชดเชย; align right |
| resultTable.statusName | string/status badge | required | คอลัมน์ 13 สถานะ; สี badge ตาม status |
| resultTable.operatorName | string | nullable | คอลัมน์ 14 ชื่อ-นามสกุลผู้ดำเนินการ |
| resultTable.resultText | string | nullable | คอลัมน์ 15 ผลการพิจารณา |
| resultTable.waitingDays | integer | >=0 | คอลัมน์ 16 รอดำเนินการ (วัน) |
| derived.salesDataDays | integer | <60 = abnormal | ข้อมูลประกอบสำหรับ class flag-red; ไม่ใช่ waitingDays |
| resultTable.roundNo | integer | >=1 | คอลัมน์ 17 ครั้งที่ |
| resultTable.createdDate | DD/MM/YYYY พ.ศ. | required | คอลัมน์ 18 วันที่สร้าง |
| resultTable.docNo | YYYY/xxxxx | required | คอลัมน์ 19 เลขที่เอกสาร; ใช้เปิด detail/preview |

## 5.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | GET /store/search (ระบบ SBP เดิม); GET /api/v1/reports/status-summary; GET /api/v1/reports/status-summary/export |
| Progress | เปิดหน้า Report; โหลด reference status/region/store type ถ้ามี API (ภาคใหม่แสดง checkbox อัตโนมัติ); ผู้ใช้ระบุ filter 7 ตัวตาม SDD สไลด์ 60; Validate status (required) · คู่รหัสร้านถูกกระทบ-เปิดกระทบ · Period Statement บังคับเมื่อสถานะ = เสร็จสิ้นดำเนินการ |
| Output | Rendered UI state or normalized API response with status/message and audit-ready trace reference. |

### 5.90 Status Summary Report Component Contract

| ID | Component / Scope | Single responsibility | Definition of done |
| --- | --- | --- | --- |
| C01 | Report filters (SDD slide 60 · 2026-08-06: สถานะ*\|รหัสร้านถูกกระทบ · รหัสร้านเปิดกระทบ\|ประเภทร้าน A/B/C/E · Period Statement From-To (date, ค.ศ.) เต็มแถว · ภาคเต็มแถว · ผลการพิจารณาเต็มแถว) | จัดการ filter 7 ตัวตาม SDD สไลด์ 60 (status, impacted/new store code, store type, period statement, region, result) พร้อม dependency validation | status required, คู่รหัสร้านต้องมาด้วยกัน, period statement บังคับเมื่อสถานะ = เสร็จสิ้นดำเนินการ และช่วง from-to ตรวจผ่านก่อนค้นหา/Export |
| C02 | Summary table (sortable 14 columns) | map response เป็น summary line และตาราง 14 คอลัมน์ (SDD สไลด์ 60) ด้วย formatter กลาง | คอลัมน์/ยอดรวม/วันที่ (ค.ศ.)/leading zero ตรง response และข้อมูลยอดขายผิดปกติใช้ salesDataDays |
| C03 | Export Excel action | ส่ง filter snapshot ล่าสุดไป export endpoint และจัดการ download/error state | Export Excel ใช้เงื่อนไขเดียวกับการค้นหา และชื่อไฟล์/content type (.xlsx) ตรง response |
| C04 | Sample data verification | รองรับ fixture สำหรับ 0 แถว, หลาย region/type, เกิน threshold และยอดขายไม่ครบ 60 วัน | sample verification ครอบคลุม table/export parity 14 คอลัมน์ โดยไม่ฝังข้อมูลทดสอบใน production |

### 5.91 Status Summary Report API Adapter Map

| Endpoint | Typed adapter purpose | Invoked by |
| --- | --- | --- |
| GET /store/search (ระบบ SBP เดิม) | Popup เลือกร้านที่ถูกกระทบ | เปิด popup ร้าน (ปุ่มแว่นขยายข้างรหัสร้านที่ถูกกระทบ) |
| GET /api/v1/reports/status-summary | ค้นหาข้อมูลรายงานตรวจสอบประกันรายได้ (14 คอลัมน์ · SDD สไลด์ 60) | ค้นหาข้อมูล (ปุ่ม ค้นหาข้อมูล); Export Excel (ปุ่ม Export Excel ท้าย filter) |
| GET /api/v1/reports/status-summary/export | Export Excel ด้วย filter เดียวกับการค้นหา | Export Excel (ปุ่ม Export Excel ท้าย filter) |

### 5.92 Status Summary Report Interaction State Machine

| Action | Trigger | API / State transition | Expected visible result |
| --- | --- | --- | --- |
| เปิด popup ร้าน | ปุ่มแว่นขยายข้างรหัสร้านที่ถูกกระทบ | GET /store/search (ระบบ SBP เดิม) | เลือก store แล้วเติม storeCode/storeName |
| ค้นหาข้อมูล | ปุ่ม ค้นหาข้อมูล | GET /api/v1/reports/status-summary | validate status (required) และคู่รหัสร้าน แล้ว render summary line + table 14 columns |
| เคลียร์ค่าเริ่มใหม่ | ปุ่มเคลียร์ค่าเริ่มใหม่ | client state | reset filter, summary, table และ error message |
| Export Excel | ปุ่ม Export Excel ท้าย filter | GET /api/v1/reports/status-summary/export | ส่ง filter ชุดเดียวกับการค้นหา แล้วดาวน์โหลดไฟล์ .xlsx 14 คอลัมน์ |
| Hover chart | hover bar chart | client chart tooltip | แสดง tooltip จำนวนเอกสาร/ยอดเงินตามภาค |
| Open detail | คลิกเลขที่เอกสารหรือ row | navigate /documents/{docNo} หรือ preview modal | เปิดเอกสารที่เกี่ยวข้อง |

### 5.93 Status Summary Report Feature Failure Checks

| Case | Feature-specific scenario | Expected evidence |
| --- | --- | --- |
| FE-01 | ไม่เลือก status แล้วค้นหาต้อง block | status เป็น required ตัวเดียวก่อนค้นหา/export (resultCategory เป็นตัวเลือก · SDD สไลด์ 60) |
| FE-02 | ระบุร้านถูกกระทบแต่ไม่ระบุร้านเปิดกระทบ ต้อง block | ระบุ impactedStoreCode แล้วต้องระบุ newStoreCode ด้วย |
| FE-03 | periodStatementFrom > periodStatementTo ต้อง error REPORT_DATE_RANGE_INVALID | Period Statement เป็นช่วงวันที่ ค.ศ. และ from <= to |
| FE-04 | สถานะ = เสร็จสิ้นดำเนินการ แต่ไม่ระบุ Period Statement ต้อง block | ตารางแสดง 14 คอลัมน์ครบและ export ออกครบ 14 คอลัมน์ |
| FE-05 | ค้นหาด้วยร้านถูกกระทบ | ยอดเงิน format #,##0.00 และ total summary ตรงกับผลรวม API |
| FE-06 | เลือกหลาย region/storeType | แถวข้อมูลยอดขายไม่ครบ 60 วันใช้ class flag-red โดยอิง derived.salesDataDays < 60 |

## 6. Button / User Action Mapping

| Action | Trigger | API / Service | Expected Result |
| --- | --- | --- | --- |
| เปิด popup ร้าน | ปุ่มแว่นขยายข้างรหัสร้านที่ถูกกระทบ | GET /store/search (ระบบ SBP เดิม) | เลือก store แล้วเติม storeCode/storeName |
| ค้นหาข้อมูล | ปุ่ม ค้นหาข้อมูล | GET /api/v1/reports/status-summary | validate status (required) และคู่รหัสร้าน แล้ว render summary line + table 14 columns |
| เคลียร์ค่าเริ่มใหม่ | ปุ่มเคลียร์ค่าเริ่มใหม่ | client state | reset filter, summary, table และ error message |
| Export Excel | ปุ่ม Export Excel ท้าย filter | GET /api/v1/reports/status-summary/export | ส่ง filter ชุดเดียวกับการค้นหา แล้วดาวน์โหลดไฟล์ .xlsx 14 คอลัมน์ |
| Hover chart | hover bar chart | client chart tooltip | แสดง tooltip จำนวนเอกสาร/ยอดเงินตามภาค |
| Open detail | คลิกเลขที่เอกสารหรือ row | navigate /documents/{docNo} หรือ preview modal | เปิดเอกสารที่เกี่ยวข้อง |

## 7. API Contract

### GET /store/search (ระบบ SBP เดิม)

Popup เลือกร้านที่ถูกกระทบ

#### Query Params

```json
{
  "q": "00788",
  "type": "impacted"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| q | string | No | UTF-8; use value domain described by endpoint purpose |
| type | string | No | UTF-8; use value domain described by endpoint purpose |

#### Response

```json
{
  "items": [
    {
      "storeCode": "00788",
      "storeName": "รัตนอุทิศ ซ.13",
      "region": "RS",
      "storeType": "FR Type B"
    }
  ]
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| items | array<object> | Yes | JSON array; element type shown in Type column |
| items[].storeCode | string | Yes | exactly 5 digits; preserve leading zero |
| items[].storeName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].region | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].storeType | string | Yes | UTF-8; use value domain described by endpoint purpose |

### GET /api/v1/reports/status-summary

ค้นหาข้อมูลรายงานตรวจสอบประกันรายได้ (14 คอลัมน์ · SDD สไลด์ 60)

#### Query Params

```json
{
  "status": "06",
  "impactedStoreCode": "00788",
  "newStoreCode": "00990",
  "periodStatementFrom": "2026-06-01",
  "periodStatementTo": "2026-06-30",
  "storeTypes": [
    "A",
    "B"
  ],
  "regions": [
    "RSU",
    "BN"
  ],
  "result": "APPROVE",
  "page": 1,
  "size": 20
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| status | string | Yes | UTF-8; use value domain described by endpoint purpose |
| impactedStoreCode | string | No | exactly 5 digits; preserve leading zero |
| newStoreCode | string | No | exactly 5 digits; preserve leading zero |
| periodStatementFrom | string | No | UTF-8; use value domain described by endpoint purpose |
| periodStatementTo | string | No | UTF-8; use value domain described by endpoint purpose |
| storeTypes | array<string> | No | JSON array; element type shown in Type column |
| regions | array<string> | No | JSON array; element type shown in Type column |
| result | string | No | UTF-8; use value domain described by endpoint purpose |
| page | integer | No | >= 1; default 1 |
| size | integer | No | 1..100; default 20 |

#### Response

```json
{
  "page": 1,
  "size": 20,
  "total": 10,
  "summary": {
    "totalItems": 10,
    "totalCompensationAmount": 439100.0,
    "overThresholdItems": 3,
    "abnormalSalesItems": 2
  },
  "items": [
    {
      "impactedStoreCode": "00788",
      "impactedStoreName": "รัตนอุทิศ ซ.13",
      "impactedRegion": "RSU",
      "impactedStoreType": "B",
      "impactMonth": "2026-05",
      "periodStatement": "2026-06-07",
      "newStoreCode": "00990",
      "newStoreName": "เซเว่นฯ รัตนาธิเบศร์ 12",
      "newRegion": "RSU",
      "newStoreType": "A",
      "compensationAmount": 48200.0,
      "roundNo": 1,
      "createdDate": "2026-06-12",
      "docNo": "2026/00123"
    }
  ]
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| page | integer | Yes | >= 1; default 1 |
| size | integer | Yes | 1..100; default 20 |
| total | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| summary | object | Yes | JSON object; nested fields listed below |
| summary.totalItems | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| summary.totalCompensationAmount | number | Yes | number >= 0 with 2 decimals |
| summary.overThresholdItems | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| summary.abnormalSalesItems | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| items | array<object> | Yes | JSON array; element type shown in Type column |
| items[].impactedStoreCode | string | Yes | exactly 5 digits; preserve leading zero |
| items[].impactedStoreName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].impactedRegion | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].impactedStoreType | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].impactMonth | string | Yes | ISO-8601 ค.ศ.; nullable only when type includes null |
| items[].periodStatement | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].newStoreCode | string | Yes | exactly 5 digits; preserve leading zero |
| items[].newStoreName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].newRegion | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].newStoreType | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].compensationAmount | number | Yes | number >= 0 with 2 decimals |
| items[].roundNo | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].createdDate | string | Yes | ISO-8601 ค.ศ.; nullable only when type includes null |
| items[].docNo | string | Yes | พ.ศ. YYYY/xxxxx |

### GET /api/v1/reports/status-summary/export

Export Excel ด้วย filter เดียวกับการค้นหา

#### Query Params

```json
{
  "sameAsSearch": true,
  "format": "xlsx"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| sameAsSearch | boolean | No | UTF-8; use value domain described by endpoint purpose |
| format | string | No | ISO-8601 ค.ศ.; nullable only when type includes null |

#### Response

```json
{
  "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "fileName": "insurance-verification-2026.xlsx"
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| contentType | string | Yes | UTF-8; use value domain described by endpoint purpose |
| fileName | string | Yes | UTF-8; use value domain described by endpoint purpose |

## 9. Processing Flow

| Step | Description |
| --- | --- |
| 1 | เปิดหน้า Report |
| 2 | โหลด reference status/region/store type ถ้ามี API (ภาคใหม่แสดง checkbox อัตโนมัติ) |
| 3 | ผู้ใช้ระบุ filter 7 ตัวตาม SDD สไลด์ 60 |
| 4 | Validate status (required) · คู่รหัสร้านถูกกระทบ-เปิดกระทบ · Period Statement บังคับเมื่อสถานะ = เสร็จสิ้นดำเนินการ |
| 5 | กด ค้นหาข้อมูล แล้ว call report API |
| 6 | แสดงวันที่เป็น ค.ศ. ตามระบบ SBP เดิม (ไม่แปลงเป็น พ.ศ. — ตัดสินใจ 2026-08-06) |
| 7 | render summary line และ table 14 คอลัมน์ |
| 8 | กด Export Excel แล้วส่ง filter เดียวกันไป export API |

## 10. Acceptance Criteria

- status เป็น required ตัวเดียวก่อนค้นหา/export (resultCategory เป็นตัวเลือก · SDD สไลด์ 60)
- ระบุ impactedStoreCode แล้วต้องระบุ newStoreCode ด้วย
- Period Statement เป็นช่วงวันที่ ค.ศ. และ from <= to
- ตารางแสดง 14 คอลัมน์ครบและ export ออกครบ 14 คอลัมน์
- ยอดเงิน format #,##0.00 และ total summary ตรงกับผลรวม API
- แถวข้อมูลยอดขายไม่ครบ 60 วันใช้ class flag-red โดยอิง derived.salesDataDays < 60
- export ใช้ filter เดียวกับการค้นหาล่าสุด

## 11. Developer Test Checklist

| No | Test |
| --- | --- |
| 1 | ไม่เลือก status แล้วค้นหาต้อง block |
| 2 | ระบุร้านถูกกระทบแต่ไม่ระบุร้านเปิดกระทบ ต้อง block |
| 3 | periodStatementFrom > periodStatementTo ต้อง error REPORT_DATE_RANGE_INVALID |
| 4 | สถานะ = เสร็จสิ้นดำเนินการ แต่ไม่ระบุ Period Statement ต้อง block |
| 5 | ค้นหาด้วยร้านถูกกระทบ |
| 6 | เลือกหลาย region/storeType |
| 7 | render table 14 columns |
| 8 | export xlsx |
| 9 | empty result แสดง summary เป็น 0 |
