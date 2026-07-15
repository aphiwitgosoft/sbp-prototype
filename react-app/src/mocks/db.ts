import type {
  AuditLog, Competitor, ConfigItem, DashboardSummary, DocumentDetail, EmailTemplate, Factor, Job,
  Lookup, MenuPermissionRow, Operator, ReportRow, RoleRow, StoreLookup, TaskRow,
} from '@/types/api';

export const STATUSES: Lookup[] = [
  { code: '06', name: 'รอฝ่าย SBP DSA ดำเนินการ' },
  { code: '08', name: 'รอเจ้าหน้าที่ SBP DSA ดำเนินการ' },
  { code: '01', name: 'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ' },
  { code: '02', name: 'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ' },
  { code: '03', name: 'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ' },
  { code: '04', name: 'รอฝ่ายบัญชี SBP ดำเนินการ' },
  { code: '05', name: 'รอบัญชีปฏิบัติการภาคดำเนินการ' },
  { code: 'END', name: 'เสร็จสิ้นดำเนินการ' },
];

export const SECTIONS: Lookup[] = [
  { code: '06', name: 'ฝ่าย SBP DSA' },
  { code: '08', name: 'เจ้าหน้าที่ SBP DSA' },
  { code: '01', name: 'ฝ่ายส่งเสริมธุรกิจฯ' },
  { code: '02', name: 'GM OPT' },
  { code: '03', name: 'AVP OPT' },
  { code: '04', name: 'ฝ่ายบัญชี SBP' },
  { code: '05', name: 'บัญชีปฏิบัติการภาค' },
];

export const TASKS: TaskRow[] = [
  { docNo: '2569/00123', storeCode: '00788', storeName: 'รัตนอุทิศ ซ.13', region: 'RS', impactMonth: '05/2569', status: 'รอฝ่าย SBP DSA ดำเนินการ', currentSection: '06', waitingDays: 2, compensateAmount: 48200, salesDropPercent: 12.45, round: 1, type: "FR Type B", created: "12/06/2569", red: false },
  { docNo: '2569/00131', storeCode: '01045', storeName: 'บางบัวทอง ก.ม.8', region: 'BW', impactMonth: '05/2569', status: 'รอเจ้าหน้าที่ SBP DSA ดำเนินการ', currentSection: '08', waitingDays: 5, compensateAmount: 31500, salesDropPercent: 15.2, round: 1, type: "FR Type C", created: "10/06/2569", red: true },
  { docNo: '2569/00140', storeCode: '00256', storeName: 'ปากเกร็ด สถานี', region: 'RN', impactMonth: '05/2569', status: 'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ', currentSection: '01', waitingDays: 1, compensateAmount: 66400, salesDropPercent: 9.8, round: 2, type: "FR Type B", created: "11/06/2569", red: false },
  { docNo: '2569/00157', storeCode: '00342', storeName: 'ติวานนท์ 25', region: 'BN', impactMonth: '05/2569', status: 'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ', currentSection: '02', waitingDays: 3, compensateAmount: 52300, salesDropPercent: 11.3, round: 1, type: "FR Type A", created: "09/06/2569", red: false },
  { docNo: '2569/00194', storeCode: '01055', storeName: 'บางพลัด จรัญฯ 79', region: 'BS', impactMonth: '05/2569', status: 'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ', currentSection: '03', waitingDays: 2, compensateAmount: 104500, salesDropPercent: 14.1, round: 1, type: "FR Type A", created: "08/06/2569", red: false },
  { docNo: '2569/00168', storeCode: '00694', storeName: 'สามัคคี ซ.58', region: 'BE', impactMonth: '05/2569', status: 'รอฝ่ายบัญชี SBP ดำเนินการ', currentSection: '04', waitingDays: 1, compensateAmount: 22150, salesDropPercent: 8.6, round: 1, type: "FR Type B", created: "06/06/2569", red: false },
  { docNo: '2569/00190', storeCode: '00623', storeName: 'สนามบินน้ำ 9', region: 'RC', impactMonth: '05/2569', status: 'รอบัญชีปฏิบัติการภาคดำเนินการ', currentSection: '05', waitingDays: 2, compensateAmount: 27800, salesDropPercent: 10.4, round: 2, type: "FR Type C", created: "05/06/2569", red: false },
  { docNo: '2569/00171', storeCode: '00415', storeName: 'ประชาชื่น 12', region: 'BN', impactMonth: '05/2569', status: 'รอฝ่าย SBP DSA ดำเนินการ', currentSection: '06', waitingDays: 6, compensateAmount: 24600, salesDropPercent: 13.75, round: 2, type: "FR Type B", created: "04/06/2569", red: true },
  { docNo: '2569/00152', storeCode: '01133', storeName: 'แคราย พลาซ่า', region: 'RS', impactMonth: '04/2569', status: 'เสร็จสิ้นดำเนินการ', currentSection: 'END', waitingDays: 0, compensateAmount: 25650, salesDropPercent: 7.9, round: 1, type: "FR Type พนักงาน", created: "02/06/2569", red: false },
  { docNo: '2569/00205', storeCode: '01260', storeName: 'ไทรม้า สถานีรถไฟฟ้า', region: 'RE', impactMonth: '05/2569', status: 'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ', currentSection: '01', waitingDays: 4, compensateAmount: 36000, salesDropPercent: 10.1, round: 1, type: "FR Type พนักงาน", created: "03/06/2569", red: false },
];

