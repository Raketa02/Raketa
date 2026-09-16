/**
 * The two sentences an answer can leave standing on either surface — **paused, not failed**,
 * and **refused, and why** — drawn under the header on the deck and in the radar's gutter.
 *
 * Paused is `networkMode: 'online'` holding a write until the connection returns: the card has
 * left, or the row is marked, and the amber sentence says the act resumes. Refused is the
 * coral sentence above whatever is back — the card, or the unmarked row — because a refusal
 * returns it, and the retry is the control the player already pressed. Nothing where neither.
 */

import type { AppError } from '@/shared/errors';
import { offlineMessage } from '@/shared/errors';
import { Note } from '@/shared/ui';

import { playErrorMessage } from './playErrorMessage';

export interface AnswerNotesProps {
  readonly paused: boolean;
  readonly error: AppError | null;
}

export function AnswerNotes({ paused, error }: AnswerNotesProps) {
  return (
    <>
      {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
      {error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {playErrorMessage(error)}
        </Note>
      ) : null}
    </>
  );
}
