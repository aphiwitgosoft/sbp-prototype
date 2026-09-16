# Error Catalog

> Contract status: `TO-BE` API/FE + `AS-BUILT` Batch · Catalog status: `Draft`

## API/FE canonical errors

| Code | HTTP/scope | เมื่อใด | ข้อความผู้ใช้ |
|---|---|---|---|
| `REPORT_STATUS_REQUIRED` | 400 | รายงานไม่เลือก status | กรุณาเลือกสถานะก่อนค้นหาข้อมูล |
| `FORBIDDEN` | 403 | ไม่มีสิทธิ์ | กรุณาติดต่อผู้ดูแลระบบ |
| `DUPLICATE_DOCUMENT` | 409 | มี active document ร้าน+งวด | ร้านนี้ในเดือนนี้มีเอกสารอยู่แล้ว |
| `CODE_DUPLICATE` | 409 | master code ซ้ำ | รหัสนี้ถูกใช้แล้ว กรุณาระบุรหัสอื่น |
| `CONFLICT` | 409 | state/resource เปลี่ยน | ข้อมูลมีการเปลี่ยนแปลง กรุณาโหลดข้อมูลล่าสุดแล้วดำเนินการใหม่ |
| `STALE_VERSION` | 409 | versionNo ไม่ตรง | ข้อมูลถูกแก้ไขโดยผู้ใช้อื่น กรุณาโหลดข้อมูลล่าสุดแล้วลองอีกครั้ง |
| `ACTION_RESULT_REQUIRED` | 422 | ไม่เลือกผล | ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ |
| `ACTION_COMMENT_REQUIRED` | 422 | comment ที่บังคับว่าง | กรุณากรอกความคิดเห็นเพิ่มเติม (บังคับกรอกสำหรับผลการพิจารณานี้) ก่อนส่งดำเนินการ |
| `COMPENSATE_PERCENT_INVALID` | 422 | ผลรวมไม่เท่ากับ 100 | โปรดตรวจสอบ %ชดเชย ของท่าน รวมกันแล้วไม่เท่ากับ 100% |
| `COMPETITOR_REQUIRED` | 422 | ไม่เลือกคู่แข่ง | กรุณาเลือกร้านคู่แข่งก่อนบันทึก |
| `EXTERNAL_FACTOR_REQUIRED` | 422 | ไม่เลือกปัจจัย | กรุณาเลือกปัจจัยอื่นก่อนบันทึก |
| `REPORT_DATE_RANGE_INVALID` | 422 | from > to | เดือนเริ่มต้นต้องไม่มากกว่าเดือนสิ้นสุด |
| `ATTACHMENT_FILE_REQUIRED` | 422 | ไม่เลือกไฟล์ | กรุณาเลือกไฟล์ที่ต้องการแนบ ก่อนกดแนบเอกสาร |
| `FILE_TOO_LARGE` | 413 | >5 MiB | ไฟล์แนบมีขนาดเกิน 5 MB |
| `FILE_TYPE_UNSUPPORTED` | 415 | type ไม่อนุญาต | ชนิดไฟล์ไม่อนุญาตให้อัปโหลด |
| `FILE_SCAN_BLOCKED` | 422 | AV blocked/failed | ไฟล์แนบไม่ผ่านการตรวจสอบความปลอดภัย |
| `FS_BRIDGE_UNAVAILABLE` | FE | iframe ไม่ ready | ไม่สามารถเชื่อมต่อแบบฟอร์ม FS ได้ กรุณาลองอีกครั้ง |
| `FS_BRIDGE_ORIGIN_INVALID` | FE | origin ไม่ผ่าน | ไม่สามารถยืนยันแหล่งที่มาของแบบฟอร์ม FS ได้ |
| `FS_PROTOCOL_VERSION_UNSUPPORTED` | FE | protocol != 1.0 | เวอร์ชันของแบบฟอร์ม FS ไม่รองรับ กรุณาติดต่อผู้ดูแลระบบ |
| `FS_BRIDGE_SCHEMA_INVALID` | FE | schema ผิด | ข้อมูลแบบฟอร์ม FS ไม่ถูกต้อง กรุณาติดต่อผู้ดูแลระบบ |
| `FS_BRIDGE_SUBMIT_FAILED` | FE | submit FS ล้ม | ส่งแบบฟอร์ม FS ไม่สำเร็จ กรุณาตรวจสอบข้อมูลแล้วลองอีกครั้ง |

BE อาจเพิ่ม `UNAUTHENTICATED` 401, `NOT_FOUND` 404, `VALIDATION_ERROR` 400/422, `INTERNAL_ERROR` 500 เมื่อสร้าง implementation แต่ต้องเพิ่ม catalog + mapping + tests ก่อนใช้

## Batch error contract

`JobRunResult.status` ที่ถือว่าสำเร็จมี `SUCCESS`, `SKIPPED`, `SKIPPED_LOCKED`; ค่าอื่นหรือ service ไม่คืนผลต้อง exit non-zero Code หลักที่ code ใช้รวม `INVALID_JOB_INPUT`, `CONFIG_INVALID`, job-specific no bucket/API/token, schema/consistency/limit errors; รายละเอียดต้องอยู่ structured log และ failure notification โดยไม่เผย secret

## Retry classification

| ชนิด | Retry | การตอบสนอง |
|---|---|---|
| validation/business reject | ไม่ retry | 4xx หรือ reject/DLQ ตาม message policy |
| optimistic conflict | client reload แล้ว retry โดย user | 409 |
| timeout/5xx/network | bounded exponential backoff | 502/503/504 หรือ Job failed |
| duplicate message/business key | acknowledge/no-op | คืน success เดิมหรือ duplicate result |
| DB constraint/data consistency | rollback, alert, ไม่วนไม่สิ้นสุด | 409/422/500 หรือ DLQ |

