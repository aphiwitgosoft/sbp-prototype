# TSM-SRM-LLDD SBP workflow 1.2 — เอกสารสรุป

> สรุปจากไฟล์ `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` (1.4 MB · 14 ชีต · ตรวจ 2026-08-07)
> เอกสารนี้เป็น **LLDD ของ workflow engine กลาง** ที่ทุกระบบใน SBP platform import ไปใช้ —
> คือตัวเดียวกับ library `@srm/glb-workflow` ที่ `SBP/srm-sps-spsap-store-backend.md` §1.5 อ้างถึง
> **ระบบประกันรายได้ (SBPGI) ต้องใช้ engine ตัวนี้** ตามมติ 2026-08-06 ที่ตัดตาราง workflow ของตัวเองทิ้งทั้งหมด

---

## 1. เอกสารนี้คืออะไร

| หัวข้อ | เนื้อหา |
|---|---|
| **วัตถุประสงค์** | "สำหรับใช้เป็น lib กลางให้ module อื่น ๆ import เพื่อใช้งาน จัดการเกี่ยวกับ workflow" |
| **ขอบเขต** | อธิบาย function การทำงานในส่วนของ lib workflow (ไม่ใช่ของระบบใดระบบหนึ่ง) |
| **ผู้จัดทำ** | Sukol K. · ผู้ทบทวน Sudtida J. |

### ประวัติเวอร์ชัน

| Version | วันที่ | รายละเอียด |
|---|---|---|
| 1.0 | 14/07/2025 | Initial Document |
| 1.1 | 22/10/2025 | ปรับเพิ่ม transaction ใน sequence diagram · เพิ่มการจัดการ display หน้าจอ |
| **1.2** | **29/04/2026** | **ปรับแก้ trigger event เพิ่มเงื่อนไขการระบุการอนุมัติเป็น user** |

### โครงสร้างชีต 14 ชีต

| ชีต | เนื้อหา |
|---|---|
| `Document Version History` · `Introduction` | หัวเอกสาร |
| `Detail` | สารบัญ 8 function + โครงสร้างโฟลเดอร์ของ lib |
| `1`–`8` | รายละเอียดทีละ function (input / logic / output) |
| `sample data` | **สคีมา 13 ตาราง + entity TypeORM + ข้อมูลตัวอย่าง + คู่มือ config** ← ชีตสำคัญที่สุด |
| `Mermaid seq` | sequence diagram 2 ฉบับ (ฉบับเก่า + ฉบับที่มี commit/rollback) |
| `temp` | **ชีตร่างทิ้ง** — มี entity ที่ไม่ได้ใช้จริง (`workflow_approver_role`, `workflow_template`) และ Prisma model ปนอยู่ · **อย่ายึดชีตนี้** |

---

## 2. โครงสร้างโค้ดของ lib

```
src/
├── app.module.ts
├── main.ts
└── workflow/
    ├── interfaces/   workflow.interface.ts · workflow-event.dto.ts
    ├── entities/     workflow-transaction · workflow-history · workflow-route
    │                 workflow-state · workflow-version
    ├── services/     workflow.service.ts      ← logic หลักทั้งหมด
    ├── providers/    workflow.repository.ts   ← เชื่อม DB ผ่าน TypeORM
    ├── workflow.module.ts
    └── index.ts
```

---

## 3. Function ทั้ง 8 ตัว

| # | Function | ทำอะไร | Input |
|---|---|---|---|
| 1 | `initializeWorkflow` | สร้าง workflow ตั้งต้น | `versionId`, `userId`, `referenceId` |
| 2 | `eventWorkflow` | ดำเนินการ action (submit / approve / reject …) | `versionId`, `referenceId`, `event`, `eventParam`, `remark`, `userData`, `userFullname`, `nextApproverId` |
| 3 | `getPermissionEvents` | ดึง event ที่ user คนนั้นทำได้ **+ ข้อมูลการแสดงผลหน้าจอ** | `versionId`, `referenceId`, `userData` |
| 4 | `getHistory` | ดึงประวัติของ workflow | `versionId`, `referenceId` |
| 5 | `getTransaction` | ดึงสถานะปัจจุบัน | `versionId`, `referenceId` |
| 6 | `getPendingFlowByUser` | งานที่รอ user คนนั้นดำเนินการ | `userData`, `versionId` (ไม่ระบุ = ทุก version) |
| 7 | `getWorkflowsByUser` | workflow ที่ user เกี่ยวข้อง **รวมที่ยังไม่ถึงคิวตัวเอง** | `userData`, `versionId` |
| 8 | `addPreApprover` | ระบุผู้อนุมัติล่วงหน้าเป็นลำดับ | `versionId`, `referenceId`, `stateId`, `approver`, `seq`, `userId` |

