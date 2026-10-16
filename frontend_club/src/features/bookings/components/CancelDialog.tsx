'use client';

import { useState, useTransition } from 'react';

import { Button } from '@/ui/Button';
import { Choices } from '@/ui/Choices';
import { Dialog } from '@/ui/Dialog';
import fieldStyles from '@/ui/Field.module.css';
import { Form } from '@/ui/Form';
import { Notice } from '@/ui/Notice';

import { readCancelPreview, type CancelPreviewAnswer } from '../actions';
import { actRefusal, BOOKINGS_COPY, courtWithKind } from '../copy';
import {
  CANCEL_REASONS,
  type CancelGivesBack,
  type CancelOutcome,
  type CancelReason,
} from '../mappers';

import type { AskedToCancel } from './Asked';
import styles from './Bookings.module.css';
import { GameFields } from './GameFields';

const COPY = BOOKINGS_COPY.cancelDialog;
const REASONS = CANCEL_REASONS.map((reason) => ({
  value: reason,
  label: BOOKINGS_COPY.cancelReasons[reason],
}));

/** Each reason's preview, once read; `null` while it is being read, or before. */
type Previews = Readonly<Partial<Record<CancelReason, CancelPreviewAnswer | null>>>;

/**
 * What the cancel would do, as the dialog says it: the court that takes the game, and what
 * *Cancel the game anyway* would do instead; or the game called off, and its money.
 */
function Foretelling({
  outcome,
  givesBack,
}: {
  outcome: CancelOutcome;
  givesBack: CancelGivesBack;
}) {
  if (outcome.outcome === 'CALLED_OFF') {
    return <p className={styles.consequence}>{COPY.calledOff(givesBack)}</p>;
  }
  return (
    <>
      <p className={styles.consequence}>{COPY.moves(courtWithKind(outcome.court))}</p>{' '}
      <p className={styles.lead}>{COPY.anyway(givesBack)}</p>
    </>
  );
}

/** What the form posts of what the dialog said, so what lands is said against it. */
function ForetoldFields({ outcome }: { outcome: CancelOutcome }) {
  return (
    <>
      <input type="hidden" name="foretold" value={outcome.outcome} />
      {outcome.outcome === 'MOVED' ? (
        <>
          <input type="hidden" name="foretold_court_id" value={outcome.court.id} />
          <input type="hidden" name="foretold_court" value={outcome.court.name} />
        </>
      ) : null}
    </>
  );
}

/**
 * The reason starts unchosen for each game asked about: the players are told it, and what a
 * cancel does depends on it. Each choice reads the preview afresh; an answer is kept by the reason
 * it was read for, so one that arrives late never stands for another.
 */
function CancelForm({
  game,
  action,
  onClose,
}: {
  game: AskedToCancel;
  action: (form: FormData) => void;
  onClose: () => void;
}) {
  const [reason, setReason] = useState<CancelReason | null>(null);
  const [previews, setPreviews] = useState<Previews>({});
  const [, startReading] = useTransition();

  const choose = (chosen: CancelReason) => {
    setReason(chosen);
    setPreviews((read) => ({ ...read, [chosen]: null }));
    startReading(async () => {
      const answer = await readCancelPreview(game.id, chosen);
      setPreviews((read) => ({ ...read, [chosen]: answer }));
    });
  };
  const answer = reason === null ? null : (previews[reason] ?? null);
  const outcome = answer?.outcome ?? null;
  const refusal = answer?.refusal ?? null;

  return (
    <Form action={action} onSent={onClose} className={styles.dialogForm}>
      <GameFields act="cancel" id={game.id} name={game.name} />
      <input type="hidden" name="gives_back" value={game.givesBack} />
      {outcome === null ? null : <ForetoldFields outcome={outcome} />}
      <div>
        <Choices
          legend={COPY.reason}
          name="reason"
          options={REASONS}
          value={reason}
          onChange={choose}
        />
        <p className={fieldStyles.hint}>{COPY.reasonHint}</p>
      </div>
      {refusal === null ? null : (
        <Notice tone="error">
          {actRefusal({ code: refusal, name: game.name, act: 'cancel' })}
        </Notice>
      )}
      <div role="status">
        {reason === null || refusal !== null ? null : outcome === null ? (
          <p className={styles.lead}>{COPY.reading}</p>
        ) : (
          <Foretelling outcome={outcome} givesBack={game.givesBack} />
        )}
      </div>
      <div className={styles.dialogButtons}>
        <Button type="button" tone="secondary" onClick={onClose}>
          {COPY.back}
        </Button>
        <Button type="submit" tone="danger" disabled={outcome === null}>
          {COPY.confirm}
        </Button>
        {outcome?.outcome === 'MOVED' ? (
          <Button type="submit" tone="danger" name="anyway" value="true">
            {COPY.confirmAnyway}
          </Button>
        ) : null}
      </div>
    </Form>
  );
}

/**
 * **"Cancel the 19:00 game on Sat 3 Oct?"** (the screens B4, the mechanics §16.9, Q122): why,
 * which the players are told; then what this cancel would do, read for that reason. Another of
 * the club's courts may take the game, *This game moves to Court 3 · indoor*, nobody refunded,
 * and then *Cancel the game anyway* calls it off instead, for a club closing the whole hour. Or
 * the game is called off, its money spelled out (before the cut-off every hold let go and nobody
 * paying a fee; after it everyone refunded in full, the card fees not returned; nobody's record
 * either way). *Keep the game* or *Cancel the booking*, once it is said.
 */
export function CancelDialog({
  game,
  action,
  onClose,
}: {
  /** The game asked about, or `null` while nothing is asked. */
  game: AskedToCancel | null;
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
