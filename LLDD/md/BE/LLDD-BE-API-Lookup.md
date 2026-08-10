# LLDD BE - API Lookup

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Overview

| รายการ | รายละเอียด |
| --- | --- |
| Track | BE |
| Estimate | 15 ชั่วโมง |
| Owner | Butsaba <But> Podamrong |
| Objective | ออกแบบ APIs กลุ่ม lookup ที่ใช้ร่วมทุกหน้าจอของ SBP Mall |

Common contract reference: ทุกหัวข้อ API/FE ต้องยึด LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts สำหรับ error/auth/format/pagination/action/RBAC ก่อนลงรายละเอียดเฉพาะหน้าหรือเฉพาะ endpoint

## 2. Screen / Functional Scope

- Lookup APIs
- Auth endpoints are platform reference only

## 4. Implementation Flow Diagram (Reference)

![รูปที่ 1: Implementation flow reference: LLDD BE - API Lookup](../../assets/flows/BE-LLDD-BE-API-Lookup.png)

_รูปที่ 1: Implementation flow reference: LLDD BE - API Lookup_

## 5. Field, Format, and Validation

| Field / UI | Format | Validation | Behavior |
| --- | --- | --- | --- |
| q | string | optional | ใช้ค้นหา stores/employees/competitors |
| type | impacted\|new | required for /store/search (ระบบ SBP เดิม) | เลือกแหล่งร้านถูกกระทบ/ร้านเปิดใหม่ |
| roleCode | 00-10 | required for permission | อ้าง roles |
| menuCode | string | required for permission | อ้าง menus |
| templateCode | EM-01..EM-08 | required | email template key |
| reason | text | ไม่บังคับแล้ว | ไม่มีปลายทางเก็บ (ยกเลิกระบบ audit ของ master 2026-08-07) |

## 5.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | GET /store/search (ระบบ SBP เดิม); GET /api/v1/document-statuses; GET /api/v1/workflow-sections |
| Progress | Validate query; Read/write table by domain; Return standard envelope for list endpoints |
| Output | roles / menus / menu_permissions; email_template (SBP) / status_email_rules |

### 5.90 Endpoint Implementation Contract

| Endpoint | Use-case owner | Service/repository behavior | Definition of done |
| --- | --- | --- | --- |
| GET /store/search (ระบบ SBP เดิม) | ค้นหาร้านสำหรับ popup | Validate query | status label ต้องเป็น verbatim |
| GET /api/v1/document-statuses | รายการสถานะเอกสาร verbatim | Read/write table by domain | permission mutation ต้อง audit |
| GET /api/v1/workflow-sections | รายการ section 5 ขั้น | Return standard envelope for list endpoints | email recipient From/To/Cc ล็อกจาก status_email_rules |
| GET /api/v1/employees/search | ค้นหาพนักงานสำหรับ master/operator | Validate query | Auth Group 1 เป็น platform/external reference ไม่ใช่งาน implement ใน LLDD นี้ |
| GET /api/v1/menu-permissions | อ่าน matrix สิทธิ์เมนูทุก role | Read/write table by domain | status label ต้องเป็น verbatim |
| PUT /api/v1/menu-permissions/{menuCode} | บันทึกสิทธิ์เมนูรายเมนู | Return standard envelope for list endpoints | permission mutation ต้อง audit |
| GET /api/v1/roles | อ่านรายการ role | Validate query | email recipient From/To/Cc ล็อกจาก status_email_rules |
| POST /api/v1/roles | สร้าง role | Read/write table by domain | Auth Group 1 เป็น platform/external reference ไม่ใช่งาน implement ใน LLDD นี้ |
| PUT /api/v1/roles/{roleCode} | แก้ role ที่ไม่ใช่ system role | Return standard envelope for list endpoints | status label ต้องเป็น verbatim |
| DELETE /api/v1/roles/{roleCode} | ลบ role ที่ไม่ถูกใช้งาน | Validate query | permission mutation ต้อง audit |
| POST /api/v1/menus | สร้างเมนูและสิทธิ์เริ่มต้นทุก role | Read/write table by domain | email recipient From/To/Cc ล็อกจาก status_email_rules |
| PUT /api/v1/menus/{menuCode} | แก้เมนู | Return standard envelope for list endpoints | Auth Group 1 เป็น platform/external reference ไม่ใช่งาน implement ใน LLDD นี้ |
| DELETE /api/v1/menus/{menuCode} | ลบเมนูพร้อมสิทธิ์ที่เกี่ยวข้อง | Validate query | status label ต้องเป็น verbatim |

### 5.91 Backend Execution Sequence

| Step | Behavior specific to this LLDD | Failure/test evidence |
| --- | --- | --- |
| 1 | Validate query | store lookup |
| 2 | Read/write table by domain | status lookup |
| 3 | Return standard envelope for list endpoints | permission save without reason |