### 3.1 `initializeWorkflow` (ชีต 1)

1. ตรวจว่า `versionId` + `referenceId` เคยสร้างในระบบแล้วหรือยัง
2. บันทึก `workflow_transaction` โดย `current_state_id` / `current_status_id` ดึงจาก `workflow_version.initial_state_id` / `initial_status_id` · `current_approver` = `userId` · `data_json` = `initialData`
3. สำเร็จ → `"Success"` · ไม่สำเร็จ → `"Initial Transaction Fail"`

> `referenceId` = **เลขเอกสารฝั่งแอป ต้อง unique** (ของ SBPGI คือ `doc_no`)

### 3.2 `eventWorkflow` — หัวใจของ engine (ชีต 2)

```
ตรวจว่ามี transaction ตาม versionId + referenceId ไหม
  ไม่มี → "ไม่พบ transaction"
  มี → หา route ที่ตรงกับ (versionId, current_state, event) จาก workflow_route
        ไม่มี → "Event ไม่ได้รับอนุญาตในสถานะปัจจุบัน"
        มี 1 route  → ใช้ route นั้นเลย
        มี > 1 route → วน loop ตาม seq แล้วเทียบ condition_json กับ eventParam
                        ไม่ตรง → continue · ตรง → ใช้ route นั้น
  → เปิด DB transaction (commit / rollback)
      อัปเดต workflow_transaction เป็น state/status ถัดไป
      หา "ผู้อนุมัติถัดไป" ตาม approver_type ของ route:
        user  → ใช้ nextApproverId ที่ส่งมา · ถ้าไม่ส่ง ไปหาใน workflow_approver ตาม state_id + seq
        group → ใช้ group_id ของ route
      บันทึก workflow_history (state ก่อน → หลัง, event, remark, create_by_name)
      ล้มเหลวขั้นใด → rollback + return error
      สำเร็จ → เรียก function ส่งเมลจาก lib แล้ว return
```

**การเทียบ `condition_json`** — `{"field", "operator", "value"}` · operator ที่รองรับ `== != > < >= <=`
ตัวอย่างจริงในไฟล์: `{"field":"amount","operator":"<","value":1000}` และ `{"field":"positionLevel","operator":">","value":210}`

**เงื่อนไขที่เพิ่มใน v1.2 (29/04/2026)**
- `approve_type = user` → ลง transaction แบบผู้อนุมัติรายคน
- `approve_type = group` → ลง transaction แบบกลุ่ม · การ map กลุ่มใช้ `workflow_group_map`
- (20/05/2026) เอา `userFullname` มาบันทึกลง `workflow_history.create_by_name`

### 3.3 `getPermissionEvents` — คุมทั้งปุ่มและการแสดงผล (ชีต 3)

ไม่ได้คืนแค่ปุ่มที่กดได้ แต่คืน **"display"** ว่าแต่ละส่วนของหน้าจอต้องแสดงแบบไหนด้วย

```json
{
  "event": [{"event":"save","eventName":"Save"}, {"event":"submit","eventName":"Submit"}],
  "display": [{"partId":"1","partName":"information","stateId":"10001","partDisplayType":"WRITE","partSeq":"1"}]
}
```

- ตรวจ `approve_type` → `user` เทียบ `userId` กับ `current_approver` · `group` เทียบ `userGroup`
- ไม่มีสิทธิ์ → `"user don't have permission event for this transaction"`
- หา part display จาก `workflow_part_display` ตาม `state_id` · ไม่มี → `display: []`

### 3.4 `getHistory` (ชีต 4) — output ต่อแถว

`versionId` · `transactionId` · `oldStateName` · `oldStatusName` · `eventName` · `newStateName` · `newStatusName` · `remark` · `updateDate` · `createByName`

### 3.5 `getTransaction` (ชีต 5)

`transactionId` · `referenceId` · `stateName` · `statusName` · `currentApprover` · `workflowName`

