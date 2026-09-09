# srm-sps-spsap-store-consumer — เอกสารวิเคราะห์ Codebase

> อ่านก่อนออกแบบการรับ-ส่งข้อมูลกับ **EAI (S3)** และ **RabbitMQ** ของงานประกันรายได้ (SGI)
> วิเคราะห์จากซอร์สจริงเมื่อ **2026-09-08** · repo อยู่ที่ `SBP/srm-sps-spsap-store-consumer` (gitignore แล้ว)
> เอกสารนี้เป็น **ผลอ่านโค้ด** ไม่ใช่ข้อกำหนด — `/SBP` เป็นระบบเดิม อ่านอย่างเดียว ห้ามแก้

---

## 0. สรุปสำหรับคนรีบ

| คำถาม | คำตอบ |
| --- | --- |
| repo นี้คืออะไร | **ตัวรับข้อความจาก RabbitMQ แล้วส่งต่อ** (fan-out dispatcher) — ไม่ใช่ระบบธุรกิจ ไม่มี business logic ของตัวเอง |
| รับจากไหน | RabbitMQ **1 queue ต่อ 1 process** (bind `exchange` + `routingKey`) |
| ส่งต่อไปไหนได้บ้าง | **3 ทาง** — `batch` (AWS Batch SubmitJob) · `api` (HTTP ผ่าน axios) · `message` (publish RabbitMQ ต่อ) |
| ตัดสินว่าไปทางไหนอย่างไร | อ่าน **config JSON จาก S3** ตอน start (`AWS_CONFIG_QUEUES_URL`) แล้วดูฟิลด์ `kind` |
| S3 ใช้ทำอะไร | **2 หน้าที่** — (1) เก็บ config ของแต่ละคิว (2) payload ชนิด `S3` ที่ส่ง **URI** มาแทนข้อมูลจริง |
| รันหลายคิวพร้อมกันยังไง | `generate-config.ts` อ่านรายการคิวจาก S3 → เขียน `ecosystem.config.js` → **PM2 รันหลาย worker** |
| ⚠️ สถานะความพร้อม | **ยังไม่ merge เข้า main** — `main` เป็น template เปล่า · โค้ดจริงอยู่บน branch `feature/initial_consumer` (2025-10-15) และ `feature/eai` (2025-11-05) |

**สิ่งที่ต้องรู้ก่อนออกแบบ SGI:** repo นี้ **ไม่ได้อ่าน/เขียนฐานข้อมูลเลย** และ **ไม่มี logic เฉพาะระบบใด** — มันคือ "ท่อ" ที่พาข้อความจาก EAI ไปยังปลายทางที่ config บอก ดังนั้นงาน SGI ที่จะรับข้อมูลจาก EAI ต้อง **ลงทะเบียนคิว + config** ที่นี่ แล้วให้มันไปเรียก job ของเราใน `srm-sps-spsap-sop-sgi-batch` อีกที

---

## 1. ⚠️ สถานะ branch — เรื่องแรกที่ต้องตัดสิน

| branch | commit ล่าสุด | ไฟล์ | เนื้อหา |
| --- | --- | --- | --- |
| `main` / `origin/main` | `be3c529` init project | 20 | **template เปล่า** (`nest-api-template`) — มีแค่ `AppModule` + middleware ว่าง ไม่มี MQ/S3 เลย |
| `origin/dev` | `9e29a96` (2025-11-05) merge main | 20 | เท่ากับ main |
| **`origin/feature/initial_consumer`** | `d9021c7` (2025-10-15) | 32 | 🟢 **ตัว consumer จริงทั้งหมด** — amqplib + AWS Batch + S3 + publisher + PM2 |
| **`origin/feature/eai`** | `40d24a5` (2025-11-05) | 23 | 🟡 ตัวรับ EAI แบบ **NestJS microservice** — คนละแนวกับ branch บน ยังเป็นแค่ log ข้อความ |
| `origin/uat` · `origin/production` | `fa772cf` (2025-08-05) | 3 | ว่างเปล่า ยังไม่เคย deploy |

