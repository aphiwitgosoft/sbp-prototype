import { useRef } from 'react';
import { Bold, Italic, Underline, List, ListOrdered, Table, RemoveFormatting } from 'lucide-react';
import { cn } from '@/lib/cn';

const COLORS = ['#c0392b', '#2f6fed', '#15803d', '#92670b'];

/** WYSIWYG editor (contentEditable + execCommand) — พอร์ตแนวคิดจาก plan-email.html */
export function RichEditor({
  initialHtml,
  variables,
  onChange,
}: {
  initialHtml: string;
  variables: string[];
  /** เรียกทุกครั้งที่ต้องอ่านค่าปัจจุบัน — parent อ่านผ่าน getHtml ก็ได้ */
  onChange?: (html: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const exec = (cmd: string, val?: string) => {
    document.execCommand(cmd, false, val);
    ref.current?.focus();
    onChange?.(ref.current?.innerHTML ?? '');
  };
  const insert = (html: string) => exec('insertHTML', html);
  const btn = 'flex h-8 w-8 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100';

  return (
    <div className="rounded-xl border border-line">
      <div className="flex flex-wrap items-center gap-1 border-b border-line bg-slate-50 p-1.5">
        <button type="button" className={btn} onClick={() => exec('bold')}><Bold size={16} /></button>
        <button type="button" className={btn} onClick={() => exec('italic')}><Italic size={16} /></button>
        <button type="button" className={btn} onClick={() => exec('underline')}><Underline size={16} /></button>
        <span className="mx-1 h-5 w-px bg-line" />
        {COLORS.map((c) => (
          <button key={c} type="button" className="h-6 w-6 rounded-md border border-line" style={{ background: c }} onClick={() => exec('foreColor', c)} />
        ))}
        <span className="mx-1 h-5 w-px bg-line" />
        <button type="button" className={btn} onClick={() => exec('insertUnorderedList')}><List size={16} /></button>
        <button type="button" className={btn} onClick={() => exec('insertOrderedList')}><ListOrdered size={16} /></button>
        <button
          type="button"
          className={btn}
          title="แทรกตาราง 3×2"
          onClick={() =>
            insert(
              '<table class="det" style="border-collapse:collapse;margin:6px 0"><tbody>' +
                Array.from({ length: 2 }, () => '<tr>' + Array.from({ length: 3 }, () => '<td style="border:1px solid #dbe3ee;padding:4px 8px">&nbsp;</td>').join('') + '</tr>').join('') +
                '</tbody></table><p></p>',
            )
          }
        >
          <Table size={16} />
        </button>
        <button type="button" className={btn} onClick={() => exec('removeFormat')}><RemoveFormatting size={16} /></button>
        <span className="mx-1 h-5 w-px bg-line" />
        <span className="text-[11px] text-muted">แทรกตัวแปร:</span>
        {variables.map((v) => (
          <button
            key={v}
            type="button"
            className="rounded-md bg-primary-soft px-2 py-1 text-[11px] font-medium text-primary hover:bg-blue-100"
            onClick={() => insert(`<span class="mf" contenteditable="false" style="background:#eaf2ff;color:#2f6fed;border-radius:5px;padding:0 5px">{{${v}}}</span>&nbsp;`)}
          >
            {`{{${v}}}`}
          </button>
        ))}
      </div>
      <div
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        onInput={() => onChange?.(ref.current?.innerHTML ?? '')}
        className={cn('min-h-[160px] px-4 py-3 text-[13.5px] leading-relaxed outline-none [&_ul]:list-disc [&_ol]:list-decimal [&_ul]:pl-6 [&_ol]:pl-6')}
        dangerouslySetInnerHTML={{ __html: initialHtml }}
      />
    </div>
  );
}
