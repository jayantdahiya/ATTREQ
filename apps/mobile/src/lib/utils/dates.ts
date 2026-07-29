// Local-calendar-day date helpers for Today + History.
//
// Deliberate divergence from the old RN app (product decision, mirrored from
// iOS TodayViewModel.todayWornDate / HistoryViewModel.dayKey): worn_date and
// History day-grouping use the user's LOCAL calendar day, not a UTC ISO slice.
// `new Date().toISOString().slice(0,10)` files a late-evening wear under
// tomorrow's date west of UTC; wearing is a diary action, so the day the user
// means is their local one. getFullYear/getMonth/getDate are all local.

const pad = (n: number): string => String(n).padStart(2, '0');

/** Today as 'YYYY-MM-DD' in the LOCAL calendar day. */
export function todayLocalISO(now: Date = new Date()): string {
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** The LOCAL calendar day ('YYYY-MM-DD') of a timestamp (ISO string or Date). */
export function localDayOf(input: string | Date): string {
  const d = typeof input === 'string' ? new Date(input) : input;
  if (Number.isNaN(d.getTime())) return typeof input === 'string' ? input : '';
  return todayLocalISO(d);
}

const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

/** Header date mono line, e.g. 'Monday 23/06' (weekday + day/month). */
export function dateLine(now: Date = new Date()): string {
  return `${WEEKDAYS[now.getDay()]} ${pad(now.getDate())}/${pad(now.getMonth() + 1)}`;
}

/** 'Good morning' <12, 'Good afternoon' 12–16, 'Good evening' from 17. */
export function greeting(now: Date = new Date()): string {
  const hour = now.getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

/** First word of a full name, 'there' when unknown (RN parity). */
export function firstName(fullName: string | null | undefined): string {
  const first = fullName?.trim().split(/\s+/)[0];
  return first && first.length > 0 ? first : 'there';
}

/**
 * Render a 'YYYY-MM-DD' day key as 'EEEE MM/dd' (long weekday, 2-digit
 * month/day), parsed as a LOCAL calendar day. Falls back to the raw key when
 * it doesn't parse.
 */
export function historyDateLabel(dayKey: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dayKey);
  if (!m) return dayKey;
  const [, year, month, day] = m;
  const d = new Date(Number(year), Number(month) - 1, Number(day));
  if (Number.isNaN(d.getTime())) return dayKey;
  return `${WEEKDAYS[d.getDay()]} ${month}/${day}`;
}
