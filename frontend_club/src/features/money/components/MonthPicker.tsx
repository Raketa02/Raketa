'use client';

import { useRouter } from 'next/navigation';

import { PeriodPicker } from '@/ui/PeriodPicker';

import { MONEY_COPY } from '../copy';
import { monthHref, realMonth } from '../schemas';

const COPY = MONEY_COPY.month;

/**
 * **Go to a month**: a month box and *Show*, which opens that month. A month the box cannot read
 * opens this one. A browser with no month box draws a text box, which takes `2026-03` too.
 */
export function MonthPicker({ month }: { month: string }) {
  const router = useRouter();
  return (
    <PeriodPicker
      type="month"
      label={COPY.pick}
      show={COPY.show}
      period={month}
      onGo={(typed) => router.push(monthHref(realMonth(typed)))}
    />
  );
}
