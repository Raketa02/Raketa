/**
 * **What waits in Needs your answer** ([#817](https://github.com/Raketa02/Raketa/issues/817),
 * ADR-0205 §1, §3) — the four sections' counts, off the reads this feature owns, for the shell's
 * envelope and sheet.
 *
 * Three ride on Home's one read (`GET /home`): the friends game invitations, the friend requests and
 * the asks for a level. **The payments to confirm stay on their own read**
 * (`GET /players/me/payments-to-confirm`), as ADR-0205 §3 keeps them: when it fails, nothing is
 * counted for them, so a failed read draws no envelope by itself, and Home's usual re-reads retry.
 */

import { useHome, useFriendsGamesWaiting, type FriendsGamesWaiting } from './useHome';
import { usePaymentsToConfirm } from './useLiveYeses';

export interface AnswersWaiting {
  /**
   * Each section's count, in the sheet's order — *TO CONFIRM*, *FRIENDS GAME*, *FRIEND REQUESTS*,
   * *ASKED FOR A LEVEL* — and `undefined` for a read not in yet, or refused: nothing waits there.
   */
  readonly counts: readonly (number | undefined)[];
  /**
   * **Whether a read behind the sheet is on its way** — Home's, or the payments to confirm. A link or
   * a notice that asks for the sheet waits for them, so it opens on what they say.
   */
  readonly reading: boolean;
  /**
   * **The invitations FRIENDS GAME draws, on the one clock they are counted by** — handed to
   * `FriendsGameSection`, so the count and the tiles never disagree, and the clock has run since the
   * owner mounted, not since the sheet opened.
   */
  readonly friendsGames: FriendsGamesWaiting;
}

export function useAnswersWaiting(): AnswersWaiting {
  const home = useHome();
  const toConfirm = usePaymentsToConfirm();
  const friendsGames = useFriendsGamesWaiting();
  return {
    counts: [
      toConfirm.data?.length,
      friendsGames.waiting?.length,
      home.data?.friendRequests.length,
      home.data?.levelAsks.length,
    ],
    reading: home.isFetching || toConfirm.isFetching,
    friendsGames,
  };
}
