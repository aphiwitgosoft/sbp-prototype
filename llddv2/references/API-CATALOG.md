# API Catalog — SGI 28 endpoints

> Contract status: `TO-BE` · Catalog status: `Verified` against `plan-api.html` on 2026-09-15

## ต้องทำอะไร และเสร็จแล้วได้อะไร

ตารางนี้เป็นรายการ endpoint canonical เพียงชุดเดียวสำหรับนับ 28 เส้น ทุก path รวม prefix `/api/v1` แล้ว FE เรียก path เดียวกันผ่าน BFF; BFF proxy ไป Store BE โดยคง method, query/body, HTTP status และ error envelope

## Catalog และ traceability

| # | Method/path | Feature | BFF/BE owner ที่ต้องสร้าง | DB/Integration | Test ID |
|---:|---|---|---|---|---|
| 01 | `GET /api/v1/sgi/document/tasks` | F01 | `SgiDocumentController.listTasks` | workflow + documents | API-01 |
| 02 | `GET /api/v1/sgi/document` | F01 | `SgiDocumentController.search` | documents/logs/store | API-02 |
| 03 | `GET /api/v1/sgi/document/{docNo}` | F03 | `SgiDocumentController.detail` | document aggregate | API-03 |
| 04 | `POST /api/v1/sgi/document` | F02 | `SgiDocumentController.create` | documents/running/interface | API-04 |
| 05 | `PUT /api/v1/sgi/document/{docNo}` | F03 | `SgiDocumentController.update` | document children | API-05 |
| 06 | `POST /api/v1/sgi/document/{docNo}/actions` | F04 | `SgiDocumentWorkflowController.action` | logs/workflow/outbox | API-06 |
| 07 | `GET /api/v1/sgi/document/{docNo}/timeline` | F04 | `SgiDocumentWorkflowController.timeline` | logs/workflow history | API-07 |
| 08 | `POST /api/v1/sgi/document/{docNo}/attachments` | F05 | `SgiAttachmentController.upload` | attachments/S3/AV | API-08 |
| 09 | `GET /api/v1/sgi/document/{docNo}/attachments/{attachId}/download` | F05 | `SgiAttachmentController.download` | attachments/S3 | API-09 |
| 10 | `GET /api/v1/sgi/document/{docNo}/attachments/download-all` | F05 | `SgiAttachmentController.downloadAll` | attachments/S3/ZIP | API-10 |
| 11 | `GET /api/v1/sgi/document/{docNo}/sales` | F05 | `SgiSalesController.list` | sales summary/transactions | API-11 |
| 12 | `GET /api/v1/sgi/lookup/document-statuses` | F01 | `SgiLookupController.documentStatuses` | `common_code` | API-12 |
| 13 | `GET /api/v1/sgi/lookup/workflow-sections` | F01/F04 | `SgiLookupController.workflowSections` | workflow/config | API-13 |
| 14 | `GET /api/v1/sgi/master/competitors` | F06 | `SgiCompetitorController.list` | `sgi_competitors` | API-14 |
| 15 | `POST /api/v1/sgi/master/competitors` | F06 | `SgiCompetitorController.create` | `sgi_competitors` | API-15 |
| 16 | `PUT /api/v1/sgi/master/competitors/{code}` | F06 | `SgiCompetitorController.update` | `sgi_competitors` | API-16 |
| 17 | `DELETE /api/v1/sgi/master/competitors/{code}` | F06 | `SgiCompetitorController.remove` | `sgi_competitors` | API-17 |
| 18 | `GET /api/v1/sgi/master/factors` | F06 | `SgiFactorController.list` | `sgi_external_factors` | API-18 |
| 19 | `POST /api/v1/sgi/master/factors` | F06 | `SgiFactorController.create` | `sgi_external_factors` | API-19 |
| 20 | `PUT /api/v1/sgi/master/factors/{code}` | F06 | `SgiFactorController.update` | `sgi_external_factors` | API-20 |
| 21 | `DELETE /api/v1/sgi/master/factors/{code}` | F06 | `SgiFactorController.remove` | `sgi_external_factors` | API-21 |
| 22 | `GET /api/v1/sgi/report/status-summary` | F07 | `SgiReportController.statusSummary` | document aggregate/store | API-22 |
| 23 | `GET /api/v1/sgi/report/status-summary/export` | F07 | `SgiReportController.exportStatusSummary` | same query/Excel | API-23 |
| 24 | `POST /api/v1/sgi/workflow/instances` | F02/F04 | `SgiWorkflowController.initialize` | workflow engine | API-24 |
| 25 | `GET /api/v1/sgi/workflow/instances/{id}` | F02/F04 | `SgiWorkflowController.getInstance` | workflow engine | API-25 |
| 26 | `GET /api/v1/sgi/workflow/summary` | F02/F04 | `SgiWorkflowController.summary` | workflow + documents | API-26 |
| 27 | `GET /api/v1/sgi/interface/tracking` | F08 | `SgiInterfaceController.tracking` | interface transactions | API-27 |
| 28 | `GET /api/v1/sgi/interface/pending-ack` | F08 | `SgiInterfaceController.pendingConfirm` | OUT outbox only | API-28 |

## Common parameters

- list: `page`, `pageSize`, canonical sort; default/maximum ต้องประกาศใน DTO และ OpenAPI
- document search: บังคับ `year`; optional `status`, `region[]`, `storeType[]`, date/money/wait/result filters
- report: บังคับ `status`; status `99` บังคับ statement period; impacted/new store เป็นคู่
- mutation: body whitelist, audit actor จาก trusted context, `versionNo` สำหรับ document update/action
- master: `code`, `nameTh`, `nameEn` ตามชนิด; duplicate = 409

## Representative contracts

Create internal document:

```json
{"impactedStoreCode":"01234","periodYear":2026,"periodMonth":8,"source":"FS","idempotencyKey":"FS:01234:2026-08:1"}
```

Document action:

```json
{"result":"ส่งหน่วยงานส่งเสริมธุรกิจ SBP","comment":"ตรวจสอบแล้ว","versionNo":3}
```

Paged response:

```json
{"success":true,"data":{"items":[],"page":1,"pageSize":20,"total":0}}
```

รายละเอียด field/error/DB ต่อ use case อยู่ใน Feature ที่คอลัมน์ Feature ชี้ไป ห้ามเพิ่ม endpoint โดยแก้ catalog นี้อย่างเดียว: ต้องแก้ `plan-api.html`, owner feature, tests และ count rule พร้อมกัน

