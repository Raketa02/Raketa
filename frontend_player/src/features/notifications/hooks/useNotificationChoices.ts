/**
 * **The three choices — the read, and a save on every tap** (#559; the screens A7.2: three working
 * *On / Off* chips).
 *
 * | | |
 * | --- | --- |
 * | `useNotificationChoices` | `GET /players/me/notifications` — the row's line and the screen |
 * | `useSaveNotificationChoices` | `PUT` the same path — all three, as the tap leaves them |
 *
 * Games & money's shape (`proposals`' `useSaveGamesAndMoney`), for its reasons, because the act is
 * the same one — a preference saved on a tap with no *Save* button:
 *
 * - **The chip turns on the tap, and the server's answer settles it.** A tap writes the three into
 *   the read at once and the save follows: nothing here is charged or reaches another person, the
 *   answer is this player's three and nothing else, and a refusal re-reads what is saved.
 * - **A tap turns from the last tap, not the last render**, so two quick taps on one chip are on and
 *   off again rather than on twice.
 * - **Saves go one at a time, in the order tapped** (one `scope`), each sending all three, and only
 *   the last one in flight writes its answer — a later tap is never undone by an earlier reply.
 * - **Offline, held** and sent on reconnect, with the amber note while the connection is down.
 *
 * Nothing else is re-read on a save: a choice decides what the backend tells this player from the
 * next trigger on, and nothing the app draws counts it.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef } from 'react';

import type { AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';

import { switched, type ChoiceKey, type NotificationChoices } from '../domain/choices';
import { readChoices, saveChoices } from '../use-cases/notifications';

import { notificationKeys } from './notificationKeys';

export function useNotificationChoices() {
  return useQuery<NotificationChoices, AppError>({
    queryKey: notificationKeys.choices(),
    queryFn: ({ signal }) => readChoices({ signal }),
  });
}

/** The saves' own key — what `isMutating` counts — and the scope that runs them in order. */
const SAVES = [...notificationKeys.choices(), 'save'] as const;

export function useSaveNotificationChoices() {
  const client = useQueryClient();
  const key = notificationKeys.choices();
  // This save is still counted while it settles: 1 is the last one in flight.
  const lastInFlight = () => client.isMutating({ mutationKey: SAVES }) === 1;
  /** The three the last tap left, until every save has settled. */
  const tapped = useRef<NotificationChoices | undefined>(undefined);
  const online = useIsOnline();

  const saving = useMutation<NotificationChoices, AppError, NotificationChoices>({
    mutationKey: SAVES,
    scope: { id: SAVES.join(' ') },
    mutationFn: saveChoices,
    onMutate: async (choices) => {
      await client.cancelQueries({ queryKey: key });
      client.setQueryData<NotificationChoices>(key, (held) =>
        held === undefined ? held : choices,
      );
    },
    onSuccess: async (saved) => {
      if (!lastInFlight()) return;
      // A read begun after the tap may still be out with the old three.
      await client.cancelQueries({ queryKey: key });
      if (lastInFlight()) client.setQueryData(key, saved);
    },
    onError: () => {
      if (lastInFlight()) void client.invalidateQueries({ queryKey: key });
    },
    onSettled: () => {
      if (lastInFlight()) tapped.current = undefined;
    },
  });

  return {
    /** Turn one choice the other way, from where the last tap left it, and save all three. */
    toggle: (choice: ChoiceKey) => {
      const held = client.getQueryData<NotificationChoices>(key);
      if (held === undefined) return;
      const next = switched(tapped.current ?? held, choice);
      tapped.current = next;
      saving.mutate(next);
    },
    /** The latest tap's refusal, until the next tap. */
    error: saving.error,
    /** A tap is waiting for the connection. */
    heldOffline: saving.isPaused && !online,
  };
}