export const REPORT: ReportRow[] = [
  { store: '00788', storeName: 'รัตนอุทิศ ซ.13', region: 'RS', type: 'FR Type B', month: '05/2569', transfer: '01/03/2566', period: '05/2569', newStore: '00990', newName: 'เซเว่นฯ รัตนาธิเบศร์ 12', newRegion: 'RS', newType: 'FR Type A', amount: 48200, status: 'รอฝ่าย SBP DSA ดำเนินการ', officer: 'สมชาย ใจดี', result: '-', waitDays: 2, round: 1, created: '12/06/2569', docNo: '2569/00123', red: false },
  { store: '01045', storeName: 'บางบัวทอง ก.ม.8', region: 'BW', type: 'FR Type C', month: '05/2569', transfer: '15/07/2565', period: '05/2569', newStore: '01200', newName: 'เซเว่นฯ บางบัวทอง 14', newRegion: 'BW', newType: 'FR Type A', amount: 31500, status: 'รอเจ้าหน้าที่ SBP DSA ดำเนินการ', officer: 'มาลี ศรีสุข', result: '-', waitDays: 5, round: 1, created: '10/06/2569', docNo: '2569/00131', red: true },
  { store: '00256', storeName: 'ปากเกร็ด สถานี', region: 'RN', type: 'FR Type B', month: '05/2569', transfer: '20/01/2566', period: '05/2569', newStore: '00501', newName: 'เซเว่นฯ แจ้งวัฒนะ 28', newRegion: 'RN', newType: 'FR Type A', amount: 66400, status: 'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ', officer: 'วีรพล มั่นคง', result: 'คำนวณเงินชดเชยเรียบร้อย', waitDays: 1, round: 2, created: '11/06/2569', docNo: '2569/00140', red: false },
  { store: '01133', storeName: 'แคราย พลาซ่า', region: 'RS', type: 'FR Type พนักงาน', month: '04/2569', transfer: '05/09/2564', period: '04/2569', newStore: '-', newName: '-', newRegion: '-', newType: '-', amount: 25650, status: 'เสร็จสิ้นดำเนินการ', officer: 'พัชริดา พงศ์วรงค์ชัย', result: 'บัญชีภาคอนุมัติ', waitDays: 0, round: 1, created: '02/06/2569', docNo: '2569/00152', red: false },
  { store: '00342', storeName: 'ติวานนท์ 25', region: 'BN', type: 'FR Type A', month: '05/2569', transfer: '11/11/2565', period: '05/2569', newStore: '00877', newName: 'เซเว่นฯ ติวานนท์ 40', newRegion: 'BN', newType: 'FR Type B', amount: 52300, status: 'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ', officer: 'สมชาย ใจดี', result: 'เห็นควรชดเชย', waitDays: 3, round: 1, created: '09/06/2569', docNo: '2569/00157', red: false },
  { store: '01055', storeName: 'บางพลัด จรัญฯ 79', region: 'BS', type: 'FR Type A', month: '05/2569', transfer: '22/02/2566', period: '05/2569', newStore: '01340', newName: 'เซเว่นฯ จรัญสนิทวงศ์ 81', newRegion: 'BS', newType: 'FR Type A', amount: 104500, status: 'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ', officer: 'จันทราภรณ์ บรรจือ', result: 'เห็นควรชดเชย (> 100,000)', waitDays: 2, round: 1, created: '08/06/2569', docNo: '2569/00194', red: false },
  { store: '00694', storeName: 'สามัคคี ซ.58', region: 'BE', type: 'FR Type B', month: '05/2569', transfer: '30/05/2565', period: '05/2569', newStore: '00912', newName: 'เซเว่นฯ สามัคคี 60', newRegion: 'BE', newType: 'FR Type C', amount: 22150, status: 'รอฝ่ายบัญชี SBP ดำเนินการ', officer: 'มาลี ศรีสุข', result: 'เห็นควรชดเชย', waitDays: 1, round: 1, created: '06/06/2569', docNo: '2569/00168', red: false },
  { store: '00623', storeName: 'สนามบินน้ำ 9', region: 'RC', type: 'FR Type C', month: '05/2569', transfer: '18/04/2566', period: '05/2569', newStore: '01108', newName: 'เซเว่นฯ สนามบินน้ำ 11', newRegion: 'RC', newType: 'FR Type B', amount: 27800, status: 'รอบัญชีปฏิบัติการภาคดำเนินการ', officer: 'วีรพล มั่นคง', result: 'เห็นควรชดเชย', waitDays: 2, round: 2, created: '05/06/2569', docNo: '2569/00190', red: false },
  { store: '00415', storeName: 'ประชาชื่น 12', region: 'BN', type: 'FR Type B', month: '05/2569', transfer: '09/10/2566', period: '05/2569', newStore: '00733', newName: 'เซเว่นฯ ประชาชื่น 18', newRegion: 'BN', newType: 'FR Type A', amount: 24600, status: 'รอฝ่าย SBP DSA ดำเนินการ', officer: 'สมชาย ใจดี', result: '-', waitDays: 6, round: 2, created: '04/06/2569', docNo: '2569/00171', red: true },
];

