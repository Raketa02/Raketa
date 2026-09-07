/**
 * The sheet's two answers, wired to the routes that take them.
 *
 * **Two mutations rather than one with a flag**, because they fail differently and only one of
 * them has anywhere to say so. A *yes* is a write the player is waiting on: it holds the
 * sheet open, draws its refusal over the button that failed, and the retry is that button. A
 * *not now* is a row nobody reads back — including the player who wrote it — so it fires as
 * the sheet closes and there is no surface left to report anything on.
 *
 * **A failed decline costs the question being asked again**, which is the state the app was in
 * before the row existed and is not worth a screen. What it must not do is keep the sheet up:
 * a modal held open over a failed write nobody can act on is the dead end
 * `SearchingLatch` was built to dissolve.
 *
 * ## The three writes are `player_profile`'s, and they arrive as ports
 *
 * Each of those hooks answers with the value **as the profile now holds it** and writes that
 * into the profile read's cache — the radius after its range and its step were re-checked, the
 * week after repeated cells were collapsed into the platform's reading order. Calling the
 * routes from here instead would leave the read holding what the client sent, which is the one
 * shape a cache cannot be corrected out of (`findAGame`, on the same seam).
 */

import { useMutation } from '@tanstack/react-query';

import {
  useChangeAvailability,
  useChangeSearchRadius,
  useDeclarePlayIntent,
} from '@/features/player_profile/types';
import type { AppError } from '@/shared/errors';

import {
  acceptPrompt,
  declinePrompt,
  type PromptAnswer,
  type PromptWrites,
} from '../use-cases/answerPrompt';

export function useAnswerPrompt() {
  const week = useChangeAvailability();
  const radius = useChangeSearchRadius();
  const intent = useDeclarePlayIntent();

  const writes: PromptWrites = {
    saveWeek: week.mutateAsync,
    saveRadius: radius.mutateAsync,
    declareIntent: intent.mutateAsync,
  };

  const accept = useMutation<void, AppError, PromptAnswer>({
    mutationFn: (answer) => acceptPrompt(answer, writes),
  });

  const decline = useMutation<void, AppError, PromptAnswer>({
    mutationFn: (answer) => declinePrompt(answer),
  });

  return { accept, decline };
}
