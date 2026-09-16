# Test และ Delivery Checklist

> Document status: `Draft`

## ต้องทำอะไร และเสร็จแล้วได้อะไร

ใช้ checklist นี้เป็น release gate ร่วมของ FE, BFF, BE, Batch/DB และ Business หลักฐานต้องแนบ command/result/environment/commit; คำว่า “ผ่าน” โดยไม่มีหลักฐานไม่ถือว่าตรวจรับ

## Documentation gates

- [ ] `python3 tools/check_docs.py` exit 0
- [ ] `git diff --check` exit 0
- [ ] Markdown links และ Mermaid ทุก block parse ได้
- [ ] API 28 เส้น trace ถึง Feature/BFF/BE/DB/test
- [ ] DB 20 new + 1 reuse มี owner/reader/writer
- [ ] Jobs 2–12 + 8b ครบ 12 ฉบับและมี Flowchart/Sequence
- [ ] ไม่มีเอกสาร Ready ที่มี `BLOCKED`
- [ ] Decision ที่ขัดกันมี ID เดียวและ cross-link ครบ

## FE/BFF/BE gates

- [ ] route/component state/loading/empty/error/permission/responsive/a11y
- [ ] BFF cookie/session, trusted context, timeout, error/status propagation
- [ ] OpenAPI/DTO strict validation และ representative contract snapshots
- [ ] 28 endpoint tests `API-01`…`API-28`; auth 401/403, not found, conflict, validation
- [ ] action transition ทุก section/result/amount boundary 99,999.99/100,000/100,000.01
- [ ] optimistic concurrency/double submit/idempotency/outbox rollback
- [ ] attachment size/type/AV/object ownership/ZIP/no file
- [ ] report filter/14 columns/export parity/large data/formula injection

## Database/migration gates

- [ ] PostgreSQL supported version: install schema+seed from clean DB และ rollback เฉพาะ dev/UAT
- [ ] FK/UK/CHECK/index, query plan, lock/deadlock, least privilege
- [ ] Oracle/MSSQL domain/row count/duplicate/orphan reconciliation
- [ ] money/percent/leading zero/date/timezone snapshot checks
- [ ] backup/restore and forward-fix rehearsal; production rollback owner

## Batch gates

- [ ] SGI unit tests และ `__svc__` tests ผ่านบน dependency ที่รับรอง
- [ ] `npx tsc --noEmit` ไม่มี error ใต้ `src/modules/sgi/`
- [ ] `test/sgi/run-lifecycle.sh` ผ่าน; SQL PREPARE ตรวจ table/column จริง
- [ ] each Job: invalid input, dryRun, limit guard, empty input, rerun, concurrent lock, partial failure, notification failure
- [ ] S3/Rabbit/API contract tests กับ sandbox ของ IAS/STA/platform
- [ ] Job 11 duplicate/redelivery/max attempts/DLQ และ money consistency
- [ ] Job 10/12 clock/business day/timezone/escalation/no-recipient

## Operations/security gates

- [ ] secret scan, credential rotation จาก legacy, no secret/raw PII log
- [ ] AWS definitions ระบุ schedule/dependency/retry/timeout/CPU-memory/network/role
- [ ] dashboard/alarm/runbook/replay/DLQ/backlog/backup/retention
- [ ] canary/rollback/owner/contact/escalation และ maintenance window

## Sign-off

| Area | ผู้ตรวจ | หลักฐาน | สถานะ |
|---|---|---|---|
| FE | TBD | PR + screenshots/e2e | Pending |
| BFF | TBD | contract/security tests | Pending |
| BE | TBD | API/transaction tests | Pending |
| Batch/DB | TBD | unit/svc/lifecycle/migration | Pending |
| Business/External owners | TBD | rule/file/message/workflow sign-off | Pending |

