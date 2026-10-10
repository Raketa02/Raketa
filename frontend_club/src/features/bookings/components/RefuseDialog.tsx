'use client';

import { useState } from 'react';

import { Button } from '@/ui/Button';
import { Dialog } from '@/ui/Dialog';
import { Form } from '@/ui/Form';
import { TextField } from '@/ui/TextField';

import { BOOKINGS_COPY } from '../copy';
import { REFUSAL_NOTE_MOST } from '../schemas';

import type { Asked } from './Asked';
import styles from './Bookings.module.css';
import { GameFields } from './GameFields';

const COPY = BOOKINGS_COPY.refuseDialog;

/** The note starts empty for each request asked about. */
function RefuseForm({
  game,
  action,
  onClose,
}: {
  game: Asked;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  const [note, setNote] = useState('');
  return (
    <Form action={action} onSent={onClose} className={styles.dialogForm}>
      <GameFields act="refuse" id={game.id} name={game.name} />
      <TextField
        label={COPY.note}
        hint={COPY.noteHint}
        name="note"
        maxLength={REFUSAL_NOTE_MOST}
        value={note}
        onChange={(event) => setNote(event.target.value)}
      />
      <div className={styles.dialogButtons}>
        <Button type="button" tone="secondary" onClick={onClose}>
          {COPY.back}
        </Button>
        <Button type="submit" tone="danger">
          {COPY.confirm}
        </Button>
      </div>
    </Form>
  );
}

/**
 * **"Refuse the 19:00 game on Sat 3 Oct?"** (the mechanics §16.8): what refusing means, with the
 * words the players will read, a note for the club's own records, then *Back* or *Refuse*.
 * Refusing posts it and closes the question at once; the page says what came of it.
 */
export function RefuseDialog({
  game,
  clubName,
  action,
  onClose,
}: {
  /** The request asked about, or `null` while nothing is asked. */
  game: Asked | null;
  /** As the players read it. */
  clubName: string;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  return (
    <Dialog
      open={game !== null}
      title={game === null ? '' : COPY.title(game.name)}
      onClose={onClose}
    >
      <p className={styles.lead}>{COPY.lead(clubName)}</p>
      {game === null ? null : (
        <RefuseForm key={game.id} game={game} action={action} onClose={onClose} />
      )}
    </Dialog>
  );
}
