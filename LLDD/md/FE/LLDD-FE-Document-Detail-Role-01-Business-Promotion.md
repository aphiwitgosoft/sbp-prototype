# LLDD FE - Document Detail Role 01 Business Promotion

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Overview

| รายการ | รายละเอียด |
| --- | --- |
| Track | FE |
| Estimate | 10 ชั่วโมง |
| Owner | Kittisak <New> Kaeowika |
| Objective | อธิบายหน้าจอ Document Detail สำหรับ role 01 - ฝ่ายส่งเสริมธุรกิจฯ |

Common contract reference: ทุกหัวข้อ API/FE ต้องยึด LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts สำหรับ error/auth/format/pagination/action/RBAC ก่อนลงรายละเอียดเฉพาะหน้าหรือเฉพาะ endpoint

## 2. Screen / Functional Scope

- Role profile P-01 - ฝ่ายส่งเสริมธุรกิจฯ
- Visible/read-only/hidden section behavior
- Editable field and validation behavior
- Attachment upload behavior
- Action panel options and API response sample

## 4. Implementation Flow Diagram (Reference)

![รูปที่ 1: Implementation flow reference: LLDD FE - Document Detail Role 01 Business Promotion](../../assets/flows/FE-LLDD-FE-Document-Detail-Role-01-Business-Promotion.png)

_รูปที่ 1: Implementation flow reference: LLDD FE - Document Detail Role 01 Business Promotion_

## 5. Field, Format, and Validation

| Field / UI | Format | Validation | Behavior |
| --- | --- | --- | --- |
| roleProfileCode | P-01 | must match API response | ใช้เลือก view profile เฉพาะบทบาทนี้; แยก namespace จาก workflow section code |
| statusCode | 01 | from API | workflow status/section code ปัจจุบัน ไม่ใช่ role profile |
| visibleSections | string[] | from API | FE แสดงเฉพาะ section ใน array |
| editableSections | string[] | from API | FE เปิด input/button เฉพาะ section ใน array |
| actionOptions | array | from API | FE render radio จาก array โดยไม่ hardcode |

### 5.1 Role View Summary

| Item | Value |
| --- | --- |
| Role profile | P-01 - ฝ่ายส่งเสริมธุรกิจฯ |
| Workflow section/status code | 01 |
| Document status shown | รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ |
| Purpose on this page | ปรับข้อมูลร้านเปิดใหม่ ร้านคู่แข่ง ปัจจัยอื่น และส่งผลพิจารณา |
| Editable sections | sec-newstore, sec-competitor, sec-factor |
| Hidden sections | sec-calc |
| Attachment upload | Allowed |

### 5.2 What This Role Sees

- เป็น role profile เดียวที่แก้เนื้อหาเอกสารได้
- แก้ % ชดเชย เพิ่ม/แก้/ลบร้านคู่แข่ง และเพิ่ม/แก้/ลบปัจจัยอื่นได้
- ไม่เห็น section คำนวณเงินชดเชย

### 5.3 Section-by-section Behavior

| Section key | UI section | State for this role | Control behavior |
| --- | --- | --- | --- |
| doc-header | ข้อมูลร้านถูกกระทบ | Read-only | แสดงข้อมูลและปิด input/editor |
| sec-sales | แนวโน้มยอดขายรายวัน | Read-only | แสดงข้อมูลและปิด input/editor |
| sec-map | แผนที่ AllMap | Read-only | แสดงข้อมูลและปิด input/editor |
| sec-newstore | ร้านเปิดใหม่ | Editable | เปิด input/action เฉพาะ field ที่ระบุในเอกสารนี้ |
| sec-competitor | ร้านคู่แข่งเปิดกระทบ | Editable | เปิด input/action เฉพาะ field ที่ระบุในเอกสารนี้ |
| sec-factor | ปัจจัยอื่นๆ | Editable | เปิด input/action เฉพาะ field ที่ระบุในเอกสารนี้ |
| sec-attach | เอกสารแนบทั้งหมด | Read-only + Upload | ดูรายการไฟล์และเพิ่มไฟล์แนบได้ |
| sec-calc | คำนวณเงินชดเชย | Hidden | ไม่ render section |
| sec-comp-history | ประวัติการชดเชย | Read-only | แสดงข้อมูลและปิด input/editor |
| sec-decision-history | ผลการพิจารณา (ประวัติ) | Read-only | แสดงข้อมูลและปิด input/editor |
| sec-action | พิจารณา / ส่งดำเนินการ | Action | แสดง radio result, textarea comment, ปุ่มส่งดำเนินการ |

### 5.4 Editable Form Fields

