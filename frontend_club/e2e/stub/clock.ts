/**
 * **The club's clock**, as the fakes read it: every club is in Poland, so a local day and hour
 * are Europe/Warsaw's, and an instant goes on the wire in UTC (the screens C5).
 */

const ZONE = 'Europe/Warsaw';

/** A local day `days` from today, as the wire writes one: `2026-10-12`. */
export function dayFromToday(days: number): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(Date.now() + days * 86_400_000));
}

/** The instant a club's local `day` and `hour` begin, as the wire writes one. */
export function atClubHour(day: string, hour: number, minute = 0): string {
  const [year = 0, month = 1, date = 1] = day.split('-').map(Number);
  const guess = Date.UTC(year, month - 1, date, hour, minute);
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: ZONE,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).formatToParts(guess);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    Number(parts.find((each) => each.type === type)?.value);
  const shown = Date.UTC(
    part('year'),
    part('month') - 1,
    part('day'),
    part('hour'),
    part('minute'),
  );
  return new Date(guess - (shown - guess)).toISOString();
}

/** The club's local day, `2026-10-12`, its ISO weekday (1 is Monday) and hour, of an instant. */
export function clubTime(instant: string): { day: string; weekday: number; hour: number } {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: ZONE,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    weekday: 'short',
  }).formatToParts(new Date(instant));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((each) => each.type === type)?.value ?? '';
  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return {
    day: `${part('year')}-${part('month')}-${part('day')}`,
    weekday: weekdays.indexOf(part('weekday')) + 1,
    hour: Number(part('hour')),
  };
}
