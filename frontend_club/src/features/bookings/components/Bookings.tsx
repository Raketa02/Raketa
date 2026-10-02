import Link from 'next/link';

import { CHECK_IN_COPY } from '@/features/check-in/copy';
import { CHECK_IN_PATH } from '@/features/check-in/schemas';
import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { PageHeader } from '@/ui/PageHeader';
import { Segments } from '@/ui/Segments';
import { TextLink } from '@/ui/TextLink';

import { BOOKINGS_COPY, dayTitle } from '../copy';
import { FILTERS, type BookingsDay } from '../mappers';
import { dayAfter, dayHref } from '../schemas';

import styles from './Bookings.module.css';
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
  pointedAt,
  checksIn,
}: {
  day: BookingsDay;
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
        <div className={styles.dayBar}>
          <nav aria-label={COPY.day.label} className={styles.dayNav}>
            <Link
              href={at(dayAfter(day.day, -1))}
              className={styles.arrow}
              aria-label={COPY.day.previous}
            >
              ‹
            </Link>
            <h2 id="day-title" className={styles.dayTitle}>
              {dayTitle(day.day, day.today)}
            </h2>
            <Link
              href={at(dayAfter(day.day, 1))}
              className={styles.arrow}
              aria-label={COPY.day.next}
            >
              ›
            </Link>
            {day.day === day.today ? null : (
              <TextLink href={dayHref({ date: null, filter: day.filter })}>
                {COPY.day.today}
              </TextLink>
            )}
          </nav>
          <DayPicker day={day.day} filter={day.filter} />
        </div>
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
