/**
 * ***Show me in General*, as a switch draws it** ([ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md)
 * §7; the You spec §3.14; the rankings screens §4.5, §8; [#778](https://github.com/Raketa02/Raketa/issues/778))
 * — the profile read's value, and the write that turns it. Two switches draw it: the You row, and
 * the hidden card on Rankings, which `rankings` draws through this feature's surface.
 *
 * **It writes at once and moves at once**, with no *Save*: while a write is out the switch stands
 * where it was pressed — the write's own value, never a copy in a store — and once it lands the
 * profile read holds the value the route answered (`204`, so the value sent). **A refused write puts
 * it back** — the profile read never moved — and says why, through `error`, until the next press.
 * No optimistic patch of the cache, so there is nothing to roll back.
 *
 * Every write joins one queue (`RANKING_VISIBILITY_WRITES`): two presses, on either switch, reach the
 * server in the order they were pressed.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { PlayerProfileSurface } from '../domain/PlayerProfileSurface';
import { changeShowMeInGeneral } from '../use-cases/changeShowMeInGeneral';

import { RANKING_VISIBILITY_WRITES, playerProfileKeys } from './playerProfileKeys';
import { useProfileSurface } from './useProfileSurface';

export interface ShowMeInGeneral {
  /**
   * The switch as drawn: where it was last pressed while that write is out, else the profile's.
   * `undefined` until the profile read has landed — there is no switch to draw on a guess.
   */
  readonly checked: boolean | undefined;
  /** The last write, refused: the switch is back where the profile holds it. Cleared by a press. */
  readonly writeError: AppError | null;
  /** Turn it, at once. */
  readonly change: (showMeInGeneral: boolean) => void;
}

/**
 * **What the profile holds** — the switch's last write that landed, and what the ranking follows
 * (`rankings`' General page reads this, and turns nothing). `undefined` until the profile read has
 * landed.
 */
export function useShownInGeneral(): boolean | undefined {
  return useProfileSurface().data?.showMeInGeneral;
}

export function useShowMeInGeneral(): ShowMeInGeneral {
  const client = useQueryClient();
  const held = useShownInGeneral();

  const write = useMutation<boolean, AppError, boolean>({
    mutationFn: (showMeInGeneral) => changeShowMeInGeneral(showMeInGeneral),
    scope: RANKING_VISIBILITY_WRITES,
    onSuccess: (showMeInGeneral) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (surface) =>
        surface === undefined ? surface : { ...surface, showMeInGeneral },
      );
    },
  });

  return {
    checked: write.isPending ? write.variables : held,
    writeError: write.error,
    change: (showMeInGeneral) => write.mutate(showMeInGeneral),
  };
}
