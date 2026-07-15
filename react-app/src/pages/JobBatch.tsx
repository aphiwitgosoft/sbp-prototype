import { useState } from 'react';
import { Cpu, FileUp, AlertTriangle, ShieldAlert, Play, Save } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Pill, Chip } from '@/components/ui/Pill';
import { Button } from '@/components/ui/Button';
import { Tabs } from '@/components/ui/Tabs';
import { DataState } from '@/components/ui/DataState';
import { DonutChart } from '@/components/charts/DonutChart';
import { BarChart } from '@/components/charts/BarChart';
import { SparkChart } from '@/components/charts/SparkChart';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import { fmt } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { Job, JobDetail } from '@/types/api';
import type { PillKind } from '@/types';

const STATUS_PILL: Record<string, PillKind> = { SUCCESS: 'ok', RUNNING: 'info', WARN: 'wait', FAILED: 'fail' };
const PHASES = ['A', 'B', 'C', 'D', 'E'];

export default function JobBatch() {
  const { toast } = useToast();
  const { data, loading, error } = useApi<{ items: Job[] }>(EP.jobs);
  const jobs = data?.items ?? [];
  const [sel, setSel] = useState<string | null>(null);
  const detail = useApi<JobDetail>(sel ? EP.job(sel) : null);

  const ok = jobs.filter((j) => j.lastStatus === 'SUCCESS').length;
  const warn = jobs.filter((j) => j.lastStatus === 'WARN' || j.lastStatus === 'FAILED').length;
  const perPhase = PHASES.map((p) => jobs.filter((j) => j.phase === p).length);

  return (
    <>
      <PageHead title="Batch Job Monitor" sub="ควบคุมและติดตาม Batch Jobs (FGI/FCS · 11 entry points)" />

      <div className="mb-6 grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard icon={Cpu} tone="blue" value={jobs.length || 11} label="Entry Point ทั้งหมด" />
        <StatCard icon={FileUp} tone="teal" value={8} label="Interface ไฟล์ รับ–ส่งภายนอก" />
        <StatCard icon={AlertTriangle} tone="amber" value={2} label="ACK ค้างเกิน 1 วัน" />
        <StatCard icon={ShieldAlert} tone="rose" value={3} label="ความเสี่ยง P0 ที่เปิดอยู่" />
      </div>

      {jobs.length > 0 && (
        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card>
            <CardHead title="สถานะรอบล่าสุด" />
            <div className="flex items-center gap-4">
              <DonutChart values={[ok, warn]} colors={['#16a34a', '#f59e0b']} center="Jobs" />
              <div className="flex flex-col gap-2.5 text-[12.5px] text-slate-600">
                <span className="flex items-center gap-2"><i className="h-3 w-3 rounded-[3px] bg-success" /> สำเร็จ <b className="text-ink">{ok}</b></span>
                <span className="flex items-center gap-2"><i className="h-3 w-3 rounded-[3px] bg-warn" /> เตือน / ACK ค้าง <b className="text-ink">{warn}</b></span>
              </div>
            </div>
          </Card>
          <Card><CardHead title="จำนวน Job ต่อเฟส (A–E)" /><BarChart values={perPhase} labels={PHASES} /></Card>
          <Card><CardHead title="ACK ค้าง (7 วันล่าสุด)" /><div className="pt-4"><SparkChart values={[1, 0, 2, 1, 3, 2, 2]} /></div></Card>
        </div>
      )}

      <Card className="mb-6">
        <CardHead title="รายการ Batch Job" right={<Chip>คลิกแถวเพื่อดูรายละเอียด</Chip>} />
        <DataState loading={loading} error={error} empty={jobs.length === 0}>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr><th>Job</th><th>ชื่องาน</th><th>เฟส</th><th>Cron</th><th>สถานะรอบล่าสุด</th><th>แถวที่ประมวลผล</th><th>เวลารันล่าสุด</th><th>เปิดใช้งาน</th></tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.jobNo} onClick={() => setSel(j.jobNo)} className={cn('cursor-pointer', sel === j.jobNo && 'bg-primary-soft/60')}>
                    <td className="num font-medium">{j.jobNo}</td>
                    <td>{j.name}</td>
                    <td>{j.phase}</td>
                    <td className="num text-muted">{j.cron}</td>
                    <td><Pill kind={STATUS_PILL[j.lastStatus]}>{j.lastStatus}</Pill></td>
                    <td className="num">{fmt(j.lastRows)}</td>
                    <td className="num text-muted">{j.lastRunAt.replace('T', ' ').slice(0, 16)}</td>
                    <td><span className={j.enabled ? 'text-success' : 'text-slate-400'}>{j.enabled ? 'เปิด' : 'ปิด'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </Card>

      {sel && (
        <Card accent>
          <DataState loading={detail.loading} error={detail.error}>
            {detail.data && (
              <>
                <div className="mb-1 flex items-center gap-2">
                  <h2 className="text-[16px] font-semibold text-ink">Job {detail.data.jobNo} · {detail.data.name}</h2>
                  <Chip>เฟส {detail.data.phase}</Chip>
                  <button className="ml-auto text-[13px] text-muted hover:text-ink" onClick={() => setSel(null)}>ปิด ✕</button>
                </div>
                <p className="mb-3 max-w-3xl text-[13px] text-muted">{detail.data.desc}</p>
                <div className="mb-4 flex flex-wrap gap-3">
                  <Button size="sm" onClick={() => toast(`สั่งรัน Job ${detail.data!.jobNo} ทันที (POST /jobs/${detail.data!.jobNo}/run)`, 'ok')}><Play size={15} /> สั่งรันทันที</Button>
                  <Chip>Main Class: {detail.data.mainClass}</Chip>
                </div>

                <Tabs
                  tabs={[
                    {
                      key: 'params',
                      label: 'พารามิเตอร์',
                      content: (
                        <>
                          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                            {detail.data.params.map((p) => (
                              <div key={p.key} className="field">
                                <label className="flex items-center gap-2">{p.key}
                                  <span className={cn('rounded px-1.5 py-0.5 text-[10px] font-semibold', p.editable ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500')}>{p.editable ? 'แก้ไขได้' : 'ค่าคงที่'}</span>
                                </label>
                                <input defaultValue={p.value} disabled={!p.editable} className={cn('num', !p.editable && 'bg-slate-50 text-slate-400')} />
                              </div>
                            ))}
                          </div>
                          <div className="mt-4 flex justify-end">
                            <Button size="sm" onClick={() => toast('บันทึกพารามิเตอร์แล้ว', 'ok')}><Save size={15} /> บันทึกพารามิเตอร์</Button>
                          </div>
                        </>
                      ),
                    },
                    {
                      key: 'flow',
                      label: 'Flowchart การทำงาน',
                      content: (
                        <ol className="relative ml-2 border-l-2 border-line pl-5">
                          {detail.data.flow.map((f, i) => (
                            <li key={i} className="mb-3">
                              <span className="absolute -left-[9px] flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white">{i + 1}</span>
                              <span className="text-[13.5px] text-slate-700">{f}</span>
                            </li>
                          ))}
                        </ol>
                      ),
                    },
                    {
                      key: 'db',
                      label: 'Database ที่ใช้',
                      content: (
                        <table className="data">
                          <thead><tr><th>ตาราง</th><th>สิทธิ์</th><th>บทบาท</th></tr></thead>
                          <tbody>
                            {detail.data.db.map((d, i) => (
                              <tr key={i}><td className="num">{d[0]}</td><td><span className={cn('pill', d[1] === 'R' ? 'info' : d[1] === 'W' ? 'ok' : 'violet')}>{d[1]}</span></td><td className="text-muted">{d[2]}</td></tr>
                            ))}
                          </tbody>
                        </table>
                      ),
                    },
                    {
                      key: 'runs',
                      label: 'ประวัติการรัน',
                      content: (
                        <table className="data">
                          <thead><tr><th>Run ID</th><th>สถานะ</th><th>แถว</th><th>ไฟล์</th><th>เริ่มเมื่อ</th><th>ใช้เวลา (วิ)</th></tr></thead>
                          <tbody>
                            {detail.data.runs.map((r) => (
                              <tr key={r.runId}>
                                <td className="num">{r.runId}</td>
                                <td><Pill kind={STATUS_PILL[r.status] ?? 'muted'}>{r.status}</Pill></td>
                                <td className="num">{fmt(r.rows)}</td>
                                <td className="text-muted">{r.file}</td>
                                <td className="num text-muted">{r.startedAt.replace('T', ' ').slice(0, 16)}</td>
                                <td className="num">{r.durationSec}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ),
                    },
                  ]}
                />
              </>
            )}
          </DataState>
        </Card>
      )}
    </>
  );
}