### 3.6 `getPendingFlowByUser` (ชีต 6)

ค้น `workflow_transaction` ทั้งจาก `user_id` และ `userGroup` ที่ `current_approver`
Output เท่ากับ `getTransaction` + `updateDate` + **`url_main`** (ลิงก์กลับไปหน้าจอของระบบต้นทาง — มาจาก `workflow_version`) + **`create_by`** (ดึงจาก `workflow_history` แถวแรกสุด)

### 3.7 `getWorkflowsByUser` (ชีต 7)

เหมือนข้อ 6 แต่ค้นเพิ่มใน `workflow_approver` ด้วย จึงเห็นงานที่ **"ยังไม่ถึงคิวตัวเอง"**

### 3.8 `addPreApprover` (ชีต 8)

insert `workflow_approver` โดย `approver_type` ตายตัวเป็น `"user"` · ต้องมี transaction อยู่ก่อน ไม่งั้น `"Transaction not found"`

---

## 4. ฐานข้อมูล 13 ตาราง

### 4.1 ตารางนิยาม flow (config — ตั้งครั้งเดียวต่อระบบ)

| ตาราง | คอลัมน์หลัก | หมายเหตุ |
|---|---|---|
| `workflow` | `workflow_id` · `workflow_name` | ระบุว่า workflow นี้ทำอะไร |
| `workflow_version` | `version_id` · `workflow_id` · `initial_state_id` · `initial_status_id` · `end_state_id` · `end_status_id` · `description` · **`url_main`** · **`url_param_mapping`** | 1 ระบบ = 1 version · `url_main` ใช้ลิงก์กลับหน้าจอจาก inbox กลาง |
| `workflow_state` | `state_id` · `state_name` · `version_id` | `state_id` running ตาม version (v1 → 10001+, v2 → 20001+) |
| `workflow_status` | `status_id` · `status_name` · `version_id` | **1 state มีได้หลาย status** |
| `workflow_event` | `event` · `event_name` | default: `save` `submit` `approve` `reject` `cancel` `sendback` |
| `workflow_route` | `route_id` · `version_id` · `from_state_id` · `event` · `to_state_id` · `to_status_id` · `seq` · `condition_json` · `approver_type` · `group_id` · **`email_id`** | หัวใจของ flow · `seq` = ลำดับตรวจเงื่อนไข · `email_id` ผูกเมลที่จะส่งเมื่อผ่าน route นี้ |

### 4.2 ตารางกลุ่มผู้อนุมัติ

| ตาราง | คอลัมน์ | หมายเหตุ |
|---|---|---|
| `workflow_group` | `group_id` · `group_name` · `approver_type` | ตัวอย่างจริง: FC · someFC · OPT · evaluate · ส่งเสริม |
| `workflow_group_map` | `group_map_id` · `group_id` · `map_table` · `map_column` · `map_key` | **ยืดหยุ่นมาก** — ไม่ระบุ `map_table` = เทียบกับ field ของ user โดยตรง (`userId`/`groupId`) · ระบุ `map_table` = ต้องเป็น **view ที่ where ด้วย user_id หรือ group_id ได้** (ตัวอย่างในไฟล์: `v_fml_responsible` · column `position`) |

### 4.3 ตารางข้อมูลรันไทม์

| ตาราง | คอลัมน์ | หมายเหตุ |
|---|---|---|
| `workflow_transaction` | `transaction_id` · `version_id` · `reference_id` · `current_state_id` · `current_status_id` · `current_approver` · `approver_type` · `data_json` · `update_date` | **UNIQUE (`transaction_id`, `version_id`)** |
| `workflow_history` | `history_id` · `version_id` · `transaction_id` · `old_state_id` · `old_status_id` · `new_state_id` · `new_status_id` · `event` · `event_data_json` · `create_by` · **`create_by_name`** · `create_date` | timeline |
| `workflow_approver` | `approver_id` · `version_id` · `transaction_id` · `current_approver` · `approver_type` · `state_id` · `approve_seq` · `create_date` · `approve_date` · `approve_event` · `remark` | ผู้อนุมัติล่วงหน้า + ผลที่อนุมัติจริง |

### 4.4 ตารางคุมการแสดงผลหน้าจอ ⭐