🔴 **ผลต่องาน SGI:** ที่ checkout ไว้ในเครื่อง (`main`) **ไม่มีโค้ดที่ใช้งานได้** ถ้าจะอ้างอิง repo นี้ในสเปก ต้องระบุให้ชัดว่าอ้าง branch ไหน และต้องตามว่าทีมเจ้าของจะ merge อันไหนเข้า main

🔴 **สอง branch ออกแบบคนละแบบ** และยังไม่มีใครรวม:

| | `feature/initial_consumer` | `feature/eai` |
| --- | --- | --- |
| วิธีต่อ MQ | `amqplib` ดิบ — `assertQueue` + `bindQueue` + `consume` เอง | `@nestjs/microservices` `Transport.RMQ` + `@MessagePattern` |
| ควบคุม ack | `noAck: false` + `nack(msg, false, false)` เอง | ปล่อยให้ Nest จัดการ |
| ทำอะไรกับข้อความ | validate ด้วย zod แล้ว dispatch 3 ทาง | `logger.log()` + `console.log()` เฉย ๆ |
| S3 | ใช้ทั้ง config และ payload | ไม่มี |
| หลายคิว | PM2 หลาย worker | ตัวเดียว |
| ยังเปิด HTTP port | ไม่ (`createApplicationContext`) | ใช่ (`app.listen`) |

**ข้อเสนอ:** ยึด `feature/initial_consumer` เป็นตัวจริง เพราะสมบูรณ์กว่ามากและตรงกับสิ่งที่ EAI ต้องการ · `feature/eai` ดูเหมือนงานทดลองรับข้อความ callback

---

## 2. Tech Stack (branch `feature/initial_consumer`)

ชื่อใน `package.json` = **`srm-sps-spsap-csi-consumer-module`** (ไม่ตรงกับชื่อ repo — อีกจุดที่ต้องยืนยันกับเจ้าของ)

| กลุ่ม | แพ็กเกจ |
| --- | --- |
| Framework | `@nestjs/common` `@nestjs/core` 11 · `@nestjs/microservices` |
| RabbitMQ | **`amqplib` 0.10.9** (ฝั่งรับ) · **`amqp-connection-manager` 5** (ฝั่งส่งต่อ) |
| AWS | `@aws-sdk/client-s3` · `@aws-sdk/client-batch` · `@aws-sdk/client-eventbridge` · `@aws-sdk/credential-providers` |
| Validation | **`zod` 4** (ไม่ใช่ class-validator เหมือน repo อื่นของ SBP) |
| HTTP | `axios` |
| Process manager | **`pm2` 6** (รันหลาย worker ใน container เดียว) |
| อื่น ๆ | `typeorm` `js-yaml` `dotenv` — **ประกาศไว้แต่ไม่มีโค้ดใช้จริง** |

⚠️ `typeorm` อยู่ใน dependencies แต่**ไม่มีการ import ที่ไหนเลย** — repo นี้ไม่แตะฐานข้อมูล

---

## 3. สถาปัตยกรรม — ท่อ 1 เส้นต่อ 1 process

```
                    ┌─── S3: config ต่อคิว (INIT_CONFIG_BUCKET/KEY) ───┐
                    │        อ่านตอน container start                    │
                    ▼                                                    │
            generate-config.ts  ──→  ecosystem.config.js  ──→  PM2       │
                    │                                          │        │
                    │  1 คิว × worker N ตัว                     ▼        │
                    │                            ┌──────────────────────┐│
RabbitMQ ──bind──→  │                            │  ConsumerService     ││
 (exchange,         │                            │  (dist/main.js)      ││
  routingKey)       │                            └──────────┬───────────┘│
                                                            │            │
                              อ่าน config ของคิวตัวเอง ◄─────┘  AWS_CONFIG_QUEUES_URL
                                        │
                        ┌───────────────┼───────────────┐
                   kind=batch      kind=api        kind=message
                        │               │               │
                 AWS Batch         HTTP (axios)   RabbitMQ publish
                 SubmitJob                          (ต่อทอดอีกที)
```

### ลำดับการทำงานจริง (`consumer.service.ts` · `onModuleInit`)

