# Config และ Environment Catalog

> Contract status: `AS-BUILT` Batch · Catalog status: `Blocked`

## ต้องทำอะไร และเสร็จแล้วได้อะไร

ตั้งค่าแต่ละ environment โดยรู้ว่าอะไรเป็น secret, default ใดเป็นเพียงค่าใน code และค่าใดต้อง sign-off รายชื่อเต็มให้ยึด `SBP/srm-sps-spsap-sop-sgi-batch/src/config/config.ts`; ตารางนี้จัดกลุ่มและระบุ ownership

| กลุ่ม | Keys หลัก | Secret | Default/หมายเหตุ |
|---|---|---:|---|
| Common | `SGI_TIMEZONE`, `DB_SCHEMA`, `SGI_ALLOW_PARTIAL_IMPORT` | no | `Asia/Bangkok`, `sps_store`; partial import ต้อง false production |
| ALLMAP | `SGI_ALLMAP_HOST/PORT/USER/PASSWORD/DATABASE`, `*_ENCRYPT`, `*_TRUST_CERT` | user/password | port 1433, encrypt true, trust cert false |
| Job 2 | `SGI_JOB2_ENABLED/CRON/SOURCE_VIEW/ALLMAP_YEAR_ERA/PROCESS_STATUS/DATASOURCE/BRANCH_TYPE_*/STALE_MONTHS/CHUNK_SIZE` | no | 07:00 วันที่ 7, view `SEVEN_IMPACT_VIEW`, AD, `IMPORTED`, `ALM` |
| Job 3 | `SGI_JOB3_ENABLED/CRON/SOURCE_VIEW/MISSING_PARENT/ON_EXISTING/CHUNK_SIZE` | no | 07:30 วันที่ 7, skip/skip |
| Job 4 | `SGI_JOB4_*S3*`, `FILE_PREFIX/EXT/ENCODING/LINE_SEPARATOR`, `INTERVAL_*`, `SOURCE_CREATED_BY`, `ALLOW_NEW_FILE_ON_TANGLE` | cloud credential | 7–16 16:00, UTF-8/LF, ALM |
| Job 5 | `SGI_JOB5_*S3*`, `ENCODING/FILE_PATTERN/DATA_NAME/TOTAL_WORKING_DAYS/OUTLIER_THRESHOLD/NULL_DIFF_STATUS/ON_INVALID_LINE` | cloud credential | 7–16 16:30, win874, 60, 50, Y, reject |
| Job 6 | `SGI_JOB6_CRON/INIT_START_DAY/NUM_WAIT_PAY/QSSI_CATEGORIES/MAX_BACKLOG/MAX_RESEND_RETRY`, `SGI_MQ_*`, `SGI_JOB6_ROUTING_KEY` | MQ URL | daily 17:00; exchange `sgi.interface` |
| Job 7 | `SGI_JOB7_CRON/DATASOURCE/SOURCE_SYSTEM/EMPTY_PRUNE_MAX_DOCS` | no | `ALM`→`ALLMAP`; D-003 |
| Job 8 | `SGI_JOB8_CRON/DATA_NAME/INIT_STATUS/INIT_SECTION/DV_GROUP_ID/MAX_RUNNING` | no | 17:00; `DOCUMENT_CREATE`, 06, group 15 |
| Job 8b | `SGI_JOB8B_CRON/WF_PATH/TIMEOUT_MS/RETRIES/BRANCH_TYPES/GROWTH_THRESHOLD/ZERO_MAX_MONTHS`, `SGI_BE_BASE_URL`, `SGI_SERVICE_TOKEN`, `SGI_WORKFLOW_VERSION_IDS` | token | 18:30; version IDs ต้องกำหนด production |
| Job 9 | `SGI_JOB9_CRON/DATASOURCE/SOURCE_SYSTEM/PERCENT_*/AMOUNT_TOLERANCE` | no | 17:45; sum target 100 |
| Job 10 | `SGI_JOB10_CRON/DATA_NAMES/PENDING_AGE_DAYS/ESCALATE_DAYS/INTERNAL_AGE_DAYS/EMAIL_TEMPLATE_ID/MAIL_TO` | recipient may sensitive | daily 08:00; 1/3 days |
| Job 11 | `SGI_JOB11_QUEUE/DLQ/PREFETCH/MAX_ATTEMPTS/IDLE_EXIT_SECONDS/CLOSED_POLICY/ON_UNKNOWN_NEW_STORE/ON_CONSISTENCY_ISSUE` | MQ URL | 10/3/60, update, dead_letter |
| Job 12 | `SGI_JOB12_CRON/BUCKET_MODE/TIERS/LEGACY_WINDOW/DAY_COUNT/STATES/GM_GROUP_ID/OPT_GROUP_ID/*TEMPLATE_ID/MAIL_TO` | recipient may sensitive | Mon 10:00; TIERED 30/45/60 BUSINESS |
| Email common | `SGI_JOB_FAIL_EMAIL_TEMPLATE_ID`, `SGI_JOB_MAIL_CC`, per-job `*_MAIL_TO` | no value in source | template/group/recipient ต้อง sign-off D-006 |

## Rules

- secret มาจาก Secrets Manager/approved store เท่านั้น; ไม่ส่งผ่าน `INPUT`; ห้ามมี default จริงใน source
- boolean parser รับ canonical `true/false`; invalid value ต้อง fail closed
- startup ต้อง validate required keys และ log เฉพาะชื่อ key/ค่าที่ไม่อ่อนไหว
- config snapshot ที่มีผลต่อเงิน/route/file schema ต้องอยู่ใน run log/audit โดย mask secret
- cron ใน code เป็น reference; AWS definition เป็น runtime source of truth (D-012)

## BLOCKED

D-001 approve limit, D-002 `mas_param` keys, D-003 datasource vocabulary, D-004 workflow IDs, D-006 email, D-008 IAS format, D-010 reminder policy และ D-012 scheduler ต้องปิดก่อน production
