'use client';

import { useActionState, useEffect, useState, useTransition } from 'react';

import { actOnBooking, readFreeCourts, type FreeCourtsAnswer } from '../actions';
import { BOOKINGS_COPY } from '../copy';
import type { BookingsDay } from '../mappers';

import { ActNotice, NOTHING_DONE } from './ActNotice';
import type { Asked } from './Asked';
import styles from './Bookings.module.css';
import { BookingsTable, rowId } from './BookingsTable';
import { CancelDialog } from './CancelDialog';
import { MoveDialog } from './MoveDialog';
import { RefuseDialog } from './RefuseDialog';

/** The question open over the day, if any. */
type Asking =
  | { readonly kind: 'refuse'; readonly game: Asked }
  | { readonly kind: 'move'; readonly game: Asked }
  | { readonly kind: 'cancel'; readonly game: Asked };

/**
 * **The day's games and what the club does to them**: the table (or the day's empty line), the
 * questions *Refuse*, *Move* and *Cancel* ask first, and over it all what came of the last act.
 * *Move* reads the free courts as it opens, keeping the answer for the game it asked about.
 */
export function DayBookings({ day, pointedAt }: { day: BookingsDay; pointedAt: string | null }) {
  const [state, act, acting] = useActionState(actOnBooking, NOTHING_DONE);
  const [asking, setAsking] = useState<Asking | null>(null);
  const [free, setFree] = useState<{ id: string; answer: FreeCourtsAnswer } | null>(null);
  const [, startReading] = useTransition();

  // A link pointed at one booking: bring it into view.
  useEffect(() => {
    if (pointedAt !== null) {
      document.getElementById(rowId(pointedAt))?.scrollIntoView({ block: 'center' });
    }
  }, [pointedAt]);

  const close = () => setAsking(null);
  const move = (game: Asked) => {
    setAsking({ kind: 'move', game });
    setFree(null);
    startReading(async () => {
      const answer = await readFreeCourts(game.id);
      setFree({ id: game.id, answer });
    });
  };
  const moving = asking?.kind === 'move' ? asking.game : null;

  return (
    <>
      <ActNotice state={state} />
      {day.bookings.length === 0 ? (
        <p className={styles.none}>{BOOKINGS_COPY.empty[day.filter]}</p>
      ) : (
        <BookingsTable
          bookings={day.bookings}
          pointedAt={pointedAt}
          action={act}
          pending={acting}
          onRefuse={(game) => setAsking({ kind: 'refuse', game })}
          onMove={move}
          onCancel={(game) => setAsking({ kind: 'cancel', game })}
        />
      )}
      <RefuseDialog
        game={asking?.kind === 'refuse' ? asking.game : null}
        action={act}
        onClose={close}
      />
      <MoveDialog
        game={moving}
        answer={moving !== null && free?.id === moving.id ? free.answer : null}
        action={act}
        onClose={close}
      />
      <CancelDialog
        game={asking?.kind === 'cancel' ? asking.game : null}
        action={act}
        onClose={close}
      />
    </>
  );
}