| ขั้น | ทำอะไร | หมายเหตุ |
| --- | --- | --- |
| 1 | `loadConfig()` — โหลด config **จาก S3** ตาม `AWS_CONFIG_QUEUES_URL` แล้ว `ConfigSchema.parse()` | ล้มเหลว → **`process.exit(1)`** ทันที (fail fast ตั้งแต่ start) |
| 2 | `amqp.connect(MQ_URL)` → `createChannel()` | |
| 3 | `channel.prefetch(MQ_PREFETCH_COUNT)` | ค่าตั้งต้น **10** |
| 4 | `assertQueue(queue, { durable: true })` | |
| 5 | `bindQueue(queue, exchange, routingKey)` | |
| 6 | `consume(..., { noAck: false })` | |
| 7 | ต่อข้อความ: `safeMessageParse()` → ดู `config.kind` → เรียก 1 ใน 3 service | |
| 8 | error ใด ๆ → `nack(msg, false, false)` | 🔴 **ทิ้งข้อความ** — ดูข้อ 7 |

---

## 4. RabbitMQ — สัญญาที่ต้องรู้

### 4.1 ฝั่งรับ (consume)

ตั้งค่าผ่าน env ล้วน ๆ ไม่มี hardcode:

| env | ความหมาย |
| --- | --- |
| `MQ_URL` | connection string (`amqp://...`) |
| `MQ_EXCHANGE_NAME` | exchange ที่ bind |
| `MQ_QUEUENAME` | ชื่อคิว (`durable: true`) |
| `MQ_ROUTING_KEY` | routing key ที่ bind |
| `MQ_PREFETCH_COUNT` | จำนวนข้อความค้างได้พร้อมกัน (ตั้งต้น 10) |

⚠️ **ไม่มีการ `assertExchange`** — consumer สมมติว่า exchange มีอยู่แล้ว ถ้ายังไม่มีจะ error ตอน `bindQueue`

### 4.2 Envelope ของข้อความ (`message.schema.ts`) — **3 ชนิด**

```jsonc
// (1) dataType = "message" — ข้อมูลมาเต็ม ๆ ใน payload
{ "dataType": "message", "dataMessage": [ {...}, {...} ], "sender": "...", "sentAt": "..." }

// (2) dataType = "S3" — ส่ง "ที่อยู่ไฟล์" มาแทนข้อมูล  ← ใช้กับไฟล์ใหญ่
{ "dataType": "S3", "urls": "s3://bucket/key", "sender": "...", "sentAt": "..." }

// (3) dataType = "file" — แนบไฟล์มาเป็น base64
{ "dataType": "file", "fileName": "...", "contentType": "text/csv",
  "fileSize": 12345, "fileContent": "<base64>", "sender": "...", "sentAt": "..." }
```

🔴 **ต่างจาก envelope ของ `sop-sgi-batch` หนึ่งฟิลด์: ไม่มี `dataName`**

| | `sop-sgi-batch` (ฝั่งเรา) | `store-consumer` (ฝั่งนี้) |
| --- | --- | --- |
| `dataType` | ✅ | ✅ (แต่ค่าเป็น `message`/`S3`/`file`) |
| **`dataName`** | ✅ **มี** — ใช้แยกชุดข้อมูล | ❌ **ไม่มี · zod จะ reject ถ้าส่งมา?** |
| `dataMessage` | ✅ | ✅ (เฉพาะ `dataType=message`) |
| `sender` / `sentAt` | ✅ | ✅ |

> **ต้องยืนยันกับทีม EAI:** `zod` object schema แบบ default **ไม่ strict** (ฟิลด์เกินผ่านได้) ดังนั้นส่ง `dataName` มาด้วยน่าจะไม่พัง — แต่ **consumer จะไม่อ่านมันเลย** ถ้า SGI ต้องแยกชนิดข้อมูลด้วย `dataName` ต้องแยกด้วย **คิว/routing key** แทน หรือขอให้ทีมนี้เพิ่มฟิลด์

### 4.3 ฝั่งส่งต่อ (`kind = message`)