| Area | Fields | Validation / Behavior |
| --- | --- | --- |
| ร้านเปิดใหม่ | newStoreCode, newStoreName, openDate, distanceKm, compensatePercent, calculatedCompensationAmount | แก้ได้เฉพาะ compensatePercent; ผลรวมต้องเท่ากับ 100 |
| ร้านคู่แข่ง | competitorName, openedImpactDate, detail, remark | เพิ่ม/แก้/ลบได้; ต้องเลือกร้านคู่แข่งก่อนบันทึก |
| ปัจจัยอื่นๆ | factorName, startDate, endDate, detail, remark | เพิ่ม/แก้/ลบได้; endDate ต้องไม่ก่อน startDate |
| เอกสารแนบ | file, fileName, attachmentType, remark | เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist |
| แผงพิจารณา | result, comment | result required; comment required เมื่อเลือก เห็นควรไม่ชดเชย |

### 5.5 Action Panel

FE ต้อง render ตัวเลือกจาก `actionOptions` ที่ API ส่งมาเท่านั้น และส่ง payload `{result,comment}` โดยไม่คำนวณปลายทาง action เอง

| Radio option | Comment rule |
| --- | --- |
| เห็นควรชดเชย | comment optional |
| เห็นควรไม่ชดเชย | ต้องกรอก comment |
| ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ) | comment ตาม actionOptions.requireComment |

### 5.6 API Response Example

#### GET /api/v1/documents/{docNo} response

```json
{
  "docNo": "2569/00123",
  "statusCode": "01",
  "viewerRbacRoleCode": "R-XX",
  "roleProfileCode": "P-01",
  "visibleSections": [
    "doc-header",
    "sec-sales",
    "sec-map",
    "sec-newstore",
    "sec-competitor",
    "sec-factor",
    "sec-attach",
    "sec-comp-history",
    "sec-decision-history",
    "sec-action"
  ],
  "editableSections": [
    "sec-newstore",
    "sec-competitor",
    "sec-factor"
  ],
  "canUploadAttachment": true,
  "canAction": true,
  "actionOptions": [
    {
      "label": "เห็นควรชดเชย",
      "requireComment": false
    },
    {
      "label": "เห็นควรไม่ชดเชย",
      "requireComment": true
    },
    {
      "label": "ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ)",
      "requireComment": false
    }
  ]
}
```

### 5.7 Validation Popup Text

| Condition | Popup message |
| --- | --- |
| กดส่งดำเนินการโดยไม่เลือกผลการพิจารณา | ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ |
| result ที่ requireComment=true แต่ comment ว่าง | กรุณากรอกความคิดเห็นเพิ่มเติม (บังคับกรอกสำหรับผลการพิจารณานี้) ก่อนส่งดำเนินการ |
| ผลรวม %ชดเชยร้านเปิดใหม่ไม่เท่ากับ 100 | โปรดตรวจสอบ %ชดเชย ของท่าน รวมกันแล้วไม่เท่ากับ 100% |

### 5.8 Role-specific Test Checklist

| No | Test |
| --- | --- |
| 1 | เปิดด้วย roleProfileCode=P-01 แล้ว sec-newstore/sec-competitor/sec-factor ต้อง editable |
| 2 | แก้ compensatePercent แล้วรวมไม่ครบ 100 ต้อง error COMPENSATE_PERCENT_INVALID |
| 3 | เพิ่มร้านคู่แข่งโดยไม่เลือก competitor ต้อง error COMPETITOR_REQUIRED |
| 4 | เพิ่มปัจจัยอื่นโดยไม่เลือก factor ต้อง error EXTERNAL_FACTOR_REQUIRED |
| 5 | sec-calc ต้องไม่ render สำหรับ role 01 |

## 5.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | GET /api/v1/documents/{docNo}; POST /api/v1/documents/{docNo}/actions |
| Progress | Load document detail; Apply visibleSections and editableSections; Render fields/actions for this role only; Validate popup text |
| Output | Rendered UI state or normalized API response with status/message and audit-ready trace reference. |

### 5.90 Document Detail Role 01 Business Promotion Implementation Steps

| Step | Implementation detail | Check |
| --- | --- | --- |
| Load exact profile | เรียก GET /api/v1/documents/{docNo} และยืนยัน roleProfileCode=P-01, statusCode=01 ก่อน render action state | profile mismatch ต้อง fail closed; ไม่ใช้ role switcher เพื่อจำลอง P-01 |
| Render profile sections | render เฉพาะ visibleSections ของ P-01: doc-header, sec-sales, sec-map, sec-newstore, sec-competitor, sec-factor, sec-attach, sec-comp-history, sec-decision-history, sec-action; ซ่อน: sec-calc | section ที่ซ่อนต้องไม่อยู่ใน DOM และ section key ที่ไม่รู้จักต้อง log/ignore แบบ fail closed |
| Apply edit boundary | เปิด mutation control เฉพาะ editableSections ของ P-01: sec-newstore, sec-competitor, sec-factor | read-only section ไม่มี focusable input/save/add/delete และ payload ต้องไม่มี field นอก editableSections |
| Attachment control | canUploadAttachment=true สำหรับ Business Promotion; ใช้ allowlist, 5 MB และ scan-status contract | ปุ่ม upload ตรง flag, FILE_TOO_LARGE/FILE_SCAN_BLOCKED แสดงที่ attachment section |
| Render exact action set | แสดง actionOptions ของ P-01 เท่านั้น: เห็นควรชดเชย; เห็นควรไม่ชดเชย; ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ); comment rules: เห็นควรชดเชย: comment optional; เห็นควรไม่ชดเชย: ต้องกรอก comment; ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ): comment ตาม actionOptions.requireComment | radio label/requireComment มาจาก API และ FE ไม่คำนวณ nextSection |
| Submit and reload | ส่ง result/comment สำหรับ P-01 แล้ว invalidate detail, timeline, task/list cache | หลัง submit ต้องโหลด status/actionOptions ใหม่และไม่คง action set ของ P-01 เมื่อ workflow เปลี่ยนขั้น |

