'use client';

import { useState } from 'react';

import { sportName } from '@/features/club-details/mappers';
import { Button } from '@/ui/Button';
import { Choices } from '@/ui/Choices';
import { Dialog } from '@/ui/Dialog';
import { Form } from '@/ui/Form';
import { Notice } from '@/ui/Notice';

import type { FreeCourtsAnswer } from '../actions';
import { actRefusal, BOOKINGS_COPY, courtWithKind } from '../copy';
import type { FreeCourt } from '../mappers';

import type { Asked } from './Asked';
import styles from './Bookings.module.css';
import { GameFields } from './GameFields';

const COPY = BOOKINGS_COPY.moveDialog;

/** The courts to choose from; none is chosen until the desk chooses. */
function MoveForm({
  game,
  courts,
  action,
  onClose,
}: {
  game: Asked;
  courts: readonly FreeCourt[];
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  const [chosen, setChosen] = useState<string | null>(null);
  return (
    <Form action={action} onSent={onClose} className={styles.dialogForm}>
      <GameFields act="move" id={game.id} name={game.name} />
      <Choices
        legend={COPY.to}
        name="court_id"
        options={courts.map((court) => ({ value: court.id, label: courtWithKind(court) }))}
        value={chosen}
        onChange={setChosen}
      />
      <div className={styles.dialogButtons}>
        <Button type="button" tone="secondary" onClick={onClose}>
          {COPY.back}
        </Button>
        <Button type="submit" tone="secondary" disabled={chosen === null}>
          {COPY.confirm}
        </Button>
      </div>
    </Form>
  );
}

/**
 * **"Move the 19:00 game on Sat 3 Oct"** (the screens B4, the mechanics §16.16): the free courts
 * of its sport at its hour of its kind of court, or indoor for an outdoor game, each with its
 * kind, read as it opens, to choose one of (Q122). None free says what to do instead; a game that can no longer be moved says why.
 */
export function MoveDialog({
  game,
  answer,
  action,
  onClose,
}: {
  /** The game asked about, or `null` while nothing is asked. */
  game: Asked | null;
  /** The free courts, or why there are none to read; `null` while they are being read. */
  answer: FreeCourtsAnswer | null;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  /** What the dialog says while it has no courts to offer: reading, why not, or none free. */
  const without = (asked: Asked, read: FreeCourtsAnswer | null) => {
    if (read === null) {
      return (
        <p role="status" className={styles.lead}>
          {COPY.reading}
        </p>
      );
    }
    if (read.refusal !== null) {
      return (
        <Notice tone="error">
          {actRefusal({ code: read.refusal, name: asked.name, act: 'move' })}
        </Notice>
      );
    }
    return (
      <p className={styles.none}>
        {COPY.none(sportName(asked.sport).toLowerCase(), asked.hour.from, asked.court.indoor)}
      </p>
    );
  };
  return (
    <Dialog
      open={game !== null}
      title={game === null ? '' : COPY.title(game.name)}
      onClose={onClose}
    >
      {game === null ? null : (
        <>
          <p className={styles.lead}>{COPY.lead(courtWithKind(game.court))}</p>
          {answer !== null && answer.refusal === null && answer.courts.length > 0 ? (
            <MoveForm
              key={game.id}
              game={game}
              courts={answer.courts}
              action={action}
              onClose={onClose}
            />
          ) : (
            <>
              {without(game, answer)}
              <div className={styles.dialogButtons}>
                <Button type="button" tone="secondary" onClick={onClose}>
                  {COPY.back}
                </Button>
              </div>
            </>
          )}
        </>
      )}
    </Dialog>
  );
}
