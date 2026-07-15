/** ฟอร์แมตตัวเลขแบบมี comma (พอร์ตจาก fmt ใน sbp prototype) */
export function fmt(n: number): string {
  return n.toFixed(n % 1 ? 2 : 0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/** ปี ค.ศ. → พ.ศ. */
export function toBE(gregorianYear: number): number {
  return gregorianYear + 543;
}
