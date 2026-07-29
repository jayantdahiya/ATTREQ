import { dateLine, greeting, historyDateLabel, localDayOf, todayLocalISO } from '@/lib/utils/dates';

describe('date helpers', () => {
  it('todayLocalISO formats the LOCAL calendar day as YYYY-MM-DD', () => {
    // Local-time constructor — no timezone slice, so the day never shifts.
    const d = new Date(2026, 5, 23, 23, 30); // 23 June 2026, 23:30 local
    expect(todayLocalISO(d)).toBe('2026-06-23');
  });

  it('todayLocalISO zero-pads month and day', () => {
    expect(todayLocalISO(new Date(2026, 0, 5))).toBe('2026-01-05');
  });

  it('localDayOf returns the local day of a timestamp', () => {
    expect(localDayOf(new Date(2026, 11, 1, 8, 0))).toBe('2026-12-01');
  });

  it('localDayOf passes an unparseable string through unchanged', () => {
    expect(localDayOf('not-a-date')).toBe('not-a-date');
  });

  it('greeting bins by hour (morning / afternoon / evening)', () => {
    expect(greeting(new Date(2026, 0, 1, 8))).toBe('Good morning');
    expect(greeting(new Date(2026, 0, 1, 11, 59))).toBe('Good morning');
    expect(greeting(new Date(2026, 0, 1, 12))).toBe('Good afternoon');
    expect(greeting(new Date(2026, 0, 1, 16, 59))).toBe('Good afternoon');
    expect(greeting(new Date(2026, 0, 1, 17))).toBe('Good evening');
    expect(greeting(new Date(2026, 0, 1, 23))).toBe('Good evening');
  });

  it('dateLine renders weekday + dd/MM', () => {
    // 23 June 2026 is a Tuesday.
    expect(dateLine(new Date(2026, 5, 23, 9))).toBe('Tuesday 23/06');
  });

  it('historyDateLabel renders a day key as weekday + MM/dd, else the raw key', () => {
    expect(historyDateLabel('2026-06-23')).toBe('Tuesday 06/23');
    expect(historyDateLabel('garbage')).toBe('garbage');
  });
});