export const DOCUMENT_DETAIL: Record<string, DocumentDetail> = {
  '2569/00123': {
    docNo: '2569/00123',
    status: 'รอฝ่าย SBP DSA ดำเนินการ',
    currentSection: '06',
    impactedStore: { storeCode: '00788', storeName: 'รัตนอุทิศ ซ.13', region: 'RS', storeType: 'FR Type B' },
    salesDropPercent: 12.45,
    compensateAmount: 48200,
    newStores: [{ storeCode: '00990', storeName: 'เซเว่นฯ รัตนาธิเบศร์ 12', compensatePercent: 100, distanceKm: 0.62 }],
    competitors: [{ competitorCode: 'C007', competitorName: 'Lotus Express', impactDate: '01/04/2569' }],
    factors: [{ factorCode: 'F001', factorName: 'ร้านคู่แข่งเปิดใหม่' }],
    timeline: [
      { section: '06', considerName: 'สมชาย ใจดี', result: 'เปิดเอกสาร', actionDateTime: '2026-06-12T09:10:00' },
    ],
  },
};

export const OPERATORS: Operator[] = [
  { operatorAssignmentId: 1, empName: 'นายสมชาย ใจดี', empMail: 'somchai.j@cpall.co.th', sectionName: 'ส่งเสริมธุรกิจพันธมิตรฯ', zoneCode: 'RN' },
  { operatorAssignmentId: 2, empName: 'นางสาวมาลี ศรีสุข', empMail: 'malee.s@cpall.co.th', sectionName: 'ฝ่าย SBP DSA', zoneCode: '-' },
  { operatorAssignmentId: 3, empName: 'นายวีรพล มั่นคง', empMail: 'weerapol.m@cpall.co.th', sectionName: 'ฝ่ายบัญชี SBP', zoneCode: '-' },
  { operatorAssignmentId: 4, empName: 'นางสาวพัชริดา พงศ์วรงค์ชัย', empMail: 'phatcharida.p@cpall.co.th', sectionName: 'เจ้าหน้าที่ SBP DSA', zoneCode: '-' },
];

export const FACTORS: Factor[] = [
  { factorCode: 'F001', factorName: 'ร้านคู่แข่งเปิดใหม่', factorRemark: 'มีร้านสะดวกซื้อคู่แข่งเปิดในรัศมีใกล้เคียง' },
  { factorCode: 'F002', factorName: 'ห้างค้าปลีกขนาดใหญ่', factorRemark: 'มีห้างสรรพสินค้า/ซูเปอร์มาร์เก็ตเปิดในพื้นที่' },
  { factorCode: 'F003', factorName: 'การก่อสร้าง / ปิดถนน', factorRemark: 'โครงการก่อสร้างหรือปิดถนนกระทบการเข้าถึงร้าน' },
  { factorCode: 'F004', factorName: 'ทำเล/สถานีเปลี่ยน', factorRemark: 'การย้ายป้ายรถเมล์ / สถานีขนส่ง กระทบปริมาณคนผ่าน' },
];

