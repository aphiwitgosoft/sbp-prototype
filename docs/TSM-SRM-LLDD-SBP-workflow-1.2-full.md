# TSM-SRM-LLDD SBP workflow 1.2 — แปลงจาก Excel เป็น Markdown

> แปลงอัตโนมัติจาก `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` (1,419 KB · 14 ชีต) ด้วย `tools/xlsx_to_md.py` — **ไฟล์ต้นทางเป็น read-only ไม่ถูกแก้ไข**
> ต้องการเนื้อหาสรุปอ่านง่ายให้ดู [`SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md`](../SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md) แทน

## สารบัญชีต

| # | ชีต | ขนาด |
|---|---|---|
| 1 | [Document Version History](#document-version-history) | 5 แถว × 6 คอลัมน์ |
| 2 | [Introduction](#introduction) | 11 แถว × 3 คอลัมน์ |
| 3 | [Detail](#detail) | 264 แถว × 15 คอลัมน์ |
| 4 | [1](#1) | 21 แถว × 13 คอลัมน์ |
| 5 | [2](#2) | 62 แถว × 29 คอลัมน์ |
| 6 | [3](#3) | 45 แถว × 25 คอลัมน์ |
| 7 | [4](#4) | 23 แถว × 12 คอลัมน์ |
| 8 | [5](#5) | 19 แถว × 9 คอลัมน์ |
| 9 | [6](#6) | 27 แถว × 13 คอลัมน์ |
| 10 | [7](#7) | 25 แถว × 13 คอลัมน์ |
| 11 | [8](#8) | 25 แถว × 9 คอลัมน์ |
| 12 | [sample data](#sample-data) | 179 แถว × 21 คอลัมน์ |
| 13 | [Mermaid seq](#mermaid-seq) | 101 แถว × 15 คอลัมน์ |
| 14 | [temp](#temp) | 269 แถว × 10 คอลัมน์ |

---

## Document Version History

**Document Version History**

| Version Number | Release Date | Created By | Detail | Reviewed by | Authorized by |
|---|---|---|---|---|---|
| 1.0 | 14/07/2025 | Sukol K.. | Initial Document | Sudtida J. |  |
| 1.1 | 22/10/2025 | Sukol K.. | - ปรับเพิ่ม transaction ใน sequence diagram<br>- เพิ่มการจัดการ display หน้าจอ | Sudtida J. |  |
| 1.2 | 29/04/2026 | Sukol K.. | ปรับแก้ trigger event เพิ่มเงื่อนไขการระบุการอนุมัติเป็น user | Sudtida J. |  |

---

## Introduction

| บทนำ (Introduction) | col2 | col3 |
|---|---|---|
|  | วัตถุประสงค์ (Purpose) |  |
|  |  | สำหรับใช้เป็น lib กลางให้ module อื่นๆ import เพื่อใช้งาน  จัดการเกี่ยวกับ workflow |
|  | ขอบเขตเอกสาร (Scope) |  |
|  |  | สำหรับอธิบาย function การทำงานในส่วนของ lib workflow |
|  | Tailoring Guideline |  |

---

## Detail

**workflow engine**

| col1 | function | initializeWorkflow | สร้าง workflow | ระบุ version, userId , referrenceId | col6 | col7 | col8 | col9 | ไปที่ 1 | col11 | col12 | col13 | col14 | col15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | eventWorkflow | ส่วนของการ action flow (submit,approve,reject,...) | ระบุ version , referenceId, event , eventParam , remark , userId |  |  |  |  | ไปที่ 2 |  |  | เพิ่ม notify ผ่าน mail กลาง |  |  |
|  |  | getPermissionEvents | ดึงรายละเอียด event ที่ user สามารถดำเนินการได้ | ระบุ version , referenceId,  userData |  |  |  |  | ไปที่ 3 | part display |  | เรื่องการส่งข้อมูล user |  |  |
|  |  | getHistory | ดึงประวัติของ workflow | ระบุ version , referenceId |  | referenceId |  |  | ไปที่ 4 |  |  |  |  |  |
|  |  | getTransaction | ดึงข้อมูล workflow | ระบุ version , referenceId |  | referenceId |  |  | ไปที่ 5 | state , approver |  |  |  |  |
|  |  | getPendingFlowByUser | ดึงข้อมูล workflow ที่อยู่ในสถานะ Pending ของ user | ระบุ userData |  |  |  |  | ไปที่ 6 |  |  |  |  |  |
|  |  | getWorkflowsByUser | ดึงข้อมูล workflow ที่มี user อยู่ใน flow รวมถึงรออนุมัติ ยังไม่ถึงขั้นตอนอนุมัติ และอนุมัติไปแล้ว | ระบุ userData |  |  |  |  | ไปที่ 7 |  |  |  |  |  |
|  |  | addPreApprover | เพิ่มการระบุผู้อนุมัติล่วงหน้า | ระบุ version, userId , referenceId , state_id , approver , seq |  |  |  |  | ไปที่ 8 |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1คน1role |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  | ปรับ seq diagram เรื่องการ rollback |
|  |  |  |  |  |  |  |  |  | ไปที่ 1 |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | ไปที่ 2 |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | param สำหรับแยก route |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | detail ตรวจสอบจะมีเรื่องการเช็คว่าจะต้องไปที่ route ไหน |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | ไปที่ 3 |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | ไปที่ 4 |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | ไปที่ 5 |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | ไปที่ 6 |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | เพิ่มหางานค้างตามคน |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | ไปที่ 7 |  |  |  |  |  |
|  | โครงสร้าง |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | src/ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ├── app.module.ts |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ├── main.ts |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | └── workflow/ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ├── interfaces/ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   ├── workflow.interface.ts |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   └── workflow-event.dto.ts |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ├── entities/ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   ├── workflow-transaction.entity.ts | entities ของ table workflow_history |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   ├── workflow-history.entity.ts | entities ของ table workflow_transaction |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   ├── workflow-route.entity.ts | entities ของ table workflow_route |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   ├── workflow-state.entity.ts | entities ของ table workflow_state |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   └── workflow-version.entity.ts | entities ของ table workflow_version |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ├── services/ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   └── workflow.service.ts | logic หลักทั้งหมดของ program |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ├── providers/ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | │   └── workflow.repository.ts | เชื่อมต่อ DB ผ่าน typeORM |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ├── workflow.module.ts |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | └── index.ts |  |  |  |  |  |  |  |  |  |  |  |  |

---

## 1

**Initialize workflow**

**สำหรับตั้งต้น workflow โดยระบุ versionIdที่ต้องการสร้าง  และ referenceId (id ของเอกสารหรือ process ที่ต้องการผูก) และ userId**

**สร้างข้อมูล transaction ด้วยข้อมูล state แรก ตาม workflowId**

| col1 | col2 | input | name | col5 | col6 | detail | col8 | col9 | example | col11 | col12 | col13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  | initialData | versionId |  | version ที่ต้องการสร้าง |  |  | 1 |  |  |  |
|  |  |  |  | userId |  | ผู้สร้าง |  |  | 123 |  |  |  |
|  |  |  |  | referenceId |  | เลขเอกสารที่ผูกกับ workflow เป็น key ของเอกสารที่มาผูกกับ workflow |  |  |  |  |  | เป็นเลขที่เอกสารของฝั่ง App จะต้องเป็น key ที่ unique |
|  |  | ตรวจสอบ versionId และ referenceId ว่าเคยมีการสร้างในระบบไหม   ถ้ามี  return   "workflow referenceId duplicate" |  |  |  |  |  |  |  |  |  |  |
|  |  | บันทึกข้อมูลลง workflow_transaction   (saveTransaction) |  |  |  |  |  |  |  |  |  |  |
|  |  | data | field | detail |  |  |  |  |  |  |  |  |
|  |  |  | transaction_id | auto gen |  |  |  |  |  |  |  |  |
|  |  |  | version_id | ที่ระบุเข้ามาว่าเป็น version อะไร |  |  |  |  |  |  |  |  |
|  |  |  | reference_id | ระบุเข้ามา |  |  |  |  |  |  |  |  |
|  |  |  | current_state_id | ดึงมาจาก workflow_version (initial_state_id) |  |  |  |  |  |  |  |  |
|  |  |  | current_status_id |  |  |  |  |  |  |  |  |  |
|  |  |  | current_approver | userId |  |  |  |  |  |  |  |  |
|  |  |  | data_json | initialData |  |  |  |  |  |  |  |  |
|  |  | บันทึกสำเร็จ return "Success" |  |  |  |  |  |  |  |  |  |  |
|  |  | บันทึกไม่สำเร็จ return "Initial Transaction Fail" |  |  |  |  |  |  |  |  |  |  |

---

## 2

**Trigger Event**

**สำหรับ update ข้อมูลจาก event ที่ส่งเข้ามา หา state ถัดไปที่ถูกต้อง**

| col1 | input | name | detail | col5 | col6 | col7 | example | col9 | col10 | col11 | เงื่อนไขการส่งข้อมูล eventParam | col13 | col14 | col15 | col16 | col17 | col18 | col19 | col20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | versionId | version ที่ต้องการดำเนินการ |  |  |  | 1 |  |  |  |  | มาจากการระบุข้อมูลใน table workflow_route ที่ field condition_json |  |  |  |  |  |  |  |
|  |  | referenceId | เลขเอกสารที่ผูกกับ workflow เป็น key ของเอกสารที่มาผูกกับ workflow |  |  |  | 1 |  |  |  |  | การระบุ route |  |  |  |  |  |  |  |
|  |  | event | event ที่จะดำเนินการ |  |  |  | submit |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | eventParam | detail เพิ่มเติมสำหรับแยก route |  |  |  | {"amount":"10000"} |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | remark | ระบุรายละเอียดการอนุมัติ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 16/6/2026 |  | userData | ข้อมูล user |  |  |  | {"userId":"123","groupId":"1"} |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | userFullname | ชื่อผู้ดำเนินการ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | nextApproverId | ผูู้้ดำเนินการถัดไป |  |  |  | 124 |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ตรวจสอบสิทธิ์ และสถานะ workflow ปัจจุบัน ตาม versionId,referenceId,userId -> flow   (checkTransaction) |  |  |  |  |  |  |  |  |  | เหลือแค่ตรวจสอบ transaction ในระบบ ว่ามี transaction ไหม ตาม versionId,referenceId |  |  |  |  |  |  |  |
|  |  | ถ้าไม่มี return "User ไม่ได้รับอนุญาตในสถานะปัจจุบัน" |  |  |  |  |  |  |  |  |  | ถ้าไม่มี return "ไม่พบ transaction" |  |  |  |  |  |  |  |
|  |  | ถ้ามี ดำเนินการต่อ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ใช้ข้อมูล workflowId,event ไปหา route ที่เป็นไปได้สำหรับ event ที่ระบุมา  -> list route   (getRoute) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ถ้าไม่มี return "Event ไม่ได้รับอนุญาตในสถานะปัจจุบัน" |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ถ้ามี ดำเนินการต่อ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | ใช้ list route ที่ได้มา ตรวจสอบจำนวน |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | ถ้ามีรายการเดียว |  |  |  |  |  |  |  |  |  |  |  |  |  |  | เงื่อนไขเพิ่มเติม 29/04/2026 |
|  |  |  |  |  | สร้าง transaction(สำหรับ commit,rollback) |  |  |  |  |  |  |  |  |  |  |  |  |  | ถ้า approve_type จาก workflow_route เป็น user ให้ลง transaction.approver เป็น nextApproverId |
|  |  |  |  |  | ดำเนินการบันทึกข้อมูล transaction  อัพเดทข้อมูล ขั้นตอนต่อไป(state),ผู้อนุมัติลำดับถัดไป(approver) จาก route ที่ได้   (saveTransaction) |  |  |  |  |  |  |  |  |  |  |  |  |  | ถ้า approve_type จาก workflow_route เป็น group ให้ลง transaction.approver เป็น route.group_id |
|  |  |  |  |  |  | ถ้า approverType เป็น user |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | ถ้ามี nextApproverId ที่ส่งเข้ามา ถ้ามี ใช้เป็น resolvedNextApproverId ขั้นต่อไป |  |  |  |  |  |  |  |  |  |  |  | การ map group ใช้จาก workflow_group_map โดย group_id ตรงกับ route.group_id , transaction.group_id |
|  |  |  |  |  |  |  | ถ้าไม่มี ไปตรวจสอบเพิ่มเติมใน workflow_approver ที่ state_id,transaction_id เดียวกัน เอา current_approver มาใช้เป็น resolvedNextApproverId |  |  |  |  |  |  |  |  |  |  |  | แล้วเอาข้อมูลใน group_map ไปหาต่อว่าต้องผูกกับข้อมูลไหน |
|  |  |  |  |  |  | ถ้า approverType เป็น group |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | ใช้จาก wf_route group_id  ใช้เป็น resolvedNextApproverId |  |  |  |  |  |  |  |  |  |  |  | เงื่อนไขเพิ่มเติม 20/05/2026 |
|  |  |  |  |  | ถ้าบันทึกไม่สำเร็จ rollback transaction , return "workflow fail to process , please check .. " |  |  |  |  |  |  |  |  |  |  |  |  |  | เอา userFullname มาบันทึกตอนลง history field create_by_name |
|  |  |  |  |  | ถ้าบันทึกสำเร็จ ดำเนินการต่อ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  | ดำเนินการบันทึกประวัติการดำเนินการ history ระบุ state ก่อนหน้า,event, state ถัดไป,userId,transactionId,versionId   (saveHistory) |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  | ถ้าบันทึกไม่สำเร็จ rollback transaction , return "workflow history fail to process , please check .. " |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  | ถ้าบันทึกสำเร็จ เรียก function ส่งเมล์จาก lib  .....  และ return success |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | ถ้ามีมากกว่า 1 รายการ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | วน loop ตาม route |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | ตรวจสอบเงื่อนไขจาก eventParam โดยใช้ค่าที่ได้จาก condition_json มาตรวจสอบว่าต้องใช้ค่าไหน เปรียบเทียบกับข้อมูล |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  | ถ้าไม่ตรงเงื่อนไข continue ตาม loop |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  | ถ้าตรงเงื่อนไข |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | สร้าง transaction(สำหรับ commit,rollback) |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | ดำเนินการบันทึกข้อมูล transaction  อัพเดทข้อมูล ขั้นตอนต่อไป(state),ผู้อนุมัติลำดับถัดไป(approver) จาก route ที่ได้   (saveTransaction) |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | ถ้า approverType เป็น user |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  | ถ้ามี nextApproverId ที่ส่งเข้ามา ถ้ามี ใช้เป็น resolvedNextApproverId ขั้นต่อไป |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  | ถ้าไม่มี ไปตรวจสอบเพิ่มเติมใน workflow_approver ที่ state_id,transaction_id เดียวกัน เอา current_approver มาใช้เป็น resolvedNextApproverId |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | ถ้า approverType เป็น group |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  | ใช้จาก wf_route group_id  ใช้เป็น resolvedNextApproverId |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | ถ้าบันทึกไม่สำเร็จ rollback transaction , return "workflow fail to process , please check .. " |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  | ถ้าบันทึกสำเร็จ ดำเนินการต่อ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  | ดำเนินการบันทึกประวัติการดำเนินการ history ระบุ state ก่อนหน้า,event, state ถัดไป,userId,transactionId,versionId  (saveHistory) |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  | ถ้าบันทึกไม่สำเร็จ rollback transaction , return "workflow history fail to process , please check .. " |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  | ถ้าบันทึกสำเร็จ เรียก function ส่งเมล์จาก lib  .....  และ  return success |  |  |  |  |  |  |  |  |  |  |  |
|  | รายละเอียดการเปรียบเทียบ condition_json |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | name | detail |  |  |  |  |  |  |  | operator | == |  |  |  |  |  |  |  |  |
|  | field | ชื่อ field ที่ใช้เปรียบเทียบ |  |  |  |  |  |  |  |  | != |  |  |  |  |  |  |  |  |
|  | operator | เครื่องหมายที่ไว้ใช้เปรียบเทียบ |  |  |  |  |  |  |  |  | > |  |  |  |  |  |  |  |  |
|  | value | ค่าที่ใช้สำหรับเปรียบเทียบ |  |  |  |  |  |  |  |  | < |  |  |  |  |  |  |  |  |
|  | จาก route ที่ได้ |  |  |  |  |  |  |  |  |  | >= |  |  |  |  |  |  |  |  |
|  |  | ได้ condition_json มา ดำเนินการวน loop ตาม list |  |  |  |  |  |  |  |  | <= |  |  |  |  |  |  |  |  |
|  |  |  | get field ใน eventParam ที่ส่งเข้ามา |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | นำค่าที่ได้ มาเปรียบเทียบด้วย operator กับ value |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ถ้าตรงตามเงื่อนไข ใช้ route นี้ในการดำเนินการต่อ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ถ้าไม่ตรง continue loop ต่อ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

## 3

**Get Permission Event**

**สำหรับดึงข้อมูลผู้มีสิทธิ์อนุมัติ ว่าสามารถกำเนินการ event ไหนได้บ้าง ในสถานะปัจจุบัน จาก versionId,transactionId,userId**

| col1 | input | name | detail | col5 | col6 | col7 | example | col9 | col10 | col11 | col12 | col13 | col14 | col15 | col16 | col17 | col18 | col19 | col20 | col21 | col22 | col23 | col24 | col25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | versionId | version ที่ต้องการดำเนินการ |  |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | referenceId | เลขเอกสารที่ผูกกับ workflow เป็น key ของเอกสารที่มาผูกกับ workflow |  |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | userData | ข้อมูล user |  |  |  | {"userId":"123","groupId":"1"} |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ดึงข้อมูลจาก DB จาก workflow_transaction โดยใช้ referenceId,versionId |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ถ้าไม่มีข้อมูล return "Transaction Not Found" |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล ดำเนินการต่อ |  |  |  |  |  |  |  |  |  | เช็ค display กับกลุ่มที่เขามา ถ้ากลุ่มไม่ตรง return user don't have permission event for this transaction |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ตรวจสอบ approve_type (user , group , role) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | display | action | read:write |
|  |  |  | ถ้า approve_type = user |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | เช็คข้อมูล userId กับ current_approver ใน workflow_transaction |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | event |  |  |
|  |  |  | ถ้า approve_type = group |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | เช็คข้อมูล userGroup กับ current_approver ใน workflow_transaction   ดูจาก workflow_group_map ว่ากลุ่มไหน |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | ถ้ากลุ่มตรงและมีข้อมูล แสดง event ทั้งหมดที่ดำเนินการได้ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ตรวจสอบ part display ตาม state ที่ดำเนินการ หาด้วย state_id ปัจจุบัน map ข้อมูล part กับ part display |  |  |  |  |  |  |  |  | หาด้วย state ที่เข้ามาจากหน้าจอ |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | ถ้าไม่มี ใส่ display เป็น [] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ถ้าไม่มีสิทธิ์ return user don't have permission event for this transaction |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ถ้ามีสิทธิ์ ตรวจสอบ event ที่สามารถดำเนินการได้ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | ตรวจสอบจาก route ที่ state ปัจจุบันว่าสามารถดำเนินการอะไรต่อได้บ้าง |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  | return event  [{"event":"save","eventName":"Save"},{"event":"submit","eventName":"Submit"}] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | output |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | name | detail |  |  |  | example |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | event | event ที่สามารถดำเนินการได้ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | eventName | ชื่อ event สำหรับแสดงผล |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | display |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | name | detail |  |  |  | example |  |  | แสดงเป็น list ถ้ามีหลาย part |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | partId | id ของ part |  |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | partName | ชื่อ part ที่ใช้ map ข้อมูล |  |  |  | information |  |  | "display" : [<br>{"partId":"1","partName":"information","stateId":"10001","partDisplayType":"WRITE","partSeq":"1"},<br>{"partId":"2","partName":"address","stateId":"10001","partDisplayType":"WRITE","partSeq":"2"},<br>{"partId":"3","partName":"education","stateId":"10001","partDisplayType":"WRITE","partSeq":"3"},<br>{"partId":"5","partName":"action","stateId":"10001","partDisplayType":"WRITE","partSeq":"5"}] |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | stateId | id ของ state ปัจจุบันที่จะแสดงผล |  |  |  | 10001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | partDisplayType | ประเภทการแสดง |  |  |  | WRITE |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | partSeq | ลำดับการแสดงผล |  |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

## 4

**Get History**

**ดึงประวัติของ transaction จาก workflowId,transactionId**

| col1 | input | name | detail | col5 | col6 | col7 | example | col9 | col10 | col11 | col12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | versionId | version ที่ต้องการดำเนินการ |  |  |  | 1 |  |  |  |  |
|  |  | referenceId | เลขเอกสารที่ผูกกับ workflow เป็น key ของเอกสารที่มาผูกกับ workflow |  |  |  | 1 |  |  |  |  |
|  |  | ดึงข้อมูล Flow จาก versionId,referenceId |  |  |  |  |  |  |  |  |  |
|  |  | ดึงข้อมูล workflow_history จาก versionId,transactionId   (getTransactionHistory) |  |  |  |  |  |  |  |  |  |
|  |  | ถ้าไม่มีข้อมูล return "History Not Found" |  |  |  |  |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล return list history |  |  |  |  |  |  |  |  |  |
|  | output | List history ทำเป็นรูปแบบ list json |  |  |  |  |  |  |  |  |  |
|  |  | name | detail |  |  |  | example |  |  |  |  |
|  |  | versionId | version ที่ต้องการดำเนินการ |  |  |  |  |  |  |  |  |
|  |  | transactionId | id ของ flow ที่จะดำเนินการ |  |  |  |  |  |  |  |  |
|  |  | oldStateName | ขั้นตอนก่อนหน้า |  |  |  |  |  |  |  |  |
|  |  | oldStatusName | สถานะก่อนหน้า |  |  |  |  |  |  |  |  |
|  |  | eventName | event ที่ดำเนินการ |  |  |  |  |  |  |  |  |
|  |  | newStateName | ขั้นตอนหลังจากดำเนินการ |  |  |  |  |  |  |  |  |
|  |  | newStatusName | สถานะหลังจากดำเนินการ |  |  |  |  |  |  |  |  |
|  |  | remark | หมายเหตุเพิ่มเติมที่ระบุมาในแต่ละ state |  |  |  |  |  |  |  |  |
|  |  | updateDate | วันและเวลาที่ดำเนินการในขั้นตอน |  |  |  |  |  |  |  |  |
|  |  | createByName | ชื่อผู้ดำเนินการ |  |  |  |  |  | create_by_name |  | 07/08/2026 |

---

## 5

**Get Transaction**

**ดึงรายละเอียดของ transaction**

| col1 | input | name | detail | col5 | col6 | col7 | example |
|---|---|---|---|---|---|---|---|
|  |  | versionId | version ที่ต้องการดำเนินการ |  |  |  | 1 |
|  |  | referenceId | เลขเอกสารที่ผูกกับ workflow เป็น key ของเอกสารที่มาผูกกับ workflow |  |  |  | 1 |
|  |  | ดึงข้อมูล workflow_transaction ปัจจุบัน จาก  referenceId,versionId |  |  |  |  |  |
|  |  | ถ้าไม่มีข้อมูล return "Transaction Not Found" |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล return ข้อมูล transaction |  |  |  |  |  |
|  | output |  |  |  |  |  |  |
|  |  | name | detail |  |  |  | example |
|  |  | transactionId | id ของ flow |  |  |  |  |
|  |  | referenceId | key ที่ผูกกับ เอกสาร |  |  |  |  |
|  |  | stateName | ชื่อขั้นตอน |  |  |  |  |
|  |  | statusName | ชื่อสถานะ |  |  |  |  |
|  |  | currentApprover | ผู้อนุมัติปัจจุบัน |  |  |  |  |
|  |  | workflowName | ชื่ื่อ workflow |  |  |  |  |

---

## 6

**Get pending flow by user**

**ดึงข้อมูลที่รอดำเนินการจาก user ที่ระบุ**

| col1 | input | name | detail | col5 | col6 | col7 | example | col9 | col10 | col11 | col12 | col13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | userData | ข้อมูล user |  |  |  | {"userId":"123","groupId":"1"} |  |  |  |  |  |
|  |  | versionId | id ของ version flow ที่ต้องการค้นหา ถ้าไม่ระบุ จะค้นหาทุก version |  |  |  | 1 |  |  |  |  |  |
|  | สร้าง List transactionList |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ตรวจสอบข้อมูล workflow_transaction จาก user_id โดยค้นหาที่ approve_type = "user"  และ current_approver = userId และ version_id = versionId(versionId null ไม่ต้อง where version_id) |  |  |  |  |  |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล ดึงรายละเอียด transaction ใส่ transactionList |  |  |  |  |  |  |  |  |  |  |
|  |  | ตรวจสอบข้อมูล workflow_transaction จาก userGroup โดยค้นหาที่ approve_type = "group"  และ current_approver = userGroup และ version_id = versionId(versionId null ไม่ต้อง where version_id) |  |  |  |  |  |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล ดึงรายละเอียด transaction ใส่ transactionList |  |  |  |  |  |  |  |  |  |  |
|  | output | list transaction  ทำเป็นรูปแบบ list json |  |  |  |  |  |  |  |  |  |  |
|  |  | name | detail |  |  |  | example |  |  |  |  |  |
|  |  | transactionId | id ของ flow |  |  |  |  |  |  |  |  |  |
|  |  | referenceId | key ที่ผูกกับ เอกสาร |  |  |  |  |  |  |  |  |  |
|  |  | stateName | ชื่อขั้นตอน |  |  |  |  |  |  |  |  |  |
|  |  | statusName | ชือสถานะ |  |  |  |  |  |  |  |  |  |
|  |  | currentApprover | ผู้อนุมัติปัจจุบัน |  |  |  |  |  |  |  |  |  |
|  |  | workflowName | ชื่ื่อ workflow |  |  |  |  |  |  |  |  |  |
|  |  | updateDate | วันที่ update |  |  |  |  |  |  |  |  |  |
| 25/05/2026 |  | url_main | url ที่จะ link ไปหน้าจอของ flow |  |  |  |  |  |  | ต้อง map key ของ url |  | เอามาจาก workflow_version |
|  |  | create_by | ชื่อเต็มของผู้สร้าง |  |  |  |  |  |  | ดึงจาก workflow_history เรียงตามวันที่ เอาคนแรกมาแสดง |  |  |

---

## 7

**Get workflows by user**

**ดึงข้อมูล workflow ที่มี user อยู่ใน flow รวมถึงรออนุมัติ ยังไม่ถึงขั้นตอนอนุมัติ และอนุมัติไปแล้ว โดยใช้ userData ที่ระบุเข้ามา**

| col1 | input | name | detail | col5 | col6 | col7 | example |
|---|---|---|---|---|---|---|---|
|  |  | userData | ข้อมูล user |  |  |  | {"userId":"123","groupId":"1"} |
|  |  | versionId | id ของ version flow ที่ต้องการค้นหา ถ้าไม่ระบุ จะค้นหาทุก version |  |  |  | 1 |
|  | สร้าง List transactionList |  |  |  |  |  |  |
|  |  | ตรวจสอบข้อมูล workflow_transaction จาก user_id โดยค้นหาที่ approve_type = "user"  และ current_approver = userId และ version_id = versionId(versionId null ไม่ต้อง where version_id) |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล ดึงรายละเอียด transaction ใส่ transactionList |  |  |  |  |  |
|  |  | ตรวจสอบข้อมูล workflow_transaction จาก userGroup โดยค้นหาที่ approve_type = "group"  และ current_approver = userGroup และ version_id = versionId(versionId null ไม่ต้อง where version_id) |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล ดึงรายละเอียด transaction ใส่ transactionList |  |  |  |  |  |
|  |  | ตรวจสอบข้อมูล workflow_approver จาก user_id โดยค้นหาที่ approve_type = "user"  และ current_approver = userId และ version_id = versionId(versionId null ไม่ต้อง where version_id) |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล ดึงรายละเอียด transaction โดยใช้ transaction_id จาก workflow_approver ที่มีข้อมูลไปค้นหาใน workflow_transaction ใส่ transactionList |  |  |  |  |  |
|  |  | ตรวจสอบข้อมูล workflow_approver จาก userGroup โดยค้นหาที่ approve_type = "group"  และ current_approver = userGroup และ version_id = versionId(versionId null ไม่ต้อง where version_id) |  |  |  |  |  |
|  |  | ถ้ามีข้อมูล ดึงรายละเอียด transaction โดยใช้ transaction_id จาก workflow_approver ที่มีข้อมูลไปค้นหาใน workflow_transaction ใส่ transactionList |  |  |  |  |  |
|  | output | list transaction  ทำเป็นรูปแบบ list json |  |  |  |  |  |
|  |  | name | detail |  |  |  | example |
|  |  | transactionId | id ของ flow |  |  |  |  |
|  |  | referenceId | key ที่ผูกกับ เอกสาร |  |  |  |  |
|  |  | stateName | ชื่อขั้นตอน |  |  |  |  |
|  |  | statusName | ชื่อสถานะ |  |  |  |  |
|  |  | currentApprover | ผู้อนุมัติปัจจุบัน |  |  |  |  |
|  |  | workflowName | ชื่ื่อ workflow |  |  |  |  |

---

## 8

**Add Prepared Approver**

**เพิ่มผู้อนุมัติไว้ล่วงหน้า**

| col1 | input | name | detail | col5 | col6 | col7 | example |
|---|---|---|---|---|---|---|---|
|  |  | versionId | version ที่ต้องการดำเนินการ |  |  |  | 1 |
|  |  | referenceId | เลขเอกสารที่ผูกกับ workflow เป็น key ของเอกสารที่มาผูกกับ workflow |  |  |  | 1 |
|  |  | stateId | state ที่ต้องการเพิ่มผู้อนุมัติ |  |  |  | 10002 |
|  |  | approver | user_id ผู้อนุมัติ |  |  |  | 123 |
|  |  | seq | ลำดับการอนุมัติ |  |  |  | 1 |
|  |  | userId | ผู้ดำเนินการ |  |  |  | 123 |
|  | ตรวจสอบข้อมูล transaction โดยใช้ versionId และ referenceId ค้นหาใน workflow_transaction |  |  |  |  |  |  |
|  | ถ้าไม่มี return "Transaction not found" |  |  |  |  |  |  |
|  | ถ้ามี insert ข้อมูล ลง workflow_approver |  |  |  |  |  |  |
|  |  | Column |  |  |  |  |  |
|  |  | approver_id | auto increase |  |  |  |  |
|  |  | version_id | versionId ที่ระบุเข้ามา |  |  |  |  |
|  |  | transaction_id | transactionId จากข้อมูล transaction ที่ตรวจสอบ |  |  |  |  |
|  |  | current_approver | approver ที่ระบุเข้ามา |  |  |  |  |
|  |  | approver_type | "user" |  |  |  |  |
|  |  | state_id | stateId ที่ระบุเข้ามา |  |  |  |  |
|  |  | approve_seq | seq ที่ระบุเข้ามา |  |  |  |  |
|  |  | create_date | sysdate |  |  |  |  |
|  |  | บันทึกไม่สำเร็จ return "Fail Add Approver" |  |  |  |  |  |
|  |  | บันทีกสำเร็จ return "Success" |  |  |  |  |  |

---

## sample data

| workflow_transaction | col2 | col3 | col4 | col5 | col6 | col7 | col8 | col9 | col10 | col11 | col12 | col13 | @Entity("workflow_transaction")<br>@Unique(["transaction_id", "version_id"])<br>export class WorkflowTransaction {<br>    @PrimaryGeneratedColumn({ name: "transaction_id" })<br>    transactionId: number;<br><br>    @Column({ name: "version_id", type: "varchar", length: 50 })<br>    versionId: string;<br><br>    @Column({ name: "reference_id", type: "varchar", length: 50 })<br>    referenceId: string;<br><br>    @Column({ name: "current_state_id", type: "varchar", length: 100 })<br>    currentStateId: string;<br>	<br>	@Column({ name: "current_status_id", type: "varchar", length: 100 })<br>    currentStatusId: string;<br><br>    @Column({ name: "current_approver", type: "varchar", length: 100 })<br>    currentApprover: string;<br><br>    @Column({ name: "approver_type", type: "varchar", length: 100 })<br>    approverType: string;<br>    <br>    @Column({ name: "data_json", type: "json", nullable: true })<br>    dataJson: Record<string, any>;<br><br>    @Column({ name: "update_date", type: "timestamptz", default: () => "CURRENT_TIMESTAMP" })<br>    updateDate: Date;<br>} | col15 | col16 | col17 | @Entity("workflow_history")<br>export class WorkflowHistory {<br>    @PrimaryGeneratedColumn({ name: "history_id" })<br>    historyId: number;<br><br>    @Column({ name: "version_id", type: "varchar", length: 50 })<br>    versionId: string;<br><br>    @Column({ name: "transaction_id", type: "varchar", length: 50 })<br>    transactionId: string;<br><br>    @Column({ name: "old_state_id", type: "varchar", length: 100 })<br>    oldStateId: string;<br>	<br>	@Column({ name: "old_status_id", type: "varchar", length: 100 })<br>    oldStatusId: string;<br><br>    @Column({ name: "event", type: "varchar", length: 100 })<br>    event: string;<br><br>    @Column({ name: "new_state_id", type: "varchar", length: 100 })<br>    newStateId: string;<br>	<br>	@Column({ name: "new_status_id", type: "varchar", length: 100 })<br>    newStatusId: string;<br><br>    @Column({ name: "event_data_json", type: "json", nullable: true })<br>    eventDataJson: Record<string, any>;<br><br>    @Column({ name: "create_by", type: "varchar", length: 100, nullable: true })<br>    createBy: string;<br><br>    @Column({ name: "create_date", type: "timestamptz", default: () => "CURRENT_TIMESTAMP" })<br>    createDate: Date;<br>} |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| transaction_id | version_id | reference_id | current_state_id | current_approver | approver_type | current_status_id | data_json |  | update_date |  |  |  |  |  |  |  |  |
| 1 | 1 | 4444 | 10001 | 123 | user | 10001 | {"documentName": "", "documentType": "", "remark": "", ...} |  | 2025-07-22T10:00:00.000Z |  |  |  |  |  |  |  |  |
| 2 | 1 | 2222 | 10005 | 2 | group | 10006 | {"documentName": "", "documentType": "", "remark": "", ...} |  | 2025-07-22T10:05:00.000Z |  |  |  |  |  |  |  |  |
| 3 | 2 | 5555 | 20002 | 3 | group | 20002 | {"documentName": "", "documentType": "", "remark": "", ...} |  | 2025-07-25T10:10:00.000Z |  |  |  |  |  |  |  |  |
| workflow_history |  |  |  |  |  |  |  |  |  |  |  | 25/05/2026 |  |  |  |  |  |
| history_id | version_id | transaction_id | old_state_id | old_status_id | new_state_id | new_status_id | event_data_json |  | event | create_by | create_date | create_by_name |  |  |  |  |  |
| 1 | 1 | 1 | 10001 | 10001 | 10001 | 10001 | {"userId": "123", "remark": ""} |  | save | 123 | 2025-07-22T10:00:00.000Z | admin admin |  |  |  |  |  |
| 2 | 1 | 2 | 10001 | 10001 | 10002 | 10002 | {"userId": "111", "remark": "test submit"} |  | submit | 111 | 2025-07-22T10:05:00.000Z | admin admin |  |  |  |  |  |
| 3 | 1 | 2 | 10002 | 10002 | 10004 | 10004 | {"userId": "222", "remark": "อนุมัติตาม role"} |  | approve | 222 | 2025-07-25T10:10:00.000Z | admin admin |  |  |  |  |  |
| 4 | 1 | 2 | 10004 | 10004 | 10005 | 10006 | {"userId": "333", "remark": ""} |  | approve | 333 | 2025-07-26T10:15:00.000Z | admin admin |  |  |  |  |  |
| 5 | 2 | 3 | 20001 | 20001 | 20002 | 20002 | {"userId": "20", "remark": ""} |  | submit | 20 | 2025-07-22T10:20:00.000Z | admin admin |  |  |  |  |  |
| workflow_group |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| group_id | group_name | approver_type |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | FC | group |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | someFC | group |  |  |  |  |  |  |  |  |  |  | @Entity("workflow_group_map")<br>export class WorkflowGroupMap {<br>    @PrimaryGeneratedColumn({ name: "group_map_id" })<br>    groupMapId: number;<br><br>    @Column({ name: "group_id", type: "int" })<br>   groupId: number;<br><br>    @Column({ name: "map_table", type: "varchar", length: 50 })<br>   mapTable: string;<br><br>    @Column({ name: "map_column", type: "varchar", length: 50 })<br>   mapColumn: string;<br><br>    @Column({ name: "map_key", type: "varchar", length: 50 })<br>   mapKey: string;<br>} |  |  |  |  |
| 3 | OPT | group |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 4 | evaluate | group |  |  |  |  |  |  |  |  |  |  |  |  |  |  | @Entity("workflow_group")<br>export class WorkflowGroup {<br>    @PrimaryGeneratedColumn({ name: "group_id" })<br>    groupId: number;<br><br>    @Column({ name: "group_name", type: "varchar", length: 50 })<br>   groupName: string;<br><br>    @Column({ name: "approver_type", type: "varchar", length: 50 })<br>   approverType: string;<br>} |
| 5 | ส่งเสริม | group |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| workflow_group_map |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| group_map_id | group_id | map_table | map_column | map_key |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 |  | groupId | 20 | ถ้าไม่ระบุ map table ใช้ การตรวจสอบจาก field ที่มีของ user จาก map_column |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | 2 |  | userId | 123 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 | 2 |  | userId | 222 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 4 | 2 |  | userId | 333 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 5 | 3 |  | groupId | 30 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 6 | 3 |  | groupId | 40 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 7 | 4 |  | groupId | 51 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 8 | 4 |  | groupId | 52 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 9 | 4 |  | groupId | 17 |  |  |  |  |  |  |  |  |  |  |  |  | @Entity("workflow_route")<br>export class WorkflowRoute {<br>    @PrimaryGeneratedColumn({ name: "route_id" })<br>    routeId: number;<br><br>    @Column({ name: "version_id", type: "varchar", length: 50 })<br>    versionId: string;<br><br>    @Column({ name: "from_state_id", type: "varchar", length: 100 })<br>    fromStateId: string;<br><br>    @Column({ name: "event", type: "varchar", length: 100 })<br>    event: string;<br><br>    @Column({ name: "to_state_id", type: "varchar", length: 100 })<br>    toStateId: string;<br>	<br>	@Column({ name: "to_status_id", type: "varchar", length: 100 })<br>    toStatusId: string;<br><br>    @Column({ name: "condition_json", type: "json", nullable: true })<br>    conditionJson: Record<string, any>;<br><br>    @Column({ name: "approver_type", type: "varchar", length: 100 })<br>    approverRoleId: string;<br><br>    @Column({ name: "approver", type: "varchar", length: 100 })<br>    approver: string;<br>} |
| 10 | 4 |  | groupId | 35 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 11 | 4 |  | groupId | 5 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 12 | 5 | v_fml_responsible | position |  | ต้องเป็น view ที่สามารถ where ด้วย user_id หรือ group_id ได้ |  |  |  |  |  |  |  | @Entity("workflow_state")<br>export class WorkflowState {<br>    @PrimaryColumn({ name: "state_id", type: "varchar", length: 50 })<br>    stateId: string;<br><br>    @Column({ name: "state_name", type: "varchar", length: 100 })<br>    stateName: string;<br>} |  |  |  |  |
| 13 | 5 | v_fml_responsible | position |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| workflow_route |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| route_id | version_id | from_state_id | event | to_state_id | seq | to_status_id | condition_json |  | approver_type | group_id | email_id |  |  |  |  |  |  |
| 1 | 1 | 10001 | save | 10001 | 1 | 10001 |  |  | user |  |  |  |  |  |  |  |  |
| 2 | 1 | 10001 | submit | 10002 | 1 | 10002 |  |  | group | 2 | 10001 |  |  |  |  |  |  |
| 3 | 1 | 10002 | approve | 10003 | 1 | 10003 | {"field": "amount", "operator": "<", "value": 1000} |  | group | 1 | 10002 |  |  |  |  |  |  |
| 4 | 1 | 10002 | approve | 10004 | 2 | 10004 | {"field": "amount", "operator": ">=", "value": 1000} |  | group | 3 | 10002 |  |  |  |  |  |  |
| 5 | 1 | 10004 | approve | 10005 | 1 | 10005 | {"field": "positionLevel", "operator": ">", "value": 210} , {"field": "amount", "operator": ">=", "value": 1000} |  | group | ... | 10003 |  |  |  |  |  |  |
| 6 | 1 | 10004 | approve | 10005 | 2 | 10006 | {"field": "positionLevel", "operator": "=", "value": 210} , {"field": "amount", "operator": ">=", "value": 1000} |  | group | ... |  |  |  |  |  |  |  |
| 7 | 1 | 10004 | approve | 10005 | 3 | 10007 | {"field": "positionLevel", "operator": "<", "value": 210} , {"field": "amount", "operator": "<", "value": 1000} |  | group | ... |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  | @Entity("workflow_status")<br>export class WorkflowStatus {<br>    @PrimaryColumn({ name: "status_id", type: "varchar", length: 50 })<br>    statusId: string;<br><br>    @Column({ name: "status_name", type: "varchar", length: 100 })<br>    statusName: string;<br>} |  |  |  |  |
| workflow_state |  |  | workflow_status |  |  | workflow_event |  |  |  |  |  |  |  |  |  |  |  |
| state_id | state_name | version_id | status_id | status_name | version_id | event | event_name |  |  |  |  |  |  |  |  |  |  |
| 10001 | initial | 1 | 10001 | รอผู้สร้างเอกสาร : ดำเนินการ | 1 | save | Save |  |  |  |  |  |  |  |  |  | @Entity("workflow_event")<br>export class WorkflowEvent {<br>    @PrimaryColumn({ name: "event_id", type: "varchar", length: 50 })<br>    eventId: string;<br><br>    @Column({ name: "event_name", type: "varchar", length: 100 })<br>    eventName: string;<br>} |
| 10002 | approve1 | 1 | 10002 | รอผูู้อนุมัติลำดับที่ 1 : ดำเนินการ | 1 | submit | Submit |  |  |  |  |  |  |  |  |  |  |
| 10003 | approve2 | 1 | 10003 | รอผูู้อนุมัติลำดับที่ 2 : ดำเนินการ | 1 | approve | Approve |  |  |  |  |  |  |  |  |  |  |
| 10004 | approve3 | 1 | 10004 | รอผูู้อนุมัติลำดับที่ 3 : ดำเนินการ | 1 | reject | Reject |  |  |  |  |  |  |  |  |  |  |
| 10005 | approve4 | 1 | 10005 | รอผูู้อนุมัติลำดับที่ 4 : ดำเนินการ level > 210 | 1 | cancel | Cancel |  |  |  |  |  |  |  |  |  |  |
| 10099 | finish | 1 | 10006 | รอผูู้อนุมัติลำดับที่ 4 : ดำเนินการ level = 210 | 1 | sendback | Send Back |  |  | workflow |  |  |  |  |  |  |  |
| 20001 | initial | 2 | 10007 | รอผูู้อนุมัติลำดับที่ 4 : ดำเนินการ level < 210 | 2 |  |  |  |  | workflow_id | workflow_name |  |  |  |  |  |  |
| 20002 | approve1 | 2 | 10099 | เสร็จสิ้นดำเนินการ | 2 |  |  |  |  | 1 | workflow subarea |  | @Entity("workflow_version")<br>export class WorkflowVersion {<br>    @PrimaryGeneratedColumn({ name: "version_id" })<br>    version_id: number;<br><br>    @Column({ name: "workflow_id", type: "varchar", length: 50 })<br>    workflowId: string;<br><br>    @Column({ name: "initial_state_id", type: "varchar", length: 100 })<br>    initialStateId: string;<br>	<br>	@Column({ name: "initial_status_id", type: "varchar", length: 100 })<br>    initialStatusId: string;<br><br>    @Column({ name: "end_state_id", type: "varchar", length: 100 })<br>    endStateId: string;<br>	<br>	@Column({ name: "end_status_id", type: "varchar", length: 100 })<br>    endStatusId: string;<br><br>    @Column({ name: "description", type: "varchar", length: 100, nullable: true })<br>    description: string;<br>} |  |  |  |  |
| 20003 | approve2 | 2 | 20001 | รอผู้สร้างเอกสาร : ดำเนินการ | 2 |  |  |  |  | 2 | workflow bellinee |  |  |  |  |  | @Entity("workflow")<br>export class Workflow {<br>    @PrimaryColumn({ name: "workflow_id", type: "varchar", length: 50 })<br>    workflowId: string;<br><br>    @Column({ name: "workflow_name", type: "varchar", length: 100 })<br>    workflowName: string;<br>} |
| 20099 | finish | 2 | 20002 | รอผูู้อนุมัติลำดับที่ 1 : ดำเนินการ | 2 |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | ... | ... |  |  |  |  |  |  |  |  |  |  |  |  |  |
| workflow_version |  |  |  |  |  |  |  | 25/05/2026 |  |  |  |  |  |  |  |  |  |
| version_id | workflow_id | initial_state_id | initial_status_id | end_state_id | end_status_id | description | update_date | url_main | url_param_mapping |  |  |  |  |  |  |  |  |
| 1 | 1 | 10001 | 10001 | 10001 | 10001 | subarea |  | /sbp/onboarding/detail/?processId={referenceId}&stepId={stepId} | {"stepId": {"table": "onboarding_master_workflow_state_to_step_mapping", "matchValue": "currentStateId", "matchColumn": "wf_state_id", "returnColumn": "onboarding_step_id"}} |  |  |  |  |  |  |  |  |
| 2 | 2 | 20001 | 20001 | 20001 | 20001 | bellinee |  | /sbp/investor-sbp-application/short/?applicantsId={referenceId}&investorUsersId={investorUsersId} | {"investorUsersId": {"table": "applicants", "matchValue": "referenceId", "matchColumn": "id", "returnColumn": "investor_users_id"}} |  |  |  |  |  |  |  |  |
| workflow_approver |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | @Entity("workflow_approver")<br>export class WorkflowApprover {<br>	@PrimaryGeneratedColumn({ name: "approver_id" })<br>    approverId: number;<br>	<br>    @Column({ name: "transaction_id", type: "int" })<br>    transactionId: number;<br><br>    @Column({ name: "current_approver", type: "int" })<br>    workflowName: number;<br>	<br>	@Column({ name: "approver_type", type: "varchar", length: 50 })<br>    approverType: string;<br>	<br>	@Column({ name: "state_id", type: "int" })<br>    stateId: number;<br>	<br>	@Column({ name: "approve_seq", type: "int" })<br>    approveSeq: number;<br>	<br>	@Column({ name: "create_date", type: "timestamptz", default: () => "CURRENT_TIMESTAMP" })<br>    createDate: Date;<br>	<br>	@Column({ name: "approve_date", type: "timestamptz", default: () => "CURRENT_TIMESTAMP" })<br>    approveDate: Date;<br>	<br>	@Column({ name: "approve_event", type: "varchar", length: 50 })<br>    approveEvent: string;<br>	<br>	@Column({ name: "remark", type: "varchar", length: 500 })<br>    remark: string;<br>	<br>} |
| approver_id | version_id | transaction_id | current_approver | approver_type | state_id | approve_seq | create_date |  | approve_date | approve_event | remark |  |  |  |  |  |  |
| 1 | 1 | 1 | 123 | user | 10001 | 1 | 2025-07-22T10:00:00.000Z |  |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 2 | 222 | user | 10002 | 1 | 2025-07-22T10:00:00.000Z |  | 2025-07-25T10:10:00.000Z | approve | test |  |  |  |  |  |  |
| 3 | 1 | 2 | 444 | user | 10005 | 1 | 2025-07-26T10:15:00.000Z |  |  |  |  |  |  |  |  |  |  |
| workflow_part |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| part_id | version_id | part_name | part_seq |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | short-application-information | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | 1 | short-application-address | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 | 1 | short-application-education | 3 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 4 | 1 | short-application-file-attach | 4 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 5 | 1 | short-application-action | 5 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| workflow_part_display |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| state_id | part_id | part_display_type | owner_type | group_id |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10001 | 1 | WRTIE | user |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10001 | 2 | WRTIE | user |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10001 | 3 | WRTIE | user |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10001 | 5 | WRTIE | user |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10002 | 1 | READ | group | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10002 | 2 | READ | group | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10002 | 3 | READ | group | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10002 | 4 | WRTIE | group | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 10002 | 5 | WRTIE | group | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | workflow_id | id เป็น key สำหรับระบุว่า workflow ที่ต้องการเป็น id อะไร |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | workflow_name | ชื่อคำอธิบายว่า workflow สำหรับทำอะไร |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_version |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | version_id | running auto generate  ใช้เป็น key เพื่อระบุว่า version นี้คือ workflow อะไร |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | workflow_id | map กับข้อมูล workflow_id ใน table workflow สำหรับระบุ id ของ workflow |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | initial_state_id | map กับข้อมูล state_id ใน table workflow_state สำหรับระบุ state เริ่มต้นของ workflow ใช้อ้างอิงตอน initializeWorkflow |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | end_state_id | map กับข้อมูล state_id ใน table workflow_state สำหรับระบุ state สิ้นสุดของ workflow |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | description | ระบุคำอธิบายของ version นั้นๆ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_state |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | state_id | running โดยปรับตาม version ที่สร้าง  เช่น ถ้าสร้างที่ version_id = 1 ให้ขึ้นต้นด้วย 1 จากนั้นต่อท้ายด้วย running 4 หลัก  จะได้ 10001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | state_name | ชื่ื่อคำอธิบาย state |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | version_id |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_status |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | status_id | running โดยปรับตาม version ที่สร้าง  เช่น ถ้าสร้างที่ version_id = 1 ให้ขึ้นต้นด้วย 1 จากนั้นต่อท้ายด้วย running 4 หลัก  จะได้ 10001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | status_name | ชื่ื่อคำอธิบาย status ใช้คู่กับ state โดย 1 state อาจมีได้มากกว่า 1 status |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | version_id |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_route |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | route_id | running auto generate |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | version_id | map กับข้อมูล version_id ใน table workflow_version สำหรับระบุ version_id ของ workflow ของ record นั้นๆ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | from_state_id | state เริ่มต้น |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | event | event ที่ดำเนินการ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | to_state_id | state ถัดไป |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | seq | ลำดับการตรวจสอบเงื่อนไข (ถ้ามีหลายเงื่อนไขที่ state เริ่มต้นเดียวกัน) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | condition_json | เงื่อนไขการตรวจสอบ จะโยงกับ field ที่ต้องระบุมาใน eventParam ที่ส่งเข้ามาด้วย  มี 3 field คือ field(ชื่อ field ที่ใช้ในการตรวจสอบ เช็คกับ eventParam)  ,  operator (เครื่องหมายที่ใช้ในการเปรียบเทียบ) , value (ค่าที่ใช้ในการเปรียบเทียบ) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | approver_type | ประเภทการอนุมัติ  ("user" อนุมัติโดย user คนเดียว , "group" อนุมัติโดย user ทั้งหมดที่อยู่ในกลุ่ม) |  |  |  |  |  |  |  |  |  | operator | == |  |  |  |  |
|  | group_id | map กับ group_id ใน table workflow_group_map สำหรับระบุกลุ่ม user ที่สามารอนุมัติได้ในขั้นตอนถัดไป |  |  |  |  |  |  |  |  |  |  | != |  |  |  |  |
|  | email_id | map กับ email_id ใน table email......  สำหรับระบุเมล์ที่จะทำการส่งหลังจากดำเนินการใน event ถ้าไม่ระบุ จะไม่มีการส่งเมล์ |  |  |  |  |  |  |  |  |  |  | > |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  | < |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  | >= |  |  |  |  |
| การใส่ config ภายใน table workflow_event |  |  |  |  |  |  |  |  |  |  |  |  | <= |  |  |  |  |
|  | event | ชื่อ event ที่ดำเนินการได้  จะมี default event ให้ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | event_name | ชื่อสำหรับแสดงผล |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_group |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | group_id | running |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | group_name | ชื่อกลุ่ม |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | approver_type | ประเภทการอนุมัติ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_group_map |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | group_map_id | running |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | group_id | map กับ group_id ใน table workflow_group_map ระบุ id ที่จะใส่สำหรับกำหนด group หรือ user ในกลุ่ม |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | map_table | กำหนดตารางในการ map ข้อมูล |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | map_column | กำหนด column ในการ map ข้อมูล |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | map_key | กำหนด key ที่ใช้ในการ map ข้อมูล |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_part |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | part_id | id |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | version_id | map กับข้อมูล version_id ใน table workflow_version สำหรับระบุ version_id ของ workflow ของ part |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | part_name | ชื่อ part หรือใช้ชื่อ component ที่ map กับหน้าจอเพื่อให้สามารถแสดงผลได้ถูกต้อง |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | part_seq | กำหนดลำดับการแสดงผล |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| การใส่ config ภายใน table workflow_part_display    (ต้องการให้แสดงผลเท่านั้นถึงจะระบุใน part_display ถ้าไม่ต้องการแสดงผล ไม่ต้องระบุ) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | state_id | map กับข้อมูล state_id ใน table workflow_state สำหรับระบุ state คู่กับ part ที่ต้องการแสดง |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | part_id | id ของ part ที่ต้องการผูกกับ state |  |  |  |  |  |  |  |  |  | part_display_type | READ | ดูได้อย่างเดียว แก้ไขไม่ได้ |  |  |  |
|  | part_display_type | กำหนดประเภทของการแสดงผล |  |  |  |  |  |  |  |  |  |  | WRITE | ดููและแก้ไขได้ |  |  |  |
|  | owner_type | ประเภทการมองเห็น  ("user" มองเห็นโดย user คนเดียว , "group" มองเห็นโดย user ทั้งหมดที่อยู่ในกลุ่ม) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | group_id | map กับ group_id ใน table workflow_group_map สำหรับระบุกลุ่ม user ที่สามารถมองเห็น part นี้ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

## Mermaid seq

| sequenceDiagram<br>    participant UserApp as แอปพลิเคชันผู้ใช้งานภายนอก<br>    participant Engine as คลาส ApprovalWorkflowEngine<br>    participant Database as ฐานข้อมูล<br><br>    %% ส่วนเริ่มต้น Workflow ใหม่<br>    UserApp->>Engine: 1. เริ่มต้น Workflow ใหม่ (initialiseWorkflow())<br>    activate Engine<br>    Engine->>Engine: 1.1 สร้าง workflowId และ transactionId ใหม่<br>    Engine->>Database: 1.2 บันทึก Context เริ่มต้นใน DB (workflowId, transactionId)<br>    activate Database<br>    Database-->>Engine: 1.3 ยืนยันการบันทึก<br>    deactivate Database<br>    Engine-->>UserApp: 1.4 ส่งคืน workflowId และ transactionId ที่สร้างขึ้น<br>    deactivate Engine<br><br>    %% การประมวลผล Workflow หลัก (การ Trigger Event)<br>    alt Trigger Event (เหตุการณ์ถูกต้อง)<br>        UserApp->>Engine: 2. Trigger Event (triggerEvent(workflowId, transactionId, event, eventData))<br>        activate Engine<br>        Engine->>Database: 2.1 สอบถามสถานะ Context ปัจจุบันจาก DB (workflowId, transactionId)<br>        activate Database<br>        Database-->>Engine: 2.2 ส่งคืนสถานะ Context<br>        deactivate Database<br>        Engine->>Database: 2.3 สอบถามกฎจาก DB ตามสถานะปัจจุบัน (workflowId)<br>        activate Database<br>        Database-->>Engine: 2.4 ส่งคืนกฎ<br>        deactivate Database<br>        Engine->>Engine: 2.5 ตรวจสอบ Event และกำหนดสถานะถัดไป<br>        Engine->>Database: 2.6 บันทึกการเปลี่ยนแปลง Context ใน DB (workflowId, transactionId)<br>        activate Database<br>        Database-->>Engine: 2.7 ยืนยันการบันทึก<br>        deactivate Database<br>        Engine->>Database: 2.8 บันทึกรายการประวัติใน DB (workflowId, transactionId)<br>        activate Database<br>        Database-->>Engine: 2.9 ยืนยันการบันทึก<br>        deactivate Database<br>        Engine-->>UserApp: 2.10 ประมวลผล Event สำเร็จ (หรือ Error)<br>        deactivate Engine<br>    else Invalid Event (เหตุการณ์ไม่ถูกต้อง)<br>        UserApp->>Engine: 2. Trigger Event (triggerEvent(workflowId, transactionId, event, eventData))<br>        activate Engine<br>        Engine->>Database: 2.1 สอบถามสถานะ Context ปัจจุบันจาก DB (workflowId, transactionId)<br>        activate Database<br>        Database-->>Engine: 2.2 ส่งคืนสถานะ Context<br>        deactivate Database<br>        Engine->>Database: 2.3 สอบถามกฎจาก DB ตามสถานะปัจจุบัน (workflowId)<br>        activate Database<br>        Database-->>Engine: 2.4 ส่งคืนกฎ (หรือไม่มีกฎที่ตรงกัน)<br>        deactivate Database<br>        Engine->>Engine: 2.5 ตรวจสอบ Event (เช่น Event ไม่ได้รับอนุญาตในสถานะปัจจุบัน)<br>        Engine-->>UserApp: 2.6 ส่งคืน Error (เช่น "Event ไม่ได้รับอนุญาตในสถานะปัจจุบัน")<br>        deactivate Engine<br>    end<br><br>    %% การเข้าถึงข้อมูล / Getters (แอปพลิเคชันผู้ใช้งานสอบถามสถานะ Engine)<br>    UserApp->>Engine: 3. ดึงผู้มีอำนาจอนุมัติปัจจุบัน (getCurrentApprover(workflowId, transactionId))<br>    activate Engine<br>    Engine->>Database: 3.1 สอบถามผู้มีอำนาจอนุมัติจาก DB (workflowId, transactionId)<br>    activate Database<br>    Database-->>Engine: 3.2 ส่งคืนผู้มีอำนาจอนุมัติ<br>    deactivate Database<br>    Engine-->>UserApp: 3.3 ส่งคืนผู้มีอำนาจอนุมัติปัจจุบัน<br>    deactivate Engine<br><br>    UserApp->>Engine: 4. ดึง Event ที่สามารถทำได้ (getAvailableEvents(workflowId, transactionId))<br>    activate Engine<br>    Engine->>Database: 4.1 สอบถามสถานะ Context ปัจจุบันจาก DB (workflowId, transactionId)<br>    activate Database<br>    Database-->>Engine: 4.2 ส่งคืนสถานะ Context<br>    deactivate Database<br>    Engine->>Database: 4.3 สอบถาม Event ที่ทำได้จาก DB ตามสถานะปัจจุบัน (workflowId)<br>    activate Database<br>    Database-->>Engine: 4.4 ส่งคืนรายการ Event<br>    deactivate Database<br>    Engine-->>UserApp: 4.5 ส่งคืน Event ที่สามารถทำได้<br>    deactivate Engine<br><br>    UserApp->>Engine: 5. ดึงประวัติ (getHistory(workflowId, transactionId))<br>    activate Engine<br>    Engine->>Database: 5.1 ดึงบันทึกประวัติทั้งหมดจาก DB (workflowId, transactionId)<br>    activate Database<br>    Database-->>Engine: 5.2 ส่งคืนข้อมูลประวัติ<br>    deactivate Database<br>    Engine-->>UserApp: 5.3 ส่งคืนข้อมูลประวัติ<br>    deactivate Engine<br><br>    UserApp->>Engine: 6. ดึง Context (getContext(workflowId, transactionId))<br>    activate Engine<br>    Engine->>Database: 6.1 ดึงข้อมูล Context ทั้งหมดจาก DB (workflowId, transactionId)<br>    activate Database<br>    Database-->>Engine: 6.2 ส่งคืนข้อมูล Context<br>    deactivate Database<br>    Engine-->>UserApp: 6.3 ส่งคืนข้อมูล Context<br>    deactivate Engine<br><br>    UserApp->>Engine: 7. ดึง Flow ที่รอการดำเนินการ (getPendingFlowsForUser(userId))<br>    activate Engine<br>    Engine->>Database: 7.1 สอบถาม Context ที่รอการดำเนินการสำหรับ userId (userId, กลุ่มผู้ใช้งาน, ระดับตำแหน่ง)<br>    activate Database<br>    Database-->>Engine: 7.2 ส่งคืนรายการ Context ที่รอการดำเนินการ<br>    deactivate Database<br>    Engine-->>UserApp: 7.3 ส่งคืนรายการ Flow ที่รอการดำเนินการ<br>    deactivate Engine | col2 | sequenceDiagram<br>    participant UserApp as OtherApp<br>    participant Engine as ApprovalWorkflowEngine<br>    participant Database as Database<br><br>    %% ส่วนเริ่มต้น Workflow ใหม่<br>    UserApp->>Engine: 1. เริ่มต้น Workflow ใหม่ <br>    activate Engine<br>    note right of UserApp: initializeWorkflow(versionId,transactionPk)<br>    %%Engine->>Engine: สร้าง workflowId และ transactionId ใหม่<br>    note over Engine: create transaction<br>    note over Engine: try<br>    Engine->>Database: บันทึก Transaction เริ่มต้นใน DB <br>    activate Database<br>    note right of Engine: saveTransaction(versionId,transactionPk)<br>    Database-->>Engine: ยืนยันการบันทึก<br>    deactivate Database<br>    alt Create Success<br>        note over Engine: commit<br>        Engine-->>UserApp: ส่งคืน workflowId และ transactionId ที่สร้างขึ้น<br>    else Error<br>        note over Engine: catch<br>        note over Engine: rollback<br>        Engine-->>UserApp: Return Exception<br>    end<br>    deactivate Engine<br><br>    %% การประมวลผล Workflow หลัก (การ Trigger Event)<br>    <br>    UserApp->>Engine: 2. Trigger Event <br>    activate Engine<br>    note right of UserApp: triggerEvent(versionId, transactionId, <br/>event, eventParam,remark,userId)<br>    Engine->>Database: ดึงสถานะและสิทธิ์ Transaction ปัจจุบันจาก DB <br>    activate Database<br>    note right of Engine: checkTransaction(versionId, transactionId, userId)<br>    Database-->>Engine: ส่งคืนสถานะและสิทธิ์ของ Transaction<br>    deactivate Database<br>    Engine->>Engine: ตรวจสอบ transaction และสิทธิ์การอนุมัติ<br>    alt Trigger Event (เหตุการณ์ถูกต้อง)<br>        Engine->>Database: ดึง route จาก DB ตามสถานะปัจจุบัน (versionId)<br>        activate Database<br>        note right of Engine: getRoute(versionId, transactionId, event)<br>        Database-->>Engine: ส่งคืน route <br>        deactivate Database<br>        Engine->>Engine: ตรวจสอบ Event และกำหนดสถานะถัดไป<br>        alt Valid Event (เหตุการณ์ถูกต้อง)<br>            note over Engine: create transaction<br>            note over Engine: try<br>            Engine->>Database: บันทึกการเปลี่ยนแปลง Transaction ใน DB <br>            activate Database<br>            note right of Engine: saveTransaction(versionId, transactionId,<br/> nextState, nextApprover)<br>            Database-->>Engine: ยืนยันการบันทึก<br>            deactivate Database<br>            alt Save Success<br>                Engine->>Database: บันทึกรายการประวัติใน DB<br>                activate Database<br>                note right of Engine: saveHistory(versionId, transactionId,<br/> currentState, nextState, userId)<br>                Database-->>Engine: ยืนยันการบันทึก<br>                deactivate Database<br>                alt Create Success<br>                    Engine-->>UserApp: ประมวลผล Event สำเร็จ (หรือ Error)<br>                else Error<br>                    note over Engine: catch<br>                    note over Engine: rollback<br>                    Engine-->>UserApp: Return Exception<br>                end<br>            else Error<br>                note over Engine: catch<br>                note over Engine: rollback<br>                Engine-->>UserApp: Return Exception<br>            end<br>        else Invalid Event (เหตุการณ์ไม่ถูกต้อง)<br>            Engine-->>UserApp: ส่งคืน Error "Event ไม่ได้รับอนุญาตในสถานะปัจจุบัน"<br>        end<br>    else Invalid Authorize (เหตุการณ์ไม่ถูกต้อง)<br>        Engine-->>UserApp: ส่งคืน Error "User ไม่ได้รับอนุญาตในสถานะปัจจุบัน"<br>        deactivate Engine<br>    end<br><br>    %% การเข้าถึงข้อมูล / Getters (แอปพลิเคชันผู้ใช้งานดึงสถานะ Engine)<br>    UserApp->>Engine: 3. ตรวจสอบสิทธิ์การอนุมัติ<br>    activate Engine<br>    note right of UserApp: getPermissionEvent(versionId, transactionId, userId)<br>    Engine->>Database: ดึงผู้มีอำนาจอนุมัติจาก DB <br>    activate Database<br>    note right of Engine: getApprover(versionId, transactionId)  <br>    Database-->>Engine: ส่งคืนผู้มีอำนาจอนุมัติ<br>    deactivate Database<br>    Engine-->>Engine: ตรวจสอบสิทธิ์ของ user<br>    note right of Engine: checkEvent(userId , listUser)<br>    alt Valid Permission (มีสิทธิ์ในการดำเนินการ)<br>        Engine-->>Database: ตรวจสอบเรื่อง Event ที่สามารถดำเนินการได้<br>        activate Database<br>        note right of Engine: getEvent(versionId, transactionId)<br>        Database-->>Engine: ส่งคืน Event ที่สามารถดำเนินการ<br>        deactivate Database<br>        Engine-->>UserApp: ส่งคืนผลการตรวจสอบ<br>    else Invalid Permission (ไม่มีสิทธิ์ในการดำเนินการ)<br>        Engine-->>UserApp: ส่งคืนผลการตรวจสอบ<br>    end<br>    deactivate Engine<br><br>    UserApp->>Engine: 4. ดึงประวัติ<br>    activate Engine<br>    note right of UserApp: getHistory(versionId, transactionId)<br>    Engine->>Database: ดึงบันทึกประวัติทั้งหมดจาก DB (versionId, transactionId)<br>    activate Database<br>    note right of Engine: getTransactionHistory(versionId, transactionId)<br>    Database-->>Engine: ส่งคืนข้อมูลประวัติ<br>    deactivate Database<br>    Engine-->>UserApp: ส่งคืนข้อมูลประวัติ<br>    deactivate Engine<br><br>    UserApp->>Engine: 5. ดึง Transaction<br>    activate Engine<br>    note right of UserApp: getTransaction(versionId, transactionPk)<br>    Engine->>Database: ดึงข้อมูล Transaction ทั้งหมดจาก DB (versionId, transactionPk)<br>    activate Database<br>    note right of Engine: getTransaction(versionId, transactionPk)<br>    Database-->>Engine: ส่งคืนข้อมูล Transaction<br>    deactivate Database<br>    Engine-->>UserApp: ส่งคืนข้อมูล Transaction<br>    deactivate Engine<br><br>    UserApp->>Engine: 6. ดึง Flow ที่รอการดำเนินการ<br>    activate Engine<br>    note right of UserApp: getPendingFlowsForUser(userData)<br>    Engine->>Database: ดึง Transaction ที่รอการดำเนินการสำหรับ userId<br>    activate Database<br>    note right of Engine: getPendingWorkflowByUserId(userId)<br>    Database-->>Engine: ส่งคืนรายการ Transaction ที่รอการดำเนินการ<br>    deactivate Database<br>    activate Database<br>    Engine->>Database: ดึง Transaction ที่รอการดำเนินการสำหรับ กลุ่มผู้ใช้งาน<br>    note right of Engine: getPendingWorkflowByGroup(กลุ่มผู้ใช้งาน)<br>    Database-->>Engine: ส่งคืนรายการ Transaction ที่รอการดำเนินการ<br>    deactivate Database<br>    activate Database<br>    Engine->>Database: ดึง Transaction ที่รอการดำเนินการสำหรับ ระดับตำแหน่ง<br>    note right of Engine: getPendingWorkflowByRole(ระดับตำแหน่ง)<br>    Database-->>Engine: ส่งคืนรายการ Transaction ที่รอการดำเนินการ<br>    deactivate Database<br>    Engine-->>Engine: list workflow ทั้งหมดและจัดรูปแบบ<br>    Engine-->>UserApp: ส่งคืนรายการ workflow ที่รอการดำเนินการ<br>    deactivate Engine<br><br>    UserApp->>Engine: 7. ดึง Flow ที่ user มีสิทธิ์อยู่ใน Flow ดำเนินการ<br>    activate Engine<br>    note right of UserApp: getWorkFlowForUser(userData)<br>    Engine->>Database: ดึง Transaction ที่ user มีสิทธิ์สำหรับ userId<br>    activate Database<br>    note right of Engine: getWorkflowByUserId(userId)<br>    Database-->>Engine: ส่งคืนรายการ Transaction ที่ user มีสิทธิ์<br>    deactivate Database<br>    activate Database<br>    Engine->>Database: ดึง Transaction ที่ user มีสิทธิ์สำหรับ กลุ่มผู้ใช้งาน<br>    note right of Engine: getWorkflowByGroup(กลุ่มผู้ใช้งาน)<br>    Database-->>Engine: ส่งคืนรายการ Transaction ที่ user มีสิทธิ์<br>    deactivate Database<br>    activate Database<br>    Engine->>Database: ดึง Transaction ที่ user มีสิทธิ์สำหรับ ระดับตำแหน่ง<br>    note right of Engine: getWorkflowByRole(ระดับตำแหน่ง)<br>    Database-->>Engine: ส่งคืนรายการ Transaction ที่ user มีสิทธิ์<br>    deactivate Database<br>    Engine-->>Engine: list workflow ทั้งหมดและจัดรูปแบบ<br>    Engine-->>UserApp: ส่งคืนรายการ workflow ที่ user มีสิทธิ์<br>    deactivate Engine |
|---|---|---|

---

## temp

| @Entity("workflow_approver_role") | col2 | col3 | col4 | col5 | col6 | col7 | col8 | col9 | model WorkflowTransaction { |
|---|---|---|---|---|---|---|---|---|---|
| export class WorkflowApproverRole { |  |  |  |  |  |  |  |  | transactionId   Int     @id @map("transaction_id") @default(autoincrement()) |
| @PrimaryColumn({ name: "role_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  | versionId      String  @map("version_id") @db.VarChar(50) |
| roleId: string; |  |  |  |  |  |  |  |  | referenceId      String  @map("reference_id") @db.VarChar(50) |
|  |  |  |  |  |  |  |  |  | currentStateId  String  @map("current_state_id") @db.VarChar(100) |
| @Column({ name: "role_name", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  | currentState    WorkflowState @relation("TransactionCurrentState", fields: [currentStateId], references: [stateId]) |
| roleName: string; |  |  |  |  |  |  |  |  | currentApprover String? @map("current_approver") @db.VarChar(100) |
|  |  |  |  |  |  |  |  |  | approverType String? @map("approver_type") @db.VarChar(100) |
| @Column({ name: "approver_type", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  | dataJson        Json?   @map("data_json") |
| approverType: string; // เช่น 'user', 'group', 'position' |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | @@unique([transactionId, versionId]) |
| // ความสัมพันธ์ One-to-Many กับ WorkflowRoute (หนึ่ง Role มีได้หลายเส้นทาง) |  |  |  |  |  |  |  |  | @@map("workflow_transaction") |
| @OneToMany(() => WorkflowRoute, (route) => route.approverRole) |  |  |  |  |  |  |  |  | } |
| routes: WorkflowRoute[]; |  |  |  |  |  |  |  |  |  |
| } |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | model WorkflowHistory { |
| // Entity สำหรับตาราง workflow_template |  |  |  |  |  |  |  |  | historyId       Int       @id @map("history_id") @default(autoincrement()) |
| // นี่คือแม่แบบหลักของ Workflow |  |  |  |  |  |  |  |  | versionId      String    @map("version_id") @db.VarChar(50) |
| @Entity("workflow_template") |  |  |  |  |  |  |  |  | transactionId   String    @map("transaction_id") @db.VarChar(50) |
| export class WorkflowTemplate { |  |  |  |  |  |  |  |  | oldStateId      String    @map("old_state_id") @db.VarChar(100) |
| @PrimaryGeneratedColumn({ name: "template_id" }) |  |  |  |  |  |  |  |  | oldState        WorkflowState @relation("HistoryOldState", fields: [oldStateId], references: [stateId]) |
| templateId: number; |  |  |  |  |  |  |  |  | eventName       String    @map("event_name") @db.VarChar(100) |
|  |  |  |  |  |  |  |  |  | newStateId      String    @map("new_state_id") @db.VarChar(100) |
| @Column({ name: "template_name", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  | newState        WorkflowState @relation("HistoryNewState", fields: [newStateId], references: [stateId]) |
| templateName: string; |  |  |  |  |  |  |  |  | eventDataJson   Json?     @map("event_data_json") |
|  |  |  |  |  |  |  |  |  | actorId         String?   @map("actor_id") @db.VarChar(100) |
| @Column({ name: "description", type: "text", nullable: true }) |  |  |  |  |  |  |  |  | timestamp       DateTime  @default(now()) @map("timestamp") @db.Timestamptz(6) |
| description: string; |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | @@map("workflow_history") |
| // ความสัมพันธ์ One-to-Many กับ WorkflowTemplateStep (หนึ่งแม่แบบมีหลายขั้นตอน) |  |  |  |  |  |  |  |  | } |
| @OneToMany(() => WorkflowTemplateStep, (step) => step.template) |  |  |  |  |  |  |  |  |  |
| steps: WorkflowTemplateStep[]; |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  | model WorkflowRoute { |
| // ความสัมพันธ์ One-to-Many กับ WorkflowVersion (หนึ่งแม่แบบมีได้หลายเวอร์ชัน) |  |  |  |  |  |  |  |  | routeId         Int     @id @map("route_id") @default(autoincrement()) |
| @OneToMany(() => WorkflowVersion, (version) => version.workflowTemplate) |  |  |  |  |  |  |  |  | versionId      String  @map("version_id") @db.VarChar(50) |
| versions: WorkflowVersion[]; |  |  |  |  |  |  |  |  | fromStateId     String  @map("from_state_id") @db.VarChar(100) |
| } |  |  |  |  |  |  |  |  | fromState       WorkflowState @relation("RouteFromState", fields: [fromStateId], references: [stateId]) |
|  |  |  |  |  |  |  |  |  | eventTrigger    String  @map("event_trigger") @db.VarChar(100) |
| // Entity สำหรับตาราง workflow_template_step |  |  |  |  |  |  |  |  | toStateId       String  @map("to_state_id") @db.VarChar(100) |
| // ใช้กำหนดขั้นตอนและลำดับของ State ในแต่ละ Workflow Template |  |  |  |  |  |  |  |  | toState         WorkflowState @relation("RouteToState", fields: [toStateId], references: [stateId]) |
| @Entity("workflow_template_step") |  |  |  |  |  |  |  |  | conditionJson   Json?   @map("condition_json") |
| @Unique(["templateId", "stepOrder"]) |  |  |  |  |  |  |  |  | approverRole    String? @map("approver_role") @db.VarChar(100) |
| export class WorkflowTemplateStep { |  |  |  |  |  |  |  |  |  |
| @PrimaryGeneratedColumn({ name: "step_id" }) |  |  |  |  |  |  |  |  | @@map("workflow_route") |
| stepId: number; |  |  |  |  |  |  |  |  | } |
| @Column({ name: "template_id", type: "int" }) |  |  |  |  |  |  |  |  |  |
| templateId: number; |  |  |  |  |  |  |  |  | model WorkflowState { |
|  |  |  |  |  |  |  |  |  | stateId   String @unique @map("state_id") @db.VarChar(50) |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowTemplate |  |  |  |  |  |  |  |  | stateName String @map("state_name") @db.VarChar(100) |
| @ManyToOne(() => WorkflowTemplate, (template) => template.steps) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "template_id" }) |  |  |  |  |  |  |  |  | transactionAsCurrentState WorkflowTransaction[] @relation("TransactionCurrentState") |
| template: WorkflowTemplate; |  |  |  |  |  |  |  |  | historyAsOldState     WorkflowHistory[] @relation("HistoryOldState") |
|  |  |  |  |  |  |  |  |  | historyAsNewState     WorkflowHistory[] @relation("HistoryNewState") |
| @Column({ name: "state_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  | routeAsFromState      WorkflowRoute[]   @relation("RouteFromState") |
| stateId: string; |  |  |  |  |  |  |  |  | routeAsToState        WorkflowRoute[]   @relation("RouteToState") |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowState |  |  |  |  |  |  |  |  | @@map("workflow_state") |
| @ManyToOne(() => WorkflowState, (state) => state.templateSteps) |  |  |  |  |  |  |  |  | } |
| @JoinColumn({ name: "state_id" }) |  |  |  |  |  |  |  |  |  |
| state: WorkflowState; |  |  |  |  |  |  |  |  | model WorkflowVersion { |
|  |  |  |  |  |  |  |  |  | version_id         Int     @id @default(autoincrement()) |
| @Column({ name: "step_order", type: "int" }) |  |  |  |  |  |  |  |  | workflowId      String  @map("workflow_id") @db.VarChar(50) |
| stepOrder: number; |  |  |  |  |  |  |  |  | initialStateId     String  @map("initial_state_id") @db.VarChar(100) |
| } |  |  |  |  |  |  |  |  | endStateId     String  @map("end_state_id") @db.VarChar(100) |
|  |  |  |  |  |  |  |  |  | description    String? @map("description") @db.VarChar(100) |
| // Entity สำหรับตาราง workflow_version |  |  |  |  |  |  |  |  |  |
| // ใช้เก็บแต่ละเวอร์ชันของ Workflow (เช่น v1, v2) |  |  |  |  |  |  |  |  | @@map("workflow_version") |
| @Entity("workflow_version") |  |  |  |  |  |  |  |  | } |
| export class WorkflowVersion { |  |  |  |  |  |  |  |  |  |
| @PrimaryGeneratedColumn({ name: "version_id" }) |  |  |  |  |  |  |  |  |  |
| version_id: number; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "workflow_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| workflowId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "initial_state_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| initialStateId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "end_state_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| endStateId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "description", type: "varchar", length: 100, nullable: true }) |  |  |  |  |  |  |  |  |  |
| description: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "template_id", type: "int" }) |  |  |  |  |  |  |  |  |  |
| templateId: number; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowTemplate |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowTemplate, (template) => template.versions) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "template_id" }) |  |  |  |  |  |  |  |  |  |
| workflowTemplate: WorkflowTemplate; |  |  |  |  |  |  |  |  |  |
| } |  |  |  |  |  |  |  |  |  |
| // Entity สำหรับตาราง workflow_state |  |  |  |  |  |  |  |  |  |
| // ตัวนี้ทำหน้าที่เป็นสถานะของ Workflow (เช่น 'In Progress', 'Approved') |  |  |  |  |  |  |  |  |  |
| @Entity("workflow_state") |  |  |  |  |  |  |  |  |  |
| export class WorkflowState { |  |  |  |  |  |  |  |  |  |
| @PrimaryColumn({ name: "state_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| stateId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "state_name", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| stateName: string; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ One-to-Many กับ WorkflowTransaction (เป็น CurrentState) |  |  |  |  |  |  |  |  |  |
| @OneToMany(() => WorkflowTransaction, (transaction) => transaction.currentState) |  |  |  |  |  |  |  |  |  |
| transactionAsCurrentState: WorkflowTransaction[]; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ One-to-Many กับ WorkflowHistory (เป็น OldState) |  |  |  |  |  |  |  |  |  |
| @OneToMany(() => WorkflowHistory, (history) => history.oldState) |  |  |  |  |  |  |  |  |  |
| historyAsOldState: WorkflowHistory[]; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ One-to-Many กับ WorkflowHistory (เป็น NewState) |  |  |  |  |  |  |  |  |  |
| @OneToMany(() => WorkflowHistory, (history) => history.newState) |  |  |  |  |  |  |  |  |  |
| historyAsNewState: WorkflowHistory[]; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ One-to-Many กับ WorkflowRoute (เป็น FromState) |  |  |  |  |  |  |  |  |  |
| @OneToMany(() => WorkflowRoute, (route) => route.fromState) |  |  |  |  |  |  |  |  |  |
| routeAsFromState: WorkflowRoute[]; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ One-to-Many กับ WorkflowRoute (เป็น ToState) |  |  |  |  |  |  |  |  |  |
| @OneToMany(() => WorkflowRoute, (route) => route.toState) |  |  |  |  |  |  |  |  |  |
| routeAsToState: WorkflowRoute[]; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ One-to-Many กับ WorkflowTemplateStep |  |  |  |  |  |  |  |  |  |
| @OneToMany(() => WorkflowTemplateStep, (step) => step.state) |  |  |  |  |  |  |  |  |  |
| templateSteps: WorkflowTemplateStep[]; |  |  |  |  |  |  |  |  |  |
| } |  |  |  |  |  |  |  |  |  |
| // Entity สำหรับตาราง workflow_transaction |  |  |  |  |  |  |  |  |  |
| // ใช้เก็บข้อมูลการขอ (transaction) ที่เกิดขึ้นจริง |  |  |  |  |  |  |  |  |  |
| @Entity("workflow_transaction") |  |  |  |  |  |  |  |  |  |
| @Unique(["transactionId", "versionId"]) |  |  |  |  |  |  |  |  |  |
| export class WorkflowTransaction { |  |  |  |  |  |  |  |  |  |
| @PrimaryGeneratedColumn({ name: "transaction_id" }) |  |  |  |  |  |  |  |  |  |
| transactionId: number; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "version_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| versionId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "reference_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| referenceId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "current_state_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| currentStateId: string; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowState (current state) |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowState, (state) => state.transactionAsCurrentState) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "current_state_id" }) |  |  |  |  |  |  |  |  |  |
| currentState: WorkflowState; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ One-to-Many กับ WorkflowApprover |  |  |  |  |  |  |  |  |  |
| @OneToMany(() => WorkflowApprover, (approver) => approver.transaction) |  |  |  |  |  |  |  |  |  |
| approvers: WorkflowApprover[]; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "data_json", type: "json", nullable: true }) |  |  |  |  |  |  |  |  |  |
| dataJson: Record<string, any>; |  |  |  |  |  |  |  |  |  |
| } |  |  |  |  |  |  |  |  |  |
| // Entity สำหรับตาราง workflow_route |  |  |  |  |  |  |  |  |  |
| // ใช้กำหนดเส้นทางการเปลี่ยนสถานะจาก State หนึ่งไปยังอีก State หนึ่ง |  |  |  |  |  |  |  |  |  |
| @Entity("workflow_route") |  |  |  |  |  |  |  |  |  |
| export class WorkflowRoute { |  |  |  |  |  |  |  |  |  |
| @PrimaryGeneratedColumn({ name: "route_id" }) |  |  |  |  |  |  |  |  |  |
| routeId: number; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "version_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| versionId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "from_state_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| fromStateId: string; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowState (from state) |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowState, (state) => state.routeAsFromState) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "from_state_id" }) |  |  |  |  |  |  |  |  |  |
| fromState: WorkflowState; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "event_trigger", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| eventTrigger: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "to_state_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| toStateId: string; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowState (to state) |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowState, (state) => state.routeAsToState) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "to_state_id" }) |  |  |  |  |  |  |  |  |  |
| toState: WorkflowState; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "condition_json", type: "json", nullable: true }) |  |  |  |  |  |  |  |  |  |
| conditionJson: Record<string, any>; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "approver_role_id", type: "varchar", length: 100, nullable: true }) |  |  |  |  |  |  |  |  |  |
| approverRoleId: string; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowApproverRole |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowApproverRole, (role) => role.routes) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "approver_role_id" }) |  |  |  |  |  |  |  |  |  |
| approverRole: WorkflowApproverRole; |  |  |  |  |  |  |  |  |  |
| } |  |  |  |  |  |  |  |  |  |
| // Entity สำหรับตาราง workflow_history |  |  |  |  |  |  |  |  |  |
| // ใช้เก็บประวัติการเปลี่ยนแปลงสถานะของแต่ละ Transaction |  |  |  |  |  |  |  |  |  |
| @Entity("workflow_history") |  |  |  |  |  |  |  |  |  |
| export class WorkflowHistory { |  |  |  |  |  |  |  |  |  |
| @PrimaryGeneratedColumn({ name: "history_id" }) |  |  |  |  |  |  |  |  |  |
| historyId: number; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "version_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| versionId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "transaction_id", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| transactionId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "old_state_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| oldStateId: string; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowState (old state) |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowState, (state) => state.historyAsOldState) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "old_state_id" }) |  |  |  |  |  |  |  |  |  |
| oldState: WorkflowState; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "event_name", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| eventName: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "new_state_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| newStateId: string; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowState (new state) |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowState, (state) => state.historyAsNewState) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "new_state_id" }) |  |  |  |  |  |  |  |  |  |
| newState: WorkflowState; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "event_data_json", type: "json", nullable: true }) |  |  |  |  |  |  |  |  |  |
| eventDataJson: Record<string, any>; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "actor_id", type: "varchar", length: 100, nullable: true }) |  |  |  |  |  |  |  |  |  |
| actorId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "timestamp", type: "timestamptz", default: () => "NOW()" }) |  |  |  |  |  |  |  |  |  |
| timestamp: Date; |  |  |  |  |  |  |  |  |  |
| } |  |  |  |  |  |  |  |  |  |
| // Entity สำหรับตาราง workflow_approver |  |  |  |  |  |  |  |  |  |
| // ใช้เก็บข้อมูลการอนุมัติแต่ละครั้ง |  |  |  |  |  |  |  |  |  |
| @Entity("workflow_approver") |  |  |  |  |  |  |  |  |  |
| export class WorkflowApprover { |  |  |  |  |  |  |  |  |  |
| @PrimaryGeneratedColumn({ name: "approver_id" }) |  |  |  |  |  |  |  |  |  |
| approverId: number; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "transaction_id", type: "int" }) |  |  |  |  |  |  |  |  |  |
| transactionId: number; |  |  |  |  |  |  |  |  |  |
| // ความสัมพันธ์ Many-to-One ไปยัง WorkflowTransaction |  |  |  |  |  |  |  |  |  |
| @ManyToOne(() => WorkflowTransaction, (transaction) => transaction.approvers) |  |  |  |  |  |  |  |  |  |
| @JoinColumn({ name: "transaction_id" }) |  |  |  |  |  |  |  |  |  |
| transaction: WorkflowTransaction; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "approver_user_id", type: "varchar", length: 100 }) |  |  |  |  |  |  |  |  |  |
| approverUserId: string; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "status", type: "varchar", length: 50 }) |  |  |  |  |  |  |  |  |  |
| status: string; // เช่น 'pending', 'approved', 'rejected' |  |  |  |  |  |  |  |  |  |
| @Column({ name: "action_date", type: "timestamptz", default: () => "NOW()" }) |  |  |  |  |  |  |  |  |  |
| actionDate: Date; |  |  |  |  |  |  |  |  |  |
| @Column({ name: "comments", type: "text", nullable: true }) |  |  |  |  |  |  |  |  |  |
| comments: string; |  |  |  |  |  |  |  |  |  |
| } |  |  |  |  |  |  |  |  |  |