## 6. Button / User Action Mapping

| Action | Trigger | API / Service | Expected Result |
| --- | --- | --- | --- |
| Load detail | เปิดเอกสาร | GET /api/v1/documents/{docNo} | render role profile |
| Save editable section | ปุ่มบันทึก | PUT /api/v1/documents/{docNo} | ใช้เฉพาะ role ที่มี editableSections |
| Upload attachment | เลือกไฟล์ | POST /api/v1/documents/{docNo}/attachments | append attachment when allowed |
| Submit action | ปุ่มส่งดำเนินการ | POST /api/v1/documents/{docNo}/actions | submit selected result |

## 7. API Contract

### GET /api/v1/documents/{docNo}

โหลด role profile P-01 สำหรับหน้า detail

#### Query Params

```json
{
  "docNo": "2569/00123"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| docNo | string | No | พ.ศ. YYYY/xxxxx |

#### Response

```json
{
  "docNo": "2569/00123",
  "statusCode": "01",
  "viewerRbacRoleCode": "R-XX",
  "roleProfileCode": "P-01",
  "visibleSections": [
    "doc-header",
    "sec-sales",
    "sec-map",
    "sec-newstore",
    "sec-competitor",
    "sec-factor",
    "sec-attach",
    "sec-comp-history",
    "sec-decision-history",
    "sec-action"
  ],
  "editableSections": [
    "sec-newstore",
    "sec-competitor",
    "sec-factor"
  ],
  "actionOptions": [
    {
      "label": "เห็นควรชดเชย",
      "requireComment": false
    },
    {
      "label": "เห็นควรไม่ชดเชย",
      "requireComment": true
    },
    {
      "label": "ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ)",
      "requireComment": false
    }
  ]
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| docNo | string | Yes | พ.ศ. YYYY/xxxxx |
| statusCode | string | Yes | canonical code; do not replace with display label |
| viewerRbacRoleCode | string | Yes | UTF-8; use value domain described by endpoint purpose |
| roleProfileCode | string | Yes | UTF-8; use value domain described by endpoint purpose |
| visibleSections | array<string> | Yes | JSON array; element type shown in Type column |
| editableSections | array<string> | Yes | JSON array; element type shown in Type column |
| actionOptions | array<object> | Yes | JSON array; element type shown in Type column |
| actionOptions[].label | string | Yes | UTF-8; use value domain described by endpoint purpose |
| actionOptions[].requireComment | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### POST /api/v1/documents/{docNo}/actions

ตัวอย่าง positive-path จาก section 01; Section 02 ใช้กรณียอดรวมมากกว่า 100,000 บาท

#### Request

```json
{
  "result": "เห็นควรชดเชย",
  "comment": "ส่งดำเนินการตามลำดับ"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| result | string | Yes | UTF-8; use value domain described by endpoint purpose |
| comment | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "statusCode": "02",
  "nextSection": "02",
  "message": "submitted"
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| statusCode | string | Yes | canonical code; do not replace with display label |
| nextSection | string | Yes | canonical code; do not replace with display label |
| message | string | Yes | UTF-8; use value domain described by endpoint purpose |

## 9. Processing Flow

| Step | Description |
| --- | --- |
| 1 | Load document detail |
| 2 | Apply visibleSections and editableSections |
| 3 | Render fields/actions for this role only |
| 4 | Validate popup text |
| 5 | Submit action or save allowed section |
| 6 | Reload detail/timeline/status |

## 10. Acceptance Criteria

- ไม่แสดง role switcher ใน production
- section ที่ hidden ต้องไม่ render
- section ที่ read-only ต้องไม่มี editable control
- action panel ตรงกับ actionOptions จาก API

## 11. Developer Test Checklist

| No | Test |
| --- | --- |
| 1 | เปิดด้วย roleProfileCode=P-01 แล้ว sec-newstore/sec-competitor/sec-factor ต้อง editable |
| 2 | แก้ compensatePercent แล้วรวมไม่ครบ 100 ต้อง error COMPENSATE_PERCENT_INVALID |
| 3 | เพิ่มร้านคู่แข่งโดยไม่เลือก competitor ต้อง error COMPETITOR_REQUIRED |
| 4 | เพิ่มปัจจัยอื่นโดยไม่เลือก factor ต้อง error EXTERNAL_FACTOR_REQUIRED |
| 5 | sec-calc ต้องไม่ render สำหรับ role 01 |