export const CONFIGS: ConfigItem[] = [
  { configKey: 'impact.radius_bkk_km', category: 'IMPACT', value: '1', valueType: 'NUMBER', unit: 'กม.', description: 'รัศมีกระทบ กทม./ปริมณฑล', isEditable: false },
  { configKey: 'impact.radius_upcountry_km', category: 'IMPACT', value: '2', valueType: 'NUMBER', unit: 'กม.', description: 'รัศมีกระทบต่างจังหวัด', isEditable: false },
  { configKey: 'impact.min_working_days', category: 'IMPACT', value: '60', valueType: 'NUMBER', unit: 'วัน', description: 'เกณฑ์วันทำการขั้นต่ำ', isEditable: false },
  { configKey: 'impact.outlier_threshold', category: 'IMPACT', value: '50', valueType: 'NUMBER', unit: '%', description: 'เกณฑ์ outlier ยอดขาย', isEditable: false },
  { configKey: 'workflow.avp_amount_threshold', category: 'WORKFLOW', value: '100000', valueType: 'NUMBER', unit: 'บาท', description: 'วงเงินเข้าเส้น AVP', isEditable: false },
  { configKey: 'workflow.escalation_days', category: 'WORKFLOW', value: '[30, 45, 60]', valueType: 'JSON', unit: 'วัน', description: 'ลำดับวัน escalation งานค้าง', isEditable: true },
  { configKey: 'workflow.reminder_cron', category: 'WORKFLOW', value: '0 10 * * 1', valueType: 'CRON', unit: '', description: 'เตือนงานค้างรายสัปดาห์ (จันทร์ 10:00)', isEditable: true },
  { configKey: 'document.max_attachment_mb', category: 'DOCUMENT', value: '5', valueType: 'NUMBER', unit: 'MB', description: 'ขนาดไฟล์แนบสูงสุด/ไฟล์', isEditable: true },
  { configKey: 'document.number_prefix', category: 'DOCUMENT', value: 'YYYY/xxxxx', valueType: 'STRING', unit: '', description: 'รูปแบบเลขเอกสาร', isEditable: false },
  { configKey: 'document.export_max_rows', category: 'DOCUMENT', value: '50000', valueType: 'NUMBER', unit: 'แถว', description: 'จำนวนแถวสูงสุดต่อไฟล์ export', isEditable: true },
  { configKey: 'auth.access_token_min', category: 'AUTH', value: '30', valueType: 'NUMBER', unit: 'นาที', description: 'อายุ accessToken', isEditable: true },
  { configKey: 'auth.refresh_token_hr', category: 'AUTH', value: '8', valueType: 'NUMBER', unit: 'ชม.', description: 'อายุ refreshToken', isEditable: true },
  { configKey: 'notification.smtp_from', category: 'NOTIFICATION', value: 'sbpgi@cpall.co.th', valueType: 'STRING', unit: '', description: 'อีเมลผู้ส่งระบบ', isEditable: true },
  { configKey: 'batch.sftp_timeout_sec', category: 'BATCH', value: '120', valueType: 'NUMBER', unit: 'วินาที', description: 'timeout การเชื่อม SFTP', isEditable: true },
];