## 6. Button / User Action Mapping

| Action | Trigger | API / Service | Expected Result |
| --- | --- | --- | --- |
| Store lookup | GET | lookup.service.searchStores | return impacted/new stores |
| Employee lookup | GET | employee.service.search | return employees for operator popup |
| Permission save | PUT | rbac.service.saveMenuPermission | update can_access and audit |
| Email template save/reset | PUT/POST | notificationTemplate.service | update/reset template and audit |

## 7. API Contract

### GET /store/search (ระบบ SBP เดิม)

ค้นหาร้านสำหรับ popup

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
      "storeName": "รัตนอุทิศ ซ.13"
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

### GET /api/v1/document-statuses

รายการสถานะเอกสาร verbatim

#### Query Params

```json
{}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| - | none | No | No fields |

#### Response

```json
{
  "items": [
    {
      "statusCode": "06",
      "statusName": "รอฝ่าย SBP DSA ดำเนินการ"
    }
  ]
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| items | array<object> | Yes | JSON array; element type shown in Type column |
| items[].statusCode | string | Yes | canonical code; do not replace with display label |
| items[].statusName | string | Yes | UTF-8; use value domain described by endpoint purpose |

### GET /api/v1/workflow-sections

รายการ section 5 ขั้น

#### Query Params

```json
{}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| - | none | No | No fields |

#### Response

```json
{
  "items": [
    {
      "sectionCode": "06",
      "sectionName": "ฝ่าย SBP DSA"
    }
  ]
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| items | array<object> | Yes | JSON array; element type shown in Type column |
| items[].sectionCode | string | Yes | canonical code; do not replace with display label |
| items[].sectionName | string | Yes | UTF-8; use value domain described by endpoint purpose |

### GET /api/v1/employees/search

ค้นหาพนักงานสำหรับ master/operator

#### Query Params

```json
{
  "q": "สมชาย"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| q | string | No | UTF-8; use value domain described by endpoint purpose |

#### Response

```json
{
  "items": [
    {
      "employeeId": "E001",
      "employeeName": "สมชาย ใจดี"
    }
  ]
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| items | array<object> | Yes | JSON array; element type shown in Type column |
| items[].employeeId | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].employeeName | string | Yes | UTF-8; use value domain described by endpoint purpose |

### GET /api/v1/menu-permissions

อ่าน matrix สิทธิ์เมนูทุก role

#### Query Params

```json
{
  "roleCode": "04"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| roleCode | string | No | canonical code; do not replace with display label |

#### Response

```json
{
  "items": [
    {
      "menuCode": "k2-report",
      "roleCode": "04",
      "canAccess": true
    }
  ]
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| items | array<object> | Yes | JSON array; element type shown in Type column |
| items[].menuCode | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].roleCode | string | Yes | canonical code; do not replace with display label |
| items[].canAccess | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### PUT /api/v1/menu-permissions/{menuCode}

บันทึกสิทธิ์เมนูรายเมนู

#### Request

```json
{
  "roleCode": "04",
  "canAccess": true,
  "reason": "ปรับสิทธิ์รายงาน"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| roleCode | string | Yes | canonical code; do not replace with display label |
| canAccess | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| reason | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "message": "saved"
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| message | string | Yes | UTF-8; use value domain described by endpoint purpose |

### GET /api/v1/roles

อ่านรายการ role

#### Query Params

```json
{
  "page": 1,
  "size": 20
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| page | integer | No | >= 1; default 1 |
| size | integer | No | 1..100; default 20 |

#### Response

```json
{
  "page": 1,
  "size": 20,
  "total": 11,
  "items": [
    {
      "roleCode": "04",
      "roleName": "ผู้ดูแลระบบ",
      "system": true,
      "active": true
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
| items | array<object> | Yes | JSON array; element type shown in Type column |
| items[].roleCode | string | Yes | canonical code; do not replace with display label |
| items[].roleName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].system | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| items[].active | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### POST /api/v1/roles

สร้าง role

#### Request

```json
{
  "roleCode": "11",
  "roleName": "ผู้ตรวจสอบ",
  "active": true,
  "reason": "เพิ่มบทบาทผู้ตรวจสอบ"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| roleCode | string | Yes | canonical code; do not replace with display label |
| roleName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| active | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| reason | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "roleCode": "11",
  "roleName": "ผู้ตรวจสอบ",
  "system": false,
  "active": true
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| roleCode | string | Yes | canonical code; do not replace with display label |
| roleName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| system | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| active | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### PUT /api/v1/roles/{roleCode}

แก้ role ที่ไม่ใช่ system role

#### Request

```json
{
  "roleName": "ผู้ตรวจสอบอาวุโส",
  "active": true,
  "reason": "ปรับชื่อบทบาท"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| roleName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| active | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| reason | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "roleCode": "11",
  "roleName": "ผู้ตรวจสอบอาวุโส",
  "system": false,
  "active": true
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| roleCode | string | Yes | canonical code; do not replace with display label |
| roleName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| system | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| active | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### DELETE /api/v1/roles/{roleCode}

ลบ role ที่ไม่ถูกใช้งาน

#### Request

```json
{
  "reason": "ยกเลิกบทบาททดสอบ"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| reason | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "roleCode": "11",
  "deleted": true
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| roleCode | string | Yes | canonical code; do not replace with display label |
| deleted | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### POST /api/v1/menus

สร้างเมนูและสิทธิ์เริ่มต้นทุก role

#### Request

```json
{
  "menuCode": "k2-audit",
  "menuName": "ประวัติการแก้ไข",
  "route": "/audit",
  "sortOrder": 90,
  "active": true,
  "reason": "เพิ่มเมนูตรวจสอบ"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| menuCode | string | Yes | UTF-8; use value domain described by endpoint purpose |
| menuName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| route | string | Yes | UTF-8; use value domain described by endpoint purpose |
| sortOrder | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| active | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| reason | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "menuCode": "k2-audit",
  "created": true
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| menuCode | string | Yes | UTF-8; use value domain described by endpoint purpose |
| created | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### PUT /api/v1/menus/{menuCode}

แก้เมนู

#### Request

```json
{
  "menuName": "ประวัติการแก้ไขข้อมูล",
  "route": "/audit",
  "sortOrder": 90,
  "active": true,
  "reason": "ปรับชื่อเมนู"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| menuName | string | Yes | UTF-8; use value domain described by endpoint purpose |
| route | string | Yes | UTF-8; use value domain described by endpoint purpose |
| sortOrder | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| active | boolean | Yes | UTF-8; use value domain described by endpoint purpose |
| reason | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "menuCode": "k2-audit",
  "updated": true
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| menuCode | string | Yes | UTF-8; use value domain described by endpoint purpose |
| updated | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

### DELETE /api/v1/menus/{menuCode}

ลบเมนูพร้อมสิทธิ์ที่เกี่ยวข้อง

#### Request

```json
{
  "reason": "ยกเลิกเมนูทดสอบ"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| reason | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "menuCode": "k2-audit",
  "deleted": true
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| menuCode | string | Yes | UTF-8; use value domain described by endpoint purpose |
| deleted | boolean | Yes | UTF-8; use value domain described by endpoint purpose |

## 8. Reference DB Mapping (No Database Page Work)

ส่วนนี้เป็นข้อมูลอ้างอิงสำหรับการ implement API/Job เท่านั้น ไม่ใช่งานสร้างหน้า Database, ไม่ใช่งานออกแบบ DB page และไม่ถูกนับเป็น deliverable แยกของ FE/BE

| Table / Object | R/W | Usage |
| --- | --- | --- |
| stores / impacted_stores | R | store picker สำหรับร้านถูกกระทบ/ร้านเปิดใหม่ |
| document_statuses / workflow_sections | R | lookup สถานะ verbatim และ section 5 ขั้น |
| employees | R | popup ค้นหาพนักงาน |
| roles / menus / menu_permissions | R/W | RBAC/menu matrix |
| email_template (SBP) / status_email_rules | R/W | เนื้อหา template ในตารางของระบบ SBP เดิม และผู้รับที่ล็อกตามสถานะ |

## 9. Skeleton Code (store-backend + BFF)

โครงโค้ดตั้งต้นของเอกสารฉบับนี้ ยึด convention จริงของ `srm-sps-spsap-store-backend` (NestJS 11 + TypeORM, schema `sps_store`, custom provider `DATA_SOURCE` ที่ route SELECT ไป slave pool) และ `srm-sps-spsap-sbp-bff` (ไม่มี DB, forward ผ่าน client service). ทุกจุดที่ต้องเติมกำกับด้วย `// TODO:` และ response ทุกเส้นถูกห่อเป็น `{success, data}` โดย ResponseInterceptor อยู่แล้ว จึงห้าม service ห่อซ้ำ

#### 9.1 ผังไฟล์ที่ต้องสร้าง

| Path | หน้าที่ |
| --- | --- |
| store-backend · src/modules/sbpgi-lookup/sbpgi-lookup.controller.ts | route ทั้งหมดของเอกสารนี้ (2 เส้น) + `@UseGuards(HttpHeaderGuard)` + `@UserId()` |
| store-backend · src/modules/sbpgi-lookup/sbpgi-lookup.service.ts | business logic — inject `'DATA_SOURCE'` แล้วยิง raw SQL, mutation ใช้ QueryRunner transaction |
| store-backend · src/modules/sbpgi-lookup/sbpgi-lookup.sql.ts | เก็บ SQL ต่อ endpoint (คัดจากหัวข้อ 10) แยกออกจาก service ให้ทดสอบ/รีวิวง่าย |
| store-backend · src/modules/sbpgi-lookup/dto/sbpgi-lookup.dto.ts | DTO + class-validator ตาม validation ในหัวข้อฟิลด์ของเอกสารนี้ |
| store-backend · src/modules/sbpgi-lookup/sbpgi-lookup.module.ts | ประกอบ controller/service/providers แล้ว register ที่ `app.module.ts` |
| store-backend · src/entitys/impacted-stores.entity.ts | entity ของ `impacted_stores` (`@Entity({schema: process.env.DB_SCHEMA})`, ไม่ประกาศ relation) |
| store-backend · src/entitys/status-email-rules.entity.ts | entity ของ `status_email_rules` (`@Entity({schema: process.env.DB_SCHEMA})`, ไม่ประกาศ relation) |
| store-backend · src/providers/sbpgi/sbpgi.ts | repository provider แบบ factory ผูก token string กับ `DATA_SOURCE` — **ไฟล์ร่วมของทุกเอกสาร BE ให้ merge array เพิ่ม ห้ามเขียนทับ** |
| store-backend · sql/deploy-sbpgi-lookup.sql | DDL production แบบ idempotent (ทีมนี้ไม่ใช้ migration เป็นหลัก) |
| BFF · src/common/client-services/sbpgi-client.service.ts | client ต่อจาก `BaseClientService` ตั้ง baseUrl + `x-api-key` ตอน `onModuleInit` |
| BFF · src/modules/sbpgi-lookup/sbpgi-lookup.controller.ts | route ฝั่ง BFF prefix `/bff/sbpgi/…` + `@UseGuards(AuthGuard('jwt'))` |
| BFF · src/modules/sbpgi-lookup/sbpgi-lookup.service.ts | แนบ `x-user-id` / `x-user-group-id` / `x-user-permissions` แล้ว forward ไป backend |

เส้นที่ไม่ต้อง implement ใหม่ในเอกสารนี้:

| Endpoint | จุดประสงค์ | เหตุผล |
| --- | --- | --- |
| GET /store/search (ระบบ SBP เดิม) | ค้นหาร้านสำหรับ popup | endpoint ของระบบ SBP เดิม — เรียกใช้ ไม่ต้อง implement ใหม่ |
| GET /api/v1/employees/search | ค้นหาพนักงานสำหรับ master/operator | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ employee backend เดิมของระบบ SBP |
| GET /api/v1/menu-permissions | อ่าน matrix สิทธิ์เมนูทุก role | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend /groups/{id}/permissions |
| PUT /api/v1/menu-permissions/{menuCode} | บันทึกสิทธิ์เมนูรายเมนู | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend /groups/{id}/permissions |
| GET /api/v1/roles | อ่านรายการ role | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend groups |
| POST /api/v1/roles | สร้าง role | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend groups |
| PUT /api/v1/roles/{roleCode} | แก้ role ที่ไม่ใช่ system role | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend groups |
| DELETE /api/v1/roles/{roleCode} | ลบ role ที่ไม่ถูกใช้งาน | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend groups |
| POST /api/v1/menus | สร้างเมนูและสิทธิ์เริ่มต้นทุก role | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend menus |
| PUT /api/v1/menus/{menuCode} | แก้เมนู | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend menus |
| DELETE /api/v1/menus/{menuCode} | ลบเมนูพร้อมสิทธิ์ที่เกี่ยวข้อง | **ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ auth-backend menus |

#### 9.2 Controller (store-backend)

```ts
// src/modules/sbpgi-lookup/sbpgi-lookup.controller.ts
import { Controller, Get, UseGuards } from '@nestjs/common';
import { HttpHeaderGuard } from '../../guards/http-header.guard';
import { UserId } from '../../common/decorators/user-id.decorator';
import { SbpgiLookupService } from './sbpgi-lookup.service';

// LLDD BE - API Lookup
// BFF เรียกด้วย x-api-key และแนบ x-user-id / x-user-group-id / x-user-permissions มาให้
@Controller('sbpgi')
@UseGuards(HttpHeaderGuard)
export class SbpgiLookupController {
  constructor(private readonly service: SbpgiLookupService) {}

  // GET /api/v1/document-statuses — รายการสถานะเอกสาร verbatim
  @Get('document-statuses')
  getDocumentStatuses(@UserId() userId: string) {
    // TODO: ตรวจ x-user-permissions ก่อนเรียก service ถ้า endpoint นี้จำกัดสิทธิ์เมนู
    return this.service.getDocumentStatuses(userId);
  }

  // GET /api/v1/workflow-sections — รายการ section 5 ขั้น
  @Get('workflow-sections')
  getWorkflowSections(@UserId() userId: string) {
    // TODO: ตรวจ x-user-permissions ก่อนเรียก service ถ้า endpoint นี้จำกัดสิทธิ์เมนู
    return this.service.getWorkflowSections(userId);
  }
}
```

#### 9.3 DTO + Validation

```ts
// src/modules/sbpgi-lookup/dto/sbpgi-lookup.dto.ts
import { Type } from 'class-transformer';
import {
  IsArray, IsBoolean, IsIn, IsInt, IsNotEmpty, IsNumber, IsObject, IsOptional,
  IsString, Matches, Max, MaxLength, Min,
} from 'class-validator';

// ValidationPipe ระดับ global ตั้ง whitelist + forbidNonWhitelisted + transform ไว้แล้ว (main.ts)
// property ที่ไม่ประกาศที่นี่จะถูก reject เป็น 400 อัตโนมัติ

// payload ของโมดูลนี้
export class LookupRequestDto {
  // TODO: endpoint นี้ไม่มี body/query ใน LLDD — เพิ่ม property เมื่อสรุป payload แล้ว
}
```

#### 9.4 Service (inject `DATA_SOURCE` + raw SQL)

service ประกาศ method ครบทุกเส้นที่ controller เรียก และ **signature มาจากแหล่งเดียวกับ controller** (จำนวน/ลำดับพารามิเตอร์จึงตรงกันเสมอ) — เส้นที่ยังไม่ได้ implement เป็น stub ที่ `throw new NotImplementedException(...)` ให้ TypeScript compile ผ่านตั้งแต่วันแรก

```ts
// src/modules/sbpgi-lookup/sbpgi-lookup.service.ts
import { Inject, Injectable, Logger, NotFoundException, NotImplementedException } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { WorkflowService } from '../workflow/workflow.service';
import { SBPGI_SQL } from './sbpgi-lookup.sql';

@Injectable()
export class SbpgiLookupService {
  private readonly logger = new Logger(SbpgiLookupService.name);
  // versionId ของ workflow ประกันรายได้ (ตั้งใน env เหมือน COOPERATION_WORKFLOW_VERSION_ID)
  private readonly versionId = Number(process.env.SBPGI_WORKFLOW_VERSION_ID);

  constructor(
    // DATA_SOURCE override query(): SELECT/WITH ไป slave pool, write ไป master
    @Inject('DATA_SOURCE') private readonly dataSource: DataSource,
    private readonly workflow: WorkflowService,
  ) {}

  // GET /api/v1/document-statuses — รายการสถานะเอกสาร verbatim
  async getDocumentStatuses(userId: string) {
    const page = 1;
    const size = 100; // endpoint นี้ไม่มี query param — ไม่แบ่งหน้า
    // SQL เต็มอยู่ในหัวข้อ Database SQL ของเอกสารนี้ (คีย์ 'GET /api/v1/document-statuses')
    // ⚠️ SQL ตัวอย่างบางเส้นเขียนด้วย named parameter (:size/:offset) แต่ dataSource.query()
    //    รับเฉพาะ positional $1..$n — ต้องแปลงชื่อเป็นลำดับก่อน หรือใช้ QueryBuilder แทน
    const rows = await this.dataSource.query(SBPGI_SQL.getDocumentStatuses, [
      // TODO: เรียงพารามิเตอร์ให้ตรงกับ $1..$n ของ SQL จริง
      userId, (page - 1) * size, size,
    ]);
    // TODO: total ต้องมาจาก COUNT(*) แยก query หรือ window function ไม่ใช่ rows.length
    return { page, size, total: rows.length, items: rows };
  }

  // GET /api/v1/workflow-sections — รายการ section 5 ขั้น
  async getWorkflowSections(userId: string) {
    // TODO: implement ตาม business rule ของ GET /api/v1/workflow-sections
    //       (SQL อยู่ในหัวข้อ Database SQL คีย์ 'GET /api/v1/workflow-sections')
    throw new NotImplementedException('getWorkflowSections ยังไม่ implement');
  }
}
```

#### 9.5 Workflow (`@srm/glb-workflow`)

⚠️ **ชื่อ function ของ engine ยังไม่ยืนยัน (บันทึก 2026-08-07)** — แหล่งอ้างอิง 3 แหล่งให้ชื่อไม่ตรงกัน ชุด A `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` ชีต Detail = `eventWorkflow` · `addPreApprover` · `getPendingFlowByUser` · ชุด B ชีต `Mermaid seq` ของไฟล์เดียวกัน = `triggerEvent` · ชุด C `SBP/srm-sps-spsap-store-backend.md` §1.5 = `TriggerEventUseCase` · `AddPreparedApproverUseCase` · `GetPendingFlowUseCase` · ชื่อที่ใช้ใน skeleton ด้านล่างเป็น **ชื่อชั่วคราว** ต้องยืนยันกับทีมเจ้าของ library ก่อนเขียนโค้ดจริง (ดู `LLDD-BE-Workflow-Engine-Definition` หัวข้อ 5.3) · engine มี **13 ตาราง** อยู่ใน schema **`sps_store`** (ไม่ใช่ 10 ตาราง และไม่ใช่ `sps_auth`)

| Endpoint | Use case ที่ต้องเรียก | เหตุผล |
| --- | --- | --- |
| (อ่านสถานะประกอบ) | getTransaction() | อ่านสถานะปัจจุบันของเอกสารเพื่อประกอบ response |

```ts
// src/modules/sbpgi-lookup/sbpgi-lookup.workflow.ts (หรือรวมไว้ใน service เดียวกัน)
// WorkflowService = wrapper ของ @srm/glb-workflow ที่ store-backend มีอยู่แล้ว
// (DataSource แยกชื่อ 'workflow-connection', ทุก use case ห่อด้วย TypeOrmUnitOfWork)

  // สถานะปัจจุบันของเอกสาร
  const trx = await this.workflow.getTransaction({ versionId: this.versionId, referenceId: docNo });
  // TODO: map currentState -> statusCode/statusName ที่ FE ใช้
```

#### 9.6 Entity (TypeORM)

```ts
// src/entitys/impacted-stores.entity.ts
import { Column, Entity, PrimaryColumn } from 'typeorm';

@Entity({ name: 'impacted_stores', schema: process.env.DB_SCHEMA })
export class ImpactedStore {
  @PrimaryColumn({ name: 'store_code', type: 'char', length: 5 })
  storeCode: string;

  @Column({ name: 'store_name', type: 'varchar', length: 200 })
  storeName: string;

  @Column({ name: 'zone_code', type: 'varchar', length: 10, nullable: true })
  zoneCode?: string;

  @Column({ name: 'region_code', type: 'varchar', length: 10, nullable: true })
  regionCode?: string;

  @Column({ name: 'store_type', type: 'varchar', length: 5, nullable: true })
  storeType?: string;

  @Column({ name: 'transfer_sbp_date', type: 'date', nullable: true })
  transferSbpDate?: Date;

  @Column({ name: 'is_active', type: 'boolean', default: true })
  isActive: boolean;

  // TODO: ตรวจความยาว/precision กับ DDL จริงใน sql/deploy-sbpgi-*.sql ก่อน merge
  //       entity ชุดนี้ไม่ประกาศ relation ตาม convention (join ด้วย raw SQL)
}
```

```ts
// src/entitys/status-email-rules.entity.ts
import { Column, Entity, PrimaryColumn } from 'typeorm';

@Entity({ name: 'status_email_rules', schema: process.env.DB_SCHEMA })
export class StatusEmailRule {
  @PrimaryColumn({ name: 'status_code', type: 'varchar', length: 2 })
  statusCode: string;

  @Column({ name: 'to_section_code', type: 'varchar', length: 2, nullable: true })
  toSectionCode?: string;

  @Column({ name: 'cc_section_code', type: 'varchar', length: 2, nullable: true })
  ccSectionCode?: string;

  @Column({ name: 'template_code', type: 'varchar', length: 10 })
  templateCode: string;

  @Column({ name: 'is_active', type: 'boolean', default: true })
  isActive: boolean;

  // TODO: ตรวจความยาว/precision กับ DDL จริงใน sql/deploy-sbpgi-*.sql ก่อน merge
  //       entity ชุดนี้ไม่ประกาศ relation ตาม convention (join ด้วย raw SQL)
}
```

ตารางที่ **ไม่ต้องสร้าง entity** เพราะใช้ของระบบเดิม/workflow engine:

| Object | R/W | ใช้ของระบบเดิมตัวไหน |
| --- | --- | --- |
| stores | R | store / mas_store / sevenshop (store-backend) |
| document_statuses | R | workflow_status (@srm/glb-workflow) |
| workflow_sections | R | workflow_state (@srm/glb-workflow) |
| employees | R | business_user (store-backend) |
| roles | R/W | auth-backend groups |
| menus | R/W | auth-backend menus |
| menu_permissions | R/W | auth-backend permissions ต่อ URL |
| email_template | R/W | email_template + email_sent + @gosoft-sbp/email-lib |

#### 9.7 Repository Providers + Module wiring

```ts
// src/providers/sbpgi/sbpgi.ts — repository provider แบบ factory (ไม่ใช้ TypeOrmModule.forFeature)
// convention ของโฟลเดอร์ providers คือ 1 ไฟล์ต่อโดเมน ตั้งชื่อตามโดเมน (business_user/business_user.ts,
// common_code/common_code.ts …) ไม่ใช่ index.ts
//
// ⚠️ ไฟล์นี้ใช้ร่วมกันทุกเอกสาร BE ของ SBPGI — ให้ **merge array เพิ่ม** เข้าไฟล์เดิม ห้ามเขียนทับ
//    (ชื่อ const แยกต่อเอกสารไว้แล้วเพื่อไม่ให้ชนกัน)
import { DataSource } from 'typeorm';
import { ImpactedStore } from '../../entitys/impacted-stores.entity';
import { StatusEmailRule } from '../../entitys/status-email-rules.entity';

export const sbpgiLookupProviders = [
  {
    provide: 'IMPACTED_STORE_REPOSITORY',
    useFactory: (dataSource: DataSource) => dataSource.getRepository(ImpactedStore),
    inject: ['DATA_SOURCE'],
  },
  {
    provide: 'STATUS_EMAIL_RULE_REPOSITORY',
    useFactory: (dataSource: DataSource) => dataSource.getRepository(StatusEmailRule),
    inject: ['DATA_SOURCE'],
  },
];

// src/modules/sbpgi-lookup/sbpgi-lookup.module.ts
import { MiddlewareConsumer, Module, NestModule } from '@nestjs/common';
import { DatabaseModule } from '../../database/database.module';
// UserContextMiddleware อ่าน header x-user-id แล้วเซ็ต request.userId ที่ @UserId() ใช้
// — app.module.ts **ไม่ได้** apply แบบ global (มีแค่ HttpContext/LoggerContext) แต่ละโมดูลต้อง apply เอง
// (ดู evaluation-process.module.ts / inform-evaluate.module.ts / cooperation-request.module.ts)
import { UserContextMiddleware } from '../../common/middleware/user-context.middleware';
import { WorkflowModule } from '../workflow/workflow.module';
import { sbpgiLookupProviders } from '../../providers/sbpgi/sbpgi';
import { SbpgiLookupController } from './sbpgi-lookup.controller';
import { SbpgiLookupService } from './sbpgi-lookup.service';

@Module({
  imports: [DatabaseModule, WorkflowModule],
  controllers: [SbpgiLookupController],
  providers: [SbpgiLookupService, ...sbpgiLookupProviders],
  exports: [SbpgiLookupService],
})
export class SbpgiLookupModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    // ถ้าไม่ apply ตรงนี้ userId จะเป็น undefined เงียบ ๆ ทุก endpoint
    consumer.apply(UserContextMiddleware).forRoutes(SbpgiLookupController);
  }
}
// TODO: register module นี้ใน app.module.ts (imports) พร้อมกับโมดูล SBPGI ตัวอื่น
```

#### 9.8 BFF Proxy (module + controller + client service)

BFF ยังไม่มีฟีเจอร์ประกันรายได้เลย จึงต้องสร้าง module ใหม่ + client service ใหม่ทั้งชุด และเลือก prefix แบบเดียวทั้งโมดูล (ที่นี่ใช้ `/bff/sbpgi/…`) เพื่อไม่ให้ปนแบบที่มี/ไม่มี `/bff` เหมือนโมดูลเดิม

```ts
// src/common/client-services/sbpgi-client.service.ts
import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { BaseClientService } from './base-client.service';

@Injectable()
export class SbpgiClientService extends BaseClientService implements OnModuleInit {
  protected logger: Logger = new Logger(SbpgiClientService.name);

  onModuleInit() {
    // TODO: ถ้า deploy SBPGI แยก service ให้เพิ่ม API_SBPGI_BACKEND_* ใน AppConfigService
    //       ตอนนี้ชี้ store backend ตัวเดียวกับ StoreClientService
    this.defaultHeaders[this.config.api.store.key.name] = this.config.api.store.key.value;
    this.baseUrl = this.config.api.store.url;
  }
}
// BaseClientService แกะ { success, data } ให้แล้ว — service ฝั่ง BFF จึงได้ data ตรง ๆ
// TODO: เพิ่ม SbpgiClientService ใน providers/exports ของ ClientServiceModule (@Global)
```

```ts
// src/modules/sbpgi-lookup/sbpgi-lookup.service.ts (BFF)
import { Injectable } from '@nestjs/common';
import { SbpgiClientService } from '@common/client-services/sbpgi-client.service';

@Injectable()
export class SbpgiLookupBffService {
  constructor(private readonly client: SbpgiClientService) {}

  // BFF ไม่มี DB — หน้าที่เดียวคือแนบ user context แล้ว forward
  private userHeaders(user: any) {
    return {
      'x-user-id': user?.userId,
      'x-user-group-id': user?.groupId,
      'x-user-permissions': (user?.permissions ?? []).join(','),
    };
  }

  getDocumentStatuses(params: any, user: any) {
    return this.client.get('/api/v1/document-statuses', { params, headers: this.userHeaders(user) });
  }

  getWorkflowSections(params: any, user: any) {
    return this.client.get('/api/v1/workflow-sections', { params, headers: this.userHeaders(user) });
  }
}

// ---------- src/modules/sbpgi-lookup/sbpgi-lookup.controller.ts (BFF) ----------
import { Body, Controller, Delete, Get, Param, Post, Put, Query, Req, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

// เลือก prefix แบบเดียวทั้งโมดูล: ใช้ '/bff/sbpgi/...' (ห้ามปนกับแบบไม่มี /bff)
@Controller('bff/sbpgi/lookup')
@UseGuards(AuthGuard('jwt'))
export class SbpgiLookupBffController {
  constructor(private readonly service: SbpgiLookupBffService) {}

  // proxy ของ GET /api/v1/document-statuses
  @Get('document-statuses')
  getDocumentStatuses(@Query() query: any, @Req() req: any) {
    return this.service.getDocumentStatuses(query, req.user);
  }

  // proxy ของ GET /api/v1/workflow-sections
  @Get('workflow-sections')
  getWorkflowSections(@Query() query: any, @Req() req: any) {
    return this.service.getWorkflowSections(query, req.user);
  }
}
// TODO: register module ใน app.module.ts ของ BFF และเพิ่ม SbpgiClientService ใน ClientServiceModule (@Global)
```

## 10. Database SQL

#### 10.1 ตารางที่อ่าน/เขียน

| Table / Object | R/W | Usage |
| --- | --- | --- |
| impacted_stores | R | store picker สำหรับร้านถูกกระทบ/ร้านเปิดใหม่ |
| status_email_rules | R/W | เนื้อหา template ในตารางของระบบ SBP เดิม และผู้รับที่ล็อกตามสถานะ |
| stores | R | ใช้ของระบบเดิม: store / mas_store / sevenshop (store-backend) |
| document_statuses | R | ใช้ของระบบเดิม: workflow_status (@srm/glb-workflow) |
| workflow_sections | R | ใช้ของระบบเดิม: workflow_state (@srm/glb-workflow) |
| employees | R | ใช้ของระบบเดิม: business_user (store-backend) |
| roles | R/W | ใช้ของระบบเดิม: auth-backend groups |
| menus | R/W | ใช้ของระบบเดิม: auth-backend menus |
| menu_permissions | R/W | ใช้ของระบบเดิม: auth-backend permissions ต่อ URL |
| email_template | R/W | ใช้ของระบบเดิม: email_template + email_sent + @gosoft-sbp/email-lib |

#### 10.2 SQL จริงต่อ Endpoint

**GET /api/v1/document-statuses** — รายการสถานะเอกสาร verbatim

```sql
-- ⚠️ SQL นี้ใช้ named parameter (:name) แต่ `dataSource.query()` ของ store-backend
--    รับเฉพาะ positional $1..$n — ต้องแปลงเป็นลำดับ หรือรันผ่าน QueryBuilder
-- ตาราง document_statuses ของ SBPGI ถูกตัดแล้ว — อ่านจาก workflow_status ของ engine กลาง
SELECT status_id AS status_code, status_name, seq AS sort_order
FROM sps_store.workflow_status
WHERE version_id = :sbpgiVersionId
ORDER BY seq;
```

**GET /api/v1/workflow-sections** — รายการ section 5 ขั้น

```sql
-- ⚠️ SQL ตัวอย่างนี้ยังอ้างตารางที่ถูกตัดจาก target design 21 ตารางแล้ว
--    ห้าม implement ตามตัวอักษร ให้แทนที่ก่อนใช้งาน:
--      workflow_sections  ->  workflow_state / route (@srm/glb-workflow)
-- approve_limit_amount = SectionLimitCost ของ K2 เดิม (GM 50,000 / AVP 300,000 · SDD GI) — วงเงินเป็น data ไม่ hardcode
SELECT section_code, section_name, sort_order, approve_limit_amount
FROM workflow_sections
ORDER BY sort_order;
```

#### 10.3 Index / Constraint ที่ควรมี (ข้อเสนอ)

ยังไม่มีข้อมูลเงื่อนไข query พอจะเสนอ index — รอ SQL ต่อ endpoint ครบก่อน

## 11. Processing Flow

| Step | Description |
| --- | --- |
| 1 | Validate query |
| 2 | Read/write table by domain |
| 3 | Return standard envelope for list endpoints |

## 12. Acceptance Criteria

- status label ต้องเป็น verbatim
- permission mutation ต้อง audit
- email recipient From/To/Cc ล็อกจาก status_email_rules
- Auth Group 1 เป็น platform/external reference ไม่ใช่งาน implement ใน LLDD นี้

## 13. Developer Test Checklist

| No | Test |
| --- | --- |
| 1 | store lookup |
| 2 | status lookup |
| 3 | permission save without reason |
| 4 | email template reset |
| 5 | (ตัดออก) audit log search |