| ตาราง | คอลัมน์ | หมายเหตุ |
|---|---|---|
| `workflow_part` | `part_id` · `version_id` · `part_name` · `part_seq` | `part_name` = ชื่อ component ที่ map กับหน้าจอ |
| `workflow_part_display` | `state_id` · `part_id` · `part_display_type` · `owner_type` · `group_id` | `part_display_type` = **`READ`** (ดูอย่างเดียว) หรือ **`WRITE`** (แก้ได้) |

> ⚠️ ในไฟล์สะกดว่า `WRTIE` (พิมพ์ผิด) ทุกแถวของ `sample data` — ต้องยืนยันกับทีม lib ว่าค่าจริงในระบบคืออะไร

---

## 5. ตัวอย่าง flow ที่ให้มาในไฟล์

**Version 1 "workflow subarea"** — state `10001 initial` → `10002 approve1` → `10003/10004 approve2/3` → `10005 approve4` → `10099 finish`

| route | from | event | to | เงื่อนไข | ผู้อนุมัติ |
|---|---|---|---|---|---|
| 1 | 10001 | save | 10001 | — | user |
| 2 | 10001 | submit | 10002 | — | group 2 |
| 3 | 10002 | approve | 10003 | `amount < 1000` | group 1 |
| 4 | 10002 | approve | 10004 | `amount >= 1000` | group 3 |
| 5–7 | 10004 | approve | 10005 | `positionLevel` > / = / < `210` | group |

**สิ่งที่ตัวอย่างนี้พิสูจน์:** engine รองรับ **การแตก route ตามวงเงิน** และ **ตามระดับตำแหน่ง** ได้ในตัว โดยไม่ต้องเขียนโค้ดเงื่อนไขเอง

---

## 6. ผลกระทบต่อระบบประกันรายได้ (SBPGI) — สิ่งที่ต้องแก้ในเอกสารเรา

### 6.1 ⚠️ ชื่อ function ในเอกสารเราไม่ตรงกับของจริง

| เอกสารเราเขียนไว้ | ของจริงตาม LLDD นี้ |
|---|---|
| `triggerEvent` | **`eventWorkflow`** |
| `addPreparedApprover` | **`addPreApprover`** |
| `getPendingFlow` | **`getPendingFlowByUser`** |
| — | เพิ่ม `getWorkflowsByUser` ที่เรายังไม่เคยอ้างถึง |

> หมายเหตุ: ชีต `Mermaid seq` ยังเขียน `triggerEvent` อยู่ (ตกค้างจากฉบับก่อน) แต่ชีต `Detail` และ `2` ซึ่งเป็นสเปกจริงใช้ `eventWorkflow` — **ต้องยืนยันกับทีม lib ก่อนเขียนโค้ด**

### 6.2 ⚠️ จำนวนตาราง engine ไม่ตรง

`database.md` เขียนว่า engine มี **10 ตาราง** — ของจริงในเอกสารนี้มี **13 ตาราง** (ที่เราไม่เคยระบุคือ `workflow_group`, `workflow_group_map`, `workflow_part`, `workflow_part_display`, `workflow_event`, `workflow`)

### 6.3 ⭐ `workflow_part_display` ทำงานแทนสิ่งที่เราออกแบบเองไว้

หน้า `k2-document.html` ของเราใช้ `data-editrole` / `data-roleonly` / `.edit-only` สลับสิทธิ์แก้ไขรายส่วนตาม role — **engine มีกลไกนี้ให้อยู่แล้ว** ผ่าน `workflow_part` + `workflow_part_display` ที่คืนมากับ `getPermissionEvents`

→ SBPGI ควร**ลงทะเบียน part ของ 12 ส่วนในหน้าเอกสาร** แล้วให้ FE อ่าน `display[]` แทนการ hardcode สิทธิ์ต่อ role ในหน้าจอ
→ กระทบเอกสาร `LLDD-FE-Document-Detail` + role pack 5 ฉบับ และ `BE-Workflow-Engine-Definition` ที่กำลังจะสร้าง

### 6.4 ⭐ วงเงินอนุมัติทำที่ `condition_json` ได้เลย