export const JOBS: Job[] = [
  { jobNo: '1', name: 'ImportQSSI', phase: 'A', cron: 'Monthly', enabled: true, lastStatus: 'SUCCESS', lastRows: 48220, lastRunAt: '2026-07-01T06:00:00' },
  { jobNo: '2', name: 'ImportImpactStore', phase: 'A', cron: '0 7 7 * *', enabled: true, lastStatus: 'SUCCESS', lastRows: 1254, lastRunAt: '2026-07-07T07:00:00' },
  { jobNo: '3', name: 'ImportImpactCompetitor', phase: 'A', cron: '0 7 7 * *', enabled: true, lastStatus: 'SUCCESS', lastRows: 863, lastRunAt: '2026-07-07T07:05:00' },
  { jobNo: '4', name: 'PrepareImpactStoreToIAS', phase: 'B', cron: '0 16 7-16 * *', enabled: true, lastStatus: 'SUCCESS', lastRows: 412, lastRunAt: '2026-07-07T16:00:00' },
  { jobNo: '5', name: 'ImportImpactSaleFromIAS', phase: 'B', cron: '30 16 7-16 * *', enabled: true, lastStatus: 'WARN', lastRows: 398, lastRunAt: '2026-07-07T16:30:00' },
  { jobNo: '6', name: 'ExportImpactStoreToFS', phase: 'D', cron: '0 17 * * *', enabled: true, lastStatus: 'SUCCESS', lastRows: 1254, lastRunAt: '2026-07-06T17:00:00' },
  { jobNo: '7', name: 'ExportCompetitor', phase: 'C', cron: '30 17 7-31 * *', enabled: false, lastStatus: 'SUCCESS', lastRows: 0, lastRunAt: '2026-07-01T17:30:00' },
  { jobNo: '8', name: 'ExportImpactStoreFlowToBPM', phase: 'C', cron: '30 17 7-31 * *', enabled: false, lastStatus: 'SUCCESS', lastRows: 0, lastRunAt: '2026-07-01T17:30:00' },
  { jobNo: '8b', name: 'StartK2WorkFlow', phase: 'D', cron: '0 18 7-31 * *', enabled: true, lastStatus: 'SUCCESS', lastRows: 58, lastRunAt: '2026-07-06T18:00:00' },
  { jobNo: '9', name: 'ExportOpenStore', phase: 'C', cron: '30 17 7-31 * *', enabled: false, lastStatus: 'SUCCESS', lastRows: 0, lastRunAt: '2026-07-01T17:30:00' },
  { jobNo: '10', name: 'NotifyNoReceiveData', phase: 'E', cron: '0 7 * * *', enabled: true, lastStatus: 'WARN', lastRows: 2, lastRunAt: '2026-07-07T07:00:00' },
];

export const ROLES: RoleRow[] = [
  { roleCode: '00', roleName: 'Default', roleDesc: 'ค่าเริ่มต้น (ไม่มีสิทธิ์)', isSystem: true },
  { roleCode: '01', roleName: 'Admin', roleDesc: 'ผู้ดูแลระบบ BPM', isSystem: true },
  { roleCode: '02', roleName: 'HQ', roleDesc: 'ส่วนกลาง', isSystem: true },
  { roleCode: '03', roleName: 'User Admin', roleDesc: 'ผู้ดูแลผู้ใช้/ข้อมูลหลัก', isSystem: true },
  { roleCode: '04', roleName: 'Report Admin', roleDesc: 'ดูรายงาน', isSystem: true },
  { roleCode: '05', roleName: 'Assign Job', roleDesc: 'แจกงานข้อมูลผิดปกติ', isSystem: true },
  { roleCode: '06', roleName: 'Report Admin ภาค', roleDesc: 'ดูรายงานเฉพาะภาค', isSystem: true },
  { roleCode: '10', roleName: 'UserViewer', roleDesc: 'ดูอย่างเดียว', isSystem: true },
];

const RC = ['00', '01', '02', '03', '04', '05', '06', '10'];
function acc(...on: string[]): Record<string, boolean> {
  return Object.fromEntries(RC.map((r) => [r, on.includes(r)]));
}
export const MENU_PERMISSIONS: MenuPermissionRow[] = [
  { menuCode: 'M01', menuName: 'สร้างเอกสาร', group: 'ระบบประกันรายได้', access: acc('01', '02', '03') },
  { menuCode: 'M02', menuName: 'เอกสาร · รอดำเนินการ', group: 'ระบบประกันรายได้', access: acc('01', '02', '03', '04', '05', '06') },
  { menuCode: 'M03', menuName: 'เอกสาร · ที่เกี่ยวข้อง', group: 'ระบบประกันรายได้', access: acc('01', '02', '03', '04', '06', '10') },
  { menuCode: 'M07', menuName: 'รายงานสรุปสถานะ', group: 'ระบบประกันรายได้', access: acc('01', '04', '06') },
  { menuCode: 'M08', menuName: 'กำหนดผู้ปฏิบัติงาน', group: 'ระบบประกันรายได้', access: acc('01', '03') },
  { menuCode: 'M09', menuName: 'กำหนดปัจจัยภายนอก', group: 'ระบบประกันรายได้', access: acc('01', '03') },
  { menuCode: 'M10', menuName: 'สิทธิ์การเข้าถึงเมนู', group: 'ระบบประกันรายได้', access: acc('01', '02') },
  { menuCode: 'M11', menuName: 'ตั้งค่าระบบ', group: 'ระบบประกันรายได้', access: acc('01') },
  { menuCode: 'M12', menuName: 'Batch Job', group: 'ระบบประกันรายได้', access: acc('01') },
];