`message-publisher.service.ts` ใช้ `amqp-connection-manager`:
- `assertExchange(exchange, exchangeType ?? 'direct', { durable: true })` หรือ `assertQueue` ถ้าไม่มี exchange
- `persistent: true` เป็นค่าตั้งต้น · `contentType: 'application/json'`
- 🔴 **เปิด connection ใหม่ทุกครั้งที่ publish แล้วปิดทิ้ง** (`conn.close()` ท้ายเมธอด) — ถ้าปริมาณข้อความสูงจะเป็นคอขวด

---

## 5. S3 — ใช้ 2 ที่ คนละหน้าที่

### 5.1 Config ของคิว (`generate-config.ts` · รันก่อน app)

อ่านจาก `INIT_CONFIG_BUCKET` / `INIT_CONFIG_KEY` ได้ JSON array:

```jsonc
[
  { "url": "amqp://...", "exchange": "eai.exchange", "routingKey": "sgi.impact",
    "queue": "sgi.impact.q", "worker": 2, "configS3": "s3://bucket/config/sgi-impact.json" }
]
```
→ สร้าง `ecosystem.config.js` ให้ PM2 รัน **`worker` ตัวต่อคิว** โดยแปลงเป็น env `MQ_URL` `MQ_EXCHANGE_NAME` `MQ_ROUTING_KEY` `MQ_QUEUENAME` `AWS_CONFIG_QUEUES_URL`

### 5.2 Config ปลายทางของคิวนั้น (`consumer.service.ts` · รันตอน start)

`AWS_CONFIG_QUEUES_URL` (= `configS3` ข้างบน) ชี้ไฟล์ JSON ที่บอกว่าคิวนี้ต้องส่งต่อไปไหน:

```jsonc
// kind = batch
{ "kind": "batch", "jobName": "...", "jobQueue": "...", "jobDefinition": "...", "jobMain": "sgi-import-impact-store",
  "parameters": {...}, "containerOverrides": { "vcpus": 2, "memory": 4096, "command": [...], "environment": [...] } }

// kind = api
{ "kind": "api", "method": "POST", "url": "https://...", "headers": {...}, "timeout": 5000 }

// kind = message
{ "kind": "message", "url": "amqp://...", "exchange": "...", "routingKey": "...", "queue": "...",
  "exchangeType": "direct|topic|headers|fanout", "durable": true, "persistent": true, "contentType": "application/json" }
```

### 5.3 อ่านไฟล์จาก S3 (`s3-helper.ts`)

- `parseS3Uri('s3://bucket/key')` → `{ bucket, key }`
- `getFileAsString()` — `GetObjectCommand` แล้วอ่าน stream เป็น utf-8
- credential ใช้ **default provider chain** (IAM role ของ task) · region จาก `AWS_REGION` / `AWS_DEFAULT_REGION` ตั้งต้น `ap-southeast-1`

🔴 **`dataType = "S3"` ยังไม่ถูกดาวน์โหลด** — โค้ดปัจจุบันส่งทั้ง payload (รวม `urls`) ต่อไปให้ปลายทางเลย ปลายทาง (job ของเรา) ต้อง **ดาวน์โหลดไฟล์เอง**

---

## 6. AWS Batch — จุดต่อกับ job ของ SGI

`aws-batch.service.ts` → `submitBatchJob()`:

```ts
parameters: { INPUT: JSON.stringify(msg) }          // ทั้ง payload ถูกยัดเป็น INPUT
containerOverrides: { command: ["node", `${config.jobMain}.js`] }
```

🟢 **ตรงกับที่ `sop-sgi-batch` รับพอดี** — repo นั้นอ่าน argument จาก `INPUT` (env ตอน local / `argv[2]` ตอน AWS Batch) และ dispatch ด้วยชื่อ job · แปลว่า **ท่อเชื่อมกันได้จริง**

⚠️ แต่มี 2 จุดที่ต้องระวัง:
1. `command` ถูก override เป็น `node <jobMain>.js` — **ไม่ใช่รูปแบบ `--job=<name>` ที่ `sop-sgi-batch` ใช้** ต้องยืนยันว่า entrypoint ฝั่ง batch รับแบบไหน
2. `parameters.INPUT` ของ AWS Batch มีเพดานขนาด — payload ใหญ่ต้องใช้ `dataType = "S3"` แทน

