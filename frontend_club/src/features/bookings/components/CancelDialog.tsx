'use client';

import { useState } from 'react';

import { Button } from '@/ui/Button';
import { Choices } from '@/ui/Choices';
import { Dialog } from '@/ui/Dialog';
import fieldStyles from '@/ui/Field.module.css';
import { Form } from '@/ui/Form';

import { BOOKINGS_COPY } from '../copy';
import { CANCEL_REASONS, type CancelReason } from '../mappers';

import type { Asked } from './Asked';
import styles from './Bookings.module.css';
import { GameFields } from './GameFields';

const COPY = BOOKINGS_COPY.cancelDialog;
const REASONS = CANCEL_REASONS.map((reason) => ({
  value: reason,
  label: BOOKINGS_COPY.cancelReasons[reason],
}));

/** The reason starts unchosen for each game asked about: the players are told it. */
function CancelForm({
  game,
  action,
  onClose,
}: {
  game: Asked;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  const [reason, setReason] = useState<CancelReason | null>(null);
  return (
    <Form action={action} onSent={onClose} className={styles.dialogForm}>
      <GameFields act="cancel" id={game.id} name={game.name} />
      <div>
        <Choices
          legend={COPY.reason}
          name="reason"
          options={REASONS}
          value={reason}
          onChange={setReason}
        />
        <p className={fieldStyles.hint}>{COPY.reasonHint}</p>
      </div>
      <p className={styles.consequence}>{COPY.consequence}</p>
      <div className={styles.dialogButtons}>
        <Button type="button" tone="secondary" onClick={onClose}>
          {COPY.back}
        </Button>
        <Button type="submit" tone="danger" disabled={reason === null}>
          {COPY.confirm}
        </Button>
      </div>
    </Form>
  );
}

/**
 * **"Cancel the 19:00 game on Sat 3 Oct?"** (the mechanics §16.9): why, which the players are
 * told; what it comes to, spelled out (everyone refunded in full, the card fees not returned,
 * nobody's record); then *Keep the game* or *Cancel the booking*, once a reason is chosen.
 */
export function CancelDialog({
  game,
  action,
  onClose,
}: {
  /** The game asked about, or `null` while nothing is asked. */
  game: Asked | null;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  return (
    <Dialog
      open={game !== null}
      title={game === null ? '' : COPY.title(game.name)}
      onClose={onClose}
    >
      {game === null ? null : (
        <CancelForm key={game.id} game={game} action={action} onClose={onClose} />
      )}
    </Dialog>
  );
}
