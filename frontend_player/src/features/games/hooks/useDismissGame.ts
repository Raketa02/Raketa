/**
 * ***Remove this card*** — the old game's dismissal, in a file of its own.
 *
 * It is the one act in this feature that reaches into `features/challenges`, the old loop
 * [#569](https://github.com/Raketa02/Raketa/issues/569) removes: a called-off court is one fact on
 * the reader's games list and on their challenges list, and the reply clears both. It sits apart
 * from the booked game's writes in `useGames.ts` so that the lint boundary can allow exactly this
 * file that import ([#574](https://github.com/Raketa02/Raketa/issues/574)), and so that
 * [#576](https://github.com/Raketa02/Raketa/issues/576) deletes it whole with the card that presses
 * it.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { challengeKeys, dropCourtOfGame } from '@/features/challenges/types';

import { dismissGame } from '../use-cases/dismissGame';

import { dropCardOfGame } from './gameCache';
import { gameKeys } from './gameKeys';

/**
 * ***Remove this card*** — the dismissal, and **the card leaves the rail on the reply**
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §5, §8).
 *
 * The one write in this feature whose reply is written into the list rather than only
 * invalidating it, and the reason is what the reply *is*: `GET /games` omits a game its reader
 * has dismissed, so a list without this game is exactly the next read's answer, arriving one
 * round trip earlier — `useLeaveGame`'s argument for the leaver's own rows, one feature over.
 * The list is then re-read as well, because the reply is one card and the list is every card.
 *
 * **And the challenge row goes with the card**
 * ([ADR-0173](../../../../../docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md)):
 * a called-off court is one fact on two of the reader's lists, and `GET /challenges` now
 * subtracts its reader off the same set — so the row is dropped on the reply through the one
 * write that list lets another feature make, and re-read as well. The Chats row's swipe meets
 * the same act through a door of its own since ADR-0175 §5 (`useDismissCourt`, one feature
 * over), which drops this list's card through `dropCardOfGame` in turn.
 *
 * **A refusal re-reads both lists and says nothing**: `game_is_not_called_off` means the card the
 * reader pressed is not the card the server holds, and the fold the re-read lands on is the
 * answer, as it is for a stale fill. Pending, never optimistic — the card stays until the reply
 * says it is gone — and it pauses offline like every act in this feature: nothing about a
 * dismissal is fixed by the moment it is tapped.
 */
export function useDismissGame() {
  const client = useQueryClient();

  return useMutation<void, AppError, string>({
    mutationFn: dismissGame,
    onSuccess: (_nothing, gameId) => {
      dropCardOfGame(client, gameId);
      dropCourtOfGame(client, gameId);
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      void client.invalidateQueries({ queryKey: challengeKeys.list() });
    },
    onError: () => {
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      void client.invalidateQueries({ queryKey: challengeKeys.list() });
    },
  });
}
