/**
 * ***Show me to new people*, as the You row's switch draws it**
 * ([ADR-0204](../../../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
 * §2; the Home rows screens §9.1; [#799](https://github.com/Rakieta02/Rakieta/issues/799)) — the profile
 * read's value, and the write that turns it. It replaced *Show me in General* (#778), and with it the
 * second switch that one had on the Rankings page: one switch, drawn once.
 *
 * **It writes at once and moves at once**, with no *Save*: while a write is out the switch stands
 * where it was pressed — the write's own value, never a copy in a store — and once it lands the
 * profile read holds the value the route answered (`204`, so the value sent). **A refused write puts
 * it back** — the profile read never moved — and says why, through `writeError`, until the next
 * press. No optimistic patch of the cache, so there is nothing to roll back.
 *
 * **Nothing on this phone follows it.** The server reads the switch live on every record open and
 * every request, so there is no list here to wait on — unlike *Show me in General*, whose ranking
 * followed it through the outbox. Every write joins one queue (`SHOW_ME_TO_NEW_PEOPLE_WRITES`): two
 * presses in quick succession reach the server in the order they were pressed.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { PlayerProfileSurface } from '../domain/PlayerProfileSurface';
import { changeShowMeToNewPeople } from '../use-cases/changeShowMeToNewPeople';

import { SHOW_ME_TO_NEW_PEOPLE_WRITES, playerProfileKeys } from './playerProfileKeys';
import { useProfileSurface } from './useProfileSurface';

export interface ShowMeToNewPeople {
  /**
   * The switch as drawn: where it was last pressed while that write is out, else the profile's.
   * `undefined` until the profile read has landed — there is no switch to draw on a guess.
   */
  readonly checked: boolean | undefined;
  /** The last write, refused: the switch is back where the profile holds it. Cleared by a press. */
  readonly writeError: AppError | null;
  /** Turn it, at once. */
  readonly change: (on: boolean) => void;
}

export function useShowMeToNewPeople(): ShowMeToNewPeople {
  const client = useQueryClient();
  const held = useProfileSurface().data?.showMeToNewPeople;

  const write = useMutation<boolean, AppError, boolean>({
    mutationFn: (on) => changeShowMeToNewPeople(on),
    scope: SHOW_ME_TO_NEW_PEOPLE_WRITES,
    onSuccess: (showMeToNewPeople) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (surface) =>
        surface === undefined ? surface : { ...surface, showMeToNewPeople },
      );
    },
  });

  return {
    checked: write.isPending ? write.variables : held,
    writeError: write.error,
    change: (on) => write.mutate(on),
  };
}
