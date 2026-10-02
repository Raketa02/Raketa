'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/ui/Button';
import { Form } from '@/ui/Form';
import { formText } from '@/ui/forms';
import { TextField } from '@/ui/TextField';

import { BOOKINGS_COPY } from '../copy';
import type { BookingsFilter } from '../mappers';
import { dayHref, realDay } from '../schemas';

import styles from './Bookings.module.css';

const COPY = BOOKINGS_COPY.day;

/**
 * **Go to a day**: a date box and *Show*, which opens that day under the same filter. A day the
 * box cannot read opens today. It goes only when asked, since a date box changes with each digit
 * typed into its year.
 */
export function DayPicker({ day, filter }: { day: string; filter: BookingsFilter }) {
  const router = useRouter();
  const [value, setValue] = useState(day);
  const [shown, setShown] = useState(day);

  // Another day was opened, by an arrow or a link: the box says which.
  if (shown !== day) {
    setShown(day);
    setValue(day);
  }

  return (
    <Form
      action={(form) => router.push(dayHref({ date: realDay(formText(form, 'date')), filter }))}
      className={styles.picker}
    >
      <TextField
        type="date"
        label={COPY.pick}
        name="date"
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
      <Button type="submit" tone="secondary">
        {COPY.show}
      </Button>
    </Form>
  );
}
