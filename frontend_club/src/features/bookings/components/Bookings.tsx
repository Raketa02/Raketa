import { Card } from '@/ui/Card';
import { PageHeader } from '@/ui/PageHeader';
import { PeriodBar } from '@/ui/PeriodBar';
import { Segments } from '@/ui/Segments';

import { BOOKINGS_COPY, dayTitle } from '../copy';
import { FILTERS, type BookingsDay } from '../mappers';
import { dayAfter, dayHref } from '../schemas';

import { DayBookings } from './DayBookings';
import { DayPicker } from './DayPicker';

const COPY = BOOKINGS_COPY;

/**
 * **Bookings** (the screens B4, the mechanics §16.7): one day at a time, *‹ Today ›* and a date
 * box, the filters with the day's count under each, and the day's games. A link may point at one
 * booking, which is marked.
 */
export function Bookings({ day, pointedAt }: { day: BookingsDay; pointedAt: string | null }) {
  const at = (date: string) =>
    dayHref({ date: date === day.today ? null : date, filter: day.filter });
  return (
    <>
      <PageHeader caption={COPY.caption} title={COPY.title} />
      <Card labelledBy="day-title">
        <PeriodBar
          label={COPY.day.label}
          titleId="day-title"
          title={dayTitle(day.day, day.today)}
          previous={{ href: at(dayAfter(day.day, -1)), label: COPY.day.previous }}
          next={{ href: at(dayAfter(day.day, 1)), label: COPY.day.next }}
          back={
            day.day === day.today
              ? null
              : { href: dayHref({ date: null, filter: day.filter }), label: COPY.day.today }
          }
          picker={<DayPicker day={day.day} filter={day.filter} />}
        />
        <Segments
          label={COPY.filters.label}
          items={FILTERS.map((filter) => ({
            href: dayHref({ date: day.day === day.today ? null : day.day, filter }),
            label: COPY.filters.names[filter],
            count: day.counts[filter],
            current: filter === day.filter,
          }))}
        />
        <DayBookings key={`${day.day} ${day.filter}`} day={day} pointedAt={pointedAt} />
      </Card>
    </>
  );
}