export const EMAIL_TEMPLATES: EmailTemplate[] = [
  { templateCode: 'EM-01', name: 'แจ้งผู้ดำเนินการลำดับถัดไป', subject: '[SBPGI] เอกสารประกันรายได้ {{doc_no}} — {{next_status}}', body: '<p>เรียน {{next_actor}}</p><p>เอกสารประกันรายได้เลขที่ <b>{{doc_no}}</b> (ร้าน {{store_name}}) ถูกส่งมายังขั้นตอนของท่านแล้ว สถานะปัจจุบัน: {{next_status}}</p><p>กรุณาเข้าระบบเพื่อพิจารณา: {{doc_url}}</p>', variables: ['doc_no', 'store_name', 'next_status', 'next_actor', 'doc_url'], to: 'ผู้ดำเนินการลำดับถัดไป', cc: 'ตาม status_email_rules', isCustomized: false },
  { templateCode: 'EM-02', name: 'แจ้งจบงาน (เสร็จสิ้น)', subject: '[SBPGI] เอกสาร {{doc_no}} เสร็จสิ้นดำเนินการ', body: '<p>เอกสาร <b>{{doc_no}}</b> ได้ดำเนินการเสร็จสิ้นแล้ว ยอดชดเชยรวม {{amount}} บาท</p>', variables: ['doc_no', 'amount'], to: 'ฝ่าย SBP DSA', cc: 'ฝ่ายบัญชี SBP', isCustomized: false },
  { templateCode: 'EM-03', name: 'แจ้งส่งกลับ (back-flow)', subject: '[SBPGI] เอกสาร {{doc_no}} ถูกส่งกลับเพื่อแก้ไข', body: '<p>เอกสาร <b>{{doc_no}}</b> ถูกส่งกลับจาก {{from_section}} เหตุผล: {{reason}}</p>', variables: ['doc_no', 'from_section', 'reason'], to: 'ผู้ดำเนินการขั้นก่อนหน้า', cc: '-', isCustomized: true },
  { templateCode: 'EM-04', name: 'เตือนงานค้างรายสัปดาห์', subject: '[SBPGI] เตือนงานค้าง {{count}} รายการ', body: '<p>ท่านมีงานค้างในระบบ {{count}} รายการ กรุณาดำเนินการ</p>', variables: ['count'], to: 'ผู้ปฏิบัติงานที่มีงานค้าง', cc: '-', isCustomized: false },
  { templateCode: 'EM-05', name: 'Escalation 30/45/60 วัน', subject: '[SBPGI] งานค้างเกินกำหนด {{days}} วัน', body: '<p>เอกสาร {{doc_no}} ค้างเกิน {{days}} วัน ส่งต่อหัวหน้า Section</p>', variables: ['doc_no', 'days'], to: 'หัวหน้า Section', cc: 'GM OPT', isCustomized: false },
  { templateCode: 'EM-06', name: 'สรุปเปิด workflow ราย DV', subject: '[SBPGI] สรุปการเปิด workflow ประจำวัน', body: '<p>เปิด workflow ใหม่ {{count}} รายการ (Y={{y}} / W={{w}} / N={{n}})</p>', variables: ['count', 'y', 'w', 'n'], to: 'ผู้ดูแลระบบ', cc: '-', isCustomized: false },
  { templateCode: 'EM-07', name: 'แจ้ง Job error', subject: '[SBPGI] Batch Job {{job_no}} ล้มเหลว', body: '<p>Batch Job {{job_no}} ({{job_name}}) ล้มเหลวเมื่อ {{time}}</p>', variables: ['job_no', 'job_name', 'time'], to: 'ผู้ดูแลระบบ Batch', cc: '-', isCustomized: false },
  { templateCode: 'EM-08', name: 'Watchdog ACK ค้าง', subject: '[SBPGI] พบ ACK ค้าง {{count}} รายการ', body: '<p>พบ ACK ค้างจากระบบ STA {{count}} รายการ เกิน 1 วัน</p>', variables: ['count'], to: 'ผู้ดูแลระบบ', cc: '-', isCustomized: false },
];