กติกา SDD GI **GM ≤ 50,000 / AVP 50,001–300,000** map เข้ากับตัวอย่าง `{"field":"amount","operator":"<","value":1000}` ได้ตรง ๆ
→ ส่ง `eventParam = {"amount": <ยอดชดเชย>}` แล้วให้ engine เลือก route เอง — **ไม่ต้องเขียน if ในโค้ด SBPGI**
→ สอดคล้องกับที่เราตัดสินใจไว้ว่าวงเงินเก็บใน `common_code` ไม่ hardcode (แต่ต้องเลือกว่าจะเก็บที่ `common_code` หรือที่ `condition_json` ของ route — **อย่าเก็บสองที่**)

### 6.5 ⭐ engine ส่งอีเมลเอง

`workflow_route.email_id` + ขั้นตอน "เรียก function ส่งเมลจาก lib" ในชีต 2 → **EM-01/02/03 ของเรา (เปลี่ยนสถานะ / จบงาน / ส่งกลับ) อาจไม่ต้องเขียนเอง** ให้ผูก `email_id` ที่ route แทน
→ ต้องตรวจว่า template ที่ engine ใช้ อยู่ตาราง `email_template` เดียวกับที่ `@gosoft-sbp/email-lib` ใช้หรือไม่

### 6.6 ⭐ `url_main` ทำให้ inbox กลางลิงก์กลับมาที่หน้าเอกสารเราได้

`workflow_version.url_main` + `url_param_mapping` คือสิ่งที่ทำให้ `GET /api/workflow/pending` (inbox รวมข้ามระบบ) เปิดกลับมาหน้าจอต้นทางได้
→ SBPGI ต้องกรอก 2 ฟิลด์นี้ตอน register version เช่น `/sbpgi/documents/{year}/{running}?...`

### 6.7 ผู้อนุมัติของ SBPGI ควรใช้แบบไหน

`workflow_group_map` รองรับการ map ผ่าน **view** ที่ where ด้วย `user_id`/`group_id` ได้ (ตัวอย่าง `v_fml_responsible`)
→ ตรงกับที่ `database.md` บันทึกไว้ว่าผู้อนุมัติ SBPGI resolve จาก view `V_FGI_SBP_APPROVER` ด้วย (`store_type`, `store_area`) + `position_level`
→ **ต้องยืนยันว่า view นั้น where ด้วย `user_id`/`group_id` ได้จริง** ไม่งั้นใช้กลไก `map_table` ไม่ได้ ต้องกลับไปใช้ `addPreApprover` แบบระบุรายคนแทน

---

## 7. สิ่งที่เอกสารนี้ยังไม่ตอบ

1. **ชื่อ function ที่ถูกต้อง** — `eventWorkflow` vs `triggerEvent` ขัดกันเองภายในไฟล์
2. **ค่า `part_display_type`** — สะกด `WRTIE` ทุกแถว ไม่รู้ว่าค่าจริงคืออะไร
3. **`workflow_route` มี 2 นิยาม** — ชีต `sample data` มีคอลัมน์ `group_id` แต่ entity ที่แนบมาเขียนเป็น `approver` และตั้งชื่อ property ว่า `approverRoleId` (ไม่ตรงกับ `approver_type`)
4. **ไม่มี API สำหรับ "ถอน/แก้ไข" ผู้อนุมัติล่วงหน้า** — มีแต่ `addPreApprover`
5. **ไม่มีรายละเอียดการ config email** — `email_id` ชี้ไป "table email......" (ยังไม่ระบุชื่อตาราง)
6. **ไม่มี versioning/migration guide** — ถ้าต้องแก้ flow หลังมี transaction วิ่งอยู่แล้วต้องทำอย่างไร

---

## 8. เอกสารที่เกี่ยวข้อง

- `SBP/srm-sps-spsap-store-backend.md` §1.5–1.6 — สรุป `WORKFLOW_GUIDE.md` / `WORKFLOW_QUICKSTART.md` ของ lib ตัวเดียวกัน (ชื่อ use case ที่ระบุไว้ที่นั่นคือ `TriggerEventUseCase`, `AddPreparedApproverUseCase`, `GetPendingFlowUseCase` — **ต่างจากไฟล์นี้อีกชุด**)
- `database.md` — หัวข้อ "ตารางที่ตัดออกรอบ 2" ที่ระบุว่า SBPGI ใช้ engine นี้แทนตาราง workflow ของตัวเอง
- `workflow.md` — flow 5 ขั้นของ SBPGI ที่ต้อง map ลง state/route ของ engine
