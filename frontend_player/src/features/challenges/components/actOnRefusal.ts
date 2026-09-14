/**
 * **What a refused act costs the screen, carried out** — `actRefusal`'s fold, applied.
 *
 * Four surfaces answer a refusal the same way — the challenge screen's two acts and the two doors
 * it draws, and the three controls composed onto the game screen (*Leave this game*, *Fill the
 * seat*, *Call it off*) — and the answer is one function rather than four copies of three lines:
 * **a re-read, never a toast**, for the codes that mean *this court is not what the screen thought
 * it was*, because the fold the re-read lands on is the sentence; **leaving**, for the one code
 * that says no challenge of yours has this id, because there is nothing behind the screen to stay
 * on; and nothing here for the rest, which the caller **says** in the sentence every write in this
 * feature says it with (`challengeErrorMessage`).
 *
 * The re-read is the caller's, because the read is theirs: the challenge screen re-reads its
 * detail, and a control on the game screen asks its composer to re-read the games list — the one
 * clock every fold on that screen is against. It is here in `components/` and not in `hooks/`
 * because it navigates, which is a component's act.
 */

import { router } from 'expo-router';

import type { AppError } from '@/shared/errors';

import { actRefusal } from '../domain/actRefusal';

export function actOnRefusal(error: AppError, onReRead: () => void): void {
  const next = actRefusal(error);
  if (next.kind === 'READ_IT_BACK') onReRead();
  if (next.kind === 'LEAVE') router.back();
}