`batch-helper.ts` ยังมี `describeJobs` · `waitForJobCompletion` (polling + exponential backoff สูงสุด 30 วิ / รอ 1 ชม.) · `listJobsByStatus` · `cancelJob` · `terminateJob` — **แต่ `aws-batch.service.ts` ยังไม่เรียกใช้เลย** submit แล้วจบ ไม่รอผล

---

## 7. 🔴 ช่องว่างที่ต้องตัดสินก่อนพึ่ง repo นี้

| # | เรื่อง | รายละเอียด | ผลถ้าไม่แก้ |
| --- | --- | --- | --- |
| C1 | **ข้อความเสียถูกทิ้ง** | `nack(msg, false, false)` — `requeue = false` และ**ไม่มี DLQ** ในโค้ด | ข้อความที่ประมวลผลไม่ผ่าน **หายถาวร** ไม่มีร่องรอย |
| C2 | **มีกลไก retry แต่ไม่ได้เปิดใช้** | `batch-helper.ts:40,50` รองรับ `retryAttempts` → `retryStrategy` ของ AWS Batch แต่ `aws-batch.service.ts` **ไม่เคยส่งค่านี้เข้าไป** · ฝั่ง `api.service.ts` ก็ไม่มี retry เลย (ตรวจแล้ว: คำว่า `retry` ไม่ปรากฏใน `src/amqp/` เลยสักที่) | งานหายเงียบ ๆ ตอน AWS มีปัญหาชั่วคราว — **แก้ง่ายมาก แค่ส่ง `retryAttempts` ตอน submit** |
| C3 | **ไม่มี log ที่ตามรอยได้** | ใช้ `console.log` ล้วน · ตรวจแล้ว **ไม่มีคำว่า `correlationId`/`messageId` ใน `src/` เลย** · `console.log(\`📩 Message received: ${msg.properties.headers}\`)` พิมพ์ object ออกมาเป็น `[object Object]` ด้วย | ตามรอยข้ามระบบไม่ได้ (ต่างจาก `integration_log` ของ batch repo) |
| C4 | **ไม่มี idempotency** | ส่งข้อความซ้ำ = submit job ซ้ำ | ข้อมูลซ้ำที่ปลายทาง |
| C5 | **`dataName` ไม่มีใน schema** | ตรวจ 4 แหล่งแล้ว **3 ใน 4 มี**: `sop-sgi-batch` ✅ · **`store-backend` ✅** (`import_mas_store_organize.service.ts:580` ส่ง `dataName = "sps_store_organize_ptt"` จริง) · สเปก STA ✅ · repo นี้ ❌ | แยกชนิดข้อมูลในคิวเดียวไม่ได้ ต้องแยกคิว — **ข้อค้าง 2.12 ใน `DECISIONS-รอตัดสินใจ.md`** |
| C6 | **ไม่ตรวจผลลัพธ์ batch** | `batch-helper.ts` เขียน `describeJobs` · `waitForJobCompletion` · `listJobsByStatus` · `cancelJob` · `terminateJob` ไว้ครบ **แต่ `src/amqp/` ไม่เรียกสักตัว (0 จุด)** — submit แล้วจบ | job ล้มแล้วไม่มีใครรู้จากฝั่ง consumer · ต้องไปดูที่ `integration_log` ของ batch repo เอง |
| C7 | `HEALTHCHECK` ชี้ `/health` | Dockerfile เช็ค `http://127.0.0.1:3000/health` แต่ branch นี้ใช้ `createApplicationContext` — **ไม่เปิด HTTP server** | health check **fail ตลอด** → container ถูก restart วน |
| C8 | ชื่อ package ≠ ชื่อ repo | `srm-sps-spsap-csi-consumer-module` vs `srm-sps-spsap-store-consumer` | สับสนตอน deploy/ตั้ง ECR |
| C9 | โค้ดจริงยังไม่ merge | `main` เป็น template เปล่า | อ้างอิงในสเปกไม่ได้จนกว่าจะ merge |

---

## 8. สิ่งที่ SGI ต้องทำถ้าจะรับข้อมูลจาก EAI ผ่าน repo นี้

