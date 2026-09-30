/**
 * **Games & money — the read, and a save on every tap** (#554; the screens A7.1: *changes save as
 * you tap*).
 *
 * | | |
 * | --- | --- |
 * | `useGamesAndMoney` | `GET /players/me/games-and-money` — the row's line and the screen |
 * | `useSaveGamesAndMoney` | `PUT` the same path — both limits, as they stand after the tap |
 *
 * ## The value moves on the tap, and the server's answer settles it
 *
 * A stepper that waited a round trip between presses would make four taps a second's walk, so a
 * tap writes the pair into the read at once (`onMutate`) and the save follows. `architecture.md`
 * Part 7 keeps optimism for cases like this one and rules it out for others, and this is not one of
 * those: nothing is charged or held — the ceiling is a preference about money, not a payment — the
 * response is this one player's pair and touches nothing else, a refusal is rare (only a form
 * offering what the server stopped offering) and its rollback is deterministic (the saved pair,
 * read again), and nothing here reaches another person. The decks it bounds are re-read, never
 * written.
 *
 * ## A tap steps from the last tap, not from the last render
 *
 * The value a tap writes into the read is drawn a tick later, and two taps inside that tick would
 * both step from the same number. So the hook keeps the pair the last tap left until every save has
 * settled, and hands it to the next tap (`save(tap)`); a tap that lands on that pair — the chip
 * already chosen, a key at the end of the range pressed before it drew shut — sends nothing.
 *
 * ## Saves go one at a time, in the order they were tapped
 *
 * Every save sends the whole pair, so the last one sent is the one that must land last. Three taps
 * in flight at once could arrive, or answer, out of order — and the answer written last would be a
 * pair the player had already moved past. The saves share a `scope`, which TanStack runs one after
 * another; **only the last one in flight writes its answer into the read**, and a refusal with
 * nothing behind it re-reads the server's pair, because the value drawn is then one that was never
 * saved.
 *
 * ## A limit bounds every deck
 *
 * Games per week decides which weeks a deck deals into, and the ceiling which cards it deals at all,
 * so once the last save settles every group's decks are marked stale and read again when next seen.
 *
 * ## A read landing late does not undo the last save
 *
 * A refetch on focus can start after a tap cancelled the reads and still be out when the last save
 * answers — and, asked before the save landed, it answers the old pair. So the last answer cancels
 * the reads before it writes itself in, and writes only if no tap came meanwhile.
 *
 * ## Offline, held
 *
 * The saves are held while offline (`networkMode: 'online'`) and sent in order on reconnect.
 * `isPaused` alone cannot say so: a save queued behind another in its scope is paused too, so the
 * hook answers *held offline* only while the connection is down (`useIsOnline`).
 *
 * The read keeps the app's defaults — thirty seconds fresh, read again on focus — because nothing
 * but this player changes the pair, and the row and the screen read the same entry.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef } from 'react';

import type { AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';

import { sameLimits, type GamesAndMoney, type Limits } from '../domain/gamesAndMoney';
import { readGamesAndMoney, saveGamesAndMoney } from '../use-cases/gamesAndMoney';

import { proposalKeys } from './proposalKeys';

export function useGamesAndMoney() {
  return useQuery<GamesAndMoney, AppError>({
    queryKey: proposalKeys.gamesAndMoney(),
    queryFn: ({ signal }) => readGamesAndMoney({ signal }),
  });
}

/** The saves' own key — what `isMutating` counts — and the scope that runs them in order. */
const SAVES = [...proposalKeys.gamesAndMoney(), 'save'] as const;

export function useSaveGamesAndMoney() {
  const client = useQueryClient();
  const key = proposalKeys.gamesAndMoney();
  // This save is still counted while it settles: 1 is the last one in flight.
  const lastInFlight = () => client.isMutating({ mutationKey: SAVES }) === 1;
  /** The pair the last tap left, until every save has settled — see the module note. */
  const tapped = useRef<Limits | undefined>(undefined);
  const online = useIsOnline();

  const saving = useMutation<GamesAndMoney, AppError, Limits>({
    mutationKey: SAVES,
    scope: { id: SAVES.join(' ') },
    mutationFn: saveGamesAndMoney,
    onMutate: async (limits) => {
      await client.cancelQueries({ queryKey: key });
      client.setQueryData<GamesAndMoney>(key, (held) =>
        held === undefined ? held : { ...held, ...limits },
      );
    },
    onSuccess: async (saved) => {
      if (!lastInFlight()) return;
      // A read begun after the tap may still be out with the old pair — see the module note.
      await client.cancelQueries({ queryKey: key });
      if (lastInFlight()) client.setQueryData(key, saved);
    },
    onError: () => {
      if (lastInFlight()) void client.invalidateQueries({ queryKey: key });
    },
    onSettled: () => {
      if (!lastInFlight()) return;
      tapped.current = undefined;
      void client.invalidateQueries({ queryKey: proposalKeys.decks() });
    },
  });

  return {
    /**
     * Save the pair a tap leaves. `tap` is handed the limits as the last tap left them — the read
     * itself when no save is out — and answers the pair to save.
     */
    save: (tap: (now: GamesAndMoney) => Limits) => {
      const held = client.getQueryData<GamesAndMoney>(key);
      if (held === undefined) return;
      const now = tapped.current === undefined ? held : { ...held, ...tapped.current };
      const next = tap(now);
      if (sameLimits(next, now)) return;
      tapped.current = next;
      saving.mutate(next);
    },
    /** The latest tap's refusal, until the next tap. */
    error: saving.error,
    /** A tap is waiting for the connection — see the module note. */
    heldOffline: saving.isPaused && !online,
  };
}