export const COMPETITORS: Competitor[] = [
  { competitorCode: 'C001', competitorName: '108 Shop' },
  { competitorCode: 'C007', competitorName: 'Lotus Express' },
  { competitorCode: 'C012', competitorName: 'CJ More' },
  { competitorCode: 'C015', competitorName: 'Big C Mini' },
  { competitorCode: 'C020', competitorName: 'Tops Daily' },
];

export const STORES: StoreLookup[] = [
  { storeCode: '00788', storeName: 'รัตนอุทิศ ซ.13', storeType: 'SP' },
  { storeCode: '00990', storeName: 'เซเว่นฯ รัตนาธิเบศร์ 12', storeType: 'NEW' },
  { storeCode: '01045', storeName: 'บางบัวทอง ก.ม.8', storeType: 'SP' },
  { storeCode: '01200', storeName: 'เซเว่นฯ บางบัวทอง 14', storeType: 'NEW' },
];

export const AUDIT: AuditLog[] = [
  { tableName: 'operator_assignments', actionType: 'EDIT', refKey: '1', change: 'zoneCode: RS → RN', reason: 'ปรับพื้นที่รับผิดชอบตามโครงสร้างใหม่', updatedBy: 'ภัชริดา ประดิษฐ์ทองใส', updatedAt: '2026-07-02 14:20' },
  { tableName: 'operator_assignments', actionType: 'ADD', refKey: '4', change: 'เพิ่ม: นางสาวพัชริดา · เจ้าหน้าที่ SBP DSA', reason: 'รับพนักงานใหม่', updatedBy: 'Admin BPM', updatedAt: '2026-06-28 09:10' },
  { tableName: 'external_factors', actionType: 'EDIT', refKey: 'F003', change: 'ชื่อ: ปิดถนน → การก่อสร้าง / ปิดถนน', reason: 'ขยายนิยามให้ครอบคลุมงานก่อสร้าง', updatedBy: 'Admin BPM', updatedAt: '2026-06-25 11:05' },
  { tableName: 'external_factors', actionType: 'ADD', refKey: 'F004', change: 'เพิ่ม: ทำเล/สถานีเปลี่ยน', reason: 'พบเคสจริงจากภาค RN', updatedBy: 'ภัชริดา ประดิษฐ์ทองใส', updatedAt: '2026-06-20 16:40' },
  { tableName: 'system_configs', actionType: 'EDIT', refKey: 'workflow.escalation_days', change: '[30, 60] → [30, 45, 60]', reason: 'เพิ่มขั้นเตือน 45 วันตามมติที่ประชุม', updatedBy: 'Admin', updatedAt: '2026-06-18 10:00' },
];

export const DASHBOARD: DashboardSummary = {
  waitingTasks: 24,
  storesThisMonth: 342,
  compensationThisMonth: 8420000,
  abnormalStores: 5,
  monthly: [
    { label: 'พ.ย.', value: 5.1 }, { label: 'ธ.ค.', value: 6.3 }, { label: 'ม.ค.', value: 5.8 },
    { label: 'ก.พ.', value: 7.2 }, { label: 'มี.ค.', value: 6.9 }, { label: 'เม.ย.', value: 8.1 },
    { label: 'พ.ค.', value: 7.6 }, { label: 'มิ.ย.', value: 8.42 },
  ],
  byStatus: [
    { label: 'รอฝ่าย SBP DSA', value: 2, color: '#f59e0b' },
    { label: 'รอเจ้าหน้าที่ SBP DSA', value: 1, color: '#7c3aed' },
    { label: 'รอฝ่ายส่งเสริมธุรกิจ', value: 2, color: '#2563eb' },
    { label: 'รอ GM OPT', value: 1, color: '#ea580c' },
    { label: 'รอ AVP OPT', value: 1, color: '#4f46e5' },
    { label: 'รอฝ่ายบัญชี SBP', value: 1, color: '#0f9f90' },
    { label: 'รอบัญชีปฏิบัติการภาค', value: 1, color: '#64748b' },
    { label: 'เสร็จสิ้น', value: 1, color: '#16a34a' },
  ],
};