1. **ขอคิวจากทีม EAI** — ระบุ `exchange` + `routingKey` + ชื่อคิวของ SGI
2. **เพิ่มรายการใน config S3 ตัวแรก** (`INIT_CONFIG_BUCKET/KEY`) — 1 แถวต่อ 1 คิว พร้อม `worker` และ `configS3`
3. **สร้าง config ปลายทาง** (`configS3`) เป็น `kind = "batch"` ชี้ `jobQueue` / `jobDefinition` ของ `sop-sgi-batch` และ `jobMain` = ชื่อ job ของเรา (เช่น `sgi-import-impact-sale`)
4. **ฝั่ง job ของเรา** ต้องอ่าน `INPUT` แล้วแตก envelope เอง — และถ้า `dataType = "S3"` ต้อง **ดาวน์โหลดไฟล์จาก `urls` เอง** (consumer ไม่ดาวน์โหลดให้)
5. **ตกลงเรื่องข้อ C1–C6 ให้จบก่อน UAT** — โดยเฉพาะ **DLQ + retry + idempotency** เพราะข้อมูลผลกระทบ/ยอดขายหายไม่ได้

### เทียบกับที่ LLDD ของเราเขียนไว้ตอนนี้

| หัวข้อใน LLDD | ตรงกับ repo นี้ไหม |
| --- | --- |
| Job 5 ดึง `AMS06001I` จาก **EAI S3** | 🟡 ได้ ถ้า EAI ส่งข้อความ `dataType = "S3"` มาเข้าคิว แล้ว job ดาวน์โหลดเอง — **แต่ LLDD ยังเขียนว่า job ไปหยิบไฟล์เองโดยตรง** ต้องเลือกทางใดทางหนึ่ง |
| Job 4 อัปโหลด `AMS06001O` ขึ้น EAI S3 | ⚪ repo นี้ **ไม่มีขา upload** — เป็น consumer อย่างเดียว ต้องใช้ `S3Service` ของ `sop-sgi-batch` |
| Job 6 ส่ง `sta.compensation.result` เข้า RabbitMQ | ⚪ ใช้ publisher ของ `sop-sgi-batch` ไม่ต้องผ่าน repo นี้ |
| Job 11 รับ `sta_update_compensate` จาก RabbitMQ | 🔴 **ต้องตัดสิน** — จะให้ job 11 consume เองใน `sop-sgi-batch` หรือให้ repo นี้รับแล้ว submit job 11 ให้ · **ทางหลังตรงกับสถาปัตยกรรมของบ้านนี้มากกว่า** แต่ LLDD ปัจจุบันเขียนแบบแรก |

---

## 9. โครงสร้าง `src/` (branch `feature/initial_consumer`)

```
src/
├─ main.ts                      createApplicationContext (ไม่เปิด HTTP)
├─ app.module.ts                imports: [AMQPModule]
├─ amqp/
│  ├─ amqp.module.ts            providers: Consumer + API + AWSBatch + MessagePublisher
│  ├─ consumer.service.ts       ★ หัวใจ — connect/bind/consume/dispatch
│  └─ service/
│     ├─ api/api.service.ts             kind=api  → axios
│     ├─ batch/aws-batch.service.ts     kind=batch → SubmitJob
│     └─ message-publisher/…            kind=message → publish ต่อ
├─ common/
│  ├─ interfaces/  config.interface.ts · message.interface.ts
│  └─ schemas/     config.schema.ts · message.schema.ts   (zod)
└─ shared/
   ├─ s3-helper.ts              parseS3Uri · getFileAsString
   └─ batch-helper.ts           submit/describe/wait/list/cancel/terminate
```

**มี unit test 4 ไฟล์** (`*.spec.ts`) ครอบ consumer + ทั้ง 3 service — mock `amqplib` และ AWS SDK ไว้เรียบร้อย เป็นตัวอย่างที่ดีสำหรับเขียน test ของ job ฝั่งเรา

---

## 10. Deploy

- **Dockerfile** multi-stage: build → `node:20-alpine` + `pm2` · รันด้วย `USER nodeapp` (ไม่ใช่ root) · `EXPOSE 3000`
- **`start.sh`**: `node dist-tools/generate-config.js` → ตรวจว่ามี `ecosystem.config.js` → `pm2-runtime ecosystem.config.js`
- **CI/CD**: `bitbucket-pipelines.yml` (template กลางของ Gosoft + SonarQube)
- ⚠️ ดู **C7** — HEALTHCHECK ชี้ `/health` ที่ไม่มีอยู่จริงบน branch นี้

