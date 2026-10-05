'use client';

import { Button } from '@/ui/Button';

import { BOOKINGS_COPY, countdown } from '../copy';
import type { AnswerBy } from '../mappers';

import styles from './Bookings.module.css';
import { GameFields } from './GameFields';
import { useCountdown } from './useCountdown';

const COPY = BOOKINGS_COPY.request;

/**
 * **A request's answer** (the mechanics §16.8): the countdown, **Accept**, a form that is only
 * its button, and **Refuse**, which asks first. Once the time runs out neither is offered: the
 * request is called off as unanswered.
 */
export function RequestActions({
  id,
  name,
  answerBy,
  action,
  pending,
  onRefuse,
}: {
  id: string;
  /** The game as the page names it: *the 19:00 game on Sat 3 Oct*. */
  name: string;
  answerBy: AnswerBy;
  action: (form: FormData) => void;
  pending: boolean;
  onRefuse: () => void;
}) {
  const left = useCountdown(answerBy);
  const over = left <= 0;
  return (
    <div className={styles.request}>
      <p role="timer" className={styles.countdown} data-over={over}>
        {over ? COPY.over : COPY.left(countdown(left))}
      </p>
      {over ? null : (
        <div className={styles.actions}>
          <form action={action}>
            <GameFields act="accept" id={id} name={name} />
            <Button
              type="submit"
              tone="secondary"
              disabled={pending}
              aria-label={`${COPY.accept} ${name}`}
            >
              {COPY.accept}
            </Button>
          </form>
          <Button
            type="button"
            tone="danger"
            disabled={pending}
            onClick={onRefuse}
            aria-label={`${COPY.refuse} ${name}`}
          >
            {COPY.refuse}
          </Button>
        </div>
      )}
    </div>
  );
}
