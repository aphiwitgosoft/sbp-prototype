import { Construction } from 'lucide-react';
import { PageHead } from './PageHead';
import { Card } from './Card';

/**
 * หน้า stub สำหรับหน้าที่ยัง port ไม่เสร็จ (stage การ full port)
 * route ต่อครบแล้ว — เนื้อหาจะถูกแทนด้วยไฟล์หน้าจริงเมื่อ port
 */
export function PagePlaceholder({ title, note }: { title: string; note?: string }) {
  return (
    <>
      <PageHead title={title} sub="ระบบประกันรายได้ (K2/SBPGI)" />
      <Card className="flex items-center gap-4 text-muted">
        <Construction size={28} className="text-warn" />
        <div>
          <div className="font-medium text-ink">อยู่ระหว่าง port เป็น React</div>
          <div className="text-[13px]">
            {note ?? 'route ต่อไว้แล้ว — เนื้อหาหน้านี้จะถูกแทนด้วยเวอร์ชัน React (Tailwind) ในรอบถัดไป'}
          </div>
        </div>
      </Card>
    </>
  );
}
