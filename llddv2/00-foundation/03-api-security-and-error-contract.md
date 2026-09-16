# Foundation 03 — API, Security และ Error Contract

> Contract status: `TO-BE` · Document status: `Blocked` · Decision: D-011

## ต้องทำอะไร และเสร็จแล้วได้อะไร

FE เรียก BFF ด้วย session cookie เดิม; BFF ยืนยันตัวตนและส่ง user context ให้ Store BE; BE ตรวจ API key, menu permission, document visibility และ current task owner ก่อนทำงาน ทุก endpoint ใช้ base path `/api/v1/sgi` และ envelope เดียวกัน

## HTTP contract กลาง

Success:

```json
{"success":true,"data":{"items":[],"page":1,"pageSize":20,"total":0},"requestId":"req-123"}
```

Failure:

```json
{"success":false,"error":{"code":"STALE_VERSION","message":"ข้อมูลถูกแก้ไขโดยผู้ใช้อื่น กรุณาโหลดข้อมูลล่าสุดแล้วลองอีกครั้ง"},"requestId":"req-123"}
```

- list ใช้ `page` เริ่ม 1, `pageSize` มีเพดาน, `total` เป็นจำนวนก่อนแบ่งหน้า และ sort ต้อง deterministic
- date ใช้ ISO `YYYY-MM-DD`; timestamp ใช้ ISO-8601 พร้อม offset; เงินเป็น JSON number สองตำแหน่งตาม response contract
- unknown query/body field ต้อง reject ใน mutation และ internal API; ห้ามกลืน typo
- HTTP status/error code ใช้ [Error Catalog](../references/ERROR-CATALOG.md)

## Authentication และ authorization

| Hop | Contract |
|---|---|
| Browser → FE/BFF | Cognito/session cookie `httpOnly`, `secure`, `sameSite` ตาม environment; FE ห้ามอ่าน token |
| BFF → BE | private network + `x-api-key`; ส่ง `x-request-id` และ canonical user/group/permission context |
| Batch → BE | service token/API key แยกจาก user session; ใช้เฉพาะ endpoint internal |
| BE → Workflow | `WorkflowGateway` สร้าง `userData` จาก context ที่ผ่าน guard แล้ว |

`BLOCKED D-011`: ต้องลงนามชื่อ header จริง, ผู้สร้าง/ตรวจ signature, key rotation และวิธีป้องกัน client spoof ก่อน Ready ปัจจุบันเอกสารเดิมอ้าง `x-user-id`, `x-user-group-id`, `x-user-permissions` แต่ BE SGI ยังไม่มี implementation ให้ยืนยัน

## Role baseline

- document list/detail: participant หรือ report/admin grant
- update/action/upload: current task owner; override ต้องมี policy + audit reason
- master: menu permission `canManage`; export: `canExport`
- workflow create/interface: service identity เท่านั้น
- attachment download: สิทธิ์เอกสาร + attachment ต้องเป็นของ `docNo` + scan guard

## Concurrency และ transaction

`PUT /document/{docNo}` และ action ต้องรับ `versionNo`; update ใช้ `WHERE doc_no=? AND version_no=?`, เพิ่ม version ใน transaction และคืน 409 `STALE_VERSION` เมื่อจำนวนแถวเป็นศูนย์ Action ต้อง lock งาน/เอกสาร ป้องกัน double submit และบันทึก consideration log/outbox ใน transaction เดียวกัน ส่วน external call ทำหลัง commit ผ่าน outbox หรือ adapter ที่ชดเชยได้

## Logging และข้อมูลอ่อนไหว

log ต้องมี `requestId`, route, actorId, docNo/business key, duration, status/errorCode; ห้าม log cookie, token, API key, secret, file body, taxpayer/address/phone เต็มค่า ให้ mask ตาม PDPA และกำหนด retention กับ Security/Operations

## Acceptance

- contract test ทุก endpoint ตรวจ success/error envelope, 401/403/404/409/422 และ requestId
- BFF ไม่เปลี่ยน status/body โดยไม่ได้ประกาศ mapping
- spoof user header จาก Browser ไป BE ไม่ผ่าน
- replay action ด้วย version เดิมเกิดผลครั้งเดียว
- error message ที่ผูก SRS ต้องตรงแบบ verbatim

API ทั้งหมด: [API Catalog](../references/API-CATALOG.md) · ข้อค้าง: [Decision Register](07-decision-register.md)

