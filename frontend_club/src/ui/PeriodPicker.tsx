'use client';

import { useState } from 'react';

import { Button } from './Button';
import { Form } from './Form';
import { formText } from './forms';
import styles from './PeriodBar.module.css';
import { TextField } from './TextField';

/**
 * **Go to a period**: a date or a month box, and *Show*, which hands `onGo` what the box held.
 * It goes only when asked, since a box like this changes with each digit typed into its year.
 * Another period opened by an arrow or a link puts its own value in the box.
 */
export function PeriodPicker({
  type,
  label,
  show,
  period,
  onGo,
}: {
  type: 'date' | 'month';
  label: string;
  show: string;
  /** The period shown, as the box writes it: `2026-10-12`, `2026-10`. */
  period: string;
  onGo: (typed: string) => void;
}) {
  const [value, setValue] = useState(period);
  const [shown, setShown] = useState(period);

  if (shown !== period) {
    setShown(period);
    setValue(period);
  }

  return (
    <Form action={(form) => onGo(formText(form, 'period').trim())} className={styles.picker}>
      <TextField
        type={type}
        label={label}
        name="period"
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
      <Button type="submit" tone="secondary">
        {show}
      </Button>
    </Form>
  );
}
