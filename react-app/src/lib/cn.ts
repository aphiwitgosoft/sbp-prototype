/** join class names (ตัด falsy ออก) — เบา ไม่ต้องพึ่ง lib */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ');
}
