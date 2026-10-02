'use client';

import { useRouter } from 'next/navigation';

import { PeriodPicker } from '@/ui/PeriodPicker';

import { BOOKINGS_COPY } from '../copy';
import type { BookingsFilter } from '../mappers';
import { dayHref, realDay } from '../schemas';

const COPY = BOOKINGS_COPY.day;

/**
 * **Go to a day**: a date box and *Show*, which opens that day under the same filter. A day the
 * box cannot read opens today.
 */
export function DayPicker({ day, filter }: { day: string; filter: BookingsFilter }) {
  const router = useRouter();
  return (
    <PeriodPicker
      type="date"
      label={COPY.pick}
      show={COPY.show}
      period={day}
      onGo={(typed) => router.push(dayHref({ date: realDay(typed), filter }))}
    />
  );
}