---

## 11. Environment Variables ทั้งหมด

| ตัวแปร | ใช้ที่ไหน | หมายเหตุ |
| --- | --- | --- |
| `INIT_CONFIG_BUCKET` / `INIT_CONFIG_KEY` | `generate-config.ts` | รายการคิวทั้งหมด (ไม่ใช่ S3 URI — แยก bucket/key) |
| `AWS_CONFIG_QUEUES_URL` | `consumer.service.ts` | **S3 URI** ของ config ปลายทางต่อคิว |
| `MQ_URL` `MQ_EXCHANGE_NAME` `MQ_QUEUENAME` `MQ_ROUTING_KEY` | consumer | PM2 ใส่ให้อัตโนมัติจาก config |
| `MQ_PREFETCH_COUNT` | consumer | ตั้งต้น `10` |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | S3 + Batch | ตั้งต้น `ap-southeast-1` |
| `PORT` | มีเฉพาะ branch `feature/eai` | `3008` ใน `.env` ของ branch นั้น |

---

## 11.5 ผลตรวจ `store-backend` — มี RabbitMQ ของตัวเองด้วย (ตรวจ 2026-09-08)

ผู้ใช้ให้ตรวจว่า backend ส่ง RabbitMQ ด้วยไหม — **มีจริง และเป็นคนละเส้นทางกับ repo นี้**

| หัวข้อ | สิ่งที่พบใน `srm-sps-spsap-store-backend` |
| --- | --- |
| ตัว publish | `src/modules/rabbitMQ/rabbitmq.service.ts` → `publishMessage(urls, exchange, routingKey, payload)` |
| รูปแบบ | `assertExchange(exchange, "topic", { durable: true })` · `persistent: true` · `contentType: application/json` · `contentEncoding: utf-8` · เปิด/ปิด connection ทุกครั้งใน `finally` |
| ผู้เรียกจริง | **1 ที่** — `modules/uploads/import_report/import_mas_store_organize.service.ts:590` |
| ช่องที่ใช้ | exchange `sps.store.master` · routingKey `sps.store.master.store-organize.ptt` · `dataName = sps_store_organize_ptt` · `sender = store` |
| ⚠️ dead import | `modules/statement/statement.service.ts:106` `import { publishMessage }` แต่ **ไม่เคยเรียก (0 ครั้ง)** |
| S3 ของ backend | `modules/aws/aws.service.ts` — `uploadFile` · `downloadFile` · `moveFile` · `checkFileExist` (bucket จาก `AWS_BUCKET_NAME`) |

**สรุปสำหรับ SGI:** ขา **ส่งออก** ของเรา (Job 4 upload ไฟล์ · Job 6 publish ให้ STA) **ไม่ต้องผ่าน repo นี้** —
ใช้ `S3Service`/publisher ของ `sop-sgi-batch` ได้เลย และรูปแบบ publish ของ backend ยืนยันว่า
**exchange type `topic` + envelope ที่มี `dataName`** คือมาตรฐานของบ้านนี้

**การตั้งชื่อ routing key ที่บ้านนี้ใช้จริง:** `<exchange>.<entity>.<variant>`
เช่น `sps.store.master` → `sps.store.master.store-organize.ptt` — ควรตั้งของ SGI ให้ล้อแบบเดียวกัน

---

## 12. เอกสารที่เกี่ยวข้อง

- `SBP/srm-sps-spsap-sop-sgi-batch.md` — batch runner ที่ consumer ตัวนี้จะ **submit job เข้าไป**
- `SBP/srm-sps-spsap-store-backend.md` — convention ของ NestJS ฝั่ง API (ต่างจาก repo นี้: ใช้ class-validator ไม่ใช่ zod)
- `workflow.md` §Batch Scheduler · `LLDD/md/Jobs/LLDD-BE-Job-5-*` และ `-Job-11-*` — จุดที่ต้องตัดสินตามข้อ 8
