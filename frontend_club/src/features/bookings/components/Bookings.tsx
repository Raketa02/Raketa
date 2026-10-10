import { CHECK_IN_COPY } from '@/features/check-in/copy';
import { CHECK_IN_PATH } from '@/features/check-in/schemas';
import { ButtonLink } from '@/ui/Button';
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
 * booking, which is marked. *Check in* is at the top right when the club checks players in.
 */
export function Bookings({
  day,
  clubName,
  pointedAt,
  checksIn,
}: {
  day: BookingsDay;
  /** As the players read it. */
  clubName: string;
  pointedAt: string | null;
  checksIn: boolean;
}) {
  const at = (date: string) =>
    dayHref({ date: date === day.today ? null : date, filter: day.filter });
  return (
    <>
      <PageHeader
        caption={COPY.caption}
        title={COPY.title}
        aside={
          checksIn ? (
            <ButtonLink href={CHECK_IN_PATH} tone="primary">
              {CHECK_IN_COPY.title}
            </ButtonLink>
          ) : undefined
        }
      />
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
        <DayBookings
          key={`${day.day} ${day.filter}`}
          day={day}
          clubName={clubName}
          pointedAt={pointedAt}
        />
      </Card>
    </>
  );
}
