/**
 * **What waits in Needs your answer, and what is new in it** ([#817](https://github.com/Raketa02/Raketa/issues/817),
 * [#819](https://github.com/Raketa02/Raketa/issues/819), ADR-0205 §1, §3) — the four sections' counts
 * and the envelope's badge, off Home's one read, and the visit that clears the badge, for the shell's
 * envelope and sheet.
 *
 * ## One read, so the watermark covers what was shown
 *
 * **All four sections ride on `GET /home`**: the payments to confirm, the friends game invitations,
 * the friend requests and the asks for a level. With them comes `needs_your_answer`: how many of
 * them arrived since the sheet was last closed, on any phone, and **this read's watermark**, the
 * newest arrival among them. The payments to confirm came onto Home's read with the watermark
 * (#815) for this reason: drawn from their own read, a payment Home's read covered could be marked
 * seen without the sheet having shown it. You › Payments keeps that read. A failed or slow Home
 * read counts nothing, so it draws no envelope (decision log §3.6), and Home's usual re-reads retry.
 *
 * ## The visit
 *
 * **When the sheet goes for good, the visit names the watermark of the newest read the sheet was
 * shown on** (`useNeedsYourAnswerVisit`, `watermarkShown`): open, never beneath a record or a fill's
 * sheet. Every item of that read was on screen, so everything up to its watermark was seen — what
 * arrived while the sheet was open included, once a re-read brought it in — and whatever reaches the
 * server after it is still new.
 *
 * - **The badge goes at the close, and nothing is written into Home's read** (`newCountAfter`): a
 *   read whose watermark is no later than a visit this phone sent — on its way or recorded — holds
 *   nothing new. So a read already in flight, or one a push or a return starts before the visit
 *   lands, keeps the badge gone and keeps every answer it carries; **Home is read again once the
 *   visit lands**, so the badge is then whatever the server counts. A visit that fails for good
 *   counts for nothing, and the badge is back.
 * - **Retried, and held while offline**, as no fill write is: the route records a watermark only
 *   when it is later than the last and answers `204` either way, so a repeat moves nothing, and
 *   since the watermark names a read, a visit landing late marks seen nothing the player did not
 *   see — the bell's visit, which names no read, is the opposite case.
 */

import { useMutation, useMutationState, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef } from 'react';

import type { AppError } from '@/shared/errors';
import { shouldRetryQuery } from '@/shared/lib/query-client';

import { newCountAfter, watermarkShown } from '../domain/home';
import { recordNeedsYourAnswerVisit } from '../use-cases/home';

import { proposalKeys } from './proposalKeys';
import { useHome, useFriendsGamesWaiting, type FriendsGamesWaiting } from './useHome';

export interface AnswersWaiting {
  /**
   * Each section's count, in the sheet's order — *TO CONFIRM*, *FRIENDS GAME*, *FRIEND REQUESTS*,
   * *ASKED FOR A LEVEL* — and `undefined` while Home's read is not in yet, or refused: nothing waits.
   */
  readonly counts: readonly (number | undefined)[];
  /**
   * **Whether Home's read is on its way.** A link or a notice that asks for the sheet waits for it,
   * so it opens on what it says.
   */
  readonly reading: boolean;
  /**
   * **The invitations FRIENDS GAME draws, on the one clock they are counted by** — handed to
   * `FriendsGameSection`, so the count and the tiles never disagree, and the clock has run since the
   * owner mounted, not since the sheet opened.
   */
  readonly friendsGames: FriendsGamesWaiting;
  /**
   * **The envelope's badge** (#819): what arrived since the sheet was last closed, as the server
   * counts it after this phone's visits — `0` while Home's read is not in.
   */
  readonly newCount: number;
}

export function useAnswersWaiting(): AnswersWaiting {
  const home = useHome();
  const friendsGames = useFriendsGamesWaiting();
  const visits = useVisitsSent();
  return {
    counts: [
      home.data?.paymentsToConfirm.length,
      friendsGames.waiting?.length,
      home.data?.friendRequests.length,
      home.data?.levelAsks.length,
    ],
    reading: home.isFetching,
    friendsGames,
    newCount: home.data === undefined ? 0 : newCountAfter(home.data.needsYourAnswer, visits),
  };
}

/** The watermarks of the visits this phone sent that are on their way or recorded. */
function useVisitsSent(): readonly string[] {
  const sent = useMutationState({
    filters: {
      mutationKey: proposalKeys.needsYourAnswerVisit(),
      predicate: (mutation) => mutation.state.status !== 'error',
    },
    select: (mutation) => mutation.state.variables,
  });
  return sent.filter((watermark): watermark is string => typeof watermark === 'string');
}

/**
 * **Needs your answer's visit** (#819) — `shown` is whether the sheet is shown (open, with something
 * in it); the answer is what the shell calls once it went for good. See the module note.
 */
export function useNeedsYourAnswerVisit(shown: boolean): () => void {
  const client = useQueryClient();
  const watermark = useHome().data?.needsYourAnswer.watermark;

  // What the sheet was shown on — an effect's, never render state: it is read when the sheet goes,
  // never drawn.
  const held = useRef<string | undefined>(undefined);
  useEffect(() => {
    held.current = watermarkShown(held.current, shown, watermark);
  }, [shown, watermark]);

  const { mutate: visit } = useMutation<void, AppError, string>({
    mutationKey: proposalKeys.needsYourAnswerVisit(),
    mutationFn: recordNeedsYourAnswerVisit,
    // Safe to repeat, by the route's own word — see the module note.
    retry: shouldRetryQuery,
    onSettled: () => client.invalidateQueries({ queryKey: proposalKeys.home() }),
  });

  return useCallback(() => {
    const seen = held.current;
    held.current = undefined;
    // A sheet only ever shown on a read with nothing in it showed nothing to see.
    if (seen !== undefined) visit(seen);
  }, [visit]);
}
