'use client';

import Link from 'next/link';
import { useState } from 'react';

import { Button } from '@/ui/Button';
import { Chips } from '@/ui/Chips';
import { Choices } from '@/ui/Choices';
import { Form } from '@/ui/Form';
import { sentenceFor, sentencesFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { SelectField } from '@/ui/SelectField';
import { TextField } from '@/ui/TextField';
import { useFormFeedback } from '@/ui/useFormFeedback';

import type { ExceptionFormState } from '../actions';
import { COURTS_COPY, EXCEPTION_REFUSALS, FROM_HOURS, UNTIL_HOURS } from '../copy';
import type { BookedThen, Court } from '../mappers';
import { EMPTY_EXCEPTION, type ClosedFor, type ExceptionDraft, type WhichCourts } from '../schemas';

import styles from './CourtsAndPrices.module.css';

const COPY = COURTS_COPY.exceptions.form;

const SCOPES = [
  { value: 'all', label: COPY.all },
  { value: 'some', label: COPY.some },
] as const satisfies readonly { value: WhichCourts; label: string }[];

const WHENS = [
  { value: 'day', label: COPY.day },
  { value: 'days', label: COPY.days },
  { value: 'hours', label: COPY.hours },
] as const satisfies readonly { value: ClosedFor; label: string }[];

/** The hours, after a blank that chooses none. */
const FROM_OR_NONE = [{ value: '', label: COPY.choose }, ...FROM_HOURS];
const UNTIL_OR_NONE = [{ value: '', label: COPY.choose }, ...UNTIL_HOURS];

/**
 * Where a booking an exception would close is cancelled: the Bookings page on its day, naming it
 * (served by #563).
 */
function bookingPath(booked: BookedThen): string {
  return `/bookings?date=${booked.day}&booking=${booked.bookingId}`;
}

/**
 * ***Add an exception*** (the screens B3): which courts (all, or the ones ticked), when (a day,
 * several, or hours on a day) and a reason for the club's own records. Refused over a booking,
 * the sentence names the court and leads to the booking, which the club cancels first.
 */
export function ExceptionForm({
  courts,
  today,
  state,
  action,
  pending,
  onCancel,
}: {
  courts: readonly Court[];
  today: string;
  state: ExceptionFormState;
  action: (form: FormData) => void;
  pending: boolean;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<ExceptionDraft>(EMPTY_EXCEPTION);
  const feedback = useFormFeedback(state);
  const sentences = sentencesFor(feedback.refusals, EXCEPTION_REFUSALS);
  const formSentence = sentenceFor(feedback.formRefusal, EXCEPTION_REFUSALS);
  const booked =
    feedback.formRefusal === 'court_booked_then' && state.bookedThen !== null
      ? state.bookedThen
      : null;
  const bookedCourt = courts.find((court) => court.id === booked?.courtId);

  const change = (next: Partial<ExceptionDraft>, field: 'courts' | 'days' | 'hours' | 'reason') => {
    setDraft({ ...draft, ...next });
    feedback.edit(field);
  };

  return (
    <div className={styles.subform}>
      <Form action={action} className={styles.form}>
        {formSentence === null ? null : (
          <Notice tone="error">
            {booked !== null && bookedCourt !== undefined
              ? COURTS_COPY.exceptions.bookedThen(bookedCourt.name)
              : formSentence}
            {booked === null ? null : (
              <Link href={bookingPath(booked)} className={styles.noticeLink}>
                {COURTS_COPY.exceptions.seeBooking}
              </Link>
            )}
          </Notice>
        )}
        <Choices
          legend={COPY.scope}
          name="scope"
          options={SCOPES}
          value={draft.scope}
          onChange={(scope) => change({ scope }, 'courts')}
        />
        {draft.scope === 'some' ? (
          <Chips
            legend={COPY.courts}
            name="court"
            options={courts.map((court) => ({ value: court.id, label: court.name }))}
            selected={draft.courtIds}
            onToggle={(id) => {
              const ticked = new Set(draft.courtIds);
              if (ticked.has(id)) ticked.delete(id);
              else ticked.add(id);
              // In the club's order, as the backend lists an exception's courts.
              const courtIds = courts.map((court) => court.id).filter((each) => ticked.has(each));
              change({ courtIds }, 'courts');
            }}
            error={sentences.courts}
          />
        ) : null}
        <Choices
          legend={COPY.when}
          name="when"
          options={WHENS}
          value={draft.when}
          onChange={(when) => change({ when }, 'days')}
        />
        <div className={styles.fields}>
          {draft.when === 'days' ? (
            <>
              <TextField
                label={COPY.first}
                name="first_day"
                type="date"
                min={today}
                value={draft.firstDay}
                onChange={(event) => change({ firstDay: event.target.value }, 'days')}
              />
              <TextField
                label={COPY.last}
                name="last_day"
                type="date"
                min={today}
                value={draft.lastDay}
                onChange={(event) => change({ lastDay: event.target.value }, 'days')}
                error={sentences.days}
              />
            </>
          ) : (
            <TextField
              label={COPY.dayLabel}
              name="first_day"
              type="date"
              min={today}
              value={draft.firstDay}
              onChange={(event) => change({ firstDay: event.target.value }, 'days')}
              error={sentences.days}
            />
          )}
          {draft.when === 'hours' ? (
            <>
              <SelectField
                label={COPY.from}
                name="from"
                options={FROM_OR_NONE}
                value={draft.from}
                onChange={(event) => change({ from: event.target.value }, 'hours')}
              />
              <SelectField
                label={COPY.until}
                name="until"
                options={UNTIL_OR_NONE}
                value={draft.until}
                onChange={(event) => change({ until: event.target.value }, 'hours')}
                error={sentences.hours}
              />
            </>
          ) : null}
        </div>
        <TextField
          label={COPY.reason}
          name="reason"
          hint={COPY.reasonHint}
          placeholder={COPY.reasonPlaceholder}
          autoComplete="off"
          value={draft.reason}
          onChange={(event) => change({ reason: event.target.value }, 'reason')}
          error={sentences.reason}
        />
        <div className={styles.buttons}>
          <Button type="button" tone="outline" onClick={onCancel}>
            {COPY.cancel}
          </Button>
          <Button type="submit" disabled={pending}>
            {pending ? COPY.adding : COPY.add}
          </Button>
        </div>
      </Form>
    </div>
  );
}
